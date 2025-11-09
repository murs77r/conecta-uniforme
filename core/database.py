"""
============================================
CORE - DATABASE
============================================
Gerenciamento centralizado de conexões e queries ao banco de dados
"""

import psycopg2
import psycopg2.extras
from config import DB_CONFIG
from typing import Optional, List, Dict, Any, Tuple


class Database:
    """Classe para gerenciar conexões e execução de queries"""
    
    @staticmethod
    def conectar():
        """
        Cria e retorna uma conexão com o banco de dados PostgreSQL
        
        Retorna:
            connection: Objeto de conexão com o banco
        """
        try:
            conexao = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                connect_timeout=DB_CONFIG.get('connect_timeout', 3)
            )
            return conexao
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return None

    @staticmethod
    def executar(query: str, parametros: Optional[Tuple] = None, 
                 fetchall: bool = False, fetchone: bool = False, 
                 commit: bool = False) -> Optional[Any]:
        """
        Executa uma query SQL no banco de dados
        
        Parâmetros:
            query (str): Query SQL a ser executada
            parametros (tuple): Parâmetros da query (opcional)
            fetchall (bool): Se True, retorna todos os resultados
            fetchone (bool): Se True, retorna apenas um resultado
            commit (bool): Se True, faz commit das alterações
        
        Retorna:
            list ou dict ou int ou None: Resultado da query
        """
        conexao = None
        cursor = None
        
        try:
            conexao = Database.conectar()
            if not conexao:
                return None
            
            cursor = conexao.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if parametros:
                cursor.execute(query, parametros)
            else:
                cursor.execute(query)
            
            if commit:
                conexao.commit()
                return cursor.rowcount
            
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
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    @staticmethod
    def inserir(tabela: str, dados: Dict[str, Any]) -> Optional[int]:
        """
        Insere um registro em uma tabela e retorna o ID gerado
        
        Parâmetros:
            tabela (str): Nome da tabela
            dados (dict): Dicionário com os dados a inserir
        
        Retorna:
            int ou None: ID do registro inserido
        """
        campos = ', '.join(dados.keys())
        placeholders = ', '.join(['%s'] * len(dados))
        query = f"INSERT INTO {tabela} ({campos}) VALUES ({placeholders}) RETURNING id"
        
        resultado = Database.executar(query, tuple(dados.values()), fetchone=True)
        return resultado['id'] if resultado and isinstance(resultado, dict) else None

    @staticmethod
    def atualizar(tabela: str, id: int, dados: Dict[str, Any]) -> bool:
        """
        Atualiza um registro em uma tabela
        
        Parâmetros:
            tabela (str): Nome da tabela
            id (int): ID do registro a atualizar
            dados (dict): Dicionário com os dados a atualizar
        
        Retorna:
            bool: True se atualizado com sucesso
        """
        set_clause = ', '.join([f"{k} = %s" for k in dados.keys()])
        query = f"UPDATE {tabela} SET {set_clause}, data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s"
        
        parametros = tuple(dados.values()) + (id,)
        resultado = Database.executar(query, parametros, commit=True)
        return resultado is not None and resultado > 0

    @staticmethod
    def excluir(tabela: str, id: int) -> bool:
        """
        Exclui um registro de uma tabela
        
        Parâmetros:
            tabela (str): Nome da tabela
            id (int): ID do registro a excluir
        
        Retorna:
            bool: True se excluído com sucesso
        """
        query = f"DELETE FROM {tabela} WHERE id = %s"
        resultado = Database.executar(query, (id,), commit=True)
        return resultado is not None and resultado > 0

    @staticmethod
    def buscar_por_id(tabela: str, id: int) -> Optional[Dict]:
        """
        Busca um registro por ID
        
        Parâmetros:
            tabela (str): Nome da tabela
            id (int): ID do registro
        
        Retorna:
            dict ou None: Registro encontrado
        """
        query = f"SELECT * FROM {tabela} WHERE id = %s"
        return Database.executar(query, (id,), fetchone=True)
