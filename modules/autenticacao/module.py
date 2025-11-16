"""
============================================
RF02 - GERENCIAR AUTENTICAÇÃO E ACESSO
============================================
Este módulo é responsável por:
- RF02.1: Solicitar código de acesso
- RF02.2: Validar código de acesso

Controla o processo de autenticação e autorização de usuários, garantindo segurança no acesso ao sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from core.database import Database
from core.services import EmailService, UtilsService, ValidacaoService, LogService
from config import CODIGO_ACESSO_DURACAO_HORAS, SESSAO_DURACAO_DIAS, DEBUG

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================
# Este blueprint funciona de forma independente
autenticacao_bp = Blueprint('autenticacao', __name__, url_prefix='/auth')

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
    rows = Database.executar(q, (email,), fetchall=True)
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
    if not ValidacaoService.validar_email(email):
        flash('Email inválido. Verifique e tente novamente.', 'danger')
        return render_template('auth/solicitar_codigo.html')
    
    # Busca todos usuários (tipos) para o email
    query_usuario = "SELECT id, nome, email, tipo, ativo FROM usuarios WHERE email = %s AND ativo = TRUE ORDER BY tipo"
    usuarios_encontrados = Database.executar(query_usuario, (email,), fetchall=True)
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
            LogService.registrar_acesso(
                usuario_id=usuario['id'],
                acao='LOGIN',
                tipo_autenticacao='codigo',
                ip_usuario=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                sucesso=False,  # Ainda não completou o login, apenas selecionou perfil
                descricao=f'Seleção de perfil para login (tipo={usuario.get("tipo")})'
            )
        except Exception:
            pass
    
    # Gera um código de acesso aleatório (6 dígitos)
    codigo = UtilsService.gerar_codigo_acesso()
    
    # Calcula a data de expiração do código (24 horas)
    data_expiracao = datetime.now() + timedelta(hours=CODIGO_ACESSO_DURACAO_HORAS)
    
    # Salva o código no banco de dados
    query_inserir = """
        INSERT INTO codigos_acesso (usuario_id, codigo, data_expiracao)
        VALUES (%s, %s, %s)
    """
    resultado = Database.executar(query_inserir, (usuario['id'], codigo, data_expiracao), commit=True)
    
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
    sucesso_envio = EmailService().enviar_codigo_acesso(email, codigo, usuario['nome'])
    
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
        return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email=aviso_email, debug=DEBUG)
    
    # Se for POST, processa o formulário
    # Pega os dados digitados
    email = request.form.get('email', '').strip().lower()
    tipo = request.form.get('tipo', '').strip()
    codigo_digitado = request.form.get('codigo', '').strip()

    # MODO DE DESENVOLVIMENTO: Login rápido com qualquer usuário
    if DEBUG and codigo_digitado == "000000":
        # Busca o primeiro usuário ativo com o email e tipo fornecidos
        query_dev_login = "SELECT id, nome, email, tipo FROM usuarios WHERE email = %s AND tipo = %s AND ativo = TRUE LIMIT 1"
        usuario = Database.executar(query_dev_login, (email, tipo), fetchone=True)

        if usuario:
            session['usuario_id'] = usuario.get('id')
            session['usuario_nome'] = usuario.get('nome')
            session['usuario_email'] = usuario.get('email')
            session['usuario_tipo'] = usuario.get('tipo')
            session['logged_in'] = True
            
            flash(f"Login de desenvolvedor como {usuario['nome']}!", 'warning')
            return redirect(url_for('home'))
        else:
            flash('Usuário de desenvolvedor não encontrado para este email/tipo.', 'danger')
            return render_template('auth/validar_codigo.html', email=email, tipo=tipo, aviso_email='0', debug=DEBUG)
    
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
    registro_codigo = Database.executar(query_codigo, (email, tipo, codigo_digitado), fetchone=True)
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
        Database.executar(query_marcar_usado, (registro_codigo['id'],), commit=True)
    
    # Salva os dados do usuário na sessão do Flask
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
    # Registra o logoff antes de limpar a sessão
    if session.get('logged_in') and session.get('usuario_id'):
        try:
            LogService.registrar_acesso(
                usuario_id=session.get('usuario_id'),
                acao='LOGOFF',
                tipo_autenticacao=None,
                ip_usuario=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                sucesso=True,
                descricao='Logout realizado pelo usuário'
            )
        except Exception:
            pass
    
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
    Verifica se o usuário está autenticado de forma stateless, lendo da sessão.
    
    Retorna:
        dict ou None: Dados do usuário se autenticado, None caso contrário
    """
    
    # Verifica se a sessão contém as chaves essenciais
    if not all(key in session for key in ['usuario_id', 'usuario_nome', 'usuario_email', 'usuario_tipo', 'logged_in']):
        return None
    
    # Verifica se o marcador de login é verdadeiro
    if not session.get('logged_in'):
        return None
    
    # Sessão válida! Retorna os dados do usuário a partir da sessão
    return {
        'id': session.get('usuario_id'),
        'nome': session.get('usuario_nome'),
        'email': session.get('usuario_email'),
        'tipo': session.get('usuario_tipo')
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
