<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/conexao.php';
require_once __DIR__ . '/funcoes.php';

iniciarSessaoSegura();

$pageTitle = $pageTitle ?? 'Conecta Uniforme';
$pageDescription = $pageDescription ?? 'Plataforma para gestão e compra de uniformes escolares.';
$pageCharset = $pageCharset ?? 'UTF-8';
$pageLanguage = $pageLanguage ?? 'pt-BR';

?>
<!DOCTYPE html>
<html lang="<?= htmlspecialchars($pageLanguage, ENT_QUOTES, 'UTF-8') ?>">
<head>
	<meta charset="<?= htmlspecialchars($pageCharset, ENT_QUOTES, 'UTF-8') ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="description" content="<?= htmlspecialchars($pageDescription, ENT_QUOTES, 'UTF-8') ?>">
	<title><?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?></title>
</head>
<body>
