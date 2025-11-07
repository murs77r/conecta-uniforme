"""
============================================
CONECTA UNIFORME - FUNÇÕES UTILITÁRIAS
============================================
Este arquivo contém funções comuns usadas por vários módulos:
- Conexão com banco de dados
- Envio de emails
- Geração de códigos
- Validações
- Logging
"""

import psycopg2
import psycopg2.extras
import smtplib
import random
import string
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from config import DB_CONFIG, SMTP_CONFIG, CODIGO_ACESSO_TAMANHO

# ============================================
# FUNÇÕES DE CONEXÃO COM BANCO DE DADOS
# ============================================

def conectar_banco():
    """
    Cria e retorna uma conexão com o banco de dados PostgreSQL
    
    Retorna:
        connection: Objeto de conexão com o banco
    """
    try:
        # Conecta ao banco usando as configurações do config.py
        conexao = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        return conexao
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def executar_query(query, parametros=None, fetchall=False, fetchone=False, commit=False):
    """
    Executa uma query SQL no banco de dados
    
    Parâmetros:
        query (str): Query SQL a ser executada
        parametros (tuple): Parâmetros da query (opcional)
        fetchall (bool): Se True, retorna todos os resultados
        fetchone (bool): Se True, retorna apenas um resultado
        commit (bool): Se True, faz commit das alterações
    
    Retorna:
        list ou dict ou None: Resultado da query
    """
    conexao = None
    cursor = None
    
    try:
        # Conecta ao banco
        conexao = conectar_banco()
        if not conexao:
            return None
        
        # Cria cursor que retorna dicionários
        cursor = conexao.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Executa a query
        if parametros:
            cursor.execute(query, parametros)
        else:
            cursor.execute(query)
        
        # Faz commit se necessário
        if commit:
            conexao.commit()
            return cursor.rowcount  # Retorna número de linhas afetadas
        
        # Retorna resultados conforme solicitado
        if fetchall:
            return cursor.fetchall()
        elif fetchone:
            return cursor.fetchone()
        
        return None
        
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        if conexao:
            conexao.rollback()
        return None
    
    finally:
        # Fecha cursor e conexão
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()


# ============================================
# FUNÇÕES DE AUTENTICAÇÃO E SEGURANÇA
# ============================================

def gerar_codigo_acesso(tamanho=CODIGO_ACESSO_TAMANHO):
    """
    Gera um código numérico aleatório para acesso
    
    Parâmetros:
        tamanho (int): Quantidade de dígitos do código
    
    Retorna:
        str: Código gerado (ex: "123456")
    """
    # Gera um código numérico aleatório
    codigo = ''.join(random.choices(string.digits, k=tamanho))
    return codigo


def gerar_token_sessao():
    """
    Gera um token único para identificar a sessão do usuário
    
    Retorna:
        str: Token único gerado
    """
    # Gera uma string aleatória e aplica hash
    texto_aleatorio = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
    timestamp = str(datetime.now().timestamp())
    texto_completo = texto_aleatorio + timestamp
    
    # Gera hash SHA256
    token = hashlib.sha256(texto_completo.encode()).hexdigest()
    return token


def validar_email(email):
    """
    Valida se um email tem formato válido
    
    Parâmetros:
        email (str): Email a ser validado
    
    Retorna:
        bool: True se válido, False caso contrário
    """
    # Validação simples de email
    if not email or '@' not in email or '.' not in email:
        return False
    
    partes = email.split('@')
    if len(partes) != 2:
        return False
    
    if len(partes[0]) == 0 or len(partes[1]) == 0:
        return False
    
    return True


