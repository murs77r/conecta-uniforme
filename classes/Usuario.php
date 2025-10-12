<?php
require_once 'conexao.php';

class Usuario {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function verificarEmailExiste($email, $tipo) {
        $email = $this->con->real_escape_string($email);
        
        $tabela = '';
        switch($tipo) {
            case 'gestor':
                $tabela = 'gestor';
                break;
            case 'fornecedor':
                $tabela = 'fornecedor';
                break;
            case 'responsavel':
                $tabela = 'responsavel';
                break;
            default:
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
    
    public function ativarDesativar($id, $tipo, $status) {
        $id = (int)$id;
        $status = $status ? 1 : 0;
        
        $tabela = $tipo == 'gestor' ? 'gestor' : 'fornecedor';
        
        $sql = "UPDATE $tabela SET ativo = $status WHERE id = $id";
        return $this->con->query($sql);
    }
}
