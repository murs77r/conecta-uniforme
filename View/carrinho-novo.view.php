<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carrinho - Conecta Uniforme</title>
</head>
<body>
    <h1>Meu Carrinho</h1>
    <p>Olá, <?= htmlspecialchars($_SESSION['user_nome']) ?>!</p>
    
    <nav>
        <a href="/dashboard-responsavel">Dashboard</a> |
        <a href="/catalogo-novo">Continuar Comprando</a> |
        <a href="/carrinho-novo">Carrinho</a> |
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
    
    <?php if(count($itens) > 0): ?>
        <h2>Itens no Carrinho (<?= $total_itens ?>)</h2>
        
        <table border="1" cellpadding="10" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Fornecedor</th>
                    <th>Variação</th>
                    <th>Preço Unit.</th>
                    <th>Quantidade</th>
                    <th>Subtotal</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($itens as $item): ?>
                    <tr>
                        <td><?= htmlspecialchars($item['produto_nome']) ?></td>
                        <td><?= htmlspecialchars($item['Fornecedor_nome']) ?></td>
                        <td>
                            Tamanho: <?= htmlspecialchars($item['tamanho']) ?><br>
                            <?php if($item['cor']): ?>
                                Cor: <?= htmlspecialchars($item['cor']) ?><br>
                            <?php endif; ?>
                            Gênero: <?= htmlspecialchars($item['genero']) ?>
                        </td>
                        <td>R$ <?= number_format($item['preco'], 2, ',', '.') ?></td>
                        <td>
                            <form method="POST" style="display: inline;">
                                <input type="hidden" name="item_id" value="<?= $item['id'] ?>">
                                <input type="number" name="quantidade" value="<?= $item['quantidade'] ?>" 
                                       min="1" max="<?= $item['quantidade_estoque'] ?>" 
                                       style="width: 60px; padding: 2px;">
                                <button type="submit" name="atualizar_quantidade" style="padding: 2px 5px;">Atualizar</button>
                            </form>
                        </td>
                        <td>R$ <?= number_format($item['subtotal'], 2, ',', '.') ?></td>
                        <td>
                            <form method="POST" style="display: inline;">
                                <input type="hidden" name="item_id" value="<?= $item['id'] ?>">
                                <button type="submit" name="remover_item" style="color: red;">Remover</button>
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="5" style="text-align: right;"><strong>Total:</strong></td>
                    <td colspan="2"><strong>R$ <?= number_format($total, 2, ',', '.') ?></strong></td>
                </tr>
            </tfoot>
        </table>
        
        <div style="margin-top: 20px;">
            <h3>Informações de Retirada</h3>
            <p><strong>Modalidade:</strong> Clique e Retire na Escola</p>
            <p><strong>Local de Retirada:</strong> <?= htmlspecialchars($aluno['escola_nome'] ?? 'Sua escola') ?></p>
            <p><strong>Observação:</strong> Você será notificado quando os produtos estiverem prontos para retirada.</p>
        </div>
        
        <form method="POST" style="margin-top: 20px;">
            <button type="submit" name="finalizar_pedido" 
                    style="padding: 15px 30px; background: #28a745; color: white; border: none; cursor: pointer; font-size: 16px;">
                Finalizar Pedido
            </button>
        </form>
        
    <?php else: ?>
        <p>Seu carrinho está vazio.</p>
        <p><a href="/catalogo-novo">Ver produtos disponíveis</a></p>
    <?php endif; ?>
</body>
</html>
