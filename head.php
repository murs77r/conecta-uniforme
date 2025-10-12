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
<!-- TODO Yuri: substituir os estilos inline por classes utilitárias do Bootstrap e carregar os assets aqui.
	1. Adicionar o link do Bootstrap CSS (v5.x) antes de quaisquer estilos customizados.
	2. Incluir o bundle JS do Bootstrap (com Popper) antes do fechamento do <body> no footer.
	3. Centralizar regras próprias em um CSS separado, mantendo este arquivo apenas para imports globais. -->
<!DOCTYPE html>
<html lang="<?= htmlspecialchars($pageLanguage, ENT_QUOTES, 'UTF-8') ?>">
<head>
	<meta charset="<?= htmlspecialchars($pageCharset, ENT_QUOTES, 'UTF-8') ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="description" content="<?= htmlspecialchars($pageDescription, ENT_QUOTES, 'UTF-8') ?>">
	<title><?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?></title>
</head>
<body>
