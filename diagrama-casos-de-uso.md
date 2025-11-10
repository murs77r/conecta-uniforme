# Diagrama de Casos de Uso - Conecta Uniforme

## 1. Visão Geral do Sistema

O **Conecta Uniforme** é uma plataforma web que conecta escolas, fornecedores e responsáveis na gestão completa de uniformes escolares. O sistema centraliza processos de autenticação, cadastro de entidades, gestão de produtos e processamento de pedidos, garantindo rastreabilidade e auditoria de todas as operações.

---

## 2. Atores do Sistema

### 2.1. Ator Primário: Visitante
- **Descrição**: Usuário não autenticado que acessa o sistema
- **Responsabilidades**: Solicitar acesso ao sistema e visualizar catálogo público de produtos
- **Exemplo**: Qualquer pessoa que acessa a plataforma pela primeira vez

### 2.2. Ator: Usuário Autenticado (Ator Abstrato)
- **Descrição**: Ator base que representa qualquer usuário com sessão ativa no sistema
- **Especializado em**: Administrador, Escola, Fornecedor, Responsável
- **Responsabilidades**: Manter sessão ativa, realizar logout

### 2.3. Ator: Administrador
- **Descrição**: Usuário com permissões totais no sistema
- **Herda de**: Usuário Autenticado
- **Responsabilidades**: 
  - Gerenciar todos os usuários da plataforma
  - Administrar escolas, fornecedores e responsáveis
  - Supervisionar produtos e pedidos
  - Acessar logs completos de auditoria
- **Exemplo**: Gestor da plataforma Conecta Uniforme

### 2.4. Ator: Escola
- **Descrição**: Usuário representando uma instituição de ensino
- **Herda de**: Usuário Autenticado
- **Responsabilidades**:
  - Autogerenciar dados institucionais da escola
  - Gerenciar gestores escolares vinculados
  - Homologar fornecedores autorizados
- **Exemplo**: Diretor ou coordenador de uma escola cadastrada

### 2.5. Ator: Fornecedor
- **Descrição**: Usuário representando empresa fornecedora de uniformes
- **Herda de**: Usuário Autenticado
- **Responsabilidades**:
  - Autogerenciar dados empresariais
  - Cadastrar e gerenciar catálogo de produtos
  - Controlar estoque de uniformes
- **Exemplo**: Proprietário de confecção de uniformes

### 2.6. Ator: Responsável
- **Descrição**: Usuário representando responsável legal por aluno(s)
- **Herda de**: Usuário Autenticado
- **Responsabilidades**:
  - Visualizar catálogo de produtos disponíveis
  - Criar e acompanhar pedidos de uniformes
  - Gerenciar carrinho de compras
- **Exemplo**: Pai, mãe ou tutor de estudante

---

## 3. Casos de Uso

### RF01 - UC01: Gerenciar Usuários

**Ator Principal**: Administrador

**Descrição**: Permite ao administrador realizar o ciclo completo de gerenciamento de usuários do sistema, incluindo cadastro, consulta, edição, exclusão e visualização de logs de auditoria.

**Pré-condições**:
- Administrador deve estar autenticado no sistema
- Administrador deve ter permissão de tipo "administrador"

**Fluxo Principal**:
1. Administrador acessa o módulo de usuários
2. Sistema exibe listagem de todos os usuários ordenados por data de cadastro
3. Administrador pode:
   - **Cadastrar**: Criar novo usuário informando nome, email, tipo (administrador, escola, fornecedor, responsável) e telefone opcional
   - **Consultar**: Visualizar detalhes completos de um usuário, incluindo informações complementares (dados de escola, fornecedor ou responsável vinculados)
   - **Editar**: Atualizar dados do usuário, alternar status ativo/inativo, modificar tipo de perfil
   - **Excluir**: Remover usuário do sistema (com verificação de dependências)
   - **Visualizar Logs**: Acessar histórico completo de alterações e logs de acesso (login/logout)
4. Sistema registra todas as operações em logs de auditoria
5. Sistema exibe mensagem de confirmação da operação

**Fluxos Alternativos**:
- **FA01 - Email duplicado**: Se o email já existe para o mesmo tipo, sistema bloqueia cadastro
- **FA02 - Último administrador**: Sistema impede inativação ou exclusão do último administrador ativo
- **FA03 - Usuário com dependências**: Se houver registros vinculados (pedidos, produtos, homologações), sistema sugere inativação ao invés de exclusão

