<?php
/**
 * Endpoint de Health Check para Railway
 * Retorna status 200 se o sistema está operacional
 */

header('Content-Type: application/json');

$status = [
    'status' => 'ok',
    'timestamp' => date('Y-m-d H:i:s'),
    'service' => 'conecta-uniforme',
    'php_version' => phpversion()
];

// Testar conexão com banco (opcional)
try {
    require_once __DIR__ . '/config.php';
    
    $dbHost = env('DB_HOST', env('MYSQLHOST'));
    $dbUser = env('DB_USER', env('MYSQLUSER'));
    $dbPass = env('DB_PASS', env('MYSQLPASSWORD'));
    $dbName = env('DB_NAME', env('MYSQLDATABASE'));
    $dbPort = (int)env('DB_PORT', env('MYSQLPORT', 3306));
    $dbSocket = env('DB_SOCKET');
    
    if ($dbHost && $dbUser && $dbName) {
        $conn = @new mysqli($dbHost, $dbUser, $dbPass, $dbName, $dbPort ?: null, $dbSocket ?: null);
        
        if ($conn->connect_error) {
            $status['database'] = 'error';
            $status['database_message'] = $conn->connect_error;
            http_response_code(503); // Service Unavailable
        } else {
            $status['database'] = 'connected';
            $conn->close();
        }
    } else {
        $status['database'] = 'not_configured';
    }
    
} catch (Exception $e) {
    $status['database'] = 'error';
    $status['database_message'] = 'Config error';
}

echo json_encode($status, JSON_PRETTY_PRINT);
?>
