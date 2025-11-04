# RF03 — Produtos e Vitrine (modules/produtos.py)

Gerencia o catálogo de produtos (uniformes) e a vitrine para navegação/compra.

- Blueprint: `produtos_bp`
- Prefixo: `/produtos`
- Tabelas: `produtos`, `fornecedores`, `escolas`, `itens_pedido` (para validação de exclusão)
- Dependências:
  - `utils.py`: `executar_query`, `registrar_log`, `formatar_dinheiro`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/produtos/*.html`

## RF03.2 — Vitrine (listar)

- Rotas: `GET /produtos/`, `GET /produtos/vitrine`
- Tela: `templates/produtos/vitrine.html`
- Filtros: `categoria`, `escola`, `busca` (nome/descrição)
- SQL:
  ```sql
  SELECT p.*, f.razao_social as fornecedor_nome, e.razao_social as escola_nome
  FROM produtos p
  JOIN fornecedores f ON p.fornecedor_id = f.id
  LEFT JOIN escolas e ON p.escola_id = e.id
  WHERE p.ativo = TRUE AND p.estoque > 0
  -- categoria
  AND p.categoria = %s
  -- escola
  AND p.escola_id = %s
  -- busca
  AND (p.nome ILIKE %s OR p.descricao ILIKE %s)
  ORDER BY p.nome
  ```
- Carrega também escolas ativas para filtro:
  ```sql
  SELECT e.id, u.nome FROM escolas e JOIN usuarios u ON e.usuario_id = u.id WHERE e.ativo = TRUE ORDER BY u.nome
  ```

## RF03.1 — Cadastrar Produto

- Rota: `GET|POST /produtos/cadastrar`
- Permissões: `administrador` ou `fornecedor`.
- GET: se usuário é `fornecedor`, busca seu `fornecedor_id`:
  ```sql
  SELECT id FROM fornecedores WHERE usuario_id = %s
  ```
  Também carrega lista de escolas ativas:
  ```sql
  SELECT e.id, u.nome FROM escolas e JOIN usuarios u ON e.usuario_id = u.id WHERE e.ativo = TRUE ORDER BY u.nome
  ```
- POST: campos principais `nome`, `descricao`, `categoria`, `tamanho`, `cor`, `preco`, `estoque`, `escola_id` e `fornecedor_id` (se admin). Inserção:
  ```sql
  INSERT INTO produtos (fornecedor_id, escola_id, nome, descricao, categoria, tamanho, cor, preco, estoque, ativo)
  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
  RETURNING id
  ```
- Registra log `INSERT`.

## RF03.3 — Editar Produto

- Rota: `GET|POST /produtos/editar/<id>`
- Permissões: `administrador` ou `fornecedor`.
- Buscar:
  ```sql
  SELECT * FROM produtos WHERE id = %s
  ```
- Atualizar:
  ```sql
  UPDATE produtos 
  SET nome = %s, preco = %s, estoque = %s, data_atualizacao = CURRENT_TIMESTAMP
  WHERE id = %s
  ```
- Registra log `UPDATE`.

## RF03.4 — Excluir Produto

- Rota: `POST /produtos/excluir/<id>`
- Antes de excluir, valida vínculos com itens de pedido:
  ```sql
  SELECT COUNT(*) AS total FROM itens_pedido WHERE produto_id = %s
  ```
- Exclusão:
  ```sql
  DELETE FROM produtos WHERE id = %s
  ```
- Registra log `DELETE`.

## Observações
- Produtos podem (ou não) ser vinculados a uma `escola_id` (campo opcional).
- Exclusão é bloqueada caso já existam itens de pedido associados.
- `formatar_dinheiro` está disponível para exibição, embora o módulo não a use diretamente nas rotas atuais.