**Pós-condições**:
- Operação registrada em `logs_alteracoes`
- Usuário recebe feedback via mensagem flash

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema
- **<<extend>>** Visualizar Logs de Auditoria

---

### RF02 - UC02: Autenticar no Sistema

**Ator Principal**: Visitante

**Atores Secundários**: Todos os perfis de usuário (Administrador, Escola, Fornecedor, Responsável)

**Descrição**: Permite que qualquer usuário cadastrado autentique-se na plataforma utilizando código de acesso temporário enviado por email, sem necessidade de senha tradicional.

**Pré-condições**:
- Usuário deve possuir cadastro ativo no sistema
- Email deve estar configurado corretamente

**Fluxo Principal**:
1. Visitante acessa a página inicial do sistema
2. Sistema redireciona para tela de solicitação de código
3. Visitante informa seu email
4. Sistema busca perfis ativos vinculados ao email
5. **Se múltiplos perfis existirem**: Sistema exibe modal para seleção de tipo (escola, fornecedor, responsável, administrador)
6. Visitante seleciona o perfil desejado
7. Sistema gera código numérico de 6 dígitos com validade de 24 horas
8. Sistema persiste código na tabela `codigos_acesso`
9. Sistema envia código por email
10. Visitante acessa tela de validação e informa o código recebido
11. Sistema valida código (existência, expiração, se já foi usado)
12. Sistema marca código como usado
13. Sistema cria sessão Flask com dados do usuário
14. Sistema registra login em `logs_acesso`
15. Sistema redireciona para página inicial autenticada (home)

**Fluxos Alternativos**:
- **FA01 - Email não cadastrado**: Sistema exibe mensagem de erro
- **FA02 - Código expirado**: Sistema solicita nova geração de código
- **FA03 - Código já usado**: Sistema bloqueia tentativa e solicita novo código
- **FA04 - Usuário inativo**: Sistema bloqueia login e orienta contato com administrador
- **FA05 - Falha no envio de email**: Em modo DEBUG, sistema exibe modal de aviso mas permite continuar (código fica disponível no log do servidor)

**Pós-condições**:
- Sessão Flask ativa com dados do usuário (`usuario_id`, `usuario_nome`, `usuario_email`, `usuario_tipo`, `logged_in`)
- Login registrado em `logs_acesso`
- Código marcado como usado

**Relacionamentos**:
- **<<included>>** por todos os outros casos de uso (exceto visualização pública de produtos)

**Como Funciona**:
- **Visitante** solicita código → se transforma em **Usuário Autenticado** específico (Administrador, Escola, Fornecedor ou Responsável)
- Este caso de uso é **pré-requisito** para todos os demais casos de uso que exigem autenticação

---

### RF03 - UC03: Gerenciar Escolas

**Ator Principal**: Administrador

**Ator Secundário**: Escola (apenas para autogerenciamento de seus próprios dados)

**Descrição**: Permite o gerenciamento completo de escolas cadastradas na plataforma, incluindo dados institucionais, gestores escolares vinculados e validação de dependências.

**Pré-condições**:
- Para **cadastro/exclusão**: Usuário deve ser Administrador autenticado
- Para **edição**: Usuário deve ser Administrador OU Escola (editando seus próprios dados)

**Fluxo Principal**:
1. Usuário autenticado acessa módulo de escolas
2. Sistema exibe listagem de escolas com dados de contato
3. Usuário pode:
   - **Cadastrar** (somente Administrador):
     - Informar dados de acesso (nome, email, telefone, senha)
     - Informar dados institucionais (CNPJ, razão social, endereço completo)
     - Adicionar múltiplos gestores escolares (nome, email, telefone, CPF, tipo)
     - Sistema cria usuário tipo "escola" e registro na tabela escolas
   - **Visualizar Detalhes**:
     - Exibir dados completos da escola
     - Listar gestores vinculados
     - Mostrar status ativo/inativo
   - **Editar**:
     - Administrador pode editar qualquer escola
     - Escola pode editar apenas seus próprios dados
     - Atualizar dados institucionais e de contato
     - Gerenciar lista de gestores (adicionar/remover)
     - Administrador pode alternar status ativo/inativo
   - **Excluir** (somente Administrador):
     - Sistema verifica dependências (homologações, produtos, pedidos)
     - Se houver bloqueios, sugere inativação
     - Se sem dependências, executa exclusão
