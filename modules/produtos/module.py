"""
============================================
RF06 - MANTER CADASTRO DE PRODUTO
============================================
Este módulo é responsável por:
- RF06.1: Listar produtos
- RF06.2: Criar produto
- RF06.3: Editar produto
- RF06.4: Apagar produto

Controla o processo de cadastro de produtos no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import ProdutoRepository, FornecedorRepository
from core.services import AutenticacaoService, CRUDService
from core.database import Database

# ============================================
# CONFIGURAÇÃO DO BLUEPRINT
# ============================================
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')

# ============================================
# INICIALIZAÇÃO DE REPOSITÓRIOS E SERVIÇOS
# ============================================
produto_repo = ProdutoRepository()
fornecedor_repo = FornecedorRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(produto_repo, 'Produto')


# ============================================
# RF06.1 - LISTAR PRODUTO
# ============================================

@produtos_bp.route('/')
@produtos_bp.route('/listar')
def listar():
    """
    Lista todos os produtos cadastrados no sistema.
    
    Returns:
        Renderiza template produtos/listar.html com:
        - produtos: Lista de todos os produtos
    """
    # Verifica se há usuário logado (opcional para listagem)
    usuario_logado = auth_service.verificar_sessao()
    
    # Monta query SQL base
    query = "SELECT * FROM produtos ORDER BY id DESC"
    
    # Executa query e obtém resultados
    produtos = Database.executar(query, fetchall=True) or []
    
    # Renderiza template com dados
    return render_template('produtos/listar.html', produtos=produtos, usuario_logado=usuario_logado)


# ============================================
# RF06.2 - CRIAR PRODUTO
# ============================================

@produtos_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    Cadastra um novo produto no sistema.
    
    Permissões necessárias:
    - Administrador: Pode cadastrar produtos para qualquer fornecedor
    - Fornecedor: Pode cadastrar produtos apenas para seu próprio cadastro
    
    Campos obrigatórios:
    - nome: Nome do produto
    - preco: Preço do produto
    - fornecedor_id: ID do fornecedor responsável
    
    Campos opcionais:
    - descricao: Descrição detalhada do produto
    - categoria: Categoria do produto (Camisa, Calça, Bermuda, Saia, Agasalho)
    - tamanho: Tamanho do produto (P, M, G, etc)
    - cor: Cor do produto
    - estoque: Quantidade em estoque (padrão: 0)
    
    GET: Exibe formulário de cadastro
    POST: Processa dados e cria o produto
    
    Returns:
        GET: Renderiza template produtos/cadastrar.html
        POST: Redireciona para listagem em caso de sucesso
    """
    # Verifica permissão de acesso (apenas administrador ou fornecedor)
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # GET: Exibe formulário de cadastro
    if request.method == 'GET':
        fornecedor_id = None
        
        # Se o usuário for fornecedor, obtém seu ID automaticamente
        if usuario_logado['tipo'] == 'fornecedor':
            forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
            fornecedor_id = forn['id'] if forn else None
        
        return render_template('produtos/cadastrar.html', fornecedor_id=fornecedor_id)
    
    # POST: Processa criação do produto
    # Coleta dados do formulário
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'descricao': request.form.get('descricao', '').strip(),
        'categoria': request.form.get('categoria', '').strip(),
        'tamanho': request.form.get('tamanho', '').strip(),
        'cor': request.form.get('cor', '').strip(),
        'preco': request.form.get('preco', '0').strip().replace(',', '.'),
        'estoque': request.form.get('estoque', '0').strip(),
        'ativo': True  # Produtos são criados como ativos por padrão
    }
    
    # Determina o fornecedor responsável pelo produto
    if usuario_logado['tipo'] == 'fornecedor':
        # Fornecedor: usa seu próprio ID
        forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        dados['fornecedor_id'] = forn['id'] if forn else None
    else:
        # Administrador: pode escolher o fornecedor
        dados['fornecedor_id'] = request.form.get('fornecedor_id')
    
    # Valida campos obrigatórios
    if not dados['nome'] or not dados['fornecedor_id'] or not dados['preco']:
        flash('Preencha os campos obrigatórios.', 'danger')
        return redirect(url_for('produtos.cadastrar'))
    
    # Cria produto no banco de dados (com log automático)
    produto_id = crud_service.criar_com_log(dados, usuario_logado['id'])
    
    if produto_id:
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))
    
    flash('Erro ao cadastrar produto.', 'danger')
    return redirect(url_for('produtos.cadastrar'))


# ============================================
# RF06.3 - EDITAR PRODUTO
# ============================================

