<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$basePath = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/\\');

if ($basePath !== '' && strpos($uri, $basePath) === 0) {
    $uri = substr($uri, strlen($basePath));
}

$uri = trim($uri, '/');

$redirectBase = $basePath === '' ? '' : $basePath;

$redirect = function (string $path = '') use ($redirectBase): void {
    $path = ltrim($path, '/');
    $location = $redirectBase . '/' . $path;
    if ($path === '') {
        $location = $redirectBase ?: '/';
    }
    header('Location: ' . $location);
    exit;
};

if ($uri === '' || $uri === 'index.php') {
    $role = $_SESSION['user_tipo'] ?? $_SESSION['role'] ?? null;
    $tipoAntigo = $_SESSION['tipo_usuario'] ?? null; // suporte ao login antigo numérico

    if (!$role && $tipoAntigo) {
        $map = [
            1 => 'gestor',
            2 => 'aluno',
            3 => 'responsavel',
            4 => 'fornecedor',
        ];
        $role = $map[$tipoAntigo] ?? null;
    }

    if ($role) {
        $destinos = [
            'gestor' => 'dashboard-gestor',
            'fornecedor' => 'dashboard-fornecedor',
            'responsavel' => 'dashboard-responsavel',
            'aluno' => 'catalogo-novo',
        ];
        if (isset($destinos[$role])) {
            $redirect($destinos[$role]);
        }
    }

    $redirect('login-novo');
}

$routes = [
    // Rotas originais
    '' => '/Model/home.php',
    'cadastro' => '/Model/cadastro.php',
    'login' => '/Model/login.php',
    'responsavel' => '/Model/responsavel.php',
    'usuarios' => '/Model/usuarios.php',
    'catalogo' => '/Model/catalogo.php',

    // Novas rotas do sistema
    'login-novo' => '/Model/login-novo.php',
    'logout' => '/Model/logout.php',

    // Dashboards por perfil
    'dashboard-gestor' => '/Model/dashboard-gestor.php',
    'dashboard-fornecedor' => '/Model/dashboard-fornecedor.php',
    'dashboard-responsavel' => '/Model/dashboard-responsavel.php',

    // Gestão de alunos (gestor)
    'alunos-gestor' => '/Model/alunos-gestor.php',

    // Gestão de produtos (fornecedor)
    'produtos-fornecedor' => '/Model/produtos-fornecedor.php',

    // Catálogo e carrinho (responsável)
    'catalogo-novo' => '/Model/catalogo-novo.php',
    'carrinho-novo' => '/Model/carrinho-novo.php',

    // Pedidos (todos os perfis)
    'pedidos-gerenciar' => '/Model/pedidos-gerenciar.php',

    // Comissões e relatórios
    'comissoes-relatorio' => '/Model/comissoes-relatorio.php',
];

if (array_key_exists($uri, $routes)) {
    $caminho_counteudo = $routes[$uri];
} else {
    http_response_code(404);
    $caminho_counteudo = '/View/404.view.php';
}

include 'View/parciais/template.php';
