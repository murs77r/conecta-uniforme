<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel do Administrador - Conecta Uniforme</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        nav a { margin-right: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        table th, table td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        fieldset { border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; }
        legend { font-weight: bold; }
        input[type="text"], input[type="email"], select { padding: 5px; width: 100%; max-width: 320px; }
        .inline-form { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
        .inline-form input { flex: 1 1 180px; }
        .acoes button { margin-right: 5px; }
        .mensagem { color: #0a7a0a; border: 1px solid #0a7a0a; padding: 10px; margin-bottom: 15px; background: #f0fff0; }
        .erro { color: #a00; border: 1px solid #a00; padding: 10px; margin-bottom: 15px; background: #fff0f0; }
    </style>
</head>
<body>
    <h1>Painel do Administrador</h1>
    <p>Bem-vindo, <?= htmlspecialchars($_SESSION['user_nome']) ?>!</p>

    <nav>
        <a href="/dashboard-administrador">Início</a> |
        <a href="/logout">Sair</a>
    </nav>

    <hr>

    <?php if($mensagem): ?>
        <div class="mensagem"><?= htmlspecialchars($mensagem) ?></div>
    <?php endif; ?>

    <?php if($erro): ?>
        <div class="erro"><?= htmlspecialchars($erro) ?></div>
    <?php endif; ?>

    <section>
        <h2>Gerenciar Fornecedores</h2>
        <fieldset>
            <legend>Novo fornecedor</legend>
            <form method="POST" class="inline-form">
                <input type="text" name="nome" placeholder="Nome" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="text" name="telefone" placeholder="Telefone">
                <input type="text" name="cnpj" placeholder="CNPJ">
                <button type="submit" name="criar_fornecedor">Cadastrar fornecedor</button>
            </form>
        </fieldset>

        <h3>Fornecedores cadastrados (<?= count($fornecedores) ?>)</h3>
        <?php if(count($fornecedores) > 0): ?>
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Telefone</th>
                        <th>CNPJ</th>
                        <th>Status</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($fornecedores as $Fornecedor): ?>
                        <tr>
                            <td colspan="6">
                                <form method="POST" class="inline-form acoes">
                                    <input type="hidden" name="Fornecedor_id" value="<?= (int)$Fornecedor['id'] ?>">
                                    <input type="text" name="nome" value="<?= htmlspecialchars($Fornecedor['nome']) ?>" required>
                                    <input type="email" name="email" value="<?= htmlspecialchars($Fornecedor['email']) ?>" required>
                                    <input type="text" name="telefone" value="<?= htmlspecialchars($Fornecedor['telefone'] ?? '') ?>">
                                    <input type="text" name="cnpj" value="<?= htmlspecialchars($Fornecedor['cnpj'] ?? '') ?>">
                                    <span>Status: <?= $Fornecedor['ativo'] ? 'Ativo' : 'Inativo' ?></span>
                                    <button type="submit" name="atualizar_fornecedor">Salvar alterações</button>
                                    <button type="submit" name="excluir_fornecedor" value="1" onclick="return confirm('Deseja excluir este fornecedor? Essa ação é irreversível.');">Excluir</button>
                                </form>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <p>Nenhum fornecedor cadastrado.</p>
        <?php endif; ?>
    </section>

    <hr>

    <section>
        <h2>Gerenciar Escolas</h2>
        <fieldset>
            <legend>Nova escola</legend>
            <form method="POST" class="inline-form">
                <input type="text" name="nome" placeholder="Nome" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="text" name="cnpj" placeholder="CNPJ" required>
                <input type="text" name="telefone" placeholder="Telefone">
                <input type="text" name="cep" placeholder="CEP">
                <input type="text" name="estado" placeholder="Estado (UF)" maxlength="2">
                <input type="text" name="cidade" placeholder="Cidade">
                <input type="text" name="endereco" placeholder="Endereço">
                <input type="text" name="complemento" placeholder="Complemento">
                <button type="submit" name="criar_escola">Cadastrar escola</button>
            </form>
        </fieldset>

        <h3>Escolas cadastradas (<?= count($escolas) ?>)</h3>
        <?php if(count($escolas) > 0): ?>
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>CNPJ</th>
                        <th>Cidade/UF</th>
                        <th>Telefone</th>
                        <th>Status</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($escolas as $escola): ?>
                        <tr>
                            <td colspan="7">
                                <form method="POST" class="inline-form acoes">
                                    <input type="hidden" name="escola_id" value="<?= (int)$escola['id'] ?>">
                                    <input type="text" name="nome" value="<?= htmlspecialchars($escola['nome']) ?>" required>
                                    <input type="email" name="email" value="<?= htmlspecialchars($escola['email']) ?>" required>
                                    <input type="text" name="cnpj" value="<?= htmlspecialchars($escola['cnpj']) ?>" required>
                                    <input type="text" name="telefone" value="<?= htmlspecialchars($escola['telefone'] ?? '') ?>">
                                    <input type="text" name="cep" value="<?= htmlspecialchars($escola['cep'] ?? '') ?>">
                                    <input type="text" name="estado" value="<?= htmlspecialchars($escola['estado'] ?? '') ?>" maxlength="2">
                                    <input type="text" name="cidade" value="<?= htmlspecialchars($escola['cidade'] ?? '') ?>">
                                    <input type="text" name="endereco" value="<?= htmlspecialchars($escola['endereco'] ?? '') ?>">
                                    <input type="text" name="complemento" value="<?= htmlspecialchars($escola['complemento'] ?? '') ?>">
                                    <span>Status: <?= $escola['ativo'] ? 'Ativa' : 'Inativa' ?></span>
                                    <button type="submit" name="atualizar_escola">Salvar alterações</button>
                                    <button type="submit" name="excluir_escola" value="1" onclick="return confirm('Deseja excluir esta escola? Todos os dados relacionados serão removidos.');">Excluir</button>
                                </form>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <p>Nenhuma escola cadastrada.</p>
        <?php endif; ?>
    </section>

    <hr>

    <section>
        <h2>Alunos cadastrados (visualização)</h2>
        <p>Total de alunos: <?= count($alunos) ?></p>
        <?php if(count($alunos) > 0): ?>
            <table>
                <thead>
                    <tr>
                        <th>Matrícula</th>
                        <th>Nome</th>
                        <th>Série</th>
                        <th>Gênero</th>
                        <th>Escola</th>
                        <th>Responsáveis</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($alunos as $aluno): ?>
                        <tr>
                            <td><?= htmlspecialchars($aluno['matricula']) ?></td>
                            <td><?= htmlspecialchars($aluno['nome']) ?></td>
                            <td><?= htmlspecialchars($aluno['serie']) ?></td>
                            <td><?= htmlspecialchars($aluno['genero']) ?></td>
                            <td><?= htmlspecialchars($aluno['escola_nome']) ?></td>
                            <td><?= (int)$aluno['total_responsaveis'] ?></td>
                            <td><?= $aluno['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <p>Nenhum aluno cadastrado.</p>
        <?php endif; ?>
    </section>
</body>
</html>
