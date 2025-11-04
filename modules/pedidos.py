"""
============================================
RF06 - GERENCIAR PEDIDOS
============================================
Este módulo é responsável por:
- RF06.1: Cadastrar Pedido
- RF06.2: Consultar Pedido
- RF06.3: Editar Pedido
- RF06.4: Excluir Pedido

Gerencia os pedidos realizados no sistema, desde a criação até a manutenção de seus registros.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import executar_query, registrar_log, formatar_dinheiro
from modules.autenticacao import verificar_sessao, verificar_permissao
from datetime import datetime
import json

# Blueprint
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

# RF06.2 - Listar pedidos
@pedidos_bp.route('/')
@pedidos_bp.route('/listar')
def listar():
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    query = """
        SELECT p.*, r.usuario_id, u.nome as responsavel_nome
        FROM pedidos p
        JOIN responsaveis r ON p.responsavel_id = r.id
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE p.status != 'carrinho'
    """
    parametros = []
    
    # Se for responsável, mostra apenas seus pedidos
    if usuario_logado['tipo'] == 'responsavel':
        query_resp = "SELECT id FROM responsaveis WHERE usuario_id = %s"
        resp = executar_query(query_resp, (usuario_logado['id'],), fetchone=True)
        if resp:
            query += " AND p.responsavel_id = %s"
            parametros.append(resp['id'])
    
    query += " ORDER BY p.data_pedido DESC"
    
    pedidos = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    if not pedidos:
        pedidos = []
    
    return render_template('pedidos/listar.html', pedidos=pedidos)

# RF06.1 - Adicionar ao carrinho
@pedidos_bp.route('/adicionar-carrinho/<int:produto_id>', methods=['POST'])
def adicionar_carrinho(produto_id):
    usuario_logado = verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o responsável
    query_resp = "SELECT id FROM responsaveis WHERE usuario_id = %s"
    responsavel = executar_query(query_resp, (usuario_logado['id'],), fetchone=True)
    
    if not responsavel:
        flash('Responsável não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    # Busca o produto
    query_produto = "SELECT * FROM produtos WHERE id = %s AND ativo = TRUE"
    produto = executar_query(query_produto, (produto_id,), fetchone=True)
    
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    quantidade = int(request.form.get('quantidade', 1))
    
    # Verifica estoque
    if quantidade > produto['estoque']:
        flash('Quantidade indisponível em estoque.', 'warning')
        return redirect(url_for('produtos.vitrine'))
    
    # Busca ou cria carrinho (pedido com status 'carrinho')
    query_carrinho = """
        SELECT id FROM pedidos 
        WHERE responsavel_id = %s AND status = 'carrinho'
        ORDER BY data_pedido DESC LIMIT 1
    """
    carrinho = executar_query(query_carrinho, (responsavel['id'],), fetchone=True)
    
    if not carrinho:
        # Cria novo carrinho
        query_novo = """
            INSERT INTO pedidos (responsavel_id, escola_id, status, valor_total)
            VALUES (%s, %s, 'carrinho', 0)
            RETURNING id
        """
        carrinho = executar_query(query_novo, (responsavel['id'], produto['escola_id']), fetchone=True)
    
    if not carrinho:
        flash('Erro ao criar carrinho.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    pedido_id = carrinho['id']
    
    # Adiciona item ao carrinho
    subtotal = float(produto['preco']) * quantidade
    
    query_item = """
        INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
        VALUES (%s, %s, %s, %s, %s)
    """
    executar_query(query_item, (pedido_id, produto_id, quantidade, produto['preco'], subtotal), commit=True)
    
    # Atualiza valor total do pedido
    query_total = "SELECT SUM(subtotal) as total FROM itens_pedido WHERE pedido_id = %s"
    total = executar_query(query_total, (pedido_id,), fetchone=True)
    
    query_update = "UPDATE pedidos SET valor_total = %s WHERE id = %s"
    executar_query(query_update, (total['total'], pedido_id), commit=True)
    
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('pedidos.ver_carrinho'))

# Ver carrinho
@pedidos_bp.route('/carrinho')
def ver_carrinho():
    usuario_logado = verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query_resp = "SELECT id FROM responsaveis WHERE usuario_id = %s"
    responsavel = executar_query(query_resp, (usuario_logado['id'],), fetchone=True)
    
    if not responsavel:
        return render_template('pedidos/carrinho.html', itens=[], pedido=None)
    
    query_carrinho = """
        SELECT * FROM pedidos 
        WHERE responsavel_id = %s AND status = 'carrinho'
        ORDER BY data_pedido DESC LIMIT 1
    """
    pedido = executar_query(query_carrinho, (responsavel['id'],), fetchone=True)
    
    if not pedido:
        return render_template('pedidos/carrinho.html', itens=[], pedido=None)
    
    query_itens = """
        SELECT i.*, p.nome as produto_nome, p.descricao, p.imagem_url
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
    """
    itens = executar_query(query_itens, (pedido['id'],), fetchall=True)
    
    return render_template('pedidos/carrinho.html', itens=itens or [], pedido=pedido)

# RF06.1 - Finalizar pedido
@pedidos_bp.route('/finalizar/<int:id>', methods=['POST'])
def finalizar(id):
    usuario_logado = verificar_permissao(['responsavel'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Atualiza status do pedido
    query = "UPDATE pedidos SET status = 'pendente', data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s"
    resultado = executar_query(query, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido finalizado')
        flash('Pedido realizado com sucesso!', 'success')
    
    return redirect(url_for('pedidos.listar'))

# RF06.4 - Cancelar
@pedidos_bp.route('/cancelar/<int:id>', methods=['POST'])
def cancelar(id):
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query = "UPDATE pedidos SET status = 'cancelado' WHERE id = %s"
    resultado = executar_query(query, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido cancelado')
        flash('Pedido cancelado!', 'success')
    
    return redirect(url_for('pedidos.listar'))