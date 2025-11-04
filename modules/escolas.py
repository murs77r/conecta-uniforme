"""
============================================
RF04 - GERENCIAR ESCOLAS HOMOLOGADAS
============================================
Este módulo é responsável por:
- RF04.1: Cadastrar Escola Homologada
- RF04.2: Consultar Escola Homologada
- RF04.3: Editar Escola Homologada
- RF04.4: Excluir Escola Homologada

Gerencia as escolas cadastradas no sistema
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import executar_query, validar_cnpj, registrar_log, validar_cep, validar_telefone
from modules.autenticacao import verificar_sessao, verificar_permissao
import json

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================
escolas_bp = Blueprint('escolas', __name__, url_prefix='/escolas')


# ============================================
# RF04.2 - CONSULTAR ESCOLAS (LISTAGEM)
# ============================================

@escolas_bp.route('/')
@escolas_bp.route('/listar')
def listar():
    """
    Lista todas as escolas cadastradas
    """
    
    # Verifica se o usuário está autenticado
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Pega filtros da URL
    filtro_busca = request.args.get('busca', '')
    filtro_ativo = request.args.get('ativo', '')
    
    # Monta a query
    query = """
        SELECT e.*, u.nome, u.email, u.telefone, u.ativo
        FROM escolas e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE 1=1
    """
    parametros = []
    
    # Aplica filtro de busca
    if filtro_busca:
        query += " AND (u.nome ILIKE %s OR e.razao_social ILIKE %s OR e.cnpj ILIKE %s)"
        busca_param = f"%{filtro_busca}%"
        parametros.extend([busca_param, busca_param, busca_param])
    
    # Aplica filtro de status
    if filtro_ativo:
        query += " AND e.ativo = %s"
        parametros.append(filtro_ativo == 'true')
    
    # Ordena por nome
    query += " ORDER BY u.nome"
    
    # Executa a query
    escolas = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    if not escolas:
        escolas = []
    
    return render_template('escolas/listar.html', 
                         escolas=escolas,
                         filtro_busca=filtro_busca,
                         filtro_ativo=filtro_ativo)


# ============================================
# RF04.1 - CADASTRAR ESCOLA
# ============================================

@escolas_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    Cadastra uma nova escola
    Apenas administradores podem cadastrar
    """
    
    # Verifica permissão
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('escolas/cadastrar.html')
    
    # Pega os dados do formulário
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    endereco = request.form.get('endereco', '').strip()
    cidade = request.form.get('cidade', '').strip()
    estado = request.form.get('estado', '').strip()
    cep = request.form.get('cep', '').strip()
    
    # Validações
    if not nome or not email or not cnpj or not razao_social:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Valida CNPJ
    if not validar_cnpj(cnpj):
        flash('CNPJ inválido.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Verifica se email já existe para o tipo escola
    query_email = "SELECT id FROM usuarios WHERE email = %s AND tipo = 'escola'"
    if executar_query(query_email, (email,), fetchone=True):
        flash('Email já cadastrado para perfil Escola.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Verifica se CNPJ já existe
    query_cnpj = "SELECT id FROM escolas WHERE cnpj = %s"
    if executar_query(query_cnpj, (cnpj,), fetchone=True):
        flash('CNPJ já cadastrado.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Insere o usuário
    query_usuario = """
        INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
        VALUES (%s, %s, %s, 'escola', TRUE)
        RETURNING id
    """
    resultado_usuario = executar_query(query_usuario, (nome, email, telefone), fetchone=True)
    
    if not resultado_usuario:
        flash('Erro ao cadastrar usuário.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    usuario_id = resultado_usuario['id']
    
    # Insere a escola
    query_escola = """
        INSERT INTO escolas (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
    """
    resultado_escola = executar_query(query_escola, 
                                      (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep),
                                      fetchone=True)
    
    if not resultado_escola:
        flash('Erro ao cadastrar escola.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    escola_id = resultado_escola['id']

    # Insere gestores escolares (múltiplos)
    try:
        # Descobre índices presentes: gestores[<i>][campo]
        indices = set()
        for k in request.form.keys():
            if k.startswith('gestores['):
                # formato: gestores[IDX][campo]
                try:
                    idx = k.split('[', 1)[1].split(']', 1)[0]
                    indices.add(idx)
                except Exception:
                    pass
        for idx in indices:
            g_nome = request.form.get(f'gestores[{idx}][nome]', '').strip()
            if not g_nome:
                continue
            g_email = request.form.get(f'gestores[{idx}][email]', '').strip().lower() or None
            g_tel = request.form.get(f'gestores[{idx}][telefone]', '').strip() or None
            g_cpf = request.form.get(f'gestores[{idx}][cpf]', '').strip() or None
            g_tipo = request.form.get(f'gestores[{idx}][tipo_gestor]', '').strip() or None
            executar_query(
                """
                INSERT INTO gestores_escolares (escola_id, nome, email, telefone, cpf, tipo_gestor)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (escola_id, g_nome, g_email, g_tel, g_cpf, g_tipo), commit=True
            )
    except Exception as e:
        # não falhar o cadastro por erro nos gestores; apenas alerta
        print('Erro ao inserir gestores_escolares:', e)
    
    # Registra log
    dados_novos = json.dumps({'nome': nome, 'cnpj': cnpj, 'razao_social': razao_social})
    registrar_log(usuario_logado['id'], 'escolas', escola_id, 'INSERT',
                  dados_novos=dados_novos, descricao='Cadastro de escola')
    
    flash('Escola cadastrada com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# RF04.2 - VISUALIZAR ESCOLA
# ============================================

@escolas_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """
    Exibe detalhes de uma escola
    """
    
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca a escola
    query = """
        SELECT e.*, u.nome, u.email, u.telefone, u.ativo, u.data_cadastro
        FROM escolas e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.id = %s
    """
    escola = executar_query(query, (id,), fetchone=True)
    
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
    fornecedores = executar_query(query_fornecedores, (id,), fetchall=True)
    
    if not fornecedores:
        fornecedores = []

    # Busca gestores escolares
    query_gestores = """
        SELECT id, nome, email, telefone, cpf, tipo_gestor, data_cadastro
        FROM gestores_escolares
        WHERE escola_id = %s
        ORDER BY nome
    """
    gestores = executar_query(query_gestores, (id,), fetchall=True) or []
    
    return render_template('escolas/visualizar.html', 
                         escola=escola,
                         fornecedores=fornecedores,
                         gestores=gestores)


# ============================================
# RF04.x - HOMOLOGAR FORNECEDOR PARA ESCOLA (ADMIN)
# ============================================

@escolas_bp.route('/homologar/<int:escola_id>', methods=['GET', 'POST'])
def homologar_fornecedor(escola_id):
    """Permite ao administrador homologar (vincular) um fornecedor a uma escola."""

    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    # Verifica escola
    escola = executar_query(
        """
        SELECT e.id, e.razao_social, u.nome
        FROM escolas e JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.id = %s
        """,
        (escola_id,), fetchone=True
    )
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))

    if request.method == 'GET':
        # Lista fornecedores ativos para seleção
        fornecedores = executar_query(
            """
            SELECT f.id, u.nome, f.razao_social
            FROM fornecedores f JOIN usuarios u ON f.usuario_id = u.id
            WHERE u.ativo = TRUE
            ORDER BY u.nome
            """,
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
    existe = executar_query(
        "SELECT id FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s",
        (escola_id, fornecedor_id), fetchone=True
    )
    if existe:
        # Se já existe mas inativo, reativa
        executar_query(
            "UPDATE homologacao_fornecedores SET ativo = TRUE WHERE id = %s",
            (existe['id'],), commit=True
        )
        registrar_log(usuario_logado['id'], 'homologacao_fornecedores', existe['id'], 'UPDATE', descricao='Reativação de homologação escola/fornecedor')
        flash('Homologação reativada com sucesso.', 'success')
        return redirect(url_for('escolas.visualizar', id=escola_id))

    # Insere nova homologação
    result = executar_query(
        """
        INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, ativo, observacoes)
        VALUES (%s, %s, TRUE, %s)
        RETURNING id
        """,
        (escola_id, fornecedor_id, observacoes), fetchone=True
    )
    if not result:
        flash('Erro ao homologar fornecedor.', 'danger')
        return redirect(url_for('escolas.visualizar', id=escola_id))

    registrar_log(usuario_logado['id'], 'homologacao_fornecedores', result['id'], 'INSERT',
                  dados_novos=json.dumps({'escola_id': escola_id, 'fornecedor_id': fornecedor_id}),
                  descricao='Homologação escola/fornecedor criada')
    flash('Fornecedor homologado com sucesso!', 'success')
    return redirect(url_for('escolas.visualizar', id=escola_id))


@escolas_bp.route('/homologacao/<int:escola_id>/<int:fornecedor_id>/status', methods=['POST'])
def alterar_status_homologacao(escola_id, fornecedor_id):
    """Ativa/Inativa uma homologação existente (toggle)."""
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    registro = executar_query(
        "SELECT id, ativo FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s",
        (escola_id, fornecedor_id), fetchone=True
    )
    if not registro:
        flash('Homologação não encontrada.', 'danger')
        return redirect(url_for('escolas.visualizar', id=escola_id))

    novo_status = not bool(registro['ativo'])
    executar_query(
        "UPDATE homologacao_fornecedores SET ativo = %s WHERE id = %s",
        (novo_status, registro['id']), commit=True
    )
    registrar_log(usuario_logado['id'], 'homologacao_fornecedores', registro['id'], 'UPDATE',
                  descricao=('Ativação' if novo_status else 'Inativação') + ' de homologação escola/fornecedor')
    flash('Status da homologação atualizado.', 'success')
    return redirect(url_for('escolas.visualizar', id=escola_id))


# ============================================
# RF04.3 - EDITAR ESCOLA
# ============================================

@escolas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita uma escola existente
    """
    
    usuario_logado = verificar_permissao(['administrador', 'escola'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca a escola
    query_buscar = """
        SELECT e.*, u.nome, u.email, u.telefone, u.ativo
        FROM escolas e
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.id = %s
    """
    escola = executar_query(query_buscar, (id,), fetchone=True)
    
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica se a escola pode editar (apenas suas próprias informações)
    if usuario_logado['tipo'] == 'escola' and escola['usuario_id'] != usuario_logado['id']:
        flash('Você só pode editar suas próprias informações.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        # Carrega gestores existentes para exibição
        gestores = executar_query(
            """
            SELECT id, nome, email, telefone, cpf, tipo_gestor
            FROM gestores_escolares
            WHERE escola_id = %s
            ORDER BY nome
            """,
            (id,), fetchall=True
        ) or []
        return render_template('escolas/editar.html', escola=escola, gestores=gestores)
    
    # Pega os dados do formulário
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    endereco = request.form.get('endereco', '').strip()
    cidade = request.form.get('cidade', '').strip()
    estado = request.form.get('estado', '').strip()
    cep = request.form.get('cep', '').strip()

    if telefone and not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    if cep and not validar_cep(cep):
        flash('CEP inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Apenas admin pode alterar status
    if usuario_logado['tipo'] == 'administrador':
        ativo = request.form.get('ativo') == 'on'
    else:
        ativo = escola['ativo']
    
    # Validações
    if not nome or not email or not cnpj or not razao_social:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Salva dados antigos para log (convertendo tipos não-serializáveis como datetime)
    dados_antigos = json.dumps(dict(escola), default=str)
    
    # Atualiza o usuário
    query_usuario = """
        UPDATE usuarios 
        SET nome = %s, email = %s, telefone = %s, ativo = %s, data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    executar_query(query_usuario, (nome, email, telefone, ativo, escola['usuario_id']), commit=True)
    
    # Atualiza a escola
    query_escola = """
        UPDATE escolas 
        SET cnpj = %s, razao_social = %s, endereco = %s, cidade = %s, estado = %s, cep = %s, ativo = %s
        WHERE id = %s
    """
    resultado = executar_query(query_escola, 
                               (cnpj, razao_social, endereco, cidade, estado, cep, ativo, id),
                               commit=True)
    
    if not resultado or resultado == 0:
        flash('Erro ao atualizar escola.', 'danger')
        return render_template('escolas/editar.html', escola=escola)

    # Substitui gestores: apaga e reinsere conforme formulário
    try:
        executar_query("DELETE FROM gestores_escolares WHERE escola_id = %s", (id,), commit=True)
        indices = set()
        for k in request.form.keys():
            if k.startswith('gestores['):
                try:
                    idx = k.split('[', 1)[1].split(']', 1)[0]
                    indices.add(idx)
                except Exception:
                    pass
        for idx in indices:
            g_nome = request.form.get(f'gestores[{idx}][nome]', '').strip()
            if not g_nome:
                continue
            g_email = request.form.get(f'gestores[{idx}][email]', '').strip().lower() or None
            g_tel = request.form.get(f'gestores[{idx}][telefone]', '').strip() or None
            g_cpf = request.form.get(f'gestores[{idx}][cpf]', '').strip() or None
            g_tipo = request.form.get(f'gestores[{idx}][tipo_gestor]', '').strip() or None
            # Validações básicas dos gestores
            if g_tel and not validar_telefone(g_tel):
                flash('Telefone de gestor inválido.', 'danger')
                return render_template('escolas/editar.html', escola=escola)
            if g_cpf and not validar_cpf(g_cpf):
                flash('CPF de gestor inválido.', 'danger')
                return render_template('escolas/editar.html', escola=escola)
            executar_query(
                """
                INSERT INTO gestores_escolares (escola_id, nome, email, telefone, cpf, tipo_gestor)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id, g_nome, g_email, g_tel, g_cpf, g_tipo), commit=True
            )
    except Exception as e:
        print('Erro ao atualizar gestores_escolares:', e)
    
    # Registra log
    dados_novos = json.dumps({'nome': nome, 'cnpj': cnpj, 'razao_social': razao_social})
    registrar_log(usuario_logado['id'], 'escolas', id, 'UPDATE',
                  dados_antigos=dados_antigos, dados_novos=dados_novos,
                  descricao='Atualização de escola')
    
    flash('Escola atualizada com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# RF04.4 - EXCLUIR ESCOLA
# ============================================

@escolas_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """
    Exclui uma escola
    Apenas administradores podem excluir
    """
    
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca a escola
    query_buscar = "SELECT * FROM escolas WHERE id = %s"
    escola = executar_query(query_buscar, (id,), fetchone=True)
    
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Validações: impedir exclusão se houver vínculos relevantes
    bloqueios = []
    q1 = "SELECT COUNT(*) AS total FROM homologacao_fornecedores WHERE escola_id = %s"
    r1 = executar_query(q1, (id,), fetchone=True)
    if r1 and int(r1['total']) > 0:
        bloqueios.append('Possui fornecedores homologados vinculados.')

    q2 = "SELECT COUNT(*) AS total FROM produtos WHERE escola_id = %s"
    r2 = executar_query(q2, (id,), fetchone=True)
    if r2 and int(r2['total']) > 0:
        bloqueios.append('Possui produtos vinculados à escola.')

    q3 = "SELECT COUNT(*) AS total FROM pedidos WHERE escola_id = %s"
    r3 = executar_query(q3, (id,), fetchone=True)
    if r3 and int(r3['total']) > 0:
        bloqueios.append('Possui pedidos vinculados à escola.')

    if bloqueios:
        flash('Não é possível excluir esta escola. Motivos: ' + ' '.join(bloqueios) + ' Você pode inativá-la ao invés de excluir.', 'warning')
        return redirect(url_for('escolas.listar'))

    # Salva dados para log (convertendo tipos não-serializáveis como datetime)
    dados_antigos = json.dumps(dict(escola), default=str)

    # Exclui a escola
    query_excluir = "DELETE FROM escolas WHERE id = %s"
    resultado = executar_query(query_excluir, (id,), commit=True)
    
    if not resultado or resultado == 0:
        flash('Erro ao excluir escola.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Registra log
    registrar_log(usuario_logado['id'], 'escolas', id, 'DELETE',
                  dados_antigos=dados_antigos, descricao='Exclusão de escola')
    
    flash('Escola excluída com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# FIM DO MÓDULO DE ESCOLAS
# ============================================