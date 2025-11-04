"""
============================================
RF07 - GERENCIAR REPASSES FINANCEIROS
============================================
Este módulo é responsável por:
- RF07.1: Cadastrar Repasse Financeiro
- RF07.2: Consultar Repasse Financeiro
- RF07.3: Editar Repasse Financeiro
- RF07.4: Excluir Repasse Financeiro

Gerencia os repasses financeiros vinculados ao sistema, permitindo controle e manutenção das movimentações.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import executar_query, registrar_log, formatar_dinheiro
from modules.autenticacao import verificar_sessao, verificar_permissao
from config import TAXA_PLATAFORMA_PERCENTUAL
import json

# Blueprint
repasses_bp = Blueprint('repasses', __name__, url_prefix='/repasses')

# RF07.2 - Listar
@repasses_bp.route('/')
@repasses_bp.route('/listar')
def listar():
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    query = """
        SELECT r.*, f.razao_social as fornecedor_nome, u.nome
        FROM repasses_financeiros r
        JOIN fornecedores f ON r.fornecedor_id = f.id
        JOIN usuarios u ON f.usuario_id = u.id
    """
    parametros = []
    
    # Se for fornecedor, mostra apenas seus repasses
    if usuario_logado['tipo'] == 'fornecedor':
        query_forn = "SELECT id FROM fornecedores WHERE usuario_id = %s"
        forn = executar_query(query_forn, (usuario_logado['id'],), fetchone=True)
        if forn:
            query += " WHERE r.fornecedor_id = %s"
            parametros.append(forn['id'])
    
    query += " ORDER BY r.data_repasse DESC"
    
    repasses = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    if not repasses:
        repasses = []
    
    return render_template('repasses/listar.html', repasses=repasses)

# RF07.1 - Gerar repasse (admin)
@repasses_bp.route('/gerar/<int:pedido_id>', methods=['POST'])
def gerar(pedido_id):
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o pedido
    query_pedido = "SELECT * FROM pedidos WHERE id = %s AND status = 'pago'"
    pedido = executar_query(query_pedido, (pedido_id,), fetchone=True)
    
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
    itens_por_fornecedor = executar_query(query_itens, (pedido_id,), fetchall=True)
    
    if not itens_por_fornecedor:
        flash('Nenhum item encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # Cria repasses para cada fornecedor
    for item in itens_por_fornecedor:
        valor = float(item['valor_total'])
        taxa = valor * (TAXA_PLATAFORMA_PERCENTUAL / 100)
        valor_liquido = valor - taxa
        
        query_repasse = """
            INSERT INTO repasses_financeiros 
            (fornecedor_id, pedido_id, valor, taxa_plataforma, valor_liquido, status)
            VALUES (%s, %s, %s, %s, %s, 'pendente')
        """
        executar_query(query_repasse, 
                      (item['fornecedor_id'], pedido_id, valor, taxa, valor_liquido),
                      commit=True)
    
    flash('Repasses gerados com sucesso!', 'success')
    return redirect(url_for('repasses.listar'))

# RF07.3 - Processar repasse
@repasses_bp.route('/processar/<int:id>', methods=['POST'])
def processar(id):
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query = """
        UPDATE repasses_financeiros 
        SET status = 'concluido', data_processamento = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    resultado = executar_query(query, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'repasses_financeiros', id, 'UPDATE', descricao='Repasse processado')
        flash('Repasse processado!', 'success')
    
    return redirect(url_for('repasses.listar'))

# RF07.4 - Cancelar repasse
@repasses_bp.route('/cancelar/<int:id>', methods=['POST'])
def cancelar(id):
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query = "UPDATE repasses_financeiros SET status = 'cancelado' WHERE id = %s"
    resultado = executar_query(query, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'repasses_financeiros', id, 'UPDATE', descricao='Repasse cancelado')
        flash('Repasse cancelado!', 'success')
    
    return redirect(url_for('repasses.listar'))