# Módulo de Autenticação

============================================
RF02 - GERENCIAR AUTENTICAÇÃO E ACESSO
============================================
Este módulo é responsável por:
- RF02.1: Solicitar código de acesso
- RF02.2: Validar código de acesso

Controla o processo de autenticação e autorização de usuários, garantindo segurança no acesso ao sistema.

---

## 📋 Visão Geral

O módulo de **Autenticação** gerencia todo o fluxo de login, controle de acesso e sessões de usuários no Conecta Uniforme. Implementa autenticação tradicional por código enviado via e-mail.

### Propósito
- Autenticar usuários via código de acesso (e-mail)
- Gerenciar sessões seguras com expiração configurável
- Controlar permissões por tipo de usuário

---

## 🏗️ Arquitetura

### Métodos de Autenticação
**Código por E-mail**
   - Usuário informa email + tipo
   - Sistema gera código aleatório (6 dígitos)
   - Código enviado por SMTP
   - Validade: configurável (padrão 2 horas)

### Padrões Utilizados
- **Session Management**: Flask sessions com tokens únicos
- **Middleware Pattern**: Verificação de sessão em decorators

---

## 🔌 Endpoints (Rotas)

### 1. `GET /auth/solicitar-codigo`
**Descrição**: Exibe formulário para solicitar código de acesso

**Autenticação**: Não requerida (público)

**Resposta**:
```html
Status: 200 OK
Template: templates/auth/solicitar_codigo.html
```

---

### 2. `POST /auth/solicitar-codigo`
**Descrição**: Gera e envia código de acesso por e-mail

**Corpo (form-data)**:
```json
{
    "email": "string (obrigatório, email válido)",
    "tipo": "string (obrigatório: administrador|escola|fornecedor|responsavel)"
}
```

**Lógica de Geração**:
```python
# 1. Valida email
if not validar_email(email):
    flash('Email inválido', 'danger')
    return redirect(...)

# 2. Busca usuário
usuario = executar_query("""
    SELECT * FROM usuarios 
    WHERE email = %s AND tipo = %s AND ativo = TRUE
""", (email, tipo), fetchone=True)

if not usuario:
    flash('Usuário não encontrado', 'danger')
    return redirect(...)

# 3. Gera código (6 dígitos)
codigo = gerar_codigo_acesso()  # Ex: 123456

# 4. Salva código com expiração
expiracao = datetime.now() + timedelta(hours=CODIGO_ACESSO_DURACAO_HORAS)
executar_query("""
    INSERT INTO codigos_acesso (usuario_id, codigo, data_expiracao, usado)
    VALUES (%s, %s, %s, FALSE)
""", (usuario['id'], codigo, expiracao))

# 5. Envia por e-mail
enviar_codigo_acesso(email, codigo, usuario['nome'])

flash('Código enviado para seu e-mail', 'success')
```

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /auth/validar-codigo?email={email}
Flash: "Código enviado para seu e-mail"
```

---

### 3. `POST /auth/validar-codigo`
**Descrição**: Valida código e cria sessão

**Corpo (form-data)**:
```json
{
    "email": "string",
    "tipo": "string",
    "codigo": "string (6 dígitos)"
}
```

**Validação de Código**:
```python
# 1. Busca código
registro = executar_query("""
    SELECT ca.*, u.* FROM codigos_acesso ca
    JOIN usuarios u ON ca.usuario_id = u.id
    WHERE u.email = %s 
      AND u.tipo = %s
      AND ca.codigo = %s
      AND ca.usado = FALSE
      AND ca.data_expiracao > NOW()
    ORDER BY ca.data_geracao DESC
    LIMIT 1
""", (email, tipo, codigo), fetchone=True)

if not registro:
    flash('Código inválido ou expirado', 'danger')
    return redirect(...)

# 2. Marca código como usado
executar_query("""
    UPDATE codigos_acesso SET usado = TRUE WHERE id = %s
""", (registro['id'],))

# 3. Cria sessão
session['usuario_id'] = registro['usuario_id']
session['tipo_usuario'] = registro['tipo']
session['nome_usuario'] = registro['nome']
session['email_usuario'] = registro['email']
session['token_sessao'] = gerar_token_sessao()
session['data_login'] = datetime.now().isoformat()
session.permanent = True  # Duração: SESSAO_DURACAO_DIAS

