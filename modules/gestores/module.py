"""
============================================
RF04 - MANTER CADASTRO DE GESTOR ESCOLAR
============================================
Este módulo é responsável por:
- RF04.1: Listar gestores escolares
- RF04.2: Criar gestor escolar
- RF04.3: Editar gestor escolar
- RF04.4: Apagar gestor escolar

Controla o processo de gerenciamento de gestores escolares no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import GestorEscolarRepository, EscolaRepository
from core.services import AutenticacaoService, ValidacaoService, LogService

# ============================================
# CONFIGURAÇÃO DO BLUEPRINT
# ============================================
gestores_bp = Blueprint('gestores', __name__, url_prefix='/gestores')

# ============================================
# INICIALIZAÇÃO DOS REPOSITÓRIOS E SERVIÇOS
# ============================================
gestor_repo = GestorEscolarRepository()
escola_repo = EscolaRepository()
auth_service = AutenticacaoService()
validacao = ValidacaoService()


# ============================================
# RF04.1 - LISTAR GESTORES ESCOLARES
# ============================================

@gestores_bp.route('/escola/<int:escola_id>')
@gestores_bp.route('/escola/<int:escola_id>/listar')
def listar(escola_id):
    """
    Lista todos os gestores de uma escola específica.
    
    Funcionalidades:
    - Verifica autenticação do usuário
    - Valida existência da escola
    - Verifica permissões de acesso (administrador ou escola proprietária)
    - Busca e exibe todos os gestores da escola
    
    Args:
        escola_id (int): ID da escola
        
    Returns:
        Template com lista de gestores ou redirecionamento em caso de erro
    """
    # Verifica autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca escola
    escola = escola_repo.buscar_com_usuario(escola_id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica permissões (administrador ou escola proprietária)
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca gestores da escola
    gestores = gestor_repo.listar_por_escola(escola_id)
    
    return render_template('gestores/listar.html', escola=escola, gestores=gestores)


# ============================================
# RF04.2 - CRIAR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/escola/<int:escola_id>/cadastrar', methods=['GET', 'POST'])
def cadastrar(escola_id):
    """
    Cadastra um novo gestor escolar vinculado a uma escola.
    
    Funcionalidades:
    - GET: Exibe formulário de cadastro
    - POST: Processa e valida os dados do novo gestor
    - Verifica autenticação e permissões
    - Valida campos obrigatórios (nome)
    - Valida formato de telefone e CPF
    - Registra log da operação
    
    Args:
        escola_id (int): ID da escola à qual o gestor será vinculado
        
    Returns:
        GET: Template do formulário de cadastro
        POST: Redirecionamento para lista de gestores após sucesso
    """
    # Verifica autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca escola
    escola = escola_repo.buscar_com_usuario(escola_id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica permissões (administrador ou escola proprietária)
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # GET: Exibe formulário
    if request.method == 'GET':
        return render_template('gestores/cadastrar.html', escola=escola)
    
    # POST: Processa cadastro
    dados = {
        'escola_id': escola_id,
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower() or None,
        'telefone': request.form.get('telefone', '').strip() or None,
        'cpf': request.form.get('cpf', '').strip() or None,
        'tipo_gestor': request.form.get('tipo_gestor', '').strip() or None
    }
    
    # Validação: Nome obrigatório
    if not dados['nome']:
        flash('Informe o nome do gestor.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    # Validação: Telefone
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    # Validação: CPF
    if dados['cpf'] and not validacao.validar_cpf(dados['cpf']):
        flash('CPF inválido.', 'danger')
        return render_template('gestores/cadastrar.html', escola=escola)
    
    # Insere gestor
    gestor_id = gestor_repo.inserir(dados)
    if gestor_id:
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', gestor_id, 'INSERT',
                           dados_novos=dados, descricao='Cadastro de gestor escolar')
        flash('Gestor cadastrado com sucesso!', 'success')
    
    return redirect(url_for('gestores.listar', escola_id=escola_id))


# ============================================
# RF04.3 - EDITAR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita os dados de um gestor escolar existente.
    
    Funcionalidades:
    - GET: Exibe formulário preenchido com dados atuais
    - POST: Processa e valida as alterações
    - Verifica autenticação e permissões
    - Valida campos obrigatórios e formatos
    - Registra log da operação
    
    Args:
        id (int): ID do gestor a ser editado
        
    Returns:
        GET: Template do formulário de edição
        POST: Redirecionamento para lista de gestores após sucesso
    """
    # Verifica autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca gestor
    gestor = gestor_repo.buscar_por_id(id)
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca escola associada
    escola = escola_repo.buscar_com_usuario(gestor['escola_id'])
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica permissões (administrador ou escola proprietária)
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # GET: Exibe formulário
    if request.method == 'GET':
        gestor['escola_nome'] = escola['nome']
        gestor['escola_id'] = escola['id']
        return render_template('gestores/editar.html', gestor=gestor)
    
    # POST: Processa atualização
    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower() or None,
        'telefone': request.form.get('telefone', '').strip() or None,
        'cpf': request.form.get('cpf', '').strip() or None,
        'tipo_gestor': request.form.get('tipo_gestor', '').strip() or None
    }
    
    # Validação: Nome obrigatório
    if not dados['nome']:
        flash('Informe o nome do gestor.', 'danger')
        gestor['escola_nome'] = escola['nome']
        gestor['escola_id'] = escola['id']
        return render_template('gestores/editar.html', gestor=gestor)
    
    # Validação: Telefone
    if dados['telefone'] and not validacao.validar_telefone(dados['telefone']):
        flash('Telefone inválido.', 'danger')
        gestor['escola_nome'] = escola['nome']
        gestor['escola_id'] = escola['id']
        return render_template('gestores/editar.html', gestor=gestor)
    
    # Validação: CPF
    if dados['cpf'] and not validacao.validar_cpf(dados['cpf']):
        flash('CPF inválido.', 'danger')
        gestor['escola_nome'] = escola['nome']
        gestor['escola_id'] = escola['id']
        return render_template('gestores/editar.html', gestor=gestor)
    
    # Atualiza gestor
    if gestor_repo.atualizar(id, dados):
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', id, 'UPDATE',
                           dados_antigos=dict(gestor), dados_novos=dados,
                           descricao='Atualização de gestor escolar')
        flash('Gestor atualizado com sucesso!', 'success')
    
    return redirect(url_for('gestores.listar', escola_id=gestor['escola_id']))


