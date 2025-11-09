"""
============================================
RF04 - GERENCIAR ESCOLAS HOMOLOGADAS (REFATORADO)
============================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import EscolaRepository, UsuarioRepository, GestorEscolarRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService, LogService
from core.database import Database
from core.pagination import paginate_query, Pagination
import json

# Blueprint e Serviços
escolas_bp = Blueprint('escolas', __name__, url_prefix='/escolas')
escola_repo = EscolaRepository()
usuario_repo = UsuarioRepository()
gestor_repo = GestorEscolarRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(escola_repo, 'Escola')
validacao = ValidacaoService()


# ============================================
# RF04.2 - CONSULTAR ESCOLAS (LISTAGEM)
# ============================================

@escolas_bp.route('/')
@escolas_bp.route('/listar')
def listar():
    """Lista todas as escolas cadastradas com paginação"""
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
        SELECT e.*, u.nome, u.email, u.telefone, u.ativo as usuario_ativo
        FROM escolas e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if filtros['busca']:
        query += """ AND (u.nome ILIKE %s OR e.razao_social ILIKE %s OR e.cnpj ILIKE %s)"""
        busca = f"%{filtros['busca']}%"
        params.extend([busca, busca, busca])
    
    if filtros['ativo']:
        query += " AND e.ativo = %s"
        params.append(filtros['ativo'] == 'true')
    
    if filtros['estado']:
        query += " AND e.estado = %s"
        params.append(filtros['estado'])
    
    if filtros['cidade']:
        query += " AND e.cidade ILIKE %s"
        params.append(f"%{filtros['cidade']}%")
    
    # Ordenação
    query += " ORDER BY u.nome"
    
    # Paginar
    paginated_query, paginated_params, pagination = paginate_query(
        query, tuple(params), page, per_page
    )
    
    # Executar query
    escolas = Database.executar(paginated_query, paginated_params, fetchall=True) or []
    
    # Estatísticas
    estatisticas = _calcular_estatisticas_escolas()
    
    # Lista de estados para filtro
    query_estados = "SELECT DISTINCT estado FROM escolas WHERE estado IS NOT NULL ORDER BY estado"
    estados = Database.executar(query_estados, fetchall=True) or []
    
    return render_template('escolas/listar.html', 
                         escolas=escolas,
                         pagination=pagination,
                         filtro_busca=filtros['busca'],
                         filtro_ativo=filtros['ativo'],
                         filtro_estado=filtros['estado'],
                         filtro_cidade=filtros['cidade'],
                         estatisticas=estatisticas,
                         estados=estados)


# ============================================
# RF04.1 - CADASTRAR ESCOLA
# ============================================

@escolas_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Cadastra uma nova escola"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('escolas/cadastrar.html')
    
    # Coleta dados do formulário
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip(),
        'tipo': 'escola',
        'ativo': True
    }
    
    dados_escola = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip(),
        'ativo': True
    }
    
    # Validações
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_escola['cnpj'], dados_escola['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    if not validacao.validar_cnpj(dados_escola['cnpj']):
        flash('CNPJ inválido.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Verifica duplicidade
    if usuario_repo.buscar_por_email_tipo(dados_usuario['email'], 'escola'):
        flash('Email já cadastrado para perfil Escola.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Insere usuário
    usuario_id = usuario_repo.inserir(dados_usuario)
    if not usuario_id:
        flash('Erro ao cadastrar usuário.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Insere escola
    dados_escola['usuario_id'] = usuario_id
    escola_id = crud_service.criar_com_log(dados_escola, usuario_logado['id'])
    
    if not escola_id:
        return render_template('escolas/cadastrar.html')
    
    # Insere gestores escolares
    _processar_gestores(request.form, escola_id)
    
    return redirect(url_for('escolas.listar'))


# ============================================
# RF04.2 - VISUALIZAR ESCOLA
# ============================================

@escolas_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """Exibe detalhes de uma escola"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    escola = escola_repo.buscar_com_usuario(id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Busca fornecedores homologados
    query_fornecedores = """
        SELECT f.id, u.nome, f.razao_social, hf.data_homologacao, hf.ativo
        FROM homologacao_fornecedores hf
        JOIN fornecedores f ON hf.fornecedor_id = f.id
        JOIN usuarios u ON f.usuario_id = u.id
        WHERE hf.escola_id = %s
        ORDER BY u.nome
    """
    fornecedores = Database.executar(query_fornecedores, (id,), fetchall=True) or []
    
    # Busca gestores
    gestores = gestor_repo.listar_por_escola(id)
    
    return render_template('escolas/visualizar.html', 
                         escola=escola,
                         fornecedores=fornecedores,
                         gestores=gestores)


