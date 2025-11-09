"""
============================================
RF04 - MANTER CADASTRO DE GESTOR ESCOLA
============================================
Este módulo é responsável por:
- RF04.1: Criar gestor escolar
- RF04.2: Apagar gestor escolar
- RF04.3: Editar gestor escolar
- RF04.4: Consultar gestor escolar

Controla o processo de gestão de gestores escolares no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import EscolaRepository, GestorEscolarRepository
from core.services import AutenticacaoService, ValidacaoService, LogService
from core.database import Database

# Blueprint e Serviços
gestores_bp = Blueprint('gestores', __name__, url_prefix='/gestores')
escola_repo = EscolaRepository()
gestor_repo = GestorEscolarRepository()
auth_service = AutenticacaoService()
validacao = ValidacaoService()


# ============================================
# RF04.1 - CADASTRAR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/escola/<int:escola_id>/cadastrar', methods=['GET', 'POST'])
def cadastrar(escola_id):
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
    
    return redirect(url_for('gestores.listar', escola_id=escola_id))


# ============================================
# RF04.4 - CONSULTAR GESTORES ESCOLARES
# ============================================

@gestores_bp.route('/escola/<int:escola_id>')
@gestores_bp.route('/escola/<int:escola_id>/listar')
def listar(escola_id):
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
# RF04.3 - EDITAR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
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
    
    return redirect(url_for('gestores.listar', escola_id=gestor['escola_id']))


# ============================================
# RF04.2 - EXCLUIR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
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
    
    return redirect(url_for('gestores.listar', escola_id=gestor['escola_id']))


# ============================================
# ATALHO - GESTORES DA PRÓPRIA ESCOLA
# ============================================

@gestores_bp.route('/meus-gestores')
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
    
    return redirect(url_for('gestores.listar', escola_id=escola['id']))
