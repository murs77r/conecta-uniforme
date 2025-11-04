# RF04 — Escolas Homologadas (modules/escolas.py)

Gerencia o ciclo de vida de escolas: cadastro, consulta, edição, exclusão e homologação de fornecedores.

- Blueprint: `escolas_bp`
- Prefixo de rota: `/escolas`
- Tabelas: `usuarios`, `escolas`, `homologacao_fornecedores`, `fornecedores`, `produtos`, `pedidos`
- Dependências:
  - `utils.py`: `executar_query`, `validar_cnpj`, `registrar_log`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/escolas/*.html`

## RF04.2 — Consultar (Listar)

- Rotas: `GET /escolas/` e `GET /escolas/listar`
- Tela: `templates/escolas/listar.html`
- Filtros (query string):
  - `busca` (nome da escola/razão social/CNPJ)
  - `ativo` (`true`/`false`)
- SQL base e filtros:
  ```sql
  SELECT e.*, u.nome, u.email, u.telefone, u.ativo
  FROM escolas e
  JOIN usuarios u ON e.usuario_id = u.id
  WHERE 1=1
  -- se busca
  AND (u.nome ILIKE %s OR e.razao_social ILIKE %s OR e.cnpj ILIKE %s)
  -- se ativo
  AND e.ativo = %s
  ORDER BY u.nome
  ```
- Requer login (`verificar_sessao`).

## RF04.1 — Cadastrar Escola

- Rota: `GET|POST /escolas/cadastrar`
- Tela: `templates/escolas/cadastrar.html`
- Permissão: apenas `administrador`.
- Entrada (POST): `nome`, `email`, `telefone`, `cnpj`, `razao_social`, `endereco`, `cidade`, `estado`, `cep`.
- Validações:
  - Campos obrigatórios (`nome`, `email`, `cnpj`, `razao_social`).
  - `cnpj` via `utils.validar_cnpj`.
  - Unicidade de `email` e `cnpj`.
- SQLs:
  - Verificar e-mail:
    ```sql
    SELECT id FROM usuarios WHERE email = %s
    ```
  - Verificar CNPJ:
    ```sql
    SELECT id FROM escolas WHERE cnpj = %s
    ```
  - Inserir usuário (perfil escola):
    ```sql
    INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
    VALUES (%s, %s, %s, 'escola', TRUE)
    RETURNING id
    ```
  - Inserir escola:
    ```sql
    INSERT INTO escolas (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    RETURNING id
    ```
- Log: `registrar_log(..., 'escolas', escola_id, 'INSERT', dados_novos=JSON)`.

## RF04.2 — Visualizar Escola

- Rota: `GET /escolas/visualizar/<id>`
- Tela: `templates/escolas/visualizar.html`
- SQLs:
  - Detalhes da escola + usuário:
    ```sql
    SELECT e.*, u.nome, u.email, u.telefone, u.ativo, u.data_cadastro
    FROM escolas e
    JOIN usuarios u ON e.usuario_id = u.id
    WHERE e.id = %s
    ```
  - Fornecedores homologados:
    ```sql
    SELECT f.id, u.nome, f.razao_social, hf.data_homologacao, hf.ativo
    FROM homologacao_fornecedores hf
    JOIN fornecedores f ON hf.fornecedor_id = f.id
    JOIN usuarios u ON f.usuario_id = u.id
    WHERE hf.escola_id = %s
    ORDER BY u.nome
    ```
- Requer login (`verificar_sessao`).

## RF04.x — Homologar Fornecedor para Escola (Admin)

- Rota: `GET|POST /escolas/homologar/<escola_id>`
- Tela: `templates/escolas/homologar.html`
- Permissão: `administrador`.
- GET: lista fornecedores ativos para seleção:
  ```sql
  SELECT f.id, u.nome, f.razao_social
  FROM fornecedores f JOIN usuarios u ON f.usuario_id = u.id
  WHERE u.ativo = TRUE
  ORDER BY u.nome
  ```
- POST: insere homologação (ou reativa se já existir):
  - Evitar duplicidade:
    ```sql
    SELECT id FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s
    ```
  - Reativar se necessário:
    ```sql
    UPDATE homologacao_fornecedores SET ativo = TRUE WHERE id = %s
    ```
  - Inserção:
    ```sql
    INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, ativo, observacoes)
    VALUES (%s, %s, TRUE, %s)
    RETURNING id
    ```
- Log correspondente (INSERT/UPDATE) em `logs_alteracoes`.

### Alternar status de homologação
- Rota: `POST /escolas/homologacao/<escola_id>/<fornecedor_id>/status`
- Permissão: `administrador`.
- SQL:
  ```sql
  SELECT id, ativo FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s;
  UPDATE homologacao_fornecedores SET ativo = %s WHERE id = %s;
  ```

## RF04.3 — Editar Escola

- Rota: `GET|POST /escolas/editar/<id>`
- Permissões: `administrador` ou a própria `escola` dona do registro (só edita a si).
- GET: carrega dados para `templates/escolas/editar.html`.
- SQLs:
  - Buscar:
    ```sql
    SELECT e.*, u.nome, u.email, u.telefone, u.ativo
    FROM escolas e
    JOIN usuarios u ON e.usuario_id = u.id
    WHERE e.id = %s
    ```
  - Atualizar `usuarios`:
    ```sql
    UPDATE usuarios 
    SET nome = %s, email = %s, telefone = %s, ativo = %s, data_atualizacao = CURRENT_TIMESTAMP
    WHERE id = %s
    ```
  - Atualizar `escolas`:
    ```sql
    UPDATE escolas 
    SET cnpj = %s, razao_social = %s, endereco = %s, cidade = %s, estado = %s, cep = %s, ativo = %s
    WHERE id = %s
    ```
- Log de atualização com `dados_antigos` e `dados_novos`.

## RF04.4 — Excluir Escola

- Rota: `POST /escolas/excluir/<id>`
- Permissão: `administrador`.
- Antes de excluir, impede se houver vínculos:
  ```sql
  SELECT COUNT(*) AS total FROM homologacao_fornecedores WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM produtos WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM pedidos WHERE escola_id = %s;
  ```
- Exclusão e log:
  ```sql
  DELETE FROM escolas WHERE id = %s;
  ```

## Observações e boas práticas
- `escolas.usuario_id` é `UNIQUE` (1:1 com `usuarios`).
- Use `utils.registrar_log` sempre que alterar dados críticos.
- `validar_cnpj` em `utils` é validação simplificada (pode ser trocada por validação completa no futuro).
