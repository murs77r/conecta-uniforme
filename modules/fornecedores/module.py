"""
============================================
RF05 - GERENCIAR FORNECEDORES (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import FornecedorRepository, UsuarioRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService
from core.pagination import paginate_query, Pagination
from core.database import Database

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
    """Lista fornecedores com paginação"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filtros = {
        'busca': request.args.get('busca', ''),
        'ativo': request.args.get('ativo', ''),
        'estado': request.args.get('estado', ''),
        'cidade': request.args.get('cidade', '')
    }
    
    # Base query
    query = """
        SELECT f.*, u.nome, u.email, u.telefone, u.ativo as usuario_ativo
        FROM fornecedores f
        JOIN usuarios u ON f.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if filtros['busca']:
        query += " AND (u.nome ILIKE %s OR f.razao_social ILIKE %s OR f.cnpj ILIKE %s)"
        busca = f"%{filtros['busca']}%"
        params.extend([busca, busca, busca])
    
    if filtros['ativo']:
        query += " AND f.ativo = %s"
        params.append(filtros['ativo'] == 'true')
    
    if filtros['estado']:
        query += " AND f.estado = %s"
        params.append(filtros['estado'])
    
    if filtros['cidade']:
        query += " AND f.cidade ILIKE %s"
        params.append(f"%{filtros['cidade']}%")
    
    # Ordenação
    query += " ORDER BY u.nome"
    
    # Paginar
    paginated_query, paginated_params, pagination = paginate_query(
        query, tuple(params), page, per_page
    )
    
    # Executar query
    fornecedores = Database.executar(paginated_query, paginated_params, fetchall=True) or []
    
    # Estatísticas
    estatisticas = _calcular_estatisticas_fornecedores()
    
    # Lista de estados para filtro
    query_estados = "SELECT DISTINCT estado FROM fornecedores WHERE estado IS NOT NULL ORDER BY estado"
    estados = Database.executar(query_estados, fetchall=True) or []
    
    return render_template('fornecedores/listar.html', 
                         fornecedores=fornecedores,
                         pagination=pagination,
                         filtro_busca=filtros['busca'],
                         filtro_ativo=filtros['ativo'],
                         filtro_estado=filtros['estado'],
                         filtro_cidade=filtros['cidade'],
                         estatisticas=estatisticas,
                         estados=estados)


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
        {'tabela': 'produtos', 'campo': 'fornecedor_id', 'mensagem': 'produtos'}
    ])
    
    if bloqueios:
        flash(f"Não é possível excluir: {' '.join(bloqueios)}", 'warning')
        return redirect(url_for('fornecedores.listar'))
    
    crud_service.excluir_com_log(id, dict(fornecedor), usuario_logado['id'])
    return redirect(url_for('fornecedores.listar'))


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _calcular_estatisticas_fornecedores():
    """Calcula estatísticas dos fornecedores"""
    query_totais = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ativo = TRUE) as ativos,
            COUNT(*) FILTER (WHERE ativo = FALSE) as inativos
        FROM fornecedores
    """
    
    result = Database.executar(query_totais, fetchone=True)
    
    # Produtos por fornecedor
    query_produtos = """
        SELECT f.id, u.nome, COUNT(p.id) as total_produtos
        FROM fornecedores f
        JOIN usuarios u ON f.usuario_id = u.id
        LEFT JOIN produtos p ON f.id = p.fornecedor_id
        GROUP BY f.id, u.nome
        ORDER BY total_produtos DESC
        LIMIT 5
    """
    
    top_fornecedores = Database.executar(query_produtos, fetchall=True) or []
    
    stats = {
        'total': result['total'] if result else 0,
        'ativos': result['ativos'] if result else 0,
        'inativos': result['inativos'] if result else 0,
        'top_fornecedores': top_fornecedores
    }
    
    return stats