@produtos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita um produto existente no sistema.
    
    Permissões necessárias:
    - Administrador: Pode editar qualquer produto
    - Fornecedor: Pode editar apenas produtos de seu próprio cadastro
    
    Campos editáveis:
    - nome: Nome do produto
    - descricao: Descrição detalhada
    - categoria: Categoria do produto
    - tamanho: Tamanho do produto
    - cor: Cor do produto
    - preco: Preço do produto
    - estoque: Quantidade em estoque
    
    Args:
        id: ID do produto a ser editado
    
    GET: Exibe formulário de edição com dados atuais
    POST: Processa alterações e atualiza o produto
    
    Returns:
        GET: Renderiza template produtos/editar.html
        POST: Redireciona para listagem em caso de sucesso
    """
    # Verifica permissão de acesso (apenas administrador ou fornecedor)
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca produto pelo ID
    produto = produto_repo.buscar_por_id(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.listar'))

    # Se o usuário for um fornecedor, verifica se ele é o "dono" do produto
    if usuario_logado['tipo'] == 'fornecedor':
        forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not forn or produto['fornecedor_id'] != forn['id']:
            flash('Você não tem permissão para editar este produto.', 'danger')
            return redirect(url_for('produtos.listar'))
    
    # GET: Exibe formulário de edição
    if request.method == 'GET':
        return render_template('produtos/editar.html', produto=produto)
    
    # POST: Processa atualização do produto
    # Coleta dados do formulário
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'descricao': request.form.get('descricao', '').strip(),
        'categoria': request.form.get('categoria', '').strip(),
        'tamanho': request.form.get('tamanho', '').strip(),
        'cor': request.form.get('cor', '').strip(),
        'preco': request.form.get('preco', '0').strip().replace(',', '.'),
        'estoque': request.form.get('estoque', '0').strip()
    }
    
    # Atualiza produto no banco de dados (com log automático)
    if crud_service.atualizar_com_log(id, dados, dict(produto), usuario_logado['id']):
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))
    
    flash('Erro ao atualizar produto.', 'danger')
    return render_template('produtos/editar.html', produto=produto)


# ============================================
# RF06.4 - APAGAR PRODUTO
# ============================================

@produtos_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """
    Exclui um produto do sistema após validações.
    
    Permissões necessárias:
    - Administrador: Pode excluir qualquer produto
    - Fornecedor: Pode excluir apenas produtos de seu próprio cadastro
    
    Validações realizadas:
    - Verifica se o produto existe
    - Verifica se há dependências (itens de pedido)
    - Bloqueia exclusão se houver dependências
    
    Dependências verificadas:
    - itens_pedido: Verifica se o produto está em algum pedido
    
    Args:
        id: ID do produto a ser excluído
    
    Returns:
        Redireciona para listagem após tentativa de exclusão
        - Sucesso: Flash de confirmação
        - Erro: Flash de erro ou aviso sobre dependências
    """
    # Verifica permissão de acesso (apenas administrador ou fornecedor)
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca produto pelo ID
    produto = produto_repo.buscar_por_id(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.listar'))

    # Se o usuário for um fornecedor, verifica se ele é o "dono" do produto
    if usuario_logado['tipo'] == 'fornecedor':
        forn = fornecedor_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not forn or produto['fornecedor_id'] != forn['id']:
            flash('Você não tem permissão para excluir este produto.', 'danger')
            return redirect(url_for('produtos.listar'))
    
    # Verifica se há dependências que impedem a exclusão
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'itens_pedido', 'campo': 'produto_id', 'mensagem': 'itens de pedido'}
    ])
    
    # Se houver dependências, bloqueia a exclusão
    if bloqueios:
        flash(f"Não é possível excluir: {' '.join(bloqueios)}", 'warning')
        return redirect(url_for('produtos.listar'))
    
    # Exclui produto do banco de dados (com log automático)
    if crud_service.excluir_com_log(id, dict(produto), usuario_logado['id']):
        flash('Produto excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir produto.', 'danger')
    
    return redirect(url_for('produtos.listar'))


# ============================================
# ROTA AUXILIAR: DETALHES DO PRODUTO
# ============================================
@produtos_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """
    Visualiza detalhes completos de um produto.
    
    Rota auxiliar para visualização detalhada do produto.
    Não faz parte do CRUD básico, mas é útil para consulta.
    
    Args:
        id: ID do produto a ser visualizado
    
    Returns:
        Renderiza template produtos/detalhes.html com todos os dados do produto
    """
    # Verifica se há usuário logado (opcional para visualização)
    usuario_logado = auth_service.verificar_sessao()
    
    # Busca produto pelo ID
    produto = produto_repo.buscar_por_id(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.listar'))
    
    # Renderiza template de detalhes
    return render_template('produtos/detalhes.html', produto=produto)

