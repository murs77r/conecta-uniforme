"""
============================================
RF02 - GERENCIAR AUTENTICAÇÃO E ACESSO
============================================
Este módulo é responsável por:
- RF02.1: Solicitar Código de Acesso
- RF02.2: Validar Código de Acesso

Controla o processo de autenticação e autorização de usuários, garantindo segurança no acesso ao sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from utils import executar_query, gerar_codigo_acesso, gerar_token_sessao, enviar_codigo_acesso, validar_email, registrar_log
from config import CODIGO_ACESSO_DURACAO_HORAS, SESSAO_DURACAO_DIAS, DEBUG, WEBAUTHN_RP_ID, WEBAUTHN_RP_NAME, WEBAUTHN_ORIGIN, WEBAUTHN_DEBUG
import os, base64, json
from webauthn import generate_registration_options, options_to_json, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement, AttestationConveyancePreference

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================
# Este blueprint funciona de forma independente
autenticacao_bp = Blueprint('autenticacao', __name__, url_prefix='/auth')

# ============================================
# ARMAZENAMENTO TEMPORÁRIO DE CHALLENGES (MEMÓRIA)
# Para produção, substituir por redis ou tabela dedicada.
# ============================================
_challenges_registro = {}
_challenges_login = {}

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _decode_b64url(data) -> bytes:
    """Decodifica base64url aceitando tanto str quanto bytes."""
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _load_webauthn_model(model_cls, data):
    """Compat loader for WebAuthn structs across Pydantic v1/v2."""
    payload = data if isinstance(data, str) else json.dumps(data)
    if hasattr(model_cls, 'model_validate_json'):
        return model_cls.model_validate_json(payload)
    if hasattr(model_cls, 'parse_raw'):
        return model_cls.parse_raw(payload)
    body = json.loads(payload)
    if hasattr(model_cls, 'model_validate'):
        return model_cls.model_validate(body)
    if hasattr(model_cls, 'parse_obj'):
        return model_cls.parse_obj(body)
    return model_cls(**body)


# ============================================
# AUX: TIPOS POR EMAIL (AJUDA FRONT A MOSTRAR MODAL)
# ============================================

@autenticacao_bp.route('/tipos-por-email')
def tipos_por_email():
    """Retorna os tipos de usuário ativos associados a um email (JSON).

    Resposta: { "email": str, "tipos": [str, ...] }
    """
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({"email": email, "tipos": []})
    q = "SELECT DISTINCT tipo FROM usuarios WHERE email = %s AND ativo = TRUE ORDER BY tipo"
    rows = executar_query(q, (email,), fetchall=True)
    tipos = [r['tipo'] for r in rows] if isinstance(rows, list) else []
    # Labels amigáveis para cada tipo (acentos e capitalização)
    rotulos = {
        'administrador': 'Administrador',
        'escola': 'Escola',
        'fornecedor': 'Fornecedor',
        'responsavel': 'Responsável',
    }
    tipos_formatados = [
        {"slug": t, "label": rotulos.get(t, t.title())} for t in tipos
    ]
    return jsonify({"email": email, "tipos": tipos_formatados})


# ============================================
# RF02.1 - SOLICITAR CÓDIGO DE ACESSO
# ============================================

@autenticacao_bp.route('/solicitar-codigo', methods=['GET', 'POST'])
def solicitar_codigo():
    """
    Tela para solicitar código de acesso
    
    GET: Exibe formulário para digitar email
    POST: Gera código, salva no banco e envia por email
    """
    
    # Se for GET, apenas mostra o formulário
    if request.method == 'GET':
        return render_template('auth/solicitar_codigo.html', passkeys_ativado=False)
    
    # Se for POST, processa o formulário
    # Pega o email digitado pelo usuário
    email = request.form.get('email', '').strip().lower()
    tipo_escolhido = request.form.get('tipo')  # opcional, quando houver múltiplos
    
    # Validação: verifica se o email foi preenchido
    if not email:
        flash('Por favor, digite seu email.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Validação: verifica se o email tem formato válido
    if not validar_email(email):
        flash('Email inválido. Verifique e tente novamente.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Busca todos usuários (tipos) para o email
    query_usuario = "SELECT id, nome, email, tipo, ativo FROM usuarios WHERE email = %s AND ativo = TRUE ORDER BY tipo"
    usuarios_encontrados = executar_query(query_usuario, (email,), fetchall=True)
    if not isinstance(usuarios_encontrados, list):
        usuarios_encontrados = []

    # Se nenhum usuário encontrado
    if not usuarios_encontrados:
        flash('Email não cadastrado no sistema.', 'danger')
        return render_template('auth/solicitar_codigo.html')

    # Se houver mais de um tipo e nenhum escolhido ainda, mostra modal de seleção
    if len(usuarios_encontrados) > 1 and not tipo_escolhido:
        tipos_disponiveis = [u['tipo'] for u in usuarios_encontrados]
        # Garante abertura do modal imediatamente e força a escolha do tipo antes de prosseguir
        return render_template('auth/solicitar_codigo.html', email=email, tipos_disponiveis=tipos_disponiveis, abrir_modal_tipo=True)

    # Determina o usuário alvo
    if len(usuarios_encontrados) == 1:
        usuario = usuarios_encontrados[0]
    else:
        usuario = next((u for u in usuarios_encontrados if u['tipo'] == tipo_escolhido), None)
        if not usuario:
            flash('Tipo de usuário inválido para este email.', 'danger')
            return render_template('auth/solicitar_codigo.html')
        # Log leve da seleção de perfil
        try:
            registrar_log(
                usuario_id=usuario['id'],
                tabela='usuarios',
                registro_id=usuario['id'],
                acao='UPDATE',  # usando UPDATE para padronizar visualização de diffs
                dados_antigos=None,
                dados_novos=None,
                descricao=f'Seleção de perfil para login (tipo={usuario.get("tipo")})'
            )
        except Exception:
            pass
    
    # Gera um código de acesso aleatório (6 dígitos)
    codigo = gerar_codigo_acesso()
    
    # Calcula a data de expiração do código (24 horas)
    data_expiracao = datetime.now() + timedelta(hours=CODIGO_ACESSO_DURACAO_HORAS)
    
    # Salva o código no banco de dados
    query_inserir = """
        INSERT INTO codigos_acesso (usuario_id, codigo, data_expiracao)
        VALUES (%s, %s, %s)
    """
    resultado = executar_query(query_inserir, (usuario['id'], codigo, data_expiracao), commit=True)
    
    # Verifica se salvou com sucesso
    if not resultado or resultado == 0:
        flash('Erro ao gerar código. Tente novamente.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Imprime o código no console para facilitar testes (ambiente de desenvolvimento)
    try:
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("=" * 60)
        print("CÓDIGO DE LOGIN GERADO")
        print(f"Data/Hora: {agora}")
        print(f"Usuário: {usuario['nome']} <{usuario['email']}> [{usuario['tipo']}]")
        print(f"Código: {codigo}")
        print("=" * 60)
    except Exception:
        # Evita quebrar o fluxo caso o print falhe por algum motivo de encoding
        pass

    # Envia o código por email (com timeout configurado)
    sucesso_envio = enviar_codigo_acesso(email, codigo, usuario['nome'])
    
    # Independente do sucesso do envio, vamos direcionar para a tela de validação
    if sucesso_envio:
        flash('Código de acesso enviado para seu email!', 'success')
        return redirect(url_for('autenticacao.validar_codigo', email=email, tipo=usuario['tipo']))
    else:
        # Em modo dev, permitir seguir e informar via modal na próxima tela
        return redirect(url_for('autenticacao.validar_codigo', email=email, tipo=usuario['tipo'], aviso_email='1' if DEBUG else '0'))


# ============================================
# RF02.2 - VALIDAR CÓDIGO DE ACESSO (LOGIN)
# ============================================

@autenticacao_bp.route('/validar-codigo', methods=['GET', 'POST'])
def validar_codigo():
    """
    Tela para validar o código de acesso e fazer login
    
    GET: Exibe formulário para digitar o código
    POST: Valida o código e cria sessão do usuário
    """
    
    # Pega o email e tipo da URL (passado pela página anterior)
    email = request.args.get('email', '')
    tipo = request.args.get('tipo', '')
    aviso_email = request.args.get('aviso_email', '0')
    
    # Se for GET, apenas mostra o formulário
    if request.method == 'GET':
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email=aviso_email, debug=DEBUG, passkeys_ativado=True)
    
    # Se for POST, processa o formulário
    # Pega os dados digitados
    email = request.form.get('email', '').strip().lower()
    tipo = request.form.get('tipo', '').strip()
    codigo_digitado = request.form.get('codigo', '').strip()
    
    # Validação: verifica se os campos foram preenchidos
    if not email or not codigo_digitado:
        flash('Preencha todos os campos.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Busca o código no banco de dados (amarra email+tipo)
    query_codigo = """
        SELECT ca.id, ca.usuario_id, ca.codigo, ca.data_expiracao, ca.usado,
               u.nome, u.email, u.tipo, u.ativo
        FROM codigos_acesso ca
        JOIN usuarios u ON ca.usuario_id = u.id
        WHERE u.email = %s AND u.tipo = %s AND ca.codigo = %s AND ca.usado = FALSE
        ORDER BY ca.data_criacao DESC
        LIMIT 1
    """
    registro_codigo = executar_query(query_codigo, (email, tipo, codigo_digitado), fetchone=True)
    if not isinstance(registro_codigo, dict):
        registro_codigo = {}
    
    # Verifica se o código existe e está válido
    if not registro_codigo or not registro_codigo.get('id'):
        flash('Código inválido ou já utilizado.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Verifica se o código expirou
    data_expiracao = registro_codigo.get('data_expiracao')
    if not data_expiracao:
        flash('Código inválido.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    if datetime.now() > data_expiracao:
        flash('Código expirado. Solicite um novo código.', 'danger')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica se o usuário está ativo
    if not registro_codigo.get('ativo'):
        flash('Usuário inativo. Entre em contato com o administrador.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Código válido! Marca como usado
    query_marcar_usado = "UPDATE codigos_acesso SET usado = TRUE WHERE id = %s"
    if registro_codigo.get('id'):
        executar_query(query_marcar_usado, (registro_codigo['id'],), commit=True)
    
    # Gera um token único para a sessão
    token_sessao = gerar_token_sessao()
    
    # Calcula a data de expiração da sessão
    data_expiracao_sessao = datetime.now() + timedelta(days=SESSAO_DURACAO_DIAS)
    
    # Salva a sessão no banco de dados
    query_sessao = """
        INSERT INTO sessoes (usuario_id, token, data_expiracao)
        VALUES (%s, %s, %s)
    """
    if registro_codigo.get('usuario_id'):
        executar_query(query_sessao, (registro_codigo['usuario_id'], token_sessao, data_expiracao_sessao), commit=True)
    
    # Salva os dados do usuário na sessão do Flask
    session['usuario_id'] = registro_codigo.get('usuario_id')
    session['usuario_nome'] = registro_codigo.get('nome')
    session['usuario_email'] = registro_codigo.get('email')
    session['usuario_tipo'] = registro_codigo.get('tipo')
    session['token_sessao'] = token_sessao
    
    # Log leve de sucesso de login (sem dados sensíveis)
    try:
        registrar_log(
            usuario_id=registro_codigo.get('usuario_id'),
            tabela='sessoes',
            registro_id=registro_codigo.get('usuario_id'),
            acao='INSERT',
            dados_antigos=None,
            dados_novos=None,
            descricao=f'Login realizado via código para tipo={registro_codigo.get("tipo")}'
        )
    except Exception:
        pass
    # Login realizado com sucesso!
    flash(f"Bem-vindo(a), {registro_codigo['nome']}!", 'success')
    
    # Redireciona para a página inicial
    return redirect(url_for('home'))


# ============================================
# LOGOUT - ENCERRAR SESSÃO
# ============================================

@autenticacao_bp.route('/logout')
def logout():
    """
    Encerra a sessão do usuário (logout)
    """
    
    # Pega o token da sessão
    token_sessao = session.get('token_sessao')
    
    # Se existe token, marca a sessão como inativa no banco
    if token_sessao:
        query_desativar = "UPDATE sessoes SET ativo = FALSE WHERE token = %s"
        executar_query(query_desativar, (token_sessao,), commit=True)
    
    # Limpa todos os dados da sessão
    session.clear()
    
    # Mensagem de logout
    flash('Logout realizado com sucesso!', 'info')
    
    # Redireciona para a página de login
    return redirect(url_for('autenticacao.solicitar_codigo'))


@autenticacao_bp.route('/passkeys')
def pagina_passkeys():
    """Página para gerenciamento e cadastro de Passkeys (requer login)."""
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para acessar o cadastro de Passkey.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    return render_template('auth/passkey.html', usuario=usuario)


# ============================================
# WEBAuthn - REGISTRO DE CREDENCIAL (Passkey)
# ============================================
@autenticacao_bp.route('/webauthn/registro/opcoes')
def webauthn_registro_opcoes():
    """Gera as opções de criação de credencial para o usuário logado."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401

    if WEBAUTHN_DEBUG:
        print('=' * 70)
        print('DEBUG WEBAUTHN - REGISTRO OPÇÕES')
        print(f'  RP_ID           : {WEBAUTHN_RP_ID}')
        print(f'  RP_NAME         : {WEBAUTHN_RP_NAME}')
        print(f'  ORIGIN          : {WEBAUTHN_ORIGIN}')
        print(f'  Usuário         : {usuario.get("email")}')
        print('=' * 70)

    # ID de usuário deve ser bytes estáveis (usar email como identificador)
    # Passkey fica vinculada ao EMAIL, não ao perfil específico
    email_usuario = (usuario.get('email') or '').strip().lower() if isinstance(usuario, dict) else ''
    if not email_usuario:
        return jsonify({'erro':'email_invalido'}), 400
    user_id_bytes = email_usuario.encode('utf-8')

    # Recupera credenciais existentes para excluir de excludeCredentials
    q = "SELECT credential_id FROM webauthn_credentials WHERE email = %s AND ativo = TRUE"
    creds = executar_query(q, (email_usuario,), fetchall=True)
    if not isinstance(creds, list):
        creds = []
    exclude = [PublicKeyCredentialDescriptor(id=_decode_b64url(c['credential_id'])) for c in creds if isinstance(c, dict) and c.get('credential_id')]

    try:
        options = generate_registration_options(
            rp_id=WEBAUTHN_RP_ID,
            rp_name=WEBAUTHN_RP_NAME,
            user_id=user_id_bytes,
            user_name=email_usuario,
            user_display_name=usuario['nome'],
            exclude_credentials=exclude,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED
            ),
            attestation=AttestationConveyancePreference.NONE,
        )
        # Armazena challenge usando email ao invés de usuario_id
        # Challenge deve ser bytes
        _challenges_registro[email_usuario] = options.challenge
        
        if WEBAUTHN_DEBUG:
            print(f'Opções de registro geradas com sucesso!')
            print(f'Challenge armazenado para: {email_usuario}')
            print(f'Challenge tipo: {type(options.challenge)}')
            print(f'Challenge length: {len(options.challenge) if hasattr(options.challenge, "__len__") else "N/A"}')
        
        return jsonify(json.loads(options_to_json(options)))
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'ERRO ao gerar opções de registro: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro': 'falha_gerar_opcoes', 'detalhes': str(e)}), 500


