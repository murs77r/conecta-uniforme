<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Gestor - Conecta Uniforme</title>
</head>
<body>
    <h1>Dashboard - Gestor Escolar</h1>
    <p>Bem-vindo, <?= htmlspecialchars($_SESSION['user_nome']) ?>!</p>
    
    <nav>
        <a href="/dashboard-gestor">Dashboard</a> |
    <a href="/alunos-gestor">Gerenciar Alunos</a> |
        <a href="/fornecedores-gestor">Gerenciar Fornecedores</a> |
        <a href="/pedidos-gerenciar">Ver Pedidos</a> |
        <a href="/comissoes-relatorio">Relatórios de Comissão</a> |
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
    
    <h2>Resumo</h2>
    <ul>
        <li>Total de Alunos: <?= $total_alunos ?></li>
        <li>Fornecedores Homologados: <?= $total_Fornecedores ?></li>
        <li>Total de Pedidos: <?= $total_pedidos ?></li>
    </ul>
    
    <h2>Fornecedores Homologados</h2>
    <?php if(count($Fornecedores_homologados) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Email</th>
                    <th>CNPJ</th>
                    <th>Status</th>
                    <th>Data Homologação</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($Fornecedores_homologados as $Fornecedor): ?>
                    <tr>
                        <td><?= htmlspecialchars($Fornecedor['nome']) ?></td>
                        <td><?= htmlspecialchars($Fornecedor['email']) ?></td>
                        <td><?= htmlspecialchars($Fornecedor['cnpj']) ?></td>
                        <td><?= $Fornecedor['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                        <td><?= date('d/m/Y', strtotime($Fornecedor['data_homologacao'])) ?></td>
                        <td>
                            <?php if($Fornecedor['ativo']): ?>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="Fornecedor_id" value="<?= $Fornecedor['id'] ?>">
                                    <button type="submit" name="desabilitar_Fornecedor">Desabilitar</button>
                                </form>
                            <?php else: ?>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="Fornecedor_id" value="<?= $Fornecedor['id'] ?>">
                                    <button type="submit" name="habilitar_Fornecedor">Habilitar</button>
                                </form>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum Fornecedor homologado ainda.</p>
    <?php endif; ?>
    
    <h2>Adicionar Fornecedor</h2>
    <?php if(count($Fornecedores_disponiveis) > 0): ?>
        <form method="POST">
            <label>Selecione o Fornecedor:</label><br>
            <select name="Fornecedor_id" required style="padding: 5px; width: 300px;">
                <option value="">Selecione...</option>
                <?php foreach($Fornecedores_disponiveis as $Fornecedor): ?>
                    <option value="<?= $Fornecedor['id'] ?>">
                        <?= htmlspecialchars($Fornecedor['nome']) ?>
                    </option>
                <?php endforeach; ?>
            </select>
            <br><br>
            <button type="submit" name="habilitar_Fornecedor">Habilitar Fornecedor</button>
        </form>
    <?php else: ?>
        <p>Todos os Fornecedores cadastrados já estão vinculados à sua escola.</p>
    <?php endif; ?>
    
    <h2>Últimos Pedidos</h2>
    <?php if(count($pedidos) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Aluno</th>
                    <th>Responsável</th>
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
                        <td><?= htmlspecialchars($pedido['aluno_nome']) ?></td>
                        <td><?= htmlspecialchars($pedido['Responsável_nome']) ?></td>
                        <td>R$ <?= number_format($pedido['total'], 2, ',', '.') ?></td>
                        <td><?= htmlspecialchars($pedido['status']) ?></td>
                        <td><?= date('d/m/Y H:i', strtotime($pedido['criado_em'])) ?></td>
                        <td>
                            <a href="/pedidos-gerenciar?id=<?= $pedido['id'] ?>">Ver Detalhes</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        <?php if(count($pedidos) > 10): ?>
            <p><a href="/pedidos-gerenciar">Ver todos os pedidos</a></p>
        <?php endif; ?>
    <?php else: ?>
        <p>Nenhum pedido realizado ainda.</p>
    <?php endif; ?>
</body>
</html>