# ============================================
# RF04.x - HOMOLOGAR FORNECEDOR PARA ESCOLA
# ============================================

@escolas_bp.route('/homologar/<int:escola_id>', methods=['GET', 'POST'])
def homologar_fornecedor(escola_id):
    """Permite ao administrador homologar (vincular) um fornecedor a uma escola"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    escola = Database.executar(
        "SELECT e.id, e.razao_social, u.nome FROM escolas e JOIN usuarios u ON e.usuario_id = u.id WHERE e.id = %s",
        (escola_id,), fetchone=True
    )
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    if request.method == 'GET':
        fornecedores = Database.executar(
            """SELECT f.id, u.nome, f.razao_social FROM fornecedores f 
               JOIN usuarios u ON f.usuario_id = u.id WHERE u.ativo = TRUE ORDER BY u.nome""",
            fetchall=True
        ) or []
        return render_template('escolas/homologar.html', escola=escola, fornecedores=fornecedores)
    
    # POST
    fornecedor_id = request.form.get('fornecedor_id')
    observacoes = request.form.get('observacoes', '').strip() or None
    
    if not fornecedor_id:
        flash('Selecione um fornecedor.', 'warning')
        return redirect(url_for('escolas.homologar_fornecedor', escola_id=escola_id))
    
    # Evita duplicidade
    existe = Database.executar(
        "SELECT id FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s",
        (escola_id, fornecedor_id), fetchone=True
    )
    if existe and isinstance(existe, dict):
        Database.executar(
            "UPDATE homologacao_fornecedores SET ativo = TRUE WHERE id = %s",
            (existe['id'],), commit=True
        )
        LogService.registrar(usuario_logado['id'], 'homologacao_fornecedores', existe['id'], 
                           'UPDATE', descricao='Reativação de homologação escola/fornecedor')
        flash('Homologação reativada com sucesso.', 'success')
        return redirect(url_for('escolas.visualizar', id=escola_id))
    
    # Insere nova homologação
    result = Database.executar(
        """INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, ativo, observacoes)
           VALUES (%s, %s, TRUE, %s) RETURNING id""",
        (escola_id, fornecedor_id, observacoes), fetchone=True
    )
    if result and isinstance(result, dict):
        LogService.registrar(usuario_logado['id'], 'homologacao_fornecedores', result['id'], 'INSERT',
                           dados_novos={'escola_id': escola_id, 'fornecedor_id': fornecedor_id},
                           descricao='Homologação escola/fornecedor criada')
        flash('Fornecedor homologado com sucesso!', 'success')
    
    return redirect(url_for('escolas.visualizar', id=escola_id))


@escolas_bp.route('/homologacao/<int:escola_id>/<int:fornecedor_id>/status', methods=['POST'])
def alterar_status_homologacao(escola_id, fornecedor_id):
    """Ativa/Inativa uma homologação existente (toggle)"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    registro = Database.executar(
        "SELECT id, ativo FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s",
        (escola_id, fornecedor_id), fetchone=True
    )
    if not registro or not isinstance(registro, dict):
        flash('Homologação não encontrada.', 'danger')
        return redirect(url_for('escolas.visualizar', id=escola_id))
    
    novo_status = not bool(registro['ativo'])
    Database.executar(
        "UPDATE homologacao_fornecedores SET ativo = %s WHERE id = %s",
        (novo_status, registro['id']), commit=True
    )
    LogService.registrar(usuario_logado['id'], 'homologacao_fornecedores', registro['id'], 'UPDATE',
                       descricao=('Ativação' if novo_status else 'Inativação') + ' de homologação escola/fornecedor')
    flash('Status da homologação atualizado.', 'success')
    return redirect(url_for('escolas.visualizar', id=escola_id))


# ============================================
# RF04.3 - EDITAR ESCOLA
# ============================================

