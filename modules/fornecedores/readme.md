# RF05 - Manter Cadastro de Fornecedor

Documento tecnico de apresentacao do requisito funcional RF05 (Manter Cadastro de Fornecedor). Este roteiro cobre os componentes, fluxos, dependencias e rotinas de suporte que viabilizam o CRUD completo de fornecedores dentro do Conecta Uniforme.

## 1. Contexto e Objetivo
- Centralizar o cadastro de fornecedores vinculados a um usuario do tipo `fornecedor`.
- Permitir que administradores gerenciem o ciclo de vida (criar, editar, excluir) e que fornecedores mantenham seus dados basicos.
- Garantir rastreabilidade das operacoes por meio de logs de auditoria e bloqueios quando ha relacionamentos ativos.

## 2. Visao Geral do Fluxo
1. Usuarios autenticados acessam `/fornecedores/listar` para visualizar o catalogo.
2. Administradores podem abrir `/fornecedores/cadastrar` para registrar novos parceiros.
3. Administradores e fornecedores acessam `/fornecedores/editar/<id>` para manter dados.
4. A rota `/fornecedores/detalhes/<id>` apresenta painel completo com contagem de produtos.
5. Exclusao ocorre via POST em `/fornecedores/excluir/<id>` com checagem de dependencias.
6. Todas as rotas dependem da sessao Flask populada pelo RF02 (Autenticacao por codigo).

## 3. Componentes Principais
- `modules/fornecedores/module.py`
  - Define o blueprint `fornecedores_bp` (prefixo `/fornecedores`).
  - Implementa rotas `listar`, `cadastrar`, `editar`, `detalhes` e `excluir`, cobrindo RF05.1 a RF05.4.
  - Orquestra autenticao/permissoes (`AutenticacaoService`), validacoes (`ValidacaoService`) e persistencia (`CRUDService`).
- `modules/fornecedores/__init__.py`
  - Expone o blueprint para registro em `app.py`.
- `app.py`
  - Registra o blueprint garantindo que o requisito esteja disponivel na aplicacao principal.

## 4. Templates e UX
- `templates/fornecedores/listar.html`
  - Lista fornecedores com acoes condicionadas ao tipo de usuario (botao de cadastro/exclusao apenas para administradores).
  - Exibe status ativo/inativo e dados de contato alinhados em tabela responsiva.
- `templates/fornecedores/cadastrar.html`
  - Formulario dividido entre "Dados de Acesso" (usuario) e "Dados da Empresa" (fornecedor).
  - Campos obrigatorios marcados com `*`; botoes de voltar e confirmar seguem padrao visual Bootstrap.
- `templates/fornecedores/editar.html`
  - Replica layout do cadastro, mantendo CNPJ bloqueado (`disabled`) com aviso textual.
  - Campos populados com os dados atuais do fornecedor.
- `templates/fornecedores/detalhes.html`
  - Dashboard com cards segmentados (empresa, contato, endereco, informacoes adicionais).
  - Mostra badges de status, contagem de produtos (`total_produtos`) e zona de perigo para exclusao quando usuario e administrador.
- `base.html` e `static/js/base.js`
  - Oferecem shell comun, exibem mensagens `flash` e disponibilizam o objeto `usuario_logado` injetado pelo `context_processor` de `app.py`.

## 5. Servicos e Camada Core
- `core.services.AutenticacaoService`
  - `verificar_sessao` protege listagem/detalhes; `verificar_permissao` restringe cadastro/edicao/exclusao.
- `core.services.ValidacaoService`
  - `validar_cnpj` garante formato minimo antes da escrita em banco (complementado por constraint unica em `schema.sql`).
- `core.services.CRUDService`
  - Encapsula `INSERT/UPDATE/DELETE` com `LogService.registrar`, mensagens `flash` e verificacao de dependencias.
- `core.repositories.FornecedorRepository`
  - Fornece consultas enriquecidas com `JOIN` em `usuarios` (`buscar_com_usuario`, `listar_com_usuario`).
- `core.repositories.UsuarioRepository`
  - Cria o usuario do tipo `fornecedor` e atualiza dados de acesso vinculados ao fornecedor.
- `core.database.Database`
  - Executa SQL brutos usados nas rotas (`Database.executar`, `inserir`, `atualizar`, `excluir`).

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Observacao |
| --- | --- | --- |
| `DB_CONFIG` | Parametros PostgreSQL para salvar fornecedores/usuarios/produtos | Obrigatorio em todos ambientes |
| `SECRET_KEY` | Assina cookies de sessao usados nas guardas de rota | Deve ser unica por ambiente |
| `DEBUG` | Controla modo dev (exibe mais flashes, mantem envio de email opcional) | Ativado por padrao |
| `MENSAGENS` | Mensagens padrao reutilizadas em outras telas | Nao e acessado diretamente aqui, mas mantem consistencia |

> Configurar `.env` com as credenciais corretas evita erros de conexao e garante que `Database.executar` realize commits e rollbacks conforme esperado.

## 7. Modelo de Dados Relevante (`schema.sql`)
- `usuarios`
  - Armazena credenciais basicas; constraint `UNIQUE(email, tipo)` previne duplicidade para o mesmo perfil.
- `fornecedores`
  - Contem informacoes empresariais (CNPJ, razao social, endereco) com `usuario_id` unico.
- `produtos`
  - Usa `fornecedor_id` como chave estrangeira; impede exclusao de fornecedores com produtos ativos (checado via `verificar_dependencias`).
- `logs_alteracoes`
  - Recebe registros de auditoria gerados pelo `CRUDService` em todas as mutacoes RF05.

