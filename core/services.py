"""
============================================
CORE - SERVICES
============================================
Camada de lógica de negócio (serviços)
"""

from typing import Optional, Dict, Any, List
from flask import session, flash
from core.database import Database
from core.repositories import BaseRepository
import json
import re
import smtplib
import random
import string
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from decimal import Decimal
from config import SMTP_CONFIG, CODIGO_ACESSO_TAMANHO


class AutenticacaoService:
    """Serviço de autenticação"""
    
    @staticmethod
    def verificar_sessao() -> Optional[Dict]:
        """
        Verifica se o usuário está autenticado
        
        Retorna:
            dict ou None: Dados do usuário se autenticado
        """
        if not all(key in session for key in ['usuario_id', 'usuario_nome', 'usuario_email', 'usuario_tipo', 'logged_in']):
            return None
        
        if not session.get('logged_in'):
            return None
        
        return {
            'id': session.get('usuario_id'),
            'nome': session.get('usuario_nome'),
            'email': session.get('usuario_email'),
            'tipo': session.get('usuario_tipo')
        }
    
    @staticmethod
    def verificar_permissao(tipos_permitidos: List[str]) -> Optional[Dict]:
        """
        Verifica se o usuário tem permissão para acessar
        
        Parâmetros:
            tipos_permitidos (list): Lista de tipos permitidos
        
        Retorna:
            dict ou None: Dados do usuário se tem permissão
        """
        usuario = AutenticacaoService.verificar_sessao()
        if not usuario:
            return None
        
        if usuario['tipo'] not in tipos_permitidos:
            return None
        
        return usuario


class ValidacaoService:
    """Serviço de validação de dados"""
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """
        Valida formato de email
        
        Args:
            email: Email a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not email or '@' not in email or '.' not in email:
            return False
        partes = email.split('@')
        return len(partes) == 2 and len(partes[0]) > 0 and len(partes[1]) > 0
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """
        Valida CPF brasileiro (formato e dígitos verificadores)
        
        Args:
            cpf: CPF a ser validado
            
        Returns:
            True se válido ou vazio (opcional), False caso contrário
        """
        if not cpf:
            return True  # CPF opcional
        cpf_numeros = ''.join(filter(str.isdigit, cpf))
        if len(cpf_numeros) != 11 or cpf_numeros == cpf_numeros[0] * 11:
            return False
        return True
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """
        Valida CNPJ brasileiro (formato e dígitos verificadores)
        
        Args:
            cnpj: CNPJ a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not cnpj:
            return False
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14 or cnpj_numeros == cnpj_numeros[0] * 14:
            return False
        return True
    
    @staticmethod
    def validar_cep(cep: str) -> bool:
        """
        Valida CEP brasileiro
        
        Args:
            cep: CEP a ser validado
            
        Returns:
            True se válido ou vazio (opcional), False caso contrário
        """
        if not cep:
            return True  # CEP opcional
        somente_digitos = ''.join(filter(str.isdigit, cep))
        return len(somente_digitos) == 8
    
    @staticmethod
    def validar_telefone(telefone: str) -> bool:
        """
        Valida telefone brasileiro (DDD + número)
        
        Args:
            telefone: Telefone a ser validado
            
        Returns:
            True se válido ou vazio (opcional), False caso contrário
        """
        if not telefone:
            return True  # Telefone opcional
        dig = ''.join(filter(str.isdigit, telefone))
        return len(dig) in (10, 11)


