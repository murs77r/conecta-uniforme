<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Aluno.php';
require_once __DIR__ . '/../classes/Produto.php';
require_once __DIR__ . '/../classes/Carrinho.php';
require_once __DIR__ . '/../classes/Pedido.php';

iniciarSessaoSegura();

// Verificar se está logado como responsável
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'responsavel') {
    header('Location: /conecta-uniforme/login-novo');
    exit;
}

$alunoClass = new Aluno();
$produto = new Produto();
$carrinho = new Carrinho();
$pedido = new Pedido();

$responsavel_id = $_SESSION['user_id'];

// Buscar dados do aluno vinculado
$sql = "SELECT aluno_id FROM responsavel WHERE id = $responsavel_id";
$result = $con->query($sql);
$resp_data = $result->fetch_assoc();
$aluno_id = $resp_data['aluno_id'];

$aluno = $alunoClass->buscarPorId($aluno_id);

$_SESSION['aluno_id'] = $aluno_id;
$_SESSION['escola_id'] = $aluno['escola_id'];

$mensagem = '';
$erro = '';

// Buscar dados
$itens_carrinho = $carrinho->listar($responsavel_id);
$meus_pedidos = $pedido->listarPorResponsavel($responsavel_id);

// Estatísticas
$total_carrinho = $carrinho->contarItens($responsavel_id);
$total_pedidos = count($meus_pedidos);
