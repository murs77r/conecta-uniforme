<?php
session_start();
require_once 'conexao.php';
require_once 'classes/Produto.php';
require_once 'classes/Carrinho.php';
require_once 'classes/Aluno.php';

// Verificar se está logado como responsável
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'responsavel') {
    header('Location: /conecta-uniforme/login-novo');
    exit;
}

$produto = new Produto();
$carrinho = new Carrinho();
$alunoClass = new Aluno();

$responsavel_id = $_SESSION['user_id'];
$aluno_id = $_SESSION['aluno_id'];

// Buscar informações do aluno
$aluno = $alunoClass->buscarPorId($aluno_id);
$escola_id = $aluno['escola_id'];
$serie = $aluno['serie'];
$genero = $aluno['genero'];

$mensagem = '';
$erro = '';

// Adicionar ao carrinho
if(isset($_POST['adicionar_carrinho'])) {
    $produto_id = $_POST['produto_id'];
    $variacao_id = $_POST['variacao_id'];
    $quantidade = $_POST['quantidade'] ?? 1;
    
    if($carrinho->adicionar($responsavel_id, $produto_id, $variacao_id, $quantidade)) {
        $mensagem = 'Produto adicionado ao carrinho!';
    } else {
        $erro = 'Erro ao adicionar produto.';
    }
}

// Buscar produtos disponíveis
$produtos = $produto->listarPorEscolaSerieGenero($escola_id, $serie, $genero);

// Buscar detalhes do produto se selecionado
$produto_selecionado = null;
$fotos = [];
$variacoes = [];

if(isset($_GET['produto_id'])) {
    $produto_id = (int)$_GET['produto_id'];
    $produto_selecionado = $produto->buscarPorId($produto_id);
    $fotos = $produto->buscarFotos($produto_id);
    $variacoes = $produto->buscarVariacoes($produto_id);
    
    // Filtrar variações pelo gênero do aluno
    $variacoes = array_filter($variacoes, function($v) use ($genero) {
        return $v['genero'] == $genero || $v['genero'] == 'unissex';
    });
}

$total_carrinho = $carrinho->contarItens($responsavel_id);
