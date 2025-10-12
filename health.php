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
    
    $dbHost = env('DB_HOST');
    $dbUser = env('DB_USER');
    $dbPass = env('DB_PASS');
    $dbName = env('DB_NAME');
    
    if ($dbHost && $dbUser && $dbName) {
        $conn = @new mysqli($dbHost, $dbUser, $dbPass, $dbName);
        
        if ($conn->connect_error) {
            $status['database'] = 'error';
            $status['database_message'] = 'Connection failed';
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
