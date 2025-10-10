<div id="div-login">
    <button onclick='carregarForm(1)'>Escola</button>
    <button onclick='carregarForm(2)'>Aluno</button>
</div>
<script>
    const divLogin = document.getElementById("div-login");
    function carregarForm (tipo) {
        if (tipo == 1) {
            divLogin.innerHTML = `
            <form method="post">
                Email: <input type="email" name="email" required><br>
                Senha: <input type="password" name="senha" required>
                <input type="hidden" name="tipo_login" value='1'>
                <input type="submit" value="Login">
            </form>
            `;
        } else {
            divLogin.innerHTML = `
            <form method="post">
                Código de acesso da escola: <input type="text" name="codacesso" required>
                <input type="hidden" name="tipo_login" value='2'>
                <input type="submit" value="Login">
            </form>
            `;
        }
    }
</script>