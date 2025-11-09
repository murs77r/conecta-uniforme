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
        """Valida formato de email"""
        if not email or '@' not in email or '.' not in email:
            return False
        partes = email.split('@')
        return len(partes) == 2 and len(partes[0]) > 0 and len(partes[1]) > 0
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF brasileiro"""
        if not cpf:
            return True  # CPF opcional
        cpf_numeros = ''.join(filter(str.isdigit, cpf))
        if len(cpf_numeros) != 11 or cpf_numeros == cpf_numeros[0] * 11:
            return False
        return True
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ brasileiro"""
        if not cnpj:
            return False
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14 or cnpj_numeros == cnpj_numeros[0] * 14:
            return False
        return True
    
    @staticmethod
    def validar_cep(cep: str) -> bool:
        """Valida CEP brasileiro"""
        if not cep:
            return True  # CEP opcional
        somente_digitos = ''.join(filter(str.isdigit, cep))
        return len(somente_digitos) == 8
    
    @staticmethod
    def validar_telefone(telefone: str) -> bool:
        """Valida telefone brasileiro"""
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
        Registra uma alteração no sistema para auditoria
        
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
