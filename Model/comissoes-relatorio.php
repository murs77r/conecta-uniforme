<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Comissao.php';

iniciarSessaoSegura();

// Verificar se está logado como fornecedor ou admin
if(!isset($_SESSION['logado']) || !in_array($_SESSION['user_tipo'], ['fornecedor', 'gestor'])) {
    header('Location: /conecta-uniforme/login-novo');
    exit;
}

$comissaoClass = new Comissao();
$user_tipo = $_SESSION['user_tipo'];

$mensagem = '';
$erro = '';

// Gerar relatório mensal (apenas admin)
if(isset($_POST['gerar_relatorio']) && $user_tipo == 'gestor') {
    $ano = $_POST['ano'];
    $mes = $_POST['mes'];
    
    $relatorios = $comissaoClass->gerarRelatorioMensal($ano, $mes);
    
    if(count($relatorios) > 0) {
        $mensagem = 'Relatório gerado com sucesso! ' . count($relatorios) . ' fornecedores processados.';
    } else {
        $erro = 'Nenhuma venda encontrada para o período.';
    }
}

// Registrar pagamento (apenas admin)
if(isset($_POST['registrar_pagamento']) && $user_tipo == 'gestor') {
    $comissao_id = $_POST['comissao_id'];
    $valor_pago = $_POST['valor_pago'];
    $data_pagamento = $_POST['data_pagamento'];
    
    if($comissaoClass->registrarPagamento($comissao_id, $valor_pago, $data_pagamento)) {
        $mensagem = 'Pagamento registrado com sucesso!';
    } else {
        $erro = 'Erro ao registrar pagamento.';
    }
}

// Buscar comissões
$comissoes = [];
$detalhes_vendas = [];

if($user_tipo == 'fornecedor') {
    $fornecedor_id = $_SESSION['user_id'];
    $comissoes = $comissaoClass->listarPorFornecedor($fornecedor_id);
    
    // Se visualizando detalhes de um mês específico
    if(isset($_GET['mes'])) {
        $mes_referencia = $_GET['mes'];
        $detalhes_vendas = $comissaoClass->detalhesVendasMes($fornecedor_id, $mes_referencia);
    }
} else {
    // Admin vê todas
    $filtro_status = $_GET['status'] ?? null;
    $comissoes = $comissaoClass->listarTodas($filtro_status);
}

// Buscar comissão específica se editando
$comissao_editando = null;
if(isset($_GET['editar'])) {
    $comissao_id = (int)$_GET['editar'];
    $comissao_editando = $comissaoClass->buscarPorId($comissao_id);
}
