<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Responsável - Conecta Uniforme</title>
</head>
<body>
    <h1>Dashboard - Responsável</h1>
    <p>Bem-vindo, <?= htmlspecialchars($_SESSION['user_nome']) ?>!</p>
    
    <nav>
        <a href="/conecta-uniforme/dashboard-responsavel">Dashboard</a> |
        <a href="/conecta-uniforme/catalogo-novo">Catálogo de Uniformes</a> |
        <a href="/conecta-uniforme/carrinho-novo">Meu Carrinho (<?= $total_carrinho ?>)</a> |
        <a href="/conecta-uniforme/pedidos-gerenciar">Meus Pedidos</a> |
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
    
    <h2>Dados do Aluno</h2>
    <ul>
        <li><strong>Nome:</strong> <?= htmlspecialchars($aluno['nome']) ?></li>
        <li><strong>Matrícula:</strong> <?= htmlspecialchars($aluno['matricula']) ?></li>
        <li><strong>Escola:</strong> <?= htmlspecialchars($aluno['escola_nome']) ?></li>
        <li><strong>Série:</strong> <?= htmlspecialchars($aluno['serie']) ?></li>
        <li><strong>Gênero:</strong> <?= htmlspecialchars($aluno['genero']) ?></li>
    </ul>
    
    <h2>Resumo</h2>
    <ul>
        <li>Itens no Carrinho: <?= $total_carrinho ?></li>
        <li>Total de Pedidos: <?= $total_pedidos ?></li>
    </ul>
    
    <h2>Ações Rápidas</h2>
    <p>
        <a href="/conecta-uniforme/catalogo-novo" style="padding: 10px 15px; background: #007bff; color: white; text-decoration: none; display: inline-block;">
            Ver Catálogo de Uniformes
        </a>
    </p>
    
    <?php if($total_carrinho > 0): ?>
        <p>
            <a href="/conecta-uniforme/carrinho-novo" style="padding: 10px 15px; background: #28a745; color: white; text-decoration: none; display: inline-block;">
                Ver Carrinho (<?= $total_carrinho ?> itens)
            </a>
        </p>
    <?php endif; ?>
    
    <h2>Meus Pedidos Recentes</h2>
    <?php if(count($meus_pedidos) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Data</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach(array_slice($meus_pedidos, 0, 5) as $pedido): ?>
                    <tr>
                        <td><?= $pedido['id'] ?></td>
                        <td><?= date('d/m/Y H:i', strtotime($pedido['criado_em'])) ?></td>
                        <td>R$ <?= number_format($pedido['total'], 2, ',', '.') ?></td>
                        <td><?= htmlspecialchars($pedido['status']) ?></td>
                        <td>
                            <a href="/conecta-uniforme/pedidos-gerenciar?id=<?= $pedido['id'] ?>">Ver Detalhes</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        <?php if(count($meus_pedidos) > 5): ?>
            <p><a href="/conecta-uniforme/pedidos-gerenciar">Ver todos os pedidos</a></p>
        <?php endif; ?>
    <?php else: ?>
        <p>Você ainda não realizou nenhum pedido.</p>
        <p><a href="/conecta-uniforme/catalogo-novo">Começar a comprar</a></p>
    <?php endif; ?>
</body>
</html>