# ============================================
# RF04.4 - APAGAR GESTOR ESCOLAR
# ============================================

@gestores_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """
    Exclui um gestor escolar do sistema.
    
    Funcionalidades:
    - Remove permanentemente o gestor
    - Verifica autenticação e permissões
    - Valida existência do gestor
    - Registra log da operação
    
    Args:
        id (int): ID do gestor a ser excluído
        
    Returns:
        Redirecionamento para lista de gestores após exclusão
    """
    # Verifica autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca gestor
    gestor = gestor_repo.buscar_por_id(id)
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca escola associada
    escola = escola_repo.buscar_com_usuario(gestor['escola_id'])
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica permissões (administrador ou escola proprietária)
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Exclui gestor
    if gestor_repo.excluir(id):
        LogService.registrar(usuario_logado['id'], 'gestores_escolares', id, 'DELETE',
                           dados_antigos=dict(gestor), descricao='Exclusão de gestor escolar')
        flash('Gestor excluído com sucesso!', 'success')
    
    return redirect(url_for('gestores.listar', escola_id=gestor['escola_id']))


# ============================================
# VISUALIZAR DETALHES DO GESTOR (OPCIONAL)
# ============================================

@gestores_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """
    Exibe os detalhes completos de um gestor escolar.
    
    Funcionalidades:
    - Mostra todas as informações do gestor
    - Verifica autenticação e permissões
    - Exibe dados da escola associada
    
    Args:
        id (int): ID do gestor
        
    Returns:
        Template com detalhes do gestor
    """
    # Verifica autenticação
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca gestor
    gestor = gestor_repo.buscar_por_id(id)
    if not gestor:
        flash('Gestor não encontrado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca escola associada
    escola = escola_repo.buscar_com_usuario(gestor['escola_id'])
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('home'))
    
    # Verifica permissões (administrador ou escola proprietária)
    if usuario_logado['tipo'] != 'administrador' and \
       (usuario_logado['tipo'] != 'escola' or escola['usuario_id'] != usuario_logado['id']):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Adiciona informações da escola
    gestor['escola_nome'] = escola['nome']
    gestor['escola_id'] = escola['id']
    
    return render_template('gestores/detalhes.html', gestor=gestor, escola=escola)
