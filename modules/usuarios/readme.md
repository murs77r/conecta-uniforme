# RF01 - Manter Cadastro de Usuario

Documento tecnico de apresentacao do requisito funcional RF01 (Manter Cadastro de Usuario). Este roteiro descreve como o modulo entrega o ciclo de vida de usuarios (administrador, escola, fornecedor, responsavel), abrangendo cadastro, consulta, edicao, exclusao e auditoria.

## 1. Contexto e Objetivo
- Centralizar o gerenciamento de todos os usuarios do ecossistema Conecta Uniforme.
- Garantir unicidade por combinacao `email + tipo` e rastrear cada alteracao relevante.
- Oferecer visibilidade operacional para administradores (logs, filtros) e autoatendimento para usuarios visualizarem seus proprios dados.
- Integrar dados complementares de escolas, fornecedores e responsaveis para compor visao 360 do usuario.

## 2. Visao Geral do Fluxo
1. Administrador acessa `/usuarios/listar` para visualizar usuarios ordenados por `data_cadastro`.
2. Cadastro de novo usuario via `/usuarios/cadastrar`, com validacao de email, telefone e tipo.
3. Visualizacao detalhada (`/usuarios/visualizar/<id>`) exige sessao ativa; usuarios comuns so enxergam o proprio registro.
4. Edicao (`/usuarios/editar/<id>`) revalida campos, respeita regras como protecao do ultimo administrador.
5. Exclusao (`/usuarios/excluir/<id>`) executa checagem de dependencias (pedidos, produtos, homologacoes) antes da remocao definitiva.
6. Logs granulares disponiveis em `/usuarios/logs/<id>` (alteracoes) e `/usuarios/logs-acesso/<id>` (LOGIN/LOGOFF); `/usuarios/logs` consolida visao geral.

## 3. Componentes Principais
- `modules/usuarios/module.py`
  - Declara blueprint `usuarios_bp` prefixado com `/usuarios`.
  - Implementa rotas RF01.1 a RF01.5 e helpers `_verificar_dependencias_usuario` e `_preparar_detalhes_logs`.
  - Consolida repositorios (`UsuarioRepository`, `EscolaRepository`, `FornecedorRepository`, `ResponsavelRepository`) e servicos (`AutenticacaoService`, `CRUDService`, `ValidacaoService`).
- `app.py`
  - Registra blueprint `usuarios_bp`.
  - Depende de `verificar_sessao`/`verificar_permissao` do modulo de autenticacao para proteger rotas globais.
- `core/database.py`
  - Prov fornece `Database.executar` para consultas ad-hoc usadas na listagem, verificacoes e logs.

## 4. Templates e UX
- `templates/usuarios/listar.html`
  - Tabela com usuarios ordenados por data, tags de status (ativo/inativo) e acoes para editar, visualizar, logs e excluir.
- `templates/usuarios/cadastrar.html`
  - Formulario responsivo com campos obrigatorios (nome, email, tipo) e opcional de telefone.
- `templates/usuarios/editar.html`
  - Repete estrutura do cadastro, habilita administradores a alternar tipo/ativo.
- `templates/usuarios/visualizar.html`
  - Exibe dados do usuario e bloco "informacoes complementares" quando ha registros vinculados (`escolas`, `fornecedores`, `responsaveis`).
- `templates/logs/logs.html`
  - Reaproveitado para historico de alteracoes (por usuario ou geral).
- `templates/logs/logs_acesso.html`
  - Lista eventos LOGIN/LOGOFF com filtros basicos (limite 100 registros). 
- `static/js/base.js`
  - Converte mensagens flash em modais padronizados utilizados pelas rotas do modulo.

## 5. Servicos e Camada Core
- `AutenticacaoService`
  - `verificar_sessao` controla acesso a rotas protegidas.
  - `verificar_permissao` restringe acoes administrativas a perfis `administrador`.
- `CRUDService`
  - `criar_com_log`, `atualizar_com_log`, `excluir_com_log` encapsulam persistencia, mensagens flash e auditoria em `logs_alteracoes`.
- `ValidacaoService`
  - `validar_email` e `validar_telefone` sustentam regras de negocio.
