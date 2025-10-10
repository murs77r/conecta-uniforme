<?php 

 // OS COMENTARIOS SÃO INSTRUÇÕES DO QUE FAZER !!
 // uma coisa que esqueci de fazer é fazer com que na hora de criar cadastro, ele confira se o email já existe no banco. Não sei se o edilberto vai implicar.

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $tipo = $_POST['tipo_login'];
    if ($tipo == 1) {
        $email = $_POST['email'];
        $senha = $_POST['senha'];

        $id = 0; // tira isso e consulta o ID da escola baseado no email e senha e coloca em uma variavel.
        $sucesso_login = true;

        // se a consulta não retornar nada, coloca $sucesso_login = false;
    } else if ($tipo == 2) {
        $cod_acesso = $_POST['codacesso'];

        $id = 0; // tira isso e consulta o ID da escola baseado no codigo de acesso e coloca em uma variavel.
        $sucesso_login = true;

        // se a consulta não retornar nada, coloca $sucesso_login = false;
    }

    if ($sucesso_login) {
        $_SESSION['id_escola'] = $id;
        $_SESSION['tipo_usuario'] = $tipo;
        header('Location: '.'/conecta-uniforme/catalogo');
    }
}

include 'View/login.view.php';
