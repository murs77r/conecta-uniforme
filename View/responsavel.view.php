<h2>Cadastro de Responsável</h2>
<?php if (!empty($errors)): ?>
    <div style="color:red"><?php echo implode('<br>', $errors); ?></div>
<?php endif; ?>
<?php if (!empty($success)): ?>
    <div style="color:green"><?php echo htmlspecialchars($success); ?></div>
<?php endif; ?>

<form method="post">
    Nome: <input type="text" name="nome" required><br>
    Email: <input type="email" name="email" required><br>
    Telefone: <input type="text" name="telefone"><br>
    Escola: <select name="escola_id">
        <?php foreach($escolas as $e): ?>
            <option value="<?php echo $e['id']; ?>"><?php echo htmlspecialchars($e['nome']); ?></option>
        <?php endforeach; ?>
    </select><br>
    Matrícula do aluno (fornecida pela escola): <input type="text" name="matricula" required><br>
    <input type="submit" value="Cadastrar">
</form>
