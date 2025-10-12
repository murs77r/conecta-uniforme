<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../funcoes.php';

if (session_status() == PHP_SESSION_NONE) session_start();

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $tipo = intval($_POST['tipo_login'] ?? 0);
    $sucesso_login = false;
    $id = null;

    if ($tipo === 1) { // Escola: email + senha (senha em `escola.senha`)
        $email = $_POST['email'] ?? '';
        $senha = $_POST['senha'] ?? '';
+
        if ($email && $senha) {
            $stmt = $con->prepare('SELECT id, senha FROM escola WHERE email = ? LIMIT 1');
            $stmt->bind_param('s', $email);
            $stmt->execute();
            $res = $stmt->get_result()->fetch_assoc();
            if ($res) {
                $hash = $res['senha'];
                <?php
                require_once __DIR__ . '/../conexao.php';
                require_once __DIR__ . '/../funcoes.php';
                require_once __DIR__ . '/../classes/Fornecedor.php';
                require_once __DIR__ . '/../classes/Responsavel.php';

                if (session_status() == PHP_SESSION_NONE) session_start();

                $error = '';
                if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                    $tipo = intval($_POST['tipo_login'] ?? 0);
                    $sucesso_login = false;
                    $id = null;

                    if ($tipo === 1) { // Gestor Escolar (escola table)
                        $email = $_POST['email'] ?? '';
                        $senha = $_POST['senha'] ?? '';
                        if ($email && $senha) {
                            $stmt = $con->prepare('SELECT id, senha FROM escola WHERE email = ? LIMIT 1');
                            $stmt->bind_param('s', $email);
                            $stmt->execute();
                            $res = $stmt->get_result()->fetch_assoc();
                            if ($res) {
                                $hash = $res['senha'];
                                if ($hash && strlen($hash) >= 60) {
                                    if (password_verify($senha, $hash)) { $sucesso_login = true; $id = $res['id']; $_SESSION['role'] = 'Gestor'; }
                                } else {
                                    if (hash_equals(hash('sha256', $senha), $hash)) { $sucesso_login = true; $id = $res['id']; $_SESSION['role'] = 'Gestor'; }
                                }
                            }
                        }

                    } else if ($tipo === 2) { // Aluno (acesso por código)
                        $cod_acesso = $_POST['codacesso'] ?? '';
                        if ($cod_acesso) {
                            $stmt = $con->prepare('SELECT id FROM escola WHERE cod_acesso = ? LIMIT 1');
                            $stmt->bind_param('s', $cod_acesso);
                            $stmt->execute();
                            $res = $stmt->get_result()->fetch_assoc();
                            if ($res) { $sucesso_login = true; $id = $res['id']; $_SESSION['role'] = 'aluno'; }
                        }

                    } else if ($tipo === 3) { // Responsável: login por codigo_escola + matricula + senha
                        $codigo_escola = $_POST['codigo_escola'] ?? '';
                        $matricula = $_POST['matricula'] ?? '';
                        $senha = $_POST['senha'] ?? '';
                        if ($codigo_escola && $matricula && $senha) {
                            $res_id = \Responsavel::autenticarPorCodigoEMatricula($codigo_escola, $matricula, $senha);
                            if ($res_id !== false) { $sucesso_login = true; $id = $res_id; $_SESSION['role'] = 'Responsável'; }
                        }

                    } else if ($tipo === 4) { // Fornecedor (tabela Fornecedor)
                        $email = $_POST['email'] ?? '';
                        $senha = $_POST['senha'] ?? '';
                        if ($email && $senha) {
                            $for_id = Fornecedor::autenticar($email, $senha);
                            if ($for_id !== false) { $sucesso_login = true; $id = $for_id; $_SESSION['role'] = 'Fornecedor'; }
                        }
                    }

                    if ($sucesso_login) {
                        $_SESSION['user_id'] = $id;
                        $_SESSION['tipo_usuario'] = $tipo;
                        header('Location: '.'/catalogo');
                        exit;
                    } else {
                        $error = 'Credenciais inválidas ou conta inativa.';
                    }
                }

                include __DIR__ . '/../View/login.view.php';

                ?>
