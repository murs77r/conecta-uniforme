# RF04 - Gestores Escolares

Documento tecnico de apresentacao do requisito funcional RF04 (Manter Cadastro de Gestor Escolar). Este roteiro descreve componentes, fluxos, dependencias e rotinas de suporte que viabilizam o CRUD de gestores associados a cada escola cadastrada.

## 1. Contexto e Objetivo
- Permitir que administradores ou escolas mantenham varios gestores vinculados a uma mesma unidade.
- Registrar informacoes de contato (email, telefone) e dados opcionais (CPF, tipo de gestor) para facilitar comunicacao e auditoria.
- Garantir que apenas o dono da escola ou administradores possam consultar e alterar gestores.

## 2. Visao Geral do Fluxo
1. Usuario autenticado navega para `/gestores/escola/<id>` a partir da tela da escola.
2. Sistema valida sessao, confirma existencia da escola e checa autorizacao (tipo administrador ou escola proprietaria).
3. Listagem apresenta todos os gestores da escola, com acoes de detalhes, edicao e exclusao.
4. Acao "Novo Gestor" redireciona para formulario `/gestores/escola/<id>/cadastrar` com validacoes de servidor.
5. Edicoes utilizam `/gestores/editar/<id>` e carregam dados atuais do gestor antes de persistir alteracoes.
6. Exclusoes executam POST em `/gestores/excluir/<id>` com confirmacao no front-end e registro em log.

## 3. Componentes Principais
- `modules/gestores/module.py`
  - Blueprint `gestores_bp` com prefixo `/gestores` concentrando todas as rotas RF04.
  - Reuso central de `AutenticacaoService` para validar sessao em cada endpoint.
  - Instancias de `GestorEscolarRepository` e `EscolaRepository` para isolar acesso ao banco.
  - Rotas implementam os subitens RF04.1 (listar), RF04.2 (cadastrar), RF04.3 (editar) e RF04.4 (excluir), alem da rota complementar de detalhes.
- `modules/escolas/module.py`
  - Navegacao primária: botoes e links acionam as rotas de gestores a partir das paginas de escola.
- `app.py`
  - Registra `gestores_bp` durante a inicializacao da aplicacao Flask, disponibilizando o modulo para toda a aplicacao.

## 4. Templates e UX
- `templates/gestores/listar.html`
  - Renderiza tabela responsiva com botoes para detalhes, edicao e exclusao.
  - Traz cabecalho com nome da escola e atalho "Novo Gestor".
- `templates/gestores/cadastrar.html`
  - Formulario Clean com campos opcionais e obrigatorios, utilizando placeholders para orientar preenchimento.
  - Botoes de voltar e confirmar mantem consistencia com demais modulos.
- `templates/gestores/editar.html`
  - Preenche campos com dados atuais permitindo ajustes pontuais.
- `templates/gestores/detalhes.html`
  - Exibe painel com informacoes completas do gestor e dados resumidos da escola vinculada.
- `static/js/base.js`
  - Converte mensagens `flash` em modais padronizados, garantindo feedback uniforme para erros e sucessos.

## 5. Servicos e Camada Core
- `core.services.AutenticacaoService`
  - `verificar_sessao` retorna usuario logado para proteger cada rota.
- `core.services.ValidacaoService`
  - `validar_telefone` e `validar_cpf` garantem formato basico antes de gravar.
- `core.services.LogService`
  - Persistencia em `logs_alteracoes` para INSERT, UPDATE e DELETE, com descricao especifica do evento.
- `core.repositories.GestorEscolarRepository`
  - Encapsula CRUD na tabela `gestores_escolares`, incluindo `listar_por_escola`.
- `core.repositories.EscolaRepository`
  - `buscar_com_usuario` retorna metadados da escola e do usuario proprietario para validacao de permissao.
- `core.database.Database`
  - Gerencia conexoes PostgreSQL, execucao de queries com commits explicitos e tratamento de excecoes.

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Observacao |
| --- | --- | --- |
| `SECRET_KEY` | Assina cookies de sessao usados por `AutenticacaoService` | Obrigatorio para manter sessao valida |
| `DB_CONFIG` | Parametros de conexao PostgreSQL para `Database` | Deve apontar para instancia com tabela `gestores_escolares` aplicada |
| `DEBUG` | Controla exibicao de mensagens detalhadas e comportamento de flash | Em desenvolvimento facilita diagnostico de validacoes |

## 7. Modelo de Dados Relevante (`schema.sql`)
- `gestores_escolares`
  - Campos: `id`, `escola_id`, `nome`, `email`, `telefone`, `cpf`, `tipo_gestor`, `data_cadastro`.
  - `escola_id` referencia `escolas(id)` com `ON DELETE CASCADE`, herdando exclusoes de escola.
  - Indice `idx_gestores_escola` acelera listagens por escola.
- `logs_alteracoes`
  - Recebe registros de auditoria para inserir, atualizar e excluir gestores.

