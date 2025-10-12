<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Pedido.php';

iniciarSessaoSegura();

// Verificar se está logado
if(!isset($_SESSION['logado'])) {
    header('Location: /login-novo');
    exit;
}

$pedidoClass = new Pedido();
$user_tipo = $_SESSION['user_tipo'];
$user_id = $_SESSION['user_id'];

$mensagem = '';
$erro = '';

// Buscar pedido específico
$pedido_id = isset($_GET['id']) ? (int)$_GET['id'] : null;
$pedido = null;
$itens = [];

if($pedido_id) {
    $pedido = $pedidoClass->buscarPorId($pedido_id);
    $itens = $pedidoClass->buscarItensPedido($pedido_id);
}

// Atualizar status (apenas Fornecedor)
if(isset($_POST['atualizar_status']) && $user_tipo == 'Fornecedor') {
    $pedido_id = $_POST['pedido_id'];
    $novo_status = $_POST['status'];
    
    if($pedidoClass->atualizarStatus($pedido_id, $novo_status)) {
        $mensagem = 'Status atualizado com sucesso!';
        // Recarregar pedido
        $pedido = $pedidoClass->buscarPorId($pedido_id);
    } else {
        $erro = 'Erro ao atualizar status.';
    }
}

// Listar pedidos conforme tipo de usuário
$pedidos = [];

if(!$pedido_id) {
    switch($user_tipo) {
        case 'Responsável':
            $pedidos = $pedidoClass->listarPorResponsavel($user_id);
            break;
        case 'Fornecedor':
            $pedidos = $pedidoClass->listarPorFornecedor($user_id);
            break;
        case 'Gestor':
            $escola_id = $_SESSION['escola_id'];
            $pedidos = $pedidoClass->listarPorEscola($escola_id);
            break;
    }
}

// Definir status disponíveis para transição
$status_labels = [
    'Pendente' => 'Pendente',
    'Aprovado' => 'Aprovado',
    'Em Produção' => 'Em Produção',
    'Disponível para Retirar' => 'Pronto para Retirada',
    'Entregue' => 'Entregue',
    'Cancelado' => 'Cancelado'
];

$proximos_status = [
    'Pendente' => ['Aprovado', 'Cancelado'],
    'Aprovado' => ['Em Produção', 'Cancelado'],
    'Em Produção' => ['Disponível para Retirar', 'Cancelado'],
    'Disponível para Retirar' => ['Entregue'],
    'Entregue' => [],
    'Cancelado' => []
];

require __DIR__ . '/../View/pedidos-gerenciar.view.php';
