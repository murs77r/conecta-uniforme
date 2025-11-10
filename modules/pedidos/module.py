"""
============================================
RF08 - MANTER CADASTRO DE PEDIDO
============================================
Este módulo é responsável por:
- RF08.1: Criar pedido
- RF08.2: Apagar pedido
- RF08.3: Editar pedido
- RF08.4: Consultar pedidos

Controla o processo de controle de pedidos no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import PedidoRepository, ResponsavelRepository
from core.services import AutenticacaoService, LogService
from core.database import Database
from core.pagination import paginate_query, Pagination

# Blueprint e Serviços
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')
pedido_repo = PedidoRepository()
responsavel_repo = ResponsavelRepository()
auth_service = AutenticacaoService()


# ============================================
# RF08.4 - CONSULTAR PEDIDOS
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
            return render_template('pedidos/listar.html',
                                 pedidos=pedidos,
                                 pagination=pagination,
                                 filtros=filtros)
    
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
    
    return render_template('pedidos/listar.html',
                         pedidos=pedidos,
                         pagination=pagination,
                         filtros=filtros)


# ============================================
# RF08.1 - CRIAR PEDIDO
# ============================================

@pedidos_bp.route('/criar', methods=['GET', 'POST'])
def criar():
    """Cria um novo pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    if request.method == 'POST':
        dados = {
            'responsavel_id': request.form.get('responsavel_id'),
            'escola_id': request.form.get('escola_id'),
            'status': request.form.get('status', 'pendente'),
            'valor_total': request.form.get('valor_total', 0)
        }
        
        pedido_id = Database.inserir('pedidos', dados)
        if pedido_id:
            LogService.registrar(usuario_logado['id'], 'pedidos', pedido_id, 'INSERT', descricao='Pedido criado')
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('pedidos.listar'))
        else:
            flash('Erro ao criar pedido.', 'danger')
    
    # GET - Exibe formulário
    return render_template('pedidos/criar.html')


# ============================================
# RF08.3 - EDITAR PEDIDO
# ============================================

@pedidos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita um pedido existente"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca o pedido
    query = "SELECT * FROM pedidos WHERE id = %s"
    pedido = Database.executar(query, (id,), fetchone=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    if request.method == 'POST':
        dados = {
            'status': request.form.get('status'),
            'valor_total': request.form.get('valor_total')
        }
        
        if Database.atualizar('pedidos', id, dados):
            LogService.registrar(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido editado')
            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('pedidos.listar'))
        else:
            flash('Erro ao atualizar pedido.', 'danger')
    
    # GET - Exibe formulário
    return render_template('pedidos/editar.html', pedido=pedido)


# ============================================
# RF08.2 - APAGAR PEDIDO
# ============================================

@pedidos_bp.route('/apagar/<int:id>', methods=['POST'])
def apagar(id):
    """Apaga um pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query = "DELETE FROM pedidos WHERE id = %s"
    if Database.executar(query, (id,)):
        LogService.registrar(usuario_logado['id'], 'pedidos', id, 'DELETE', descricao='Pedido apagado')
        flash('Pedido apagado com sucesso!', 'success')
    else:
        flash('Erro ao apagar pedido.', 'danger')
    
    return redirect(url_for('pedidos.listar'))


# ============================================
# RF08.4 - CONSULTAR DETALHES DO PEDIDO
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
    
    # Busca itens do pedido
    query_itens = """
        SELECT i.*, 
               p.nome as produto_nome, 
               p.descricao as produto_descricao, 
               p.imagem_url as produto_imagem
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
        ORDER BY i.id
    """
    itens = Database.executar(query_itens, (id,), fetchall=True) or []
    
    return render_template('pedidos/detalhes.html', pedido=pedido, itens=itens)