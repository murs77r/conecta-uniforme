<!-- TODO Yuri: transformar este cabeçalho em um `navbar navbar-expand-lg navbar-dark bg-primary` do Bootstrap.
	- Remover os estilos inline e substituí-los por classes utilitárias (padding, margens, tipografia).
	- Incluir o botão hamburguer para mobile e usar `.container` para limitar a largura.
	- Ajustar os links para usar `.nav-link` e `.navbar-brand` mantendo a identidade visual. -->
<header style="background:#0d6efd;color:#fff;padding:1.5rem 0;margin-bottom:2rem;">
	<div style="max-width:960px;margin:0 auto;padding:0 1rem;display:flex;align-items:center;justify-content:space-between;">
		<a href="/" style="color:#fff;font-weight:600;font-size:1.25rem;text-decoration:none;">
			Conecta Uniforme
		</a>
		<nav>
			<a href="/login-novo" style="color:#fff;margin-right:1rem;text-decoration:none;">Login</a>
			<a href="/cadastro" style="color:#fff;text-decoration:none;">Cadastro</a>
		</nav>
	</div>
</header>
<!-- TODO Yuri: envolver o conteúdo em um `.container` ou `.container-fluid` conforme a página precisar,
	 aplicando utilitários como `.py-4`/`.pb-5` no lugar destas dimensões fixas. -->
<main style="max-width:960px;margin:0 auto;padding:0 1rem 3rem;">