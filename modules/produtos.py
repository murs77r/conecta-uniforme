"""
============================================
RF03 - GERENCIAR PRODUTOS E VITRINE
============================================
Este módulo é responsável por:
- RF03.1: Cadastrar Produto
- RF03.2: Consultar Produto
- RF03.3: Editar Produto
- RF03.4: Excluir Produto

Gerencia o catálogo de produtos disponíveis no sistema, permitindo manutenção e exibição em vitrine.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import executar_query, registrar_log, formatar_dinheiro
from modules.autenticacao import verificar_sessao, verificar_permissao
import json

# Blueprint
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')

# RF03.2 - Listar (Vitrine)
@produtos_bp.route('/')
@produtos_bp.route('/vitrine')
def vitrine():
    usuario_logado = verificar_sessao()
    
    filtro_categoria = request.args.get('categoria', '')
    filtro_escola = request.args.get('escola', '')
    filtro_busca = request.args.get('busca', '')
    
    query = """
        SELECT p.*, f.razao_social as fornecedor_nome, e.razao_social as escola_nome
        FROM produtos p
        JOIN fornecedores f ON p.fornecedor_id = f.id
        LEFT JOIN escolas e ON p.escola_id = e.id
        WHERE p.ativo = TRUE AND p.estoque > 0
    """
    parametros = []
    
    if filtro_categoria:
        query += " AND p.categoria = %s"
        parametros.append(filtro_categoria)
    
    if filtro_escola:
        query += " AND p.escola_id = %s"
        parametros.append(filtro_escola)
    
    if filtro_busca:
        query += " AND (p.nome ILIKE %s OR p.descricao ILIKE %s)"
        busca_param = f"%{filtro_busca}%"
        parametros.extend([busca_param, busca_param])
    
    query += " ORDER BY p.nome"
    
    produtos = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    if not produtos:
        produtos = []
    
    # Busca escolas para filtro
    query_escolas = "SELECT e.id, u.nome FROM escolas e JOIN usuarios u ON e.usuario_id = u.id WHERE e.ativo = TRUE ORDER BY u.nome"
    escolas = executar_query(query_escolas, fetchall=True)
    
    if not escolas:
        escolas = []
    
    return render_template('produtos/vitrine.html', 
                         produtos=produtos,
                         escolas=escolas,
                         filtro_categoria=filtro_categoria,
                         filtro_escola=filtro_escola,
                         filtro_busca=filtro_busca)

# RF03.1 - Cadastrar
@produtos_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    usuario_logado = verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        # Busca fornecedor do usuário logado
        fornecedor_id = None
        if usuario_logado['tipo'] == 'fornecedor':
            query_forn = "SELECT id FROM fornecedores WHERE usuario_id = %s"
            forn = executar_query(query_forn, (usuario_logado['id'],), fetchone=True)
            if forn:
                fornecedor_id = forn['id']
        
        # Busca escolas
        query_escolas = "SELECT e.id, u.nome FROM escolas e JOIN usuarios u ON e.usuario_id = u.id WHERE e.ativo = TRUE ORDER BY u.nome"
        escolas = executar_query(query_escolas, fetchall=True)
        
        return render_template('produtos/cadastrar.html', escolas=escolas or [], fornecedor_id=fornecedor_id)
    
    # Pega dados do formulário
    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()
    categoria = request.form.get('categoria', '').strip()
    tamanho = request.form.get('tamanho', '').strip()
    cor = request.form.get('cor', '').strip()
    preco = request.form.get('preco', '0').strip().replace(',', '.')
    estoque = request.form.get('estoque', '0').strip()
    escola_id = request.form.get('escola_id', '').strip()
    
    # Pega o fornecedor_id
    if usuario_logado['tipo'] == 'fornecedor':
        query_forn = "SELECT id FROM fornecedores WHERE usuario_id = %s"
        forn = executar_query(query_forn, (usuario_logado['id'],), fetchone=True)
        fornecedor_id = forn['id'] if forn else None
    else:
        fornecedor_id = request.form.get('fornecedor_id')
    
    if not nome or not fornecedor_id or not preco:
        flash('Preencha os campos obrigatórios.', 'danger')
        return redirect(url_for('produtos.cadastrar'))
    
    # Insere produto
    query = """
        INSERT INTO produtos (fornecedor_id, escola_id, nome, descricao, categoria, tamanho, cor, preco, estoque, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
    """
    resultado = executar_query(query, 
                              (fornecedor_id, escola_id or None, nome, descricao, categoria, tamanho, cor, preco, estoque),
                              fetchone=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'produtos', resultado['id'], 'INSERT')
        flash('Produto cadastrado!', 'success')
        return redirect(url_for('produtos.vitrine'))
    
    flash('Erro ao cadastrar.', 'danger')
    return redirect(url_for('produtos.cadastrar'))

# RF03.3 - Editar
@produtos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario_logado = verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query_buscar = "SELECT * FROM produtos WHERE id = %s"
    produto = executar_query(query_buscar, (id,), fetchone=True)
    
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    if request.method == 'GET':
        return render_template('produtos/editar.html', produto=produto)
    
    # Atualiza
    nome = request.form.get('nome', '').strip()
    preco = request.form.get('preco', '0').strip().replace(',', '.')
    estoque = request.form.get('estoque', '0').strip()
    
    query_update = """
        UPDATE produtos 
        SET nome = %s, preco = %s, estoque = %s, data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    resultado = executar_query(query_update, (nome, preco, estoque, id), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'produtos', id, 'UPDATE')
        flash('Produto atualizado!', 'success')
    
    return redirect(url_for('produtos.vitrine'))

# RF03.4 - Excluir
@produtos_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    usuario_logado = verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    # Impedir exclusão se houver itens de pedido vinculados
    q_itens = "SELECT COUNT(*) AS total FROM itens_pedido WHERE produto_id = %s"
    r_itens = executar_query(q_itens, (id,), fetchone=True)
    if r_itens and int(r_itens['total']) > 0:
        flash('Não é possível excluir: produto já está presente em pedidos.', 'warning')
        return redirect(url_for('produtos.vitrine'))

    query_excluir = "DELETE FROM produtos WHERE id = %s"
    resultado = executar_query(query_excluir, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'produtos', id, 'DELETE')
        flash('Produto excluído!', 'success')
    
    return redirect(url_for('produtos.vitrine'))