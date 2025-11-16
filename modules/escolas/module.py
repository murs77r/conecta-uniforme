"""
============================================
RF03 - MANTER CADASTRO DE ESCOLA
============================================
Este módulo é responsável por:
- RF03.1: Listar escolas
- RF03.2: Criar escola
- RF03.3: Visualizar escola
- RF03.4: Editar escola
- RF03.5: Apagar escola

Controla o processo de cadastro e gestão de escolas no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import EscolaRepository, UsuarioRepository, GestorEscolarRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService
from core.database import Database

# Blueprint e Serviços
escolas_bp = Blueprint('escolas', __name__, url_prefix='/escolas')
escola_repo = EscolaRepository()
usuario_repo = UsuarioRepository()
gestor_repo = GestorEscolarRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(escola_repo, 'Escola')
validacao = ValidacaoService()


# ============================================
# RF03.1 - LISTAR ESCOLAS
# ============================================

@escolas_bp.route('/')
@escolas_bp.route('/listar')
def listar():
    """Lista todas as escolas cadastradas"""
    # Verifica se o usuário está logado
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca escolas com dados do usuário através do repositório
    escolas = escola_repo.listar_com_filtros({}) or []
    
    return render_template('escolas/listar.html', escolas=escolas)


# ============================================
# RF03.2 - CRIAR ESCOLA
# ============================================

@escolas_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Cadastra uma nova escola"""
    # Verifica permissão de administrador
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # GET: Exibe o formulário de cadastro
    if request.method == 'GET':
        return render_template('escolas/cadastrar.html')
    
    # POST: Processa o cadastro
    # Coleta dados do usuário (login da escola)
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip(),
        'tipo': 'escola',
        'ativo': True
    }
    
    # Coleta dados específicos da escola
    dados_escola = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip(),
        'ativo': True
    }
    
    # Validação: Campos obrigatórios
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_escola['cnpj'], dados_escola['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Validação: CNPJ válido
    if not validacao.validar_cnpj(dados_escola['cnpj']):
        flash('CNPJ inválido.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Verifica duplicidade de email
    if usuario_repo.buscar_por_email_tipo(dados_usuario['email'], 'escola'):
        flash('Email já cadastrado para perfil Escola.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Insere usuário (login)
    usuario_id = usuario_repo.inserir(dados_usuario)
    if not usuario_id:
        flash('Erro ao cadastrar usuário.', 'danger')
        return render_template('escolas/cadastrar.html')
    
    # Insere escola vinculada ao usuário
    dados_escola['usuario_id'] = usuario_id
    escola_id = crud_service.criar_com_log(dados_escola, usuario_logado['id'])
    
    if not escola_id:
        return render_template('escolas/cadastrar.html')
    
    # Processa gestores escolares (se informados)
    _processar_gestores(request.form, escola_id)
    
    flash('Escola cadastrada com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# RF03.3 - VISUALIZAR DETALHES DA ESCOLA
# ============================================

@escolas_bp.route('/visualizar/<int:id>')
@escolas_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """Exibe os detalhes completos de uma escola"""
    # Verifica se o usuário está logado
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca escola com dados do usuário
    escola = escola_repo.buscar_com_usuario(id)
    if not escola:
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Busca gestores da escola
    gestores = gestor_repo.listar_por_escola(id)
    
    return render_template('escolas/detalhes.html', 
                         escola=escola,
                         gestores=gestores)


# ============================================
# RF03.4 - EDITAR ESCOLA
# ============================================

@escolas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita uma escola existente"""
    # Verifica permissão (administrador ou a própria escola)
    usuario_logado = auth_service.verificar_permissao(['administrador', 'escola'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca escola
    escola = escola_repo.buscar_com_usuario(id)
    if not escola or not isinstance(escola, dict):
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica se escola pode editar apenas seus próprios dados
    if usuario_logado['tipo'] == 'escola' and escola['usuario_id'] != usuario_logado['id']:
        flash('Você só pode editar suas próprias informações.', 'danger')
        return redirect(url_for('home'))
    
    # GET: Exibe formulário de edição
    if request.method == 'GET':
        gestores = gestor_repo.listar_por_escola(id)
        return render_template('escolas/editar.html', escola=escola, gestores=gestores)
    
    # POST: Processa atualização
    # Coleta dados do usuário
    dados_usuario = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': request.form.get('telefone', '').strip()
    }
    
    # Coleta dados da escola
    dados_escola = {
        'cnpj': request.form.get('cnpj', '').strip(),
        'razao_social': request.form.get('razao_social', '').strip(),
        'endereco': request.form.get('endereco', '').strip(),
        'cidade': request.form.get('cidade', '').strip(),
        'estado': request.form.get('estado', '').strip(),
        'cep': request.form.get('cep', '').strip()
    }
    
    # Validação: Telefone
    if dados_usuario['telefone'] and not validacao.validar_telefone(dados_usuario['telefone']):
        flash('Telefone inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Validação: CEP
    if dados_escola['cep'] and not validacao.validar_cep(dados_escola['cep']):
        flash('CEP inválido.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Apenas administrador pode alterar status
    if usuario_logado['tipo'] == 'administrador':
        ativo = request.form.get('ativo') == 'on'
        dados_usuario['ativo'] = ativo
        dados_escola['ativo'] = ativo
    
    # Validação: Campos obrigatórios
    if not all([dados_usuario['nome'], dados_usuario['email'], 
                dados_escola['cnpj'], dados_escola['razao_social']]):
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return render_template('escolas/editar.html', escola=escola)
    
    # Atualiza usuário
    usuario_repo.atualizar(escola['usuario_id'], dados_usuario)
    
    # Atualiza escola
    crud_service.atualizar_com_log(id, dados_escola, dict(escola), usuario_logado['id'])
    
    # Atualiza gestores (remove todos e insere novamente)
    gestor_repo.excluir_por_escola(id)
    _processar_gestores(request.form, id)
    
    flash('Escola atualizada com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# RF03.5 - APAGAR ESCOLA
# ============================================

@escolas_bp.route('/excluir/<int:id>', methods=['POST'])
@escolas_bp.route('/apagar/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui (apaga) uma escola do sistema"""
    # Apenas administrador pode excluir
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    # Busca escola
    escola = escola_repo.buscar_por_id(id)
    if not escola or not isinstance(escola, dict):
        flash('Escola não encontrada.', 'danger')
        return redirect(url_for('escolas.listar'))
    
    # Verifica dependências (não permite excluir se houver registros relacionados)
    bloqueios = crud_service.verificar_dependencias(id, [
        {'tabela': 'homologacao_fornecedores', 'campo': 'escola_id', 'mensagem': 'fornecedores homologados'},
        {'tabela': 'produtos', 'campo': 'escola_id', 'mensagem': 'produtos'},
        {'tabela': 'pedidos', 'campo': 'escola_id', 'mensagem': 'pedidos'}
    ])
    
    if bloqueios:
        flash('Não é possível excluir esta escola. ' + ' '.join(bloqueios) + 
              ' Você pode inativá-la ao invés de excluir.', 'warning')
        return redirect(url_for('escolas.listar'))
    
    # Exclui escola (com log)
    crud_service.excluir_com_log(id, dict(escola), usuario_logado['id'])
    
    flash('Escola excluída com sucesso!', 'success')
    return redirect(url_for('escolas.listar'))


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def _processar_gestores(form_data, escola_id):
    """
    Processa e insere gestores escolares a partir do formulário.
    Gestores são contatos adicionais da escola (diretor, coordenador, etc)
    """
    # Identifica índices dos gestores no formulário
    indices = set()
    for k in form_data.keys():
        if k.startswith('gestores['):
            try:
                idx = k.split('[', 1)[1].split(']', 1)[0]
                indices.add(idx)
            except Exception:
                pass
    
    # Insere cada gestor
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
