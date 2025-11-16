"""
============================================
RF07 - MANTER CADASTRO DE PEDIDO
============================================
Este módulo é responsável por:
- RF07.1: Criar pedido
- RF07.2: Apagar pedido
- RF07.3: Editar pedido
- RF07.4: Consultar pedidos

Controla o processo de controle de pedidos no sistema.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories import PedidoRepository, ResponsavelRepository
from core.services import AutenticacaoService, LogService
from core.database import Database

# Blueprint e Serviços
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')
pedido_repo = PedidoRepository()
responsavel_repo = ResponsavelRepository()

# ============================================
# RF07.1 - CRIAR PEDIDO
# ============================================
auth_service = AutenticacaoService()

@pedidos_bp.route('/criar', methods=['GET', 'POST'])
def criar():
    """Cria um novo pedido (Rota administrativa)"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    if usuario_logado['tipo'] != 'administrador':
        flash('Acesso negado. Apenas administradores podem criar pedidos manualmente.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        dados = {
            'responsavel_id': request.form.get('responsavel_id'),
            'escola_id': request.form.get('escola_id'),
            'status': request.form.get('status', 'pendente'),
            'valor_total': request.form.get('valor_total', 0)
        }

        pedido_id = Database.inserir('pedidos', dados)
        if pedido_id:
            LogService.registrar(usuario_logado['id'], 'pedidos', pedido_id, 'INSERT', descricao='Pedido criado')
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('pedidos.listar'))
        else:
            flash('Erro ao criar pedido.', 'danger')

    # GET - Exibe formulário
    return render_template('pedidos/criar.html')


@pedidos_bp.route('/carrinho')
def ver_carrinho():
    """Exibe o carrinho atual do responsável logado (status 'carrinho')."""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    # Apenas responsáveis devem acessar o carrinho
    if usuario_logado['tipo'] != 'responsavel':
        flash('Acesso negado. Apenas responsáveis podem acessar o carrinho.', 'danger')
        return redirect(url_for('home'))

    responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not responsavel:
        # Exibe template com carrinho vazio
        return render_template('pedidos/carrinho.html', pedido=None, itens=[])

    carrinho = pedido_repo.buscar_carrinho(responsavel['id'])
    if not carrinho:
        return render_template('pedidos/carrinho.html', pedido=None, itens=[])

    pedido_id = carrinho['id']
    query_pedido = "SELECT * FROM pedidos WHERE id = %s"
    pedido = Database.executar(query_pedido, (pedido_id,), fetchone=True)

    query_itens = """
        SELECT i.*, p.nome as produto_nome, p.descricao as produto_descricao, p.imagem_url as produto_imagem
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
        ORDER BY i.id
    """
    itens = Database.executar(query_itens, (pedido_id,), fetchall=True) or []

    return render_template('pedidos/carrinho.html', pedido=pedido, itens=itens)


