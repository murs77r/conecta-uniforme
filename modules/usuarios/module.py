"""
============================================
RF01 - MANTER CADASTRO DE USUÁRIO
============================================
Este módulo é responsável por:
- RF01.1: Criar usuário
- RF01.2: Apagar usuário
- RF01.3: Editar Usuário
- RF01.4: Consultar Usuário

Controla o processo de controle de usuários no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import UsuarioRepository, EscolaRepository, FornecedorRepository, ResponsavelRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService, LogService
from core.database import Database
from core.pagination import paginate_query, Pagination
import json
import re

# Blueprint e Serviços
usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')
usuario_repo = UsuarioRepository()
escola_repo = EscolaRepository()
fornecedor_repo = FornecedorRepository()
responsavel_repo = ResponsavelRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(usuario_repo, 'Usuário')
validacao = ValidacaoService()


# ============================================
# RF01.2 - CONSULTAR USUÁRIOS (LISTAGEM)
# ============================================

@usuarios_bp.route('/')
@usuarios_bp.route('/listar')
def listar():
    """Lista todos os usuários cadastrados com paginação"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('home'))
    
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filtros = {
        'tipo': request.args.get('tipo', ''),
        'busca': request.args.get('busca', ''),
        'ativo': request.args.get('ativo', '')
    }
    
    # Base query
    query = "SELECT * FROM usuarios WHERE 1=1"
    params = []
    
    # Aplicar filtros
    if filtros['tipo']:
        query += " AND tipo = %s"
        params.append(filtros['tipo'])
    
    if filtros['busca']:
        query += " AND (nome ILIKE %s OR email ILIKE %s)"
        busca = f"%{filtros['busca']}%"
        params.extend([busca, busca])
    
    if filtros['ativo']:
        query += " AND ativo = %s"
        params.append(filtros['ativo'] == 'true')
    
    # Ordenação
    query += " ORDER BY data_cadastro DESC"
    
    # Paginar
    paginated_query, paginated_params, pagination = paginate_query(
        query, tuple(params), page, per_page
    )
    
    # Executar query
    usuarios = Database.executar(paginated_query, paginated_params, fetchall=True) or []
    
    # Estatísticas
    estatisticas = _calcular_estatisticas_usuarios()
    
    return render_template('usuarios/listar.html', 
                         usuarios=usuarios,
                         pagination=pagination,
                         filtro_tipo=filtros['tipo'],
                         filtro_busca=filtros['busca'],
                         filtro_ativo=filtros['ativo'],
                         estatisticas=estatisticas)


# ============================================
# RF01.1 - CADASTRAR USUÁRIO
# ============================================

