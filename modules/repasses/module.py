"""
============================================
RF07 - GERENCIAR REPASSES FINANCEIROS (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import RepasseFinanceiroRepository, FornecedorRepository
from core.services import AutenticacaoService, LogService
from core.database import Database
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
    """Lista repasses financeiros"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Se for fornecedor, mostra apenas seus repasses
    if usuario_logado['tipo'] == 'fornecedor':
        fornecedor = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        fornecedor_id = fornecedor['id'] if fornecedor else None
        repasses = repasse_repo.listar_com_fornecedor(fornecedor_id) if fornecedor_id else []
    else:
        repasses = repasse_repo.listar_com_fornecedor()
    
    return render_template('repasses/listar.html', repasses=repasses)


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