@pedidos_bp.route('/finalizar/<int:id>', methods=['POST'])
def finalizar(id):
    """Finaliza o pedido com status 'carrinho' (deixa como 'pendente')."""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    # Busca o pedido
    pedido = Database.executar("SELECT * FROM pedidos WHERE id = %s", (id,), fetchone=True)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))

    # Validação de permissão: só administrador ou dono do pedido podem finalizar
    if usuario_logado['tipo'] != 'administrador':
        if usuario_logado['tipo'] == 'responsavel':
            responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
            if not responsavel or pedido['responsavel_id'] != responsavel['id']:
                flash('Acesso negado. Você só pode finalizar seus próprios pedidos.', 'danger')
                return redirect(url_for('pedidos.listar'))
        else:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.listar'))

    # Só finaliza se estiver em 'carrinho'
    if pedido['status'] != 'carrinho':
        flash('Somente pedidos em status carrinho podem ser finalizados.', 'danger')
        return redirect(url_for('pedidos.listar'))

    # Atualiza status e registra log
    if Database.atualizar('pedidos', id, {'status': 'pendente'}):
        LogService.registrar(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido finalizado')
        flash('Pedido finalizado com sucesso!', 'success')
    else:
        flash('Erro ao finalizar pedido.', 'danger')

    return redirect(url_for('pedidos.listar'))


@pedidos_bp.route('/adicionar_item', methods=['POST'])
def adicionar_item():
    """Adiciona um produto ao carrinho do responsável logado.

    Fluxo:
    - Verifica sessão e tipo: apenas 'responsavel' pode adicionar itens ao carrinho
    - Valida existencia do produto, estoque e status ativo
    - Encontra ou cria um pedido com status 'carrinho' para o responsavel
    - Se o item já existe no carrinho: atualiza quantidade e subtotal
    - Caso contrário: insere novo item
    - Atualiza o valor_total do pedido
    """
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    if usuario_logado['tipo'] != 'responsavel':
        flash('Apenas responsáveis podem adicionar itens ao carrinho.', 'danger')
        return redirect(url_for('home'))

    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade', 1))

    # Valida produto
    produto = Database.executar('SELECT * FROM produtos WHERE id = %s', (produto_id,), fetchone=True)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))

    if not produto.get('ativo'):
        flash('Produto inativo.', 'warning')
        return redirect(url_for('produtos.vitrine'))

    if produto.get('estoque', 0) < quantidade:
        flash('Quantidade solicitada maior que o estoque disponível.', 'warning')
        return redirect(url_for('produtos.vitrine'))

    responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not responsavel:
        flash('Responsável não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))


    preco_unitario = float(produto['preco'])

    # Realiza todas as operações em uma transação atômica:
    def operacoes_cart(cursor):
        # Busca carrinho existente
        cursor.execute("SELECT id FROM pedidos WHERE responsavel_id = %s AND status = 'carrinho' ORDER BY data_pedido DESC LIMIT 1", (responsavel['id'],))
        carrinho_row = cursor.fetchone()
        if carrinho_row and carrinho_row.get('id'):
            pedido_id_local = carrinho_row['id']
        else:
            # Cria novo pedido
            cursor.execute("INSERT INTO pedidos (responsavel_id, escola_id, status, valor_total) VALUES (%s,%s,%s,%s) RETURNING id",
                           (responsavel['id'], produto.get('escola_id'), 'carrinho', 0))
            pedido_id_local = cursor.fetchone()['id']

        # Verifica se item já existe
        cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = %s AND produto_id = %s", (pedido_id_local, produto_id))
        item_existente_local = cursor.fetchone()

        if item_existente_local:
            nova_quantidade_local = int(item_existente_local['quantidade']) + quantidade
            novo_subtotal_local = round(preco_unitario * nova_quantidade_local, 2)
            cursor.execute("UPDATE itens_pedido SET quantidade = %s, subtotal = %s WHERE id = %s",
                           (nova_quantidade_local, novo_subtotal_local, item_existente_local['id']))
        else:
            novo_subtotal_local = round(preco_unitario * quantidade, 2)
            cursor.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal) VALUES (%s,%s,%s,%s,%s)",
                           (pedido_id_local, produto_id, quantidade, preco_unitario, novo_subtotal_local))

        # Atualiza valor_total do pedido
        cursor.execute("SELECT COALESCE(SUM(subtotal),0) as total FROM itens_pedido WHERE pedido_id = %s", (pedido_id_local,))
        total_row_local = cursor.fetchone()
        total_local = float(total_row_local.get('total', 0)) if total_row_local and isinstance(total_row_local, dict) else 0
        cursor.execute("UPDATE pedidos SET valor_total = %s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s", (total_local, pedido_id_local))
        return pedido_id_local

    pedido_id = Database.transaction(operacoes_cart)
    if not pedido_id:
        flash('Erro ao criar/atualizar carrinho.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    return redirect(url_for('pedidos.ver_carrinho'))

    return redirect(url_for('pedidos.ver_carrinho'))


# ============================================
# RF07.3 - EDITAR PEDIDO
# ============================================

@pedidos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita um pedido existente"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca o pedido
    query = "SELECT * FROM pedidos WHERE id = %s"
    pedido = Database.executar(query, (id,), fetchone=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))

    # ==================================================================
    # RF07.3 - REGRA DE NEGÓCIO: Impedir edição de pedidos finalizados
    # ==================================================================
    if pedido['status'] in ['entregue', 'cancelado']:
        flash(f"Pedidos com status '{pedido['status']}' não podem ser editados.", 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # ==================================================================
    # CORREÇÃO DE SEGURANÇA: Validar permissão (Admin ou Dono do Pedido)
    # ==================================================================
    if usuario_logado['tipo'] != 'administrador':
        if usuario_logado['tipo'] == 'responsavel':
            responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
            if not responsavel or pedido['responsavel_id'] != responsavel['id']:
                flash('Acesso negado. Você só pode editar seus próprios pedidos.', 'danger')
                return redirect(url_for('pedidos.listar'))
        else:
            # Outros tipos (escola, fornecedor) não podem editar
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.listar'))
    
    if request.method == 'POST':
        dados = {
            'status': request.form.get('status'),
            'valor_total': request.form.get('valor_total')
        }
        
        if Database.atualizar('pedidos', id, dados):
            LogService.registrar(usuario_logado['id'], 'pedidos', id, 'UPDATE', descricao='Pedido editado')
            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('pedidos.listar'))
        else:
            flash('Erro ao atualizar pedido.', 'danger')
    
    # GET - Exibe formulário
    return render_template('pedidos/editar.html', pedido=pedido)


