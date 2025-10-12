<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Fornecedores - Conecta Uniforme</title>
</head>
<body>
    <h1>Gestão de Fornecedores</h1>
    <p>Bem-vindo, <?= htmlspecialchars($_SESSION['user_nome'] ?? 'Gestor') ?>!</p>

    <nav>
        <a href="/dashboard-gestor">Dashboard</a> |
        <a href="/alunos-gestor">Gerenciar Alunos</a> |
        <a href="/fornecedores-gestor">Gerenciar Fornecedores</a> |
        <a href="/pedidos-gerenciar">Ver Pedidos</a> |
        <a href="/comissoes-relatorio">Relatórios de Comissão</a> |
        <a href="/logout">Sair</a>
    </nav>

    <hr>

    <?php if (!empty($mensagem)): ?>
        <div style="color: green; border: 1px solid green; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($mensagem) ?>
        </div>
    <?php endif; ?>

    <?php if (!empty($erro)): ?>
        <div style="color: red; border: 1px solid red; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($erro) ?>
        </div>
    <?php endif; ?>

    <section>
        <h2>Fornecedores Homologados</h2>
        <?php if (count($fornecedoresHomologados) > 0): ?>
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
                    <?php foreach ($fornecedoresHomologados as $fornecedor): ?>
                        <tr>
                            <td><?= htmlspecialchars($fornecedor['nome']) ?></td>
                            <td><?= htmlspecialchars($fornecedor['email']) ?></td>
                            <td><?= htmlspecialchars($fornecedor['cnpj']) ?></td>
                            <td><?= $fornecedor['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                            <td><?= isset($fornecedor['data_homologacao']) ? date('d/m/Y', strtotime($fornecedor['data_homologacao'])) : '-' ?></td>
                            <td>
                                <?php if ($fornecedor['ativo']): ?>
                                    <form method="POST" style="display: inline;">
                                        <input type="hidden" name="Fornecedor_id" value="<?= (int)$fornecedor['id'] ?>">
                                        <button type="submit" name="desabilitar_Fornecedor">Desabilitar</button>
                                    </form>
                                <?php else: ?>
                                    <form method="POST" style="display: inline;">
                                        <input type="hidden" name="Fornecedor_id" value="<?= (int)$fornecedor['id'] ?>">
                                        <button type="submit" name="habilitar_Fornecedor">Reabilitar</button>
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
    </section>

    <section style="margin-top: 2rem;">
        <h2>Habilitar novo fornecedor</h2>
        <?php if (count($fornecedoresDisponiveis) > 0): ?>
            <form method="POST">
                <label for="Fornecedor_id">Selecione o fornecedor:</label><br>
                <select id="Fornecedor_id" name="Fornecedor_id" required style="padding: 5px; width: 300px;">
                    <option value="">Selecione...</option>
                    <?php foreach ($fornecedoresDisponiveis as $fornecedor): ?>
                        <option value="<?= (int)$fornecedor['id'] ?>">
                            <?= htmlspecialchars($fornecedor['nome']) ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <br><br>
                <button type="submit" name="habilitar_Fornecedor">Habilitar Fornecedor</button>
            </form>
        <?php else: ?>
            <p>Todos os fornecedores ativos já estão vinculados à sua escola.</p>
        <?php endif; ?>
    </section>
</body>
</html>
