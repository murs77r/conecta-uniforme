<?php
require_once 'conexao.php';

class Produto {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function criar($dados) {
        $fornecedor_id = (int)$dados['fornecedor_id'];
        $nome = $this->con->real_escape_string($dados['nome']);
        $descricao = $this->con->real_escape_string($dados['descricao'] ?? '');
        $preco = (float)$dados['preco'];
        
    $sql = "INSERT INTO produto (fornecedor_id, nome, descricao, preco, ativo) 
        VALUES ($fornecedor_id, '$nome', '$descricao', $preco, 1)";
        
        if($this->con->query($sql)) {
            return $this->con->insert_id;
        }
        return false;
    }
    
    public function atualizar($id, $dados) {
        $id = (int)$id;
        $nome = $this->con->real_escape_string($dados['nome']);
        $descricao = $this->con->real_escape_string($dados['descricao'] ?? '');
        $preco = (float)$dados['preco'];
        
        $sql = "UPDATE produto SET nome = '$nome', descricao = '$descricao', preco = $preco WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function ativarDesativar($id, $status) {
        $id = (int)$id;
        $status = $status ? 1 : 0;
        $sql = "UPDATE produto SET ativo = $status WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function homologarProduto($produto_id, $escola_id, $serie) {
        $produto_id = (int)$produto_id;
        $escola_id = (int)$escola_id;
        $serie = $this->con->real_escape_string($serie);
        
        $sql = "INSERT IGNORE INTO produto_homologacao (produto_id, escola_id, serie) 
                VALUES ($produto_id, $escola_id, '$serie')";
        
        return $this->con->query($sql);
    }
    
    public function removerHomologacao($produto_id, $escola_id, $serie) {
        $produto_id = (int)$produto_id;
        $escola_id = (int)$escola_id;
        $serie = $this->con->real_escape_string($serie);
        
        $sql = "DELETE FROM produto_homologacao 
                WHERE produto_id = $produto_id AND escola_id = $escola_id AND serie = '$serie'";
        
        return $this->con->query($sql);
    }
    
    public function adicionarVariacao($produto_id, $dados) {
        $produto_id = (int)$produto_id;
        $tamanho = $this->con->real_escape_string($dados['tamanho']);
        $cor = $this->con->real_escape_string($dados['cor'] ?? '');
        $genero = $this->con->real_escape_string($dados['genero']);
        $quantidade = (int)($dados['quantidade_estoque'] ?? 0);
        
        $sql = "INSERT INTO produto_variacao (produto_id, tamanho, cor, genero, quantidade_estoque) 
                VALUES ($produto_id, '$tamanho', '$cor', '$genero', $quantidade)
                ON DUPLICATE KEY UPDATE quantidade_estoque = quantidade_estoque + $quantidade";
        
        return $this->con->query($sql);
    }
    
    public function atualizarEstoque($variacao_id, $quantidade) {
        $variacao_id = (int)$variacao_id;
        $quantidade = (int)$quantidade;
        
        $sql = "UPDATE produto_variacao SET quantidade_estoque = $quantidade WHERE id = $variacao_id";
        return $this->con->query($sql);
    }
    
    public function listarPorFornecedor($fornecedor_id) {
        $fornecedor_id = (int)$fornecedor_id;
        
        $sql = "SELECT p.*, 
                (SELECT COUNT(*) FROM produto_variacao WHERE produto_id = p.id) as total_variacoes
                FROM produto p
                WHERE p.fornecedor_id = $fornecedor_id
                ORDER BY p.criado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function buscarPorId($id) {
        $id = (int)$id;
        
    $sql = "SELECT p.*, f.nome as Fornecedor_nome
        FROM produto p
        INNER JOIN fornecedor f ON p.fornecedor_id = f.id
                WHERE p.id = $id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_assoc() : null;
    }
    
    public function buscarVariacoes($produto_id) {
        $produto_id = (int)$produto_id;
        
        $sql = "SELECT * FROM produto_variacao WHERE produto_id = $produto_id ORDER BY genero, tamanho";
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarPorEscolaSerieGenero($escola_id, $serie, $genero) {
        $escola_id = (int)$escola_id;
        $serie = $this->con->real_escape_string($serie);
        $genero = $this->con->real_escape_string($genero);
        
    $sql = "SELECT DISTINCT p.*, f.nome as Fornecedor_nome
        FROM produto p
        INNER JOIN fornecedor f ON p.fornecedor_id = f.id
                INNER JOIN produto_homologacao ph ON p.id = ph.produto_id
                INNER JOIN homologacao h ON f.id = h.fornecedor_id AND ph.escola_id = h.escola_id
                WHERE ph.escola_id = $escola_id 
                AND ph.serie = '$serie'
                AND h.ativo = 1
                AND p.ativo = 1
                AND EXISTS (
                    SELECT 1 FROM produto_variacao pv 
                    WHERE pv.produto_id = p.id 
                    AND (pv.genero = '$genero' OR pv.genero = 'Unissex')
                    AND pv.quantidade_estoque > 0
                )
                ORDER BY p.nome";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
}