- `UsuarioRepository`
  - Acesso padrao a tabela `usuarios` mais `buscar_por_email_tipo` e `listar_com_filtros`.
- `EscolaRepository`, `FornecedorRepository`, `ResponsavelRepository`
  - Utilizados para carregar relacionamentos e validar dependencias na exclusao.
- `LogService`
  - Invocado indiretamente pelo `CRUDService` para registrar INSERT/UPDATE/DELETE.

## 6. Configuracao Necessaria (`config.py`)
| Variavel | Finalidade | Default |
| --- | --- | --- |
| `DB_CONFIG` | Credenciais PostgreSQL utilizadas por `Database` | localhost/5432 |
| `ITENS_POR_PAGINA` | Baseline para listagens (pode ser aplicada em futuras paginacoes) | 20 |
| `MENSAGENS` | Mensagens padrao referenciadas por flash | conforme arquivo |
| `DEBUG` | Controla feedback adicional no front (via templates) | true |
| `SECRET_KEY` | Necessario para sessao Flask usada por `AutenticacaoService` | change-me |

> Garantir `.env` consistente evita falhas de conexao em consultas diretas (`Database.executar`) empregadas pelas rotas `listar`, `logs` e `logs_acesso`.

## 7. Modelo de Dados Relevante (`schema.sql`)
- `usuarios`
  - Campos basicos (`nome`, `email`, `telefone`, `tipo`, `ativo`) e `UNIQUE (email, tipo)` prevenindo duplicidade por perfil.
- `logs_alteracoes`
  - Armazena auditoria dos CRUDs via `CRUDService`, incluindo `dados_antigos` e `dados_novos` em JSON.
- `logs_acesso`
  - Coleta LOGIN/LOGOFF para consulta em `/usuarios/logs-acesso/<id>`.
- `escolas`, `fornecedores`, `responsaveis`, `homologacao_fornecedores`, `produtos`, `pedidos`
  - Referenciados por `_verificar_dependencias_usuario` para impedir exclusao quebrando integridade relacional.

## 8. Fluxo Detalhado RF01.1 - Cadastrar Usuario
1. GET `/usuarios/cadastrar` exige `verificar_permissao(['administrador'])`; nega acesso com flash `danger` e redirect `home` se nao autorizado.
2. POST coleta dados do formulario, normaliza `nome`, `email`, `telefone`, `tipo` e define `ativo=True`.
3. Valida obrigatoriedade de `nome`, `email`, `tipo`; telefone opcional passa por `validar_telefone`.
4. `validar_email` garante formato basico; lista `tipos_validos` controla dominio permitido.
5. `UsuarioRepository.buscar_por_email_tipo` assegura unicidade por perfil antes de inserir.
6. Sucesso delega a `CRUDService.criar_com_log`, que inserta registro, grava auditoria (`logs_alteracoes`) e publica flash `success`; fallback renderiza template com mensagens.

## 9. Fluxo Detalhado RF01.2 - Consultar Usuarios
- **Listagem (`/usuarios/listar`)**
  1. Apenas administradores; fallback `flash('Acesso negado', 'danger')`.
  2. Consulta direta (`SELECT * FROM usuarios ORDER BY data_cadastro DESC`) via `Database.executar`.
  3. Renderiza `usuarios/listar.html` com lista completa (pode ser expandido a filtros/paginacao).
- **Visualizacao (`/usuarios/visualizar/<id>`)**
  1. Requer sessao valida (`verificar_sessao`); sem login redireciona para `/auth/solicitar-codigo`.
  2. Usuario logado so pode visualizar o proprio registro, exceto administradores.
  3. `UsuarioRepository.buscar_por_id` recupera dados base.
  4. Repositorios especificos (`EscolaRepository`, `FornecedorRepository`, `ResponsavelRepository`) carregam informacao complementar conforme `tipo`.
  5. Template exibe dados e contextos adicionais quando existentes.

