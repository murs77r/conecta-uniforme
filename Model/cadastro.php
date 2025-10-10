<?php
require_once 'Classes/Escola.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'] ?? '';
    $nome = $_POST['nome'] ?? '';
    $cnpj = $_POST['cnpj'] ?? '';
    $senha = $_POST['senha'] ?? '';

    $cep = $_POST['cep'] ?? '';
    $estado = $_POST['estado'] ?? '';
    $cidade = $_POST['cidade'] ?? '';
    $endereco = $_POST['endereco'] ?? '';
    $complemento = $_POST['complemento'] ?? '';

    $escola = new Escola($email, $nome, $cnpj, $senha, $cep, $estado, $cidade, $endereco, $complemento);
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

include 'View/cadastro.view.php';