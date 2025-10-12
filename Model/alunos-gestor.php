<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Aluno.php';
require_once __DIR__ . '/../classes/Usuario.php';
require_once __DIR__ . '/../classes/Escola.php';
iniciarSessaoSegura();

// Verificar se está logado como Gestor
if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] != 'Gestor') {
    header('Location: /login-novo');
    exit;
}

$alunoClass = new Aluno();
$usuario = new Usuario();

$escola_id = $_SESSION['escola_id'];

$mensagem = '';
$erro = '';
$responsaveis_aluno = [];

// Adicionar aluno individual
if(isset($_POST['adicionar_aluno'])) {
    $dados = [
        'nome' => $_POST['nome'],
        'matricula' => $_POST['matricula'],
        'escola_id' => $escola_id,
        'serie' => $_POST['serie'],
        'genero' => $_POST['genero']
    ];
    
    $aluno_id = $alunoClass->criar($dados);
    
    if($aluno_id) {
        // Criar responsável se fornecido
        if(!empty($_POST['Responsável_nome']) && !empty($_POST['Responsável_email'])) {
            $dados_resp = [
                'nome' => $_POST['Responsável_nome'],
                'email' => $_POST['Responsável_email'],
                'telefone' => $_POST['Responsável_telefone'] ?? '',
                'aluno_id' => $aluno_id
            ];
            
            $usuario->criarResponsavel($dados_resp);
        }
        
        $mensagem = 'Aluno adicionado com sucesso!';
    } else {
        $erro = 'Erro ao adicionar aluno. Verifique se a matrícula já não existe.';
    }
}

// Importar alunos em lote (CSV)
if(isset($_POST['importar_csv']) && isset($_FILES['arquivo_csv'])) {
    $arquivo = $_FILES['arquivo_csv']['tmp_name'];
    
    if($arquivo) {
        $handle = fopen($arquivo, 'r');
        $header = fgetcsv($handle); // Primeira linha (cabeçalho)
        
        $alunos_array = [];
        while(($row = fgetcsv($handle)) !== false) {
            // Espera-se: nome, matricula, serie, genero, Responsável_nome, Responsável_email, Responsável_telefone
            if(count($row) >= 4) {
                $alunos_array[] = [
                    'nome' => $row[0],
                    'matricula' => $row[1],
                    'serie' => $row[2],
                    'genero' => $row[3],
                    'Responsável_nome' => $row[4] ?? '',
                    'Responsável_email' => $row[5] ?? '',
                    'Responsável_telefone' => $row[6] ?? ''
                ];
            }
        }
        fclose($handle);
        
        // Importar
        $inseridos = 0;
        $erros_import = [];
        
        foreach($alunos_array as $dados_aluno) {
            $dados = [
                'nome' => $dados_aluno['nome'],
                'matricula' => $dados_aluno['matricula'],
                'escola_id' => $escola_id,
                'serie' => $dados_aluno['serie'],
                'genero' => $dados_aluno['genero']
            ];
            
            $aluno_id = $alunoClass->criar($dados);
            
            if($aluno_id) {
                $inseridos++;
                
                // Criar responsável se fornecido
                if(!empty($dados_aluno['Responsável_email'])) {
                    $dados_resp = [
                        'nome' => $dados_aluno['Responsável_nome'],
                        'email' => $dados_aluno['Responsável_email'],
                        'telefone' => $dados_aluno['Responsável_telefone'],
                        'aluno_id' => $aluno_id
                    ];
                    
                    $usuario->criarResponsavel($dados_resp);
                }
            } else {
                $erros_import[] = $dados_aluno['matricula'];
            }
        }
        
        $mensagem = "Importados $inseridos alunos com sucesso!";
        if(count($erros_import) > 0) {
            $erro = "Erros nas matrículas: " . implode(', ', $erros_import);
        }
    }
}

// Editar aluno
if(isset($_POST['editar_aluno'])) {
    $aluno_id = $_POST['aluno_id'];
    $dados = [
        'nome' => $_POST['nome'],
        'serie' => $_POST['serie'],
        'genero' => $_POST['genero']
    ];
    
    if($alunoClass->atualizar($aluno_id, $dados)) {
        $responsaveisDados = $_POST['responsaveis'] ?? [];
        foreach($responsaveisDados as $resp_id => $resp_info) {
            $resp_id = (int)$resp_id;
            if($resp_id <= 0) {
                continue;
            }

            $remover = isset($resp_info['remover']) && $resp_info['remover'] == '1';
            if($remover) {
                if(!$usuario->removerResponsavel($resp_id)) {
                    $erro = 'Erro ao remover responsável.';
                }
                continue;
            }

            $nome_resp = trim($resp_info['nome'] ?? '');
            $email_resp = trim($resp_info['email'] ?? '');
            $telefone_resp = trim($resp_info['telefone'] ?? '');

            if($nome_resp === '' || $email_resp === '') {
                $erro = 'Nome e email do responsável são obrigatórios.';
                continue;
            }

            if(!$usuario->atualizarResponsavel($resp_id, [
                'nome' => $nome_resp,
                'email' => $email_resp,
                'telefone' => $telefone_resp
            ])) {
                $erro = 'Erro ao atualizar responsável. Verifique se o email já está em uso.';
            }
        }

        $novoResponsavel = $_POST['novo_responsavel'] ?? null;
        if($novoResponsavel) {
            $nomeNovo = trim($novoResponsavel['nome'] ?? '');
            $emailNovo = trim($novoResponsavel['email'] ?? '');
            $telefoneNovo = trim($novoResponsavel['telefone'] ?? '');

            if($nomeNovo || $emailNovo || $telefoneNovo) {
                if($nomeNovo === '' || $emailNovo === '') {
                    $erro = 'Para adicionar um novo responsável, informe nome e email.';
                } else {
                    if(!$usuario->criarResponsavel([
                        'nome' => $nomeNovo,
                        'email' => $emailNovo,
                        'telefone' => $telefoneNovo,
                        'aluno_id' => $aluno_id
                    ])) {
                        $erro = 'Erro ao adicionar novo responsável. Verifique se o email já está cadastrado.';
                    }
                }
            }
        }

        if($erro === '') {
            $mensagem = 'Aluno e responsáveis atualizados!';
        } else {
            $mensagem = 'Aluno atualizado com avisos. Confira os responsáveis.';
        }

        $aluno_editando = $alunoClass->buscarPorId($aluno_id);
        $responsaveis_aluno = $usuario->listarResponsaveisPorAluno($aluno_id);
    } else {
        $erro = 'Erro ao atualizar aluno.';
    }
}

// Ativar/Desativar aluno
if(isset($_POST['toggle_aluno'])) {
    $aluno_id = $_POST['aluno_id'];
    $status = $_POST['status'];
    
    if($alunoClass->ativarDesativar($aluno_id, $status)) {
        $mensagem = 'Status atualizado!';
    } else {
        $erro = 'Erro ao atualizar status.';
    }
}

// Buscar alunos
$alunos = $alunoClass->listarPorEscola($escola_id);

// Buscar aluno específico se editando
$aluno_editando = null;
if(isset($_GET['editar'])) {
    $aluno_id = (int)$_GET['editar'];
    $aluno_editando = $alunoClass->buscarPorId($aluno_id);
    if($aluno_editando) {
        $responsaveis_aluno = $usuario->listarResponsaveisPorAluno($aluno_id);
    }
}

require __DIR__ . '/../View/alunos-gestor.view.php';
