# RF07 — Repasses Financeiros (modules/repasses.py)

Administra repasses para fornecedores com base nos pedidos pagos.

- Blueprint: `repasses_bp`
- Prefixo: `/repasses`
- Tabelas: `repasses_financeiros`, `fornecedores`, `usuarios`, `pedidos`, `produtos`, `itens_pedido`
- Dependências:
  - `utils.py`: `executar_query`, `registrar_log`, `formatar_dinheiro`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - `config.py`: `TAXA_PLATAFORMA_PERCENTUAL`
  - Templates: `templates/repasses/listar.html`

## RF07.2 — Listar Repasses

- Rotas: `GET /repasses/`, `GET /repasses/listar`
- Se tipo `fornecedor`, filtra pelos repasses do fornecedor logado:
  ```sql
  SELECT id FROM fornecedores WHERE usuario_id = %s
  ```
  Ajuste na listagem:
  ```sql
  SELECT r.*, f.razao_social as fornecedor_nome, u.nome
  FROM repasses_financeiros r
  JOIN fornecedores f ON r.fornecedor_id = f.id
  JOIN usuarios u ON f.usuario_id = u.id
  -- se fornecedor
  WHERE r.fornecedor_id = %s
  ORDER BY r.data_repasse DESC
  ```

## RF07.1 — Gerar Repasses (Admin)

- Rota: `POST /repasses/gerar/<pedido_id>`
- Pré-condição: `pedidos.status = 'pago'`.
- SQLs:
  - Validar pedido pago:
    ```sql
    SELECT * FROM pedidos WHERE id = %s AND status = 'pago'
    ```
  - Itens do pedido, agregados por fornecedor:
    ```sql
    SELECT p.fornecedor_id, SUM(i.subtotal) as valor_total
    FROM itens_pedido i
    JOIN produtos p ON i.produto_id = p.id
    WHERE i.pedido_id = %s
    GROUP BY p.fornecedor_id
    ```
  - Para cada fornecedor, calcula `taxa = valor * (TAXA_PLATAFORMA_PERCENTUAL/100)` e insere:
    ```sql
    INSERT INTO repasses_financeiros 
    (fornecedor_id, pedido_id, valor, taxa_plataforma, valor_liquido, status)
    VALUES (%s, %s, %s, %s, %s, 'pendente')
    ```

## RF07.3 — Processar Repasse (Admin)

- Rota: `POST /repasses/processar/<id>`
- SQL:
  ```sql
  UPDATE repasses_financeiros 
  SET status = 'concluido', data_processamento = CURRENT_TIMESTAMP
  WHERE id = %s
  ```
- Log: `registrar_log(..., 'repasses_financeiros', id, 'UPDATE', descricao='Repasse processado')`.

## RF07.4 — Cancelar Repasse (Admin)

- Rota: `POST /repasses/cancelar/<id>`
- SQL:
  ```sql
  UPDATE repasses_financeiros SET status = 'cancelado' WHERE id = %s
  ```
- Log: `registrar_log(..., 'repasses_financeiros', id, 'UPDATE', descricao='Repasse cancelado')`.

## Observações
- `status` permitido: `pendente`, `processando`, `concluido`, `cancelado` (vide `schema.sql`).
- A taxa de plataforma é configurável em `config.py` e aplicada no momento da geração.
