"""
============================================
CONECTA UNIFORME - APLICAÇÃO PRINCIPAL
============================================
Este é o arquivo principal que inicia a aplicação Flask
e integra todos os módulos (microfront-ends).

Para executar:
    python app.py
"""

from flask import Flask, render_template, redirect, url_for, session, jsonify
from config import SECRET_KEY, DEBUG, PORT, CODIGO_ACESSO_TAMANHO, CODIGO_ACESSO_DURACAO_HORAS
from modules.autenticacao import autenticacao_bp, verificar_sessao
from modules.usuarios import usuarios_bp
from modules.escolas import escolas_bp
from modules.gestores import gestores_bp
from modules.fornecedores import fornecedores_bp
from modules.produtos import produtos_bp
from modules.pedidos import pedidos_bp
from core.database import Database

# ============================================
# CRIAÇÃO DA APLICAÇÃO FLASK
# ============================================
app = Flask(__name__)

# Define chave secreta para assinatura de cookies de sessão (SESSION_COOKIE_HTTPONLY e SESSION_COOKIE_SECURE)
app.secret_key = SECRET_KEY

# Ativa modo de depuração: recarregamento automático e mensagens de erro detalhadas
app.config['DEBUG'] = DEBUG

# ============================================
# REGISTRO DOS BLUEPRINTS (MÓDULOS)
# ============================================
# Cada blueprint representa um módulo funcional independente (padrão micro frontend)
# permitindo desenvolvimento e manutenção isolados de cada funcionalidade

# RF02 - Autenticação e Acesso
app.register_blueprint(autenticacao_bp)

# RF01 - Cadastro de Usuários
app.register_blueprint(usuarios_bp)

# RF03 - Gerenciar Escolas
app.register_blueprint(escolas_bp)

# RF04 - Gerenciar Gestores Escolares
app.register_blueprint(gestores_bp)

# RF05 - Gerenciar Fornecedores
app.register_blueprint(fornecedores_bp)

# RF06 - Gerenciar Produtos
app.register_blueprint(produtos_bp)

# RF08 - Gerenciar Pedidos
app.register_blueprint(pedidos_bp)


# ============================================
# ROTA PRINCIPAL (HOME)
# ============================================

@app.route('/')
def index():
    """
    Rota raiz: Implementa healthcheck do banco antes de redirecionar
    
    Fluxo:
    1. Verifica conectividade com PostgreSQL via banco_esta_ativo()
    2. Se banco indisponível: exibe tela de carregamento com polling JS
    3. Se banco OK: segue fluxo de autenticação padrão (verificar_sessao)
    """
    # Healthcheck: evita erros de sessão se o banco estiver iniciando (ex: Docker)
    if not banco_esta_ativo():
        return render_template('carregando.html')

    # Banco disponível: valida sessão do usuário via cookie
    usuario = verificar_sessao()
    if not usuario:
        return redirect(url_for('autenticacao.solicitar_codigo'))
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """
    Página inicial pós-autenticação
    
    Exibe menu principal com opções de navegação baseadas no tipo de usuário.
    Evita acesso direto sem autenticação (guarda de rota).
    """
    # Valida sessão via verificação de cookies assinados pelo Flask
    usuario = verificar_sessao()
    
    # Sessão inválida: redireciona para fluxo de autenticação
    if not usuario:
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Sessão válida: exibe página inicial com menu de navegação
    return render_template('home.html')


# ============================================
# HEALTHCHECK DO BANCO DE DADOS
# ============================================

def banco_esta_ativo() -> bool:
    """
    Verifica disponibilidade do PostgreSQL executando query simples.
    
    Utilizado para:
    - Evitar erros ao carregar app durante inicialização do container Docker
    - Implementar retry logic no frontend via polling
    - Garantir que migrations foram aplicadas antes de aceitar requests
    
    Returns:
        bool: True se SELECT 1 executou com sucesso, False caso contrário
    """
    try:
        conexao = Database.conectar()
        if not conexao:
            return False
        cur = None
        try:
            cur = conexao.cursor()
            cur.execute('SELECT 1')
            return True
        finally:
            # Garante fechamento de recursos mesmo em caso de exceção
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
            try:
                conexao.close()
            except Exception:
                pass
    except Exception:
        return False


@app.route('/health/db')
def health_db():
    """
    Endpoint HTTP para healthcheck do banco (usado pelo frontend e orquestradores).
    
    Frontend faz polling neste endpoint quando detecta banco indisponível.
    Retorna JSON com status HTTP 503 (Service Unavailable) se banco offline.
    """
    if banco_esta_ativo():
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 503


# ============================================
# FAVICON
# ============================================

@app.route('/favicon.ico')
def favicon():
    """
    Serve favicon via redirect para static folder.
    
    Evita logs de erro 404 repetidos em navegadores que buscam /favicon.ico
    automaticamente na raiz do domínio.
    """
    return redirect(url_for('static', filename='favicon.svg'))


# ============================================
# PÁGINA DE ERRO 404
# ============================================

@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    """
    Página exibida quando uma rota não é encontrada
    """
    return render_template('erro_404.html'), 404


# ============================================
# PÁGINA DE ERRO 500
# ============================================

@app.errorhandler(500)
def erro_servidor(erro):
    """
    Página exibida quando ocorre um erro no servidor
    """
    return render_template('erro_500.html'), 500


# ============================================
# CONTEXT PROCESSOR
# ============================================
# Injeta variáveis globais acessíveis em todos os templates Jinja2 renderizados

@app.context_processor
def injetar_variaveis():
    """
    Context processor: disponibiliza dados em todos os templates sem passar explicitamente.
    
    Variáveis injetadas:
    - usuario_logado: dados do usuário autenticado (None se não autenticado)
    - session: objeto de sessão Flask (cookies)
    - CODIGO_ACESSO_*: constantes de configuração de autenticação
    - ROTULOS_TIPOS: mapeamento de tipos técnicos para labels UI amigáveis
    """
    # Busca dados do usuário na sessão atual (via cookies assinados)
    usuario = verificar_sessao()
    
    # Mapeamento para exibir tipos de usuário de forma humanizada no frontend
    ROTULOS_TIPOS = {
        'administrador': 'Administrador',
        'escola': 'Escola',
        'fornecedor': 'Fornecedor',
        'responsavel': 'Responsável',
    }

    return {
        'usuario_logado': usuario,
        'session': session,
        # Configurações de autenticação expostas ao template
        'CODIGO_ACESSO_TAMANHO': CODIGO_ACESSO_TAMANHO,
        'CODIGO_ACESSO_DURACAO_HORAS': CODIGO_ACESSO_DURACAO_HORAS,
        # Labels para tipos de usuário
        'ROTULOS_TIPOS': ROTULOS_TIPOS,
    }


# ============================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ============================================

if __name__ == '__main__':
    """
    Entry point: executa servidor de desenvolvimento Flask (Werkzeug).
    
    Em produção, usar WSGI server (Gunicorn, uWSGI) ao invés de app.run().
    """
    
    print("=" * 50)
    print("CONECTA UNIFORME - Sistema Iniciado")
    print("=" * 50)
    print(f"Acesse: http://localhost:{PORT}")
    print("Pressione CTRL+C para encerrar")
    print("=" * 50)
    
    # Inicia servidor Werkzeug (desenvolvimento apenas)
    # host='0.0.0.0' permite acesso externo (necessário para Docker)
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG
    )


# ============================================
# FIM DA APLICAÇÃO PRINCIPAL
# ============================================
