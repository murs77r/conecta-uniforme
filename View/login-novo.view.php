<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Conecta Uniforme</title>
</head>
<body>
    <h1>Conecta Uniforme - Login</h1>
    
    <?php if($erro): ?>
        <div style="color: red; border: 1px solid red; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($erro) ?>
        </div>
    <?php endif; ?>
    
    <?php if($mensagem): ?>
        <div style="color: green; border: 1px solid green; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($mensagem) ?>
        </div>
    <?php endif; ?>
    
    <?php if($step == 'email'): ?>
        <h2>Digite seu e-mail para entrar</h2>
        <form method="POST">
            <div>
                <label>E-mail:</label><br>
                <input type="email" name="email" required style="width: 300px; padding: 5px;">
            </div>
            
            <div style="margin-top: 15px;">
                <label>Tipo de usuário:</label><br>
                <select name="tipo_usuario" required style="width: 310px; padding: 5px;">
                    <option value="">Selecione...</option>
                    <option value="responsavel">Responsável (Pai/Mãe)</option>
                    <option value="fornecedor">Fornecedor</option>
                    <option value="gestor">Gestor Escolar</option>
                </select>
            </div>
            
            <div style="margin-top: 20px;">
                <button type="submit" name="enviar_email" style="padding: 10px 20px;">
                    Enviar Código de Acesso
                </button>
            </div>
        </form>
        
        <p style="margin-top: 30px;">
            <a href="/conecta-uniforme/">Voltar para a página inicial</a>
        </p>
        
    <?php else: ?>
        <h2>Digite o código recebido por e-mail</h2>
        <p>Um código foi enviado para: <strong><?= htmlspecialchars($_SESSION['login_email'] ?? '') ?></strong></p>
        
        <form method="POST">
            <div>
                <label>Código de acesso:</label><br>
                <input type="text" name="codigo" required maxlength="10" 
                       style="width: 300px; padding: 5px; font-size: 18px; letter-spacing: 2px;" 
                       placeholder="ABC123">
            </div>
            
            <div style="margin-top: 20px;">
                <button type="submit" name="validar_codigo" style="padding: 10px 20px;">
                    Entrar
                </button>
            </div>
        </form>
        
        <form method="POST" style="margin-top: 15px;">
            <button type="submit" name="reenviar_codigo" style="padding: 8px 15px;">
                Reenviar Código
            </button>
        </form>
        
        <p style="margin-top: 20px;">
            <a href="/conecta-uniforme/login-novo">Voltar para digitar outro e-mail</a>
        </p>
    <?php endif; ?>
</body>
</html>
