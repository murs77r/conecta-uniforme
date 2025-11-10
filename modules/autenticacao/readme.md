# RF02 - Autenticacao e Acesso

Documento tecnico de apresentacao do requisito funcional RF02 (Gerenciar Autenticacao e Acesso). Este roteiro descreve os componentes, fluxos, dependencias e rotinas de suporte que implementam a autenticacao baseada em codigo de acesso temporario.

## 1. Contexto e Objetivo
- Prover autenticao sem senha utilizando codigos numericos enviados por email.
- Permitir que um mesmo email escolha o perfil (tipo de usuario) antes de gerar o codigo.
- Garantir expiracao, auditoria e rastreabilidade para os acessos.

## 2. Visao Geral do Fluxo
1. Usuario acessa `/auth/solicitar-codigo` e informa email.
2. Sistema identifica tipos ativos vinculados ao email e, se necessario, obriga selecao de perfil.
3. Codigo aleatorio eh persistido em `codigos_acesso`, registrado no log e enviado via email (ou deixado para consulta em log quando em DEBUG).
4. Usuario navega para `/auth/validar_codigo`, informa codigo e valida autenticidade/expiracao.
5. Sessao Flask eh materializada com dados do usuario; sucesso e falhas sao auditados em `logs_acesso`.
6. Rota `/auth/logout` encerra sessao e registra logoff.

## 3. Componentes Principais
- `modules/autenticacao/module.py`
  - Blueprint `autenticacao_bp` com prefixo `/auth`.
  - Rota auxiliar `/tipos-por-email` para suportar o modal de selecao de perfil.
  - Implementacoes RF02.1 (`solicitar_codigo`) e RF02.2 (`validar_codigo`).
  - Funcoes auxiliares `verificar_sessao` e `verificar_permissao` reutilizadas em `app.py` e demais modulos.
- `app.py`
  - Registra o blueprint e reutiliza `verificar_sessao` para proteger `index` e `home`.
  - Injeta constantes (`CODIGO_ACESSO_TAMANHO`, `CODIGO_ACESSO_DURACAO_HORAS`) e rotulos de tipos para templates.

## 4. Templates e UX
- `templates/auth/solicitar_codigo.html`
  - Formulario de solicitacao com modal Bootstrap para selecao de perfil quando ha multiplos tipos.
  - Exibe instrucoes com base nas constantes injetadas.
- `templates/auth/validar_codigo.html`
  - Formulario de validacao com reforco visual do email/perfil selecionado.
  - Modal opcional que avisa sobre falha no envio de email (controlado por query string `aviso_email`).
- `static/js/base.js`
  - Converte mensagens flash Flask em modais padronizados.
- Scripts inline dos templates
  - Fazem pre-checagem AJAX de tipos (`/auth/tipos-por-email`) para evitar round-trip desnecessario.
  - Sanitizam entradas, bloqueiam submissao sem tipo definido e automatizam foco/comportamentos do modal.

## 5. Servicos e Camada Core
- `core.services.ValidacaoService`
  - `validar_email` garante formato basico antes de consultar o banco.
- `core.services.UtilsService`
  - `gerar_codigo_acesso` produz codigo numerico com tamanho parametrico.
- `core.services.EmailService`
  - Envia o email com o codigo; suporta retry, TLS e autenticacao SMTP baseados em `SMTP_CONFIG`.
- `core.services.LogService`
  - `registrar_acesso` audita logins, selecoes de perfil e logoffs.
- `core.database.Database`
  - Encapsula conexao PostgreSQL e execucao de queries com RealDictCursor, commit explicito e rollback em caso de erro.

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Default |
| --- | --- | --- |
| `CODIGO_ACESSO_TAMANHO` | Numero de digitos gerados | 6 |
| `CODIGO_ACESSO_DURACAO_HORAS` | Validade do codigo | 24 |
| `SESSAO_DURACAO_DIAS` | TTL do cookie Flask (referenciado em outras partes do app) | 7 |
| `SMTP_*` | Parametros SMTP para envio de email | vide defaults em `config.py` |
| `DB_CONFIG` | Parametros de conexao PostgreSQL | `localhost:5432` etc. |

> Carregar `.env` com credenciais validas garante envio real de email; em ambiente de desenvolvimento (`DEBUG=true`) falhas de envio apenas disparam modal de aviso e mantem fluxo via log do servidor.

## 7. Modelo de Dados Relevante (`schema.sql`)
- `usuarios`
  - Email unico por tipo (`UNIQUE (email, tipo)`), controla perfis multiplos.
- `codigos_acesso`
  - Campos: `usuario_id`, `codigo`, `data_expiracao`, `usado`.
  - Registro eh criado a cada solicitacao; `usado` evita reutilizacao.
- `logs_acesso`
  - Captura `LOGIN` e `LOGOFF` com metadados (`ip_usuario`, `user_agent`, `sucesso`).

