<?php
/**
 * Arquivo de Configuração Central
 * Carrega variáveis de ambiente do arquivo .env
 */

// Carrega o arquivo .env
function carregarEnv($caminho = __DIR__ . '/.env') {
    if (!file_exists($caminho)) {
        die("Erro: Arquivo .env não encontrado. Copie o arquivo .env.example para .env e configure as variáveis.");
    }
    
    $linhas = file($caminho, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($linhas as $linha) {
        // Ignora comentários
        if (strpos(trim($linha), '#') === 0) {
            continue;
        }
        
        // Separa chave=valor
        list($chave, $valor) = explode('=', $linha, 2);
        $chave = trim($chave);
        $valor = trim($valor);
        
        // Remove aspas se existirem
        $valor = trim($valor, '"\'');
        
        // Define como constante se ainda não existir
        if (!defined($chave)) {
            define($chave, $valor);
        }
        
        // Também adiciona ao $_ENV para compatibilidade
        $_ENV[$chave] = $valor;
        putenv("$chave=$valor");
    }
}

// Carrega as variáveis de ambiente
carregarEnv();

// Função auxiliar para pegar valores do .env com fallback
function env($chave, $padrao = null) {
    if (defined($chave)) {
        return constant($chave);
    }
    
    $valor = getenv($chave);
    if ($valor !== false) {
        return $valor;
    }
    
    return $padrao;
}

// Configurações de erro baseadas no ambiente
if (env('APP_ENV') === 'production') {
    error_reporting(0);
    ini_set('display_errors', '0');
} else {
    error_reporting(E_ALL);
    ini_set('display_errors', '1');
}

// Configurações de sessão
ini_set('session.gc_maxlifetime', env('SESSION_TIMEOUT', 3600));
ini_set('session.cookie_lifetime', env('SESSION_TIMEOUT', 3600));

// Timezone
date_default_timezone_set('America/Sao_Paulo');
