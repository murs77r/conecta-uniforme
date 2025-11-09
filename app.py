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
from modules.fornecedores import fornecedores_bp
from modules.produtos import produtos_bp
from modules.pedidos import pedidos_bp
from modules.repasses import repasses_bp
from utils import conectar_banco

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

# RF04 - Gerenciar Escolas e Gestores Escolares
app.register_blueprint(escolas_bp)

# RF05 - Gerenciar Fornecedores
app.register_blueprint(fornecedores_bp)

# RF03 - Gerenciar Produtos
app.register_blueprint(produtos_bp)

# RF06 - Gerenciar Pedidos
app.register_blueprint(pedidos_bp)

# RF07 - Gerenciar Repasses Financeiros
app.register_blueprint(repasses_bp)


# ============================================
# ROTA PRINCIPAL (HOME)
# ============================================

@app.route('/')
def index():
    """
    Página inicial do sistema
    Redireciona conforme o estado de autenticação
    """
    # 1) Verifica se o banco está ativo; se não, exibe página de carregamento
    if not banco_esta_ativo():
        return render_template('carregando.html')

    # 2) Banco ativo: segue fluxo normal de autenticação
    usuario = verificar_sessao()
    if not usuario:
        return redirect(url_for('autenticacao.solicitar_codigo'))
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
# HEALTHCHECK DO BANCO DE DADOS
# ============================================

def banco_esta_ativo() -> bool:
    """Tenta abrir uma conexão simples e executar SELECT 1."""
    try:
        conexao = conectar_banco()
        if not conexao:
            return False
        cur = None
        try:
            cur = conexao.cursor()
            cur.execute('SELECT 1')
            return True
        finally:
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
    """Endpoint para o front verificar se o banco já está pronto."""
    if banco_esta_ativo():
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 503


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
    
    # Rótulos amigáveis para exibição de tipos de usuário
    ROTULOS_TIPOS = {
        'administrador': 'Administrador',
        'escola': 'Escola',
        'fornecedor': 'Fornecedor',
        'responsavel': 'Responsável',
    }

    return {
        'usuario_logado': usuario,
        'session': session,
        # Variáveis de autenticação usadas em templates
        'CODIGO_ACESSO_TAMANHO': CODIGO_ACESSO_TAMANHO,
        'CODIGO_ACESSO_DURACAO_HORAS': CODIGO_ACESSO_DURACAO_HORAS,
        # Mapeamento global para labels amigáveis
        'ROTULOS_TIPOS': ROTULOS_TIPOS,
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
