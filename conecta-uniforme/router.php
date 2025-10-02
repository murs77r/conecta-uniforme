<?php
$host = $_SERVER['HTTP_HOST'];
$caminho = $_SERVER['REQUEST_URI'];

$caminho = substr($caminho, 1);
$partes = explode('/',$caminho);

echo $partes[0];

$routes = [
    $host => '/Model/home.php',
    $host.'/cadastro' => '/Model/cadastro.php',
    $host.'/login' => '/Model/login.php',
];

if (array_key_exists($host.'/'.$caminho,$routes)) {
    $caminho_counteudo = $routes[$host.'/'.$caminho];
    include 'View/parciais/template.php';
}