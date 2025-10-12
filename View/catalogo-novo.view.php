<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo - Conecta Uniforme</title>
</head>
<body>
    <h1>Catálogo de Uniformes</h1>
    <p>Olá, <?= htmlspecialchars($_SESSION['user_nome']) ?>! | Aluno: <?= htmlspecialchars($aluno['nome']) ?></p>
    
    <nav>
        <a href="/dashboard-responsavel">Dashboard</a> |
        <a href="/catalogo-novo">Catálogo</a> |
        <a href="/carrinho-novo">Carrinho (<?= $total_carrinho ?>)</a> |
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
    
    <?php if(!$produto_selecionado): ?>
        <h2>Uniformes Disponíveis</h2>
        <p>Exibindo uniformes para: <?= htmlspecialchars($aluno['serie']) ?> - <?= htmlspecialchars($aluno['genero']) ?></p>
        
        <?php if(count($produtos) > 0): ?>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
                <?php foreach($produtos as $produto): ?>
                    <div style="border: 1px solid #ccc; padding: 10px;">
                        <h3><?= htmlspecialchars($produto['nome']) ?></h3>
                        <p><strong>Fornecedor:</strong> <?= htmlspecialchars($produto['Fornecedor_nome']) ?></p>
                        <p><strong>Preço:</strong> R$ <?= number_format($produto['preco'], 2, ',', '.') ?></p>
                        <p>
                            <a href="/catalogo-novo?produto_id=<?= $produto['id'] ?>">Ver Detalhes</a>
                        </p>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php else: ?>
            <p>Nenhum uniforme disponível no momento para sua série e gênero.</p>
        <?php endif; ?>
        
    <?php else: ?>
        <h2><?= htmlspecialchars($produto_selecionado['nome']) ?></h2>
        <p><a href="/catalogo-novo">← Voltar ao catálogo</a></p>
        
        <div style="display: flex; gap: 20px;">
            <div style="flex: 1;">
                <h3>Fotos</h3>
                <?php if(count($fotos) > 0): ?>
                    <?php foreach($fotos as $foto): ?>
                        <div style="margin-bottom: 10px;">
                            <img src="<?= htmlspecialchars($foto['caminho_foto']) ?>" alt="Foto do produto" style="max-width: 100%; height: auto; border: 1px solid #ccc;">
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <p>Sem fotos disponíveis</p>
                <?php endif; ?>
            </div>
            
            <div style="flex: 1;">
                <h3>Informações</h3>
                <p><strong>Fornecedor:</strong> <?= htmlspecialchars($produto_selecionado['Fornecedor_nome']) ?></p>
                <p><strong>Preço:</strong> R$ <?= number_format($produto_selecionado['preco'], 2, ',', '.') ?></p>
                <p><strong>Descrição:</strong></p>
                <p><?= nl2br(htmlspecialchars($produto_selecionado['descricao'])) ?></p>
                
                <h3>Adicionar ao Carrinho</h3>
                <form method="POST">
                    <input type="hidden" name="produto_id" value="<?= $produto_selecionado['id'] ?>">
                    
                    <?php if(count($variacoes) > 0): ?>
                        <label>Selecione a variação:</label><br>
                        <select name="variacao_id" required style="width: 100%; padding: 5px; margin-bottom: 10px;">
                            <option value="">Selecione...</option>
                            <?php foreach($variacoes as $variacao): ?>
                                <option value="<?= $variacao['id'] ?>">
                                    Tamanho: <?= htmlspecialchars($variacao['tamanho']) ?>
                                    <?php if($variacao['cor']): ?>
                                        - Cor: <?= htmlspecialchars($variacao['cor']) ?>
                                    <?php endif; ?>
                                    (<?= htmlspecialchars($variacao['genero']) ?>)
                                    - Estoque: <?= $variacao['quantidade_estoque'] ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                        <br>
                        
                        <label>Quantidade:</label><br>
                        <input type="number" name="quantidade" value="1" min="1" required style="width: 100px; padding: 5px;">
                        <br><br>
                        
                        <button type="submit" name="adicionar_carrinho" style="padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer;">
                            Adicionar ao Carrinho
                        </button>
                    <?php else: ?>
                        <p style="color: red;">Produto sem variações disponíveis.</p>
                    <?php endif; ?>
                </form>
            </div>
        </div>
    <?php endif; ?>
</body>
</html>