def validar_cpf(cpf):
    """
    Valida um CPF brasileiro
    
    Parâmetros:
        cpf (str): CPF a ser validado
    
    Retorna:
        bool: True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação básica (simplificada)
    return True


def validar_cnpj(cnpj):
    """
    Valida um CNPJ brasileiro
    
    Parâmetros:
        cnpj (str): CNPJ a ser validado
    
    Retorna:
        bool: True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = ''.join(filter(str.isdigit, cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação básica (simplificada)
    return True


def validar_cep(cep: str) -> bool:
    """
    Valida um CEP brasileiro (apenas tamanho e dígitos)
    """
    if not cep:
        return True
    somente_digitos = ''.join(filter(str.isdigit, cep))
    return len(somente_digitos) == 8


def validar_telefone(telefone: str) -> bool:
    """
    Valida telefone brasileiro (DDD + número)
    Aceita 10 ou 11 dígitos
    """
    if not telefone:
        return True
    dig = ''.join(filter(str.isdigit, telefone))
    return len(dig) in (10, 11)


# ============================================
# FUNÇÕES DE ENVIO DE EMAIL
# ============================================

def enviar_email(destinatario, assunto, corpo_html):
    """
    Envia um email usando SMTP
    
    Parâmetros:
        destinatario (str): Email do destinatário
        assunto (str): Assunto do email
        corpo_html (str): Conteúdo HTML do email
    
    Retorna:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Cria a mensagem
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = f"{SMTP_CONFIG['from_name']} <{SMTP_CONFIG['from_email']}>"
        mensagem['To'] = destinatario
        
        # Adiciona o corpo HTML
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        mensagem.attach(parte_html)
        
        # Conecta ao servidor SMTP com timeout configurável para não travar
        timeout = float(SMTP_CONFIG.get('timeout', 10))
        servidor = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'], timeout=timeout)
        
        # Inicia conexão TLS se configurado
        if SMTP_CONFIG['use_tls']:
            servidor.starttls()
        
        # Faz login no servidor (se usuário/senha fornecidos)
        username = SMTP_CONFIG.get('username')
        password = SMTP_CONFIG.get('password')
        if username and password:
            servidor.login(username, password)
        
        # Envia o email
        servidor.send_message(mensagem)
        
        # Fecha a conexão
        servidor.quit()
        
        print(f"Email enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


def enviar_codigo_acesso(email, codigo, nome_usuario):
    """
    Envia email com código de acesso para login
    
    Parâmetros:
        email (str): Email do usuário
        codigo (str): Código de acesso gerado
        nome_usuario (str): Nome do usuário
    
    Retorna:
        bool: True se enviado com sucesso, False caso contrário
    """
    # Define o assunto
    assunto = "Seu código de acesso - Conecta Uniforme"
    
    # Cria o corpo do email em HTML
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0d6efd;">Conecta Uniforme</h2>
            
            <p>Olá, <strong>{nome_usuario}</strong>!</p>
            
            <p>Você solicitou um código de acesso para entrar no sistema.</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #666;">Seu código de acesso é:</p>
                <p style="margin: 10px 0; font-size: 32px; font-weight: bold; color: #0d6efd; letter-spacing: 5px;">
                    {codigo}
                </p>
                <p style="margin: 0; font-size: 12px; color: #666;">
                    Este código é válido por 24 horas
                </p>
            </div>
            
            <p>Se você não solicitou este código, ignore este email.</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #666;">
                Este é um email automático. Por favor, não responda.
            </p>
        </div>
    </body>
    </html>
    """
    
    # Envia o email
    return enviar_email(email, assunto, corpo_html)


# ============================================
# FUNÇÕES DE LOG E AUDITORIA
# ============================================

def registrar_log(usuario_id, tabela, registro_id, acao, dados_antigos=None, dados_novos=None, ip_usuario=None, descricao=None):
    """
    Registra uma alteração no sistema para auditoria
    
    Parâmetros:
        usuario_id (int): ID do usuário que fez a alteração
        tabela (str): Nome da tabela alterada
        registro_id (int): ID do registro alterado
        acao (str): Tipo de ação ('INSERT', 'UPDATE', 'DELETE')
        dados_antigos (str): Dados antes da alteração (opcional)
        dados_novos (str): Dados depois da alteração (opcional)
        ip_usuario (str): IP do usuário (opcional)
        descricao (str): Descrição da alteração (opcional)
    
    Retorna:
        bool: True se registrado com sucesso, False caso contrário
    """
    query = """
        INSERT INTO logs_alteracoes 
        (usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, ip_usuario, descricao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    parametros = (usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, ip_usuario, descricao)
    
    resultado = executar_query(query, parametros, commit=True)
    if resultado is None:
        return False
    if isinstance(resultado, int):
        return resultado > 0
    if isinstance(resultado, list):
        return len(resultado) > 0
    return bool(resultado)


# ============================================
# FUNÇÕES DE FORMATAÇÃO
# ============================================

def formatar_dinheiro(valor):
    """
    Formata um valor numérico como moeda brasileira
    
    Parâmetros:
        valor (float): Valor a ser formatado
    
    Retorna:
        str: Valor formatado (ex: "R$ 1.234,56")
    """
    if valor is None:
        valor = 0
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')


def formatar_data(data):
    """
    Formata uma data no padrão brasileiro
    
    Parâmetros:
        data (datetime): Data a ser formatada
    
    Retorna:
        str: Data formatada (ex: "25/12/2024 15:30")
    """
    if not data:
        return ""
    
    if isinstance(data, str):
        return data
    
    return data.strftime("%d/%m/%Y %H:%M")


def formatar_cpf(cpf):
    """
    Formata um CPF no padrão brasileiro
    
    Parâmetros:
        cpf (str): CPF a ser formatado
    
    Retorna:
        str: CPF formatado (ex: "123.456.789-00")
    """
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_cnpj(cnpj):
    """
    Formata um CNPJ no padrão brasileiro
    
    Parâmetros:
        cnpj (str): CNPJ a ser formatado
    
    Retorna:
        str: CNPJ formatado (ex: "12.345.678/0001-00")
    """
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


# ============================================
# FIM DAS FUNÇÕES UTILITÁRIAS
# ============================================
