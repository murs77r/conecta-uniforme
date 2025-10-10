<div id="div-login">
    <button onclick='carregarForm(1)'>Escola</button>
    <button onclick='carregarForm(2)'>Aluno</button>
</div>
<script>
    const divLogin = document.getElementById("div-login");
    function carregarForm (tipo) {
        if (tipo == 1) {
            divLogin.innerHTML = `
            Email: <input type="email" name="email" required><br>
            Senha: <input type="password" name="senha" required>
            `;
        } else {
            divLogin.innerHTML = `
            Código de acesso da escola: <input type="text" name="codacesso" required>
            `;
        }
    }
</script>