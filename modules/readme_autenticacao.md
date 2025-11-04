# RF02 — Autenticação e Acesso (modules/autenticacao.py)

Este requisito implementa a autenticação via código de acesso temporário (login sem senha) e o controle de sessão/permissões.

- Blueprint: `autenticacao_bp`
- Prefixo de rota: `/auth`
- Tabelas envolvidas: `usuarios`, `codigos_acesso`, `sessoes`
- Dependências:
  - `utils.py`: `executar_query`, `gerar_codigo_acesso`, `gerar_token_sessao`, `enviar_codigo_acesso`, `validar_email`
  - `config.py`: `CODIGO_ACESSO_DURACAO_HORAS`, `SESSAO_DURACAO_DIAS`
  - Flask: `session`, `flash`, `redirect`, `url_for`

## RF02.1 — Solicitar Código de Acesso

- Rota: `GET|POST /auth/solicitar-codigo`
- Tela: `templates/auth/solicitar_codigo.html`
- Entrada (POST):
  - `email` (string) — obrigatório; validado por `utils.validar_email`
- Saída:
  - Em caso de sucesso, redireciona para `/auth/validar-codigo?email=<email>` e exibe flash de sucesso.
  - Em erros de validação ou execução, renderiza a própria tela com mensagens de erro.

Fluxo detalhado:
1. GET: renderiza o formulário.
2. POST:
   - Normaliza `email` (trim/lower) e valida o formato.
   - Busca o usuário por e-mail.
     - SQL:
       ```sql
       SELECT id, nome, email, tipo, ativo FROM usuarios WHERE email = %s
       ```
   - Rejeita se não existir ou se estiver inativo.
   - Gera `codigo` (6 dígitos) via `gerar_codigo_acesso()`.
   - Calcula `data_expiracao = now() + CODIGO_ACESSO_DURACAO_HORAS`.
   - Persiste o código de acesso:
     - SQL:
       ```sql
       INSERT INTO codigos_acesso (usuario_id, codigo, data_expiracao)
       VALUES (%s, %s, %s)
       ```
   - Tenta enviar e-mail com `utils.enviar_codigo_acesso(email, codigo, usuario['nome'])`.
   - Sucesso: flash “código enviado” e redirect para validação; Falha: mantém na tela com aviso sobre SMTP.

Notas de implementação e segurança:
- O código é exibido em `print()` no console apenas para facilitar testes (dev); não faça isso em produção.
- A query de inserção não marca explicitamente `usado = FALSE` pois a coluna tem default.
- Emails são tratados como identificadores únicos (constraint em `schema.sql`).

## RF02.2 — Validar Código de Acesso (Login)

- Rota: `GET|POST /auth/validar-codigo`
- Tela: `templates/auth/validar_codigo.html`
- Entrada (POST):
  - `email` (string) — obrigatório
  - `codigo` (string) — obrigatório
- Saída:
  - Em sucesso: cria sessão (cookie Flask + registro em `sessoes`) e redireciona para `url_for('home')`.
  - Em falhas: mantém na tela com mensagens (código inválido/expirado, usuário inativo, etc.).

Fluxo detalhado:
1. GET: recebe `email` na query string (opcional) para pré-preencher a tela.
2. POST:
   - Normaliza campos e valida preenchimento.
   - Busca o registro de código ainda não utilizado, mais recente:
     - SQL:
       ```sql
       SELECT ca.id, ca.usuario_id, ca.codigo, ca.data_expiracao, ca.usado,
              u.nome, u.email, u.tipo, u.ativo
       FROM codigos_acesso ca
       JOIN usuarios u ON ca.usuario_id = u.id
       WHERE u.email = %s AND ca.codigo = %s AND ca.usado = FALSE
       ORDER BY ca.data_criacao DESC
       LIMIT 1
       ```
   - Verifica expiração e se o usuário está ativo.
   - Marca o código como utilizado:
     - SQL:
       ```sql
       UPDATE codigos_acesso SET usado = TRUE WHERE id = %s
       ```
   - Gera token com `gerar_token_sessao()` e calcula `data_expiracao_sessao = now() + SESSAO_DURACAO_DIAS`.
   - Insere sessão persistente:
     - SQL:
       ```sql
       INSERT INTO sessoes (usuario_id, token, data_expiracao)
       VALUES (%s, %s, %s)
       ```
   - Popula `session` do Flask:
     - `usuario_id`, `usuario_nome`, `usuario_email`, `usuario_tipo`, `token_sessao`.

Boas práticas:
- Tokens de sessão são aleatórios (SHA-256) e armazenados em `sessoes` com validade.
- A aplicação usa `SECRET_KEY` (config.py) para assinar cookies de sessão.

## Logout — Encerrar Sessão

- Rota: `GET /auth/logout`
- Efeito:
  - Desativa sessão persistente:
    ```sql
    UPDATE sessoes SET ativo = FALSE WHERE token = %s
    ```
  - Limpa `session.clear()` e redireciona para `/auth/solicitar-codigo`.

## Funções auxiliares (reuso por todo o sistema)

### verificar_sessao()
- Contrato: retorna `None` se não autenticado; caso válido, retorna `{id, nome, email, tipo}` do usuário.
- Valida presença de `usuario_id` e `token_sessao` na sessão Flask.
- Busca sessão ativa e não expirada e o status do usuário:
  ```sql
  SELECT s.id, s.usuario_id, s.data_expiracao, s.ativo,
         u.nome, u.email, u.tipo, u.ativo as usuario_ativo
  FROM sessoes s
  JOIN usuarios u ON s.usuario_id = u.id
  WHERE s.token = %s AND s.ativo = TRUE
  ```
- Expira ou limpa sessão local se token inválido, sessão expirada ou usuário inativo.

### verificar_permissao(tipos_permitidos: list)
- Usa `verificar_sessao()`; confere se `usuario['tipo']` está em `tipos_permitidos`.
- Retorna os dados básicos do usuário quando autorizado; caso contrário `None`.

## Considerações de banco e índices
- Ver `schema.sql` para constraints e índices: `idx_codigos_acesso_usuario`, `idx_sessoes_usuario`, `idx_sessoes_token`, além de `usuarios.email` único.
- Campos de data usam `CURRENT_TIMESTAMP` como default para criação e atualização.

## Possíveis extensões
- Rate limiting para `/solicitar-codigo` por IP/email.
- Expurgo periódico de códigos expirados e sessões inativas.
- Segundo fator (2FA) e/ou captcha para elevar segurança.
- Auditoria de logins (tabela de auditoria extra).
