<?php 
class Escola {
    private $id;

    private $email;
    private $nome;
    private $cnpj;
    private $cep;
    private $estado;
    private $cidade;
    private $endereco;
    private $complemento;

    private $cod_acesso;

    public function __construct($email, $nome, $cnpj, $cep, $estado, $cidade, $endereco, $complemento) {
        $this->email = $email;
        $this->nome = $nome;
        $this->cnpj = $cnpj;
        $this->cep = $cep;
        $this->estado = $estado;
        $this->cidade = $cidade;
        $this->endereco = $endereco;
        $this->complemento = $complemento;
    }
    public static function getPorId($id) {
        $sql = "SELECT * FROM escola WHERE id = " . intval($id) . " LIMIT 1";
        $resultado = consulta_sql($sql);
        if (empty($resultado)) {
            throw new Exception("Escola não encontrada.");
        }
        $dados = $resultado[0];

        $email = $dados['email'];
        $nome = $dados['nome'];
        $cnpj = $dados['cnpj'];
        $cep = $dados['cep'];
        $estado = $dados['estado'];
        $cidade = $dados['cidade'];
        $endereco = $dados['endereco'];
        $complemento = $dados['complemento'];

        return new Escola($email, $nome, $cnpj, $cep, $estado, $cidade, $endereco, $complemento);   
    }
    public function gerarChave() {
        $this->cod_acesso = random_int(100000000, 999999999);
    }
    public function salvar() {
        global $con;
    
        try {
            if ($this->id) {
                $stmt = $con->prepare("UPDATE escola SET email=?, nome=?, cnpj=?, cep=?, estado=?, cidade=?, endereco=?, complemento=?, cod_acesso=? WHERE id=?");
                if (!$stmt) {
                    throw new Exception("Erro ao preparar statement: " . $con->error);
                }
                $stmt->bind_param(
                    "sssssssssi",
                    $this->email,
                    $this->nome,
                    $this->cnpj,
                    $this->cep,
                    $this->estado,
                    $this->cidade,
                    $this->endereco,
                    $this->complemento,
                    $this->cod_acesso,
                    $this->id
                );
                if (!$stmt->execute()) {
                    throw new Exception("Erro ao executar statement: " . $stmt->error);
                }
                $stmt->close();
            } else {
                $stmt = $con->prepare("INSERT INTO escola (email, nome, cnpj, cep, estado, cidade, endereco, complemento, cod_acesso) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
                if (!$stmt) {
                    throw new Exception("Erro ao preparar statement: " . $con->error);
                }
                $stmt->bind_param(
                    "sssssssss",
                    $this->email,
                    $this->nome,
                    $this->cnpj,
                    $this->cep,
                    $this->estado,
                    $this->cidade,
                    $this->endereco,
                    $this->complemento,
                    $this->cod_acesso
                );
                if (!$stmt->execute()) {
                    throw new Exception("Erro ao executar statement: " . $stmt->error);
                }
                $this->id = $stmt->insert_id;
                $stmt->close();
            }
        } catch (Exception $e) {
            return "Erro: " . $e->getMessage();
        }
    }


    public function getId() {
        return $this->id;
    }
    public function getEmail() {
        return $this->email;
    }
    public function getNome() {
        return $this->nome;
    }
    public function getCnpj() {
        return $this->cnpj;
    }
    public function getCep() {
        return $this->cep;
    }
    public function getEstado() {
        return $this->estado;
    }
    public function getCidade() {
        return $this->cidade;
    }
    public function getEndereco() {
        return $this->endereco;
    }
    public function getComplemento() {
        return $this->complemento;
    }
}