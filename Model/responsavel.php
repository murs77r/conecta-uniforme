<?php
// Cadastro simplificado de Responsável (Pai/Aluno)
require_once __DIR__ . '/../funcoes.php';
require_once __DIR__ . '/../classes/Responsavel.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = $_POST['nome'] ?? '';
    $email = $_POST['email'] ?? '';
    $telefone = $_POST['telefone'] ?? '';
    $escola_id = intval($_POST['escola_id'] ?? 0);
    $matricula = trim($_POST['matricula'] ?? '');

    // validações básicas
    $errors = [];
    if (empty($nome)) $errors[] = 'Nome é obrigatório.';
    if (empty($email)) $errors[] = 'Email é obrigatório.';
    if ($escola_id <= 0) $errors[] = 'Escola inválida.';
    if (empty($matricula)) $errors[] = 'Matrícula inválida.';

    if (empty($errors)) {
        // cria responsavel na tabela responsavel
        $senha_temp = bin2hex(random_bytes(4));
        $resp = new Responsavel($nome, $email, $telefone, $senha_temp, $escola_id, $matricula);
        $resultado = $resp->salvar();
        if (is_string($resultado) && strpos($resultado, 'Erro:') === 0) {
            $errors[] = $resultado;
        } else {
            $success = "Responsável cadastrado com sucesso. Senha temporária: $senha_temp";
        }
    }
}

// Busca dados para formulário
$escolas = consulta_sql('SELECT id, nome FROM escola');
// sem tabela de alunos; o frontend deve coletar matrícula fornecida pela escola

include __DIR__ . '/../View/responsavel.view.php';
