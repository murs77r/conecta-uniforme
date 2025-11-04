# RF01 — Manter Cadastro de Usuário (modules/usuarios.py)

Administra usuários do sistema (administrador, escola, fornecedor, responsável), incluindo auditoria de alterações.

- Blueprint: `usuarios_bp`
- Prefixo: `/usuarios`
- Tabelas: `usuarios`, `escolas`, `fornecedores`, `responsaveis`, `logs_alteracoes`, além de tabelas relacionadas usadas em validações (`pedidos`, `produtos`, `homologacao_fornecedores`, `repasses_financeiros`)
- Dependências:
  - `utils.py`: `executar_query`, `validar_email`, `validar_cpf`, `validar_cnpj`, `registrar_log`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/usuarios/*.html`

## RF01.2 — Consultar (Listar)

- Rotas: `GET /usuarios/`, `GET /usuarios/listar`
- Filtros: `tipo`, `busca` (nome/email)
- SQL:
  ```sql
  SELECT id, nome, email, telefone, tipo, ativo, data_cadastro
  FROM usuarios
  WHERE 1=1
  -- se tipo
  AND tipo = %s
  -- se busca
  AND (nome ILIKE %s OR email ILIKE %s)
  ORDER BY data_cadastro DESC
  ```
- Permissão: somente `administrador`.

## RF01.1 — Cadastrar Usuário

- Rota: `GET|POST /usuarios/cadastrar`
- Permissão: `administrador`.
- Validações: campos obrigatórios (`nome`, `email`, `tipo`), `validar_email`, e `tipo` ∈ {`administrador`, `escola`, `fornecedor`, `responsavel`}.
- Evita e-mails duplicados:
  ```sql
  SELECT id FROM usuarios WHERE email = %s
  ```
- Inserção:
  ```sql
  INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
  VALUES (%s, %s, %s, %s, TRUE)
  RETURNING id
  ```
- Log `INSERT` com `dados_novos` (JSON).

## RF01.2 — Visualizar Usuário (Detalhes)

- Rota: `GET /usuarios/visualizar/<id>`
- Regras de acesso: `administrador` pode ver todos; outros apenas a si mesmos.
- SQL principal:
  ```sql
  SELECT id, nome, email, telefone, tipo, ativo, data_cadastro, data_atualizacao
  FROM usuarios
  WHERE id = %s
  ```
- Informações complementares por tipo:
  ```sql
  -- escola
  SELECT * FROM escolas WHERE usuario_id = %s;
  -- fornecedor
  SELECT * FROM fornecedores WHERE usuario_id = %s;
  -- responsavel
  SELECT * FROM responsaveis WHERE usuario_id = %s;
  ```

## RF01.3 — Editar Usuário

- Rota: `GET|POST /usuarios/editar/<id>`
- Regras: usuário autenticado; `administrador` edita qualquer; demais apenas o próprio registro.
- Evita e-mail duplicado em outro ID:
  ```sql
  SELECT id FROM usuarios WHERE email = %s AND id != %s
  ```
- Regra de segurança: não permitir inativar o último administrador ativo:
  ```sql
  SELECT COUNT(*) AS total FROM usuarios WHERE tipo = 'administrador' AND id != %s AND ativo = TRUE
  ```
- Atualização:
  ```sql
  UPDATE usuarios 
  SET nome = %s, email = %s, telefone = %s, tipo = %s, ativo = %s, data_atualizacao = CURRENT_TIMESTAMP
  WHERE id = %s
  ```
- Log `UPDATE` com `dados_antigos` e `dados_novos`.

## RF01.4 — Excluir Usuário

- Rota: `POST /usuarios/excluir/<id>`
- Permissão: `administrador`. Não permite excluir a si próprio.
- Bloqueios por dependências (variando conforme o `tipo` do usuário):
  - Administrador: não excluir se for o último admin ativo.
  - Escola: bloqueia se houver `homologacao_fornecedores`, `produtos`, `pedidos` vinculados à sua escola.
  - Fornecedor: bloqueia se houver `produtos` ou `repasses_financeiros`.
  - Responsável: bloqueia se houver `pedidos`.
- Exemplos de SQL verificados:
  ```sql
  SELECT id FROM escolas WHERE usuario_id = %s;
  SELECT COUNT(*) AS total FROM homologacao_fornecedores WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM produtos WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM pedidos WHERE escola_id = %s;
  SELECT id FROM fornecedores WHERE usuario_id = %s;
  SELECT COUNT(*) AS total FROM produtos WHERE fornecedor_id = %s;
  SELECT COUNT(*) AS total FROM repasses_financeiros WHERE fornecedor_id = %s;
  SELECT id FROM responsaveis WHERE usuario_id = %s;
  SELECT COUNT(*) AS total FROM pedidos WHERE responsavel_id = %s;
  ```
- Exclusão e log:
  ```sql
  DELETE FROM usuarios WHERE id = %s
  ```

## RF01.5 — Logs de Alterações

- Rotas:
  - `GET /usuarios/logs/<id>` — logs de um usuário específico.
  - `GET /usuarios/logs` — visão geral (opcionalmente filtrável por `acao`, `tabela`, `usuario_id`).
- SQLs:
  ```sql
  -- Por usuário
  SELECT l.*, u.nome as usuario_nome
  FROM logs_alteracoes l
  LEFT JOIN usuarios u ON l.usuario_id = u.id
  WHERE l.tabela = 'usuarios' AND l.registro_id = %s
  ORDER BY l.data_alteracao DESC;

  -- Geral
  SELECT l.*, u.nome as usuario_nome
  FROM logs_alteracoes l
  LEFT JOIN usuarios u ON l.usuario_id = u.id
  WHERE 1=1
  -- filtros opcionais: l.acao = %s, l.tabela = %s, l.usuario_id = %s
  ORDER BY l.data_alteracao DESC LIMIT 200;
  ```
- Formatação dos detalhes: `_preparar_detalhes_logs(logs)` converte `dados_antigos`/`dados_novos` de JSON e gera `mudancas` campo a campo, ignorando campos automáticos (`data_atualizacao`, `data_cadastro`, `id`) e ocultando padrões de IDs em `descricao`.

## Observações
- `usuarios.email` é `UNIQUE` (vide `schema.sql`).
- Sempre registrar operações críticas com `utils.registrar_log`.
- As validações de CPF/CNPJ são simplificadas em `utils` e podem ser substituídas por versões canônicas.
