<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Usuario.php';
require_once __DIR__ . '/../classes/CodigoAcesso.php';

iniciarSessaoSegura();

$usuario = new Usuario();
$codigoAcesso = new CodigoAcesso();

$mensagem = '';
$erro = '';
$step = 'email'; // email ou codigo

if(isset($_POST['enviar_email'])) {
    $email = $_POST['email'] ?? '';
    $tipo = $_POST['tipo_usuario'] ?? '';
    
    if(empty($email) || empty($tipo)) {
        $erro = 'Preencha todos os campos';
    } else {
        // Verificar se o email existe
        $user = $usuario->verificarEmailExiste($email, $tipo);
        
        if($user) {
            // Gerar e enviar código
            $resultado = $codigoAcesso->criarCodigo($email, $tipo);
            
            if($resultado) {
                $enviado = $codigoAcesso->enviarCodigoPorEmail($email, $resultado['codigo']);
                
                if($enviado) {
                    $_SESSION['login_email'] = $email;
                    $_SESSION['login_tipo'] = $tipo;
                    $step = 'codigo';
                    $mensagem = 'Código enviado para seu email! Verifique sua caixa de entrada.';
                } else {
                    $erro = 'Erro ao enviar email. Tente novamente.';
                }
            } else {
                $erro = 'Erro ao gerar código. Tente novamente.';
            }
        } else {
            $erro = 'Email não cadastrado ou usuário inativo.';
        }
    }
}

if(isset($_POST['validar_codigo'])) {
    $email = $_SESSION['login_email'] ?? '';
    $tipo = $_SESSION['login_tipo'] ?? '';
    $codigo = $_POST['codigo'] ?? '';
    
    if(empty($codigo)) {
        $erro = 'Digite o código recebido';
        $step = 'codigo';
    } else {
        $validacao = $codigoAcesso->validarCodigo($email, $codigo);
        
        if($validacao) {
            // Buscar dados completos do usuário
            $user = $usuario->buscarPorEmail($email, $tipo);
            
            if($user) {
                // Criar sessão
                $_SESSION['user_id'] = $user['id'];
                $_SESSION['user_email'] = $user['email'];
                $_SESSION['user_nome'] = $user['nome'];
                $_SESSION['user_tipo'] = $tipo;
                $_SESSION['logado'] = true;
                
                // Redirecionar para dashboard apropriado
                switch($tipo) {
                    case 'gestor':
                        header('Location: /dashboard-gestor');
                        exit;
                    case 'fornecedor':
                        header('Location: /dashboard-fornecedor');
                        exit;
                    case 'responsavel':
                        header('Location: /dashboard-responsavel');
                        exit;
                }
            }
        } else {
            $erro = 'Código inválido ou expirado.';
            $step = 'codigo';
        }
    }
}

if(isset($_POST['reenviar_codigo'])) {
    $email = $_SESSION['login_email'] ?? '';
    $tipo = $_SESSION['login_tipo'] ?? '';
    
    if($email && $tipo) {
        $resultado = $codigoAcesso->criarCodigo($email, $tipo);
        
        if($resultado) {
            $enviado = $codigoAcesso->enviarCodigoPorEmail($email, $resultado['codigo']);
            
            if($enviado) {
                $mensagem = 'Novo código enviado!';
                $step = 'codigo';
            } else {
                $erro = 'Erro ao enviar email.';
                $step = 'codigo';
            }
        }
    }
}

// Verificar se já está na etapa de código
if(isset($_SESSION['login_email']) && !isset($_POST['enviar_email'])) {
    $step = 'codigo';
}

require __DIR__ . '/../View/login-novo.view.php';