@escolas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita uma escola existente"""
    usuario_logado = auth_service.verificar_permissao(['administrador', 'escola'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    escola = escola_repo.buscar_com_usuario(id)
    if not escola or not isinstance(escola, dict):
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica permissão
    if usuario_logado['tipo'] == 'escola' and escola['usuario_id'] != usuario_logado['id']:
        flash('Você só pode editar suas próprias informações.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        gestores = gestor_repo.listar_por_escola(id)
        return render_template('escolas/editar.html', escola=escola, gestores=gestores)
    
    # POST - coleta dados
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip()
    }
    
    dados_escola = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip()
    }
    
    # Validações
    if dados_usuario['telefone'] and not validacao.validar_telefone(dados_usuario['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    if dados_escola['cep'] and not validacao.validar_cep(dados_escola['cep']):
        flash('CEP inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Apenas admin pode alterar status
    if usuario_logado['tipo'] == 'administrador':
        dados_usuario['ativo'] = request.form.get('ativo') == 'on'
        dados_escola['ativo'] = request.form.get('ativo') == 'on'
    
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_escola['cnpj'], dados_escola['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Atualiza usuário e escola
    usuario_repo.atualizar(escola['usuario_id'], dados_usuario)
    crud_service.atualizar_com_log(id, dados_escola, dict(escola), usuario_logado['id'])
    
    # Atualiza gestores
    gestor_repo.excluir_por_escola(id)
    _processar_gestores(request.form, id)
    
    return redirect(url_for('escolas.listar'))


# ============================================
# RF04.4 - EXCLUIR ESCOLA
# ============================================

@escolas_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui uma escola"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    escola = escola_repo.buscar_por_id(id)
    if not escola or not isinstance(escola, dict):
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica dependências
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'homologacao_fornecedores', 'campo': 'escola_id', 'mensagem': 'fornecedores homologados'},
        {'tabela': 'produtos', 'campo': 'escola_id', 'mensagem': 'produtos'},
        {'tabela': 'pedidos', 'campo': 'escola_id', 'mensagem': 'pedidos'}
    ])
    
    if bloqueios:
        flash('Não é possível excluir esta escola. ' + ' '.join(bloqueios) + 
              ' Você pode inativá-la ao invés de excluir.', 'warning')
        return redirect(url_for('escolas.listar'))
    
    crud_service.excluir_com_log(id, dict(escola), usuario_logado['id'])
    return redirect(url_for('escolas.listar'))


# ============================================
# RF04.5 - CADASTRAR GESTOR ESCOLAR
# ============================================

@escolas_bp.route('/escola/<int:escola_id>/gestores/cadastrar', methods=['GET', 'POST'])
def cadastrar_gestor(escola_id):
    """Cadastra um novo gestor escolar"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    escola = escola_repo.buscar_com_usuario(escola_id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica permissão
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('gestores/cadastrar.html', escola=escola)
    
    # POST - coleta dados
    dados = {
        'escola_id': escola_id,
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower() or None,
        'telefone': request.form.get('telefone', '').strip() or None,
        'cpf': request.form.get('cpf', '').strip() or None,
        'tipo_gestor': request.form.get('tipo_gestor', '').strip() or None
    }
    
    if not dados['nome']:
        flash('Informe o nome do gestor.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    if dados['cpf'] and not validacao.validar_cpf(dados['cpf']):
        flash('CPF inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    gestor_id = gestor_repo.inserir(dados)
    if gestor_id:
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', gestor_id, 'INSERT',
                           dados_novos=dados, descricao='Cadastro de gestor escolar')
        flash('Gestor cadastrado com sucesso!', 'success')
    
    return redirect(url_for('escolas.listar_gestores', escola_id=escola_id))


# ============================================
# RF04.6 - CONSULTAR GESTORES ESCOLARES
# ============================================

@escolas_bp.route('/escola/<int:escola_id>/gestores')
def listar_gestores(escola_id):
    """Lista todos os gestores de uma escola"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    escola = escola_repo.buscar_com_usuario(escola_id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica permissão
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    gestores = gestor_repo.listar_por_escola(escola_id)
    
    return render_template('gestores/listar.html', escola=escola, gestores=gestores)


# ============================================
# RF04.7 - EDITAR GESTOR ESCOLAR
# ============================================

@escolas_bp.route('/gestores/editar/<int:id>', methods=['GET', 'POST'])
def editar_gestor(id):
    """Edita um gestor escolar existente"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    gestor = Database.executar(
        """SELECT g.*, e.usuario_id, u.nome as escola_nome, e.id as escola_id
           FROM gestores_escolares g
           JOIN escolas e ON g.escola_id = e.id
           JOIN usuarios u ON e.usuario_id = u.id
           WHERE g.id = %s""",
        (id,), fetchone=True
    )
    
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica permissão
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or gestor['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('gestores/editar.html', gestor=gestor)
    
    # POST - atualiza
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower() or None,
        'telefone': request.form.get('telefone', '').strip() or None,
        'cpf': request.form.get('cpf', '').strip() or None,
        'tipo_gestor': request.form.get('tipo_gestor', '').strip() or None
    }
    
    if not dados['nome']:
        flash('Informe o nome do gestor.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)
    
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)
    
    if dados['cpf'] and not validacao.validar_cpf(dados['cpf']):
        flash('CPF inválido.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)
    
    if gestor_repo.atualizar(id, dados):
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', id, 'UPDATE',
                           dados_antigos=dict(gestor), dados_novos=dados,
                           descricao='Atualização de gestor escolar')
        flash('Gestor atualizado com sucesso!', 'success')
    
    return redirect(url_for('escolas.listar_gestores', escola_id=gestor['escola_id']))


