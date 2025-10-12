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

// Atualizar status (apenas fornecedor)
if(isset($_POST['atualizar_status']) && $user_tipo == 'fornecedor') {
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
        case 'responsavel':
            $pedidos = $pedidoClass->listarPorResponsavel($user_id);
            break;
        case 'fornecedor':
            $pedidos = $pedidoClass->listarPorFornecedor($user_id);
            break;
        case 'gestor':
            $escola_id = $_SESSION['escola_id'];
            $pedidos = $pedidoClass->listarPorEscola($escola_id);
            break;
    }
}

// Definir status disponíveis para transição
$status_labels = [
    'pendente' => 'Pendente',
    'aprovado' => 'Aprovado',
    'em_producao' => 'Em Produção',
    'pronto_retirada' => 'Pronto para Retirada',
    'entregue' => 'Entregue',
    'cancelado' => 'Cancelado'
];

$proximos_status = [
    'pendente' => ['aprovado', 'cancelado'],
    'aprovado' => ['em_producao', 'cancelado'],
    'em_producao' => ['pronto_retirada', 'cancelado'],
    'pronto_retirada' => ['entregue'],
    'entregue' => [],
    'cancelado' => []
];

require __DIR__ . '/../View/pedidos-gerenciar.view.php';
