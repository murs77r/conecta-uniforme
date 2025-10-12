<h2>Usuários</h2>
<table border="1">
    <tr><th>ID</th><th>Nome</th><th>Email</th><th>Role</th><th>Ativo</th><th>Escola</th></tr>
    <?php foreach($usuarios as $u): ?>
        <tr>
            <td><?php echo $u['id']; ?></td>
            <td><?php echo htmlspecialchars($u['nome']); ?></td>
            <td><?php echo htmlspecialchars($u['email']); ?></td>
            <td><?php echo $u['role']; ?></td>
            <td><?php echo $u['ativo'] ? 'Sim' : 'Não'; ?></td>
            <td><?php echo htmlspecialchars($u['escola']); ?></td>
        </tr>
    <?php endforeach; ?>
</table>
