"""
============================================
RF05 - GERENCIAR FORNECEDORES HOMOLOGADOS
============================================
Este módulo é responsável por:
- RF05.1: Cadastrar Fornecedor Homologado
- RF05.2: Consultar Fornecedor Homologado
- RF05.3: Editar Fornecedor Homologado
- RF05.4: Excluir Fornecedor Homologado

Gerencia os fornecedores homologados cadastrados no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import executar_query, validar_cnpj, registrar_log, validar_cep, validar_telefone
from modules.autenticacao import verificar_sessao, verificar_permissao
import json

# Blueprint
fornecedores_bp = Blueprint('fornecedores', __name__, url_prefix='/fornecedores')

# RF05.2 - Listar
@fornecedores_bp.route('/')
@fornecedores_bp.route('/listar')
def listar():
    usuario_logado = verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    filtro_busca = request.args.get('busca', '')
    
    query = """
        SELECT f.*, u.nome, u.email, u.telefone, u.ativo
        FROM fornecedores f
        JOIN usuarios u ON f.usuario_id = u.id
        WHERE 1=1
    """
    parametros = []
    
    if filtro_busca:
        query += " AND (u.nome ILIKE %s OR f.razao_social ILIKE %s)"
        busca_param = f"%{filtro_busca}%"
        parametros.extend([busca_param, busca_param])
    
    query += " ORDER BY u.nome"
    
    fornecedores = executar_query(query, tuple(parametros) if parametros else None, fetchall=True)
    
    if not fornecedores:
        fornecedores = []
    
    return render_template('fornecedores/listar.html', 
                         fornecedores=fornecedores,
                         filtro_busca=filtro_busca)

# RF05.1 - Cadastrar
@fornecedores_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('fornecedores/cadastrar.html')
    
    # Pega dados do formulário
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    endereco = request.form.get('endereco', '').strip()
    cidade = request.form.get('cidade', '').strip()
    estado = request.form.get('estado', '').strip()
    cep = request.form.get('cep', '').strip()
    
    if not nome or not email or not cnpj or not razao_social:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    # Insere usuário
    query_usuario = """
        INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
        VALUES (%s, %s, %s, 'fornecedor', TRUE)
        RETURNING id
    """
    resultado_usuario = executar_query(query_usuario, (nome, email, telefone), fetchone=True)
    
    if not resultado_usuario:
        flash('Erro ao cadastrar.', 'danger')
        return render_template('fornecedores/cadastrar.html')
    
    usuario_id = resultado_usuario['id']
    
    # Insere fornecedor
    query_fornecedor = """
        INSERT INTO fornecedores (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
    """
    resultado = executar_query(query_fornecedor, 
                              (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep),
                              fetchone=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'fornecedores', resultado['id'], 'INSERT',
                      dados_novos=json.dumps({'nome': nome, 'cnpj': cnpj}))
        flash('Fornecedor cadastrado com sucesso!', 'success')
        return redirect(url_for('fornecedores.listar'))
    
    flash('Erro ao cadastrar.', 'danger')
    return render_template('fornecedores/cadastrar.html')

# RF05.3 - Editar
@fornecedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario_logado = verificar_permissao(['administrador', 'fornecedor'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    query_buscar = """
        SELECT f.*, u.nome, u.email, u.telefone, u.ativo
        FROM fornecedores f
        JOIN usuarios u ON f.usuario_id = u.id
        WHERE f.id = %s
    """
    fornecedor = executar_query(query_buscar, (id,), fetchone=True)
    
    if not fornecedor:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores.listar'))
    
    if request.method == 'GET':
        return render_template('fornecedores/editar.html', fornecedor=fornecedor)
    
    # Atualiza dados
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()
    telefone = request.form.get('telefone', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    endereco = request.form.get('endereco', '').strip()
    
    query_usuario = """
        UPDATE usuarios 
        SET nome = %s, email = %s, telefone = %s, data_atualizacao = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    executar_query(query_usuario, (nome, email, telefone, fornecedor['usuario_id']), commit=True)
    
    query_fornecedor = """
        UPDATE fornecedores 
        SET razao_social = %s, endereco = %s
        WHERE id = %s
    """
    resultado = executar_query(query_fornecedor, (razao_social, endereco, id), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'fornecedores', id, 'UPDATE')
        flash('Fornecedor atualizado!', 'success')
    
    return redirect(url_for('fornecedores.listar'))

# RF05.4 - Excluir
@fornecedores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    usuario_logado = verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Impedir exclusão se houver vínculos relevantes
    bloqueios = []
    q1 = "SELECT COUNT(*) AS total FROM produtos WHERE fornecedor_id = %s"
    r1 = executar_query(q1, (id,), fetchone=True)
    if r1 and int(r1['total']) > 0:
        bloqueios.append('Possui produtos vinculados ao fornecedor.')

    q2 = "SELECT COUNT(*) AS total FROM repasses_financeiros WHERE fornecedor_id = %s"
    r2 = executar_query(q2, (id,), fetchone=True)
    if r2 and int(r2['total']) > 0:
        bloqueios.append('Possui repasses financeiros vinculados.')

    if bloqueios:
        flash('Não é possível excluir este fornecedor. Motivos: ' + ' '.join(bloqueios) + ' Você pode inativá-lo ao invés de excluir.', 'warning')
        return redirect(url_for('fornecedores.listar'))

    query_excluir = "DELETE FROM fornecedores WHERE id = %s"
    resultado = executar_query(query_excluir, (id,), commit=True)
    
    if resultado:
        registrar_log(usuario_logado['id'], 'fornecedores', id, 'DELETE')
        flash('Fornecedor excluído!', 'success')
    
    return redirect(url_for('fornecedores.listar'))
