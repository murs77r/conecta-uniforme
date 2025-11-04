# RF06 — Pedidos (modules/pedidos.py)

Gerencia carrinho e pedidos: criação, listagem, finalização e cancelamento.

- Blueprint: `pedidos_bp`
- Prefixo: `/pedidos`
- Tabelas: `pedidos`, `itens_pedido`, `produtos`, `responsaveis`, `usuarios`
- Dependências:
  - `utils.py`: `executar_query`, `registrar_log`, `formatar_dinheiro`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/pedidos/*.html`

## RF06.2 — Listar Pedidos

- Rotas: `GET /pedidos/`, `GET /pedidos/listar`
- Tela: `templates/pedidos/listar.html`
- Regra: esconde pedidos com `status = 'carrinho'`.
- Se usuário `responsavel`, filtra pelos seus próprios pedidos (via tabela `responsaveis`).
- SQL:
  ```sql
  SELECT p.*, r.usuario_id, u.nome as responsavel_nome
  FROM pedidos p
  JOIN responsaveis r ON p.responsavel_id = r.id
  JOIN usuarios u ON r.usuario_id = u.id
  WHERE p.status != 'carrinho'
  -- se responsavel
  AND p.responsavel_id = %s
  ORDER BY p.data_pedido DESC
  ```

## RF06.1 — Adicionar ao Carrinho

- Rota: `POST /pedidos/adicionar-carrinho/<produto_id>`
- Permissão: `responsavel`.
- Passos:
  1. Descobre `responsavel_id` pelo usuário logado:
     ```sql
     SELECT id FROM responsaveis WHERE usuario_id = %s
     ```
  2. Busca produto ativo e com estoque:
     ```sql
     SELECT * FROM produtos WHERE id = %s AND ativo = TRUE
     ```
  3. Verifica `quantidade` solicitada <= `produto.estoque`.
  4. Busca (ou cria) o carrinho (pedido com `status = 'carrinho'`):
     ```sql
     SELECT id FROM pedidos 
     WHERE responsavel_id = %s AND status = 'carrinho'
     ORDER BY data_pedido DESC LIMIT 1
     ```
     Se não existir, cria:
     ```sql
     INSERT INTO pedidos (responsavel_id, escola_id, status, valor_total)
     VALUES (%s, %s, 'carrinho', 0)
     RETURNING id
     ```
  5. Adiciona item:
     ```sql
     INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
     VALUES (%s, %s, %s, %s, %s)
     ```
  6. Recalcula total:
     ```sql
     SELECT SUM(subtotal) as total FROM itens_pedido WHERE pedido_id = %s;
     UPDATE pedidos SET valor_total = %s WHERE id = %s;
     ```

## Ver Carrinho

- Rota: `GET /pedidos/carrinho`
- Permissão: `responsavel`.
- SQLs:
  ```sql
  SELECT id FROM responsaveis WHERE usuario_id = %s;
  SELECT * FROM pedidos 
  WHERE responsavel_id = %s AND status = 'carrinho'
  ORDER BY data_pedido DESC LIMIT 1;
  SELECT i.*, p.nome as produto_nome, p.descricao, p.imagem_url
  FROM itens_pedido i
  JOIN produtos p ON i.produto_id = p.id
  WHERE i.pedido_id = %s;
  ```
- Tela: `templates/pedidos/carrinho.html`

## RF06.1 — Finalizar Pedido

- Rota: `POST /pedidos/finalizar/<id>`
- Permissão: `responsavel`.
- SQL:
  ```sql
  UPDATE pedidos SET status = 'pendente', data_atualizacao = CURRENT_TIMESTAMP WHERE id = %s
  ```
- Log: `registrar_log(..., 'pedidos', id, 'UPDATE', descricao='Pedido finalizado')`.

## RF06.4 — Cancelar Pedido

- Rota: `POST /pedidos/cancelar/<id>`
- Permissão: qualquer usuário autenticado.
- SQL:
  ```sql
  UPDATE pedidos SET status = 'cancelado' WHERE id = %s
  ```
- Log: `registrar_log(..., 'pedidos', id, 'UPDATE', descricao='Pedido cancelado')`.

## Observações
- `status` permitido conforme `schema.sql`: `carrinho`, `pendente`, `pago`, `enviado`, `entregue`, `cancelado`.
- Regras de pagamento/estoque avançadas podem ser incluídas em etapas futuras (baixa de estoque, gateways etc.).
