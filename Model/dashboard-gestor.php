<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Homologacao.php';
require_once __DIR__ . '/../classes/Usuario.php';
require_once __DIR__ . '/../classes/Aluno.php';
require_once __DIR__ . '/../classes/Pedido.php';

iniciarSessaoSegura();

// Verificar se está logado como Gestor
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'Gestor') {
    header('Location: /login-novo');
    exit;
}

$homologacao = new Homologacao();
$usuario = new Usuario();
$aluno = new Aluno();
$pedido = new Pedido();

// Buscar escola do Gestor
$Gestor_id = $_SESSION['user_id'];
$sql = "SELECT escola_id FROM Gestor WHERE id = $Gestor_id";
$result = $con->query($sql);
$escola_data = $result->fetch_assoc();
$escola_id = $escola_data['escola_id'];

$_SESSION['escola_id'] = $escola_id;

$mensagem = '';
$erro = '';

// Ações
if(isset($_POST['habilitar_Fornecedor'])) {
    $Fornecedor_id = $_POST['Fornecedor_id'];
    if($homologacao->criar($escola_id, $Fornecedor_id)) {
        $mensagem = 'Fornecedor habilitado com sucesso!';
    } else {
        $erro = 'Erro ao habilitar Fornecedor.';
    }
}

if(isset($_POST['desabilitar_Fornecedor'])) {
    $Fornecedor_id = $_POST['Fornecedor_id'];
    if($homologacao->remover($escola_id, $Fornecedor_id)) {
        $mensagem = 'Fornecedor desabilitado com sucesso!';
    } else {
        $erro = 'Erro ao desabilitar Fornecedor.';
    }
}

if(isset($_POST['importar_alunos'])) {
    // Processar CSV ou array de alunos
    // Exemplo simplificado
    $mensagem = 'Funcionalidade de importação em lote disponível';
}

// Buscar dados
$Fornecedores_homologados = $homologacao->listarFornecedoresHomologados($escola_id);
$Fornecedores_disponiveis = $homologacao->listarFornecedoresDisponiveis($escola_id);
$alunos = $aluno->listarPorEscola($escola_id);
$pedidos = $pedido->listarPorEscola($escola_id);

// Estatísticas
$total_alunos = count($alunos);
$total_Fornecedores = count($Fornecedores_homologados);
$total_pedidos = count($pedidos);

require __DIR__ . '/../View/dashboard-Gestor.view.php';
