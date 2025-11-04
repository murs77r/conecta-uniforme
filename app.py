"""
============================================
CONECTA UNIFORME - APLICAÇÃO PRINCIPAL
============================================
Este é o arquivo principal que inicia a aplicação Flask
e integra todos os módulos (microfront-ends).

Para executar:
    python app.py
"""

from flask import Flask, render_template, redirect, url_for, session
from config import SECRET_KEY, DEBUG, PORT
from modules.autenticacao import autenticacao_bp, verificar_sessao
from modules.usuarios import usuarios_bp
from modules.escolas import escolas_bp
from modules.fornecedores import fornecedores_bp
from modules.produtos import produtos_bp
from modules.pedidos import pedidos_bp
from modules.repasses import repasses_bp
from modules.gestores import gestores_bp

# ============================================
# CRIAÇÃO DA APLICAÇÃO FLASK
# ============================================
app = Flask(__name__)

# Configura a chave secreta para sessões
app.secret_key = SECRET_KEY

# Configura modo debug
app.config['DEBUG'] = DEBUG

# ============================================
# REGISTRO DOS BLUEPRINTS (MICROFRONT-ENDS)
# ============================================
# Cada blueprint funciona de forma independente
# Isso permite trabalhar cada módulo separadamente

# RF02 - Autenticação e Acesso
app.register_blueprint(autenticacao_bp)

# RF01 - Cadastro de Usuários
app.register_blueprint(usuarios_bp)

# RF04 - Gerenciar Escolas
app.register_blueprint(escolas_bp)

# RF05 - Gerenciar Fornecedores
app.register_blueprint(fornecedores_bp)

# RF03 - Gerenciar Produtos
app.register_blueprint(produtos_bp)

# RF06 - Gerenciar Pedidos
app.register_blueprint(pedidos_bp)

# RF07 - Gerenciar Repasses Financeiros
app.register_blueprint(repasses_bp)

# RF04.x - Gerenciar Gestores Escolares
app.register_blueprint(gestores_bp)


# ============================================
# ROTA PRINCIPAL (HOME)
# ============================================

@app.route('/')
def index():
    """
    Página inicial do sistema
    Redireciona conforme o estado de autenticação
    """
    
    # Verifica se o usuário está autenticado
    usuario = verificar_sessao()
    
    # Se não estiver autenticado, vai para o login
    if not usuario:
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Se estiver autenticado, vai para a home
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """
    Dashboard principal após login
    Exibe informações personalizadas conforme o tipo de usuário
    """
    
    # Verifica se o usuário está autenticado
    usuario = verificar_sessao()
    
    # Se não estiver autenticado, redireciona para login
    if not usuario:
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Renderiza a home passando os dados do usuário
    return render_template('home.html', usuario=usuario)


# ============================================
# FAVICON
# ============================================

@app.route('/favicon.ico')
def favicon():
    """Redireciona o favicon para o arquivo em static (evita 404 no navegador)."""
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
# Torna algumas variáveis disponíveis em todos os templates

@app.context_processor
def injetar_variaveis():
    """
    Injeta variáveis que estarão disponíveis em todos os templates
    """
    
    # Verifica se o usuário está autenticado
    usuario = verificar_sessao()
    
    return {
        'usuario_logado': usuario,
        'session': session
    }


# ============================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ============================================

if __name__ == '__main__':
    """
    Inicia o servidor Flask quando o arquivo é executado diretamente
    """
    
    print("=" * 50)
    print("CONECTA UNIFORME - Sistema Iniciado")
    print("=" * 50)
    print(f"Acesse: http://localhost:{PORT}")
    print("Pressione CTRL+C para encerrar")
    print("=" * 50)
    
    # Inicia o servidor
    app.run(
        host='0.0.0.0',  # Aceita conexões de qualquer IP
        port=PORT,       # Porta configurada
        debug=DEBUG      # Modo debug configurado
    )


# ============================================
# FIM DA APLICAÇÃO PRINCIPAL
# ============================================
