"""
============================================
RF06 - GERENCIAR PEDIDOS (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import PedidoRepository, ProdutoRepository, ResponsavelRepository
from core.services import AutenticacaoService, LogService
from core.database import Database
from core.pagination import paginate_query, Pagination

# Blueprint e Serviços
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')
pedido_repo = PedidoRepository()
produto_repo = ProdutoRepository()
responsavel_repo = ResponsavelRepository()
auth_service = AutenticacaoService()


# ============================================
# RF06.2 - LISTAR PEDIDOS
# ============================================

@pedidos_bp.route('/')
@pedidos_bp.route('/listar')
def listar():
    """Lista pedidos com paginação e filtros"""
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
        'responsavel_id': request.args.get('responsavel_id', ''),
        'escola_id': request.args.get('escola_id', ''),
        'fornecedor_id': request.args.get('fornecedor_id', ''),
        'data_inicio': request.args.get('data_inicio', ''),
        'data_fim': request.args.get('data_fim', ''),
        'valor_min': request.args.get('valor_min', ''),
        'valor_max': request.args.get('valor_max', '')
    }
    
    # Base query
    query = """
        SELECT p.*, 
               r.usuario_id, 
               u.nome as responsavel_nome,
               e.id as escola_id,
               e_usr.nome as escola_nome
        FROM pedidos p
        JOIN responsaveis r ON p.responsavel_id = r.id
        JOIN usuarios u ON r.usuario_id = u.id
        LEFT JOIN escolas e ON p.escola_id = e.id
        LEFT JOIN usuarios e_usr ON e.usuario_id = e_usr.id
        WHERE p.status != 'carrinho'
    """
    params = []
    
    # Se for responsável, mostra apenas seus pedidos
    if usuario_logado['tipo'] == 'responsavel':
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if responsavel:
            query += " AND p.responsavel_id = %s"
            params.append(responsavel['id'])
        else:
            pedidos = []
            pagination = Pagination(page=1, per_page=per_page, total=0)
            estatisticas = _calcular_estatisticas_pedidos(None)
            responsaveis = []
            return render_template('pedidos/listar.html',
                                 pedidos=pedidos,
                                 pagination=pagination,
                                 filtros=filtros,
                                 estatisticas=estatisticas,
                                 responsaveis=responsaveis)
    
    # Aplicar filtros
    if filtros['status']:
        query += " AND p.status = %s"
        params.append(filtros['status'])
    
    if filtros['responsavel_id']:
        query += " AND p.responsavel_id = %s"
        params.append(int(filtros['responsavel_id']))
    
    if filtros['escola_id']:
        query += " AND p.escola_id = %s"
        params.append(int(filtros['escola_id']))
    
    if filtros['fornecedor_id']:
        query += """ AND EXISTS (
            SELECT 1 FROM itens_pedido ip
            JOIN produtos prod ON ip.produto_id = prod.id
            WHERE ip.pedido_id = p.id AND prod.fornecedor_id = %s
        )"""
        params.append(int(filtros['fornecedor_id']))
    
    if filtros['data_inicio']:
        query += " AND p.data_pedido >= %s"
        params.append(filtros['data_inicio'])
    
    if filtros['data_fim']:
        query += " AND p.data_pedido <= %s"
        params.append(filtros['data_fim'])
    
    if filtros['valor_min']:
        query += " AND p.valor_total >= %s"
        params.append(float(filtros['valor_min']))
    
    if filtros['valor_max']:
        query += " AND p.valor_total <= %s"
        params.append(float(filtros['valor_max']))
    
    # Ordenação
    query += " ORDER BY p.data_pedido DESC"
    
    # Paginar
    paginated_query, paginated_params, pagination = paginate_query(
        query, tuple(params), page, per_page
    )
    
    # Executar query
    pedidos = Database.executar(paginated_query, paginated_params, fetchall=True) or []
    
    # Calcular estatísticas
    responsavel_id_filtro = None
    if usuario_logado['tipo'] == 'responsavel':
        responsavel_id_filtro = responsavel['id'] if responsavel else None
    estatisticas = _calcular_estatisticas_pedidos(responsavel_id_filtro)
    
    # Lista de responsáveis para o filtro (apenas admin)
    responsaveis = []
    escolas = []
    fornecedores = []
    
    if usuario_logado['tipo'] in ['administrador', 'escola']:
        query_responsaveis = """
            SELECT r.id, u.nome
            FROM responsaveis r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE u.ativo = TRUE
            ORDER BY u.nome
        """
        responsaveis = Database.executar(query_responsaveis, fetchall=True) or []
    
    if usuario_logado['tipo'] == 'administrador':
        query_escolas = """
            SELECT e.id, u.nome
            FROM escolas e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE u.ativo = TRUE
            ORDER BY u.nome
        """
        escolas = Database.executar(query_escolas, fetchall=True) or []
        
        query_fornecedores = """
            SELECT f.id, u.nome, f.razao_social
            FROM fornecedores f
            JOIN usuarios u ON f.usuario_id = u.id
            WHERE u.ativo = TRUE
            ORDER BY u.nome
        """
        fornecedores = Database.executar(query_fornecedores, fetchall=True) or []
    
    return render_template('pedidos/listar.html',
                         pedidos=pedidos,
                         pagination=pagination,
                         filtros=filtros,
                         estatisticas=estatisticas,
                         responsaveis=responsaveis,
                         escolas=escolas,
                         fornecedores=fornecedores)


# ============================================
# RF06.1 - ADICIONAR AO CARRINHO
# ============================================

@pedidos_bp.route('/adicionar-carrinho/<int:produto_id>', methods=['POST'])
def adicionar_carrinho(produto_id):
    """Adiciona produto ao carrinho"""
    usuario_logado = auth_service.verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o responsável
    responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not responsavel:
        flash('Responsável não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    # Busca o produto
    produto = produto_repo.buscar_por_id(produto_id)
    if not produto or not produto.get('ativo'):
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    quantidade = int(request.form.get('quantidade', 1))
    
    # Verifica estoque
    if quantidade > produto['estoque']:
        flash('Quantidade indisponível em estoque.', 'warning')
        return redirect(url_for('produtos.vitrine'))
    
    # Busca ou cria carrinho
    carrinho = pedido_repo.buscar_carrinho(responsavel['id'])
    
    if not carrinho:
        # Cria novo carrinho
        dados_pedido = {
            'responsavel_id': responsavel['id'],
            'escola_id': produto['escola_id'],
            'status': 'carrinho',
            'valor_total': 0
        }
        pedido_id = Database.inserir('pedidos', dados_pedido)
    else:
        pedido_id = carrinho['id']
    
    if not pedido_id:
        flash('Erro ao criar carrinho.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    # Adiciona item ao carrinho
    subtotal = float(produto['preco']) * quantidade
    
    dados_item = {
        'pedido_id': pedido_id,
        'produto_id': produto_id,
        'quantidade': quantidade,
        'preco_unitario': produto['preco'],
        'subtotal': subtotal
    }
    Database.inserir('itens_pedido', dados_item)
    
    # Atualiza valor total do pedido
    query_total = "SELECT SUM(subtotal) as total FROM itens_pedido WHERE pedido_id = %s"
    total = Database.executar(query_total, (pedido_id,), fetchone=True)
    
    Database.atualizar('pedidos', pedido_id, {'valor_total': total['total'] if total else 0})
    
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('pedidos.ver_carrinho'))


# ============================================
# VER CARRINHO
# ============================================

@pedidos_bp.route('/carrinho')
def ver_carrinho():
    """Exibe carrinho do responsável"""
    usuario_logado = auth_service.verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not responsavel:
        return render_template('pedidos/carrinho.html', itens=[], pedido=None)
    
    pedido = pedido_repo.buscar_carrinho(responsavel['id'])
    if not pedido:
        return render_template('pedidos/carrinho.html', itens=[], pedido=None)
    
    # Busca itens do carrinho
    query_itens = """
        SELECT i.*, p.nome as produto_nome, p.descricao, p.imagem_url
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
    """
    itens = Database.executar(query_itens, (pedido['id'],), fetchall=True) or []
    
    return render_template('pedidos/carrinho.html', itens=itens, pedido=pedido)


# ============================================
# RF06.1 - FINALIZAR PEDIDO
# ============================================

@pedidos_bp.route('/finalizar/<int:id>', methods=['POST'])
def finalizar(id):
    """Finaliza um pedido (muda status de carrinho para pendente)"""
    usuario_logado = auth_service.verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if Database.atualizar('pedidos', id, {'status': 'pendente'}):
        LogService.registrar(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido finalizado')
        flash('Pedido realizado com sucesso!', 'success')
    
    return redirect(url_for('pedidos.listar'))


# ============================================
# RF06.4 - CANCELAR PEDIDO
# ============================================

@pedidos_bp.route('/cancelar/<int:id>', methods=['POST'])
def cancelar(id):
    """Cancela um pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if Database.atualizar('pedidos', id, {'status': 'cancelado'}):
        LogService.registrar(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido cancelado')
        flash('Pedido cancelado!', 'success')
    
    return redirect(url_for('pedidos.listar'))


# ============================================
# VISUALIZAR DETALHES DO PEDIDO
# ============================================

@pedidos_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """Visualiza detalhes completos de um pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca o pedido com todas as informações
    query_pedido = """
        SELECT p.*, 
               r.cpf as responsavel_cpf,
               u.telefone as responsavel_telefone,
               r.endereco as responsavel_endereco,
               u.nome as responsavel_nome,
               u.email as responsavel_email,
               e.id as escola_id,
               e_usr.nome as escola_nome,
               e.cnpj as escola_cnpj,
               e.endereco as escola_endereco
        FROM pedidos p
        JOIN responsaveis r ON p.responsavel_id = r.id
        JOIN usuarios u ON r.usuario_id = u.id
        LEFT JOIN escolas e ON p.escola_id = e.id
        LEFT JOIN usuarios e_usr ON e.usuario_id = e_usr.id
        WHERE p.id = %s
    """
    pedido = Database.executar(query_pedido, (id,), fetchone=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # Verifica permissão
    if usuario_logado['tipo'] == 'responsavel':
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not responsavel or pedido['responsavel_id'] != responsavel['id']:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.listar'))
    
    # Busca itens do pedido com informações do produto e fornecedor
    query_itens = """
        SELECT i.*, 
               p.nome as produto_nome, 
               p.descricao as produto_descricao, 
               p.imagem_url as produto_imagem,
               p.fornecedor_id,
               f_usr.nome as fornecedor_nome,
               f.razao_social as fornecedor_razao_social
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        LEFT JOIN usuarios f_usr ON f.usuario_id = f_usr.id
        WHERE i.pedido_id = %s
        ORDER BY i.id
    """
    itens = Database.executar(query_itens, (id,), fetchall=True) or []
    
    # Agrupa itens por fornecedor
    itens_por_fornecedor = {}
    for item in itens:
        forn_id = item.get('fornecedor_id')
        forn_nome = item.get('fornecedor_nome', 'Sem fornecedor')
        
        if forn_id not in itens_por_fornecedor:
            itens_por_fornecedor[forn_id] = {
                'fornecedor_nome': forn_nome,
                'fornecedor_razao_social': item.get('fornecedor_razao_social', ''),
                'itens': [],
                'subtotal': 0
            }
        
        itens_por_fornecedor[forn_id]['itens'].append(item)
        itens_por_fornecedor[forn_id]['subtotal'] += float(item.get('subtotal', 0))
    
    return render_template('pedidos/detalhes.html', 
                         pedido=pedido, 
                         itens=itens,
                         itens_por_fornecedor=itens_por_fornecedor)


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _calcular_estatisticas_pedidos(responsavel_id=None):
    """Calcula estatísticas dos pedidos"""
    query_base = """
        SELECT status, COUNT(*) as total, SUM(valor_total) as soma 
        FROM pedidos 
        WHERE status != 'carrinho'
    """
    
    if responsavel_id:
        query_base += f" AND responsavel_id = {responsavel_id}"
    
    query_base += " GROUP BY status"
    
    resultados = Database.executar(query_base, fetchall=True) or []
    
    stats = {
        'total_pedidos': 0,
        'total_valor': 0,
        'pendente': {'qtd': 0, 'valor': 0},
        'pago': {'qtd': 0, 'valor': 0},
        'enviado': {'qtd': 0, 'valor': 0},
        'entregue': {'qtd': 0, 'valor': 0},
        'cancelado': {'qtd': 0, 'valor': 0}
    }
    
    for r in resultados:
        status = r['status']
        qtd = int(r['total']) if r['total'] else 0
        valor = float(r['soma']) if r['soma'] else 0
        
        stats['total_pedidos'] += qtd
        stats['total_valor'] += valor
        
        if status in stats:
            stats[status] = {'qtd': qtd, 'valor': valor}
    
    return stats