## 8. Fluxo Detalhado RF02.1 - Solicitar Codigo
1. GET `/auth/solicitar-codigo` renderiza formulario limpo.
2. POST valida email (nao vazio + formato basico) via `ValidacaoService` e busca perfis ativos no banco.
3. Nenhum usuario -> mensagem flash `danger`.
4. Multiplos perfis -> renderiza novamente com `abrir_modal_tipo=True` para obrigar selecao front-end.
5. Tipo selecionado dispara `LogService.registrar_acesso(..., sucesso=False, descricao='Selecao de perfil ...')` para auditoria.
6. `UtilsService.gerar_codigo_acesso` cria codigo; `datetime.now() + timedelta(CODIGO_ACESSO_DURACAO_HORAS)` define expiracao.
7. Insere registro em `codigos_acesso`; falha gera `flash` de erro.
8. Codigo e metadados sao impressos no console (helpers de QA) com protecao de `try/except`.
9. `EmailService.enviar_codigo_acesso` tenta envio; sucesso redireciona para `/auth/validar-codigo?email=...&tipo=...`; falha redireciona com `aviso_email=1` quando `DEBUG` ativo.

## 9. Fluxo Detalhado RF02.2 - Validar Codigo
1. GET `/auth/validar-codigo` recebe `email`, `tipo`, `aviso_email` de query string e renderiza pagina.
2. POST valida campos obrigatorios e consulta `codigos_acesso` juntando com `usuarios` para reforco de tipo/estado (`ativo`).
3. Caso inexistente/usado -> `flash` `danger`.
4. Expiracao invalida -> redireciona para solicitacao.
5. Usuario inativo -> bloqueia login e orienta contato com administrador.
6. Marca codigo como usado com `UPDATE` (commit explicito) e hidrata `session` com `usuario_*` + `logged_in=True`.
7. `LogService.registrar_acesso(..., sucesso=True, descricao='Login realizado via codigo ...')` grava auditoria.
8. Mensagem de boas-vindas e redirect `url_for('home')`.

## 10. Logout e Permissoes
- `/auth/logout`
  - Registra logoff antes de `session.clear()`.
  - Redireciona para solicitacao de codigo com `flash` informativo.
- `verificar_sessao`
  - Usa apenas `session` (stateless server-side) para checar se usuario esta autenticado.
- `verificar_permissao`
  - Compara `usuario['tipo']` com lista permitida; retorno `None` deve ser tratado nos modulos chamadores para negar acesso.

## 11. Tratamento de Erros e Seguranca
- Valida email e tipo antes de acessar dados sensiveis.
- Forca expiracao com `data_expiracao` e flag `usado` para autenticar uma unica vez.
- Falha ao registrar codigo ou enviar email gera feedback imediato ao usuario.
- `session.clear()` em logout previne dangling sessions.
- Logs de acesso suportam rastreabilidade para incidentes de seguranca.
- Endpoint `/auth/tipos-por-email` filtra email e garante resposta vazia quando parametro ausente.

## 12. Observabilidade e Auditoria
- Console logging (ambiente dev) facilita QA com codigo impresso.
- `LogService` grava eventos de selecao, login e logoff.
- `logs_acesso` pode ser consultado via `templates/logs/logs_acesso.html` (modulo de logs) para apresentacoes.

## 13. Dependencias Externas (`requirements.txt`)
- Flask e extensoes (Blueprint, session, flash).
- `psycopg2-binary` para PostgreSQL.
- `python-dotenv` para carregar configuracoes.
- Bibliotecas padrao (datetime, smtplib) utilizadas sem dependencias adicionais.

## 14. Testes Recomendados
- **Fluxo positivo**: email valido com um perfil, codigo enviado, login bem-sucedido.
- **Perfil multiplo**: email cadastrado com dois perfis; validar bloqueio ate selecionar tipo e log registrar selecao.
- **Codigo expirado**: alterar `data_expiracao` manualmente e verificar mensagem de expiracao.
- **Codigo reutilizado**: tentar validar mesmo codigo duas vezes; segunda tentativa deve falhar (`usado = TRUE`).
- **Usuario inativo**: setar `ativo = FALSE` e garantir bloqueio.
- **SMTP indisponivel**: derrubar servidor SMTP e observar modal de aviso com `DEBUG=true`.

## 15. Checklist de Implantacao
1. Aplicar `schema.sql` (ou migrations equivalentes) garantindo indices e constraints.
2. Configurar variaveis `.env` com credenciais de banco e SMTP.
3. Validar conectividade com `/health/db` antes da demonstracao.
4. Realizar smoke test dos fluxos descritos na secao 14.
5. Habilitar monitoramento de `logs_acesso` para auditoria em producao.

---

Para ajustes ou extensoes (ex. MFA adicional, limites de tentativas, internacionalizacao), considerar novos campos em `codigos_acesso`, controles de throttling na rota `/solicitar-codigo` e templates com suporte a i18n.
