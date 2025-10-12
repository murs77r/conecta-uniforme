<?php
require_once 'conexao.php';

class Homologacao {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function criar($escola_id, $Fornecedor_id) {
        $escola_id = (int)$escola_id;
        $Fornecedor_id = (int)$Fornecedor_id;
        
        $sql = "INSERT INTO homologacao (escola_id, Fornecedor_id, ativo) 
                VALUES ($escola_id, $Fornecedor_id, 1)
                ON DUPLICATE KEY UPDATE ativo = 1, data_homologacao = CURRENT_TIMESTAMP";
        
        return $this->con->query($sql);
    }
    
    public function remover($escola_id, $Fornecedor_id) {
        $escola_id = (int)$escola_id;
        $Fornecedor_id = (int)$Fornecedor_id;
        
        $sql = "UPDATE homologacao SET ativo = 0 WHERE escola_id = $escola_id AND Fornecedor_id = $Fornecedor_id";
        return $this->con->query($sql);
    }
    
    public function listarFornecedoresHomologados($escola_id) {
        $escola_id = (int)$escola_id;
        
        $sql = "SELECT f.*, h.data_homologacao, h.ativo
                FROM Fornecedor f
                INNER JOIN homologacao h ON f.id = h.Fornecedor_id
                WHERE h.escola_id = $escola_id
                ORDER BY f.nome";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarFornecedoresDisponiveis($escola_id) {
        $escola_id = (int)$escola_id;
        
        $sql = "SELECT f.*
                FROM Fornecedor f
                WHERE f.ativo = 1
                AND f.id NOT IN (
                    SELECT Fornecedor_id FROM homologacao 
                    WHERE escola_id = $escola_id AND ativo = 1
                )
                ORDER BY f.nome";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function verificarHomologacao($escola_id, $Fornecedor_id) {
        $escola_id = (int)$escola_id;
        $Fornecedor_id = (int)$Fornecedor_id;
        
        $sql = "SELECT * FROM homologacao 
                WHERE escola_id = $escola_id AND Fornecedor_id = $Fornecedor_id AND ativo = 1";
        
        $result = $this->con->query($sql);
        return $result && $result->num_rows > 0;
    }
}
