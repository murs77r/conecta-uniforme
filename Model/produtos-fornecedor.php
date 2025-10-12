<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Produto.php';

iniciarSessaoSegura();

// Verificar se está logado como fornecedor
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'fornecedor') {
    header('Location: /conecta-uniforme/login-novo');
    exit;
}

$produto = new Produto();
$fornecedor_id = $_SESSION['user_id'];

$mensagem = '';
$erro = '';

// Criar produto
if(isset($_POST['criar_produto'])) {
    $dados = [
        'fornecedor_id' => $fornecedor_id,
        'nome' => $_POST['nome'],
        'descricao' => $_POST['descricao'] ?? '',
        'preco' => $_POST['preco']
    ];
    
    $produto_id = $produto->criar($dados);
    
    if($produto_id) {
        // Adicionar homologações
        if(isset($_POST['escolas']) && is_array($_POST['escolas'])) {
            foreach($_POST['escolas'] as $escola_serie) {
                list($escola_id, $serie) = explode('|', $escola_serie);
                $produto->homologarProduto($produto_id, $escola_id, $serie);
            }
        }
        
        // Adicionar variações
        if(isset($_POST['variacoes']) && is_array($_POST['variacoes'])) {
            foreach($_POST['variacoes'] as $variacao) {
                $produto->adicionarVariacao($produto_id, $variacao);
            }
        }
        
        $mensagem = 'Produto criado com sucesso!';
    } else {
        $erro = 'Erro ao criar produto.';
    }
}

// Atualizar produto
if(isset($_POST['atualizar_produto'])) {
    $produto_id = $_POST['produto_id'];
    $dados = [
        'nome' => $_POST['nome'],
        'descricao' => $_POST['descricao'] ?? '',
        'preco' => $_POST['preco']
    ];
    
    if($produto->atualizar($produto_id, $dados)) {
        $mensagem = 'Produto atualizado com sucesso!';
    } else {
        $erro = 'Erro ao atualizar produto.';
    }
}

// Ativar/Desativar produto
if(isset($_POST['toggle_produto'])) {
    $produto_id = $_POST['produto_id'];
    $status = $_POST['status'];
    
    if($produto->ativarDesativar($produto_id, $status)) {
        $mensagem = 'Status atualizado!';
    } else {
        $erro = 'Erro ao atualizar status.';
    }
}

// Adicionar variação
if(isset($_POST['adicionar_variacao'])) {
    $produto_id = $_POST['produto_id'];
    $dados = [
        'tamanho' => $_POST['tamanho'],
        'cor' => $_POST['cor'] ?? '',
        'genero' => $_POST['genero'],
        'quantidade_estoque' => $_POST['quantidade'] ?? 0
    ];
    
    if($produto->adicionarVariacao($produto_id, $dados)) {
        $mensagem = 'Variação adicionada!';
    } else {
        $erro = 'Erro ao adicionar variação.';
    }
}

// Atualizar estoque
if(isset($_POST['atualizar_estoque'])) {
    $variacao_id = $_POST['variacao_id'];
    $quantidade = $_POST['quantidade'];
    
    if($produto->atualizarEstoque($variacao_id, $quantidade)) {
        $mensagem = 'Estoque atualizado!';
    } else {
        $erro = 'Erro ao atualizar estoque.';
    }
}

// Buscar produtos do fornecedor
$produtos = $produto->listarPorFornecedor($fornecedor_id);

// Buscar produto específico se editando
$produto_editando = null;
$variacoes = [];
if(isset($_GET['editar']) && $_GET['editar']) {
    $produto_id = (int)$_GET['editar'];
    $produto_editando = $produto->buscarPorId($produto_id);
    $variacoes = $produto->buscarVariacoes($produto_id);
}

// Buscar escolas disponíveis para homologação
$sql = "SELECT DISTINCT e.id, e.nome 
        FROM escola e 
        INNER JOIN homologacao h ON e.id = h.escola_id 
        WHERE h.fornecedor_id = $fornecedor_id AND h.ativo = 1
        ORDER BY e.nome";
$result = $con->query($sql);
$escolas_disponiveis = $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
