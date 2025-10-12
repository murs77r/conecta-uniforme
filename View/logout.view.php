<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Logout - Conecta Uniforme</title>
</head>
<body>
    <h1>Saindo...</h1>
    <p>Você foi desconectado com sucesso.</p>
    <p><a href="/">Voltar para página inicial</a></p>
    <p><a href="/login-novo">Fazer login novamente</a></p>
</body>
</html>
<?php
session_start();
session_destroy();
header('refresh:2;url=/');
?>
