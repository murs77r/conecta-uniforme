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
from utils import executar_query, gerar_codigo_acesso, gerar_token_sessao, enviar_codigo_acesso, validar_email
from config import CODIGO_ACESSO_DURACAO_HORAS, SESSAO_DURACAO_DIAS, DEBUG, WEBAUTHN_RP_ID, WEBAUTHN_RP_NAME, WEBAUTHN_ORIGIN, WEBAUTHN_DEBUG
import os, base64, json
from webauthn import (generate_registration_options, options_to_json, verify_registration_response, generate_authentication_options, verify_authentication_response)
from webauthn.helpers.structs import (PublicKeyCredentialRpEntity, UserVerificationRequirement, PublicKeyCredentialDescriptor, RegistrationCredential, AuthenticationCredential,)

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

def _decode_b64url(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


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
        return render_template('auth/solicitar_codigo.html', passkeys_ativado=True)
    
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
        return render_template('auth/solicitar_codigo.html', email=email, tipos_disponiveis=tipos_disponiveis, abrir_modal_tipo=True)

    # Determina o usuário alvo
    if len(usuarios_encontrados) == 1:
        usuario = usuarios_encontrados[0]
    else:
        usuario = next((u for u in usuarios_encontrados if u['tipo'] == tipo_escolhido), None)
        if not usuario:
            flash('Tipo de usuário inválido para este email.', 'danger')
            return render_template('auth/solicitar_codigo.html')
    
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

    # ID de usuário deve ser bytes estáveis (usar id numérico convertido)
    user_id_bytes = str(usuario['id']).encode('utf-8')

    # Recupera credenciais existentes para excluir de excludeCredentials
    q = "SELECT credential_id FROM webauthn_credentials WHERE usuario_id = %s AND ativo = TRUE"
    creds = executar_query(q, (usuario['id'],), fetchall=True) or []
    if not isinstance(creds, list):
        creds = []
    exclude = [PublicKeyCredentialDescriptor(id=_decode_b64url(c['credential_id'])) for c in creds if isinstance(c, dict) and c.get('credential_id')]

    options = generate_registration_options(
        rp=PublicKeyCredentialRpEntity(id=WEBAUTHN_RP_ID, name=WEBAUTHN_RP_NAME),
        user_id=user_id_bytes,
        user_name=usuario['email'],
        user_display_name=usuario['nome'],
        exclude_credentials=exclude,
        authenticator_selection=None,
        attestation="none",
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    _challenges_registro[usuario['id']] = options.challenge
    return jsonify(json.loads(options_to_json(options)))


@autenticacao_bp.route('/webauthn/registro', methods=['POST'])
def webauthn_registro():
    """Recebe resposta de criação de credencial e valida."""
    usuario = verificar_sessao()
    if not usuario:
        return jsonify({'erro': 'nao_autenticado'}), 401
    dados = request.get_json(force=True)
    challenge_esperado = _challenges_registro.get(usuario['id'])
    if not challenge_esperado:
        return jsonify({'erro': 'challenge_expirado'}), 400
    try:
        verificado = verify_registration_response(
            credential=RegistrationCredential.parse_raw(json.dumps(dados)),
            expected_challenge=challenge_esperado,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
        )
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print('Erro verificação registro WebAuthn:', e)
        return jsonify({'erro': 'verificacao_falhou'}), 400

    cred_id_b64 = _b64url(verificado.credential_id)
    pubkey_b64 = _b64url(verificado.credential_public_key)
    # Salva no banco
    q_ins = """
        INSERT INTO webauthn_credentials (usuario_id, credential_id, public_key, sign_count, transports, backup_eligible, backup_state, aaguid)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (credential_id) DO NOTHING
    """
    executar_query(q_ins, (
        usuario['id'], cred_id_b64, pubkey_b64, verificado.sign_count,
        json.dumps(dados.get('transports') or []),
        getattr(verificado, 'backup_eligible', False),
        getattr(verificado, 'backup_state', False),
        _b64url(verificado.aaguid) if getattr(verificado, 'aaguid', None) else None
    ), commit=True)
    _challenges_registro.pop(usuario['id'], None)
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
    if email:
        # Busca usuário (se múltiplos tipos, pode filtrar por tipo)
        q = "SELECT id, nome, email, tipo FROM usuarios WHERE email=%s " + ("AND tipo=%s" if tipo else "") + " LIMIT 1"
        params = (email, tipo) if tipo else (email,)
        usuario = executar_query(q, params, fetchone=True)
        if not usuario:
            return jsonify({'erro':'usuario_nao_encontrado'}), 404
        # Pega credenciais registradas
        q2 = "SELECT credential_id FROM webauthn_credentials WHERE usuario_id=%s AND ativo=TRUE"
        usuario_id = usuario.get('id') if isinstance(usuario, dict) else None
        creds = executar_query(q2, (usuario_id,), fetchall=True) if usuario_id is not None else []
        if not creds:
            creds = []
        if not isinstance(creds, list):
            creds = []
        if creds:
            allow = [PublicKeyCredentialDescriptor(id=_decode_b64url(c['credential_id'])) for c in creds if isinstance(c, dict) and c.get('credential_id')]
    # allow=None permite credenciais descobríveis (resident)
    options = generate_authentication_options(
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
        rp_id=WEBAUTHN_RP_ID,
    )
    # Guarda challenge na sessão
    session['webauthn_challenge'] = options.challenge
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
    # Identifica credencial enviada
    cred_id_b64 = dados.get('id') or dados.get('rawId')
    if not cred_id_b64:
        return jsonify({'erro':'credencial_sem_id'}), 400
    # Encontra dono da credencial
    q = "SELECT wc.usuario_id as uid, wc.public_key, wc.sign_count, u.email, u.tipo FROM webauthn_credentials wc JOIN usuarios u ON u.id = wc.usuario_id WHERE wc.credential_id=%s AND wc.ativo=TRUE"
    reg = executar_query(q, (cred_id_b64,), fetchone=True)
    if not isinstance(reg, dict) or not reg:
        return jsonify({'erro':'credencial_desconhecida'}), 404
    try:
        verificado = verify_authentication_response(
            credential=AuthenticationCredential.parse_raw(json.dumps(dados)),
            expected_challenge=challenge_esperado,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
            credential_public_key=_decode_b64url(reg.get('public_key','')),
            credential_current_sign_count=reg.get('sign_count', 0),
        )
    except Exception as e:
        if WEBAUTHN_DEBUG:
            print('Erro verificação login WebAuthn:', e)
        return jsonify({'erro':'verificacao_falhou'}), 400
    # Atualiza sign_count
    executar_query("UPDATE webauthn_credentials SET sign_count=%s, ultimo_uso=NOW() WHERE credential_id=%s", (verificado.new_sign_count, cred_id_b64), commit=True)
    # Cria sessão normal
    uid = reg.get('uid')
    email = reg.get('email')
    tipo = reg.get('tipo')
    # Gera token sessão
    token_sessao = gerar_token_sessao()
    data_expiracao_sessao = datetime.now() + timedelta(days=SESSAO_DURACAO_DIAS)
    executar_query("INSERT INTO sessoes (usuario_id, token, data_expiracao) VALUES (%s,%s,%s)", (uid, token_sessao, data_expiracao_sessao), commit=True)
    # Preenche sessão flask
    session['usuario_id'] = uid
    session['usuario_nome'] = session.get('usuario_nome')  # preserva se existir
    # Busca nome
    uinfo = executar_query("SELECT nome FROM usuarios WHERE id=%s", (uid,), fetchone=True)
    if isinstance(uinfo, dict) and 'nome' in uinfo:
        session['usuario_nome'] = uinfo.get('nome')
    session['usuario_email'] = email
    session['usuario_tipo'] = tipo
    session['token_sessao'] = token_sessao
    return jsonify({'status':'ok'})


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
