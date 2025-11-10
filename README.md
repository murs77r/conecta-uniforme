# Conecta Uniforme — Roteiro Técnico

## Visão Geral
- Plataforma Flask modular que conecta escolas, fornecedores e responsáveis na gestão completa de uniformes escolares.
- Aplicação segue arquitetura em blueprints (microfront-ends) para cada requisito funcional RF01–RF07.
- Persistência em PostgreSQL com camada `core` responsável por acesso a dados, serviços de negócio, validações e utilitários.
- Interface server-side renderizada com Jinja2, assets em `static/`, e autenticação por código de acesso temporário enviado por e-mail.

## Stack Principal
- **Backend:** Python 3.x, Flask, Blueprints, Jinja2.
- **Banco:** PostgreSQL via `psycopg2` com cursores `RealDict`.
- **Serviços de aplicação:** `core/database.py`, `core/repositories.py`, `core/services.py`, `core/pagination.py`.
- **Infra:** Dockerfile com Gunicorn + threads, variáveis de ambiente definidas em `.env` (carregadas por `python-dotenv`).
- **Outros:** Envio de e-mail SMTP, logging de auditoria e acesso, templating responsivo Bootstrap (customizações em `static/css/custom.css`).

## Arquitetura em Camadas
- **Camada Web (Blueprints em `modules/`):** cada pasta implementa um módulo isolado, mapeado diretamente para um requisito funcional.
- **Camada Core:** abstrai conexões, repositórios, serviços utilitários, validações, formatação e paginação.
- **Camada de Banco:** scripts SQL completos em `schema.sql`, incluindo índices e dados de demonstração.
- **Configuração:** `config.py` carrega variáveis de ambiente tipadas (DB, SMTP, autenticação, uploads, mensagens padrão).

## Fluxo de Autenticação (RF02)
1. Usuário acessa `/` → `app.py` executa health-check (`banco_esta_ativo`) antes de redirecionar.
2. Blueprint `modules/autenticacao/module.py`:
   - **RF02.1** `/auth/solicitar-codigo` (GET/POST): valida e-mail, exige seleção de perfil se houver múltiplos, gera OTP (`UtilsService.gerar_codigo_acesso`), persiste em `codigos_acesso`, envia e-mail via `EmailService`.
   - **RF02.2** `/auth/validar-codigo` (GET/POST): confere código ativo, expiração, marca como usado, cria sessão Flask, registra log de acesso (`LogService.registrar_acesso`).
   - `/auth/tipos-por-email`: endpoint auxiliar JSON usado pelo front.
   - `/auth/logout`: encerra sessão e registra logoff.
3. `verificar_sessao` e `verificar_permissao` centralizam a proteção de rotas, retornando dicionário do usuário autenticado.
4. Sessões Flask assinadas utilizam `SECRET_KEY`, TTL configurável via `SESSAO_DURACAO_DIAS`.

## Roteiro por Requisito Funcional

### RF01 — Manter Cadastro de Usuário (`modules/usuarios/module.py`)
- **Escopo:** cadastro, consulta, edição, exclusão e auditoria de usuários.
- **Rotas principais:**
  - `GET /usuarios/listar` — listagem segura (admin).
  - `GET|POST /usuarios/cadastrar` — criação com validações (`ValidacaoService`).
  - `GET /usuarios/visualizar/<id>` — detalhamento + info complementar.
  - `GET|POST /usuarios/editar/<id>` — atualização com restrições (ex.: último admin ativo).
  - `POST /usuarios/excluir/<id>` — exclusão com checagem de dependências (`CRUDService.verificar_dependencias`).
  - `GET /usuarios/logs` e variantes — histórico detalhado, parsing JSON para diffs (`_preparar_detalhes_logs`).
- **Tabelas relacionadas:** `usuarios`, `logs_alteracoes`, `logs_acesso`, além de FK indiretas (`escolas`, `fornecedores`, `responsaveis`).
- **Templates:** `templates/usuarios/*.html`, `templates/logs/*.html`.

### RF02 — Gerenciar Autenticação e Acesso (detalhado acima)
- **Templates:** `templates/auth/solicitar_codigo.html`, `templates/auth/validar_codigo.html`.
- **Serviços:** `EmailService`, `UtilsService`, `ValidacaoService`, `LogService`.
- **Tabelas:** `codigos_acesso`, `logs_acesso`, `usuarios`.

