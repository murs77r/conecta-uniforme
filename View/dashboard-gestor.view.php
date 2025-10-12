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
        <a href="/conecta-uniforme/dashboard-gestor">Dashboard</a> |
        <a href="/conecta-uniforme/alunos-gestor">Gerenciar Alunos</a> |
        <a href="/conecta-uniforme/fornecedores-gestor">Gerenciar Fornecedores</a> |
        <a href="/conecta-uniforme/pedidos-gerenciar">Ver Pedidos</a> |
        <a href="/conecta-uniforme/comissoes-relatorio">Relatórios de Comissão</a> |
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
        <li>Total de Alunos: <?= $total_alunos ?></li>
        <li>Fornecedores Homologados: <?= $total_fornecedores ?></li>
        <li>Total de Pedidos: <?= $total_pedidos ?></li>
    </ul>
    
    <h2>Fornecedores Homologados</h2>
    <?php if(count($fornecedores_homologados) > 0): ?>
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
                <?php foreach($fornecedores_homologados as $fornecedor): ?>
                    <tr>
                        <td><?= htmlspecialchars($fornecedor['nome']) ?></td>
                        <td><?= htmlspecialchars($fornecedor['email']) ?></td>
                        <td><?= htmlspecialchars($fornecedor['cnpj']) ?></td>
                        <td><?= $fornecedor['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                        <td><?= date('d/m/Y', strtotime($fornecedor['data_homologacao'])) ?></td>
                        <td>
                            <?php if($fornecedor['ativo']): ?>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="fornecedor_id" value="<?= $fornecedor['id'] ?>">
                                    <button type="submit" name="desabilitar_fornecedor">Desabilitar</button>
                                </form>
                            <?php else: ?>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="fornecedor_id" value="<?= $fornecedor['id'] ?>">
                                    <button type="submit" name="habilitar_fornecedor">Habilitar</button>
                                </form>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum fornecedor homologado ainda.</p>
    <?php endif; ?>
    
    <h2>Adicionar Fornecedor</h2>
    <?php if(count($fornecedores_disponiveis) > 0): ?>
        <form method="POST">
            <label>Selecione o fornecedor:</label><br>
            <select name="fornecedor_id" required style="padding: 5px; width: 300px;">
                <option value="">Selecione...</option>
                <?php foreach($fornecedores_disponiveis as $fornecedor): ?>
                    <option value="<?= $fornecedor['id'] ?>">
                        <?= htmlspecialchars($fornecedor['nome']) ?>
                    </option>
                <?php endforeach; ?>
            </select>
            <br><br>
            <button type="submit" name="habilitar_fornecedor">Habilitar Fornecedor</button>
        </form>
    <?php else: ?>
        <p>Todos os fornecedores cadastrados já estão vinculados à sua escola.</p>
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
                        <td><?= htmlspecialchars($pedido['responsavel_nome']) ?></td>
                        <td>R$ <?= number_format($pedido['total'], 2, ',', '.') ?></td>
                        <td><?= htmlspecialchars($pedido['status']) ?></td>
                        <td><?= date('d/m/Y H:i', strtotime($pedido['criado_em'])) ?></td>
                        <td>
                            <a href="/conecta-uniforme/pedidos-gerenciar?id=<?= $pedido['id'] ?>">Ver Detalhes</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        <?php if(count($pedidos) > 10): ?>
            <p><a href="/conecta-uniforme/pedidos-gerenciar">Ver todos os pedidos</a></p>
        <?php endif; ?>
    <?php else: ?>
        <p>Nenhum pedido realizado ainda.</p>
    <?php endif; ?>
</body>
</html>
