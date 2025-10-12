<?php
require_once __DIR__ . '/../funcoes.php';

class Fornecedor {
    private $id;
    private $nome;
    private $email;
    private $telefone;
    private $cnpj;
    private $senha;
    private $ativo = 0;

    public function __construct($nome, $email = null, $telefone = null, $cnpj = null, $senha_plain = null, $ativo = 0) {
        $this->nome = $nome;
        $this->email = $email;
        $this->telefone = $telefone;
        $this->cnpj = $cnpj;
        if ($senha_plain) $this->senha = password_hash($senha_plain, PASSWORD_DEFAULT);
        $this->ativo = $ativo;
    }

    public function salvar() {
        global $con;
        try {
            $stmt = $con->prepare('INSERT INTO Fornecedor (nome, email, telefone, cnpj, senha, ativo) VALUES (?,?,?,?,?,?)');
            $stmt->bind_param('sssssi', $this->nome, $this->email, $this->telefone, $this->cnpj, $this->senha, $this->ativo);
            if (!$stmt->execute()) {
                throw new Exception('Erro ao salvar Fornecedor: ' . $stmt->error);
            }
            $this->id = $stmt->insert_id;
            $stmt->close();
            return $this->id;
        } catch (Exception $e) {
            return 'Erro: ' . $e->getMessage();
        }
    }

    public function ativar() {
        global $con;
        if (!$this->id) return false;
        $stmt = $con->prepare('UPDATE Fornecedor SET ativo = 1 WHERE id = ?');
        $stmt->bind_param('i', $this->id);
        return $stmt->execute();
    }

    public static function autenticar($email, $senha_plain) {
        global $con;
        $stmt = $con->prepare('SELECT id, senha, ativo FROM Fornecedor WHERE email = ? LIMIT 1');
        $stmt->bind_param('s', $email);
        $stmt->execute();
        $res = $stmt->get_result()->fetch_assoc();
        if ($res && $res['ativo']) {
            $hash = $res['senha'];
            if ($hash && password_verify($senha_plain, $hash)) return $res['id'];
        }
        return false;
    }

    public function vincularEscola($escola_id, $parceiro_desde = null) {
        global $con;
        try {
            $stmt = $con->prepare('INSERT INTO escola_Fornecedor (escola_id, Fornecedor_id, parceiro_desde) VALUES (?,?,?)');
            $stmt->bind_param('iis', $escola_id, $this->id, $parceiro_desde);
            if (!$stmt->execute()) {
                throw new Exception('Erro ao vincular Fornecedor: ' . $stmt->error);
            }
            $stmt->close();
            return true;
        } catch (Exception $e) {
            return 'Erro: ' . $e->getMessage();
        }
    }

    public static function getPorId($id) {
        $res = consulta_sql('SELECT * FROM Fornecedor WHERE id = ' . intval($id) . ' LIMIT 1');
        if (empty($res)) return null;
        $d = $res[0];
        $f = new Fornecedor($d['nome'], $d['email'], $d['telefone'], $d['cnpj']);
        $f->id = $d['id'];
        return $f;
    }
}
