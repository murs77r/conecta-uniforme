<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Meus Produtos - Conecta Uniforme</title>
</head>
<body>
    <h1>Gerenciar Produtos</h1>
    <p>Fornecedor: <?= htmlspecialchars($_SESSION['user_nome']) ?></p>
    
    <nav>
        <a href="/conecta-uniforme/dashboard-fornecedor">Dashboard</a> |
        <a href="/conecta-uniforme/produtos-fornecedor">Produtos</a> |
        <a href="/conecta-uniforme/pedidos-gerenciar">Pedidos</a> |
        <a href="/conecta-uniforme/logout">Sair</a>
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
    
    <?php if(isset($_GET['novo']) || $produto_editando): ?>
        <h2><?= $produto_editando ? 'Editar Produto' : 'Novo Produto' ?></h2>
        
        <form method="POST">
            <?php if($produto_editando): ?>
                <input type="hidden" name="produto_id" value="<?= $produto_editando['id'] ?>">
            <?php endif; ?>
            
            <label>Nome do Produto:</label><br>
            <input type="text" name="nome" required value="<?= htmlspecialchars($produto_editando['nome'] ?? '') ?>" style="width: 400px; padding: 5px;"><br><br>
            
            <label>Descrição:</label><br>
            <textarea name="descricao" rows="5" style="width: 400px; padding: 5px;"><?= htmlspecialchars($produto_editando['descricao'] ?? '') ?></textarea><br><br>
            
            <label>Preço (R$):</label><br>
            <input type="number" name="preco" step="0.01" required value="<?= $produto_editando['preco'] ?? '' ?>" style="width: 150px; padding: 5px;"><br><br>
            
            <?php if(!$produto_editando): ?>
                <h3>Homologação (Escolas/Séries)</h3>
                <p>Selecione as escolas e séries para as quais este produto está homologado:</p>
                <?php foreach($escolas_disponiveis as $escola): ?>
                    <div style="margin-bottom: 10px;">
                        <strong><?= htmlspecialchars($escola['nome']) ?></strong><br>
                        <input type="checkbox" name="escolas[]" value="<?= $escola['id'] ?>|1º Ano"> 1º Ano
                        <input type="checkbox" name="escolas[]" value="<?= $escola['id'] ?>|2º Ano"> 2º Ano
                        <input type="checkbox" name="escolas[]" value="<?= $escola['id'] ?>|3º Ano"> 3º Ano
                        <input type="checkbox" name="escolas[]" value="<?= $escola['id'] ?>|4º Ano"> 4º Ano
                        <input type="checkbox" name="escolas[]" value="<?= $escola['id'] ?>|5º Ano"> 5º Ano
                    </div>
                <?php endforeach; ?>
                <br>
            <?php endif; ?>
            
            <button type="submit" name="<?= $produto_editando ? 'atualizar_produto' : 'criar_produto' ?>" style="padding: 10px 20px;">
                <?= $produto_editando ? 'Atualizar Produto' : 'Criar Produto' ?>
            </button>
            
            <a href="/conecta-uniforme/produtos-fornecedor" style="margin-left: 10px;">Cancelar</a>
        </form>
        
        <?php if($produto_editando): ?>
            <hr>
            <h3>Variações do Produto</h3>
            
            <h4>Adicionar Nova Variação</h4>
            <form method="POST">
                <input type="hidden" name="produto_id" value="<?= $produto_editando['id'] ?>">
                
                <label>Tamanho:</label>
                <input type="text" name="tamanho" required placeholder="Ex: P, M, G, 10, 12" style="padding: 5px;">
                
                <label>Cor:</label>
                <input type="text" name="cor" placeholder="Ex: Azul, Branco" style="padding: 5px;">
                
                <label>Gênero:</label>
                <select name="genero" required style="padding: 5px;">
                    <option value="masculino">Masculino</option>
                    <option value="feminino">Feminino</option>
                    <option value="unissex">Unissex</option>
                </select>
                
                <label>Quantidade em Estoque:</label>
                <input type="number" name="quantidade" value="0" min="0" style="width: 80px; padding: 5px;">
                
                <button type="submit" name="adicionar_variacao">Adicionar Variação</button>
            </form>
            
            <?php if(count($variacoes) > 0): ?>
                <h4>Variações Existentes</h4>
                <table border="1" cellpadding="5" cellspacing="0">
                    <thead>
                        <tr>
                            <th>Tamanho</th>
                            <th>Cor</th>
                            <th>Gênero</th>
                            <th>Estoque</th>
                            <th>Atualizar Estoque</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach($variacoes as $variacao): ?>
                            <tr>
                                <td><?= htmlspecialchars($variacao['tamanho']) ?></td>
                                <td><?= htmlspecialchars($variacao['cor']) ?></td>
                                <td><?= htmlspecialchars($variacao['genero']) ?></td>
                                <td><?= $variacao['quantidade_estoque'] ?></td>
                                <td>
                                    <form method="POST" style="display: inline;">
                                        <input type="hidden" name="variacao_id" value="<?= $variacao['id'] ?>">
                                        <input type="number" name="quantidade" value="<?= $variacao['quantidade_estoque'] ?>" min="0" style="width: 70px; padding: 2px;">
                                        <button type="submit" name="atualizar_estoque">Atualizar</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        <?php endif; ?>
        
    <?php else: ?>
        <h2>Meus Produtos</h2>
        <p><a href="/conecta-uniforme/produtos-fornecedor?novo=1" style="padding: 10px 15px; background: #007bff; color: white; text-decoration: none; display: inline-block;">Adicionar Novo Produto</a></p>
        
        <?php if(count($produtos) > 0): ?>
            <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome</th>
                        <th>Preço</th>
                        <th>Variações</th>
                        <th>Status</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($produtos as $produto): ?>
                        <tr>
                            <td><?= $produto['id'] ?></td>
                            <td><?= htmlspecialchars($produto['nome']) ?></td>
                            <td>R$ <?= number_format($produto['preco'], 2, ',', '.') ?></td>
                            <td><?= $produto['total_variacoes'] ?></td>
                            <td><?= $produto['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                            <td>
                                <a href="/conecta-uniforme/produtos-fornecedor?editar=<?= $produto['id'] ?>">Editar</a> |
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="produto_id" value="<?= $produto['id'] ?>">
                                    <input type="hidden" name="status" value="<?= $produto['ativo'] ? 0 : 1 ?>">
                                    <button type="submit" name="toggle_produto" style="color: <?= $produto['ativo'] ? 'red' : 'green' ?>;">
                                        <?= $produto['ativo'] ? 'Desativar' : 'Ativar' ?>
                                    </button>
                                </form>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <p>Você ainda não cadastrou produtos.</p>
        <?php endif; ?>
    <?php endif; ?>
</body>
</html>
