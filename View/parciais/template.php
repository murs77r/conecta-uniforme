<?php
$templateIniciouBuffer = false;
if (ob_get_level() === 0) {
	ob_start();
	$templateIniciouBuffer = true;
}

require 'head.php'; // lugar pra colocar qualquer include que precisa em todas as páginas, tipo conexão do banco de dados
?>
<!-- TODO Yuri: avaliar criação de layouts específicos (ex.: dashboard vs. público) usando seções do Bootstrap.
	- Caso surjam grids complexos, considere extrair para partials adicionais ou usar `@yield`-like manual com PHP.
	- Este template deve ficar responsável apenas por montar as regiões fixas (navbar, conteúdo, footer). -->
<?php require 'header.php'; ?>
<?php require __DIR__.'/../..'.$caminho_counteudo; ?>
<?php
require 'footer.php';

if ($templateIniciouBuffer && ob_get_level() > 0) {
	ob_end_flush();
}
?>