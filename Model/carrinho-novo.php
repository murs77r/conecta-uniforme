<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Carrinho.php';
require_once __DIR__ . '/../classes/Pedido.php';
require_once __DIR__ . '/../classes/Aluno.php';

iniciarSessaoSegura();

// Verificar se está logado como responsável
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'responsavel') {
    header('Location: /login-novo');
    exit;
}

$carrinho = new Carrinho();
$pedido = new Pedido();
$alunoClass = new Aluno();

$responsavel_id = $_SESSION['user_id'];
$aluno_id = $_SESSION['aluno_id'];
$escola_id = $_SESSION['escola_id'];

$mensagem = '';
$erro = '';

// Atualizar quantidade
if(isset($_POST['atualizar_quantidade'])) {
    $item_id = $_POST['item_id'];
    $quantidade = $_POST['quantidade'];
    
    if($carrinho->atualizar($item_id, $quantidade)) {
        $mensagem = 'Quantidade atualizada!';
    } else {
        $erro = 'Erro ao atualizar quantidade.';
    }
}

// Remover item
if(isset($_POST['remover_item'])) {
    $item_id = $_POST['item_id'];
    
    if($carrinho->remover($item_id)) {
        $mensagem = 'Item removido!';
    } else {
        $erro = 'Erro ao remover item.';
    }
}

// Finalizar pedido
if(isset($_POST['finalizar_pedido'])) {
    // Validar estoque
    $erros_estoque = $carrinho->validarEstoque($responsavel_id);
    
    if(count($erros_estoque) > 0) {
        $erro = 'Alguns produtos não têm estoque suficiente.';
    } else {
        $itens = $carrinho->listar($responsavel_id);
        
        // Preparar itens para o pedido
        $itens_pedido = [];
        foreach($itens as $item) {
            $itens_pedido[] = [
                'produto_id' => $item['produto_id'],
                'variacao_id' => $item['variacao_id'],
                'fornecedor_id' => $item['fornecedor_id'],
                'quantidade' => $item['quantidade'],
                'preco_unitario' => $item['preco']
            ];
        }
        
        $pedido_id = $pedido->criar($responsavel_id, $aluno_id, $escola_id, $itens_pedido);
        
        if($pedido_id) {
            $_SESSION['pedido_realizado'] = $pedido_id;
            header('Location: /pedido-sucesso');
            exit;
        } else {
            $erro = 'Erro ao finalizar pedido. Tente novamente.';
        }
    }
}

// Buscar itens do carrinho
$itens = $carrinho->listar($responsavel_id);
$total = $carrinho->calcularTotal($responsavel_id);
$total_itens = $carrinho->contarItens($responsavel_id);