4. Sistema registra operação em logs de auditoria
5. Sistema exibe mensagem de confirmação

**Fluxos Alternativos**:
- **FA01 - CNPJ inválido**: Sistema valida formato e bloqueia cadastro com CNPJ inválido
- **FA02 - Email duplicado**: Sistema impede cadastro de email já existente para tipo "escola"
- **FA03 - Escola com dependências**: Sistema lista bloqueios (produtos vinculados, pedidos, homologações) e sugere inativação
- **FA04 - Escola tenta editar outra escola**: Sistema bloqueia com mensagem "Acesso negado"

**Pós-condições**:
- Registro criado/atualizado/excluído nas tabelas `usuarios` e `escolas`
- Gestores vinculados gravados em `gestores_escolares` (com CASCADE DELETE)
- Operação registrada em `logs_alteracoes`

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema
- **<<extend>>** Gerenciar Gestores Escolares

**Como Funciona**:
- **Administrador** conecta-se com este caso de uso para **TODAS** as operações (CRUD completo)
- **Escola** conecta-se com este caso de uso apenas para **consultar e editar seus próprios dados**
- **Extensão**: Ao gerenciar escola, pode-se gerenciar gestores vinculados (UC04)

---

### RF04 - UC04: Gerenciar Gestores Escolares

**Atores Principais**: Administrador, Escola

**Descrição**: Permite o gerenciamento de gestores vinculados a escolas específicas, incluindo dados de contato, CPF e tipo de gestor.

**Pré-condições**:
- Usuário deve estar autenticado
- Usuário deve ser Administrador OU Escola proprietária dos gestores
- Escola vinculada deve existir no sistema

**Fluxo Principal**:
1. Usuário autenticado acessa gestores de uma escola específica (via `/gestores/escola/<id>`)
2. Sistema valida permissão:
   - Administrador: acesso total a qualquer escola
   - Escola: acesso apenas aos próprios gestores
3. Sistema exibe listagem de gestores da escola ordenados por nome
4. Usuário pode:
   - **Cadastrar**:
     - Informar nome (obrigatório), email, telefone, CPF, tipo de gestor
     - Sistema valida formato de telefone e CPF
     - Sistema vincula gestor à escola
   - **Visualizar Detalhes**:
     - Exibir dados completos do gestor
     - Mostrar escola vinculada
   - **Editar**:
     - Atualizar dados do gestor
     - Sistema mantém vínculo com escola
   - **Excluir**:
     - Remover gestor após confirmação
     - Sistema executa exclusão (não afeta escola devido a CASCADE)
5. Sistema registra operação em `logs_alteracoes`
6. Sistema exibe mensagem de confirmação

**Fluxos Alternativos**:
- **FA01 - Nome não informado**: Sistema bloqueia cadastro com mensagem de erro
- **FA02 - Telefone inválido**: Se preenchido, sistema valida formato com apenas dígitos
- **FA03 - CPF inválido**: Se preenchido, sistema valida formato básico
- **FA04 - Escola não proprietária tenta acessar**: Sistema bloqueia com "Acesso negado"

**Pós-condições**:
- Registro criado/atualizado/excluído em `gestores_escolares`
- Operação registrada em `logs_alteracoes`
- Vínculo com escola mantido (campo `escola_id`)

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema
- **<<extended by>>** Gerenciar Escolas (pode ser acessado ao gerenciar escola)

**Como Funciona**:
- **Administrador** conecta-se com este caso de uso para gerenciar gestores de **qualquer escola**
- **Escola** conecta-se com este caso de uso para gerenciar **apenas seus próprios gestores**
- Acesso é controlado por verificação de `usuario_id` da escola vs escola proprietária do gestor

---

### RF05 - UC05: Gerenciar Fornecedores

**Ator Principal**: Administrador

**Ator Secundário**: Fornecedor (apenas para autogerenciamento)

**Descrição**: Permite o gerenciamento completo de fornecedores de uniformes, incluindo dados empresariais, contato e controle de produtos vinculados.

