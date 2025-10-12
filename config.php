<?php
/**
 * Arquivo de Configuração Central
 * Carrega variáveis de ambiente do arquivo .env (dev) ou do ambiente (produção/Railway)
 */

// Carrega o arquivo .env apenas se existir (desenvolvimento local)
function carregarEnv($caminho = __DIR__ . '/.env') {
    // No Railway e Docker, não precisa do arquivo .env
    if (!file_exists($caminho)) {
        return; // Variáveis já estão no ambiente
    }
    
    $linhas = file($caminho, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($linhas as $linha) {
        // Ignora comentários
        if (strpos(trim($linha), '#') === 0) {
            continue;
        }
        
        // Ignora linhas sem "="
        if (strpos($linha, '=') === false) {
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

// Carrega as variáveis de ambiente (se o arquivo existir)
carregarEnv();

// Harmoniza variáveis de ambiente comuns do Railway com o padrão da aplicação
function definirEnvSeAusente($chave, $valor)
{
    if ($valor === null || $valor === false || $valor === '') {
        return;
    }

    if (!defined($chave)) {
        define($chave, $valor);
    }

    if (getenv($chave) === false) {
        putenv($chave . '=' . $valor);
    }

    $_ENV[$chave] = $valor;
}

(function () {
    $mapeamentos = [
        'DB_HOST' => ['DB_HOST', 'MYSQLHOST', 'JAWSDB_HOST'],
        'DB_PORT' => ['DB_PORT', 'MYSQLPORT', 'JAWSDB_PORT'],
        'DB_USER' => ['DB_USER', 'MYSQLUSER', 'JAWSDB_USER'],
        'DB_PASS' => ['DB_PASS', 'MYSQLPASSWORD', 'JAWSDB_PASS'],
        'DB_NAME' => ['DB_NAME', 'MYSQLDATABASE', 'JAWSDB_DB'],
    ];

    foreach ($mapeamentos as $alvo => $origens) {
        $valorExistente = defined($alvo) ? constant($alvo) : getenv($alvo);
        if ($valorExistente !== false && $valorExistente !== null && $valorExistente !== '') {
            continue;
        }

        foreach ($origens as $origem) {
            $valorOrigem = getenv($origem);
            if ($valorOrigem !== false && $valorOrigem !== null && $valorOrigem !== '') {
                definirEnvSeAusente($alvo, $valorOrigem);
                break;
            }
        }
    }

    // Railway também expõe DATABASE_URL no formato mysql://usuario:senha@host:porta/banco
    $databaseUrl = getenv('DATABASE_URL');
    if ($databaseUrl && (!getenv('DB_HOST') || !getenv('DB_USER'))) {
        $componentes = parse_url($databaseUrl);
        if ($componentes !== false) {
            definirEnvSeAusente('DB_HOST', $componentes['host'] ?? null);
            definirEnvSeAusente('DB_PORT', $componentes['port'] ?? null);
            definirEnvSeAusente('DB_USER', $componentes['user'] ?? null);
            definirEnvSeAusente('DB_PASS', $componentes['pass'] ?? null);
            if (!empty($componentes['path'])) {
                definirEnvSeAusente('DB_NAME', ltrim($componentes['path'], '/'));
            }
        }
    }
})();

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
