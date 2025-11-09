"""
============================================
RF02 - GERENCIAR AUTENTICAÃ‡ÃƒO E ACESSO
============================================
Este mÃ³dulo Ã© responsÃ¡vel por:
- RF02.1: Solicitar CÃ³digo de Acesso
- RF02.2: Validar CÃ³digo de Acesso

Controla o processo de autenticaÃ§Ã£o e autorizaÃ§Ã£o de usuÃ¡rios, garantindo seguranÃ§a no acesso ao sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from core.database import Database
from core.services import EmailService, UtilsService, ValidacaoService, LogService
from config import CODIGO_ACESSO_DURACAO_HORAS, SESSAO_DURACAO_DIAS, DEBUG, WEBAUTHN_RP_ID, WEBAUTHN_RP_NAME, WEBAUTHN_ORIGIN, WEBAUTHN_DEBUG
import os, base64, json
from webauthn import generate_registration_options, options_to_json, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement, AttestationConveyancePreference, AuthenticatorAttestationResponse, AuthenticatorAssertionResponse

# ============================================
# CRIAÃ‡ÃƒO DO BLUEPRINT (MICROFRONT-END)
# ============================================
# Este blueprint funciona de forma independente
autenticacao_bp = Blueprint('autenticacao', __name__, url_prefix='/auth')

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _decode_b64url(data) -> bytes:
    """Decodifica base64url aceitando tanto str quanto bytes."""
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _load_webauthn_model(model_cls, data):
    """Compat loader for WebAuthn structs across Pydantic v1/v2.

    EstratÃ©gia: raw_id deve permanecer bytes (nÃ£o JSON-safe), enquanto campos internos
    em 'response' podem ser convertidos apenas se necessÃ¡rio. Pydantic v2 aceita bytes nativamente
    em model_validate(), entÃ£o preferimos esse caminho ao invÃ©s de JSON serialization.
    """
    # Se for dict, usa validaÃ§Ã£o direta preservando bytes onde a biblioteca espera
    if isinstance(data, dict):
        # Tenta validaÃ§Ã£o direta que preserve bytes (Pydantic v2 model_validate aceita bytes)
        if hasattr(model_cls, 'model_validate'):
            return model_cls.model_validate(data)  # Pydantic v2 (aceita bytes em campos)
        if hasattr(model_cls, 'parse_obj'):
            return model_cls.parse_obj(data)  # Pydantic v1
        # Fallback direto
        return model_cls(**data)

    # Caso seja string JSON, use os caminhos nativos
    if isinstance(data, str):
        payload = data
    else:
        # Para outros tipos serializÃ¡veis (sem bytes)
        payload = json.dumps(data)

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
    """Retorna os tipos de usuÃ¡rio ativos associados a um email (JSON).

    Resposta: { "email": str, "tipos": [str, ...] }
    """
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({"email": email, "tipos": []})
    q = "SELECT DISTINCT tipo FROM usuarios WHERE email = %s AND ativo = TRUE ORDER BY tipo"
    rows = Database.executar(q, (email,), fetchall=True)
    tipos = [r['tipo'] for r in rows] if isinstance(rows, list) else []
    # Labels amigÃ¡veis para cada tipo (acentos e capitalizaÃ§Ã£o)
    rotulos = {
        'administrador': 'Administrador',
        'escola': 'Escola',
        'fornecedor': 'Fornecedor',
        'responsavel': 'ResponsÃ¡vel',
    }
    tipos_formatados = [
        {"slug": t, "label": rotulos.get(t, t.title())} for t in tipos
    ]
    return jsonify({"email": email, "tipos": tipos_formatados})


# ============================================
# RF02.1 - SOLICITAR CÃ“DIGO DE ACESSO
# ============================================

@autenticacao_bp.route('/solicitar-codigo', methods=['GET', 'POST'])
def solicitar_codigo():
    """
    Tela para solicitar cÃ³digo de acesso
    
    GET: Exibe formulÃ¡rio para digitar email
    POST: Gera cÃ³digo, salva no banco e envia por email
    """
    
    # Se for GET, apenas mostra o formulÃ¡rio
    if request.method == 'GET':
        return render_template('auth/solicitar_codigo.html', passkeys_ativado=False)
    
    # Se for POST, processa o formulÃ¡rio
    # Pega o email digitado pelo usuÃ¡rio
    email = request.form.get('email', '').strip().lower()
    tipo_escolhido = request.form.get('tipo')  # opcional, quando houver mÃºltiplos
    
    # ValidaÃ§Ã£o: verifica se o email foi preenchido
    if not email:
        flash('Por favor, digite seu email.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # ValidaÃ§Ã£o: verifica se o email tem formato vÃ¡lido
    if not ValidacaoService.validar_email(email):
        flash('Email invÃ¡lido. Verifique e tente novamente.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Busca todos usuÃ¡rios (tipos) para o email
    query_usuario = "SELECT id, nome, email, tipo, ativo FROM usuarios WHERE email = %s AND ativo = TRUE ORDER BY tipo"
    usuarios_encontrados = Database.executar(query_usuario, (email,), fetchall=True)
    if not isinstance(usuarios_encontrados, list):
        usuarios_encontrados = []

    # Se nenhum usuÃ¡rio encontrado
    if not usuarios_encontrados:
        flash('Email nÃ£o cadastrado no sistema.', 'danger')
        return render_template('auth/solicitar_codigo.html')

    # Se houver mais de um tipo e nenhum escolhido ainda, mostra modal de seleÃ§Ã£o
    if len(usuarios_encontrados) > 1 and not tipo_escolhido:
        tipos_disponiveis = [u['tipo'] for u in usuarios_encontrados]
        # Garante abertura do modal imediatamente e forÃ§a a escolha do tipo antes de prosseguir
        return render_template('auth/solicitar_codigo.html', email=email, tipos_disponiveis=tipos_disponiveis, abrir_modal_tipo=True)

    # Determina o usuÃ¡rio alvo
    if len(usuarios_encontrados) == 1:
        usuario = usuarios_encontrados[0]
    else:
        usuario = next((u for u in usuarios_encontrados if u['tipo'] == tipo_escolhido), None)
        if not usuario:
            flash('Tipo de usuÃ¡rio invÃ¡lido para este email.', 'danger')
            return render_template('auth/solicitar_codigo.html')
        # Log leve da seleÃ§Ã£o de perfil
        try:
            LogService.registrar_acesso(
                usuario_id=usuario['id'],
                acao='LOGIN',
                tipo_autenticacao='codigo',
                ip_usuario=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                sucesso=False,  # Ainda nÃ£o completou o login, apenas selecionou perfil
                descricao=f'SeleÃ§Ã£o de perfil para login (tipo={usuario.get("tipo")})'
            )
        except Exception:
            pass
    
    # Gera um cÃ³digo de acesso aleatÃ³rio (6 dÃ­gitos)
    codigo = UtilsService.gerar_codigo_acesso()
    
    # Calcula a data de expiraÃ§Ã£o do cÃ³digo (24 horas)
    data_expiracao = datetime.now() + timedelta(hours=CODIGO_ACESSO_DURACAO_HORAS)
    
    # Salva o cÃ³digo no banco de dados
    query_inserir = """
        INSERT INTO codigos_acesso (usuario_id, codigo, data_expiracao)
        VALUES (%s, %s, %s)
    """
    resultado = Database.executar(query_inserir, (usuario['id'], codigo, data_expiracao), commit=True)
    
    # Verifica se salvou com sucesso
    if not resultado or resultado == 0:
        flash('Erro ao gerar cÃ³digo. Tente novamente.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Imprime o cÃ³digo no console para facilitar testes (ambiente de desenvolvimento)
    try:
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("=" * 60)
        print("CÃ“DIGO DE LOGIN GERADO")
        print(f"Data/Hora: {agora}")
        print(f"UsuÃ¡rio: {usuario['nome']} <{usuario['email']}> [{usuario['tipo']}]")
        print(f"CÃ³digo: {codigo}")
        print("=" * 60)
    except Exception:
        # Evita quebrar o fluxo caso o print falhe por algum motivo de encoding
        pass

    # Envia o cÃ³digo por email (com timeout configurado)
    sucesso_envio = EmailService().enviar_codigo_acesso(email, codigo, usuario['nome'])
    
    # Independente do sucesso do envio, vamos direcionar para a tela de validaÃ§Ã£o
    if sucesso_envio:
        flash('CÃ³digo de acesso enviado para seu email!', 'success')
        return redirect(url_for('autenticacao.validar_codigo', email=email, tipo=usuario['tipo']))
    else:
        # Em modo dev, permitir seguir e informar via modal na prÃ³xima tela
        return redirect(url_for('autenticacao.validar_codigo', email=email, tipo=usuario['tipo'], aviso_email='1' if DEBUG else '0'))


# ============================================
# RF02.2 - VALIDAR CÃ“DIGO DE ACESSO (LOGIN)
# ============================================

@autenticacao_bp.route('/validar-codigo', methods=['GET', 'POST'])
def validar_codigo():
    """
    Tela para validar o cÃ³digo de acesso e fazer login
    
    GET: Exibe formulÃ¡rio para digitar o cÃ³digo
    POST: Valida o cÃ³digo e cria sessÃ£o do usuÃ¡rio
    """
    
    # Pega o email e tipo da URL (passado pela pÃ¡gina anterior)
    email = request.args.get('email', '')
    tipo = request.args.get('tipo', '')
    aviso_email = request.args.get('aviso_email', '0')
    
    # Se for GET, apenas mostra o formulÃ¡rio
    if request.method == 'GET':
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email=aviso_email, debug=DEBUG, passkeys_ativado=True)
    
    # Se for POST, processa o formulÃ¡rio
    # Pega os dados digitados
    email = request.form.get('email', '').strip().lower()
    tipo = request.form.get('tipo', '').strip()
    codigo_digitado = request.form.get('codigo', '').strip()
    
    # ValidaÃ§Ã£o: verifica se os campos foram preenchidos
    if not email or not codigo_digitado:
        flash('Preencha todos os campos.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Busca o cÃ³digo no banco de dados (amarra email+tipo)
    query_codigo = """
        SELECT ca.id, ca.usuario_id, ca.codigo, ca.data_expiracao, ca.usado,
               u.nome, u.email, u.tipo, u.ativo
        FROM codigos_acesso ca
        JOIN usuarios u ON ca.usuario_id = u.id
        WHERE u.email = %s AND u.tipo = %s AND ca.codigo = %s AND ca.usado = FALSE
        ORDER BY ca.data_criacao DESC
        LIMIT 1
    """
    registro_codigo = Database.executar(query_codigo, (email, tipo, codigo_digitado), fetchone=True)
    if not isinstance(registro_codigo, dict):
        registro_codigo = {}
    
    # Verifica se o cÃ³digo existe e estÃ¡ vÃ¡lido
    if not registro_codigo or not registro_codigo.get('id'):
        flash('CÃ³digo invÃ¡lido ou jÃ¡ utilizado.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Verifica se o cÃ³digo expirou
    data_expiracao = registro_codigo.get('data_expiracao')
    if not data_expiracao:
        flash('CÃ³digo invÃ¡lido.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    if datetime.now() > data_expiracao:
        flash('CÃ³digo expirado. Solicite um novo cÃ³digo.', 'danger')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica se o usuÃ¡rio estÃ¡ ativo
    if not registro_codigo.get('ativo'):
        flash('UsuÃ¡rio inativo. Entre em contato com o administrador.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # CÃ³digo vÃ¡lido! Marca como usado
    query_marcar_usado = "UPDATE codigos_acesso SET usado = TRUE WHERE id = %s"
    if registro_codigo.get('id'):
        Database.executar(query_marcar_usado, (registro_codigo['id'],), commit=True)
    
    # Salva os dados do usuÃ¡rio na sessÃ£o do Flask
    session['usuario_id'] = registro_codigo.get('usuario_id')
    session['usuario_nome'] = registro_codigo.get('nome')
    session['usuario_email'] = registro_codigo.get('email')
    session['usuario_tipo'] = registro_codigo.get('tipo')
    session['logged_in'] = True
    
    # Log de sucesso de login
    try:
        LogService.registrar_acesso(
            usuario_id=registro_codigo.get('usuario_id'),
            acao='LOGIN',
            tipo_autenticacao='codigo',
            ip_usuario=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            sucesso=True,
            descricao=f'Login realizado via cÃ³digo para tipo={registro_codigo.get("tipo")}'
        )
    except Exception:
        pass
    # Login realizado com sucesso!
    flash(f"Bem-vindo(a), {registro_codigo['nome']}!", 'success')
    
    # Redireciona para a pÃ¡gina inicial
    return redirect(url_for('home'))


# ============================================
# LOGOUT - ENCERRAR SESSÃƒO
# ============================================

@autenticacao_bp.route('/logout')
def logout():
    """
    Encerra a sessÃ£o do usuÃ¡rio (logout)
    """
    # Registra o logoff antes de limpar a sessÃ£o
    if session.get('logged_in') and session.get('usuario_id'):
        try:
            LogService.registrar_acesso(
                usuario_id=session.get('usuario_id'),
                acao='LOGOFF',
                tipo_autenticacao=None,
                ip_usuario=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                sucesso=True,
                descricao='Logout realizado pelo usuÃ¡rio'
            )
        except Exception:
            pass
    
    # Limpa todos os dados da sessÃ£o
    session.clear()
    
    # Mensagem de logout
    flash('Logout realizado com sucesso!', 'info')
    
    # Redireciona para a pÃ¡gina de login
    return redirect(url_for('autenticacao.solicitar_codigo'))


@autenticacao_bp.route('/passkeys')
def pagina_passkeys():
    """PÃ¡gina para gerenciamento e cadastro de Passkeys (requer login)."""
    usuario = verificar_sessao()
    if not usuario:
        flash('FaÃ§a login para acessar o cadastro de Passkey.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    # Busca as passkeys existentes para o email do usuÃ¡rio
    q = "SELECT credential_id, data_criacao, ultimo_uso FROM webauthn_credentials WHERE email = %s AND ativo = TRUE ORDER BY data_criacao DESC"
    passkeys = Database.executar(q, (usuario['email'],), fetchall=True)
    if not isinstance(passkeys, list):
        passkeys = []

    return render_template('auth/passkey.html', usuario=usuario, passkeys=passkeys)


# ============================================
# WEBAuthn - REGISTRO DE CREDENCIAL (Passkey)
# ============================================
@autenticacao_bp.route('/webauthn/registro/opcoes')
def webauthn_registro_opcoes():
    """Gera as opÃ§Ãµes de criaÃ§Ã£o de credencial para o usuÃ¡rio logado."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401

    if WEBAUTHN_DEBUG:
        print('=' * 70)
        print('DEBUG WEBAUTHN - REGISTRO OPÃ‡Ã•ES')
        print(f'  RP_ID           : {WEBAUTHN_RP_ID}')
        print(f'  RP_NAME         : {WEBAUTHN_RP_NAME}')
        print(f'  ORIGIN          : {WEBAUTHN_ORIGIN}')
        print(f'  UsuÃ¡rio         : {usuario.get("email")}')
        print('=' * 70)

    # ID de usuÃ¡rio deve ser bytes estÃ¡veis (usar email como identificador)
    # Passkey fica vinculada ao EMAIL, nÃ£o ao perfil especÃ­fico
    email_usuario = (usuario.get('email') or '').strip().lower() if isinstance(usuario, dict) else ''
    if not email_usuario:
        return jsonify({'erro':'email_invalido'}), 400
    user_id_bytes = email_usuario.encode('utf-8')

    # Recupera credenciais existentes para excluir de excludeCredentials
    q = "SELECT credential_id FROM webauthn_credentials WHERE email = %s AND ativo = TRUE"
    creds = Database.executar(q, (email_usuario,), fetchall=True)
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
        # Armazena challenge no banco de dados com expiraÃ§Ã£o
        challenge_b64 = _b64url(options.challenge)
        expiracao = datetime.now() + timedelta(minutes=5) # Challenge vÃ¡lido por 5 minutos
        Database.executar(
            "INSERT INTO webauthn_challenges (challenge, email, data_expiracao) VALUES (%s, %s, %s)",
            (challenge_b64, email_usuario, expiracao),
            commit=True
        )
        
        if WEBAUTHN_DEBUG:
            print(f'OpÃ§Ãµes de registro geradas com sucesso!')
            print(f'Challenge armazenado no banco para: {email_usuario}')
        
        return jsonify(json.loads(options_to_json(options)))
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'ERRO ao gerar opÃ§Ãµes de registro: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro': 'falha_gerar_opcoes', 'detalhes': str(e)}), 500


