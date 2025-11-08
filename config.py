"""
============================================
CONECTA UNIFORME - ARQUIVO DE CONFIGURAÇÃO VIA .env
============================================
Este arquivo lê as configurações do ambiente (.env/variáveis) para uso pela aplicação.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env localizado na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ============================================
# CONFIGURAÇÕES DO BANCO DE DADOS POSTGRESQL
# ============================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'conecta_uniforme'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '3'))
}

# ============================================
# CONFIGURAÇÕES DO SERVIDOR SMTP (EMAIL)
# ============================================
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', '587')),
    'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes', 'on'),
    'username': os.getenv('SMTP_USERNAME', ''),
    'password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('SMTP_FROM_EMAIL', 'no-reply@example.com'),
    'from_name': os.getenv('SMTP_FROM_NAME', 'Conecta Uniforme'),
    'timeout': int(os.getenv('SMTP_TIMEOUT', '10'))  # Timeout para conexões SMTP
}

# ============================================
# CONFIGURAÇÕES DA APLICAÇÃO FLASK
# ============================================
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
DEBUG = os.getenv('DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')
PORT = int(os.getenv('PORT', '5000'))

# ============================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO
# ============================================
CODIGO_ACESSO_DURACAO_HORAS = int(os.getenv('CODIGO_ACESSO_DURACAO_HORAS', '24'))
CODIGO_ACESSO_TAMANHO = int(os.getenv('CODIGO_ACESSO_TAMANHO', '6'))
SESSAO_DURACAO_DIAS = int(os.getenv('SESSAO_DURACAO_DIAS', '7'))

# ============================================
# CONFIGURAÇÕES DE WEBAuthn / Passkeys
# ============================================
# RP_ID deve ser o domínio (sem protocolo) da aplicação em produção.
# Em desenvolvimento pode usar 'localhost'. Para teste em dispositivos móveis
# com passkeys, prefira configurar um domínio local (ex: dev.conecta.local) no hosts.
WEBAUTHN_RP_ID = os.getenv('WEBAUTHN_RP_ID', 'localhost')
WEBAUTHN_RP_NAME = os.getenv('WEBAUTHN_RP_NAME', 'Conecta Uniforme')
WEBAUTHN_ORIGIN = os.getenv('WEBAUTHN_ORIGIN', f'http://localhost:{PORT}')
WEBAUTHN_ALLOW_ATTESTATION = os.getenv('WEBAUTHN_ALLOW_ATTESTATION', 'false').lower() in ('1','true','yes','on')
WEBAUTHN_DEBUG = os.getenv('WEBAUTHN_DEBUG', 'true').lower() in ('1','true','yes','on')  # ativa prints de verificação

# Debug: Imprime configurações WebAuthn na inicialização (apenas se DEBUG ativo)
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
ITENS_POR_PAGINA = int(os.getenv('ITENS_POR_PAGINA', '20'))

# ============================================
# CONFIGURAÇÕES DE UPLOAD
# ============================================
DEFAULT_UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(DEFAULT_UPLOAD_FOLDER))
EXTENSOES_PERMITIDAS = set(os.getenv('EXTENSOES_PERMITIDAS', 'png,jpg,jpeg,gif').split(','))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', str(5 * 1024 * 1024)))

# ============================================
# CONFIGURAÇÕES DE REPASSE FINANCEIRO
# ============================================
TAXA_PLATAFORMA_PERCENTUAL = float(os.getenv('TAXA_PLATAFORMA_PERCENTUAL', '5.0'))

# ============================================
# MENSAGENS DO SISTEMA (constantes)
# ============================================
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
