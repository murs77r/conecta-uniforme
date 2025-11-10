"""
============================================
RF05 - MANTER CADASTRO DE FORNECEDOR
============================================
Este módulo é responsável pelo CRUD básico de fornecedores:
- RF05.1: Listar fornecedores
- RF05.2: Criar fornecedor
- RF05.3: Editar fornecedor
- RF05.4: Apagar fornecedor
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import FornecedorRepository, UsuarioRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService
from core.database import Database

# Blueprint
fornecedores_bp = Blueprint('fornecedores', __name__, url_prefix='/fornecedores')

# Repositories e Services
fornecedor_repo = FornecedorRepository()
usuario_repo = UsuarioRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(fornecedor_repo, 'Fornecedor')
validacao = ValidacaoService()


# ============================================
# RF05.1 - LISTAR FORNECEDORES
# ============================================
@fornecedores_bp.route('/')
@fornecedores_bp.route('/listar')
def listar():
    """
    RF05.1 - Listar fornecedores
    """
    # Verificar autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Query base - JOIN simples com usuários
    query = """
        SELECT f.*, u.nome, u.email, u.telefone
        FROM fornecedores f
        JOIN usuarios u ON f.usuario_id = u.id
        ORDER BY u.nome
    """
    
    # Executar query
    fornecedores = Database.executar(query, fetchall=True) or []
    
    return render_template('fornecedores/listar.html', fornecedores=fornecedores)


# ============================================
# RF05.2 - CRIAR FORNECEDOR
# ============================================
@fornecedores_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    RF05.2 - Criar novo fornecedor
    """
    # Verificar permissão de administrador
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Exibir formulário
    if request.method == 'GET':
        return render_template('fornecedores/cadastrar.html')
    
    # Processar criação (POST)
    # Coletar dados do usuário
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip(),
        'tipo': 'fornecedor',
        'ativo': True
    }
    
    # Coletar dados do fornecedor
    dados_fornecedor = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip(),
        'ativo': True
    }
    
    # Validar campos obrigatórios
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_fornecedor['cnpj'], dados_fornecedor['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Validar CNPJ
    if not validacao.validar_cnpj(dados_fornecedor['cnpj']):
        flash('CNPJ inválido.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Inserir usuário
    usuario_id = usuario_repo.inserir(dados_usuario)
    if not usuario_id:
        flash('Erro ao cadastrar usuário.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Inserir fornecedor
    dados_fornecedor['usuario_id'] = usuario_id
    fornecedor_id = crud_service.criar_com_log(dados_fornecedor, usuario_logado['id'])
    
    if fornecedor_id:
        flash('Fornecedor cadastrado com sucesso!', 'success')
        return redirect(url_for('fornecedores.listar'))
    
    flash('Erro ao cadastrar fornecedor.', 'danger')
    return render_template('fornecedores/cadastrar.html')


# ============================================
# RF05.3 - EDITAR FORNECEDOR
# ============================================
@fornecedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    RF05.3 - Editar fornecedor existente
    """
    # Verificar permissão (administrador ou próprio fornecedor)
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Buscar fornecedor
    fornecedor = fornecedor_repo.buscar_com_usuario(id)
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    # Exibir formulário
    if request.method == 'GET':
        return render_template('fornecedores/editar.html', fornecedor=fornecedor)
    
    # Processar edição (POST)
    # Coletar dados do usuário
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip()
    }
    
    # Coletar dados do fornecedor
    dados_fornecedor = {
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip()
    }
    
    # Validar campos obrigatórios
    if not all([dados_usuario['nome'], dados_usuario['email'], dados_fornecedor['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('fornecedores/editar.html', fornecedor=fornecedor)
    
    # Atualizar usuário
    usuario_repo.atualizar(fornecedor['usuario_id'], dados_usuario)
    
    # Atualizar fornecedor
    crud_service.atualizar_com_log(id, dados_fornecedor, dict(fornecedor), usuario_logado['id'])
    
    flash('Fornecedor atualizado com sucesso!', 'success')
    return redirect(url_for('fornecedores.listar'))


# ============================================
# VISUALIZAR DETALHES DO FORNECEDOR
# ============================================
@fornecedores_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """
    Visualizar detalhes completos do fornecedor
    """
    # Verificar autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Buscar fornecedor com dados do usuário
    fornecedor = fornecedor_repo.buscar_com_usuario(id)
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    # Contar produtos vinculados (opcional, informação útil)
    query_produtos = """
        SELECT COUNT(*) as total_produtos
        FROM produtos
        WHERE fornecedor_id = %s
    """
    result = Database.executar(query_produtos, (id,), fetchone=True)
    total_produtos = result['total_produtos'] if result else 0
    
    return render_template('fornecedores/detalhes.html', 
                         fornecedor=fornecedor,
                         total_produtos=total_produtos)


# ============================================
# RF05.4 - APAGAR FORNECEDOR
# ============================================
@fornecedores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """
    RF05.4 - Apagar fornecedor
    """
    # Verificar permissão de administrador
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Buscar fornecedor
    fornecedor = fornecedor_repo.buscar_por_id(id)
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    # Verificar dependências (se existem produtos vinculados)
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'produtos', 'campo': 'fornecedor_id', 'mensagem': 'produtos cadastrados'}
    ])
    
    if bloqueios:
        flash(f"Não é possível excluir: existem {bloqueios[0]}", 'warning')
        return redirect(url_for('fornecedores.listar'))
    
    # Excluir fornecedor
    crud_service.excluir_com_log(id, dict(fornecedor), usuario_logado['id'])
    
    flash('Fornecedor excluído com sucesso!', 'success')
    return redirect(url_for('fornecedores.listar'))
