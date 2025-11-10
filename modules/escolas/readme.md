# RF03 - Manter Cadastro de Escola

Documento tecnico de apresentacao do requisito funcional RF03 (Gerenciar Escolas). Este roteiro cobre os componentes, fluxos, validacoes e pontos de auditoria que suportam o ciclo completo de vida da entidade Escola dentro do Conecta Uniforme.

## 1. Contexto e Objetivo
- Permitir que administradores cadastrem novas escolas e gerenciem suas informacoes institucionais.
- Oferecer autogestao parcial para usuarios do tipo `escola`, permitindo atualizacao dos proprios dados.
- Garantir rastreabilidade de alteracoes e bloqueio seguro de exclusoes quando ha dependencias relacionadas (produtos, pedidos, homologacoes).

## 2. Visao Geral do Fluxo
1. Usuario autenticado acessa `/escolas/listar` para visualizar o catalogo de escolas.
2. Administradores podem abrir `/escolas/cadastrar` e registrar novos logins e dados institucionais.
3. Ao salvar, gestores opcionais sao vinculados e exibidos em `/escolas/detalhes/<id>`.
4. Administradores ou a propria escola acessam `/escolas/editar/<id>` para atualizar dados e gestores.
5. Exclusao somente e permitida quando nao existem registros dependentes; caso contrario, e exibido alerta orientando inativacao.

## 3. Componentes Principais
- `modules/escolas/module.py`
  - Blueprint `escolas_bp` com prefixo `/escolas`.
  - Funcoes alinhadas a RF03.1 (listar), RF03.2 (cadastrar), RF03.3 (detalhes), RF03.4 (editar), RF03.5 (excluir).
  - Helper `_processar_gestores` para mapear campos dinamicos do formulario e inserir gestores vinculados.
- `modules/escolas/__init__.py`
  - Expone `escolas_bp` para registro central.
- `app.py`
  - Registra o blueprint (RF03) e injeta `usuario_logado` em todos os templates, permitindo controles de exibicao de botoes e restricao de acoes no frontend.

## 4. Templates e UX
- `templates/escolas/listar.html`
  - Tabela responsiva com botoes de acao condicionados ao tipo de usuario.
  - Usa `usuario_logado` para exibir `Nova Escola` apenas para administradores.
- `templates/escolas/cadastrar.html`
  - Formulario dividido em sessoes (dados de acesso, dados institucionais, gestores).
  - Script inline adiciona/remova cards de gestores dinamicamente com campos obrigatorios de nome.
- `templates/escolas/editar.html`
  - Reaproveita estrutura de cadastro com dados pre-populados.
  - Checkbox `ativo` so aparece para administradores.
- `templates/escolas/detalhes.html`
  - Exibe resumo da escola e tabela de gestores.
  - Botoes de navegacao para editar e voltar.
- `static/js/base.js`
  - Converte mensagens `flash` em modais, reforcando feedback imediato de sucesso ou erro em todas as rotas.

## 5. Servicos e Camada Core
- `core.services.AutenticacaoService`
  - `verificar_sessao` protege listagem e detalhes para qualquer usuario autenticado.
  - `verificar_permissao` garante que somente administradores criem/excluam e que escolas editem apenas o proprio cadastro.
- `core.services.CRUDService`
  - `criar_com_log`, `atualizar_com_log`, `excluir_com_log` padronizam mensagens e registram auditoria via `LogService`.
  - `verificar_dependencias` consulta tabelas relacionadas antes de excluir.
- `core.services.ValidacaoService`
  - `validar_cnpj`, `validar_cep`, `validar_telefone` evitam dados inconsistentes.
- `core.repositories.EscolaRepository`
  - `buscar_com_usuario` e `listar_com_filtros` trazem uniao com dados do usuario vinculados (nome, email, ativo).
- `core.repositories.UsuarioRepository`
  - `buscar_por_email_tipo` impede duplicidade de login por email/tipo.
