<?php
require_once 'conexao.php';

class Usuario {
    private $con;
    private const MAPA_TABELAS = [
        'Gestor' => 'gestor',
        'Fornecedor' => 'fornecedor',
        'Responsável' => 'responsavel',
        'Responsavel' => 'responsavel',
        'Administrador' => 'administrador',
    ];
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function verificarEmailExiste($email, $tipo) {
        $email = strtolower($this->con->real_escape_string($email));
        
        $tabela = self::MAPA_TABELAS[$tipo] ?? null;
        if(!$tabela) {
            return false;
        }
        
    $sql = "SELECT id, nome, email, ativo FROM $tabela WHERE email = '$email' AND ativo = 1";
        $result = $this->con->query($sql);
        
        if($result && $result->num_rows > 0) {
            return $result->fetch_assoc();
        }
        return false;
    }
    
    public function buscarPorEmail($email, $tipo) {
        return $this->verificarEmailExiste($email, $tipo);
    }
    
    public function criarGestor($dados) {
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone']);
        $escola_id = (int)$dados['escola_id'];
        
    $sql = "INSERT INTO gestor (nome, email, telefone, escola_id, ativo) 
                VALUES ('$nome', '$email', '$telefone', $escola_id, 1)";
        
        return $this->con->query($sql);
    }
    
    public function criarAdministrador($dados) {
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');

    $sql = "INSERT INTO administrador (nome, email, telefone, ativo)
                VALUES ('$nome', '$email', '$telefone', 1)";

        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }

    public function criarFornecedor($dados) {
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');
        $cnpj = $this->con->real_escape_string($dados['cnpj'] ?? '');
        
    $sql = "INSERT INTO fornecedor (nome, email, telefone, cnpj, ativo) 
                VALUES ('$nome', '$email', '$telefone', '$cnpj', 1)";
        
        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }

    public function atualizarFornecedor($id, $dados) {
        $id = (int)$id;
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');
        $cnpj = $this->con->real_escape_string($dados['cnpj'] ?? '');

    $sql = "UPDATE fornecedor SET nome = '$nome', email = '$email', telefone = '$telefone', cnpj = '$cnpj' WHERE id = $id";
        return $this->con->query($sql);
    }

    public function removerFornecedor($id) {
        $id = (int)$id;
    $sql = "DELETE FROM fornecedor WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function criarResponsavel($dados) {
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');
        $aluno_id = (int)$dados['aluno_id'];
        
    $sql = "INSERT INTO responsavel (nome, email, telefone, aluno_id, ativo) 
                VALUES ('$nome', '$email', '$telefone', $aluno_id, 1)";
        
        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }

    public function listarResponsaveisPorAluno($aluno_id) {
        $aluno_id = (int)$aluno_id;
    $sql = "SELECT * FROM responsavel WHERE aluno_id = $aluno_id ORDER BY nome";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }

    public function atualizarResponsavel($id, $dados) {
        $id = (int)$id;
        $nome = $this->con->real_escape_string($dados['nome']);
        $email = $this->con->real_escape_string($dados['email']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');

    $sql = "UPDATE responsavel SET nome = '$nome', email = '$email', telefone = '$telefone' WHERE id = $id";
        return $this->con->query($sql);
    }

    public function removerResponsavel($id) {
        $id = (int)$id;
    $sql = "DELETE FROM responsavel WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function listarGestoresPorEscola($escola_id) {
        $escola_id = (int)$escola_id;
    $sql = "SELECT * FROM gestor WHERE escola_id = $escola_id ORDER BY nome";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarFornecedores() {
    $sql = "SELECT * FROM fornecedor ORDER BY nome";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }

    public function listarEscolas() {
        $sql = "SELECT * FROM escola ORDER BY nome";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }

    public function criarEscola($dados) {
        $email = $this->con->real_escape_string($dados['email']);
        $nome = $this->con->real_escape_string($dados['nome']);
        $cnpj = $this->con->real_escape_string($dados['cnpj']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');
        $cep = $this->con->real_escape_string($dados['cep'] ?? '');
        $estado = $this->con->real_escape_string($dados['estado'] ?? '');
        $cidade = $this->con->real_escape_string($dados['cidade'] ?? '');
        $endereco = $this->con->real_escape_string($dados['endereco'] ?? '');
        $complemento = $this->con->real_escape_string($dados['complemento'] ?? '');

        $sql = "INSERT INTO escola (email, nome, cnpj, telefone, cep, estado, cidade, endereco, complemento, ativo)
                VALUES ('$email', '$nome', '$cnpj', '$telefone', '$cep', '$estado', '$cidade', '$endereco', '$complemento', 1)";

        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }

    public function atualizarEscola($id, $dados) {
        $id = (int)$id;
        $email = $this->con->real_escape_string($dados['email']);
        $nome = $this->con->real_escape_string($dados['nome']);
        $cnpj = $this->con->real_escape_string($dados['cnpj']);
        $telefone = $this->con->real_escape_string($dados['telefone'] ?? '');
        $cep = $this->con->real_escape_string($dados['cep'] ?? '');
        $estado = $this->con->real_escape_string($dados['estado'] ?? '');
        $cidade = $this->con->real_escape_string($dados['cidade'] ?? '');
        $endereco = $this->con->real_escape_string($dados['endereco'] ?? '');
        $complemento = $this->con->real_escape_string($dados['complemento'] ?? '');

        $sql = "UPDATE escola SET email = '$email', nome = '$nome', cnpj = '$cnpj', telefone = '$telefone', cep = '$cep', estado = '$estado', cidade = '$cidade', endereco = '$endereco', complemento = '$complemento' WHERE id = $id";
        return $this->con->query($sql);
    }

    public function removerEscola($id) {
        $id = (int)$id;
        $sql = "DELETE FROM escola WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function ativarDesativar($id, $tipo, $status) {
        $id = (int)$id;
        $status = $status ? 1 : 0;
        
        $tabela = self::MAPA_TABELAS[$tipo] ?? null;
        if(!$tabela) {
            return false;
        }

        $sql = "UPDATE $tabela SET ativo = $status WHERE id = $id";
        return $this->con->query($sql);
    }
}
