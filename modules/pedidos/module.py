"""
============================================
RF06 - GERENCIAR PEDIDOS (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import PedidoRepository, ProdutoRepository, ResponsavelRepository
from core.services import AutenticacaoService, LogService
from core.database import Database

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
    """Lista pedidos"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Se for responsável, mostra apenas seus pedidos
    if usuario_logado['tipo'] == 'responsavel':
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if responsavel:
            pedidos = pedido_repo.listar_por_responsavel(responsavel['id'])
        else:
            pedidos = []
    else:
        # Admin e outros veem todos
        query = """
            SELECT p.*, r.usuario_id, u.nome as responsavel_nome
            FROM pedidos p
            JOIN responsaveis r ON p.responsavel_id = r.id
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE p.status != 'carrinho'
            ORDER BY p.data_pedido DESC
        """
        pedidos = Database.executar(query, fetchall=True) or []
    
    return render_template('pedidos/listar.html', pedidos=pedidos)


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
