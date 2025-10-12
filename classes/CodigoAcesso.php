<?php
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../conexao.php';

class CodigoAcesso {
    private $con;
    private $mailersendApiKey;
    private $mailersendFromEmail;
    private $mailersendFromName;
    
    public function __construct() {
        global $con;
        $this->con = $con;
        
        // Carrega configurações do .env
        $this->mailersendApiKey = env('MAILERSEND_API_KEY');
        $this->mailersendFromEmail = env('MAILERSEND_FROM_EMAIL', 'noreply@seudominio.com.br');
        $this->mailersendFromName = env('MAILERSEND_FROM_NAME', 'Conecta Uniforme');
        
        // Valida se a API key está configurada
        if (empty($this->mailersendApiKey) || $this->mailersendApiKey === 'sua_chave_api_aqui') {
            if (env('APP_ENV') !== 'production') {
                error_log("AVISO: MAILERSEND_API_KEY não configurada no arquivo .env");
            }
        }
    }
    
    public function gerarCodigo($tamanho = null) {
        if ($tamanho === null) {
            $tamanho = (int)env('CODIGO_ACESSO_TAMANHO', 6);
        }
        return strtoupper(substr(str_shuffle('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 0, $tamanho));
    }
    
    public function criarCodigo($email, $tipo_usuario) {
        $email = $this->con->real_escape_string($email);
        $tipo_usuario = $this->con->real_escape_string($tipo_usuario);
        
        // Invalidar códigos anteriores não usados
        $sql = "UPDATE codigo_acesso SET usado = 1 WHERE email = '$email' AND usado = 0";
        $this->con->query($sql);
        
        // Gerar novo código
        $codigo = $this->gerarCodigo();
        $minutos_expiracao = (int)env('CODIGO_ACESSO_EXPIRACAO', 600) / 60;
        $expira_em = date('Y-m-d H:i:s', strtotime("+{$minutos_expiracao} minutes"));
        
        $sql = "INSERT INTO codigo_acesso (email, codigo, tipo_usuario, expira_em, usado) 
                VALUES ('$email', '$codigo', '$tipo_usuario', '$expira_em', 0)";
        
        if($this->con->query($sql)) {
            return [
                'codigo' => $codigo,
                'expira_em' => $expira_em
            ];
        }
        
        return false;
    }
    
    public function validarCodigo($email, $codigo) {
        $email = $this->con->real_escape_string($email);
        $codigo = $this->con->real_escape_string($codigo);
        $agora = date('Y-m-d H:i:s');
        
        $sql = "SELECT * FROM codigo_acesso 
                WHERE email = '$email' 
                AND codigo = '$codigo' 
                AND usado = 0 
                AND expira_em > '$agora'
                ORDER BY criado_em DESC
                LIMIT 1";
        
        $result = $this->con->query($sql);
        
        if($result && $result->num_rows > 0) {
            $dados = $result->fetch_assoc();
            
            // Marcar código como usado
            $id = $dados['id'];
            $this->con->query("UPDATE codigo_acesso SET usado = 1 WHERE id = $id");
            
            return $dados;
        }
        
        return false;
    }
    
    public function enviarCodigoPorEmail($email, $codigo, $nome = '') {
        $minutos_expiracao = (int)env('CODIGO_ACESSO_EXPIRACAO', 600) / 60;
        $app_name = env('APP_NAME', 'Conecta Uniforme');
        
        $saudacao_nome = $nome ? " <strong>" . htmlspecialchars($nome) . "</strong>" : "";
        $saudacao_texto = $nome ? " " . $nome : "";
        
        $data = [
            'from' => [
                'email' => $this->mailersendFromEmail,
                'name' => $this->mailersendFromName
            ],
            'to' => [
                [
                    'email' => $email,
                    'name' => $nome
                ]
            ],
            'subject' => "Seu código de acesso - " . $app_name,
            'html' => "
                <html>
                <body>
                    <h2>Bem-vindo ao " . $app_name . "!</h2>
                    <p>Olá" . $saudacao_nome . ",</p>
                    <p>Seu código de acesso é:</p>
                    <h1 style='font-size: 32px; letter-spacing: 5px; color: #007bff;'><strong>" . $codigo . "</strong></h1>
                    <p style='color: #666;'>Este código expira em " . $minutos_expiracao . " minutos.</p>
                    <p style='color: #999; font-size: 12px;'>Se você não solicitou este código, ignore este e-mail.</p>
                    <hr>
                    <p style='color: #666; font-size: 12px;'>Atenciosamente,<br>Equipe " . $app_name . "</p>
                </body>
                </html>
            ",
            'text' => "Olá" . $saudacao_texto . ",\n\n" .
                     "Seu código de acesso é: " . $codigo . "\n\n" .
                     "Este código expira em " . $minutos_expiracao . " minutos.\n\n" .
                     "Se você não solicitou este código, ignore este e-mail.\n\n" .
                     "Atenciosamente,\nEquipe " . $app_name
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, 'https://api.mailersend.com/v1/email');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $this->mailersendApiKey
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return $httpCode >= 200 && $httpCode < 300;
    }
    
    public function limparCodigosExpirados() {
        $agora = date('Y-m-d H:i:s');
        $sql = "DELETE FROM codigo_acesso WHERE expira_em < '$agora' OR usado = 1";
        return $this->con->query($sql);
    }
}
