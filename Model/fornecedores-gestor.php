<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Homologacao.php';
require_once __DIR__ . '/../classes/Fornecedor.php';

iniciarSessaoSegura();

if (!isset($_SESSION['logado']) || $_SESSION['user_tipo'] !== 'Gestor') {
    header('Location: /login-novo');
    exit;
}

$homologacao = new Homologacao();

$gestorId = (int)($_SESSION['user_id'] ?? 0);
$escolaId = $_SESSION['escola_id'] ?? null;

if (!$escolaId && $gestorId) {
    $sql = "SELECT escola_id FROM Gestor WHERE id = $gestorId LIMIT 1";
    $resultado = $con->query($sql);
    if ($resultado && $resultado->num_rows > 0) {
        $escolaId = (int)$resultado->fetch_assoc()['escola_id'];
        $_SESSION['escola_id'] = $escolaId;
    }
}

if (!$escolaId) {
    header('Location: /dashboard-gestor');
    exit;
}

$mensagem = '';
$erro = '';

if (isset($_POST['habilitar_Fornecedor'])) {
    $FornecedorId = (int)($_POST['Fornecedor_id'] ?? 0);
    if ($FornecedorId && $homologacao->criar($escolaId, $FornecedorId)) {
        $mensagem = 'Fornecedor habilitado com sucesso!';
    } else {
        $erro = 'Não foi possível habilitar o fornecedor.';
    }
}

if (isset($_POST['desabilitar_Fornecedor'])) {
    $FornecedorId = (int)($_POST['Fornecedor_id'] ?? 0);
    if ($FornecedorId && $homologacao->remover($escolaId, $FornecedorId)) {
        $mensagem = 'Fornecedor desabilitado com sucesso!';
    } else {
        $erro = 'Não foi possível desabilitar o fornecedor.';
    }
}

$fornecedoresHomologados = $homologacao->listarFornecedoresHomologados($escolaId);
$fornecedoresDisponiveis = $homologacao->listarFornecedoresDisponiveis($escolaId);

require __DIR__ . '/../View/fornecedores-gestor.view.php';