# ============================================
# RF04.8 - EXCLUIR GESTOR ESCOLAR
# ============================================

@escolas_bp.route('/gestores/excluir/<int:id>', methods=['POST'])
def excluir_gestor(id):
    """Exclui um gestor escolar"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    gestor = Database.executar(
        """SELECT g.id, g.escola_id, e.usuario_id FROM gestores_escolares g 
           JOIN escolas e ON g.escola_id = e.id WHERE g.id = %s""",
        (id,), fetchone=True
    )
    
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica permissão
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or gestor['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if gestor_repo.excluir(id):
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', id, 'DELETE',
                           dados_antigos=dict(gestor), descricao='Exclusão de gestor escolar')
        flash('Gestor excluído com sucesso!', 'success')
    
    return redirect(url_for('escolas.listar_gestores', escola_id=gestor['escola_id']))


# ============================================
# ATALHO - GESTORES DA PRÓPRIA ESCOLA
# ============================================

@escolas_bp.route('/meus-gestores')
def meus_gestores():
    """Redireciona a escola para a listagem de seus próprios gestores"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    if usuario_logado['tipo'] != 'escola':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    escola = escola_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('home'))
    
    return redirect(url_for('escolas.listar_gestores', escola_id=escola['id']))


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _processar_gestores(form_data, escola_id):
    """Processa e insere gestores escolares do formulário"""
    indices = set()
    for k in form_data.keys():
        if k.startswith('gestores['):
            try:
                idx = k.split('[', 1)[1].split(']', 1)[0]
                indices.add(idx)
            except Exception:
                pass
    
    for idx in indices:
        nome = form_data.get(f'gestores[{idx}][nome]', '').strip()
        if not nome:
            continue
        
        dados = {
            'escola_id': escola_id,
            'nome': nome,
            'email': form_data.get(f'gestores[{idx}][email]', '').strip().lower() or None,
            'telefone': form_data.get(f'gestores[{idx}][telefone]', '').strip() or None,
            'cpf': form_data.get(f'gestores[{idx}][cpf]', '').strip() or None,
            'tipo_gestor': form_data.get(f'gestores[{idx}][tipo_gestor]', '').strip() or None
        }
        
        gestor_repo.inserir(dados)


def _calcular_estatisticas_escolas():
    """Calcula estatísticas das escolas"""
    query_totais = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ativo = TRUE) as ativos,
            COUNT(*) FILTER (WHERE ativo = FALSE) as inativos
        FROM escolas
    """
    
    result = Database.executar(query_totais, fetchone=True)
    
    query_por_estado = """
        SELECT estado, COUNT(*) as total
        FROM escolas
        WHERE estado IS NOT NULL
        GROUP BY estado
        ORDER BY total DESC
        LIMIT 5
    """
    
    por_estado = Database.executar(query_por_estado, fetchall=True) or []
    
    stats = {
        'total': result['total'] if result else 0,
        'ativos': result['ativos'] if result else 0,
        'inativos': result['inativos'] if result else 0,
        'por_estado': por_estado
    }
    
    return stats
