"""
============================================
CORE - REPOSITORIES
============================================
Camada de acesso a dados usando padrão Repository
"""

from typing import Optional, List, Dict, Any
from core.database import Database
import json


class BaseRepository:
    """Repositório base com operações CRUD genéricas"""
    
    def __init__(self, tabela: str):
        self.tabela = tabela
    
    def buscar_por_id(self, id: int) -> Optional[Dict]:
        """Busca um registro por ID"""
        return Database.buscar_por_id(self.tabela, id)
    
    def inserir(self, dados: Dict[str, Any]) -> Optional[int]:
        """Insere um registro e retorna o ID"""
        return Database.inserir(self.tabela, dados)
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        """Atualiza um registro"""
        return Database.atualizar(self.tabela, id, dados)
    
    def excluir(self, id: int) -> bool:
        """Exclui um registro"""
        return Database.excluir(self.tabela, id)
    
    def listar(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """Lista registros com filtros opcionais"""
        query = f"SELECT * FROM {self.tabela}"
        parametros = []
        
        if filtros:
            condicoes = []
            for campo, valor in filtros.items():
                if valor:
                    condicoes.append(f"{campo} = %s")
                    parametros.append(valor)
            
            if condicoes:
                query += " WHERE " + " AND ".join(condicoes)
        
        query += " ORDER BY id DESC"
        resultado = Database.executar(query, tuple(parametros) if parametros else None, fetchall=True)
        return resultado if resultado else []


class UsuarioRepository(BaseRepository):
    """Repositório de usuários"""
    
    def __init__(self):
        super().__init__('usuarios')
    
    def buscar_por_email_tipo(self, email: str, tipo: str) -> Optional[Dict]:
        """Busca usuário por email e tipo"""
        query = "SELECT * FROM usuarios WHERE email = %s AND tipo = %s"
        return Database.executar(query, (email, tipo), fetchone=True)
    
    def listar_com_filtros(self, filtros: Dict) -> List[Dict]:
        """Lista usuários com filtros de busca e tipo"""
        query = "SELECT * FROM usuarios WHERE 1=1"
        parametros = []
        
        if filtros.get('tipo'):
            query += " AND tipo = %s"
            parametros.append(filtros['tipo'])
        
        if filtros.get('busca'):
            query += " AND (nome ILIKE %s OR email ILIKE %s)"
            busca = f"%{filtros['busca']}%"
            parametros.extend([busca, busca])
        
        query += " ORDER BY data_cadastro DESC"
        return Database.executar(query, tuple(parametros) if parametros else None, fetchall=True) or []


class EscolaRepository(BaseRepository):
    """Repositório de escolas"""
    
    def __init__(self):
        super().__init__('escolas')
    
    def buscar_com_usuario(self, id: int) -> Optional[Dict]:
        """Busca escola com dados do usuário"""
        query = """
            SELECT e.*, u.nome, u.email, u.telefone, u.ativo, u.data_cadastro
            FROM escolas e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.id = %s
        """
        return Database.executar(query, (id,), fetchone=True)
    
    def listar_com_filtros(self, filtros: Dict) -> List[Dict]:
        """Lista escolas com filtros"""
        query = """
            SELECT e.*, u.nome, u.email, u.telefone, u.ativo
            FROM escolas e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE 1=1
        """
        parametros = []
        
        if filtros.get('busca'):
            query += " AND (u.nome ILIKE %s OR e.razao_social ILIKE %s OR e.cnpj ILIKE %s)"
            busca = f"%{filtros['busca']}%"
            parametros.extend([busca, busca, busca])
        
        if filtros.get('ativo'):
            query += " AND e.ativo = %s"
            parametros.append(filtros['ativo'] == 'true')
        
        query += " ORDER BY u.nome"
        return Database.executar(query, tuple(parametros) if parametros else None, fetchall=True) or []
    
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[Dict]:
        """Busca escola pelo ID do usuário"""
        query = "SELECT * FROM escolas WHERE usuario_id = %s"
        return Database.executar(query, (usuario_id,), fetchone=True)


class GestorEscolarRepository(BaseRepository):
    """Repositório de gestores escolares"""
    
    def __init__(self):
        super().__init__('gestores_escolares')
    
    def listar_por_escola(self, escola_id: int) -> List[Dict]:
        """Lista gestores de uma escola"""
        query = """
            SELECT id, nome, email, telefone, cpf, tipo_gestor, data_cadastro
            FROM gestores_escolares
            WHERE escola_id = %s
            ORDER BY nome
        """
        return Database.executar(query, (escola_id,), fetchall=True) or []
    
    def excluir_por_escola(self, escola_id: int) -> bool:
        """Remove todos gestores de uma escola"""
        query = "DELETE FROM gestores_escolares WHERE escola_id = %s"
        resultado = Database.executar(query, (escola_id,), commit=True)
        return resultado is not None


class FornecedorRepository(BaseRepository):
    """Repositório de fornecedores"""
    
    def __init__(self):
        super().__init__('fornecedores')
    
    def buscar_com_usuario(self, id: int) -> Optional[Dict]:
        """Busca fornecedor com dados do usuário"""
        query = """
            SELECT f.*, u.nome, u.email, u.telefone, u.ativo
            FROM fornecedores f
            JOIN usuarios u ON f.usuario_id = u.id
            WHERE f.id = %s
        """
        return Database.executar(query, (id,), fetchone=True)
    
    def listar_com_usuario(self, filtros: Dict) -> List[Dict]:
        """Lista fornecedores com dados do usuário"""
        query = """
            SELECT f.*, u.nome, u.email, u.telefone, u.ativo
            FROM fornecedores f
            JOIN usuarios u ON f.usuario_id = u.id
            WHERE 1=1
        """
        parametros = []
        
        if filtros.get('busca'):
            query += " AND (u.nome ILIKE %s OR f.razao_social ILIKE %s)"
            busca = f"%{filtros['busca']}%"
            parametros.extend([busca, busca])
        
        query += " ORDER BY u.nome"
        return Database.executar(query, tuple(parametros) if parametros else None, fetchall=True) or []
    
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[Dict]:
        """Busca fornecedor pelo ID do usuário"""
        query = "SELECT * FROM fornecedores WHERE usuario_id = %s"
        return Database.executar(query, (usuario_id,), fetchone=True)


class ProdutoRepository(BaseRepository):
    """Repositório de produtos"""
    
    def __init__(self):
        super().__init__('produtos')
    
    def listar_vitrine(self, filtros: Dict) -> List[Dict]:
        """Lista produtos para vitrine com filtros"""
        query = """
            SELECT p.*, f.razao_social as fornecedor_nome, 
                   u.nome as fornecedor_usuario_nome,
                   e.razao_social as escola_nome
            FROM produtos p
            JOIN fornecedores f ON p.fornecedor_id = f.id
            JOIN usuarios u ON f.usuario_id = u.id
            LEFT JOIN escolas e ON p.escola_id = e.id
            WHERE p.ativo = TRUE AND p.estoque > 0
        """
        parametros = []
        
        if filtros.get('categoria'):
            query += " AND p.categoria = %s"
            parametros.append(filtros['categoria'])
        
        if filtros.get('escola'):
            query += " AND p.escola_id = %s"
            parametros.append(filtros['escola'])
        
        if filtros.get('busca'):
            query += " AND p.nome ILIKE %s"
            parametros.append(f"%{filtros['busca']}%")
        
        query += " ORDER BY p.data_cadastro DESC"
        return Database.executar(query, tuple(parametros) if parametros else None, fetchall=True) or []


class PedidoRepository(BaseRepository):
    """Repositório de pedidos"""
    
    def __init__(self):
        super().__init__('pedidos')
    
    def buscar_carrinho(self, responsavel_id: int) -> Optional[Dict]:
        """Busca carrinho ativo do responsável"""
        query = """
            SELECT id FROM pedidos 
            WHERE responsavel_id = %s AND status = 'carrinho'
            ORDER BY data_pedido DESC LIMIT 1
        """
        return Database.executar(query, (responsavel_id,), fetchone=True)
    
    def listar_por_responsavel(self, responsavel_id: int) -> List[Dict]:
        """Lista pedidos de um responsável"""
        query = """
            SELECT p.*, r.usuario_id, u.nome as responsavel_nome
            FROM pedidos p
            JOIN responsaveis r ON p.responsavel_id = r.id
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE p.responsavel_id = %s AND p.status != 'carrinho'
            ORDER BY p.data_pedido DESC
        """
        return Database.executar(query, (responsavel_id,), fetchall=True) or []


class ResponsavelRepository(BaseRepository):
    """Repositório de responsáveis"""
    
    def __init__(self):
        super().__init__('responsaveis')
    
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[Dict]:
        """Busca responsável pelo ID do usuário"""
        query = "SELECT id FROM responsaveis WHERE usuario_id = %s"
        return Database.executar(query, (usuario_id,), fetchone=True)