## 8. Fluxo Detalhado RF05.1 - Listar Fornecedores
1. GET `/fornecedores/` ou `/fornecedores/listar` valida sessao via `AutenticacaoService.verificar_sessao`.
2. Falha de sessao => `flash` "Faca login" e redirect para `autenticacao.solicitar_codigo`.
3. Query SQL realiza `JOIN` entre `fornecedores` e `usuarios` para exibir dados de contato.
4. Lista e renderizada em `listar.html` com botoes contextuais baseados em `usuario_logado.tipo`.

## 9. Fluxo Detalhado RF05.2 - Cadastrar Fornecedor
1. GET `/fornecedores/cadastrar` exige permissao `administrador`; acesso negado gera redirect para `home`.
2. POST coleta dados de usuario e fornecedor do formulario (todos com `strip()` para saneamento basico).
3. Validacao verifica campos obrigatorios e chama `ValidacaoService.validar_cnpj`.
4. Caso valido, cria usuario via `UsuarioRepository.inserir`; falha interrompe fluxo com `flash` de erro.
5. `CRUDService.criar_com_log` insere fornecedor, registra auditoria (`logs_alteracoes`) e reaproveita `usuario_logado['id']` como autor.
6. Sucesso redireciona para listagem com mensagem positiva; falhas retornam ao formulario mantendo feedback.

## 10. Fluxo Detalhado RF05.3 - Editar Fornecedor
1. GET `/fornecedores/editar/<id>` aceita `administrador` ou `fornecedor` logado; demais perfis recebem `flash` de "Acesso negado".
2. `FornecedorRepository.buscar_com_usuario` carrega o registro. Ausencia gera redirect para listagem com alerta.
3. Template `editar.html` mostra CNPJ desabilitado para preservar chave normativa.
4. POST valida campos obrigatorios (nome, email, razao social) e atualiza `usuarios` e `fornecedores`.
5. `CRUDService.atualizar_com_log` compara `dados_antigos` (copia do registro original) para gravar diff em `logs_alteracoes`.
6. Em caso de sucesso, redireciona para listagem com `flash` informativo.

## 11. Fluxo de Apoio - Visualizar Detalhes
1. GET `/fornecedores/detalhes/<id>` reutiliza `verificar_sessao`; login requerido.
2. Carrega dados via `buscar_com_usuario`; inexistente => alerta e volta para listagem.
3. `Database.executar` conta produtos vinculados (`SELECT COUNT(*) FROM produtos`).
4. Template `detalhes.html` exibe cards com badges, links mailto/tel e zona de exclusao (apenas administradores).

## 12. Fluxo Detalhado RF05.4 - Excluir Fornecedor
1. POST `/fornecedores/excluir/<id>` exige permissao `administrador`.
2. `FornecedorRepository.buscar_por_id` garante existencia antes de prosseguir.
3. `CRUDService.verificar_dependencias` checa tabela `produtos` (campo `fornecedor_id`), retornando mensagens quando bloqueado.
4. Sem dependencias, `CRUDService.excluir_com_log` remove registro e grava auditoria `DELETE`.
5. Mensagens `flash` orientam o usuario sobre sucesso ou impeditivos.

## 13. Tratamento de Erros e Validacoes
- `flash` indica motivos de bloqueio (sem sessao, permissao insuficiente, campos obrigatorios, CNPJ invalido, dependencias).
- Validacoes de integridade rely em constraints PostgreSQL (`UNIQUE`, `NOT NULL`) alem das verificacoes em `module.py`.
- Confirmacoes de exclusao usam `onclick="return confirm(...)"` nos templates para evitar remocoes acidentais.
- `try/except` implicito do `Database` garante rollback automatico em falhas (vide implementacao em `core/database.py`).

## 14. Observabilidade e Auditoria
- `CRUDService` aciona `LogService.registrar` para todas as operacoes RF05, armazenando antes/depois em `logs_alteracoes`.
- Mensagens de console provenientes do `Database` (quando em DEBUG) auxiliam troubleshooting de SQL.
- `logs_alteracoes` pode ser consultado via modulo de logs para demonstrar trilha de auditoria durante apresentacoes.

## 15. Dependencias Externas (`requirements.txt`)
- Flask (Blueprints, `session`, `flash`, templating Jinja2).
- `psycopg2-binary` para acesso PostgreSQL via `Database`.
- `python-dotenv` para carregar configuracoes de ambiente.
- Bibliotecas padrao (`datetime`, `json`) utilizadas nos servicos compartilhados.

## 16. Testes Recomendados
- **Fluxo feliz**: Administrador cadastra fornecedor completo e verifica aparicao na listagem.
- **Permissao**: Usuario tipo `fornecedor` tenta acessar `/cadastrar`; deve ser bloqueado e redirecionado.
- **Validacao CNPJ**: Informar CNPJ vazio ou repetido para validar mensagens de erro/constraint.
- **Edicao fornecedor**: Ajustar dados de contato e confirmar registro no banco/logs.
- **Exclusao com produtos**: Relacionar produtos existentes e garantir bloqueio por dependencia.
- **Exclusao sem vinculos**: Remover fornecedor sem produtos e validar auditoria `DELETE`.

## 17. Checklist de Implantacao
1. Garantir que `schema.sql` (tabelas `usuarios`, `fornecedores`, `produtos`, `logs_alteracoes`) esteja aplicado.
2. Revisar `.env` com parametros de banco e `SECRET_KEY` especificos do ambiente.
3. Executar smoke test dos fluxos descritos nas secoes 8 a 12 usando usuario administrador.
4. Monitorar tabela `logs_alteracoes` durante apresentacao para evidenciar auditoria.
5. Preparar base de dados com pelo menos um fornecedor de exemplo para demos em producao.
