"""
============================================
RF04.x - GERENCIAR GESTORES ESCOLARES
============================================
Este módulo é responsável por:
- Listar gestores por escola
- Cadastrar gestor
- Editar gestor
- Excluir gestor

Gerencia os gestores vinculados a uma escola.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import executar_query, validar_cpf, validar_telefone
from modules.autenticacao import verificar_sessao, verificar_permissao

# ============================================
# CRIAÇÃO DO BLUEPRINT (MICROFRONT-END)
# ============================================

gestores_bp = Blueprint('gestores', __name__, url_prefix='/gestores')


def _buscar_escola(escola_id):
    return executar_query(
        """
        SELECT e.id, e.usuario_id, u.nome as escola_nome
        FROM escolas e JOIN usuarios u ON e.usuario_id = u.id
        WHERE e.id = %s
        """,
        (escola_id,), fetchone=True
    )


def _pode_gerenciar(usuario, escola):
    if not usuario or not escola:
        return False
    if usuario['tipo'] == 'administrador':
        return True
    if usuario['tipo'] == 'escola' and escola['usuario_id'] == usuario['id']:
        return True
    return False


# ============================================
# LISTAR GESTORES DA ESCOLA
# ============================================

@gestores_bp.route('/escola/<int:escola_id>')
def listar_por_escola(escola_id):
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    escola = _buscar_escola(escola_id)
    if not escola or not _pode_gerenciar(usuario, escola):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    gestores = executar_query(
        """
        SELECT id, nome, email, telefone, cpf, tipo_gestor, data_cadastro
        FROM gestores_escolares
        WHERE escola_id = %s
        ORDER BY nome
        """,
        (escola_id,), fetchall=True
    ) or []

    return render_template('gestores/listar.html', escola=escola, gestores=gestores)


# ============================================
# CADASTRAR GESTOR
# ============================================

@gestores_bp.route('/escola/<int:escola_id>/cadastrar', methods=['GET', 'POST'])
def cadastrar(escola_id):
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    escola = _buscar_escola(escola_id)
    if not escola or not _pode_gerenciar(usuario, escola):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template('gestores/cadastrar.html', escola=escola)

    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower() or None
    telefone = request.form.get('telefone', '').strip() or None
    cpf = request.form.get('cpf', '').strip() or None
    tipo_gestor = request.form.get('tipo_gestor', '').strip() or None

    if not nome:
        flash('Informe o nome do gestor.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)

    if telefone and not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)

    if cpf and not validar_cpf(cpf):
        flash('CPF inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)

    executar_query(
        """
        INSERT INTO gestores_escolares (escola_id, nome, email, telefone, cpf, tipo_gestor)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (escola_id, nome, email, telefone, cpf, tipo_gestor), commit=True
    )

    flash('Gestor cadastrado com sucesso!', 'success')
    return redirect(url_for('gestores.listar_por_escola', escola_id=escola_id))


# ============================================
# EDITAR GESTOR
# ============================================

@gestores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    gestor = executar_query(
        """
        SELECT g.*, e.usuario_id, u.nome as escola_nome
        FROM gestores_escolares g
        JOIN escolas e ON g.escola_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE g.id = %s
        """,
        (id,), fetchone=True
    )
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))

    escola_stub = {'id': gestor['escola_id'], 'usuario_id': gestor['usuario_id'], 'escola_nome': gestor['escola_nome']}
    if not _pode_gerenciar(usuario, escola_stub):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template('gestores/editar.html', gestor=gestor)

    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower() or None
    telefone = request.form.get('telefone', '').strip() or None
    cpf = request.form.get('cpf', '').strip() or None
    tipo_gestor = request.form.get('tipo_gestor', '').strip() or None

    if not nome:
        flash('Informe o nome do gestor.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)

    if telefone and not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)

    if cpf and not validar_cpf(cpf):
        flash('CPF inválido.', 'danger')
        return render_template('gestores/editar.html', gestor=gestor)

    executar_query(
        """
        UPDATE gestores_escolares
        SET nome = %s, email = %s, telefone = %s, cpf = %s, tipo_gestor = %s
        WHERE id = %s
        """,
        (nome, email, telefone, cpf, tipo_gestor, id), commit=True
    )

    flash('Gestor atualizado com sucesso!', 'success')
    return redirect(url_for('gestores.listar_por_escola', escola_id=gestor['escola_id']))


# ============================================
# EXCLUIR GESTOR
# ============================================

@gestores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    gestor = executar_query(
        """
        SELECT g.id, g.escola_id, e.usuario_id
        FROM gestores_escolares g JOIN escolas e ON g.escola_id = e.id
        WHERE g.id = %s
        """,
        (id,), fetchone=True
    )
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))

    escola_stub = {'id': gestor['escola_id'], 'usuario_id': gestor['usuario_id']}
    if not _pode_gerenciar(usuario, escola_stub):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    executar_query("DELETE FROM gestores_escolares WHERE id = %s", (id,), commit=True)
    flash('Gestor excluído com sucesso!', 'success')
    return redirect(url_for('gestores.listar_por_escola', escola_id=gestor['escola_id']))


# ============================================
# MINHA PÁGINA (ATUALIZAÇÕES RECENTES)
# ============================================

@gestores_bp.route('/minha')
def minha():
    usuario = verificar_sessao()
    if not usuario:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    if usuario['tipo'] != 'escola':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    escola = executar_query("SELECT id FROM escolas WHERE usuario_id = %s", (usuario['id'],), fetchone=True)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('home'))
    return redirect(url_for('gestores.listar_por_escola', escola_id=escola['id']))