@autenticacao_bp.route('/webauthn/registro', methods=['POST'])
def webauthn_registro():
    """Recebe resposta de criaÃ§Ã£o de credencial e valida."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401
    
    email_usuario = (usuario.get('email') or '').strip().lower()
    if not email_usuario:
        return jsonify({'erro': 'email_invalido'}), 400
    
    dados = request.get_json(force=True)

    # Busca e valida o challenge no banco de dados
    q_challenge = "SELECT challenge FROM webauthn_challenges WHERE email = %s AND data_expiracao > NOW() ORDER BY data_expiracao DESC LIMIT 1"
    challenge_rec = Database.executar(q_challenge, (email_usuario,), fetchone=True)
    
    if not challenge_rec or not challenge_rec.get('challenge'):
        return jsonify({'erro': 'challenge_expirado_ou_invalido'}), 400
    
    challenge_esperado = _decode_b64url(challenge_rec.get('challenge'))

    # Limpa o challenge do banco para que nÃ£o seja reutilizado
    Database.executar("DELETE FROM webauthn_challenges WHERE challenge = %s", (challenge_rec.get('challenge'),), commit=True)
    
    if WEBAUTHN_DEBUG:
        print('=== DEBUG REGISTRO PASSKEY ===')
        print(f'Email: {email_usuario}')
        print(f'Dados recebidos (tipo): {type(dados)}')
        print(f'Dados recebidos (keys): {dados.keys() if isinstance(dados, dict) else "N/A"}')
        if 'id' in dados:
            print(f'ID tipo: {type(dados["id"])}, valor: {dados["id"][:20]}...')
        if 'rawId' in dados:
            print(f'rawId tipo: {type(dados["rawId"])}, valor: {dados["rawId"][:20]}...')
    
    # Guarda e remove 'transports' se existir, pois nÃ£o faz parte do RegistrationCredential
    transports = dados.pop('transports', [])

    # Converte campos base64url (strings) para bytes onde necessÃ¡rio
    # O navegador envia tudo como strings base64url
    # A biblioteca WebAuthn espera: id=string, raw_id=bytes, response.*=bytes
    
    # Guarda o ID original como string (necessÃ¡rio para o modelo)
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
    # Depois cria um objeto AuthenticatorAttestationResponse
    if 'response' in dados and isinstance(dados['response'], dict):
        resp = dados['response']
        
        # Converte clientDataJSON
        if 'clientDataJSON' in resp:
            if isinstance(resp['clientDataJSON'], str):
                client_data_json_bytes = _decode_b64url(resp['clientDataJSON'])
            else:
                client_data_json_bytes = resp['clientDataJSON']
        elif 'client_data_json' in resp:
            if isinstance(resp['client_data_json'], str):
                client_data_json_bytes = _decode_b64url(resp['client_data_json'])
            else:
                client_data_json_bytes = resp['client_data_json']
        else:
            client_data_json_bytes = b''
        
        # Converte attestationObject
        if 'attestationObject' in resp:
            if isinstance(resp['attestationObject'], str):
                attestation_object_bytes = _decode_b64url(resp['attestationObject'])
            else:
                attestation_object_bytes = resp['attestationObject']
        elif 'attestation_object' in resp:
            if isinstance(resp['attestation_object'], str):
                attestation_object_bytes = _decode_b64url(resp['attestation_object'])
            else:
                attestation_object_bytes = resp['attestation_object']
        else:
            attestation_object_bytes = b''
        
        # Cria o objeto AuthenticatorAttestationResponse
        dados['response'] = AuthenticatorAttestationResponse(
            client_data_json=client_data_json_bytes,
            attestation_object=attestation_object_bytes
        )
    
    if WEBAUTHN_DEBUG:
        print('ApÃ³s conversÃµes (registro):')
        id_val = dados.get("id")
        raw_id_val = dados.get("raw_id")
        print(f'  - id: {type(id_val)} = {id_val[:30] + "..." if isinstance(id_val, str) and len(id_val) > 30 else id_val if isinstance(id_val, str) else "N/A"}')
        print(f'  - raw_id: {type(raw_id_val)} (bytes: {len(raw_id_val) if isinstance(raw_id_val, bytes) else "N/A"} bytes)')
        if 'response' in dados:
            resp_obj = dados['response']
            print(f'  - response: {type(resp_obj)}')
            print(f'  - response.client_data_json: {type(resp_obj.client_data_json)}')
            print(f'  - response.attestation_object: {type(resp_obj.attestation_object)}')
    
    try:
        if WEBAUTHN_DEBUG:
            print(f'Tentando carregar modelo RegistrationCredential...')
            print(f'  Estrutura de dados preparada (tipos):')
            print(f'    - id: {type(dados.get("id"))}')
            print(f'    - raw_id: {type(dados.get("raw_id"))}')
            if 'response' in dados:
                print(f'    - response: {type(dados["response"])}')
        
        credencial = _load_webauthn_model(RegistrationCredential, dados)
        
        if WEBAUTHN_DEBUG:
            print(f'Modelo carregado com sucesso')
            try:
                print(f'  Tipo credencial: {type(credencial)}')
                resp_attr = getattr(credencial, "response", None)
                print(f'  Tipo credencial.response: {type(resp_attr)}')
            except Exception:
                pass
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
            print('VerificaÃ§Ã£o bem-sucedida!')
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'Erro verificaÃ§Ã£o registro WebAuthn: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro': 'verificacao_falhou', 'detalhes': str(e)}), 400

    cred_id_b64 = _b64url(verificado.credential_id)
    pubkey_b64 = _b64url(verificado.credential_public_key)
    # Salva no banco - vinculado ao EMAIL, nÃ£o ao usuario_id especÃ­fico
    # usuario_id pode ser qualquer um dos perfis do email (usamos o atual apenas como referÃªncia)
    q_ins = """
        INSERT INTO webauthn_credentials (usuario_id, email, credential_id, public_key, sign_count, transports, backup_eligible, backup_state, aaguid)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (credential_id) DO NOTHING
    """
    resultado = Database.executar(q_ins, (
        usuario['id'], email_usuario, cred_id_b64, pubkey_b64, verificado.sign_count,
        json.dumps(transports or []),
        getattr(verificado, 'backup_eligible', False),
        getattr(verificado, 'backup_state', False),
        _b64url(bytes.fromhex(verificado.aaguid.replace('-', ''))) if getattr(verificado, 'aaguid', None) else None
    ), commit=True)
    
    if WEBAUTHN_DEBUG:
        print(f'Credencial salva com sucesso! ID: {cred_id_b64}')
    
    return jsonify({'status': 'ok'})


@autenticacao_bp.route('/webauthn/anular', methods=['POST'])
def webauthn_anular():
    """Anula (desativa) uma passkey existente."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401

    dados = request.get_json(force=True)
    credencial_id = dados.get('id')

    if not credencial_id:
        return jsonify({'erro': 'id_nao_fornecido'}), 400

    # Desativa a credencial no banco, garantindo que pertence ao usuÃ¡rio logado
    q = "UPDATE webauthn_credentials SET ativo = FALSE WHERE credential_id = %s AND email = %s"
    resultado = Database.executar(q, (credencial_id, usuario['email']), commit=True)

    if resultado > 0:
        # Log da anulação (não é um login/logoff, é uma alteração)
        try:
            LogService.registrar(
                usuario_id=usuario['id'],
                tabela='webauthn_credentials',
                registro_id=None, # O ID da tabela não é o credential_id
                acao='DELETE', # Semanticamente é uma remoção
                dados_antigos={'credential_id': credencial_id, 'ativo': True},
                dados_novos={'ativo': False},
                descricao=f'Anulação de Passkey'
            )
        except Exception:
            pass
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'erro': 'falha_ao_anular'}), 500


