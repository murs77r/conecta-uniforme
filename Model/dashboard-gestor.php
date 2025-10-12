<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Homologacao.php';
require_once __DIR__ . '/../classes/Usuario.php';
require_once __DIR__ . '/../classes/Aluno.php';
require_once __DIR__ . '/../classes/Pedido.php';

iniciarSessaoSegura();

// Verificar se está logado como gestor
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'gestor') {
    header('Location: /login-novo');
    exit;
}

$homologacao = new Homologacao();
$usuario = new Usuario();
$aluno = new Aluno();
$pedido = new Pedido();

// Buscar escola do gestor
$gestor_id = $_SESSION['user_id'];
$sql = "SELECT escola_id FROM gestor WHERE id = $gestor_id";
$result = $con->query($sql);
$escola_data = $result->fetch_assoc();
$escola_id = $escola_data['escola_id'];

$_SESSION['escola_id'] = $escola_id;

$mensagem = '';
$erro = '';

// Ações
if(isset($_POST['habilitar_fornecedor'])) {
    $fornecedor_id = $_POST['fornecedor_id'];
    if($homologacao->criar($escola_id, $fornecedor_id)) {
        $mensagem = 'Fornecedor habilitado com sucesso!';
    } else {
        $erro = 'Erro ao habilitar fornecedor.';
    }
}

if(isset($_POST['desabilitar_fornecedor'])) {
    $fornecedor_id = $_POST['fornecedor_id'];
    if($homologacao->remover($escola_id, $fornecedor_id)) {
        $mensagem = 'Fornecedor desabilitado com sucesso!';
    } else {
        $erro = 'Erro ao desabilitar fornecedor.';
    }
}

if(isset($_POST['importar_alunos'])) {
    // Processar CSV ou array de alunos
    // Exemplo simplificado
    $mensagem = 'Funcionalidade de importação em lote disponível';
}

// Buscar dados
$fornecedores_homologados = $homologacao->listarFornecedoresHomologados($escola_id);
$fornecedores_disponiveis = $homologacao->listarFornecedoresDisponiveis($escola_id);
$alunos = $aluno->listarPorEscola($escola_id);
$pedidos = $pedido->listarPorEscola($escola_id);

// Estatísticas
$total_alunos = count($alunos);
$total_fornecedores = count($fornecedores_homologados);
$total_pedidos = count($pedidos);
