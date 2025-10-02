<?php
require_once 'Classes/Escola.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'] ?? '';
    $nome = $_POST['nome'] ?? '';
    $cnpj = $_POST['cnpj'] ?? '';
    $cep = $_POST['cep'] ?? '';
    $estado = $_POST['estado'] ?? '';
    $cidade = $_POST['cidade'] ?? '';
    $endereco = $_POST['endereco'] ?? '';
    $complemento = $_POST['complemento'] ?? '';

    $escola = new Escola($email, $nome, $cnpj, $cep, $estado, $cidade, $endereco, $complemento);
    $escola->gerarChave();
    $resultado = $escola->salvar();
    if (is_string($resultado)) {
        echo "Erro ao cadastrar a escola: " . htmlspecialchars($resultado);
    } else {
        echo "Escola cadastrada com sucesso! ID: " . $escola->getId();
        header('Location: /conecta-uniforme');
        exit;
    }
}
?>

<form method="post">
    Email: <input type="email" name="email" required><br>
    Nome: <input type="text" name="nome" required><br>
    CNPJ: <input type="text" name="cnpj" required><br>
    CEP: <input type="text" name="cep" required><br>
    Estado: <input type="text" name="estado" required><br>
    Cidade: <input type="text" name="cidade" required><br>
    Endereço: <input type="text" name="endereco" required><br>
    Complemento: <input type="text" name="complemento"><br>
    <input type="submit" value="Cadastrar">
</form>