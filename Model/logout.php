<?php
// Arquivo simples para criar Model do logout
require_once dirname(__DIR__) . '/config.php';

iniciarSessaoSegura();

$_SESSION = [];
session_destroy();
header('Location: /conecta-uniforme/');
exit;