@autenticacao_bp.route('/webauthn/registro', methods=['POST'])
def webauthn_registro():
    """Recebe resposta de criação de credencial e valida."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401
    
    email_usuario = (usuario.get('email') or '').strip().lower()
    if not email_usuario:
        return jsonify({'erro': 'email_invalido'}), 400
    
    dados = request.get_json(force=True)
    challenge_esperado = _challenges_registro.get(email_usuario)
    if not challenge_esperado:
        return jsonify({'erro': 'challenge_expirado'}), 400
    
    if WEBAUTHN_DEBUG:
        print('=== DEBUG REGISTRO PASSKEY ===')
        print(f'Email: {email_usuario}')
        print(f'Dados recebidos (tipo): {type(dados)}')
        print(f'Dados recebidos (keys): {dados.keys() if isinstance(dados, dict) else "N/A"}')
        if 'id' in dados:
            print(f'ID tipo: {type(dados["id"])}, valor: {dados["id"][:20]}...')
        if 'rawId' in dados:
            print(f'rawId tipo: {type(dados["rawId"])}, valor: {dados["rawId"][:20]}...')
    
    # Guarda e remove 'transports' se existir, pois não faz parte do RegistrationCredential
    transports = dados.pop('transports', [])

    # Converte campos base64url (strings) para bytes onde necessário
    # O navegador envia tudo como strings base64url
    # A biblioteca WebAuthn espera: id=string, raw_id=bytes, response.*=bytes
    
    # Guarda o ID original como string (necessário para o modelo)
    id_original = dados.get('id') or dados.get('rawId')
    
    # Processa rawId -> raw_id (deve ser bytes)
    if 'rawId' in dados:
        raw_id_str = dados.pop('rawId')
        if isinstance(raw_id_str, str):
            dados['raw_id'] = _decode_b64url(raw_id_str)
        else:
            dados['raw_id'] = raw_id_str
    elif 'raw_id' in dados and isinstance(dados['raw_id'], str):
        dados['raw_id'] = _decode_b64url(dados['raw_id'])
    
    # Garante que 'id' seja string base64url
    if 'id' not in dados and id_original:
        dados['id'] = id_original
    
    # Se 'id' foi convertido para bytes por engano, reverte
    if 'id' in dados and isinstance(dados['id'], bytes):
        dados['id'] = _b64url(dados['id'])

    # Processa response e converte campos base64url para bytes
    if 'response' in dados and isinstance(dados['response'], dict):
        resp = dados['response']
        
        # Converte clientDataJSON
        if 'clientDataJSON' in resp:
            if isinstance(resp['clientDataJSON'], str):
                resp['client_data_json'] = _decode_b64url(resp['clientDataJSON'])
            else:
                resp['client_data_json'] = resp['clientDataJSON']
            resp.pop('clientDataJSON', None)
        elif 'client_data_json' in resp and isinstance(resp['client_data_json'], str):
            resp['client_data_json'] = _decode_b64url(resp['client_data_json'])
        
        # Converte attestationObject
        if 'attestationObject' in resp:
            if isinstance(resp['attestationObject'], str):
                resp['attestation_object'] = _decode_b64url(resp['attestationObject'])
            else:
                resp['attestation_object'] = resp['attestationObject']
            resp.pop('attestationObject', None)
        elif 'attestation_object' in resp and isinstance(resp['attestation_object'], str):
            resp['attestation_object'] = _decode_b64url(resp['attestation_object'])
    
    if WEBAUTHN_DEBUG:
        print('Após conversões (registro):')
        id_val = dados.get("id")
        raw_id_val = dados.get("raw_id")
        print(f'  - id: {type(id_val)} = {id_val[:30] + "..." if isinstance(id_val, str) and len(id_val) > 30 else id_val if isinstance(id_val, str) else "N/A"}')
        print(f'  - raw_id: {type(raw_id_val)} (bytes: {len(raw_id_val) if isinstance(raw_id_val, bytes) else "N/A"} bytes)')
        if 'response' in dados:
            resp_debug = dados['response']
            print(f'  - response.client_data_json: {type(resp_debug.get("client_data_json"))}')
            print(f'  - response.attestation_object: {type(resp_debug.get("attestation_object"))}')
    
    try:
        if WEBAUTHN_DEBUG:
            print(f'Tentando carregar modelo RegistrationCredential...')
            print(f'  Estrutura de dados preparada (tipos):')
            print(f'    - id: {type(dados.get("id"))}')
            print(f'    - raw_id: {type(dados.get("raw_id"))}')
            if 'response' in dados:
                print(f'    - response.client_data_json: {type(dados["response"].get("client_data_json"))}')
                print(f'    - response.attestation_object: {type(dados["response"].get("attestation_object"))}')
        
        credencial = _load_webauthn_model(RegistrationCredential, dados)
        
        if WEBAUTHN_DEBUG:
            print(f'Modelo carregado com sucesso')
            print(f'Challenge esperado (tipo): {type(challenge_esperado)}')
            print(f'Challenge esperado (len): {len(challenge_esperado) if hasattr(challenge_esperado, "__len__") else "N/A"}')
        
        verificado = verify_registration_response(
            credential=credencial,
            expected_challenge=challenge_esperado,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
        )
        if WEBAUTHN_DEBUG:
            print('Verificação bem-sucedida!')
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'Erro verificação registro WebAuthn: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro': 'verificacao_falhou', 'detalhes': str(e)}), 400

    cred_id_b64 = _b64url(verificado.credential_id)
    pubkey_b64 = _b64url(verificado.credential_public_key)
    # Salva no banco - vinculado ao EMAIL, não ao usuario_id específico
    # usuario_id pode ser qualquer um dos perfis do email (usamos o atual apenas como referência)
    q_ins = """
        INSERT INTO webauthn_credentials (usuario_id, email, credential_id, public_key, sign_count, transports, backup_eligible, backup_state, aaguid)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (credential_id) DO NOTHING
    """
    resultado = executar_query(q_ins, (
        usuario['id'], email_usuario, cred_id_b64, pubkey_b64, verificado.sign_count,
        json.dumps(transports or []),
        getattr(verificado, 'backup_eligible', False),
        getattr(verificado, 'backup_state', False),
        _b64url(verificado.aaguid) if getattr(verificado, 'aaguid', None) else None
    ), commit=True)
    
    if WEBAUTHN_DEBUG:
        print(f'Credencial salva com sucesso! ID: {cred_id_b64}')
    
    _challenges_registro.pop(email_usuario, None)
    return jsonify({'status': 'ok'})


# ============================================
# WEBAuthn - AUTENTICAÇÃO (LOGIN)
# ============================================
@autenticacao_bp.route('/webauthn/login/opcoes')
def webauthn_login_opcoes():
    email = request.args.get('email','').strip().lower()
    tipo = request.args.get('tipo','').strip()
    allow = None
    usuario = None
    if email and isinstance(email, str):
        # Busca usuário (se múltiplos tipos, pode filtrar por tipo)
        q = "SELECT id, nome, email, tipo FROM usuarios WHERE email=%s " + ("AND tipo=%s" if tipo else "") + " LIMIT 1"
        params = (email, tipo) if tipo else (email,)
        usuario = executar_query(q, params, fetchone=True)
        if not isinstance(usuario, dict) or not usuario:
            return jsonify({'erro':'usuario_nao_encontrado'}), 404
        # Pega credenciais registradas
        q2 = "SELECT credential_id FROM webauthn_credentials WHERE email=%s AND ativo=TRUE"
        email_lookup = usuario.get('email') if isinstance(usuario, dict) else None
        creds = executar_query(q2, (email_lookup,), fetchall=True) if email_lookup else []
        if not isinstance(creds, list):
            creds = []
        if creds:
            allow = [PublicKeyCredentialDescriptor(id=_decode_b64url(c['credential_id'])) for c in creds if isinstance(c, dict) and c.get('credential_id')]
    # allow=None permite credenciais descobríveis (resident)
    options = generate_authentication_options(
        allow_credentials=allow,
        rp_id=WEBAUTHN_RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    # Guarda challenge na sessão (precisa ser bytes)
    session['webauthn_challenge'] = options.challenge
    
    if WEBAUTHN_DEBUG:
        print('=== DEBUG LOGIN OPÇÕES ===')
        print(f'Challenge tipo: {type(options.challenge)}')
        print(f'Challenge length: {len(options.challenge) if hasattr(options.challenge, "__len__") else "N/A"}')
    
    if usuario and isinstance(usuario, dict):
        session['webauthn_login_email'] = usuario.get('email')
        session['webauthn_login_tipo'] = usuario.get('tipo')
    return jsonify(json.loads(options_to_json(options)))


@autenticacao_bp.route('/webauthn/login', methods=['POST'])
def webauthn_login():
    dados = request.get_json(force=True)
    challenge_esperado = session.pop('webauthn_challenge', None)
    if not challenge_esperado:
        return jsonify({'erro':'challenge_expirado'}), 400
    
    if WEBAUTHN_DEBUG:
        print('=== DEBUG LOGIN PASSKEY ===')
        print(f'Challenge esperado (tipo): {type(challenge_esperado)}')
    
    # Tipo escolhido pode vir no corpo da requisição (quando há múltiplos perfis)
    tipo_escolhido = dados.get('tipo')
    
    # Identifica credencial enviada (ANTES das conversões - precisa ser string base64url)
    cred_id_b64 = dados.get('id') or dados.get('rawId')
    if not cred_id_b64:
        return jsonify({'erro':'credencial_sem_id'}), 400
    
    # Converte campos base64url (strings) para bytes onde necessário
    # O navegador envia tudo como strings base64url
    # A biblioteca WebAuthn espera: id=string, raw_id=bytes, response.*=bytes
    
    # Guarda o ID original como string (necessário para o modelo)
    id_original = dados.get('id') or dados.get('rawId')
    
    # Processa rawId -> raw_id (deve ser bytes)
    if 'rawId' in dados:
        raw_id_str = dados.pop('rawId')
        if isinstance(raw_id_str, str):
            dados['raw_id'] = _decode_b64url(raw_id_str)
        else:
            dados['raw_id'] = raw_id_str
    elif 'raw_id' in dados and isinstance(dados['raw_id'], str):
        dados['raw_id'] = _decode_b64url(dados['raw_id'])
    
    # Garante que 'id' seja string base64url
    if 'id' not in dados and id_original:
        dados['id'] = id_original
    
    # Se 'id' foi convertido para bytes por engano, reverte
    if 'id' in dados and isinstance(dados['id'], bytes):
        dados['id'] = _b64url(dados['id'])
    
    # Processa response e converte campos base64url para bytes
    if 'response' in dados and isinstance(dados['response'], dict):
        resp = dados['response']
        
        # Converte clientDataJSON
        if 'clientDataJSON' in resp:
            if isinstance(resp['clientDataJSON'], str):
                resp['client_data_json'] = _decode_b64url(resp['clientDataJSON'])
            else:
                resp['client_data_json'] = resp['clientDataJSON']
            resp.pop('clientDataJSON', None)
        elif 'client_data_json' in resp and isinstance(resp['client_data_json'], str):
            resp['client_data_json'] = _decode_b64url(resp['client_data_json'])
        
        # Converte authenticatorData
        if 'authenticatorData' in resp:
            if isinstance(resp['authenticatorData'], str):
                resp['authenticator_data'] = _decode_b64url(resp['authenticatorData'])
            else:
                resp['authenticator_data'] = resp['authenticatorData']
            resp.pop('authenticatorData', None)
        elif 'authenticator_data' in resp and isinstance(resp['authenticator_data'], str):
            resp['authenticator_data'] = _decode_b64url(resp['authenticator_data'])
        
        # Converte signature
        if 'signature' in resp and isinstance(resp['signature'], str):
            resp['signature'] = _decode_b64url(resp['signature'])
        
        # Converte userHandle se existir
        if 'userHandle' in resp:
            if resp['userHandle'] and isinstance(resp['userHandle'], str):
                resp['user_handle'] = _decode_b64url(resp['userHandle'])
            resp.pop('userHandle', None)
        elif 'user_handle' in resp and resp['user_handle'] and isinstance(resp['user_handle'], str):
            resp['user_handle'] = _decode_b64url(resp['user_handle'])
    
    if WEBAUTHN_DEBUG:
        print('Após conversões (login):')
        print(f'  - id: {type(dados.get("id"))}')
        print(f'  - raw_id: {type(dados.get("raw_id"))}')
        if 'response' in dados:
            print(f'  - response.client_data_json: {type(dados["response"].get("client_data_json"))}')
            print(f'  - response.authenticator_data: {type(dados["response"].get("authenticator_data"))}')
            print(f'  - response.signature: {type(dados["response"].get("signature"))}')
    
    # Encontra dono da credencial
    q = "SELECT wc.usuario_id as uid, wc.email, wc.public_key, wc.sign_count FROM webauthn_credentials wc WHERE wc.credential_id=%s AND wc.ativo=TRUE"
    reg = executar_query(q, (cred_id_b64,), fetchone=True)
    if not isinstance(reg, dict) or not reg:
        return jsonify({'erro':'credencial_desconhecida'}), 404
    try:
        if WEBAUTHN_DEBUG:
            print(f'Tentando verificar autenticação com challenge tipo: {type(challenge_esperado)}')
        
        verificado = verify_authentication_response(
            credential=_load_webauthn_model(AuthenticationCredential, dados),
            expected_challenge=challenge_esperado,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
            credential_public_key=_decode_b64url(reg.get('public_key','')),
            credential_current_sign_count=reg.get('sign_count', 0),
        )
        
        if WEBAUTHN_DEBUG:
            print('Verificação de login bem-sucedida!')
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'Erro verificação login WebAuthn: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro':'verificacao_falhou', 'detalhes': str(e)}), 400
    # Atualiza sign_count
    executar_query("UPDATE webauthn_credentials SET sign_count=%s, ultimo_uso=NOW() WHERE credential_id=%s", (verificado.new_sign_count, cred_id_b64), commit=True)
    # Cria sessão normal
    email = reg.get('email')
    u_lista = executar_query("SELECT id, nome, tipo FROM usuarios WHERE email=%s AND ativo=TRUE ORDER BY tipo", (email,), fetchall=True)
    if not isinstance(u_lista, list) or len(u_lista) == 0:
        return jsonify({'erro':'usuario_nao_encontrado'}), 404
    
    # Se múltiplos tipos E nenhum tipo foi escolhido, pede para escolher
    if len(u_lista) > 1 and not tipo_escolhido:
        tipos_disp = [row.get('tipo') for row in u_lista if isinstance(row, dict)]
        return jsonify({'erro':'selecionar_tipo', 'tipos': tipos_disp}), 200
    
    # Se tipo foi escolhido, busca o usuário correspondente
    if tipo_escolhido:
        u = next((row for row in u_lista if row.get('tipo') == tipo_escolhido), None)
        if not u:
            return jsonify({'erro':'tipo_invalido'}), 400
    else:
        u = u_lista[0]
    
    uid = u.get('id')
    tipo = u.get('tipo')
    nome = u.get('nome')
    
    # Gera token sessão
    token_sessao = gerar_token_sessao()
    data_expiracao_sessao = datetime.now() + timedelta(days=SESSAO_DURACAO_DIAS)
    executar_query("INSERT INTO sessoes (usuario_id, token, data_expiracao) VALUES (%s,%s,%s)", (uid, token_sessao, data_expiracao_sessao), commit=True)
    # Preenche sessão flask
    session['usuario_id'] = uid
    session['usuario_nome'] = nome
    session['usuario_email'] = email
    session['usuario_tipo'] = tipo
    session['token_sessao'] = token_sessao
    
    # Log do login via passkey
    try:
        registrar_log(
            usuario_id=uid,
            tabela='sessoes',
            registro_id=uid,
            acao='INSERT',
            dados_antigos=None,
            dados_novos=None,
            descricao=f'Login realizado via Passkey para tipo={tipo}'
        )
    except Exception:
        pass
    
    return jsonify({'status':'ok'})


# ============================================
# WEBAuthn - UTIL: TEM PASSKEY PARA EMAIL?
# ============================================
@autenticacao_bp.route('/webauthn/tem')
def webauthn_tem():
    email = request.args.get('email','').strip().lower()
    if not email:
        return jsonify({'tem': False})
    reg = executar_query("SELECT 1 FROM webauthn_credentials WHERE email=%s AND ativo=TRUE LIMIT 1", (email,), fetchone=True)
    return jsonify({'tem': bool(reg)})


# ============================================
# WEBAuthn - DIAGNÓSTICO (apenas em DEBUG)
# ============================================
@autenticacao_bp.route('/webauthn/diagnostico')
def webauthn_diagnostico():
    """Endpoint de diagnóstico para verificar configuração WebAuthn (apenas em modo DEBUG)."""
    if not DEBUG:
        return jsonify({'erro': 'disponivel_apenas_em_debug'}), 403
    
    # Pega informações do request
    host_header = request.headers.get('Host', 'N/A')
    origin_header = request.headers.get('Origin', 'N/A')
    referer_header = request.headers.get('Referer', 'N/A')
    scheme = request.scheme
    full_url = request.url
    
    return jsonify({
        'configuracao': {
            'WEBAUTHN_RP_ID': WEBAUTHN_RP_ID,
            'WEBAUTHN_RP_NAME': WEBAUTHN_RP_NAME,
            'WEBAUTHN_ORIGIN': WEBAUTHN_ORIGIN,
            'WEBAUTHN_DEBUG': WEBAUTHN_DEBUG,
        },
        'request_info': {
            'scheme': scheme,
            'host': host_header,
            'origin': origin_header,
            'referer': referer_header,
            'full_url': full_url,
        },
        'diagnostico': {
            'rp_id_matches_host': WEBAUTHN_RP_ID == host_header or WEBAUTHN_RP_ID in host_header,
            'origin_matches': WEBAUTHN_ORIGIN == f"{scheme}://{host_header}",
            'sugestao_rp_id': host_header,
            'sugestao_origin': f"{scheme}://{host_header}",
        }
    })


# ============================================
# VERIFICAR SESSÃO (FUNÇÃO AUXILIAR)
# ============================================

def verificar_sessao():
    """
    Verifica se o usuário está autenticado
    
    Retorna:
        dict ou None: Dados do usuário se autenticado, None caso contrário
    """
    
    # Verifica se existe usuario_id na sessão
    if 'usuario_id' not in session:
        return None
    
    # Verifica se existe token na sessão
    token_sessao = session.get('token_sessao')
    if not token_sessao:
        return None
    
    # Busca a sessão no banco de dados
    query_sessao = """
        SELECT s.id, s.usuario_id, s.data_expiracao, s.ativo,
               u.nome, u.email, u.tipo, u.ativo as usuario_ativo
        FROM sessoes s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.token = %s AND s.ativo = TRUE
    """
    sessao_db = executar_query(query_sessao, (token_sessao,), fetchone=True)
    if not isinstance(sessao_db, dict):
        sessao_db = {}
    
    # Verifica se a sessão existe
    if not sessao_db:
        session.clear()
        return None
    
    # Verifica se a sessão expirou
    data_exp = sessao_db.get('data_expiracao')
    if not data_exp or datetime.now() > data_exp:
        session.clear()
        return None
    
    # Verifica se o usuário está ativo
    if not sessao_db.get('usuario_ativo'):
        session.clear()
        return None
    
    # Sessão válida! Retorna os dados do usuário
    return {
        'id': sessao_db.get('usuario_id'),
        'nome': sessao_db.get('nome'),
        'email': sessao_db.get('email'),
        'tipo': sessao_db.get('tipo')
    }


# ============================================
# VERIFICAR PERMISSÃO (FUNÇÃO AUXILIAR)
# ============================================

def verificar_permissao(tipos_permitidos):
    """
    Verifica se o usuário tem permissão para acessar uma página
    
    Parâmetros:
        tipos_permitidos (list): Lista de tipos de usuário permitidos
                                 Ex: ['administrador', 'escola']
    
    Retorna:
        dict ou None: Dados do usuário se tem permissão, None caso contrário
    """
    
    # Verifica se o usuário está autenticado
    usuario = verificar_sessao()
    if not usuario:
        return None
    
    # Verifica se o tipo do usuário está na lista de permitidos
    if usuario['tipo'] not in tipos_permitidos:
        return None
    
    # Usuário tem permissão!
    return usuario


# ============================================
# FIM DO MÓDULO DE AUTENTICAÇÃO
# ============================================
