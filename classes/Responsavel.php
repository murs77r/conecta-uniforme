<?php
require_once __DIR__ . '/../funcoes.php';

class Responsavel {
    private $id;
    private $nome;
    private $email;
    private $telefone;
    private $senha; // hash
    private $escola_id;
    private $matricula;

    public function __construct($nome, $email, $telefone, $senha_plain, $escola_id, $matricula) {
        $this->nome = $nome;
        $this->email = $email;
        $this->telefone = $telefone;
        $this->senha = password_hash($senha_plain, PASSWORD_DEFAULT);
        $this->escola_id = $escola_id;
        $this->matricula = $matricula;
    }

    public function salvar() {
        global $con;
        try {
            $stmt = $con->prepare('INSERT INTO Responsável (nome, email, telefone, senha, escola_id, matricula) VALUES (?,?,?,?,?,?)');
            $stmt->bind_param('sssssi', $this->nome, $this->email, $this->telefone, $this->senha, $this->escola_id, $this->matricula);
            if (!$stmt->execute()) {
                throw new Exception('Erro ao salvar responsável: ' . $stmt->error);
            }
            $this->id = $stmt->insert_id;
            $stmt->close();
            return $this->id;
        } catch (Exception $e) {
            return 'Erro: ' . $e->getMessage();
        }
    }

    public static function getPorId($id) {
        $res = consulta_sql('SELECT * FROM Responsável WHERE id = ' . intval($id) . ' LIMIT 1');
        if (empty($res)) return null;
        $d = $res[0];
        $r = new Responsavel($d['nome'], $d['email'], $d['telefone'], $d['senha'], $d['escola_id'], $d['matricula']);
        $r->id = $d['id'];
        return $r;
    }

    public static function autenticarPorCodigoEMatricula($codigo_escola, $matricula, $senha_plain) {
        global $con;
        // Busca a escola pelo código
        $stmt = $con->prepare('SELECT id FROM escola WHERE cod_acesso = ? LIMIT 1');
        $stmt->bind_param('s', $codigo_escola);
        $stmt->execute();
        $e = $stmt->get_result()->fetch_assoc();
        if (!$e) return false;
        $escola_id = $e['id'];

        $stmt = $con->prepare('SELECT id, senha FROM Responsável WHERE escola_id = ? AND matricula = ? LIMIT 1');
        $stmt->bind_param('is', $escola_id, $matricula);
        $stmt->execute();
        $r = $stmt->get_result()->fetch_assoc();
        if ($r && password_verify($senha_plain, $r['senha'])) return $r['id'];
        return false;
    }
}