### RF03 — Manter Cadastro de Escola (`modules/escolas/module.py`)
- **Rotas:**
  - `GET /escolas/listar` — join com `usuarios` para dados de contato.
  - `GET|POST /escolas/cadastrar` — cria usuário-tipo `escola` e registro em `escolas`; suporta múltiplos gestores via `_processar_gestores`.
  - `GET /escolas/detalhes/<id>` — detalhamento + gestores associados.
  - `GET|POST /escolas/editar/<id>` — distinção de permissões (admin vs escola).
  - `POST /escolas/excluir/<id>` — exclusão condicionada a dependências (homologações, produtos, pedidos).
- **Tabelas:** `escolas`, `usuarios`, `gestores_escolares`, `homologacao_fornecedores`, `produtos`, `pedidos`.
- **Templates:** `templates/escolas/*.html`.

### RF04 — Manter Cadastro de Gestor Escolar (`modules/gestores/module.py`)
- **Rotas:**
  - `GET /gestores/escola/<escola_id>/listar` — lista gestores da escola.
  - `GET|POST /gestores/escola/<escola_id>/cadastrar` — valida nome, CPF, telefone.
  - `GET|POST /gestores/editar/<id>` — atualização controlada.
  - `POST /gestores/excluir/<id>` — remoção com registro em `logs_alteracoes` via `LogService`.
  - `GET /gestores/detalhes/<id>` — visão completa com escola associada.
- **Tabelas:** `gestores_escolares`, `escolas`, `usuarios`.
- **Templates:** `templates/gestores/*.html`.

### RF05 — Manter Cadastro de Fornecedor (`modules/fornecedores/module.py`)
- **Rotas:**
  - `GET /fornecedores/listar` — join com `usuarios`.
  - `GET|POST /fornecedores/cadastrar` — cria usuário `fornecedor` + registro na tabela.
  - `GET /fornecedores/detalhes/<id>` — inclui contagem de produtos cadastrados.
  - `GET|POST /fornecedores/editar/<id>` — edição com validação básica.
  - `POST /fornecedores/excluir/<id>` — bloqueio se existirem produtos vinculados.
- **Tabelas:** `fornecedores`, `usuarios`, `produtos`.
- **Templates:** `templates/fornecedores/*.html`.

### RF06 — Manter Cadastro de Produto (`modules/produtos/module.py`)
- **Rotas:**
  - `GET /produtos/listar` — listagem geral.
  - `GET|POST /produtos/cadastrar` — respeita contexto do usuário (admin escolhe fornecedor, fornecedor usa auto-ID).
  - `GET|POST /produtos/editar/<id>` — atualização de atributos e estoque.
  - `POST /produtos/excluir/<id>` — valida dependências (`itens_pedido`).
  - `GET /produtos/detalhes/<id>` — consulta individual.
- **Tabelas:** `produtos`, `fornecedores`, `itens_pedido`, `escolas`.
- **Templates:** `templates/produtos/*.html`.

### RF07 — Manter Cadastro de Pedido (`modules/pedidos/module.py`)
- **Rotas:**
  - `GET /pedidos/listar` — filtros por perfil (responsável vê apenas seus pedidos).
  - `GET|POST /pedidos/criar` — usa `Database.inserir`, registra log.
  - `GET|POST /pedidos/editar/<id>` — atualização de status/valor.
  - `POST /pedidos/apagar/<id>` — exclusão com auditoria.
  - `GET /pedidos/detalhes/<id>` — detalhamento com joins (responsável, escola, itens, produtos).
- **Tabelas:** `pedidos`, `itens_pedido`, `responsaveis`, `usuarios`, `escolas`.
- **Templates:** `templates/pedidos/*.html`.

## Camada Core e Reaproveitamento
- `core/database.py`: conexão efêmera com PostgreSQL, rollback automático, helpers CRUD (inserir/atualizar/excluir/buscar_por_id).
- `core/repositories.py`: padrão Repository para encapsular queries específicas por entidade (ex.: `ProdutoRepository.listar_vitrine`).
- `core/services.py`: serviços horizontais
  - `AutenticacaoService`, `ValidacaoService`, `CRUDService`, `EmailService`, `UtilsService`, `FormatadorService`, `LogService`.
  - `CRUDService` adiciona notificações flash e logs automáticos em operações.
- `core/pagination.py`: utilitário para paginação e construção de cláusulas WHERE (`FilterHelper`).
- `core/models.py`: dataclasses referenciais para entidades (não usados diretamente nas views, servem como contrato de dados).

