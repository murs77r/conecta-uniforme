<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Produto.php';
require_once __DIR__ . '/../classes/Pedido.php';
require_once __DIR__ . '/../classes/Comissao.php';

iniciarSessaoSegura();

// Verificar se está logado como fornecedor
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'fornecedor') {
    header('Location: /conecta-uniforme/login-novo');
    exit;
}

$produto = new Produto();
$pedido = new Pedido();
$comissao = new Comissao();

$fornecedor_id = $_SESSION['user_id'];

$mensagem = '';
$erro = '';

// Ações
if(isset($_POST['atualizar_status_pedido'])) {
    $pedido_id = $_POST['pedido_id'];
    $novo_status = $_POST['status'];
    
    if($pedido->atualizarStatus($pedido_id, $novo_status)) {
        $mensagem = 'Status atualizado com sucesso!';
    } else {
        $erro = 'Erro ao atualizar status.';
    }
}

// Buscar dados
$produtos = $produto->listarPorFornecedor($fornecedor_id);
$pedidos = $pedido->listarPorFornecedor($fornecedor_id);
$comissoes = $comissao->listarPorFornecedor($fornecedor_id);

// Estatísticas
$total_produtos = count($produtos);
$total_pedidos = count($pedidos);
$pedidos_pendentes = count(array_filter($pedidos, function($p) {
    return $p['status'] == 'pendente' || $p['status'] == 'aprovado';
}));
