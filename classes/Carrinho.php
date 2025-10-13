<?php
require_once 'conexao.php';

class Carrinho {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function adicionar($responsavel_id, $produto_id, $variacao_id, $quantidade) {
        $responsavel_id = (int)$responsavel_id;
        $produto_id = (int)$produto_id;
        $variacao_id = (int)$variacao_id;
        $quantidade = (int)$quantidade;
        
        // Verificar se já existe
    $sql = "SELECT id, quantidade FROM carrinho 
        WHERE responsavel_id = $responsavel_id 
                AND produto_id = $produto_id 
                AND variacao_id = $variacao_id";
        
        $result = $this->con->query($sql);
        
        if($result && $result->num_rows > 0) {
            // Atualizar quantidade
            $row = $result->fetch_assoc();
            $nova_quantidade = $row['quantidade'] + $quantidade;
            $id = $row['id'];
            
            $sql = "UPDATE carrinho SET quantidade = $nova_quantidade WHERE id = $id";
        } else {
            // Inserir novo
        $sql = "INSERT INTO carrinho (responsavel_id, produto_id, variacao_id, quantidade) 
            VALUES ($responsavel_id, $produto_id, $variacao_id, $quantidade)";
        }
        
        return $this->con->query($sql);
    }
    
    public function atualizar($id, $quantidade) {
        $id = (int)$id;
        $quantidade = (int)$quantidade;
        
        if($quantidade <= 0) {
            return $this->remover($id);
        }
        
        $sql = "UPDATE carrinho SET quantidade = $quantidade WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function remover($id) {
        $id = (int)$id;
        $sql = "DELETE FROM carrinho WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function limpar($responsavel_id) {
        $responsavel_id = (int)$responsavel_id;
        $sql = "DELETE FROM carrinho WHERE responsavel_id = $responsavel_id";
        return $this->con->query($sql);
    }
    
    public function listar($responsavel_id) {
        $responsavel_id = (int)$responsavel_id;
        
        $sql = "SELECT c.*, 
                p.nome as produto_nome, p.preco, p.fornecedor_id,
                pv.tamanho, pv.cor, pv.genero, pv.quantidade_estoque,
                f.nome as Fornecedor_nome,
                (p.preco * c.quantidade) as subtotal
                FROM carrinho c
                INNER JOIN produto p ON c.produto_id = p.id
                INNER JOIN produto_variacao pv ON c.variacao_id = pv.id
                INNER JOIN fornecedor f ON p.fornecedor_id = f.id
                WHERE c.responsavel_id = $responsavel_id
                ORDER BY c.adicionado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function contarItens($responsavel_id) {
        $responsavel_id = (int)$responsavel_id;
        
        $sql = "SELECT SUM(quantidade) as total FROM carrinho WHERE responsavel_id = $responsavel_id";
        $result = $this->con->query($sql);
        
        if($result) {
            $row = $result->fetch_assoc();
            return (int)$row['total'];
        }
        return 0;
    }
    
    public function calcularTotal($responsavel_id) {
        $responsavel_id = (int)$responsavel_id;
        
        $sql = "SELECT SUM(p.preco * c.quantidade) as total
                FROM carrinho c
                INNER JOIN produto p ON c.produto_id = p.id
                WHERE c.responsavel_id = $responsavel_id";
        
        $result = $this->con->query($sql);
        
        if($result) {
            $row = $result->fetch_assoc();
            return (float)$row['total'];
        }
        return 0;
    }
    
    public function validarEstoque($responsavel_id) {
        $itens = $this->listar($responsavel_id);
        $erros = [];
        
        foreach($itens as $item) {
            if($item['quantidade'] > $item['quantidade_estoque']) {
                $erros[] = [
                    'produto' => $item['produto_nome'],
                    'solicitado' => $item['quantidade'],
                    'disponivel' => $item['quantidade_estoque']
                ];
            }
        }
        
        return $erros;
    }
}
