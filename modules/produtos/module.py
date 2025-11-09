"""
============================================
RF05 - MANTER CADASTRO DE PRODUTO
============================================
Este módulo é responsável por:
- RF05.1: Criar produto
- RF05.2: Apagar produto
- RF05.3: Editar produto
- RF05.4: Consultar produto

Controla o processo de controle de produtos no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import ProdutoRepository, FornecedorRepository
from core.services import AutenticacaoService, CRUDService, LogService
from core.database import Database

# Blueprint
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')

# Repositories e Services
produto_repo = ProdutoRepository()
fornecedor_repo = FornecedorRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(produto_repo, 'Produto')


@produtos_bp.route('/')
@produtos_bp.route('/vitrine')
def vitrine():
    """Vitrine de produtos"""
    usuario_logado = auth_service.verificar_sessao()
    
    filtros = {
        'categoria': request.args.get('categoria', ''),
        'escola': request.args.get('escola', ''),
        'busca': request.args.get('busca', '')
    }
    
    produtos = produto_repo.listar_vitrine(filtros)
    
    # Busca escolas para filtro
    query_escolas = """
        SELECT e.id, u.nome FROM escolas e 
        JOIN usuarios u ON e.usuario_id = u.id 
        WHERE e.ativo = TRUE ORDER BY u.nome
    """
    escolas = Database.executar(query_escolas, fetchall=True) or []
    
    return render_template('produtos/vitrine.html', 
                         produtos=produtos, escolas=escolas,
                         filtro_categoria=filtros['categoria'],
                         filtro_escola=filtros['escola'],
                         filtro_busca=filtros['busca'])


@produtos_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Cadastra produto"""
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        fornecedor_id = None
        if usuario_logado['tipo'] == 'fornecedor':
            forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
            fornecedor_id = forn['id'] if forn else None
        
        query_escolas = """
            SELECT e.id, u.nome FROM escolas e 
            JOIN usuarios u ON e.usuario_id = u.id 
            WHERE e.ativo = TRUE ORDER BY u.nome
        """
        escolas = Database.executar(query_escolas, fetchall=True) or []
        
        return render_template('produtos/cadastrar.html', 
                             escolas=escolas, fornecedor_id=fornecedor_id)
    
    # POST - coleta dados
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'descricao': request.form.get('descricao', '').strip(),
        'categoria': request.form.get('categoria', '').strip(),
        'tamanho': request.form.get('tamanho', '').strip(),
        'cor': request.form.get('cor', '').strip(),
        'preco': request.form.get('preco', '0').strip().replace(',', '.'),
        'estoque': request.form.get('estoque', '0').strip(),
        'escola_id': request.form.get('escola_id', '').strip() or None,
        'ativo': True
    }
    
    # Determina fornecedor
    if usuario_logado['tipo'] == 'fornecedor':
        forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        dados['fornecedor_id'] = forn['id'] if forn else None
    else:
        dados['fornecedor_id'] = request.form.get('fornecedor_id')
    
    if not dados['nome'] or not dados['fornecedor_id'] or not dados['preco']:
        flash('Preencha os campos obrigatórios.', 'danger')
        return redirect(url_for('produtos.cadastrar'))
    
    produto_id = crud_service.criar_com_log(dados, usuario_logado['id'])
    if produto_id:
        return redirect(url_for('produtos.vitrine'))
    
    return redirect(url_for('produtos.cadastrar'))


@produtos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita produto"""
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    produto = produto_repo.buscar_por_id(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    if request.method == 'GET':
        return render_template('produtos/editar.html', produto=produto)
    
    # POST - atualiza
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'preco': request.form.get('preco', '0').strip().replace(',', '.'),
        'estoque': request.form.get('estoque', '0').strip()
    }
    
    if crud_service.atualizar_com_log(id, dados, dict(produto), usuario_logado['id']):
        return redirect(url_for('produtos.vitrine'))
    
    return render_template('produtos/editar.html', produto=produto)


@produtos_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui produto"""
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    produto = produto_repo.buscar_por_id(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    
    # Verifica dependências
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'itens_pedido', 'campo': 'produto_id', 'mensagem': 'itens de pedido'}
    ])
    
    if bloqueios:
        flash(f"Não é possível excluir: {' '.join(bloqueios)}", 'warning')
        return redirect(url_for('produtos.vitrine'))
    
    crud_service.excluir_com_log(id, dict(produto), usuario_logado['id'])
    return redirect(url_for('produtos.vitrine'))
