<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gerenciar Alunos - Conecta Uniforme</title>
</head>
<body>
    <h1>Gerenciar Alunos</h1>
    <p>Gestor: <?= htmlspecialchars($_SESSION['user_nome']) ?></p>
    
    <nav>
        <a href="/dashboard-gestor">Dashboard</a> |
    <a href="/alunos-gestor">Alunos</a> |
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
    
    <h2><?= $aluno_editando ? 'Editar Aluno' : 'Adicionar Novo Aluno' ?></h2>
    
    <form method="POST">
        <?php if($aluno_editando): ?>
            <input type="hidden" name="aluno_id" value="<?= $aluno_editando['id'] ?>">
        <?php endif; ?>
        
        <label>Nome do Aluno:</label><br>
        <input type="text" name="nome" required value="<?= htmlspecialchars($aluno_editando['nome'] ?? '') ?>" style="width: 300px; padding: 5px;"><br><br>
        
        <?php if(!$aluno_editando): ?>
            <label>Matrícula:</label><br>
            <input type="text" name="matricula" required style="width: 200px; padding: 5px;"><br><br>
        <?php endif; ?>
        
        <label>Série:</label><br>
        <input type="text" name="serie" required value="<?= htmlspecialchars($aluno_editando['serie'] ?? '') ?>" placeholder="Ex: 5º Ano" style="width: 200px; padding: 5px;"><br><br>
        
        <label>Gênero:</label><br>
        <select name="genero" required style="width: 200px; padding: 5px;">
            <option value="">Selecione...</option>
            <option value="Masculino" <?= ($aluno_editando['genero'] ?? '') == 'Masculino' ? 'selected' : '' ?>>Masculino</option>
            <option value="Feminino" <?= ($aluno_editando['genero'] ?? '') == 'Feminino' ? 'selected' : '' ?>>Feminino</option>
        </select><br><br>
        
        <?php if(!$aluno_editando): ?>
            <h3>Dados do Responsável (opcional)</h3>
            <label>Nome do Responsável:</label><br>
            <input type="text" name="Responsável_nome" style="width: 300px; padding: 5px;"><br><br>
            
            <label>Email do Responsável:</label><br>
            <input type="email" name="Responsável_email" style="width: 300px; padding: 5px;"><br><br>
            
            <label>Telefone do Responsável:</label><br>
            <input type="text" name="Responsável_telefone" style="width: 200px; padding: 5px;"><br><br>
        <?php else: ?>
            <h3>Responsáveis do aluno</h3>
            <?php if(!empty($responsaveis_aluno)): ?>
                <?php foreach($responsaveis_aluno as $responsavel): ?>
                    <fieldset style="margin-bottom: 15px; padding: 10px; border: 1px solid #ccc;">
                        <legend><?= htmlspecialchars($responsavel['nome']) ?></legend>
                        <label>Nome:</label><br>
                        <input type="text" name="responsaveis[<?= (int)$responsavel['id'] ?>][nome]" value="<?= htmlspecialchars($responsavel['nome']) ?>" style="width: 300px; padding: 5px;"><br><br>

                        <label>Email:</label><br>
                        <input type="email" name="responsaveis[<?= (int)$responsavel['id'] ?>][email]" value="<?= htmlspecialchars($responsavel['email']) ?>" style="width: 300px; padding: 5px;"><br><br>

                        <label>Telefone:</label><br>
                        <input type="text" name="responsaveis[<?= (int)$responsavel['id'] ?>][telefone]" value="<?= htmlspecialchars($responsavel['telefone'] ?? '') ?>" style="width: 200px; padding: 5px;"><br><br>

                        <label style="color: #c00;">
                            <input type="checkbox" name="responsaveis[<?= (int)$responsavel['id'] ?>][remover]" value="1">
                            Remover responsável
                        </label>
                    </fieldset>
                <?php endforeach; ?>
            <?php else: ?>
                <p>Nenhum responsável cadastrado para este aluno.</p>
            <?php endif; ?>

            <h3>Adicionar novo responsável</h3>
            <p>Preencha os campos abaixo para incluir mais um responsável.</p>
            <label>Nome:</label><br>
            <input type="text" name="novo_responsavel[nome]" style="width: 300px; padding: 5px;"><br><br>

            <label>Email:</label><br>
            <input type="email" name="novo_responsavel[email]" style="width: 300px; padding: 5px;"><br><br>

            <label>Telefone:</label><br>
            <input type="text" name="novo_responsavel[telefone]" style="width: 200px; padding: 5px;"><br><br>
        <?php endif; ?>
        
        <button type="submit" name="<?= $aluno_editando ? 'editar_aluno' : 'adicionar_aluno' ?>" style="padding: 10px 20px;">
            <?= $aluno_editando ? 'Atualizar Aluno' : 'Adicionar Aluno' ?>
        </button>
        
        <?php if($aluno_editando): ?>
            <a href="/alunos-gestor" style="margin-left: 10px;">Cancelar</a>
        <?php endif; ?>
    </form>
    
    <hr>
    
    <h2>Importar Alunos em Lote (CSV)</h2>
    <p>Formato do CSV: nome, matricula, serie, genero, Responsável_nome, Responsável_email, Responsável_telefone</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="arquivo_csv" accept=".csv" required>
        <button type="submit" name="importar_csv">Importar CSV</button>
    </form>
    
    <hr>
    
    <h2>Lista de Alunos (<?= count($alunos) ?>)</h2>
    
    <?php if(count($alunos) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Matrícula</th>
                    <th>Nome</th>
                    <th>Série</th>
                    <th>Gênero</th>
                    <th>Responsáveis</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($alunos as $aluno): ?>
                    <tr>
                        <td><?= htmlspecialchars($aluno['matricula']) ?></td>
                        <td><?= htmlspecialchars($aluno['nome']) ?></td>
                        <td><?= htmlspecialchars($aluno['serie']) ?></td>
                        <td><?= htmlspecialchars($aluno['genero']) ?></td>
                        <td><?= $aluno['total_responsaveis'] ?></td>
                        <td><?= $aluno['ativo'] ? 'Ativo' : 'Inativo' ?></td>
                        <td>
                            <a href="/alunos-gestor?editar=<?= $aluno['id'] ?>">Editar</a> |
                            <form method="POST" style="display: inline;">
                                <input type="hidden" name="aluno_id" value="<?= $aluno['id'] ?>">
                                <input type="hidden" name="status" value="<?= $aluno['ativo'] ? 0 : 1 ?>">
                                <button type="submit" name="toggle_aluno" style="color: <?= $aluno['ativo'] ? 'red' : 'green' ?>;">
                                    <?= $aluno['ativo'] ? 'Desativar' : 'Ativar' ?>
                                </button>
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum aluno cadastrado ainda.</p>
    <?php endif; ?>
</body>
</html>
