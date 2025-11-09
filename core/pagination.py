"""
============================================
CORE - PAGINATION HELPER
============================================
Utilitário para paginação de listagens
"""

from typing import Dict, List, Any, Optional
from math import ceil


class Pagination:
    """Classe para gerenciar paginação de listas"""
    
    def __init__(self, page: int = 1, per_page: int = 10, total: int = 0):
        """
        Inicializa o paginador
        
        Args:
            page: Página atual (inicia em 1)
            per_page: Itens por página
            total: Total de itens
        """
        self.page = max(1, page)
        self.per_page = max(1, per_page)
        self.total = max(0, total)
        self.pages = ceil(self.total / self.per_page) if self.per_page > 0 else 0
        
    @property
    def has_prev(self) -> bool:
        """Verifica se existe página anterior"""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Verifica se existe próxima página"""
        return self.page < self.pages
    
    @property
    def prev_num(self) -> Optional[int]:
        """Retorna número da página anterior"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_num(self) -> Optional[int]:
        """Retorna número da próxima página"""
        return self.page + 1 if self.has_next else None
    
    @property
    def offset(self) -> int:
        """Calcula offset para query SQL"""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Retorna o limit para query SQL"""
        return self.per_page
    
    def iter_pages(self, left_edge: int = 2, left_current: int = 2,
                   right_current: int = 2, right_edge: int = 2) -> List[Optional[int]]:
        """
        Gera lista de números de páginas para navegação
        Retorna None para indicar lacunas (...)
        
        Args:
            left_edge: Páginas à esquerda
            left_current: Páginas antes da atual
            right_current: Páginas depois da atual
            right_edge: Páginas à direita
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (num > self.page - left_current - 1 and
                 num < self.page + right_current) or
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte paginação para dicionário"""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num
        }


def paginate_query(query: str, params: tuple, page: int, per_page: int, 
                   count_query: Optional[str] = None) -> tuple:
    """
    Helper para paginar resultados de query SQL
    
    Args:
        query: Query SQL principal
        params: Parâmetros da query
        page: Página atual
        per_page: Itens por página
        count_query: Query para contar total (opcional, será gerado automaticamente se None)
    
    Returns:
        Tuple com (query paginada, params, pagination object)
    """
    from core.database import Database
    
    # Gera query de contagem se não fornecida
    if count_query is None:
        # Remove ORDER BY para performance
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
    
    # Busca total de registros
    result = Database.executar(count_query, params, fetchone=True)
    total = result['total'] if result and 'total' in result else 0
    
    # Cria objeto de paginação
    pagination = Pagination(page=page, per_page=per_page, total=total)
    
    # Adiciona LIMIT e OFFSET à query
    paginated_query = f"{query} LIMIT %s OFFSET %s"
    paginated_params = params + (pagination.limit, pagination.offset)
    
    return paginated_query, paginated_params, pagination


class FilterHelper:
    """Helper para construir filtros em queries SQL"""
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any], 
                          field_mappings: Optional[Dict[str, str]] = None) -> tuple:
        """
        Constrói cláusula WHERE e parâmetros a partir de filtros
        
        Args:
            filters: Dicionário com filtros
            field_mappings: Mapeamento de nomes de filtros para campos SQL
        
        Returns:
            Tuple (where_clause, params_list)
        """
        conditions = []
        params = []
        
        field_mappings = field_mappings or {}
        
        for key, value in filters.items():
            if value is None or value == '':
                continue
            
            # Usa mapeamento ou nome direto
            field = field_mappings.get(key, key)
            
            # Busca textual (ILIKE)
            if key in ['busca', 'search', 'q']:
                # Assume que é busca em múltiplos campos
                continue  # Deve ser tratado especificamente
            
            # Operadores especiais
            elif key.endswith('_min'):
                field_name = field_mappings.get(key[:-4], key[:-4])
                conditions.append(f"{field_name} >= %s")
                params.append(value)
            elif key.endswith('_max'):
                field_name = field_mappings.get(key[:-4], key[:-4])
                conditions.append(f"{field_name} <= %s")
                params.append(value)
            elif key.endswith('_like'):
                field_name = field_mappings.get(key[:-5], key[:-5])
                conditions.append(f"{field_name} ILIKE %s")
                params.append(f"%{value}%")
            else:
                # Comparação de igualdade
                conditions.append(f"{field} = %s")
                params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params
