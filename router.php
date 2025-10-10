<?php
$host = $_SERVER['HTTP_HOST'];
$caminho = $_SERVER['REQUEST_URI'];

$caminho = substr($caminho, 1);
$partes = explode('/',$caminho);

$root = $host.'/conecta-uniforme/';
$routes = [
    $root => '/Model/home.php',
    $root.'cadastro' => '/Model/cadastro.php',
    $root.'login' => '/Model/login.php',
    $root.'catalogo' => '/Model/catalogo.php',
];

if (array_key_exists($host.'/'.$caminho,$routes)) {
    $caminho_counteudo = $routes[$host.'/'.$caminho];
} else {
    $caminho_counteudo = '/View/404.view.php';
}
include 'View/parciais/template.php';