## 10. Fluxo Detalhado RF01.3 - Editar Usuario
1. Acesso protegido por `verificar_sessao`; usuarios comuns so editam a si mesmos.
2. GET preenche `usuarios/editar.html` com dados existentes.
3. POST normaliza nome/email/telefone; administradores podem alterar `tipo` e `ativo` via toggle.
4. Validacoes replicam cadastro (obrigatorios, formato email/telefone).
5. Regra especifica impede inativar o ultimo administrador: consulta `SELECT COUNT(*) ... WHERE tipo='administrador' AND ativo=TRUE` antes de aceitar toggle.
6. `CRUDService.atualizar_com_log` persiste mudancas, gera flash `success` e auditoria; quando usuario edita a si mesmo, redireciona para `home` para revalidar sessao.

## 11. Fluxo Detalhado RF01.4 - Excluir Usuario
1. Apenas administradores (`verificar_permissao`).
2. Bloqueia autoexclusao (`usuario_logado['id'] == id`).
3. Carrega usuario alvo; ausencia gera flash `danger`.
4. `_verificar_dependencias_usuario` avalia:
   - Administrador: impede exclusao se seria o ultimo ativo.
   - Escola: verifica registros em `homologacao_fornecedores`, `produtos`, `pedidos`.
   - Fornecedor: valida estoque vinculado em `produtos`.
   - Responsavel: checa `pedidos` associados.
5. Havendo bloqueios, exibe mensagem `warning` sugerindo inativacao.
6. `CRUDService.excluir_com_log` executa `DELETE`, registra log e retorna a listagem.

## 12. Fluxo Detalhado RF01.5 - Visualizar Logs
- **`/usuarios/logs/<id>`**
  - Lista alteracoes em `logs_alteracoes` para o registro alvo, juntando com `usuarios` para nome do autor.
  - `_preparar_detalhes_logs` normaliza JSON antigo/novo, mascara IDs sensiveis e apresenta mudancas campo a campo.
- **`/usuarios/logs-acesso/<id>`**
  - Recupera ultimos 100 eventos em `logs_acesso` (LOGIN/LOGOFF) associados ao usuario.
- **`/usuarios/logs`**
  - Visao consolidada com filtros `acao`, `tabela`, `usuario_id`; recicla template `logs.html`.

## 13. Regras de Negocio Complementares
- `usuario_logado['tipo'] != 'administrador'` limita visualizacao/edicao a dados proprios.
- Mensagens padronizadas via `flash` (categorias `danger`, `warning`, `success`) alinham UX com outros modulos.
- `ValidacaoService` trata telefone como opcional mas sempre sanitiza com digitos.
- `_preparar_detalhes_logs` remove identificadores numericos (`id`, `*_id`) ao exibir diffs, reforcando LGPD.

## 14. Observabilidade e Seguranca
- Auditoria detalhada por acao (INSERT/UPDATE/DELETE) e usuario executante.
- Logs de acesso monitoram tentativa de login, inclusive falhas capturadas por outros modulos.
- Verificacoes de permissao centralizadas evitam exposicao indevida de dados sensiveis.
- `flash` + `base.js` tornam alertas visiveis e uniformes, importante para apresentacoes e treinamento.

## 15. Testes Recomendados
- **Cadastro feliz**: administrador cria usuario responsavel com telefone valido.
- **Duplicidade**: repetir cadastro com mesmo email+tipo para validar bloqueio.
- **Autogerenciamento**: usuario tipo responsavel faz login e tenta editar outro usuario (deve falhar).
- **Ultimo administrador**: tentar inativar ou excluir unico admin ativo.
- **Dependencias**: excluir usuario escola com pedidos vinculados (deve sugerir inativacao).
- **Logs**: editar usuario e conferir `logs_alteracoes` exibindo delta correto.
- **Logs de acesso**: realizar login/logout e validar exibicao na tela dedicada.

## 16. Checklist de Implantacao
1. Aplicar `schema.sql` garantindo indices (`idx_usuarios_email`, `idx_logs_usuario`).
2. Revisar `.env` com credenciais de banco e `SECRET_KEY` segura.
3. Criar perfis administrativos iniciais para habilitar fluxo completo.
4. Executar smoke test dos cenarios da secao 15.
5. Disponibilizar acesso as telas de logs para equipe de suporte durante demonstracao.

---

Para extensoes futuras (paginacao, filtros avancados, importacao em massa), reutilizar `UsuarioRepository.listar_com_filtros`, expandir `CRUDService` para validacoes customizadas e avaliar triggers no banco para reforcar auditoria automatica.
