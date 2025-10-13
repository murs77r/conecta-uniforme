<!-- TODO Yuri: transformar este cabeçalho em um `navbar navbar-expand-lg navbar-dark bg-primary` do Bootstrap.
	- Remover os estilos inline e substituí-los por classes utilitárias (padding, margens, tipografia).
	- Incluir o botão hamburguer para mobile e usar `.container` para limitar a largura.
	- Ajustar os links para usar `.nav-link` e `.navbar-brand` mantendo a identidade visual. -->
<?php
$userTipo = $_SESSION['user_tipo'] ?? null;
$userNome = $_SESSION['user_nome'] ?? null;
$destinos = [
	'Gestor' => '/dashboard-gestor',
	'Fornecedor' => '/dashboard-fornecedor',
	'Responsável' => '/dashboard-responsavel',
	'Administrador' => '/dashboard-administrador',
];
?>
<header style="background:#0d6efd;color:#fff;padding:1.5rem 0;margin-bottom:2rem;">
	<div style="max-width:960px;margin:0 auto;padding:0 1rem;display:flex;align-items:center;justify-content:space-between;">
		<a href="/" style="color:#fff;font-weight:600;font-size:1.25rem;text-decoration:none;">
			Conecta Uniforme
		</a>
		<nav style="display:flex;gap:1rem;align-items:center;">
			<?php if($userTipo && isset($destinos[$userTipo])): ?>
				<span style="font-size:0.95rem;">Olá, <?= htmlspecialchars($userNome ?? 'Usuário') ?></span>
				<a href="<?= $destinos[$userTipo] ?>" style="color:#fff;text-decoration:none;">Dashboard</a>
				<a href="/logout" style="color:#fff;text-decoration:none;">Sair</a>
			<?php else: ?>
				<a href="/login-novo" style="color:#fff;text-decoration:none;">Login</a>
			<?php endif; ?>
		</nav>
	</div>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,opsz,wdth,wght,YTLC@0,6..12,75..125,200..1000,440..540;1,6..12,75..125,200..1000,440..540&display=swap" rel="stylesheet">
    <style>
        body {margin: 0!important; font-family: "Nunito Sans", sans-serif;}
    </style>
</header>
<!-- TODO Yuri: envolver o conteúdo em um `.container` ou `.container-fluid` conforme a página precisar,
	 aplicando utilitários como `.py-4`/`.pb-5` no lugar destas dimensões fixas. -->
<main style="max-width:960px;margin:0 auto;padding:0 1rem 3rem;">
