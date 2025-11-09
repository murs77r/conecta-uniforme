"""
============================================
RF07 - GERENCIAR REPASSES FINANCEIROS (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import RepasseFinanceiroRepository, FornecedorRepository
from core.services import AutenticacaoService, LogService
from core.database import Database
from core.pagination import paginate_query, Pagination
from config import TAXA_PLATAFORMA_PERCENTUAL

# Blueprint e Serviços
repasses_bp = Blueprint('repasses', __name__, url_prefix='/repasses')
repasse_repo = RepasseFinanceiroRepository()
fornecedor_repo = FornecedorRepository()
auth_service = AutenticacaoService()


# ============================================
# RF07.2 - LISTAR REPASSES
# ============================================

@repasses_bp.route('/')
@repasses_bp.route('/listar')
def listar():
    """Lista repasses financeiros com paginação e filtros"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtros
    filtros = {
        'status': request.args.get('status', ''),
        'fornecedor_id': request.args.get('fornecedor_id', ''),
        'data_inicio': request.args.get('data_inicio', ''),
        'data_fim': request.args.get('data_fim', ''),
        'valor_min': request.args.get('valor_min', ''),
        'valor_max': request.args.get('valor_max', '')
    }
    
    # Base query
    query = """
        SELECT r.*, 
               f.razao_social as fornecedor_nome,
               u.nome as fornecedor_usuario_nome
        FROM repasses_financeiros r
        JOIN fornecedores f ON r.fornecedor_id = f.id
        JOIN usuarios u ON f.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    # Se for fornecedor, filtra apenas seus repasses
    if usuario_logado['tipo'] == 'fornecedor':
        fornecedor = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        if fornecedor:
            query += " AND r.fornecedor_id = %s"
            params.append(fornecedor['id'])
        else:
            # Fornecedor sem registro, não mostra nada
            repasses = []
            pagination = Pagination(page=1, per_page=per_page, total=0)
            estatisticas = _calcular_estatisticas_repasses(None)
            fornecedores = []
            return render_template('repasses/listar.html', 
                                 repasses=repasses, 
                                 pagination=pagination,
                                 filtros=filtros,
                                 estatisticas=estatisticas,
                                 fornecedores=fornecedores)
    
    # Aplicar filtros
    if filtros['status']:
        query += " AND r.status = %s"
        params.append(filtros['status'])
    
    if filtros['fornecedor_id']:
        query += " AND r.fornecedor_id = %s"
        params.append(int(filtros['fornecedor_id']))
    
    if filtros['data_inicio']:
        query += " AND r.data_repasse >= %s"
        params.append(filtros['data_inicio'])
    
    if filtros['data_fim']:
        query += " AND r.data_repasse <= %s"
        params.append(filtros['data_fim'])
    
    if filtros['valor_min']:
        query += " AND r.valor_liquido >= %s"
        params.append(float(filtros['valor_min']))
    
    if filtros['valor_max']:
        query += " AND r.valor_liquido <= %s"
        params.append(float(filtros['valor_max']))
    
    # Ordenação
    query += " ORDER BY r.data_repasse DESC, r.id DESC"
    
    # Paginar
    paginated_query, paginated_params, pagination = paginate_query(
        query, tuple(params), page, per_page
    )
    
    # Executar query
    repasses = Database.executar(paginated_query, paginated_params, fetchall=True) or []
    
    # Calcular estatísticas
    fornecedor_id_filtro = None
    if usuario_logado['tipo'] == 'fornecedor':
        fornecedor_id_filtro = fornecedor['id'] if fornecedor else None
    estatisticas = _calcular_estatisticas_repasses(fornecedor_id_filtro)
    
    # Lista de fornecedores para o filtro (apenas admin)
    fornecedores = []
    if usuario_logado['tipo'] == 'administrador':
        query_fornecedores = """
            SELECT f.id, u.nome, f.razao_social
            FROM fornecedores f
            JOIN usuarios u ON f.usuario_id = u.id
            WHERE u.ativo = TRUE
            ORDER BY u.nome
        """
        fornecedores = Database.executar(query_fornecedores, fetchall=True) or []
    
    return render_template('repasses/listar.html', 
                         repasses=repasses, 
                         pagination=pagination,
                         filtros=filtros,
                         estatisticas=estatisticas,
                         fornecedores=fornecedores)


# ============================================
# RF07.1 - GERAR REPASSE (ADMIN)
# ============================================

@repasses_bp.route('/gerar/<int:pedido_id>', methods=['POST'])
def gerar(pedido_id):
    """Gera repasses para um pedido pago"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o pedido
    pedido = Database.executar("SELECT * FROM pedidos WHERE id = %s AND status = 'pago'", 
                               (pedido_id,), fetchone=True)
    
    if not pedido:
        flash('Pedido não encontrado ou não pago.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # Busca itens do pedido agrupados por fornecedor
    query_itens = """
        SELECT p.fornecedor_id, SUM(i.subtotal) as valor_total
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
        GROUP BY p.fornecedor_id
    """
    itens_por_fornecedor = Database.executar(query_itens, (pedido_id,), fetchall=True) or []
    
    if not itens_por_fornecedor:
        flash('Nenhum item encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # Cria repasses para cada fornecedor
    for item in itens_por_fornecedor:
        valor = float(item['valor_total'])
        taxa = valor * (TAXA_PLATAFORMA_PERCENTUAL / 100)
        valor_liquido = valor - taxa
        
        dados_repasse = {
            'fornecedor_id': item['fornecedor_id'],
            'pedido_id': pedido_id,
            'valor': valor,
            'taxa_plataforma': taxa,
            'valor_liquido': valor_liquido,
            'status': 'pendente'
        }
        
        repasse_id = repasse_repo.inserir(dados_repasse)
        if repasse_id:
            LogService.registrar(usuario_logado['id'], 'repasses_financeiros', repasse_id, 
                               'INSERT', dados_novos=dados_repasse, descricao='Repasse gerado')
    
    flash('Repasses gerados com sucesso!', 'success')
    return redirect(url_for('repasses.listar'))


# ============================================
# RF07.3 - PROCESSAR REPASSE
# ============================================

@repasses_bp.route('/processar/<int:id>', methods=['POST'])
def processar(id):
    """Marca um repasse como concluído"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query = """
        UPDATE repasses_financeiros 
        SET status = 'concluido', data_processamento = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    resultado = Database.executar(query, (id,), commit=True)
    
    if resultado:
        LogService.registrar(usuario_logado['id'], 'repasses_financeiros', id, 'UPDATE', 
                           descricao='Repasse processado')
        flash('Repasse processado!', 'success')
    
    return redirect(url_for('repasses.listar'))


# ============================================
# RF07.4 - CANCELAR REPASSE
# ============================================

@repasses_bp.route('/cancelar/<int:id>', methods=['POST'])
def cancelar(id):
    """Cancela um repasse"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if repasse_repo.atualizar(id, {'status': 'cancelado'}):
        LogService.registrar(usuario_logado['id'], 'repasses_financeiros', id, 'UPDATE', 
                           descricao='Repasse cancelado')
        flash('Repasse cancelado!', 'success')
    
    return redirect(url_for('repasses.listar'))


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _calcular_estatisticas_repasses(fornecedor_id=None):
    """Calcula estatísticas dos repasses"""
    query_base = "SELECT status, COUNT(*) as total, SUM(valor_liquido) as soma FROM repasses_financeiros"
    
    if fornecedor_id:
        query_base += f" WHERE fornecedor_id = {fornecedor_id}"
    
    query_base += " GROUP BY status"
    
    resultados = Database.executar(query_base, fetchall=True) or []
    
    stats = {
        'total_repasses': 0,
        'total_valor': 0,
        'pendente': {'qtd': 0, 'valor': 0},
        'concluido': {'qtd': 0, 'valor': 0},
        'cancelado': {'qtd': 0, 'valor': 0}
    }
    
    for r in resultados:
        status = r['status']
        qtd = int(r['total']) if r['total'] else 0
        valor = float(r['soma']) if r['soma'] else 0
        
        stats['total_repasses'] += qtd
        stats['total_valor'] += valor
        
        if status in stats:
            stats[status] = {'qtd': qtd, 'valor': valor}
    
    return stats