**Pré-condições**:
- Para **cadastro/exclusão**: Usuário deve ser Administrador autenticado
- Para **edição**: Usuário deve ser Administrador OU Fornecedor (editando seus próprios dados)

**Fluxo Principal**:
1. Usuário autenticado acessa módulo de fornecedores
2. Sistema exibe listagem com join de `fornecedores` e `usuarios`
3. Usuário pode:
   - **Cadastrar** (somente Administrador):
     - Informar dados de acesso (nome, email, telefone)
     - Informar dados empresariais (CNPJ, razão social, endereço completo)
     - Sistema valida CNPJ (formato e unicidade)
     - Sistema cria usuário tipo "fornecedor" e registro em fornecedores
   - **Visualizar Detalhes**:
     - Exibir dados completos do fornecedor
     - Mostrar contagem de produtos cadastrados
     - Apresentar badges de status ativo/inativo
   - **Editar**:
     - Administrador pode editar qualquer fornecedor
     - Fornecedor pode editar apenas seus próprios dados
     - CNPJ permanece bloqueado (disabled) para preservar chave normativa
     - Atualizar dados empresariais e contato
     - Administrador pode alternar status ativo/inativo
   - **Excluir** (somente Administrador):
     - Sistema verifica se existem produtos vinculados
     - Se houver produtos, bloqueia exclusão
     - Se sem dependências, executa remoção
4. Sistema registra operação em logs
5. Sistema exibe mensagem de confirmação

**Fluxos Alternativos**:
- **FA01 - CNPJ inválido ou duplicado**: Sistema bloqueia cadastro
- **FA02 - Email duplicado**: Sistema impede email já existente para tipo "fornecedor"
- **FA03 - Fornecedor com produtos**: Sistema lista produtos vinculados e bloqueia exclusão
- **FA04 - Fornecedor tenta editar outro**: Sistema nega acesso

**Pós-condições**:
- Registro criado/atualizado/excluído em `usuarios` e `fornecedores`
- Operação registrada em `logs_alteracoes`
- Produtos mantêm vínculo se fornecedor apenas inativado

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema
- **Associação**: Fornecedores cadastram produtos (UC06)

**Como Funciona**:
- **Administrador** conecta-se com este caso de uso para **TODAS** as operações (CRUD completo)
- **Fornecedor** conecta-se com este caso de uso apenas para **consultar e editar seus próprios dados**
- Fornecedores **não podem excluir a si mesmos** (apenas Administrador)

---

### RF06 - UC06: Gerenciar Produtos

**Atores Principais**: Administrador, Fornecedor

**Ator Secundário**: Visitante (apenas consulta pública do catálogo)

**Descrição**: Permite o gerenciamento completo do catálogo de produtos (uniformes), incluindo cadastro, edição de estoque, preços e exclusão com validação de dependências.

**Pré-condições**:
- Para **cadastro/edição/exclusão**: Usuário deve ser Administrador OU Fornecedor autenticado
- Fornecedor só manipula produtos próprios (vinculados ao seu `fornecedor_id`)

**Fluxo Principal**:
1. Usuário acessa módulo de produtos
2. Sistema exibe catálogo ordenado por ID decrescente
3. **Visitante**: Pode apenas visualizar listagem e detalhes
4. **Administrador/Fornecedor** pode:
   - **Cadastrar**:
     - Fornecedor: Sistema auto-identifica `fornecedor_id` vinculado ao usuário
     - Administrador: Pode escolher qualquer fornecedor ativo
     - Informar nome, descrição, categoria, preço, estoque inicial
     - Opcionalmente vincular a escola específica
     - Sistema normaliza preço (vírgula para ponto)
     - Sistema valida campos obrigatórios
   - **Visualizar Detalhes**:
     - Exibir dados completos do produto
     - Mostrar badges de categoria e status ativo/inativo
     - Exibir informações do fornecedor
     - Exibir estoque disponível
   - **Editar**:
     - Atualizar nome, descrição, preço, estoque
     - Administrador pode alterar status ativo/inativo
     - Sistema revalida campos obrigatórios
   - **Excluir**:
     - Sistema verifica se produto está em `itens_pedido`
     - Se houver pedidos, bloqueia exclusão
     - Se sem dependências, executa remoção
