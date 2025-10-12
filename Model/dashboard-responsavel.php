<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Aluno.php';
require_once __DIR__ . '/../classes/Produto.php';
require_once __DIR__ . '/../classes/Carrinho.php';
require_once __DIR__ . '/../classes/Pedido.php';

iniciarSessaoSegura();

// Verificar se está logado como responsável
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'Responsável') {
    header('Location: /login-novo');
    exit;
}

$alunoClass = new Aluno();
$produto = new Produto();
$carrinho = new Carrinho();
$pedido = new Pedido();

$Responsável_id = $_SESSION['user_id'];

// Buscar dados do aluno vinculado
$sql = "SELECT aluno_id FROM Responsável WHERE id = $Responsável_id";
$result = $con->query($sql);
$resp_data = $result->fetch_assoc();
$aluno_id = $resp_data['aluno_id'];

$aluno = $alunoClass->buscarPorId($aluno_id);

$_SESSION['aluno_id'] = $aluno_id;
$_SESSION['escola_id'] = $aluno['escola_id'];

$mensagem = '';
$erro = '';

// Buscar dados
$itens_carrinho = $carrinho->listar($Responsável_id);
$meus_pedidos = $pedido->listarPorResponsavel($Responsável_id);

// Estatísticas
$total_carrinho = $carrinho->contarItens($Responsável_id);
$total_pedidos = count($meus_pedidos);

require __DIR__ . '/../View/dashboard-responsavel.view.php';