## Banco de Dados
- Script completo em `schema.sql` cria estrutura, índices e popula dados de demonstração.
- Relações chave:
  - `usuarios` (tabela-mãe) → `escolas`, `fornecedores`, `responsaveis` (1:1 via `usuario_id`).
  - `escolas` ↔ `homologacao_fornecedores` ↔ `fornecedores` (n:n).
  - `pedidos` → `itens_pedido` (1:n) e `produtos`.
  - Logs (`logs_alteracoes`, `logs_acesso`) rastreiam todo o ciclo de auditoria.
- Índices extras otimizam filtros por e-mail, status, foreign keys e logs.

## Configuração e Execução
1. **Dependências:** `pip install -r requirements.txt` (Python 3.11 recomendado).
2. **Banco:** provisionar PostgreSQL e executar `schema.sql` (pgAdmin, psql ou migrations futuras).
3. **Variáveis `.env`:**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=conecta_uniforme
   DB_USER=postgres
   DB_PASSWORD=****
   SECRET_KEY=troque-esta-chave
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=usuario@example.com
   SMTP_PASSWORD=senha
   SMTP_FROM_EMAIL=no-reply@conecta.uniforme
   SMTP_FROM_NAME="Conecta Uniforme"
   CODIGO_ACESSO_TAMANHO=6
   CODIGO_ACESSO_DURACAO_HORAS=24
   SESSAO_DURACAO_DIAS=7
   ITENS_POR_PAGINA=20
   ```
4. **Execução local:** `python app.py` (modo debug controlado por `DEBUG` em `.env`).
5. **Execução Docker:**
   ```bash
   docker build -t conecta-uniforme .
   docker run --env-file .env -p 5000:5000 conecta-uniforme
   ```
6. **Produção:** utilizar Gunicorn (configurado no Dockerfile), preferencialmente atrás de um proxy reverso (Nginx) e com SMTP real.

## Templates e UX
- Layout base em `templates/base.html` com includes para mensagens flash, navegação e carregamento condicional.
- Páginas de erro dedicadas (`erro_404.html`, `erro_500.html`) e tela de espera `carregando.html` acionada quando o banco encara cold start (Docker).
- JavaScript genérico em `static/js/base.js` para interações, modais e polling do health-check (`/health/db`).

## Logging e Auditoria
- `LogService` insere registros em `logs_alteracoes` (CRUD) e `logs_acesso` (login/logoff).
- `usuarios/logs` converte payload JSON para diffs legíveis no template, com mascaramento leve de dados sensíveis.
- `app.py` registra health-checks e fornece endpoint `/health/db` (HTTP 200/503).

## Dados de Demonstração
- `schema.sql` inclui seeds para usuários (todos os perfis), escolas, fornecedores, responsáveis, gestores, homologações, produtos, pedidos, itens e logs.
- Seeds permitem demos imediatas dos fluxos sem necessidade de cadastro inicial manual.

## Roteiro de Demonstração Sugerido
1. **Login:** solicitar código para `murilosr@outlook.com.br` como fornecedor, validar login (RF02).
2. **Gestão de Produtos:**
   - Listar (`/produtos/listar`).
   - Cadastrar novo produto (RF06.2).
   - Editar preço/estoque (RF06.3).
3. **Gestão de Pedidos:**
   - Autenticar como responsável (`yurihenriquersilva343@gmail.com`).
   - Listar apenas pedidos próprios (RF07.4) e abrir detalhes.
4. **Administração:**
   - Logar como administrador (`jpfreitass2005@gmail.com`).
   - Navegar por /usuarios, /escolas, /fornecedores e revisar logs (`/usuarios/logs`).
5. **Auditoria:** mostrar entradas em `logs_acesso` e logs de alteração após ações anteriores.

## Qualidade e Próximos Passos
- **Testes automatizados:** não presentes; sugerido adicionar cobertura para serviços de autenticação, repositórios e rotas críticas.
- **Paginação:** helpers prontos em `core/pagination.py`, integrar nas listagens principais para ambientes com grande volume.
- **Uploads:** estrutura preparada (`UPLOAD_FOLDER`, `EXTENSOES_PERMITIDAS`), falta implementação nas telas.
- **Segurança:** considerar rate limiting para solicitação de códigos, CSRF para formulários, e hashing de senhas se migrar para autenticação tradicional.
- **Observabilidade:** integrar logger estruturado (ex.: Python `logging` + handlers) e monitoramento do health-check.

---