5. Sistema registra operação em `logs_alteracoes`
6. Sistema exibe mensagem de confirmação

**Fluxos Alternativos**:
- **FA01 - Campos obrigatórios vazios**: Sistema bloqueia com mensagem
- **FA02 - Preço inválido**: Sistema valida formato numérico
- **FA03 - Produto em pedidos**: Sistema lista dependências e bloqueia exclusão
- **FA04 - Fornecedor tenta manipular produto de outro**: Sistema (idealmente) deve bloquear

**Pós-condições**:
- Registro criado/atualizado/excluído em `produtos`
- Operação registrada em `logs_alteracoes`
- Vínculo com fornecedor mantido

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema (para cadastro/edição)
- **Público** para Visitantes (consulta)
- **Associação**: Produtos são cadastrados por Fornecedores
- **Usado por**: Pedidos (UC07)

**Como Funciona**:
- **Visitante** conecta-se com este caso de uso apenas para **visualizar catálogo** (sem autenticação)
- **Administrador** conecta-se para **CRUD completo** de qualquer produto
- **Fornecedor** conecta-se para **CRUD apenas de seus próprios produtos**
- Auto-identificação de `fornecedor_id` impede que fornecedor manipule produtos alheios

---

### RF07 - UC07: Gerenciar Pedidos

**Ator Principal**: Responsável

**Ator Secundário**: Administrador (supervisão)

**Descrição**: Permite que responsáveis criem e acompanhem pedidos de uniformes, com controle de status, valor total e restrição de visibilidade por perfil.

**Pré-condições**:
- Usuário deve estar autenticado
- Responsável deve ter cadastro vinculado a um usuário
- Produtos devem estar disponíveis no catálogo

**Fluxo Principal**:
1. Usuário autenticado acessa módulo de pedidos
2. Sistema valida perfil:
   - **Responsável**: Exibe apenas pedidos próprios (filtro por `responsavel_id`)
   - **Administrador**: Exibe todos os pedidos do sistema
3. Sistema exibe listagem com status, valor, data e ações
4. Usuário pode:
   - **Criar Pedido**:
     - Informar responsável, escola, status inicial (padrão: "pendente")
     - Sistema calcula valor total baseado em itens
     - Sistema persiste em `pedidos` e `itens_pedido`
     - Sistema registra em `logs_alteracoes`
   - **Visualizar Detalhes**:
     - Responsável: Apenas pedidos próprios
     - Administrador: Qualquer pedido
     - Exibir cabeçalho com dados do pedido
     - Mostrar dados do responsável e escola
     - Listar itens com produtos, quantidades e subtotais
     - Exibir badges de status (pendente, pago, enviado, entregue, cancelado)
   - **Editar Status/Valor**:
     - Atualizar status do pedido
     - Ajustar valor total manualmente
     - Sistema atualiza `data_atualizacao`
   - **Cancelar/Apagar**:
     - Remover pedido do sistema
     - Sistema registra exclusão em logs
5. Sistema registra operação em auditoria
6. Sistema exibe mensagem de confirmação

**Fluxos Alternativos**:
- **FA01 - Responsável tenta acessar pedido alheio**: Sistema bloqueia com "Acesso negado"
- **FA02 - Pedido inexistente**: Sistema redireciona para listagem com mensagem de erro
- **FA03 - Dados obrigatórios ausentes**: Sistema bloqueia criação/edição
- **FA04 - Exclusão sem confirmação**: JavaScript solicita confirmação antes de submeter

**Pós-condições**:
- Registro criado/atualizado/excluído em `pedidos`
- Itens vinculados em `itens_pedido`
- Operação registrada em `logs_alteracoes`

**Relacionamentos**:
- **<<include>>** Autenticar no Sistema
- **Usa**: Produtos (UC06) - pedidos referenciam produtos via itens_pedido
- **Associação**: Responsáveis criam pedidos para escolas

**Como Funciona**:
- **Responsável** conecta-se com este caso de uso para **criar, visualizar e editar apenas seus próprios pedidos**
- **Administrador** conecta-se com este caso de uso para **supervisionar todos os pedidos** do sistema
- Filtro automático por `responsavel_id` garante isolamento de dados entre responsáveis
- Administrador tem visão 360° para suporte e auditoria