@usuarios_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Cadastra um novo usuário no sistema"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem cadastrar usuários.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('usuarios/cadastrar.html')
    
    # POST - coleta dados
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip(),
        'tipo': request.form.get('tipo', '').strip(),
        'ativo': True
    }
    
    # Validações
    if not all([dados['nome'], dados['email'], dados['tipo']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    if not validacao.validar_email(dados['email']):
        flash('Email inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    tipos_validos = ['administrador', 'escola', 'fornecedor', 'responsavel']
    if dados['tipo'] not in tipos_validos:
        flash('Tipo de usuário inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Verifica duplicidade
    if usuario_repo.buscar_por_email_tipo(dados['email'], dados['tipo']):
        flash('Já existe um usuário com este email para o mesmo tipo selecionado.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Insere usuário
    novo_id = crud_service.criar_com_log(dados, usuario_logado['id'])
    if novo_id:
        return redirect(url_for('usuarios.listar'))
    
    return render_template('usuarios/cadastrar.html')


# ============================================
# RF01.2 - CONSULTAR USUÁRIO (DETALHES)
# ============================================

@usuarios_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """Exibe os detalhes de um usuário específico"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica permissões
    if usuario_logado['tipo'] != 'administrador' and usuario_logado['id'] != id:
        flash('Você não tem permissão para visualizar este usuário.', 'danger')
        return redirect(url_for('home'))
    
    usuario = usuario_repo.buscar_por_id(id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Busca informações complementares
    info_complementar = None
    if isinstance(usuario, dict):
        if usuario['tipo'] == 'escola':
            info_complementar = escola_repo.buscar_por_usuario_id(id)
        elif usuario['tipo'] == 'fornecedor':
            info_complementar = fornecedor_repo.buscar_por_usuario_id(id)
        elif usuario['tipo'] == 'responsavel':
            info_complementar = responsavel_repo.buscar_por_usuario_id(id)
    
    return render_template('usuarios/visualizar.html', 
                         usuario=usuario,
                         info_complementar=info_complementar)


# ============================================
# RF01.3 - EDITAR USUÁRIO
# ============================================

@usuarios_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita os dados de um usuário existente"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica permissões
    if usuario_logado['tipo'] != 'administrador' and usuario_logado['id'] != id:
        flash('Você não tem permissão para editar este usuário.', 'danger')
        return redirect(url_for('home'))
    
    usuario = usuario_repo.buscar_por_id(id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    if request.method == 'GET':
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # POST - coleta dados
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip()
    }
    
    # Apenas admin pode alterar tipo e status
    if usuario_logado['tipo'] == 'administrador':
        dados['tipo'] = request.form.get('tipo', usuario['tipo'] if isinstance(usuario, dict) else '')
        dados['ativo'] = request.form.get('ativo') == 'on'
    
    # Validações
    if not all([dados['nome'], dados['email']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    if not validacao.validar_email(dados['email']):
        flash('Email inválido.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # Regra: não permitir inativar o último administrador ativo
    if isinstance(usuario, dict) and usuario['tipo'] == 'administrador' and \
       usuario['ativo'] and not dados.get('ativo', True):
        q = "SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'administrador' AND id != %s AND ativo = TRUE"
        r = Database.executar(q, (id,), fetchone=True)
        if isinstance(r, dict) and int(r['total']) == 0:
            flash('Não é possível inativar: seria o último administrador ativo.', 'warning')
            return render_template('usuarios/editar.html', usuario=usuario)
    
    # Atualiza
    if crud_service.atualizar_com_log(id, dados, dict(usuario) if isinstance(usuario, dict) else {}, usuario_logado['id']):
        if usuario_logado['id'] == id:
            return redirect(url_for('home'))
        return redirect(url_for('usuarios.listar'))
    
    return render_template('usuarios/editar.html', usuario=usuario)


# ============================================
# RF01.4 - EXCLUIR USUÁRIO
# ============================================

@usuarios_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui um usuário do sistema"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem excluir usuários.', 'danger')
        return redirect(url_for('home'))
    
    if usuario_logado['id'] == id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    usuario = usuario_repo.buscar_por_id(id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Validações de integridade
    bloqueios = _verificar_dependencias_usuario(id, usuario)
    
    if bloqueios:
        flash('Não é possível excluir este usuário. Motivos: ' + ' '.join(bloqueios) + 
              ' Você pode inativá-lo ao invés de excluir.', 'warning')
        return redirect(url_for('usuarios.listar'))
    
    crud_service.excluir_com_log(id, dict(usuario) if isinstance(usuario, dict) else {}, usuario_logado['id'])
    return redirect(url_for('usuarios.listar'))


# ============================================
# RF01.5 - VISUALIZAR LOGS DE ALTERAÇÕES
# ============================================

@usuarios_bp.route('/logs/<int:id>')
def logs(id):
    """Exibe o histórico de alterações de um usuário"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem visualizar logs.', 'danger')
        return redirect(url_for('home'))
    
    usuario = Database.executar("SELECT nome, email FROM usuarios WHERE id = %s", (id,), fetchone=True)
    
    query_logs = """
        SELECT l.*, u.nome as usuario_nome
        FROM logs_alteracoes l
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        WHERE l.tabela = 'usuarios' AND l.registro_id = %s
        ORDER BY l.data_alteracao DESC
    """
    logs = Database.executar(query_logs, (id,), fetchall=True)
    logs = _preparar_detalhes_logs(logs or [])
    
    # Template movido para templates/logs/
    return render_template('logs/logs.html', usuario=usuario, logs=logs)


@usuarios_bp.route('/logs-acesso/<int:id>')
def logs_acesso(id):
    """Exibe o histórico de acessos (LOGIN/LOGOFF) de um usuário"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem visualizar logs de acesso.', 'danger')
        return redirect(url_for('home'))
    
    usuario = Database.executar("SELECT id, nome, email FROM usuarios WHERE id = %s", (id,), fetchone=True)
    
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    query_logs = """
        SELECT *
        FROM logs_acesso
        WHERE usuario_id = %s
        ORDER BY data_acesso DESC
        LIMIT 100
    """
    logs = Database.executar(query_logs, (id,), fetchall=True)
    
    # Template movido para templates/logs/
    return render_template('logs/logs_acesso.html', usuario=usuario, logs=logs or [])


@usuarios_bp.route('/logs')
def logs_sistema():
    """Exibe o histórico geral de alterações do sistema"""
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem visualizar logs.', 'danger')
        return redirect(url_for('home'))
    
    filtro_acao = request.args.get('acao')
    filtro_tabela = request.args.get('tabela')
    filtro_usuario_id = request.args.get('usuario_id')
    
    query = """
        SELECT l.*, u.nome as usuario_nome
        FROM logs_alteracoes l
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        WHERE 1=1
    """
    parametros = []
    
    if filtro_acao:
        query += " AND l.acao = %s"
        parametros.append(filtro_acao)
    
    if filtro_tabela:
        query += " AND l.tabela = %s"
        parametros.append(filtro_tabela)
    
    if filtro_usuario_id:
        query += " AND l.usuario_id = %s"
        parametros.append(filtro_usuario_id)
    
    query += " ORDER BY l.data_alteracao DESC LIMIT 200"
    
    logs = Database.executar(query, tuple(parametros) if parametros else None, fetchall=True)
    logs = _preparar_detalhes_logs(logs or [])
    
    # Template movido para templates/logs/
    return render_template('logs/logs.html', usuario=None, logs=logs)


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _verificar_dependencias_usuario(id: int, usuario: dict) -> list:
    """Verifica dependências de um usuário antes de excluir"""
    bloqueios = []
    tipo = usuario.get('tipo') if isinstance(usuario, dict) else None
    
    if tipo == 'administrador':
        q = "SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'administrador' AND id != %s AND ativo = TRUE"
        r = Database.executar(q, (id,), fetchone=True)
        if isinstance(r, dict) and int(r['total']) == 0:
            bloqueios.append('Não é possível excluir: seria o último administrador ativo.')
    
    elif tipo == 'escola':
        escola = escola_repo.buscar_por_usuario_id(id)
        if isinstance(escola, dict):
            escola_id = escola['id']
            checks = [
                ('homologacao_fornecedores', 'escola_id', 'fornecedores homologados'),
                ('produtos', 'escola_id', 'produtos'),
                ('pedidos', 'escola_id', 'pedidos')
            ]
            for tabela, campo, msg in checks:
                q = f"SELECT COUNT(*) AS total FROM {tabela} WHERE {campo} = %s"
                r = Database.executar(q, (escola_id,), fetchone=True)
                if isinstance(r, dict) and int(r['total']) > 0:
                    bloqueios.append(f'Possui {msg} vinculados.')
    
    elif tipo == 'fornecedor':
        forn = fornecedor_repo.buscar_por_usuario_id(id)
        if isinstance(forn, dict):
            forn_id = forn['id']
            checks = [
                ('produtos', 'fornecedor_id', 'produtos')
            ]
            for tabela, campo, msg in checks:
                q = f"SELECT COUNT(*) AS total FROM {tabela} WHERE {campo} = %s"
                r = Database.executar(q, (forn_id,), fetchone=True)
                if isinstance(r, dict) and int(r['total']) > 0:
                    bloqueios.append(f'Possui {msg} vinculados.')
    
    elif tipo == 'responsavel':
        resp = responsavel_repo.buscar_por_usuario_id(id)
        if isinstance(resp, dict):
            resp_id = resp['id']
            q = "SELECT COUNT(*) AS total FROM pedidos WHERE responsavel_id = %s"
            r = Database.executar(q, (resp_id,), fetchone=True)
            if isinstance(r, dict) and int(r['total']) > 0:
                bloqueios.append('Possui pedidos vinculados ao responsável.')
    
    return bloqueios


def _preparar_detalhes_logs(logs):
    """Converte JSON antigos/novos e calcula mudanças campo a campo"""
    if not logs:
        return []
    
    def parse_json(texto):
        if not texto:
            return {}
        try:
            return json.loads(texto)
        except Exception:
            return {}
    
    campos_ignorados = {"data_atualizacao", "data_cadastro", "id"}
    
    def eh_campo_id(chave: str) -> bool:
        if not isinstance(chave, str):
            return False
        return chave == 'id' or chave.endswith('_id')
    
    def sanitizar(texto: str) -> str:
        if not texto:
            return texto
        padroes = [
            r"(?i)\b(id|registro|reg|cod|codigo)\s*[:=#-]?\s*\d+\b",
            r"#[0-9]+\b",
        ]
        resultado = texto
        for p in padroes:
            resultado = re.sub(p, '[oculto]', resultado)
        return resultado
    
    for l in logs:
        antigos = parse_json(l.get('dados_antigos'))
        novos = parse_json(l.get('dados_novos'))
        l['antigos'] = antigos
        l['novos'] = novos
        mudancas = []
        
        l['descricao'] = sanitizar(l.get('descricao'))
        
        acao = l.get('acao')
        if acao == 'UPDATE':
            chaves = set(antigos.keys()) | set(novos.keys())
            for k in sorted(chaves):
                if k in campos_ignorados or eh_campo_id(k):
                    continue
                antes = antigos.get(k)
                depois = novos.get(k)
                if antes != depois:
                    mudancas.append({'campo': k, 'antes': antes, 'depois': depois})
        elif acao == 'INSERT':
            for k in sorted(novos.keys()):
                if k in campos_ignorados or eh_campo_id(k):
                    continue
                mudancas.append({'campo': k, 'antes': None, 'depois': novos.get(k)})
        elif acao == 'DELETE':
            for k in sorted(antigos.keys()):
                if k in campos_ignorados or eh_campo_id(k):
                    continue
                mudancas.append({'campo': k, 'antes': antigos.get(k), 'depois': None})
        
        l['mudancas'] = mudancas
    
    return logs


def _calcular_estatisticas_usuarios():
    """Calcula estatísticas dos usuários"""
    query_totais = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ativo = TRUE) as ativos,
            COUNT(*) FILTER (WHERE ativo = FALSE) as inativos,
            COUNT(*) FILTER (WHERE tipo = 'administrador') as administradores,
            COUNT(*) FILTER (WHERE tipo = 'escola') as escolas,
            COUNT(*) FILTER (WHERE tipo = 'fornecedor') as fornecedores,
            COUNT(*) FILTER (WHERE tipo = 'responsavel') as responsaveis
        FROM usuarios
    """
    
    result = Database.executar(query_totais, fetchone=True)
    
    stats = {
        'total': result['total'] if result else 0,
        'ativos': result['ativos'] if result else 0,
        'inativos': result['inativos'] if result else 0,
        'administradores': result['administradores'] if result else 0,
        'escolas': result['escolas'] if result else 0,
        'fornecedores': result['fornecedores'] if result else 0,
        'responsaveis': result['responsaveis'] if result else 0
    }
    
    return stats