class LogService:
    """Serviço de logging/auditoria"""
    
    @staticmethod
    def registrar(usuario_id: int, tabela: str, registro_id: Optional[int], 
                  acao: str, dados_antigos: Optional[Any] = None, 
                  dados_novos: Optional[Any] = None, 
                  descricao: Optional[str] = None) -> bool:
        """
        Registra uma alteração no sistema para auditoria (INSERT, UPDATE, DELETE)
        
        Parâmetros:
            usuario_id (int): ID do usuário que fez a alteração
            tabela (str): Nome da tabela alterada
            registro_id (int): ID do registro alterado
            acao (str): Tipo de ação ('INSERT', 'UPDATE', 'DELETE')
            dados_antigos: Dados antes da alteração
            dados_novos: Dados depois da alteração
            descricao (str): Descrição da alteração
        
        Retorna:
            bool: True se registrado com sucesso
        """
        # Converte dados para JSON se necessário
        if dados_antigos and not isinstance(dados_antigos, str):
            dados_antigos = json.dumps(dados_antigos, default=str)
        if dados_novos and not isinstance(dados_novos, str):
            dados_novos = json.dumps(dados_novos, default=str)
        
        query = """
            INSERT INTO logs_alteracoes 
            (usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, descricao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        resultado = Database.executar(query, 
                                     (usuario_id, tabela, registro_id, acao, 
                                      dados_antigos, dados_novos, descricao),
                                     commit=True)
        return resultado is not None and resultado > 0
    
    @staticmethod
    def registrar_acesso(usuario_id: int, acao: str, 
                        tipo_autenticacao: Optional[str] = None,
                        ip_usuario: Optional[str] = None,
                        user_agent: Optional[str] = None,
                        sucesso: bool = True,
                        descricao: Optional[str] = None) -> bool:
        """
        Registra um evento de acesso (LOGIN ou LOGOFF)
        
        Parâmetros:
            usuario_id (int): ID do usuário
            acao (str): Tipo de ação ('LOGIN' ou 'LOGOFF')
            tipo_autenticacao (str): Tipo de autenticação ('codigo', 'passkey')
            ip_usuario (str): IP do usuário
            user_agent (str): User agent do navegador
            sucesso (bool): Se o acesso foi bem-sucedido
            descricao (str): Descrição adicional
        
        Retorna:
            bool: True se registrado com sucesso
        """
        query = """
            INSERT INTO logs_acesso 
            (usuario_id, acao, tipo_autenticacao, ip_usuario, user_agent, sucesso, descricao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        resultado = Database.executar(query, 
                                     (usuario_id, acao, tipo_autenticacao, 
                                      ip_usuario, user_agent, sucesso, descricao),
                                     commit=True)
        return resultado is not None and resultado > 0


class CRUDService:
    """Serviço genérico de CRUD com logging"""
    
    def __init__(self, repository: BaseRepository, entidade_nome: str):
        self.repository = repository
        self.entidade_nome = entidade_nome
    
    def criar_com_log(self, dados: Dict[str, Any], usuario_id: int) -> Optional[int]:
        """Cria um registro e registra log"""
        id_criado = self.repository.inserir(dados)
        
        if id_criado:
            LogService.registrar(
                usuario_id=usuario_id,
                tabela=self.repository.tabela,
                registro_id=id_criado,
                acao='INSERT',
                dados_novos=dados,
                descricao=f'Cadastro de {self.entidade_nome}'
            )
            flash(f'{self.entidade_nome} cadastrado com sucesso!', 'success')
            return id_criado
        
        flash(f'Erro ao cadastrar {self.entidade_nome}.', 'danger')
        return None
    
    def atualizar_com_log(self, id: int, dados: Dict[str, Any], 
                          dados_antigos: Dict, usuario_id: int) -> bool:
        """Atualiza um registro e registra log"""
        sucesso = self.repository.atualizar(id, dados)
        
        if sucesso:
            LogService.registrar(
                usuario_id=usuario_id,
                tabela=self.repository.tabela,
                registro_id=id,
                acao='UPDATE',
                dados_antigos=dados_antigos,
                dados_novos=dados,
                descricao=f'Atualização de {self.entidade_nome}'
            )
            flash(f'{self.entidade_nome} atualizado com sucesso!', 'success')
            return True
        
        flash(f'Erro ao atualizar {self.entidade_nome}.', 'danger')
        return False
    
    def excluir_com_log(self, id: int, dados_antigos: Dict, usuario_id: int) -> bool:
        """Exclui um registro e registra log"""
        sucesso = self.repository.excluir(id)
        
        if sucesso:
            LogService.registrar(
                usuario_id=usuario_id,
                tabela=self.repository.tabela,
                registro_id=id,
                acao='DELETE',
                dados_antigos=dados_antigos,
                descricao=f'Exclusão de {self.entidade_nome}'
            )
            flash(f'{self.entidade_nome} excluído com sucesso!', 'success')
            return True
        
        flash(f'Erro ao excluir {self.entidade_nome}.', 'danger')
        return False
    
    def verificar_dependencias(self, id: int, checagens: List[Dict]) -> List[str]:
        """
        Verifica dependências antes de excluir
        
        Parâmetros:
            id: ID do registro
            checagens: Lista de dicts com 'tabela', 'campo' e 'mensagem'
        
        Retorna:
            List[str]: Lista de mensagens de bloqueio
        """
        bloqueios = []
        
        for check in checagens:
            query = f"SELECT COUNT(*) AS total FROM {check['tabela']} WHERE {check['campo']} = %s"
            resultado = Database.executar(query, (id,), fetchone=True)
            
            if resultado and isinstance(resultado, dict) and int(resultado.get('total', 0)) > 0:
                bloqueios.append(f"Possui {check['mensagem']} vinculados.")
        
        return bloqueios


class EmailService:
    """Serviço robusto para envio de emails"""
    
    def __init__(self):
        self.config = SMTP_CONFIG
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Valida configurações de email"""
        required_fields = ['server', 'port', 'from_email', 'from_name']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Configuração de email inválida: {field} não definido")
    
    def _criar_conexao_smtp(self) -> smtplib.SMTP:
        """
        Cria e retorna uma conexão SMTP configurada
        
        Returns:
            Conexão SMTP ativa
            
        Raises:
            smtplib.SMTPException: Erro ao conectar ao servidor
        """
        timeout = float(self.config.get('timeout', 10))
        servidor = smtplib.SMTP(
            self.config['server'], 
            self.config['port'], 
            timeout=timeout
        )
        
        if self.config.get('use_tls', True):
            servidor.starttls()
        
        username = self.config.get('username')
        password = self.config.get('password')
        if username and password:
            servidor.login(username, password)
        
        return servidor
    
    def enviar(self, destinatario: str, assunto: str, corpo_html: str, 
               tentativas: int = 3) -> bool:
        """
        Envia um email com retry automático
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo_html: Conteúdo HTML do email
            tentativas: Número de tentativas em caso de falha
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        for tentativa in range(tentativas):
            try:
                mensagem = MIMEMultipart('alternative')
                mensagem['Subject'] = assunto
                mensagem['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
                mensagem['To'] = destinatario
                
                parte_html = MIMEText(corpo_html, 'html', 'utf-8')
                mensagem.attach(parte_html)
                
                servidor = self._criar_conexao_smtp()
                servidor.send_message(mensagem)
                servidor.quit()
                
                print(f"✅ Email enviado com sucesso para {destinatario}")
                return True
                
            except smtplib.SMTPException as e:
                print(f"❌ Tentativa {tentativa + 1}/{tentativas} falhou: {e}")
                if tentativa == tentativas - 1:
                    print(f"❌ Falha definitiva ao enviar email para {destinatario}")
                    return False
            except Exception as e:
                print(f"❌ Erro inesperado ao enviar email: {e}")
                return False
        
        return False
    
    def enviar_codigo_acesso(self, email: str, codigo: str, nome_usuario: str) -> bool:
        """
        Envia email com código de acesso para login
        
        Args:
            email: Email do usuário
            codigo: Código de acesso gerado
            nome_usuario: Nome do usuário
            
        Returns:
            True se enviado com sucesso
        """
        assunto = "Seu código de acesso - Conecta Uniforme"
        
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
        
        return self.enviar(email, assunto, corpo_html)
    
    def enviar_notificacao(self, destinatario: str, titulo: str, mensagem: str) -> bool:
        """
        Envia email de notificação genérica
        
        Args:
            destinatario: Email do destinatário
            titulo: Título da notificação
            mensagem: Mensagem da notificação
            
        Returns:
            True se enviado com sucesso
        """
        assunto = f"{titulo} - Conecta Uniforme"
        
        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0d6efd;">Conecta Uniforme</h2>
                <h3>{titulo}</h3>
                <p>{mensagem}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    Este é um email automático. Por favor, não responda.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.enviar(destinatario, assunto, corpo_html)


class UtilsService:
    """Serviço para funções utilitárias gerais"""
    
    @staticmethod
    def gerar_codigo_acesso(tamanho: int = CODIGO_ACESSO_TAMANHO) -> str:
        """
        Gera um código numérico aleatório para acesso
        
        Args:
            tamanho: Quantidade de dígitos do código
            
        Returns:
            Código numérico (ex: "123456")
        """
        return ''.join(random.choices(string.digits, k=tamanho))
    
    @staticmethod
    def gerar_token_sessao() -> str:
        """
        Gera um token único para identificar a sessão do usuário
        
        Returns:
            Token único SHA256
        """
        texto_aleatorio = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        timestamp = str(datetime.now().timestamp())
        texto_completo = texto_aleatorio + timestamp
        
        return hashlib.sha256(texto_completo.encode()).hexdigest()
    
    @staticmethod
    def gerar_hash_senha(senha: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Gera hash seguro de senha com salt
        
        Args:
            senha: Senha em texto plano
            salt: Salt opcional (será gerado se não fornecido)
            
        Returns:
            Tupla (hash, salt)
        """
        if not salt:
            salt = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', senha.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt
    
    @staticmethod
    def verificar_senha(senha: str, hash_armazenado: str, salt: str) -> bool:
        """
        Verifica se a senha corresponde ao hash armazenado
        
        Args:
            senha: Senha em texto plano
            hash_armazenado: Hash armazenado no banco
            salt: Salt usado na geração do hash
            
        Returns:
            True se a senha está correta
        """
        hash_calculado, _ = UtilsService.gerar_hash_senha(senha, salt)
        return hash_calculado == hash_armazenado


class FormatadorService:
    """Serviço para formatação de dados"""
    
    @staticmethod
    def formatar_dinheiro(valor: Any) -> str:
        """
        Formata um valor numérico como moeda brasileira
        
        Args:
            valor: Valor a ser formatado (float, int, Decimal, str)
            
        Returns:
            Valor formatado (ex: "R$ 1.234,56")
        """
        if valor is None:
            valor = 0
        
        try:
            if isinstance(valor, str):
                valor = float(valor.replace(',', '.'))
            elif isinstance(valor, Decimal):
                valor = float(valor)
            
            return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
        except (ValueError, TypeError):
            return "R$ 0,00"
    
    @staticmethod
    def formatar_data(data: Any, formato: str = "%d/%m/%Y %H:%M") -> str:
        """
        Formata uma data no padrão especificado
        
        Args:
            data: Data a ser formatada (datetime, str)
            formato: Formato de saída
            
        Returns:
            Data formatada
        """
        if not data:
            return ""
        
        if isinstance(data, str):
            return data
        
        try:
            return data.strftime(formato)
        except (AttributeError, TypeError):
            return str(data)
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        """
        Formata um CPF no padrão brasileiro
        
        Args:
            cpf: CPF a ser formatado (com ou sem formatação)
            
        Returns:
            CPF formatado (ex: "123.456.789-00")
        """
        if not cpf:
            return ""
        
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11:
            return cpf
        
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @staticmethod
    def formatar_cnpj(cnpj: str) -> str:
        """
        Formata um CNPJ no padrão brasileiro
        
        Args:
            cnpj: CNPJ a ser formatado (com ou sem formatação)
            
        Returns:
            CNPJ formatado (ex: "12.345.678/0001-00")
        """
        if not cnpj:
            return ""
        
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) != 14:
            return cnpj
        
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """
        Formata um telefone brasileiro
        
        Args:
            telefone: Telefone a ser formatado (com ou sem formatação)
            
        Returns:
            Telefone formatado (ex: "(11) 98765-4321")
        """
        if not telefone:
            return ""
        
        digitos = ''.join(filter(str.isdigit, telefone))
        
        if len(digitos) == 11:  # Celular com DDD
            return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
        elif len(digitos) == 10:  # Fixo com DDD
            return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
        else:
            return telefone
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        """
        Formata um CEP brasileiro
        
        Args:
            cep: CEP a ser formatado (com ou sem formatação)
            
        Returns:
            CEP formatado (ex: "12345-678")
        """
        if not cep:
            return ""
        
        digitos = ''.join(filter(str.isdigit, cep))
        if len(digitos) != 8:
            return cep
        
        return f"{digitos[:5]}-{digitos[5:]}"
    
    @staticmethod
    def limpar_formatacao(texto: str) -> str:
        """
        Remove toda formatação de um texto, deixando apenas números
        
        Args:
            texto: Texto a ser limpo
            
        Returns:
            Apenas números
        """
        if not texto:
            return ""
        
        return ''.join(filter(str.isdigit, texto))

