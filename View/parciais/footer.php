<!-- TODO Yuri: substituir este rodapé por um componente flexível usando `.bg-light`, `.text-muted` e espaçamentos do Bootstrap.
	- Remover estilos inline, aplicar `.py-4` e `.mt-4`.
	- Avaliar uso de `.d-flex` para centralizar conteúdo e incluir ícones (Font Awesome/Bootstrap Icons) quando estiverem disponíveis.
	- Garantir que o bundle JS do Bootstrap (adicionado no footer) venha antes do fechamento de </body>. -->
</main>
<footer style="background:#f4f6fb;color:#495057;padding:2rem 0;margin-top:2rem;">
	<div style="max-width:960px;margin:0 auto;padding:0 1rem;text-align:center;font-size:0.9rem;">
		<p>&copy; <?= date('Y') ?> Conecta Uniforme. Todos os direitos reservados.</p>
		<p><a href="mailto:suporte@conectauniforme.com" style="color:#0d6efd;text-decoration:none;">suporte@conectauniforme.com</a></p>
	</div>
</footer>
</body>
</html>