<?php
if (session_status() === PHP_SESSION_NONE) {
	session_start();
}

require_once __DIR__ . '/conexao.php';
require_once __DIR__ . '/funcoes.php';