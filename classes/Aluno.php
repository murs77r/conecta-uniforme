<?php
require_once 'conexao.php';

class Aluno {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function criar($dados) {
        $nome = $this->con->real_escape_string($dados['nome']);
        $matricula = $this->con->real_escape_string($dados['matricula']);
        $escola_id = (int)$dados['escola_id'];
        $serie = $this->con->real_escape_string($dados['serie']);
        $genero = $this->con->real_escape_string($dados['genero']);
        
        $sql = "INSERT INTO aluno (nome, matricula, escola_id, serie, genero, ativo) 
                VALUES ('$nome', '$matricula', $escola_id, '$serie', '$genero', 1)";
        
        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }
    
    public function buscarPorId($id) {
        $id = (int)$id;
        $sql = "SELECT a.*, e.nome as escola_nome 
                FROM aluno a
                INNER JOIN escola e ON a.escola_id = e.id
                WHERE a.id = $id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_assoc() : null;
    }
    
    public function buscarPorMatricula($matricula, $escola_id) {
        $matricula = $this->con->real_escape_string($matricula);
        $escola_id = (int)$escola_id;
        
        $sql = "SELECT * FROM aluno WHERE matricula = '$matricula' AND escola_id = $escola_id";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_assoc() : null;
    }
    
    public function listarPorEscola($escola_id) {
        $escola_id = (int)$escola_id;
        
        $sql = "SELECT a.*, 
                (SELECT COUNT(*) FROM responsavel WHERE aluno_id = a.id) as total_responsaveis
                FROM aluno a
                WHERE a.escola_id = $escola_id
                ORDER BY a.serie, a.nome";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function importarLote($escola_id, $alunos_array) {
        $inseridos = 0;
        $erros = [];
        
        foreach($alunos_array as $aluno) {
            $resultado = $this->criar(array_merge($aluno, ['escola_id' => $escola_id]));
            if($resultado) {
                $inseridos++;
            } else {
                $erros[] = $aluno['matricula'] . ' - ' . $this->con->error;
            }
        }
        
        return [
            'inseridos' => $inseridos,
            'erros' => $erros
        ];
    }
    
    public function atualizar($id, $dados) {
        $id = (int)$id;
        $nome = $this->con->real_escape_string($dados['nome']);
        $serie = $this->con->real_escape_string($dados['serie']);
        $genero = $this->con->real_escape_string($dados['genero']);
        
        $sql = "UPDATE aluno SET nome = '$nome', serie = '$serie', genero = '$genero' WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function ativarDesativar($id, $status) {
        $id = (int)$id;
        $status = $status ? 1 : 0;
        $sql = "UPDATE aluno SET ativo = $status WHERE id = $id";
        return $this->con->query($sql);
    }
}
