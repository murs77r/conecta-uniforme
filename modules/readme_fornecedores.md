# RF05 — Fornecedores Homologados (modules/fornecedores.py)

Gerencia cadastro, consulta, edição e exclusão de fornecedores.

- Blueprint: `fornecedores_bp`
- Prefixo de rota: `/fornecedores`
- Tabelas: `usuarios`, `fornecedores`, `produtos`, `repasses_financeiros`
- Dependências:
  - `utils.py`: `executar_query`, `validar_cnpj` (opcional), `registrar_log`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/fornecedores/*.html`

## RF05.2 — Consultar (Listar)

- Rotas: `GET /fornecedores/`, `GET /fornecedores/listar`
- Tela: `templates/fornecedores/listar.html`
- Filtro: `busca` (nome/razão social)
- SQL:
  ```sql
  SELECT f.*, u.nome, u.email, u.telefone, u.ativo
  FROM fornecedores f
  JOIN usuarios u ON f.usuario_id = u.id
  WHERE 1=1
  -- se busca
  AND (u.nome ILIKE %s OR f.razao_social ILIKE %s)
  ORDER BY u.nome
  ```
- Requer login via `verificar_sessao`.

## RF05.1 — Cadastrar Fornecedor

- Rota: `GET|POST /fornecedores/cadastrar`
- Permissão: `administrador`.
- Entrada: `nome`, `email`, `telefone`, `cnpj`, `razao_social`, `endereco`, `cidade`, `estado`, `cep`.
- SQLs:
  - Inserir `usuarios` (tipo fornecedor):
    ```sql
    INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
    VALUES (%s, %s, %s, 'fornecedor', TRUE)
    RETURNING id
    ```
  - Inserir `fornecedores`:
    ```sql
    INSERT INTO fornecedores (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    RETURNING id
    ```
- Log de criação em `logs_alteracoes`.

## RF05.3 — Editar Fornecedor

- Rota: `GET|POST /fornecedores/editar/<id>`
- Permissões: `administrador` ou o próprio fornecedor dono do registro.
- SQLs:
  - Buscar dados:
    ```sql
    SELECT f.*, u.nome, u.email, u.telefone, u.ativo
    FROM fornecedores f
    JOIN usuarios u ON f.usuario_id = u.id
    WHERE f.id = %s
    ```
  - Atualizar `usuarios`:
    ```sql
    UPDATE usuarios 
    SET nome = %s, email = %s, telefone = %s, data_atualizacao = CURRENT_TIMESTAMP
    WHERE id = %s
    ```
  - Atualizar `fornecedores`:
    ```sql
    UPDATE fornecedores 
    SET razao_social = %s, endereco = %s
    WHERE id = %s
    ```
- Log: `registrar_log(..., 'fornecedores', id, 'UPDATE')`.

## RF05.4 — Excluir Fornecedor

- Rota: `POST /fornecedores/excluir/<id>`
- Permissão: `administrador`.
- Bloqueia exclusão se houver dependências:
  ```sql
  SELECT COUNT(*) AS total FROM produtos WHERE fornecedor_id = %s;
  SELECT COUNT(*) AS total FROM repasses_financeiros WHERE fornecedor_id = %s;
  ```
- Exclusão e log:
  ```sql
  DELETE FROM fornecedores WHERE id = %s;
  ```

## Observações
- `fornecedores.usuario_id` é `UNIQUE` (1:1 com `usuarios`).
- A validação de CNPJ pode ser aplicada com `utils.validar_cnpj`.
- Produtos e repasses vinculados impedem a exclusão; considere inativar ao invés de excluir.