# ============================================
# WEBAuthn - AUTENTICAÃ‡ÃƒO (LOGIN)
# ============================================
@autenticacao_bp.route('/webauthn/login/opcoes')
def webauthn_login_opcoes():
    email = request.args.get('email','').strip().lower()
    tipo = request.args.get('tipo','').strip()
    allow = None
    usuario = None
    if email and isinstance(email, str):
        # Busca usuÃ¡rio (se mÃºltiplos tipos, pode filtrar por tipo)
        q = "SELECT id, nome, email, tipo FROM usuarios WHERE email=%s " + ("AND tipo=%s" if tipo else "") + " LIMIT 1"
        params = (email, tipo) if tipo else (email,)
        usuario = Database.executar(q, params, fetchone=True)
        if not isinstance(usuario, dict) or not usuario:
            return jsonify({'erro':'usuario_nao_encontrado'}), 404
        # Pega credenciais registradas
        q2 = "SELECT credential_id FROM webauthn_credentials WHERE email=%s AND ativo=TRUE"
        email_lookup = usuario.get('email') if isinstance(usuario, dict) else None
        creds = Database.executar(q2, (email_lookup,), fetchall=True) if email_lookup else []
        if not isinstance(creds, list):
            creds = []
        if creds:
            allow = [PublicKeyCredentialDescriptor(id=_decode_b64url(c['credential_id'])) for c in creds if isinstance(c, dict) and c.get('credential_id')]
    # allow=None permite credenciais descobrÃ­veis (resident)
    options = generate_authentication_options(
        allow_credentials=allow,
        rp_id=WEBAUTHN_RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    # Guarda challenge na sessÃ£o (precisa ser bytes)
    session['webauthn_challenge'] = options.challenge
    
    if WEBAUTHN_DEBUG:
        print('=== DEBUG LOGIN OPÃ‡Ã•ES ===')
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
    
    # Tipo escolhido pode vir no corpo da requisiÃ§Ã£o (quando hÃ¡ mÃºltiplos perfis)
    tipo_escolhido = dados.pop('tipo', None)
    
    # Identifica credencial enviada (ANTES das conversÃµes - precisa ser string base64url)
    cred_id_b64 = dados.get('id') or dados.get('rawId')
    if not cred_id_b64:
        return jsonify({'erro':'credencial_sem_id'}), 400
    
    # Converte campos base64url (strings) para bytes onde necessÃ¡rio
    # O navegador envia tudo como strings base64url
    # A biblioteca WebAuthn espera: id=string, raw_id=bytes, response.*=bytes
    
    # Guarda o ID original como string (necessÃ¡rio para o modelo)
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
    # Depois cria um objeto AuthenticatorAssertionResponse
    if 'response' in dados and isinstance(dados['response'], dict):
        resp = dados['response']
        
        # Converte clientDataJSON
        if 'clientDataJSON' in resp:
            if isinstance(resp['clientDataJSON'], str):
                client_data_json_bytes = _decode_b64url(resp['clientDataJSON'])
            else:
                client_data_json_bytes = resp['clientDataJSON']
        elif 'client_data_json' in resp:
            if isinstance(resp['client_data_json'], str):
                client_data_json_bytes = _decode_b64url(resp['client_data_json'])
            else:
                client_data_json_bytes = resp['client_data_json']
        else:
            client_data_json_bytes = b''
        
        # Converte authenticatorData
        if 'authenticatorData' in resp:
            if isinstance(resp['authenticatorData'], str):
                authenticator_data_bytes = _decode_b64url(resp['authenticatorData'])
            else:
                authenticator_data_bytes = resp['authenticatorData']
        elif 'authenticator_data' in resp:
            if isinstance(resp['authenticator_data'], str):
                authenticator_data_bytes = _decode_b64url(resp['authenticator_data'])
            else:
                authenticator_data_bytes = resp['authenticator_data']
        else:
            authenticator_data_bytes = b''
        
        # Converte signature
        if 'signature' in resp:
            if isinstance(resp['signature'], str):
                signature_bytes = _decode_b64url(resp['signature'])
            else:
                signature_bytes = resp['signature']
        else:
            signature_bytes = b''
        
        # Converte userHandle se existir (opcional)
        user_handle_bytes = None
        if 'userHandle' in resp:
            if resp['userHandle'] and isinstance(resp['userHandle'], str):
                user_handle_bytes = _decode_b64url(resp['userHandle'])
            elif resp['userHandle']:
                user_handle_bytes = resp['userHandle']
        elif 'user_handle' in resp:
            if resp['user_handle'] and isinstance(resp['user_handle'], str):
                user_handle_bytes = _decode_b64url(resp['user_handle'])
            elif resp['user_handle']:
                user_handle_bytes = resp['user_handle']
        
        # Cria o objeto AuthenticatorAssertionResponse
        dados['response'] = AuthenticatorAssertionResponse(
            client_data_json=client_data_json_bytes,
            authenticator_data=authenticator_data_bytes,
            signature=signature_bytes,
            user_handle=user_handle_bytes
        )
    
    if WEBAUTHN_DEBUG:
        print('ApÃ³s conversÃµes (login):')
        print(f'  - id: {type(dados.get("id"))}')
        print(f'  - raw_id: {type(dados.get("raw_id"))}')
        if 'response' in dados:
            resp_obj = dados['response']
            print(f'  - response: {type(resp_obj)}')
            print(f'  - response.client_data_json: {type(resp_obj.client_data_json)}')
            print(f'  - response.authenticator_data: {type(resp_obj.authenticator_data)}')
            print(f'  - response.signature: {type(resp_obj.signature)}')
    
    # Encontra dono da credencial
    q = "SELECT wc.usuario_id as uid, wc.email, wc.public_key, wc.sign_count FROM webauthn_credentials wc WHERE wc.credential_id=%s AND wc.ativo=TRUE"
    reg = Database.executar(q, (cred_id_b64,), fetchone=True)
    if not isinstance(reg, dict) or not reg:
        return jsonify({'erro':'credencial_desconhecida'}), 404
    try:
        if WEBAUTHN_DEBUG:
            print(f'Tentando verificar autenticaÃ§Ã£o com challenge tipo: {type(challenge_esperado)}')
        
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
            print('VerificaÃ§Ã£o de login bem-sucedida!')
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print(f'Erro verificaÃ§Ã£o login WebAuthn: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
        return jsonify({'erro':'verificacao_falhou', 'detalhes': str(e)}), 400
    # Atualiza sign_count
    Database.executar("UPDATE webauthn_credentials SET sign_count=%s, ultimo_uso=NOW() WHERE credential_id=%s", (verificado.new_sign_count, cred_id_b64), commit=True)
    # Cria sessÃ£o normal
    email = reg.get('email')
    u_lista = Database.executar("SELECT id, nome, tipo FROM usuarios WHERE email=%s AND ativo=TRUE ORDER BY tipo", (email,), fetchall=True)
    if not isinstance(u_lista, list) or len(u_lista) == 0:
        return jsonify({'erro':'usuario_nao_encontrado'}), 404
    
    # Se mÃºltiplos tipos E nenhum tipo foi escolhido, pede para escolher
    if len(u_lista) > 1 and not tipo_escolhido:
        tipos_disp = [row.get('tipo') for row in u_lista if isinstance(row, dict)]
        return jsonify({'erro':'selecionar_tipo', 'tipos': tipos_disp}), 200
    
    # Se tipo foi escolhido, busca o usuÃ¡rio correspondente
    if tipo_escolhido:
        u = next((row for row in u_lista if row.get('tipo') == tipo_escolhido), None)
        if not u:
            return jsonify({'erro':'tipo_invalido'}), 400
    else:
        u = u_lista[0]
    
    uid = u.get('id')
    tipo = u.get('tipo')
    nome = u.get('nome')
    
    # Preenche sessÃ£o flask
    session['usuario_id'] = uid
    session['usuario_nome'] = nome
    session['usuario_email'] = email
    session['usuario_tipo'] = tipo
    session['logged_in'] = True
    
    # Log do login via passkey
    try:
        LogService.registrar_acesso(
            usuario_id=uid,
            acao='LOGIN',
            tipo_autenticacao='passkey',
            ip_usuario=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            sucesso=True,
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
    reg = Database.executar("SELECT 1 FROM webauthn_credentials WHERE email=%s AND ativo=TRUE LIMIT 1", (email,), fetchone=True)
    return jsonify({'tem': bool(reg)})


# ============================================
# WEBAuthn - DIAGNÃ“STICO (apenas em DEBUG)
# ============================================
@autenticacao_bp.route('/webauthn/diagnostico')
def webauthn_diagnostico():
    """Endpoint de diagnÃ³stico para verificar configuraÃ§Ã£o WebAuthn (apenas em modo DEBUG)."""
    if not DEBUG:
        return jsonify({'erro': 'disponivel_apenas_em_debug'}), 403
    
    # Pega informaÃ§Ãµes do request
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
# VERIFICAR SESSÃƒO (FUNÃ‡ÃƒO AUXILIAR)
# ============================================

def verificar_sessao():
    """
    Verifica se o usuÃ¡rio estÃ¡ autenticado de forma stateless, lendo da sessÃ£o.
    
    Retorna:
        dict ou None: Dados do usuÃ¡rio se autenticado, None caso contrÃ¡rio
    """
    
    # Verifica se a sessÃ£o contÃ©m as chaves essenciais
    if not all(key in session for key in ['usuario_id', 'usuario_nome', 'usuario_email', 'usuario_tipo', 'logged_in']):
        return None
    
    # Verifica se o marcador de login Ã© verdadeiro
    if not session.get('logged_in'):
        return None
    
    # SessÃ£o vÃ¡lida! Retorna os dados do usuÃ¡rio a partir da sessÃ£o
    return {
        'id': session.get('usuario_id'),
        'nome': session.get('usuario_nome'),
        'email': session.get('usuario_email'),
        'tipo': session.get('usuario_tipo')
    }


# ============================================
# VERIFICAR PERMISSÃƒO (FUNÃ‡ÃƒO AUXILIAR)
# ============================================

def verificar_permissao(tipos_permitidos):
    """
    Verifica se o usuÃ¡rio tem permissÃ£o para acessar uma pÃ¡gina
    
    ParÃ¢metros:
        tipos_permitidos (list): Lista de tipos de usuÃ¡rio permitidos
                                 Ex: ['administrador', 'escola']
    
    Retorna:
        dict ou None: Dados do usuÃ¡rio se tem permissÃ£o, None caso contrÃ¡rio
    """
    
    # Verifica se o usuÃ¡rio estÃ¡ autenticado
    usuario = verificar_sessao()
    if not usuario:
        return None
    
    # Verifica se o tipo do usuÃ¡rio estÃ¡ na lista de permitidos
    if usuario['tipo'] not in tipos_permitidos:
        return None
    
    # UsuÃ¡rio tem permissÃ£o!
    return usuario


# ============================================
# FIM DO MÃ“DULO DE AUTENTICAÃ‡ÃƒO
# ============================================