# ============================================
# RF07.2 - APAGAR PEDIDO
# ============================================

@pedidos_bp.route('/apagar/<int:id>', methods=['POST'])
def apagar(id):
    """Apaga um pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Acesso negado. Faça login para continuar.', 'danger')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # ==================================================================
    # Buscar pedido para verificar propriedade
    # ==================================================================
    pedido = Database.executar("SELECT * FROM pedidos WHERE id = %s", (id,), fetchone=True)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))

    # ==================================================================
    # Impedir exclusão de pedidos em andamento ou finalizados
    # ==================================================================
    if pedido['status'] in ['pago', 'enviado', 'entregue']:
        flash(f"Pedidos com status '{pedido['status']}' não podem ser apagados, apenas cancelados.", 'danger')
        return redirect(url_for('pedidos.listar'))

    # ==================================================================
    # Validar permissão (Admin ou Dono do Pedido)
    # ==================================================================
    if usuario_logado['tipo'] != 'administrador':
        if usuario_logado['tipo'] == 'responsavel':
            responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
            if not responsavel or pedido['responsavel_id'] != responsavel['id']:
                flash('Acesso negado. Você só pode apagar seus próprios pedidos.', 'danger')
                return redirect(url_for('pedidos.listar'))
        else:
            # Outros tipos (escola, fornecedor) não podem apagar
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.listar'))

    # Se passou na verificação, pode apagar
    # Verifica se há itens vinculados ao pedido (bloqueia exclusão para responsáveis)
    query_itens_count = "SELECT COUNT(*) AS total FROM itens_pedido WHERE pedido_id = %s"
    resultado_count = Database.executar(query_itens_count, (id,), fetchone=True)
    total_itens = int(resultado_count.get('total', 0)) if resultado_count and isinstance(resultado_count, dict) else 0

    if total_itens > 0:
        # Administradores podem apagar pedidos com itens (remove itens primeiro)
        if usuario_logado['tipo'] == 'administrador':
            # Tenta apagar os itens do pedido e em seguida o pedido dentro de uma transação
            def operacao_apagar(cursor):
                cursor.execute("DELETE FROM itens_pedido WHERE pedido_id = %s", (id,))
                cursor.execute("DELETE FROM pedidos WHERE id = %s", (id,))
                return True

            if Database.transaction(operacao_apagar):
                LogService.registrar(usuario_logado['id'], 'pedidos', id, 'DELETE', descricao='Pedido apagado (com itens)')
                flash('Pedido apagado com sucesso (itens removidos)!', 'success')
            else:
                flash('Erro ao apagar pedido após remover itens.', 'danger')
        else:
            # Usuários responsáveis não podem apagar pedidos que possuem itens por integridade de dados
            flash('Não é possível apagar este pedido porque há itens vinculados. Remova os itens do carrinho antes de apagar o pedido.', 'warning')
            return redirect(url_for('pedidos.listar'))
    else:
        query = "DELETE FROM pedidos WHERE id = %s"
        if Database.executar(query, (id,), commit=True):
            LogService.registrar(usuario_logado['id'], 'pedidos', id, 'DELETE', descricao='Pedido apagado')
            flash('Pedido apagado com sucesso!', 'success')
        else:
            flash('Erro ao apagar pedido.', 'danger')
    
    return redirect(url_for('pedidos.listar'))


# ============================================
# RF07.4 - CONSULTAR DETALHES DO PEDIDO
# ============================================

@pedidos_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """Visualiza detalhes completos de um pedido"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    # Busca o pedido com todas as informações
    query_pedido = """
        SELECT p.*, 
               r.cpf as responsavel_cpf,
               u.telefone as responsavel_telefone,
               r.endereco as responsavel_endereco,
               u.nome as responsavel_nome,
               u.email as responsavel_email,
               e.id as escola_id,
               e_usr.nome as escola_nome,
               e.cnpj as escola_cnpj,
               e.endereco as escola_endereco
        FROM pedidos p
        JOIN responsaveis r ON p.responsavel_id = r.id
        JOIN usuarios u ON r.usuario_id = u.id
        LEFT JOIN escolas e ON p.escola_id = e.id
        LEFT JOIN usuarios e_usr ON e.usuario_id = e_usr.id
        WHERE p.id = %s
    """
    pedido = Database.executar(query_pedido, (id,), fetchone=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.listar'))
    
    # Verifica permissão
    if usuario_logado['tipo'] == 'responsavel':
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not responsavel or pedido['responsavel_id'] != responsavel['id']:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.listar'))
    
    # Busca itens do pedido
    query_itens = """
        SELECT i.*, 
               p.nome as produto_nome, 
               p.descricao as produto_descricao, 
               p.imagem_url as produto_imagem
        FROM itens_pedido i
        JOIN produtos p ON i.produto_id = p.id
        WHERE i.pedido_id = %s
        ORDER BY i.id
    """
    itens = Database.executar(query_itens, (id,), fetchall=True) or []
    
    return render_template('pedidos/detalhes.html', pedido=pedido, itens=itens)


# ============================================
# COMPLEMENTAR/OPCIONAL - Gerenciar itens do carrinho
# ============================================

def adicionar_item_complementar():
    """Complementar: Adiciona um produto ao carrinho do responsável logado."""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    if usuario_logado['tipo'] != 'responsavel':
        flash('Apenas responsáveis podem adicionar itens ao carrinho.', 'danger')
        return redirect(url_for('home'))

    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade', 1))

    # Valida produto
    produto = Database.executar('SELECT * FROM produtos WHERE id = %s', (produto_id,), fetchone=True)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))

    if not produto.get('ativo'):
        flash('Produto inativo.', 'warning')
        return redirect(url_for('produtos.vitrine'))

    if produto.get('estoque', 0) < quantidade:
        flash('Quantidade solicitada maior que o estoque disponível.', 'warning')
        return redirect(url_for('produtos.vitrine'))

    responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
    if not responsavel:
        flash('Responsável não encontrado.', 'danger')
        return redirect(url_for('produtos.vitrine'))

    preco_unitario = float(produto['preco'])

    def operacoes_cart(cursor):
        # Busca carrinho existente
        cursor.execute("SELECT id FROM pedidos WHERE responsavel_id = %s AND status = 'carrinho' ORDER BY data_pedido DESC LIMIT 1", (responsavel['id'],))
        carrinho_row = cursor.fetchone()
        if carrinho_row and carrinho_row.get('id'):
            pedido_id_local = carrinho_row['id']
        else:
            # Cria novo pedido
            cursor.execute("INSERT INTO pedidos (responsavel_id, escola_id, status, valor_total) VALUES (%s,%s,%s,%s) RETURNING id",
                           (responsavel['id'], produto.get('escola_id'), 'carrinho', 0))
            pedido_id_local = cursor.fetchone()['id']

        # Verifica se item já existe
        cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = %s AND produto_id = %s", (pedido_id_local, produto_id))
        item_existente_local = cursor.fetchone()

        if item_existente_local:
            nova_quantidade_local = int(item_existente_local['quantidade']) + quantidade
            novo_subtotal_local = round(preco_unitario * nova_quantidade_local, 2)
            cursor.execute("UPDATE itens_pedido SET quantidade = %s, subtotal = %s WHERE id = %s",
                           (nova_quantidade_local, novo_subtotal_local, item_existente_local['id']))
        else:
            novo_subtotal_local = round(preco_unitario * quantidade, 2)
            cursor.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal) VALUES (%s,%s,%s,%s,%s)",
                           (pedido_id_local, produto_id, quantidade, preco_unitario, novo_subtotal_local))

        # Atualiza valor_total do pedido
        cursor.execute("SELECT COALESCE(SUM(subtotal),0) as total FROM itens_pedido WHERE pedido_id = %s", (pedido_id_local,))
        total_row_local = cursor.fetchone()
        total_local = float(total_row_local.get('total', 0)) if total_row_local and isinstance(total_row_local, dict) else 0
        cursor.execute("UPDATE pedidos SET valor_total = %s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s", (total_local, pedido_id_local))
        return pedido_id_local

    pedido_id = Database.transaction(operacoes_cart)
    if not pedido_id:
        flash('Erro ao criar/atualizar carrinho.', 'danger')
        return redirect(url_for('produtos.vitrine'))
    return redirect(url_for('pedidos.ver_carrinho'))

