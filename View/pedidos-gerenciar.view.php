<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gerenciar Pedidos - Conecta Uniforme</title>
</head>
<body>
    <h1>Pedidos</h1>
    <p>Usuário: <?= htmlspecialchars($_SESSION['user_nome']) ?> (<?= htmlspecialchars($user_tipo) ?>)</p>
    
    <nav>
        <?php if($user_tipo == 'responsavel'): ?>
            <a href="/dashboard-responsavel">Dashboard</a> |
            <a href="/catalogo-novo">Catálogo</a> |
        <?php elseif($user_tipo == 'fornecedor'): ?>
            <a href="/dashboard-fornecedor">Dashboard</a> |
            <a href="/produtos-fornecedor">Produtos</a> |
        <?php else: ?>
            <a href="/dashboard-gestor">Dashboard</a> |
        <?php endif; ?>
        <a href="/pedidos-gerenciar">Pedidos</a> |
        <a href="/logout">Sair</a>
    </nav>
    
    <hr>
    
    <?php if($mensagem): ?>
        <div style="color: green; border: 1px solid green; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($mensagem) ?>
        </div>
    <?php endif; ?>
    
    <?php if($erro): ?>
        <div style="color: red; border: 1px solid red; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($erro) ?>
        </div>
    <?php endif; ?>
    
    <?php if($pedido): ?>
        <!-- Detalhes do Pedido -->
        <h2>Pedido #<?= $pedido['id'] ?></h2>
        <p><a href="/pedidos-gerenciar">← Voltar para lista</a></p>
        
        <h3>Informações do Pedido</h3>
        <ul>
            <li><strong>Data:</strong> <?= date('d/m/Y H:i', strtotime($pedido['criado_em'])) ?></li>
            <li><strong>Status:</strong> <?= $status_labels[$pedido['status']] ?? $pedido['status'] ?></li>
            <li><strong>Responsável:</strong> <?= htmlspecialchars($pedido['responsavel_nome']) ?> (<?= htmlspecialchars($pedido['responsavel_email']) ?>)</li>
            <li><strong>Aluno:</strong> <?= htmlspecialchars($pedido['aluno_nome']) ?> - Matrícula: <?= htmlspecialchars($pedido['aluno_matricula']) ?></li>
            <li><strong>Escola:</strong> <?= htmlspecialchars($pedido['escola_nome']) ?></li>
            <li><strong>Total:</strong> R$ <?= number_format($pedido['total'], 2, ',', '.') ?></li>
            <li><strong>Comissão Plataforma (15%):</strong> R$ <?= number_format($pedido['comissao'], 2, ',', '.') ?></li>
        </ul>
        
        <h3>Itens do Pedido</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Fornecedor</th>
                    <th>Variação</th>
                    <th>Quantidade</th>
                    <th>Preço Unit.</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($itens as $item): ?>
                    <tr>
                        <td><?= htmlspecialchars($item['produto_nome']) ?></td>
                        <td><?= htmlspecialchars($item['fornecedor_nome']) ?></td>
                        <td>
                            Tamanho: <?= htmlspecialchars($item['tamanho']) ?><br>
                            <?php if($item['cor']): ?>Cor: <?= htmlspecialchars($item['cor']) ?><br><?php endif; ?>
                            Gênero: <?= htmlspecialchars($item['genero']) ?>
                        </td>
                        <td><?= $item['quantidade'] ?></td>
                        <td>R$ <?= number_format($item['preco_unitario'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($item['subtotal'], 2, ',', '.') ?></td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        
        <?php if($user_tipo == 'fornecedor' && count($proximos_status[$pedido['status']] ?? []) > 0): ?>
            <h3>Atualizar Status</h3>
            <form method="POST">
                <input type="hidden" name="pedido_id" value="<?= $pedido['id'] ?>">
                <label>Novo status:</label><br>
                <select name="status" required style="padding: 5px; width: 200px;">
                    <option value="">Selecione...</option>
                    <?php foreach($proximos_status[$pedido['status']] as $prox_status): ?>
                        <option value="<?= $prox_status ?>"><?= $status_labels[$prox_status] ?></option>
                    <?php endforeach; ?>
                </select>
                <br><br>
                <button type="submit" name="atualizar_status">Atualizar Status</button>
            </form>
        <?php endif; ?>
        
    <?php else: ?>
        <!-- Lista de Pedidos -->
        <h2>Lista de Pedidos</h2>
        
        <?php if(count($pedidos) > 0): ?>
            <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <?php if($user_tipo != 'responsavel'): ?><th>Aluno</th><?php endif; ?>
                        <?php if($user_tipo == 'fornecedor'): ?><th>Escola</th><?php endif; ?>
                        <?php if($user_tipo == 'gestor'): ?><th>Responsável</th><?php endif; ?>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Data</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($pedidos as $p): ?>
                        <tr>
                            <td><?= $p['id'] ?></td>
                            <?php if($user_tipo != 'responsavel'): ?>
                                <td><?= htmlspecialchars($p['aluno_nome']) ?></td>
                            <?php endif; ?>
                            <?php if($user_tipo == 'fornecedor'): ?>
                                <td><?= htmlspecialchars($p['escola_nome']) ?></td>
                            <?php endif; ?>
                            <?php if($user_tipo == 'gestor'): ?>
                                <td><?= htmlspecialchars($p['responsavel_nome']) ?></td>
                            <?php endif; ?>
                            <td>R$ <?= number_format($p['total'], 2, ',', '.') ?></td>
                            <td><?= $status_labels[$p['status']] ?? $p['status'] ?></td>
                            <td><?= date('d/m/Y H:i', strtotime($p['criado_em'])) ?></td>
                            <td>
                                <a href="/pedidos-gerenciar?id=<?= $p['id'] ?>">Ver Detalhes</a>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <p>Nenhum pedido encontrado.</p>
        <?php endif; ?>
    <?php endif; ?>
</body>
</html>
