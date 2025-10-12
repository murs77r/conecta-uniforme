<?php
/**
 * Arquivo de Conexão com Banco de Dados
 * Utiliza variáveis de ambiente do .env
 */

// Carrega configurações
require_once __DIR__ . '/config.php';

// Conexão com o banco de dados usando variáveis do .env
$servidor = env('DB_HOST', env('MYSQLHOST', '127.0.0.1'));
$usuario = env('DB_USER', env('MYSQLUSER', 'root'));
$senha = env('DB_PASS', env('MYSQLPASSWORD', ''));
$banco = env('DB_NAME', env('MYSQLDATABASE', 'conecta_uniformes'));
$porta = (int)env('DB_PORT', env('MYSQLPORT', 3306));
$socket = env('DB_SOCKET');

try {
    $con = new mysqli($servidor, $usuario, $senha, $banco, $porta ?: null, $socket ?: null);
    
    if ($con->connect_error) {
        throw new Exception("Erro de conexão: " . $con->connect_error);
    }
    
    // Define charset para UTF-8
    $con->set_charset("utf8mb4");
    
} catch(Exception $e) {
    if (env('APP_ENV') === 'production') {
        die("Erro ao conectar ao banco de dados. Contate o suporte.");
    } else {
        die("Falha na conexão: " . $e->getMessage());
    }
}
?>