---

## 4. Diagrama de Relacionamentos

### 4.1. Relacionamentos de Inclusão (<<include>>)

Todos os casos de uso (exceto visualização pública de produtos) **incluem** obrigatoriamente:
- **UC02: Autenticar no Sistema**

Isso significa que antes de executar qualquer operação protegida, o sistema verifica se o usuário está autenticado através de sessão Flask válida.

### 4.2. Relacionamentos de Extensão (<<extend>>)

- **UC03: Gerenciar Escolas** estende-se para **UC04: Gerenciar Gestores Escolares**
  - Ao gerenciar uma escola, pode-se gerenciar seus gestores vinculados

### 4.3. Relacionamentos de Associação

- **Administrador** ↔ **UC01, UC03, UC05** (controle total)
- **Escola** ↔ **UC03, UC04** (autogerenciamento)
- **Fornecedor** ↔ **UC05, UC06** (autogerenciamento de dados e produtos)
- **Responsável** ↔ **UC07** (gerenciamento de pedidos próprios)
- **Visitante** ↔ **UC02** (autenticação) e **UC06** (consulta pública)

### 4.4. Relacionamentos de Especialização

```
Visitante
    |
    └── (autentica via UC02) → Usuário Autenticado
                                       |
                                       ├── Administrador
                                       ├── Escola
                                       ├── Fornecedor
                                       └── Responsável
```

---

## 5. Matriz de Permissões

| Caso de Uso | Administrador | Escola | Fornecedor | Responsável | Visitante |
|-------------|---------------|--------|------------|-------------|-----------|
| UC01: Gerenciar Usuários | ✅ CRUD completo | ❌ | ❌ | ❌ | ❌ |
| UC02: Autenticar no Sistema | ✅ | ✅ | ✅ | ✅ | ✅ |
| UC03: Gerenciar Escolas | ✅ CRUD completo | ✅ Autogerenciar | ❌ | ❌ | ❌ |
| UC04: Gerenciar Gestores | ✅ Todas escolas | ✅ Próprios gestores | ❌ | ❌ | ❌ |
| UC05: Gerenciar Fornecedores | ✅ CRUD completo | ❌ | ✅ Autogerenciar | ❌ | ❌ |
| UC06: Gerenciar Produtos | ✅ CRUD completo | ❌ | ✅ Próprios produtos | ❌ | ✅ Consulta |
| UC07: Gerenciar Pedidos | ✅ Supervisionar | ❌ | ❌ | ✅ Próprios pedidos | ❌ |

---

## 6. Fluxos de Auditoria (Transversal a Todos os Casos de Uso)

### 6.1. Logs de Alterações
Todos os casos de uso que realizam operações de **CREATE, UPDATE, DELETE** registram automaticamente em `logs_alteracoes`:
- Tabela afetada
- Ação executada (INSERT/UPDATE/DELETE)
- Usuário executor (id e nome)
- Timestamp da operação
- Dados antigos (JSON) - para UPDATE e DELETE
- Dados novos (JSON) - para INSERT e UPDATE
- Descrição textual da operação

### 6.2. Logs de Acesso
O caso de uso **UC02: Autenticar no Sistema** registra em `logs_acesso`:
- Login bem-sucedido
- Tentativas de login malsucedidas
- Seleção de perfil (quando múltiplos perfis)
- Logout
- IP do usuário e User-Agent
- Timestamp

---

## 7. Regras de Negócio Transversais

### 7.1. Unicidade de Email por Tipo
- Um mesmo email pode existir para diferentes tipos de usuário
- Constraint: `UNIQUE(email, tipo)` na tabela `usuarios`
- Exemplo: `admin@escola.com` pode ser tipo "administrador" E tipo "escola"

### 7.2. Proteção do Último Administrador
- Sistema **nunca** permite:
  - Inativar o último administrador ativo
  - Excluir o último administrador ativo
  - Alterar tipo do último administrador ativo

### 7.3. Exclusão com Dependências
- Sistema **bloqueia** exclusão quando houver registros vinculados:
  - Usuário com escolas/fornecedores/responsáveis/pedidos
  - Escola com homologações/produtos/pedidos
  - Fornecedor com produtos
  - Produto com itens de pedido
