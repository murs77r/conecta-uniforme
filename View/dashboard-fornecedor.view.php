<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Fornecedor - Conecta Uniforme</title>
</head>
<body>
    <h1>Dashboard - Fornecedor</h1>
    <p>Bem-vindo, <?= htmlspecialchars($_SESSION['user_nome']) ?>!</p>
    
    <nav>
        <a href="/conecta-uniforme/dashboard-fornecedor">Dashboard</a> |
        <a href="/conecta-uniforme/produtos-fornecedor">Meus Produtos</a> |
        <a href="/conecta-uniforme/pedidos-gerenciar">Pedidos</a> |
        <a href="/conecta-uniforme/comissoes-relatorio">Relatórios Financeiros</a> |
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
    
    <h2>Resumo</h2>
    <ul>
        <li>Total de Produtos: <?= $total_produtos ?></li>
        <li>Pedidos Recebidos: <?= $total_pedidos ?></li>
        <li>Pedidos Pendentes: <?= $pedidos_pendentes ?></li>
    </ul>
    
    <h2>Pedidos Recentes</h2>
    <?php if(count($pedidos) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Escola</th>
                    <th>Aluno</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Data</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach(array_slice($pedidos, 0, 10) as $pedido): ?>
                    <tr>
                        <td><?= $pedido['id'] ?></td>
                        <td><?= htmlspecialchars($pedido['escola_nome']) ?></td>
                        <td><?= htmlspecialchars($pedido['aluno_nome']) ?></td>
                        <td>R$ <?= number_format($pedido['total'], 2, ',', '.') ?></td>
                        <td><?= htmlspecialchars($pedido['status']) ?></td>
                        <td><?= date('d/m/Y H:i', strtotime($pedido['criado_em'])) ?></td>
                        <td>
                            <a href="/conecta-uniforme/pedidos-gerenciar?id=<?= $pedido['id'] ?>">Ver/Atualizar</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum pedido recebido ainda.</p>
    <?php endif; ?>
    
    <h2>Meus Produtos</h2>
    <p><a href="/conecta-uniforme/produtos-fornecedor">Gerenciar Produtos</a> | 
       <a href="/conecta-uniforme/produtos-fornecedor?novo=1">Adicionar Novo Produto</a></p>
    
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
                <?php foreach(array_slice($produtos, 0, 5) as $produto): ?>
                    <tr>
                        <td><?= $produto['id'] ?></td>
                        <td><?= htmlspecialchars($produto['nome']) ?></td>
                        <td>R$ <?= number_format($produto['preco'], 2, ',', '.') ?></td>
                        <td><?= $produto['total_variacoes'] ?></td>
                        <td><?= $produto['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                        <td>
                            <a href="/conecta-uniforme/produtos-fornecedor?editar=<?= $produto['id'] ?>">Editar</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Você ainda não cadastrou produtos.</p>
    <?php endif; ?>
    
    <h2>Relatórios Financeiros</h2>
    <?php if(count($comissoes) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Mês/Ano</th>
                    <th>Total Vendas</th>
                    <th>Comissão (15%)</th>
                    <th>Valor Líquido</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach(array_slice($comissoes, 0, 6) as $comissao): ?>
                    <tr>
                        <td><?= date('m/Y', strtotime($comissao['mes_referencia'])) ?></td>
                        <td>R$ <?= number_format($comissao['total_vendas'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($comissao['total_comissao'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($comissao['valor_liquido'], 2, ',', '.') ?></td>
                        <td><?= $comissao['status'] == 'pago' ? 'Pago' : 'Pendente' ?></td>
                        <td>
                            <a href="/conecta-uniforme/comissoes-relatorio?mes=<?= $comissao['mes_referencia'] ?>">Ver Detalhes</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum relatório disponível ainda.</p>
    <?php endif; ?>
</body>
</html>
