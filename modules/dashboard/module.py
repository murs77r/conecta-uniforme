"""
============================================
DASHBOARD - ESTATÍSTICAS GERAIS
============================================
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from core.services import AutenticacaoService
from core.database import Database

# Blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
auth_service = AutenticacaoService()


@dashboard_bp.route('/')
def index():
    """Dashboard principal com estatísticas gerais"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Estatísticas gerais
    stats = {}
    
    # Usuários
    query_usuarios = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ativo = TRUE) as ativos,
            COUNT(*) FILTER (WHERE tipo = 'administrador') as administradores,
            COUNT(*) FILTER (WHERE tipo = 'escola') as escolas,
            COUNT(*) FILTER (WHERE tipo = 'fornecedor') as fornecedores,
            COUNT(*) FILTER (WHERE tipo = 'responsavel') as responsaveis
        FROM usuarios
    """
    stats['usuarios'] = Database.executar(query_usuarios, fetchone=True) or {}
    
    # Pedidos
    query_pedidos = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'pendente') as pendentes,
            COUNT(*) FILTER (WHERE status = 'pago') as pagos,
            COUNT(*) FILTER (WHERE status = 'entregue') as entregues,
            SUM(valor_total) as valor_total,
            SUM(CASE WHEN status = 'pago' THEN valor_total ELSE 0 END) as valor_pago
        FROM pedidos
        WHERE status != 'carrinho'
    """
    stats['pedidos'] = Database.executar(query_pedidos, fetchone=True) or {}
    
    # Produtos
    query_produtos = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ativo = TRUE) as ativos,
            SUM(estoque) as estoque_total,
            AVG(preco) as preco_medio
        FROM produtos
    """
    stats['produtos'] = Database.executar(query_produtos, fetchone=True) or {}
    
    # Repasses
    query_repasses = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'pendente') as pendentes,
            COUNT(*) FILTER (WHERE status = 'concluido') as concluidos,
            SUM(valor_liquido) as valor_total,
            SUM(CASE WHEN status = 'pendente' THEN valor_liquido ELSE 0 END) as valor_pendente
        FROM repasses_financeiros
    """
    stats['repasses'] = Database.executar(query_repasses, fetchone=True) or {}
    
    # Últimos pedidos
    query_ultimos_pedidos = """
        SELECT p.*, u.nome as responsavel_nome
        FROM pedidos p
        JOIN responsaveis r ON p.responsavel_id = r.id
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE p.status != 'carrinho'
        ORDER BY p.data_pedido DESC
        LIMIT 10
    """
    ultimos_pedidos = Database.executar(query_ultimos_pedidos, fetchall=True) or []
    
    # Top 5 produtos mais vendidos
    query_top_produtos = """
        SELECT 
            pr.id,
            pr.nome,
            pr.preco,
            COUNT(ip.id) as qtd_vendas,
            SUM(ip.quantidade) as qtd_total,
            SUM(ip.subtotal) as valor_total
        FROM produtos pr
        JOIN itens_pedido ip ON pr.id = ip.produto_id
        JOIN pedidos p ON ip.pedido_id = p.id
        WHERE p.status != 'carrinho'
        GROUP BY pr.id, pr.nome, pr.preco
        ORDER BY qtd_total DESC
        LIMIT 5
    """
    top_produtos = Database.executar(query_top_produtos, fetchall=True) or []
    
    # Pedidos por mês (últimos 6 meses)
    query_pedidos_mes = """
        SELECT 
            TO_CHAR(data_pedido, 'YYYY-MM') as mes,
            COUNT(*) as total,
            SUM(valor_total) as valor
        FROM pedidos
        WHERE status != 'carrinho' 
          AND data_pedido >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY TO_CHAR(data_pedido, 'YYYY-MM')
        ORDER BY mes DESC
    """
    pedidos_por_mes = Database.executar(query_pedidos_mes, fetchall=True) or []
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         ultimos_pedidos=ultimos_pedidos,
                         top_produtos=top_produtos,
                         pedidos_por_mes=pedidos_por_mes)