- Sistema **sugere inativação** como alternativa segura

### 7.4. Autoexclusão
- Nenhum usuário pode excluir o próprio registro
- Mesmo administradores precisam de outro administrador para serem excluídos

### 7.5. Validações de Formato
Aplicadas por `ValidacaoService`:
- **Email**: formato básico `user@domain.com`
- **CNPJ**: 14 dígitos, sem repetição completa
- **CPF**: formato básico (opcional)
- **Telefone**: apenas dígitos (opcional)
- **CEP**: formato brasileiro (opcional)

---

## 8. Considerações de Segurança

### 8.1. Autenticação sem Senha
- Sistema utiliza **códigos de acesso temporários** ao invés de senhas
- Códigos gerados aleatoriamente (6 dígitos)
- Validade configurável (padrão: 24 horas)
- Uso único (flag `usado` impede reutilização)
- Envio por email SMTP

### 8.2. Controle de Sessão
- Sessão Flask assinada com `SECRET_KEY`
- TTL configurável (padrão: 7 dias)
- Dados armazenados: `usuario_id`, `usuario_nome`, `usuario_email`, `usuario_tipo`, `logged_in`
- `verificar_sessao` protege rotas sensíveis
- `verificar_permissao` valida tipo de usuário

### 8.3. Isolamento de Dados
- **Escolas** só acessam próprios dados e gestores
- **Fornecedores** só manipulam próprios produtos
- **Responsáveis** só visualizam próprios pedidos
- **Administradores** têm visão global para supervisão

---

## 9. Cenários de Uso Típicos

### Cenário 1: Administrador Cadastra Nova Escola
1. **Administrador** autentica-se (UC02)
2. Acessa UC03: Gerenciar Escolas
3. Clica em "Nova Escola"
4. Preenche dados de acesso (email, nome, telefone)
5. Preenche dados institucionais (CNPJ, razão social, endereço)
6. Adiciona 2 gestores escolares (nome, email, telefone)
7. Confirma cadastro
8. Sistema cria usuário tipo "escola" + registro em `escolas` + 2 registros em `gestores_escolares`
9. Sistema registra em `logs_alteracoes`
10. Administrador visualiza escola na listagem

### Cenário 2: Fornecedor Cadastra Produto
1. **Fornecedor** autentica-se (UC02) com email cadastrado
2. Sistema identifica `fornecedor_id` vinculado ao usuário
3. Fornecedor acessa UC06: Gerenciar Produtos
4. Clica em "Novo Produto"
5. Sistema preenche automaticamente campo `fornecedor_id` (oculto)
6. Fornecedor informa nome, descrição, categoria, preço, estoque
7. Confirma cadastro
8. Sistema valida campos e grava produto vinculado ao fornecedor
9. Produto aparece no catálogo público
10. Sistema registra em `logs_alteracoes`

### Cenário 3: Responsável Cria Pedido
1. **Responsável** autentica-se (UC02)
2. Navega pelo catálogo (UC06 - consulta pública)
3. Seleciona produtos desejados (carrinho - fluxo futuro)
4. Acessa UC07: Gerenciar Pedidos
5. Cria novo pedido informando escola e produtos
6. Sistema calcula valor total
7. Sistema grava pedido com status "pendente"
8. Responsável visualiza pedido na listagem (apenas seus pedidos)
9. Administrador pode supervisionar todos os pedidos

### Cenário 4: Escola Gerencia Próprios Gestores
1. **Escola** autentica-se (UC02)
2. Acessa UC03: Gerenciar Escolas → visualiza próprios dados
3. Clica em "Gestores" → redireciona para UC04
4. Sistema valida que escola é proprietária
5. Escola adiciona novo gestor (diretor pedagógico)
6. Sistema vincula gestor à escola
7. Escola edita telefone de gestor existente
8. Sistema registra alterações em `logs_alteracoes`

---

## 10. Observações Finais
### Pontos de Atenção
- Sistema **não usa senhas tradicionais** (apenas códigos temporários)
- Todos os CRUDs passam por `CRUDService` com logging automático
- Permissões validadas em **duas camadas**: backend (`verificar_permissao`) e frontend (botões condicionais)
- Exclusões sempre verificam dependências antes de executar
- Inativação é preferível à exclusão para manter integridade referencial
