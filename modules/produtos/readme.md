# RF06 - Manter Cadastro de Produto

Documento técnico do requisito funcional RF06, responsável por manter o ciclo completo de cadastro de produtos (uniformes) fornecidos às escolas homologadas. Este roteiro apresenta a visão de arquitetura, fluxos, dependências e rotinas auxiliares ligadas ao módulo de produtos.

## 1. Contexto e Objetivo
- Disponibilizar CRUD completo de produtos vinculado a fornecedores homologados.
- Garantir que fornecedores só manipulem seus próprios itens, preservando integridade multi-tenant entre escolas.
- Registrar toda alteração com trilha de auditoria enquanto protege rotas sensíveis via sessão Flask.

## 2. Visão Geral do Fluxo
1. Usuários autenticados acessam `/produtos` para listar itens disponíveis.
2. Perfis administradores e fornecedores podem abrir `/produtos/cadastrar` para criar novos registros.
3. Detalhes individuais são exibidos em `/produtos/detalhes/<id>` com ações de edição/exclusão.
4. Edições ocorrem em `/produtos/editar/<id>` reutilizando o formulário preenchido.
5. Exclusões são enviadas para `/produtos/excluir/<id>` após confirmação em modal/alerta do front-end.

## 3. Componentes Principais
- `modules/produtos/module.py`
  - Declara o blueprint `produtos_bp` com prefixo `/produtos`.
  - Implementa RF06.1 (`listar`), RF06.2 (`cadastrar`), RF06.3 (`editar`) e RF06.4 (`excluir`).
  - Rota complementar `detalhes` oferece visão expandida sem alterar dados.
- `templates/produtos/*.html`
  - Formulários e listagens em Bootstrap alinhados à UI global.
- `core/repositories.ProdutoRepository`
  - Encapsula acesso à tabela `produtos` (busca genérica, listagens especiais, vitrine).
- `core/services.CRUDService`
  - Aplica operações de persistência com logging automático no `LogService`.
- `core/services.AutenticacaoService`
  - Centraliza verificação de sessão/permissoes antes de operações críticas.
- `core.repositories.FornecedorRepository`
  - Resolve o `fornecedor_id` associado ao usuário logado do tipo fornecedor.

## 4. Templates e UX
- `templates/produtos/listar.html`
  - Tabela responsiva com ações em grupo; botão "Novo Produto" condicionado a permissões.
  - Script inline `confirmarExclusao` aciona POST para `/excluir/<id>`.
- `templates/produtos/cadastrar.html`
  - Formulário dividido em blocos, lista categorias pré-definidas e campos opcionais.
  - Para fornecedores logados injeta `fornecedor_id` oculto, evitando seleção manual.
- `templates/produtos/editar.html`
  - Reutiliza estrutura do cadastro, pré-populando valores e mantendo validações HTML5.
- `templates/produtos/detalhes.html`
  - Painel descritivo com badges de categoria/status, botões de ação condicionais e confirmação de exclusão.

## 5. Serviços e Camada Core
- `AutenticacaoService.verificar_sessao` e `.verificar_permissao` validam sessão e perfil antes de expor formulários.
- `CRUDService`
  - `criar_com_log`, `atualizar_com_log`, `excluir_com_log` envolvem a operação de repositório, disparam `LogService.registrar` e mensagens `flash` padronizadas.
  - `verificar_dependencias` executa checagens SQL customizadas antes de DELETE (ex.: `itens_pedido`).
- `ProdutoRepository`
  - Herdado de `BaseRepository`, fornece `buscar_por_id`, `listar`, `inserir`, `atualizar`, `excluir`.
- `FornecedorRepository.buscar_por_usuario_id`
  - Identifica fornecedoras vinculadas ao usuário autenticado para associar novos produtos.
- `Database`
  - Funções estáticas `executar`, `inserir`, `atualizar`, `excluir` encapsulam psycopg2, commits e rollbacks.

## 6. Configuração Necessária (`config.py`)
| Variável | Finalidade | Observações |
| --- | --- | --- |
| `DB_CONFIG` | Conexão PostgreSQL | Necessário para todas operações CRUD.
| `ITENS_POR_PAGINA` | Paginação de listagens | Disponível para futura paginação da rota `/listar`.
| `DEFAULT_UPLOAD_FOLDER`, `EXTENSOES_PERMITIDAS` | Upload de ativos | Permite expansão futura para anexar imagens de produtos.
| `MENSAGENS[...]` | Mensagens padrão | Reutilizadas via `flash` pelo `CRUDService`.

Carregar `.env` com credenciais válidas de banco e ajustar parâmetros de upload caso o módulo venha a aceitar mídia.

## 7. Modelo de Dados Relevante (`schema.sql`)
- `produtos`
  - FKs: `fornecedor_id` (obrigatória), `escola_id` (opcional) vinculando item ao contexto escolar.
  - Campos chave: `nome`, `preco`, `estoque`, `ativo`, `data_cadastro`, `data_atualizacao`.
- `fornecedores`
  - Mantém vínculo `usuario_id` usado para restringir CRUD de fornecedores.
- `itens_pedido`
  - Dependência impeditiva para exclusão: registros referenciam `produto_id`.
- Índices `idx_produtos_fornecedor` e `idx_produtos_escola` otimizam consultas filtradas.

