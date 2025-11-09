"""
============================================
RF05 - GERENCIAR FORNECEDORES (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import FornecedorRepository, UsuarioRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService

# Blueprint
fornecedores_bp = Blueprint('fornecedores', __name__, url_prefix='/fornecedores')

# Repositories e Services
fornecedor_repo = FornecedorRepository()
usuario_repo = UsuarioRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(fornecedor_repo, 'Fornecedor')
validacao = ValidacaoService()


@fornecedores_bp.route('/')
@fornecedores_bp.route('/listar')
def listar():
    """Lista fornecedores"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    filtros = {'busca': request.args.get('busca', '')}
    fornecedores = fornecedor_repo.listar_com_usuario(filtros)
    
    return render_template('fornecedores/listar.html', 
                         fornecedores=fornecedores,
                         filtro_busca=filtros['busca'])


@fornecedores_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Cadastra fornecedor"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('fornecedores/cadastrar.html')
    
    # Coleta dados
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip(),
        'tipo': 'fornecedor',
        'ativo': True
    }
    
    dados_fornecedor = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip(),
        'ativo': True
    }
    
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_fornecedor['cnpj'], dados_fornecedor['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    if not validacao.validar_cnpj(dados_fornecedor['cnpj']):
        flash('CNPJ inválido.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Insere usuário
    usuario_id = usuario_repo.inserir(dados_usuario)
    if not usuario_id:
        flash('Erro ao cadastrar.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Insere fornecedor
    dados_fornecedor['usuario_id'] = usuario_id
    fornecedor_id = crud_service.criar_com_log(dados_fornecedor, usuario_logado['id'])
    
    if fornecedor_id:
        return redirect(url_for('fornecedores.listar'))
    
    return render_template('fornecedores/cadastrar.html')


@fornecedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita fornecedor"""
    usuario_logado = auth_service.verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    fornecedor = fornecedor_repo.buscar_com_usuario(id)
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    if request.method == 'GET':
        return render_template('fornecedores/editar.html', fornecedor=fornecedor)
    
    # Coleta dados
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip()
    }
    
    dados_fornecedor = {
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip()
    }
    
    # Atualiza usuário e fornecedor
    usuario_repo.atualizar(fornecedor['usuario_id'], dados_usuario)
    crud_service.atualizar_com_log(id, dados_fornecedor, dict(fornecedor), usuario_logado['id'])
    
    return redirect(url_for('fornecedores.listar'))


@fornecedores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui fornecedor"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    fornecedor = fornecedor_repo.buscar_por_id(id)
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    # Verifica dependências
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'produtos', 'campo': 'fornecedor_id', 'mensagem': 'produtos'},
        {'tabela': 'repasses_financeiros', 'campo': 'fornecedor_id', 'mensagem': 'repasses'}
    ])
    
    if bloqueios:
        flash(f"Não é possível excluir: {' '.join(bloqueios)}", 'warning')
        return redirect(url_for('fornecedores.listar'))
    
    crud_service.excluir_com_log(id, dict(fornecedor), usuario_logado['id'])
    return redirect(url_for('fornecedores.listar'))
