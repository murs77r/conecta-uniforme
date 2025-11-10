# RF07 - Manter Cadastro de Pedido

Documento tecnico de apresentacao do requisito funcional RF07 (Manter Cadastro de Pedido). Este roteiro detalha componentes, fluxos, dependencias e artefatos de apoio que viabilizam o CRUD completo de pedidos, incluindo filtros por perfil e trilha de auditoria.

## 1. Contexto e Objetivo
- Permitir que responsaveis e administradores acompanhem pedidos apos autenticacao.
- Garantir controle de ciclo de vida (criar, editar, cancelar, detalhar) com registro de auditoria.
- Manter restricao de visibilidade para responsaveis, exibindo apenas os proprios pedidos.

## 2. Visao Geral do Fluxo
1. Usuario autenticado acessa `/pedidos/listar` para consultar pedidos ativos (exceto status `carrinho`).
2. A partir da listagem, pode abrir detalhamento, editar status/valor ou acionar exclusao.
3. Formulario `/pedidos/criar` cria novos pedidos administrativos informando IDs de relacao e status inicial.
4. Rotas de atualizacao e exclusao registram auditoria via `LogService` e retornam mensagem flash.
5. Consulta detalhada monta cabecalho do pedido, responsavel, escola e itens, com restricoes por perfil.

## 3. Componentes Principais
- `modules/pedidos/module.py`
  - Blueprint `pedidos_bp` (`/pedidos`) com handlers para RF07.1 a RF07.4.
  - Instancias compartilhadas de `PedidoRepository` e `ResponsavelRepository` para consultas auxiliares.
  - Uso direto de `Database` para operacoes pontuais (SELECT, INSERT, UPDATE, DELETE) e `LogService.registrar` para auditoria.
- `modules/pedidos/__init__.py`
  - Expone `pedidos_bp` para registro em `app.py`.
- `app.py`
  - Registra blueprint (RF07) e injeta `usuario_logado` via context processor, utilizado em templates para regras de exibicao.

## 4. Templates e UX
- `templates/pedidos/listar.html`
  - Tabela responsiva com colunas dinamicas (escola visivel apenas para administradores) e badgets de status.
  - Botoes de acao alinhados a cada linha (detalhar, editar, excluir) e fallback de lista vazia.
- `templates/pedidos/criar.html`
  - Formulario simples para insercao manual de IDs relacionados, status e valor total.
- `templates/pedidos/editar.html`
  - Preenche status atual e valor do pedido, destacando informacoes chave em alerta informativo.
- `templates/pedidos/detalhes.html`
  - Agrupa informacoes do pedido, responsavel, escola e itens em cards tematicos, com badgets de status e botoes de acao finais.
- `static/js/base.js`
  - Converte mensagens flash produzidas nas rotas em modais padronizados (mesmo comportamento dos demais modulos).

## 5. Servicos e Camada Core
- `core.services.AutenticacaoService`
  - `verificar_sessao` valida sessao antes de qualquer operacao de pedido; garante retorno para fluxo de autenticacao quando ausente.
- `core.services.LogService`
  - `registrar` grava INSERT/UPDATE/DELETE em `logs_alteracoes`, preservando trilha de auditoria.
- `core.repositories.PedidoRepository`
  - Disponibiliza utilitarios (ex. `listar_por_responsavel`, `buscar_carrinho`) usados por outros fluxos e fornece nomenclatura centralizada da tabela.
- `core.repositories.ResponsavelRepository`
  - `buscar_por_usuario_id` vincula usuario logado ao registro de responsavel, restringindo listagem e detalhes.
- `core.database.Database`
  - Executa queries PostgreSQL com RealDictCursor, commit explicito e rollback automatico em caso de erro.

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Default |
| --- | --- | --- |
| `DB_CONFIG` | Parametros de conexao PostgreSQL consumidos por `Database` | `localhost:5432` etc. |
| `SECRET_KEY` | Assina cookies de sessao usados por `AutenticacaoService` | `change-me` |
| `DEBUG` | Ativa modais de aviso e logging mais verboso | `true` |
| `MENSAGENS` | Mensagens padrao globais (nao utilizadas diretamente aqui, mas mantem consistencia com outros modulos) | ver `config.py` |

## 7. Modelo de Dados Relevante (`schema.sql`)
- `pedidos`
  - Campos chave: `responsavel_id`, `escola_id`, `valor_total`, `status`, `data_pedido`, `observacoes`.
  - Constraint `CHECK` garante status valido (`carrinho`, `pendente`, `pago`, `enviado`, `entregue`, `cancelado`).
- `itens_pedido`
  - Relaciona produtos ao pedido, guardando quantidade, preco e subtotal.
- `responsaveis` e `usuarios`
  - Permitem identificar dono do pedido e controlar permissao por perfil.
- `logs_alteracoes`
  - Cade avaliacoes de auditoria gravadas por `LogService` (INSERT/UPDATE/DELETE de pedidos).

