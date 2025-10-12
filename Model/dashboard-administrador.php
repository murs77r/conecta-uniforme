<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Usuario.php';
require_once __DIR__ . '/../classes/Aluno.php';

iniciarSessaoSegura();

if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] !== 'Administrador') {
    header('Location: /login-novo');
    exit;
}

$usuarioClass = new Usuario();
$alunoClass = new Aluno();

$mensagem = '';
$erro = '';

// Fornecedores
if(isset($_POST['criar_fornecedor'])) {
    $dados = [
        'nome' => trim($_POST['nome'] ?? ''),
        'email' => trim($_POST['email'] ?? ''),
        'telefone' => trim($_POST['telefone'] ?? ''),
        'cnpj' => trim($_POST['cnpj'] ?? '')
    ];

    if($dados['nome'] === '' || $dados['email'] === '') {
        $erro = 'Informe nome e email para cadastrar um fornecedor.';
    } else {
        if($usuarioClass->criarFornecedor($dados)) {
            $mensagem = 'Fornecedor criado com sucesso!';
        } else {
            $erro = 'Não foi possível criar o fornecedor. Verifique se o email ou CNPJ já existem.';
        }
    }
}

if(isset($_POST['atualizar_fornecedor'])) {
    $Fornecedor_id = (int)($_POST['Fornecedor_id'] ?? 0);
    $dados = [
        'nome' => trim($_POST['nome'] ?? ''),
        'email' => trim($_POST['email'] ?? ''),
        'telefone' => trim($_POST['telefone'] ?? ''),
        'cnpj' => trim($_POST['cnpj'] ?? '')
    ];

    if($Fornecedor_id <= 0) {
        $erro = 'Fornecedor inválido.';
    } elseif($dados['nome'] === '' || $dados['email'] === '') {
        $erro = 'Nome e email são obrigatórios.';
    } else {
        if($usuarioClass->atualizarFornecedor($Fornecedor_id, $dados)) {
            $mensagem = 'Fornecedor atualizado!';
        } else {
            $erro = 'Erro ao atualizar fornecedor. Verifique os dados informados.';
        }
    }
}

if(isset($_POST['excluir_fornecedor'])) {
    $Fornecedor_id = (int)($_POST['Fornecedor_id'] ?? 0);
    if($Fornecedor_id <= 0) {
        $erro = 'Fornecedor inválido.';
    } else {
        if($usuarioClass->removerFornecedor($Fornecedor_id)) {
            $mensagem = 'Fornecedor removido.';
        } else {
            $erro = 'Erro ao remover fornecedor. Verifique se existem registros relacionados.';
        }
    }
}

// Escolas
if(isset($_POST['criar_escola'])) {
    $dados = [
        'nome' => trim($_POST['nome'] ?? ''),
        'email' => trim($_POST['email'] ?? ''),
        'cnpj' => trim($_POST['cnpj'] ?? ''),
        'telefone' => trim($_POST['telefone'] ?? ''),
        'cep' => trim($_POST['cep'] ?? ''),
        'estado' => trim($_POST['estado'] ?? ''),
        'cidade' => trim($_POST['cidade'] ?? ''),
        'endereco' => trim($_POST['endereco'] ?? ''),
        'complemento' => trim($_POST['complemento'] ?? '')
    ];

    if($dados['nome'] === '' || $dados['email'] === '' || $dados['cnpj'] === '') {
        $erro = 'Nome, email e CNPJ são obrigatórios para a escola.';
    } else {
        if($usuarioClass->criarEscola($dados)) {
            $mensagem = 'Escola criada com sucesso!';
        } else {
            $erro = 'Não foi possível criar a escola. Verifique se o email ou CNPJ já existem.';
        }
    }
}

if(isset($_POST['atualizar_escola'])) {
    $escola_id = (int)($_POST['escola_id'] ?? 0);
    $dados = [
        'nome' => trim($_POST['nome'] ?? ''),
        'email' => trim($_POST['email'] ?? ''),
        'cnpj' => trim($_POST['cnpj'] ?? ''),
        'telefone' => trim($_POST['telefone'] ?? ''),
        'cep' => trim($_POST['cep'] ?? ''),
        'estado' => trim($_POST['estado'] ?? ''),
        'cidade' => trim($_POST['cidade'] ?? ''),
        'endereco' => trim($_POST['endereco'] ?? ''),
        'complemento' => trim($_POST['complemento'] ?? '')
    ];

    if($escola_id <= 0) {
        $erro = 'Escola inválida.';
    } elseif($dados['nome'] === '' || $dados['email'] === '' || $dados['cnpj'] === '') {
        $erro = 'Preencha os campos obrigatórios da escola.';
    } else {
        if($usuarioClass->atualizarEscola($escola_id, $dados)) {
            $mensagem = 'Escola atualizada!';
        } else {
            $erro = 'Erro ao atualizar escola. Verifique os dados informados.';
        }
    }
}

if(isset($_POST['excluir_escola'])) {
    $escola_id = (int)($_POST['escola_id'] ?? 0);
    if($escola_id <= 0) {
        $erro = 'Escola inválida.';
    } else {
        if($usuarioClass->removerEscola($escola_id)) {
            $mensagem = 'Escola removida.';
        } else {
            $erro = 'Erro ao remover escola. Verifique se existem dependências.';
        }
    }
}

$fornecedores = $usuarioClass->listarFornecedores();
$escolas = $usuarioClass->listarEscolas();
$alunos = $alunoClass->listarTodos();

require __DIR__ . '/../View/dashboard-administrador.view.php';
