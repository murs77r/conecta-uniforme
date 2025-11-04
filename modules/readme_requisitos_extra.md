# Visão cruzada de dependências entre módulos

- Autenticação (RF02) oferece `verificar_sessao` e `verificar_permissao` usados por todos os outros módulos.
- Usuários (RF01) é a base de perfis; `escolas`, `fornecedores` e `responsaveis` referenciam `usuarios(usuario_id)` 1:1.
- Produtos (RF03) referenciam `fornecedores` e opcionalmente `escolas`.
- Pedidos (RF06) referenciam `responsaveis` e `escolas`; `itens_pedido` referenciam `pedidos` e `produtos`.
- Repasses (RF07) computam valores a partir de `itens_pedido` + `produtos` por `fornecedor_id`.
- Homologação (em RF04) relaciona `escolas` e `fornecedores`.

Consulte os READMEs específicos para SQLs detalhados e rotas.
