<?php
$host = $_SERVER['HTTP_HOST'];
$caminho = $_SERVER['REQUEST_URI'];

$caminho = substr($caminho, 1);
$partes = explode('/',$caminho);

$root = $host.'/conecta-uniforme/';
$routes = [
    // Rotas originais
    $root => '/Model/home.php',
    $root.'cadastro' => '/Model/cadastro.php',
    $root.'login' => '/Model/login.php',
    $root.'responsavel' => '/Model/responsavel.php',
    $root.'usuarios' => '/Model/usuarios.php',
    $root.'catalogo' => '/Model/catalogo.php',
    
    // Novas rotas do sistema
    $root.'login-novo' => '/Model/login-novo.php',
    $root.'logout' => '/Model/logout.php',
    
    // Dashboards por perfil
    $root.'dashboard-gestor' => '/Model/dashboard-gestor.php',
    $root.'dashboard-fornecedor' => '/Model/dashboard-fornecedor.php',
    $root.'dashboard-responsavel' => '/Model/dashboard-responsavel.php',
    
    // Gestão de alunos (gestor)
    $root.'alunos-gestor' => '/Model/alunos-gestor.php',
    
    // Gestão de produtos (fornecedor)
    $root.'produtos-fornecedor' => '/Model/produtos-fornecedor.php',
    
    // Catálogo e carrinho (responsável)
    $root.'catalogo-novo' => '/Model/catalogo-novo.php',
    $root.'carrinho-novo' => '/Model/carrinho-novo.php',
    
    // Pedidos (todos os perfis)
    $root.'pedidos-gerenciar' => '/Model/pedidos-gerenciar.php',
    
    // Comissões e relatórios
    $root.'comissoes-relatorio' => '/Model/comissoes-relatorio.php',
];

if (array_key_exists($host.'/'.$caminho,$routes)) {
    $caminho_counteudo = $routes[$host.'/'.$caminho];
} else {
    $caminho_counteudo = '/View/404.view.php';
}
include 'View/parciais/template.php';
