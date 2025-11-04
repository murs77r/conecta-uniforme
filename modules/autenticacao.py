"""
============================================
RF02 - GERENCIAR AUTENTICAÇÃO E ACESSO
============================================
Este módulo é responsável por:
- RF02.1: Solicitar Código de Acesso
- RF02.2: Validar Código de Acesso

Controla o processo de autenticação e autorização de usuários, garantindo segurança no acesso ao sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from utils import executar_query, gerar_codigo_acesso, gerar_token_sessao, enviar_codigo_acesso, validar_email
from config import CODIGO_ACESSO_DURACAO_HORAS, SESSAO_DURACAO_DIAS, DEBUG

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================
# Este blueprint funciona de forma independente
autenticacao_bp = Blueprint('autenticacao', __name__, url_prefix='/auth')


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
        return render_template('auth/solicitar_codigo.html')
    
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
    
    # Verifica se o email existe
    if not usuarios_encontrados:
        flash('Email não cadastrado no sistema.', 'danger')
        return render_template('auth/solicitar_codigo.html')

    # Se houver mais de um tipo e nenhum escolhido ainda, mostra modal de seleção
    if len(usuarios_encontrados) > 1 and not tipo_escolhido:
        tipos_disponiveis = [u['tipo'] for u in usuarios_encontrados]
        # Renderiza a mesma página com o modal para seleção de tipo
        return render_template('auth/solicitar_codigo.html', email=email, tipos_disponiveis=tipos_disponiveis, abrir_modal_tipo=True)

    # Determina o usuário alvo
    if len(usuarios_encontrados) == 1:
        usuario = usuarios_encontrados[0]
    else:
        # Procura pelo tipo escolhido
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
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email=aviso_email, debug=DEBUG)
    
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
    
    # Verifica se o código existe e está válido
    if not registro_codigo:
        flash('Código inválido ou já utilizado.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Verifica se o código expirou
    data_expiracao = registro_codigo['data_expiracao']
    if datetime.now() > data_expiracao:
        flash('Código expirado. Solicite um novo código.', 'danger')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica se o usuário está ativo
    if not registro_codigo['ativo']:
        flash('Usuário inativo. Entre em contato com o administrador.', 'danger')
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
    # Código válido! Marca como usado
    query_marcar_usado = "UPDATE codigos_acesso SET usado = TRUE WHERE id = %s"
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
    executar_query(query_sessao, (registro_codigo['usuario_id'], token_sessao, data_expiracao_sessao), commit=True)
    
    # Salva os dados do usuário na sessão do Flask
    session['usuario_id'] = registro_codigo['usuario_id']
    session['usuario_nome'] = registro_codigo['nome']
    session['usuario_email'] = registro_codigo['email']
    session['usuario_tipo'] = registro_codigo['tipo']
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
    
    # Verifica se a sessão existe
    if not sessao_db:
        session.clear()
        return None
    
    # Verifica se a sessão expirou
    if datetime.now() > sessao_db['data_expiracao']:
        session.clear()
        return None
    
    # Verifica se o usuário está ativo
    if not sessao_db['usuario_ativo']:
        session.clear()
        return None
    
    # Sessão válida! Retorna os dados do usuário
    return {
        'id': sessao_db['usuario_id'],
        'nome': sessao_db['nome'],
        'email': sessao_db['email'],
        'tipo': sessao_db['tipo']
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