- `core.repositories.GestorEscolarRepository`
  - `listar_por_escola`, `inserir`, `excluir_por_escola` mantem contatos vinculados.
- `core.database.Database`
  - Executa queries SQL e aplica commits atomicos, garantindo rollback em caso de erro.

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Default |
| --- | --- | --- |
| `SECRET_KEY` | Assina cookies de sessao usados pelas verificacoes do modulo | `"chave-super-secreta"` |
| `DB_CONFIG` | Parametros de conexao PostgreSQL para `Database` | `localhost:5432` etc. |
| `DEBUG` | Habilita mensagens flash detalhadas e logs verbose | `True` |

> Em ambiente de apresentacao, confirme que os dados de `DB_CONFIG` e `SECRET_KEY` estao parametrizados via `.env` para permitir autenticacao e operacoes CRUD sem ajustes de codigo.

## 7. Modelo de Dados Relevante (`schema.sql`)
- `usuarios`
  - Campo `tipo` com valor `escola` diferencia perfis e suporta regra UNIQUE `(email, tipo)`.
- `escolas`
  - `usuario_id` (UNIQUE) referencia o login, `cnpj` com constraint de unicidade.
  - Atributos de endereco e atributo `ativo` para controle de disponibilidade.
- `gestores_escolares`
  - FK `escola_id` com `ON DELETE CASCADE`, permitindo limpeza automatica quando escola e excluida.
- `homologacao_fornecedores`, `produtos`, `pedidos`
  - Dependencias consultadas antes da exclusao via `verificar_dependencias`.
- `logs_alteracoes`
  - Recebe registros de INSERT/UPDATE/DELETE disparados por `CRUDService`.

## 8. Fluxo Detalhado RF03.1 - Listar Escolas
1. Rotas `/` e `/listar` (GET) chamam `listar`.
2. `AutenticacaoService.verificar_sessao` garante que apenas usuarios autenticados avancem.
3. Query manual em `Database.executar` utiliza JOIN com `usuarios` para trazer nome/email/telefone.
4. Template recebe lista de dicionarios; botoes de acao variam conforme `usuario_logado.tipo`.

## 9. Fluxo Detalhado RF03.2 - Cadastrar Escola
1. `verificar_permissao(['administrador'])` bloqueia usuarios nao administradores.
2. GET retorna formulario com scripts JS para gestao de gestores.
3. POST coleta campos de usuario (login) e escola, aplicando `.strip()` e normalizacao de email.
4. Valida obrigatorios (nome, email, cnpj, razao_social) e formato do CNPJ.
5. `UsuarioRepository.buscar_por_email_tipo` evita cadastrar email duplicado para perfil escola.
6. Usuario e criado via `usuario_repo.inserir`; ID e usado como FK em `escolas`.
7. `CRUDService.criar_com_log` grava escola e registra auditoria (log + flash de sucesso).
8. `_processar_gestores` percorre campos `gestores[...]` e chama `gestor_repo.inserir` para cada contato valido.
9. Redireciona para `/escolas/listar` e exibe mensagem de confirmacao.

## 10. Fluxo Detalhado RF03.3 - Visualizar Escola
1. `verificar_sessao` assegura acesso autenticado.
2. `escola_repo.buscar_com_usuario` retorna dicionario com dados da escola e usuario.
3. `gestor_repo.listar_por_escola` traz contatos associados ordenados por nome.
4. Template apresenta informacoes em `dl` e tabela responsiva, exibindo status ativo/inativo.

