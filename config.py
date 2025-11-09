"""
============================================
CONECTA UNIFORME - CONFIGURAÇÃO VIA VARIÁVEIS DE AMBIENTE
============================================
Carrega configurações do arquivo .env usando python-dotenv.
Todas as configurações são tipadas e validadas com valores padrão.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Localiza e carrega arquivo .env da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ============================================
# CONFIGURAÇÕES DO BANCO DE DADOS POSTGRESQL
# ============================================
# Parâmetros de conexão via psycopg2 (PostgreSQL adapter)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'conecta_uniforme'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '3'))  # Timeout em segundos para evitar travamento
}

# ============================================
# CONFIGURAÇÕES DO SERVIDOR SMTP (ENVIO DE EMAIL)
# ============================================
# Credenciais e parâmetros para envio via smtplib (TLS obrigatório para segurança)
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', '587')),
    'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes', 'on'),
    'username': os.getenv('SMTP_USERNAME', ''),
    'password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('SMTP_FROM_EMAIL', 'no-reply@example.com'),
    'from_name': os.getenv('SMTP_FROM_NAME', 'Conecta Uniforme'),
    'timeout': int(os.getenv('SMTP_TIMEOUT', '10'))  # Timeout de rede para evitar blocking infinito
}

# ============================================
# CONFIGURAÇÕES DA APLICAÇÃO FLASK
# ============================================
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')  # Chave para assinatura de cookies (SESSION, CSRF)
DEBUG = os.getenv('DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')  # Modo desenvolvimento com traceback
PORT = int(os.getenv('PORT', '5000'))  # Porta do servidor Werkzeug

# ============================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO
# ============================================
CODIGO_ACESSO_DURACAO_HORAS = int(os.getenv('CODIGO_ACESSO_DURACAO_HORAS', '24'))  # TTL do código numérico
CODIGO_ACESSO_TAMANHO = int(os.getenv('CODIGO_ACESSO_TAMANHO', '6'))  # Quantidade de dígitos (ex: 123456)
SESSAO_DURACAO_DIAS = int(os.getenv('SESSAO_DURACAO_DIAS', '7'))  # Validade do cookie de sessão após login

# ============================================
# CONFIGURAÇÕES DE WEBAUTHN / PASSKEYS (FIDO2)
# ============================================
# RP_ID: Domínio ou hostname do Relying Party (deve corresponder ao origin sem protocolo)
# Em produção, usar domínio real (ex: 'app.conecta.com'). Em dev, 'localhost' é válido.
# Para testes em dispositivos móveis, configurar domínio local no /etc/hosts (ex: 'dev.conecta.local')
WEBAUTHN_RP_ID = os.getenv('WEBAUTHN_RP_ID', 'localhost')
WEBAUTHN_RP_NAME = os.getenv('WEBAUTHN_RP_NAME', 'Conecta Uniforme')
WEBAUTHN_ORIGIN = os.getenv('WEBAUTHN_ORIGIN', f'http://localhost:{PORT}')  # Origin completo com protocolo
WEBAUTHN_ALLOW_ATTESTATION = os.getenv('WEBAUTHN_ALLOW_ATTESTATION', 'false').lower() in ('1','true','yes','on')
WEBAUTHN_DEBUG = os.getenv('WEBAUTHN_DEBUG', 'true').lower() in ('1','true','yes','on')  # Logs detalhados de verificação

# Diagnóstico: imprime configurações WebAuthn na inicialização se DEBUG ativo
if DEBUG:
    print("=" * 70)
    print("CONFIGURAÇÃO WEBAUTHN CARREGADA:")
    print(f"  WEBAUTHN_RP_ID    : {WEBAUTHN_RP_ID}")
    print(f"  WEBAUTHN_RP_NAME  : {WEBAUTHN_RP_NAME}")
    print(f"  WEBAUTHN_ORIGIN   : {WEBAUTHN_ORIGIN}")
    print(f"  WEBAUTHN_DEBUG    : {WEBAUTHN_DEBUG}")
    print("=" * 70)

# ============================================
# CONFIGURAÇÕES DE PAGINAÇÃO
# ============================================
ITENS_POR_PAGINA = int(os.getenv('ITENS_POR_PAGINA', '20'))  # Quantidade padrão de registros por página em listagens

# ============================================
# CONFIGURAÇÕES DE UPLOAD DE ARQUIVOS
# ============================================
DEFAULT_UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(DEFAULT_UPLOAD_FOLDER))  # Diretório para armazenar uploads
EXTENSOES_PERMITIDAS = set(os.getenv('EXTENSOES_PERMITIDAS', 'png,jpg,jpeg,gif').split(','))  # Whitelist de tipos MIME
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', str(5 * 1024 * 1024)))  # Tamanho máximo em bytes (padrão: 5MB)

# ============================================
# CONFIGURAÇÕES DE REPASSE FINANCEIRO
# ============================================
TAXA_PLATAFORMA_PERCENTUAL = float(os.getenv('TAXA_PLATAFORMA_PERCENTUAL', '15.0'))  # % deduzida do valor bruto antes de repassar ao fornecedor

# ============================================
# MENSAGENS PADRÃO DO SISTEMA
# ============================================
# Dicionário centralizado de mensagens para consistência de UX e facilitar i18n futuro
MENSAGENS = {
    'sucesso_cadastro': 'Cadastro realizado com sucesso!',
    'sucesso_edicao': 'Registro atualizado com sucesso!',
    'sucesso_exclusao': 'Registro excluído com sucesso!',
    'erro_geral': 'Ocorreu um erro. Tente novamente.',
    'erro_permissao': 'Você não tem permissão para esta ação.',
    'codigo_enviado': 'Código de acesso enviado para seu email!',
    'codigo_invalido': 'Código de acesso inválido ou expirado.',
    'login_sucesso': 'Login realizado com sucesso!',
    'logout_sucesso': 'Logout realizado com sucesso!'
}