## 8. Fluxo Detalhado RF07.4 - Listar
1. Rotas `/pedidos/` e `/pedidos/listar` chamam `auth_service.verificar_sessao`; sem sessao, redirecionam para `/auth/solicitar-codigo` com flash `warning`.
2. Query base junta `pedidos`, `responsaveis`, `usuarios` e, opcionalmente, `escolas` para enriquecer exibicao.
3. Usuarios do tipo `responsavel` sao filtrados para exibir somente pedidos proprios; ausentando vinculo, devolve lista vazia.
4. Ordena por `data_pedido DESC` e renderiza `listar.html` com a colecao.

## 9. Fluxo Detalhado RF07.1 - Criar Pedido
1. GET renderiza formulario limpo (`criar.html`) apos validar sessao.
2. POST coleta `responsavel_id`, `escola_id`, `status` (default `pendente`) e `valor_total`.
3. `Database.inserir('pedidos', dados)` persiste registro e retorna `pedido_id`.
4. Sucesso aciona `LogService.registrar(..., acao='INSERT')`, mostra flash `success` e redireciona para listagem.
5. Falha gera flash `danger`, mantendo usuario na pagina de criacao.

## 10. Fluxo Detalhado RF07.3 - Editar Pedido
1. Rota `/pedidos/editar/<id>` valida sessao e busca pedido via SELECT.
2. Pedido inexistente retorna flash `danger` e redireciona para listagem.
3. POST atualiza `status` e `valor_total` com `Database.atualizar`, que tambem atualiza `data_atualizacao`.
4. Sucesso registra auditoria (`acao='UPDATE'`) e redireciona com flash `success`; caso contrario, apresenta flash `danger`.
5. GET popula formulario com dados atuais e resumo informativo para consulta rapida.

## 11. Fluxo Detalhado RF07.2 - Apagar Pedido
1. Endpoint `/pedidos/apagar/<id>` (POST) exige sessao valida; falha redireciona para `home` com flash `danger`.
2. Executa `DELETE FROM pedidos WHERE id = %s` via `Database.executar` com commit implicito.
3. Sucesso dispara `LogService.registrar(..., acao='DELETE')` e flash `success`; falha retorna flash `danger`.
4. Em ambos os casos, usuario retorna para listagem.

## 12. Fluxo Detalhado RF07.4 - Detalhes
1. Rota `/pedidos/detalhes/<id>` valida sessao e executa query enriquecida com dados do responsavel e da escola.
2. Inexistencia do pedido produz flash `danger` e redirecionamento para listagem.
3. Quando usuario logado e `responsavel`, valida se o pedido pertence ao mesmo `responsavel_id`; caso contrario, nega acesso.
4. Busca itens associados em `itens_pedido` com join em `produtos` para nomes, descricoes e imagens.
5. Renderiza `detalhes.html` com cards tematicos, tabela de itens e acoes de editar/excluir.

## 13. Regras de Permissao e Seguranca
- Todas as rotas passam por `AutenticacaoService.verificar_sessao`; ausencia de sessao redireciona para autenticao RF02.
- Responsaveis apenas visualizam pedidos proprios (checagem cruzada entre sessao e `responsavel_id`).
- Exclusao exige POST para evitar acionamento via link GET e inclui confirmacao JavaScript no template.
- `flash` com categorias `warning` e `danger` sinalizam tentativas sem permissao.

## 14. Tratamento de Erros e Auditoria
- Falhas de insercao/atualizacao/exclusao retornam feedback imediato com `flash('Erro...', 'danger')`.
- Queries usam `Database.executar`, que possui rollback automatico em excecoes e imprime erros no console (ambiente dev).
- `LogService.registrar` garante rastreabilidade de todas as operacoes mutaveis em `logs_alteracoes`.
- Templates suportam cenario de colecoes vazias (listar) e exibem placeholders quando dados ausentes (ex.: escola opcional).

## 15. Testes Recomendados
- **Crud completo**: Criar pedido e confirmar visualizacao na listagem e nos detalhes.
- **Restricao por perfil**: Logar como responsavel e tentar acessar pedido de outro responsavel (deve bloquear).
- **Atualizacao de status**: Alterar status e verificar mudanca do badge na listagem.
- **Exclusao**: Excluir pedido e garantir que sumiu da listagem e que log de auditoria foi gravado.
- **Dados faltantes**: Criar pedido sem `escola_id` para validar exibicao de placeholder e ausencia de card de escola.
- **Carga de itens**: Garantir que itens vinculados aparecam corretamente no detalhe.

## 16. Checklist de Implantacao
1. Aplicar `schema.sql` (garantindo constraints de status e relacionamentos com responsaveis/escolas/produtos).
2. Popular tabelas de `responsaveis`, `escolas`, `produtos` e `itens_pedido` conforme ambiente de demonstracao.
3. Validar conectividade com PostgreSQL (`/health/db`) antes de apresentar o fluxo.
4. Realizar smoke test dos cenarios listados na secao 15.
5. Monitorar `logs_alteracoes` para confirmar registros de CREATE/UPDATE/DELETE durante a apresentacao.

---

Para evolucoes futuras (ex.: gerenciamento de carrinho, workflow de faturamento, notificacoes), reutilizar `PedidoRepository` para listar carrinhos ativos e introduzir servicos dedicados para calculo de valor total e disparo de e-mails de status.