## 8. Fluxo Detalhado RF04.1 - Listar Gestores
1. Recebe `escola_id` pela rota `/gestores/escola/<int:escola_id>` (ou alias `/listar`).
2. Executa `auth_service.verificar_sessao`; sessao invalida redireciona para `/auth/solicitar-codigo`.
3. `escola_repo.buscar_com_usuario` valida existencia e recupera dono da escola.
4. Permissao: permite acesso apenas a administradores ou usuarios do tipo escola proprietaria.
5. `gestor_repo.listar_por_escola` retorna dados ordenados pelo nome.
6. Template `gestores/listar.html` recebe `escola` e `gestores`, exibindo botoes de acao condicionados ao resultado.

## 9. Fluxo Detalhado RF04.2 - Cadastrar Gestor
1. GET `/gestores/escola/<id>/cadastrar` reaproveita as validacoes basicas e renderiza formulario vazio.
2. POST coleta campos via `request.form`, normaliza espacos e converte email para minusculas.
3. Nome obrigatorio; ausencia gera `flash` `danger` e re-renderizacao do formulario com contexto da escola.
4. `ValidacaoService.validar_telefone` e `validar_cpf` garantem formatos basicos (campos sao opcionais, mas se preenchidos precisam ser validos).
5. `gestor_repo.inserir` grava registro; ID retornado aciona `LogService.registrar` (acao `INSERT`).
6. Mensagem `success` confirma criacao e redireciona para `/gestores/escola/<id>/listar`.

## 10. Fluxos Detalhados RF04.3 e RF04.4 - Editar e Excluir Gestor
- **RF04.3 - Editar Gestor**
  1. GET `/gestores/editar/<id>` valida sessao, busca gestor e escola vinculada.
  2. Permissao mantem mesma regra: administrador ou escola proprietaria.
  3. Dados atuais sao enviados ao template `gestores/editar.html` (campanha `escola_nome`, `escola_id`).
  4. POST aplica mesmas validacoes de nome, telefone e CPF.
  5. `gestor_repo.atualizar` persiste mudancas; sucesso gera `LogService.registrar` com `dados_antigos` e `dados_novos`.
  6. Redireciona para listagem da escola com mensagem `success`.
- **RF04.4 - Excluir Gestor**
  1. POST `/gestores/excluir/<id>` apenas apos confirmacao no frontend.
  2. Valida sessao, existente do gestor e escola proprietaria.
  3. `gestor_repo.excluir` remove registro; `LogService.registrar` grava acao `DELETE` com dados antigos para rastreabilidade.
  4. Usuario e redirecionado para listagem da escola com mensagem de sucesso.

## 11. Permissoes Complementares e Rota de Detalhes
- Rota `/gestores/detalhes/<id>` reusa mesmos guardas de sessao e permissao antes de expor informacoes sensiveis.
- Apenas administradores e escolas controladoras conseguem visualizar detalhes completos.
- Detalhes agregam `escola` e `gestor` para facilitar consultas e acoes subsequentes (editar ou excluir) com botoes contextuais.

## 12. Tratamento de Erros e Seguranca
- Todas as rotas verificam autenticacao antes de qualquer acesso ao banco.
- Falta de permissao aciona `flash('Acesso negado.', 'danger')` e redireciona para `home` ou listagem apropriada.
- Dados opcionais sao saneados (trim, lower) e validados para evitar gravacao inconsistente.
- Exclusoes dependem de confirmacao HTML `onsubmit` evitando acoes acidentais.
- `redirect` apos operacoes POST evita reenvio de formulario (Post/Redirect/Get).

## 13. Observabilidade e Auditoria
- `LogService` grava todas as alteracoes (INSERT/UPDATE/DELETE) em `logs_alteracoes` com JSON serializado de dados.
- Mensagens `flash` informam resultado ao usuario e sao exibidas como modais via `static/js/base.js`.
- Acompanhar evolucao via `templates/logs/logs.html` (modulo de logs) durante apresentacoes ou auditorias.

## 14. Testes Recomendados
- **Listagem autorizada**: acessar `/gestores/escola/<id>` como administrador e como escola proprietaria; verificar exibicao correta.
- **Bloqueio de permissao**: tentar acessar listagem como fornecedor ou escola nao proprietaria; deve redirecionar com aviso de acesso negado.
- **Cadastro valido**: criar gestor com dados completos e confirmar registro no banco e log de alteracao.
- **Cadastro invalido**: enviar formulario sem nome ou com CPF/telefone invalido; validar mensagens e permanencia na pagina.
- **Edicao**: alterar apenas telefone ou tipo e garantir que log registre `dados_antigos` x `dados_novos`.
- **Exclusao**: remover gestor e confirmar cascateamento de permissao e registro de log.

## 15. Checklist de Implantacao
1. Aplicar `schema.sql` garantindo existencia de `gestores_escolares`, indices e `logs_alteracoes`.
2. Configurar `.env` com `SECRET_KEY`, `DB_CONFIG` e demais variaveis utilizadas pelo app.
3. Realizar smoke test dos fluxos (listar, cadastrar, editar, excluir) em usuario administrador e escola proprietaria.
4. Validar visibilidade dos registros em `logs_alteracoes` e monitorar mensagens flash no frontend.
5. Repassar roteiro de apresentacao destacando links de navegacao a partir de `escolas/detalhes`.

---

Expansoes futuras podem incluir busca textual de gestores, anexos de documentos ou notificacoes automaticas; avaliar impacto em `GestorEscolarRepository` e em novos campos na tabela `gestores_escolares` antes de evoluir o requisito.
