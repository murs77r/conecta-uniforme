"""
============================================
RF01 - MANTER CADASTRO DE USUÁRIO
============================================
Este módulo é responsável por:
- RF01.1: Cadastrar Usuário
- RF01.2: Consultar Usuário
- RF01.3: Editar Usuário
- RF01.4: Excluir Usuário
- RF01.5: Manter Log de Alterações

Gerencia todos os usuários do sistema (administrador, escola, fornecedor, responsável)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import executar_query, validar_email, validar_cpf, validar_cnpj, registrar_log, validar_telefone
from modules.autenticacao import verificar_sessao, verificar_permissao
import json
import re

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================
usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


# ============================================
# RF01.2 - CONSULTAR USUÁRIOS (LISTAGEM)
# ============================================

@usuarios_bp.route('/')
@usuarios_bp.route('/listar')
def listar():
    """
    Lista todos os usuários cadastrados
    Apenas administradores podem acessar
    """
    
    # Verifica se o usuário está autenticado e é administrador
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('home'))
    
    # Pega filtros da URL (se houver)
    filtro_tipo = request.args.get('tipo', '')
    filtro_busca = request.args.get('busca', '')
    
    # Monta a query base
    query = """
        SELECT id, nome, email, telefone, tipo, ativo, data_cadastro
        FROM usuarios
        WHERE 1=1
    """
    parametros = []
    
    # Aplica filtro de tipo se selecionado
    if filtro_tipo:
        query += " AND tipo = %s"
        parametros.append(filtro_tipo)
    
    # Aplica filtro de busca (nome ou email)
    if filtro_busca:
        query += " AND (nome ILIKE %s OR email ILIKE %s)"
        busca_param = f"%{filtro_busca}%"
        parametros.extend([busca_param, busca_param])
    
    # Ordena por data de cadastro (mais recente primeiro)
    query += " ORDER BY data_cadastro DESC"
    
    # Executa a query
    usuarios = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    # Se não encontrou usuários
    if not usuarios:
        usuarios = []
    
    # Renderiza a página
    return render_template('usuarios/listar.html', 
                         usuarios=usuarios, 
                         filtro_tipo=filtro_tipo,
                         filtro_busca=filtro_busca)


# ============================================
# RF01.1 - CADASTRAR USUÁRIO
# ============================================

@usuarios_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    Cadastra um novo usuário no sistema
    Apenas administradores podem cadastrar
    """
    
    # Verifica se o usuário está autenticado e é administrador
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem cadastrar usuários.', 'danger')
        return redirect(url_for('home'))
    
    # Se for GET, apenas mostra o formulário
    if request.method == 'GET':
        return render_template('usuarios/cadastrar.html')
    
    # Se for POST, processa o formulário
    # Pega os dados do formulário
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    tipo = request.form.get('tipo', '').strip()
    
    # Validações básicas
    if not nome or not email or not tipo:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    if telefone and not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Valida o email
    if not validar_email(email):
        flash('Email inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Valida o tipo de usuário
    tipos_validos = ['administrador', 'escola', 'fornecedor', 'responsavel']
    if tipo not in tipos_validos:
        flash('Tipo de usuário inválido.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Verifica se já existe usuário com mesmo email+tipo
    query_verificar = "SELECT id FROM usuarios WHERE email = %s AND tipo = %s"
    usuario_existente = executar_query(query_verificar, (email, tipo), fetchone=True)
    
    if usuario_existente:
        flash('Já existe um usuário com este email para o mesmo tipo selecionado.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    # Insere o novo usuário
    query_inserir = """
        INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
        VALUES (%s, %s, %s, %s, TRUE)
        RETURNING id
    """
    
    # Executa a query e pega o ID gerado
    resultado = executar_query(query_inserir, (nome, email, telefone, tipo), fetchone=True)
    
    if not resultado:
        flash('Erro ao cadastrar usuário.', 'danger')
        return render_template('usuarios/cadastrar.html')
    
    novo_id = resultado['id']
    
    # Registra o log da operação (RF01.5)
    dados_novos = json.dumps({
        'nome': nome,
        'email': email,
        'telefone': telefone,
        'tipo': tipo
    })
    registrar_log(usuario_logado['id'], 'usuarios', novo_id, 'INSERT', 
                  dados_novos=dados_novos, descricao='Cadastro de novo usuário')
    
    # Sucesso!
    flash('Usuário cadastrado com sucesso!', 'success')
    return redirect(url_for('usuarios.listar'))


# ============================================
# RF01.2 - CONSULTAR USUÁRIO (DETALHES)
# ============================================

@usuarios_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """
    Exibe os detalhes de um usuário específico
    """
    
    # Verifica se o usuário está autenticado
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica permissões: administrador pode ver todos, outros só podem ver a si mesmos
    if usuario_logado['tipo'] != 'administrador' and usuario_logado['id'] != id:
        flash('Você não tem permissão para visualizar este usuário.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o usuário no banco
    query = """
        SELECT id, nome, email, telefone, tipo, ativo, data_cadastro, data_atualizacao
        FROM usuarios
        WHERE id = %s
    """
    usuario = executar_query(query, (id,), fetchone=True)
    
    # Verifica se o usuário existe
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Busca informações complementares dependendo do tipo
    info_complementar = None
    
    if usuario['tipo'] == 'escola':
        query_escola = "SELECT * FROM escolas WHERE usuario_id = %s"
        info_complementar = executar_query(query_escola, (id,), fetchone=True)
    
    elif usuario['tipo'] == 'fornecedor':
        query_fornecedor = "SELECT * FROM fornecedores WHERE usuario_id = %s"
        info_complementar = executar_query(query_fornecedor, (id,), fetchone=True)
    
    elif usuario['tipo'] == 'responsavel':
        query_responsavel = "SELECT * FROM responsaveis WHERE usuario_id = %s"
        info_complementar = executar_query(query_responsavel, (id,), fetchone=True)
    
    # Renderiza a página
    return render_template('usuarios/visualizar.html', 
                         usuario=usuario,
                         info_complementar=info_complementar)


# ============================================
# RF01.3 - EDITAR USUÁRIO
# ============================================

@usuarios_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita os dados de um usuário existente
    """
    
    # Verifica se o usuário está autenticado
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Verifica permissões: administrador pode editar todos, outros só podem editar a si mesmos
    if usuario_logado['tipo'] != 'administrador' and usuario_logado['id'] != id:
        flash('Você não tem permissão para editar este usuário.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o usuário atual no banco
    query_buscar = "SELECT * FROM usuarios WHERE id = %s"
    usuario = executar_query(query_buscar, (id,), fetchone=True)
    
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Se for GET, mostra o formulário preenchido
    if request.method == 'GET':
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # Se for POST, processa o formulário
    # Pega os dados do formulário
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    
    # Apenas administrador pode alterar o tipo e status
    if usuario_logado['tipo'] == 'administrador':
        tipo = request.form.get('tipo', usuario['tipo'])
        ativo = request.form.get('ativo') == 'on'
    else:
        tipo = usuario['tipo']
        ativo = usuario['ativo']
    
    # Validações básicas
    if not nome or not email:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)

    if telefone and not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # Valida o email
    if not validar_email(email):
        flash('Email inválido.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # Verifica se já existe outro usuário com o mesmo email+tipo
    query_verificar = "SELECT id FROM usuarios WHERE email = %s AND tipo = %s AND id != %s"
    email_existente = executar_query(query_verificar, (email, tipo, id), fetchone=True)
    
    if email_existente:
        flash('Já existe outro usuário com este email para o mesmo tipo.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)

    # Regra: não permitir inativar o último administrador ativo
    if usuario['tipo'] == 'administrador' and usuario['ativo'] and not ativo:
        q = "SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'administrador' AND id != %s AND ativo = TRUE"
        r = executar_query(q, (id,), fetchone=True)
        if not r or int(r['total']) == 0:
            flash('Não é possível inativar: seria o último administrador ativo.', 'warning')
            return render_template('usuarios/editar.html', usuario=usuario)
    
    # Salva os dados antigos para o log (RF01.5) convertendo tipos não-serializáveis
    dados_antigos = json.dumps(dict(usuario), default=str)
    
    # Atualiza o usuário
    query_atualizar = """
        UPDATE usuarios 
        SET nome = %s, email = %s, telefone = %s, tipo = %s, ativo = %s, data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    
    resultado = executar_query(query_atualizar, (nome, email, telefone, tipo, ativo, id), commit=True)
    
    if not resultado or resultado == 0:
        flash('Erro ao atualizar usuário.', 'danger')
        return render_template('usuarios/editar.html', usuario=usuario)
    
    # Registra o log da operação (RF01.5)
    dados_novos = json.dumps({
        'nome': nome,
        'email': email,
        'telefone': telefone,
        'tipo': tipo,
        'ativo': ativo
    })
    registrar_log(usuario_logado['id'], 'usuarios', id, 'UPDATE',
                  dados_antigos=dados_antigos, dados_novos=dados_novos, 
                  descricao='Atualização de usuário')
    
    # Sucesso!
    flash('Usuário atualizado com sucesso!', 'success')
    
    # Se o usuário editou a si mesmo, redireciona para home
    if usuario_logado['id'] == id:
        return redirect(url_for('home'))
    
    return redirect(url_for('usuarios.listar'))


# ============================================
# RF01.4 - EXCLUIR USUÁRIO
# ============================================

@usuarios_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """
    Exclui um usuário do sistema
    Apenas administradores podem excluir
    """
    
    # Verifica se o usuário está autenticado e é administrador
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem excluir usuários.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica se não está tentando excluir a si mesmo
    if usuario_logado['id'] == id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Busca o usuário antes de excluir (para o log)
    query_buscar = "SELECT * FROM usuarios WHERE id = %s"
    usuario = executar_query(query_buscar, (id,), fetchone=True)
    
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Validações de integridade antes de excluir
    bloqueios = []

    # Verifica tipo do usuário e dependências
    tipo = usuario.get('tipo')
    if tipo == 'administrador':
        # Não permitir excluir o último administrador ativo
        q = "SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'administrador' AND id != %s AND ativo = TRUE"
        r = executar_query(q, (id,), fetchone=True)
        if not r or int(r['total']) == 0:
            bloqueios.append('Não é possível excluir: seria o último administrador ativo.')
    elif tipo == 'escola':
        q_escola = "SELECT id FROM escolas WHERE usuario_id = %s"
        escola = executar_query(q_escola, (id,), fetchone=True)
        if escola:
            escola_id = escola['id']
            # Homologações
            q1 = "SELECT COUNT(*) AS total FROM homologacao_fornecedores WHERE escola_id = %s"
            r1 = executar_query(q1, (escola_id,), fetchone=True)
            if r1 and int(r1['total']) > 0:
                bloqueios.append('Possui fornecedores homologados vinculados.')
            # Produtos da escola
            q2 = "SELECT COUNT(*) AS total FROM produtos WHERE escola_id = %s"
            r2 = executar_query(q2, (escola_id,), fetchone=True)
            if r2 and int(r2['total']) > 0:
                bloqueios.append('Possui produtos vinculados à escola.')
            # Pedidos da escola
            q3 = "SELECT COUNT(*) AS total FROM pedidos WHERE escola_id = %s"
            r3 = executar_query(q3, (escola_id,), fetchone=True)
            if r3 and int(r3['total']) > 0:
                bloqueios.append('Possui pedidos vinculados à escola.')
    elif tipo == 'fornecedor':
        q_forn = "SELECT id FROM fornecedores WHERE usuario_id = %s"
        forn = executar_query(q_forn, (id,), fetchone=True)
        if forn:
            forn_id = forn['id']
            # Produtos do fornecedor
            q1 = "SELECT COUNT(*) AS total FROM produtos WHERE fornecedor_id = %s"
            r1 = executar_query(q1, (forn_id,), fetchone=True)
            if r1 and int(r1['total']) > 0:
                bloqueios.append('Possui produtos vinculados ao fornecedor.')
            # Repasses do fornecedor
            q2 = "SELECT COUNT(*) AS total FROM repasses_financeiros WHERE fornecedor_id = %s"
            r2 = executar_query(q2, (forn_id,), fetchone=True)
            if r2 and int(r2['total']) > 0:
                bloqueios.append('Possui repasses financeiros vinculados.')
    elif tipo == 'responsavel':
        q_resp = "SELECT id FROM responsaveis WHERE usuario_id = %s"
        resp = executar_query(q_resp, (id,), fetchone=True)
        if resp:
            resp_id = resp['id']
            q1 = "SELECT COUNT(*) AS total FROM pedidos WHERE responsavel_id = %s"
            r1 = executar_query(q1, (resp_id,), fetchone=True)
            if r1 and int(r1['total']) > 0:
                bloqueios.append('Possui pedidos vinculados ao responsável.')

    if bloqueios:
        flash('Não é possível excluir este usuário. Motivos: ' + ' '.join(bloqueios) + ' Você pode inativá-lo ao invés de excluir.', 'warning')
        return redirect(url_for('usuarios.listar'))

    # Salva os dados para o log (RF01.5) convertendo tipos não-serializáveis
    dados_antigos = json.dumps(dict(usuario), default=str)

    # Exclui o usuário
    query_excluir = "DELETE FROM usuarios WHERE id = %s"
    resultado = executar_query(query_excluir, (id,), commit=True)
    
    if not resultado or resultado == 0:
        flash('Erro ao excluir usuário.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    # Registra o log da operação (RF01.5)
    registrar_log(usuario_logado['id'], 'usuarios', id, 'DELETE',
                  dados_antigos=dados_antigos, descricao='Exclusão de usuário')
    
    # Sucesso!
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuarios.listar'))


# ============================================
# RF01.5 - VISUALIZAR LOGS DE ALTERAÇÕES
# ============================================

@usuarios_bp.route('/logs/<int:id>')
def logs(id):
    """
    Exibe o histórico de alterações de um usuário
    Apenas administradores podem visualizar
    """
    
    # Verifica se o usuário está autenticado e é administrador
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem visualizar logs.', 'danger')
        return redirect(url_for('home'))
    
    # Busca o usuário
    query_usuario = "SELECT nome, email FROM usuarios WHERE id = %s"
    usuario = executar_query(query_usuario, (id,), fetchone=True)
    
    # Busca os logs relacionados ao usuário
    query_logs = """
        SELECT l.*, u.nome as usuario_nome
        FROM logs_alteracoes l
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        WHERE l.tabela = 'usuarios' AND l.registro_id = %s
        ORDER BY l.data_alteracao DESC
    """
    logs = executar_query(query_logs, (id,), fetchall=True)

    # Prepara difs campo a campo (antes/depois)
    logs = _preparar_detalhes_logs(logs)

    # Renderiza a página
    return render_template('usuarios/logs.html', 
                         usuario=usuario,
                         logs=logs)


# ============================================
# LOGS DO SISTEMA (GERAL)
# ============================================

@usuarios_bp.route('/logs')
def logs_sistema():
    """
    Exibe o histórico geral de alterações do sistema
    Apenas administradores podem visualizar
    """

    # Verifica se o usuário está autenticado e é administrador
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado. Apenas administradores podem visualizar logs.', 'danger')
        return redirect(url_for('home'))

    # Filtros opcionais via query string
    filtro_acao = request.args.get('acao')  # INSERT, UPDATE, DELETE
    filtro_tabela = request.args.get('tabela')  # nome da tabela
    filtro_usuario_id = request.args.get('usuario_id')  # quem realizou

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

    logs = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    logs = _preparar_detalhes_logs(logs)

    # Renderiza usando o mesmo template; sem 'usuario' significa visão geral
    return render_template('usuarios/logs.html', usuario=None, logs=logs)


def _preparar_detalhes_logs(logs):
    """Converte JSON antigos/novos e calcula mudanças campo a campo."""
    if not logs:
        return []

    def parse_json(texto):
        if not texto:
            return {}
        try:
            return json.loads(texto)
        except Exception:
            return {}

    # Campos que geralmente mudam automaticamente e poluem o diff
    campos_ignorados = {"data_atualizacao", "data_cadastro", "id"}

    def eh_campo_id(chave: str) -> bool:
        if not isinstance(chave, str):
            return False
        if chave == 'id':
            return True
        # Qualquer campo terminado com _id não deve aparecer
        return chave.endswith('_id')

    def sanitizar(texto: str) -> str:
        if not texto:
            return texto
        # Remove/mascara padrões comuns de ID (ex.: "ID 123", "#123", "id=123", "registro: 123")
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

        # Sanitiza descrição para não exibir IDs
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


# ============================================
# FIM DO MÓDULO DE USUÁRIOS
# ============================================
