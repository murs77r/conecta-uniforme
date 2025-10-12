<?php
require_once 'conexao.php';

class Comissao {
    private $con;
    
    public function __construct() {
        global $con;
        $this->con = $con;
    }
    
    public function gerarRelatorioMensal($ano, $mes) {
        $mes_referencia = sprintf('%04d-%02d-01', $ano, $mes);
        $data_inicio = $mes_referencia;
        $data_fim = date('Y-m-t', strtotime($mes_referencia));
        
        // Buscar vendas do mês por fornecedor
        $sql = "SELECT pi.fornecedor_id, f.nome as fornecedor_nome,
                SUM(pi.subtotal) as total_vendas,
                COUNT(DISTINCT pi.pedido_id) as total_pedidos
                FROM pedido_item pi
                INNER JOIN pedido p ON pi.pedido_id = p.id
                INNER JOIN fornecedor f ON pi.fornecedor_id = f.id
                WHERE p.status IN ('aprovado', 'em_producao', 'pronto_retirada', 'entregue')
                AND DATE(p.criado_em) BETWEEN '$data_inicio' AND '$data_fim'
                GROUP BY pi.fornecedor_id, f.nome";
        
        $result = $this->con->query($sql);
        
        if($result) {
            $relatorios = [];
            while($row = $result->fetch_assoc()) {
                $total_vendas = (float)$row['total_vendas'];
                $total_comissao = $total_vendas * 0.15;
                $valor_liquido = $total_vendas - $total_comissao;
                
                // Inserir ou atualizar comissão
                $fornecedor_id = (int)$row['fornecedor_id'];
                
                $sql_insert = "INSERT INTO comissao 
                              (fornecedor_id, mes_referencia, total_vendas, total_comissao, valor_liquido, status) 
                              VALUES ($fornecedor_id, '$mes_referencia', $total_vendas, $total_comissao, $valor_liquido, 'pendente')
                              ON DUPLICATE KEY UPDATE 
                              total_vendas = $total_vendas, 
                              total_comissao = $total_comissao, 
                              valor_liquido = $valor_liquido";
                
                $this->con->query($sql_insert);
                
                $relatorios[] = array_merge($row, [
                    'total_comissao' => $total_comissao,
                    'valor_liquido' => $valor_liquido,
                    'mes_referencia' => $mes_referencia
                ]);
            }
            
            return $relatorios;
        }
        
        return [];
    }
    
    public function registrarPagamento($comissao_id, $valor_pago, $data_pagamento = null) {
        $comissao_id = (int)$comissao_id;
        $valor_pago = (float)$valor_pago;
        $data_pagamento = $data_pagamento ?: date('Y-m-d');
        
        $sql = "UPDATE comissao 
                SET status = 'pago', 
                    data_pagamento = '$data_pagamento', 
                    valor_pago = $valor_pago 
                WHERE id = $comissao_id";
        
        return $this->con->query($sql);
    }
    
    public function listarPorFornecedor($fornecedor_id) {
        $fornecedor_id = (int)$fornecedor_id;
        
        $sql = "SELECT * FROM comissao 
                WHERE fornecedor_id = $fornecedor_id 
                ORDER BY mes_referencia DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function listarTodas($status = null) {
        $where = '';
        if($status) {
            $status = $this->con->real_escape_string($status);
            $where = "WHERE c.status = '$status'";
        }
        
        $sql = "SELECT c.*, f.nome as fornecedor_nome, f.email as fornecedor_email
                FROM comissao c
                INNER JOIN fornecedor f ON c.fornecedor_id = f.id
                $where
                ORDER BY c.mes_referencia DESC, f.nome";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
    
    public function buscarPorId($id) {
        $id = (int)$id;
        
        $sql = "SELECT c.*, f.nome as fornecedor_nome, f.email as fornecedor_email
                FROM comissao c
                INNER JOIN fornecedor f ON c.fornecedor_id = f.id
                WHERE c.id = $id";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_assoc() : null;
    }
    
    public function detalhesVendasMes($fornecedor_id, $mes_referencia) {
        $fornecedor_id = (int)$fornecedor_id;
        $mes_referencia = $this->con->real_escape_string($mes_referencia);
        $data_inicio = $mes_referencia;
        $data_fim = date('Y-m-t', strtotime($mes_referencia));
        
        $sql = "SELECT p.id as pedido_id, p.criado_em, p.status, p.total,
                a.nome as aluno_nome, e.nome as escola_nome,
                SUM(pi.subtotal) as valor_fornecedor
                FROM pedido p
                INNER JOIN pedido_item pi ON p.id = pi.pedido_id
                INNER JOIN aluno a ON p.aluno_id = a.id
                INNER JOIN escola e ON p.escola_id = e.id
                WHERE pi.fornecedor_id = $fornecedor_id
                AND p.status IN ('aprovado', 'em_producao', 'pronto_retirada', 'entregue')
                AND DATE(p.criado_em) BETWEEN '$data_inicio' AND '$data_fim'
                GROUP BY p.id, p.criado_em, p.status, p.total, a.nome, e.nome
                ORDER BY p.criado_em DESC";
        
        $result = $this->con->query($sql);
        return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
    }
}
