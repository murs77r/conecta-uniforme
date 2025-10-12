<?php
require_once 'conexao.php';

class Pedido {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function criar($responsavel_id, $aluno_id, $escola_id, $itens) {
        // Iniciar transação
        $this->con->begin_transaction();
        
        try {
            // Calcular total
            $total = 0;
            foreach($itens as $item) {
                $total += $item['preco_unitario'] * $item['quantidade'];
            }
            
            // Calcular comissão (15%)
            $comissao = $total * 0.15;
            
            // Criar pedido
            $sql = "INSERT INTO pedido (responsavel_id, aluno_id, escola_id, total, comissao, status) 
                    VALUES ($responsavel_id, $aluno_id, $escola_id, $total, $comissao, 'pendente')";
            
            if(!$this->con->query($sql)) {
                throw new Exception('Erro ao criar pedido');
            }
            
            $pedido_id = $this->con->insert_id;
            
            // Adicionar itens
            foreach($itens as $item) {
                $produto_id = (int)$item['produto_id'];
                $variacao_id = (int)$item['variacao_id'];
                $fornecedor_id = (int)$item['fornecedor_id'];
                $quantidade = (int)$item['quantidade'];
                $preco_unitario = (float)$item['preco_unitario'];
                $subtotal = $preco_unitario * $quantidade;
                
                $sql = "INSERT INTO pedido_item 
                        (pedido_id, produto_id, variacao_id, fornecedor_id, quantidade, preco_unitario, subtotal) 
                        VALUES ($pedido_id, $produto_id, $variacao_id, $fornecedor_id, $quantidade, $preco_unitario, $subtotal)";
                
                if(!$this->con->query($sql)) {
                    throw new Exception('Erro ao adicionar item ao pedido');
                }
                
                // Atualizar estoque
                $sql = "UPDATE produto_variacao SET quantidade_estoque = quantidade_estoque - $quantidade 
                        WHERE id = $variacao_id AND quantidade_estoque >= $quantidade";
                
                if(!$this->con->query($sql) || $this->con->affected_rows == 0) {
                    throw new Exception('Estoque insuficiente');
                }
            }
            
            // Limpar carrinho do responsável
            $sql = "DELETE FROM carrinho WHERE responsavel_id = $responsavel_id";
            $this->con->query($sql);
            
            $this->con->commit();
            return $pedido_id;
            
        } catch(Exception $e) {
            $this->con->rollback();
            return false;
        }
    }
    
    public function buscarPorId($id) {
        $id = (int)$id;
        
        $sql = "SELECT p.*, r.nome as responsavel_nome, r.email as responsavel_email,
                a.nome as aluno_nome, a.matricula as aluno_matricula,
                e.nome as escola_nome
                FROM pedido p
                INNER JOIN responsavel r ON p.responsavel_id = r.id
                INNER JOIN aluno a ON p.aluno_id = a.id
                INNER JOIN escola e ON p.escola_id = e.id
                WHERE p.id = $id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_assoc() : null;
    }
    
    public function buscarItensPedido($pedido_id) {
        $pedido_id = (int)$pedido_id;
        
        $sql = "SELECT pi.*, p.nome as produto_nome, 
                pv.tamanho, pv.cor, pv.genero,
                f.nome as fornecedor_nome
                FROM pedido_item pi
                INNER JOIN produto p ON pi.produto_id = p.id
                INNER JOIN produto_variacao pv ON pi.variacao_id = pv.id
                INNER JOIN fornecedor f ON pi.fornecedor_id = f.id
                WHERE pi.pedido_id = $pedido_id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarPorResponsavel($responsavel_id) {
        $responsavel_id = (int)$responsavel_id;
        
        $sql = "SELECT p.*, a.nome as aluno_nome
                FROM pedido p
                INNER JOIN aluno a ON p.aluno_id = a.id
                WHERE p.responsavel_id = $responsavel_id
                ORDER BY p.criado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarPorFornecedor($fornecedor_id) {
        $fornecedor_id = (int)$fornecedor_id;
        
        $sql = "SELECT DISTINCT p.*, a.nome as aluno_nome, e.nome as escola_nome
                FROM pedido p
                INNER JOIN pedido_item pi ON p.id = pi.pedido_id
                INNER JOIN aluno a ON p.aluno_id = a.id
                INNER JOIN escola e ON p.escola_id = e.id
                WHERE pi.fornecedor_id = $fornecedor_id
                ORDER BY p.criado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarPorEscola($escola_id) {
        $escola_id = (int)$escola_id;
        
        $sql = "SELECT p.*, a.nome as aluno_nome, r.nome as responsavel_nome
                FROM pedido p
                INNER JOIN aluno a ON p.aluno_id = a.id
                INNER JOIN responsavel r ON p.responsavel_id = r.id
                WHERE p.escola_id = $escola_id
                ORDER BY p.criado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function atualizarStatus($id, $novo_status) {
        $id = (int)$id;
        $novo_status = $this->con->real_escape_string($novo_status);
        
        $sql = "UPDATE pedido SET status = '$novo_status' WHERE id = $id";
        return $this->con->query($sql);
    }
    
    public function calcularComissoesMensais($ano, $mes) {
        $data_inicio = "$ano-$mes-01";
        $data_fim = date('Y-m-t', strtotime($data_inicio));
        
        $sql = "SELECT pi.fornecedor_id, 
                SUM(pi.subtotal) as total_vendas,
                SUM(p.comissao) as total_comissao
                FROM pedido_item pi
                INNER JOIN pedido p ON pi.pedido_id = p.id
                WHERE p.status IN ('aprovado', 'em_producao', 'pronto_retirada', 'entregue')
                AND DATE(p.criado_em) BETWEEN '$data_inicio' AND '$data_fim'
                GROUP BY pi.fornecedor_id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
}