## 11. Fluxo Detalhado RF03.4 - Editar Escola
1. Permissao checa `administrador` ou `escola`.
2. Caso tipo `escola`, valida se `usuario_logado['id']` coincide com `escola['usuario_id']`, impedindo edicao cruzada.
3. GET popula formulario com dados correntes e lista gestores atuais (renderizada via script dinamico; dados sao reinseridos manualmente pelo usuario no prototipo atual).
4. POST executa validacao de telefone e CEP quando preenchidos usando `ValidacaoService`.
5. Apenas administradores podem alternar `ativo`; valor propaga para `usuarios` e `escolas`.
6. Campos obrigatorios sao reconfirmados antes da persistencia.
7. `usuario_repo.atualizar` salva dados do login; `crud_service.atualizar_com_log` grava alteracoes de escola com dif `dados_antigos`.
8. `gestor_repo.excluir_por_escola` limpa contatos, e `_processar_gestores` reinsere lista enviada.
9. Mensagens flash indicam sucesso e rota volta para listagem.

## 12. Fluxo Detalhado RF03.5 - Excluir Escola
1. Somente administradores passam em `verificar_permissao(['administrador'])`.
2. `escola_repo.buscar_por_id` verifica existencia.
3. `crud_service.verificar_dependencias` monta lista de bloqueios (homologacoes, produtos, pedidos) e gera mensagens descritivas.
4. Se houver dependencias, `flash` informativo orienta inativacao como alternativa.
5. Sem bloqueios, `crud_service.excluir_com_log` executa delete, registra auditoria e retorna sucesso.

## 13. Tratamento de Erros e Regras de Negocio
- Validacao de campos obrigatorios com feedback imediato via `flash`.
- CNPJ obrigatorio e validado contra repeticao de digitos para evitar cadastros artificiais.
- Emails sao normalizados para minusculas, evitando duplicidade por variacao de case.
- Gestores sem nome sao descartados silenciosamente no helper `_processar_gestores`.
- Gestores usam `ON DELETE CASCADE`, evitando registros orfaos quando escola e excluida.
- Permissao garante que perfis escola nao consigam manipular dados de terceiros.

## 14. Observabilidade e Auditoria
- `flash` + modais (via `base.js`) evidenciam sucesso/erros ao usuario final.
- `CRUDService` registra eventos de cadastro, atualizacao e exclusao em `logs_alteracoes` com descricao contextual.
- `print` e mensagens de erro do `Database` ajudam diagnostico durante demonstracoes em modo `DEBUG`.
- Dependencias bloqueadas exibem mensagens concatenadas (ex.: produtos vinculados) facilitando identificar pendencias antes de excluir.

## 15. Testes Recomendados
- **Cadastro feliz**: criar escola completa com dois gestores e validar aparicao na lista e detalhes.
- **CNPJ invalido**: informar CNPJ com menos de 14 digitos e verificar mensagem de erro.
- **Email duplicado**: reutilizar email de escola existente e garantir bloqueio.
- **Edicao por administrador**: alternar flag `ativo`, atualizar CEP invalido e confirmar validacao.
- **Edicao por perfil escola**: autenticar como escola, tentar editar outra escola e assegurar bloqueio.
- **Exclusao com dependencias**: vincular produtos ou pedidos e garantir que exclusao e barrada com mensagem adequada.
- **Exclusao sem dependencias**: remover escola recem-cadastrada (sem vinculos) e validar registro em `logs_alteracoes`.

## 16. Checklist de Implantacao
1. Aplicar `schema.sql`, assegurando tabelas `escolas` e `gestores_escolares` com constraints atualizadas.
2. Confirmar que usuarios administradores estao presentes para executar rotinas de cadastro.
3. Verificar conectividade com banco via `/health/db` antes de demonstrar o modulo.
4. Testar fluxos descritos na secao 15 em ambiente de staging, incluindo tentativas de exclusao com e sem dependencia.
5. Manter monitoramento de `logs_alteracoes` para auditoria das operacoes de cadastro de escola.

---

Para evolucoes futuras (ex.: upload de documentos de homologacao, anexos de logotipo, filtros avanzados na listagem), considere integrar `UploadService`, persistencia de arquivos em storage dedicado e expansao de filtros em `EscolaRepository.listar_com_filtros`.