# 4. Log de login
registrar_log(
    usuario_id=registro['usuario_id'],
    acao='LOGIN',
    descricao=f"Login via código de acesso"
)

flash('Login realizado com sucesso', 'success')
return redirect(url_for('home'))
```

---

### 4. `GET /auth/logout`
**Descrição**: Encerra sessão do usuário

**Comportamento**:
```python
# Log antes de destruir sessão
if 'usuario_id' in session:
    registrar_log(
        usuario_id=session['usuario_id'],
        acao='LOGOUT',
        descricao='Logout manual'
    )

# Limpa sessão
session.clear()

flash('Você foi desconectado', 'info')
return redirect(url_for('autenticacao.solicitar_codigo'))
```

---

### 5. `GET /auth/tipos-por-email`
**Descrição**: Retorna tipos de usuário para um email (AJAX)

**Autenticação**: Não requerida

**Parâmetros Query**:
```json
{
    "email": "string"
}
```

**Resposta JSON**:
```json
{
    "email": "usuario@exemplo.com",
    "tipos": [
        {"slug": "administrador", "label": "Administrador"},
        {"slug": "escola", "label": "Escola"}
    ]
}
```

**SQL**:
```sql
SELECT DISTINCT tipo FROM usuarios 
WHERE email = %s AND ativo = TRUE 
ORDER BY tipo
```

**Caso de Uso**: Frontend JavaScript mostra modal de seleção se usuário tem múltiplos perfis.

---

##  Modelos de Dados

### Tabela `codigos_acesso`
```sql
CREATE TABLE codigos_acesso (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id),
    codigo VARCHAR(6) NOT NULL,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_codigos_usuario ON codigos_acesso(usuario_id);
CREATE INDEX idx_codigos_expiracao ON codigos_acesso(data_expiracao);
```

---

## 🔐 Segurança

### Código de Acesso
- **Geração**: Aleatório (6 dígitos), criptograficamente seguro
- **Validade**: 2 horas (configurável)
- **Uso Único**: Marcado como `usado=TRUE` após validação
- **Rate Limiting**: Máximo de 3 tentativas por minuto (recomendado)

### Sessões
- **Token Único**: UUID v4 gerado por sessão
- **Expiração**: Configurável (padrão: 7 dias)
- **HttpOnly**: Cookies não acessíveis por JavaScript
- **Secure**: HTTPS obrigatório em produção
- **SameSite**: Proteção CSRF

---

## 📝 Regras de Negócio

### 1. Tipos de Usuário
```python
TIPOS_USUARIO = {
    'administrador': 'Administrador',
    'escola': 'Escola',
    'fornecedor': 'Fornecedor',
    'responsavel': 'Responsável'
}
```

### 2. Múltiplos Perfis
- Um email pode ter múltiplos tipos de usuário
- Frontend exibe modal de seleção se `len(tipos) > 1`
- Cada tipo tem sessão independente

### 3. Expiração de Código
```python
# Configuração em config.py
CODIGO_ACESSO_DURACAO_HORAS = 2
SESSAO_DURACAO_DIAS = 7

# Limpeza automática de códigos expirados (cron job)
DELETE FROM codigos_acesso 
WHERE data_expiracao < NOW() - INTERVAL '7 days'
```

### 4. Permissões
```python
def verificar_permissao(tipos_permitidos: List[str]) -> Optional[dict]:
    """Verifica se usuário logado tem permissão"""
    if not verificar_sessao():
        return None
    
    tipo_atual = session.get('tipo_usuario')
    if tipo_atual not in tipos_permitidos:
        return None
    
    return {
        'id': session['usuario_id'],
        'tipo': tipo_atual,
        'nome': session['nome_usuario']
    }
```

---

## 💡 Exemplos de Uso

### Solicitar Código
```bash
curl -X POST http://localhost:5000/auth/solicitar-codigo \
  -F "email=usuario@exemplo.com" \
  -F "tipo=responsavel"
```

### Validar Código
```bash
curl -X POST http://localhost:5000/auth/validar-codigo \
  -F "email=usuario@exemplo.com" \
  -F "tipo=responsavel" \
  -F "codigo=123456"
```

### Verificar Sessão em Rota
```python
from core.services import AutenticacaoService

@app.route('/dashboard')
def dashboard():
    usuario = AutenticacaoService.verificar_sessao()
    if not usuario:
        flash('Faça login', 'warning')
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    return render_template('dashboard.html', usuario=usuario)
```