## 8. Fluxo Detalhado RF06.1 - Listar Produtos
1. Rotas `/produtos/` e `/produtos/listar` chamam `listar()`.
2. `AutenticacaoService.verificar_sessao` tenta recuperar sessão; ausência não bloqueia leitura.
3. `Database.executar("SELECT * FROM produtos ORDER BY id DESC", fetchall=True)` retorna coleção de dicionários.
4. Template recebe `produtos`; badges exibem `categoria` e `ativo`.
5. Botão "Novo Produto" e ações de edição/exclusão aparecem somente para administradores/fornecedores logados.

## 9. Fluxo Detalhado RF06.2 - Criar Produto
1. `@produtos_bp.route('/cadastrar', methods=['GET', 'POST'])` exige `verificar_permissao(['administrador', 'fornecedor'])`.
2. GET: identifica fornecedor automaticamente quando usuário logado é fornecedor (`FornecedorRepository.buscar_por_usuario_id`).
3. POST: coleta formulário, sanitiza com `.strip()` e normaliza preço (`replace(',', '.')`).
4. Validação impede submissão sem `nome`, `fornecedor_id` ou `preco` (flash `danger`).
5. `crud_service.criar_com_log(dados, usuario_logado['id'])` insere registro via `ProdutoRepository.inserir`.
6. Em caso de sucesso: flash `success`, redireciona para `/produtos/listar`; falha retorna ao formulário com alerta.

## 10. Fluxo Detalhado RF06.3 - Editar Produto
1. `editar(id)` repete guarda de permissão (`administrador`/`fornecedor`).
2. Consulta `ProdutoRepository.buscar_por_id`; inexistência retorna flash `danger` e redireciona.
3. GET renderiza formulário preenchido; SELECT com `selected` por comparação direta.
4. POST monta `dados` com campos editáveis e normaliza preço.
5. `crud_service.atualizar_com_log(id, dados, dict(produto), usuario_logado['id'])` executa UPDATE + log.
6. Sucesso -> flash `success` e redirect listagem; erro mantém template com alerta `danger`.

## 11. Fluxo Detalhado RF06.4 - Excluir Produto
1. Rota POST `/produtos/excluir/<id>` valida permissão e existência do produto.
2. `crud_service.verificar_dependencias` avalia lista de bloqueios (atualmente `itens_pedido`).
3. Existindo dependências, concatena mensagens em flash `warning` e aborta exclusão.
4. Sem bloqueios, `crud_service.excluir_com_log(id, dict(produto), usuario_logado['id'])` executa DELETE e registra auditoria.
5. Template de listagem/detalhes submete formulário oculto após confirmação JavaScript.

## 12. Rota Auxiliar - Detalhes do Produto
- `/produtos/detalhes/<id>` aceita GET para renderizar visão completa do item.
- Utiliza `verificar_sessao` apenas para habilitar ações opcionais.
- Reaproveita badges, mostra estoque e mantém botão de exclusão com confirmação inline.

## 13. Permissões e Segurança
- Listagem e detalhes permitem visitantes autenticados ou não; ações destrutivas exigem sessão com tipo válido.
- Fornecedores ficam restritos aos seus próprios `fornecedor_id` na criação (via lookup) e edição/exclusão só devem ser oferecidas se o produto lhes pertence (responsabilidade do front-end + regras adicionais no repositório quando necessário).
- Dados críticos são protegidos por `session` (Flask) e mensagens `flash` informam tentativas sem permissão.

## 14. Observabilidade e Auditoria
- `CRUDService` envia todas alterações para `logs_alteracoes` (`ação`: INSERT/UPDATE/DELETE) com JSON antes/depois.
- Mensagens `flash` facilitam monitoramento manual durante demos.
- Dependências de exclusão evitam perda de rastreabilidade de pedidos: tentativas geram aviso explícito.

## 15. Testes Recomendados
- **CRUD completo administrador**: cadastro, edição, exclusão de produto com dados válidos.
- **Fluxo fornecedor**: login como fornecedor, cadastro automático com `fornecedor_id` próprio e tentativa de manipular item de outro fornecedor (esperado bloqueio).
- **Validação obrigatória**: enviar formulário sem `nome` ou `preço` para checar flash de erro.
- **Dependência de pedido**: vincular produto a `itens_pedido` e tentar excluir (deve bloquear e emitir `warning`).
- **Permissão negada**: acessar `/produtos/cadastrar` como usuário sem tipo autorizado e validar redirect para `home` com alerta.
- **Listagem pública**: acessar `/produtos/listar` sem login; tabela deve carregar (quando dados disponíveis) sem ações privilegiadas.

## 16. Checklist de Implantação
1. Aplicar `schema.sql` garantindo existência de tabelas `produtos`, `fornecedores`, `itens_pedido` e índices.
2. Configurar `.env` com DSN válido de PostgreSQL e ajustar variáveis de upload se houver mídia associada.
3. Realizar smoke test dos cenários descritos na seção 15.
4. Validar logs em `logs_alteracoes` após operações de insert/update/delete.
5. Monitorar estoque inicial e status `ativo` para evitar exibição inadvertida em vitrine/vendas.

---

Para futuras extensões (imagens, padronização de preços, integrações com estoque externo), planeje uso das configurações de upload, inclusão de validações adicionais no `CRUDService` ou criação de serviços específicos para sincronização.