@pedidos_bp.route('/atualizar_item', methods=['POST'])
def atualizar_item():
    """Complementar: Atualiza quantidade de um item no carrinho"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    item_id = request.form.get('item_id')
    quantidade = int(request.form.get('quantidade', 1))

    if quantidade <= 0:
        flash('Quantidade inválida.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))

    # Valida item
    item = Database.executar('SELECT * FROM itens_pedido WHERE id = %s', (item_id,), fetchone=True)
    if not item:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))

    pedido = Database.executar('SELECT * FROM pedidos WHERE id = %s', (item['pedido_id'],), fetchone=True)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))

    # Permissão: apenas admin ou dono do pedido
    if usuario_logado['tipo'] != 'administrador':
        if usuario_logado['tipo'] != 'responsavel':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.ver_carrinho'))
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not responsavel or pedido['responsavel_id'] != responsavel['id']:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.ver_carrinho'))

    # Valida produto estoque atual
    produto = Database.executar('SELECT * FROM produtos WHERE id = %s', (item['produto_id'],), fetchone=True)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))
    if produto.get('estoque', 0) < quantidade:
        flash('Quantidade maior que estoque disponível.', 'warning')
        return redirect(url_for('pedidos.ver_carrinho'))

    preco_unitario = float(item['preco_unitario'])
    novo_subtotal = round(preco_unitario * quantidade, 2)

    def operacao_update(cursor):
        cursor.execute('UPDATE itens_pedido SET quantidade = %s, subtotal = %s WHERE id = %s', (quantidade, novo_subtotal, item_id))
        # Recalcula total
        cursor.execute('SELECT COALESCE(SUM(subtotal),0) as total FROM itens_pedido WHERE pedido_id = %s', (item['pedido_id'],))
        total_row = cursor.fetchone()
        total = float(total_row.get('total', 0)) if total_row and isinstance(total_row, dict) else 0
        cursor.execute('UPDATE pedidos SET valor_total = %s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s', (total, item['pedido_id']))
        return True

    if Database.transaction(operacao_update):
        flash('Item atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar item.', 'danger')

    return redirect(url_for('pedidos.ver_carrinho'))


@pedidos_bp.route('/remover_item', methods=['POST'])
def remover_item():
    """Complementar: Remove um item do carrinho"""
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        flash('Faça login para continuar.', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))

    item_id = request.form.get('item_id')

    # Valida item
    item = Database.executar('SELECT * FROM itens_pedido WHERE id = %s', (item_id,), fetchone=True)
    if not item:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))

    pedido = Database.executar('SELECT * FROM pedidos WHERE id = %s', (item['pedido_id'],), fetchone=True)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.ver_carrinho'))

    # Permissão: apenas admin ou dono do pedido
    if usuario_logado['tipo'] != 'administrador':
        if usuario_logado['tipo'] != 'responsavel':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.ver_carrinho'))
        responsavel = responsavel_repo.buscar_por_usuario_id(usuario_logado['id'])
        if not responsavel or pedido['responsavel_id'] != responsavel['id']:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('pedidos.ver_carrinho'))

    def operacao_remover(cursor):
        cursor.execute('DELETE FROM itens_pedido WHERE id = %s', (item_id,))
        # Recalcula total
        cursor.execute('SELECT COALESCE(SUM(subtotal),0) as total FROM itens_pedido WHERE pedido_id = %s', (item['pedido_id'],))
        total_row = cursor.fetchone()
        total = float(total_row.get('total', 0)) if total_row and isinstance(total_row, dict) else 0
        cursor.execute('UPDATE pedidos SET valor_total = %s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s', (total, item['pedido_id']))
        return True

    if Database.transaction(operacao_remover):
        flash('Item removido com sucesso!', 'success')
    else:
        flash('Erro ao remover item.', 'danger')

    return redirect(url_for('pedidos.ver_carrinho'))