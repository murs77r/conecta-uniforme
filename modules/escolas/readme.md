# Módulo de Escolas# Módulo de Escolas



========================================================================================

RF03 - MANTER CADASTRO DE ESCOLARF03 - MANTER CADASTRO DE ESCOLA

========================================================================================

Este módulo é responsável por:Este módulo é responsável por:

- RF03.1: Criar escola- RF03.1: Criar escola

- RF03.2: Apagar escola- RF03.2: Apagar escola

- RF03.3: Editar escola- RF03.3: Editar escola

- RF03.4: Consultar escola- RF03.4: Consultar escola



Controla o processo de cadastro e gestão de escolas no sistema.Controla o processo de controle de escolas no sistema.



------



## 📋 Visão Geral## 📋 Visão Geral



O módulo de **Escolas** gerencia instituições de ensino cadastradas no sistema Conecta Uniforme. Este módulo é fundamental para conectar escolas com fornecedores homologados e responsáveis na plataforma.O módulo de **Escolas** gerencia instituições de ensino homologadas e seus gestores escolares no sistema Conecta Uniforme. Este módulo é fundamental para conectar escolas, fornecedores e responsáveis na plataforma, permitindo homologação de fornecedores e gestão de relacionamentos entre entidades.



### Propósito### Propósito

- Cadastrar e gerenciar escolas- Cadastrar e gerenciar escolas homologadas

- Controlar homologação de fornecedores por escola- Gerenciar gestores escolares vinculados às escolas

- Visualizar informações detalhadas das instituições- Controlar homologação de fornecedores por escola

- Manter integridade referencial entre escolas e usuários- Manter integridade referencial entre escolas e usuários



------



## 🏗️ Arquitetura## 🏗️ Arquitetura



### Padrões de Design Utilizados### Padrões de Design Utilizados

- **Repository Pattern**: `EscolaRepository`- **Repository Pattern**: `EscolaRepository` e `GestorEscolarRepository`

- **Service Layer**: `CRUDService`, `ValidacaoService`, `AutenticacaoService`- **Service Layer**: `CRUDService`, `ValidacaoService`, `AutenticacaoService`

- **Blueprint Pattern**: Separação de rotas por contexto- **Aggregate Root**: Escola como entidade principal com agregados (gestores, fornecedores homologados)

- **Blueprint Pattern**: Separação de rotas por contexto (escolas, gestores, homologação)

### Camadas da Aplicação

```### Camadas da Aplicação

┌─────────────────────────────────────┐```

│  Apresentação (module.py)           │┌─────────────────────────────────────┐

│  - Blueprints de rotas              ││  Apresentação (module.py)           │

└──────────────┬──────────────────────┘│  - Blueprints de rotas              │

               ↓└──────────────┬──────────────────────┘

┌─────────────────────────────────────┐               ↓

│  Serviços (core/services.py)        │┌─────────────────────────────────────┐

│  - CRUDService                      ││  Serviços (core/services.py)        │

│  - ValidacaoService                 ││  - CRUDService                      │

│  - AutenticacaoService              ││  - ValidacaoService                 │

└──────────────┬──────────────────────┘│  - AutenticacaoService              │

               ↓└──────────────┬──────────────────────┘

┌─────────────────────────────────────┐               ↓

│  Repositórios (core/repositories)   │┌─────────────────────────────────────┐

│  - EscolaRepository                 ││  Repositórios (core/repositories)   │

│  - UsuarioRepository                ││  - EscolaRepository                 │

└──────────────┬──────────────────────┘│  - GestorEscolarRepository          │

               ↓│  - FornecedorRepository             │

┌─────────────────────────────────────┐└──────────────┬──────────────────────┘

│  Database (core/database.py)        │               ↓

└─────────────────────────────────────┘┌─────────────────────────────────────┐

```│  Database (core/database.py)        │

└─────────────────────────────────────┘

### Diagrama de Relacionamentos```

```

┌──────────────┐### Diagrama de Relacionamentos

│   Usuario    │```

└──────┬───────┘┌──────────────┐

       │ 1│   Usuario    │

       │└──────┬───────┘

       │ 1       │ 1

┌──────┴───────┐       N:M      ┌─────────────────┐       │

│   Escola     │◄────────────────┤ Homologacao     │       │ N

│              │                 │ - escola_id     │┌──────┴────────────────┐

└──────────────┘                 │ - fornecedor_id ││  GestorEscolar        │

                                 └─────────────────┘│  - usuario_id (FK)    │

```│  - escola_id (FK)     │

└──────┬────────────────┘

---       │ N

       │

## 🔌 Endpoints (Rotas)       │ 1

┌──────┴───────┐       N:M      ┌─────────────────┐

### 1. `GET /escolas/listar`│   Escola     │◄────────────────┤ Homologacao     │

**Descrição**: Lista todas as escolas cadastradas com filtros e paginação│              │                 │ - escola_id     │

└──────────────┘                 │ - fornecedor_id │

**Autenticação**: Requerida (Todos os tipos de usuário autenticados)                                 └─────────────────┘

```

**Parâmetros Query String**:

```typescript---

{

    busca?: string,            // Busca parcial em nome/razão social/CNPJ## 🔌 Endpoints (Rotas)

    ativo?: 'true'|'false'|'', // Filtra por status

    estado?: string,           // Filtra por UF### ESCOLAS

    cidade?: string,           // Busca parcial em cidade

    page?: number,             // Paginação (default: 1)#### 1. `GET /escolas/listar`

    per_page?: number          // Itens por página (default: 20)**Descrição**: Lista todas as escolas homologadas com filtros

}

```**Autenticação**: Requerida (Administrador ou Escola)



**Resposta**:**Parâmetros Query String**:

```html```typescript

Status: 200 OK{

Template: templates/escolas/listar.html    filtro_nome?: string,      // Busca parcial em nome/razão social

Contexto: {    filtro_cnpj?: string,      // Busca exata em CNPJ

    'escolas': List[Escola],    filtro_cidade?: string,    // Busca parcial em cidade

    'pagination': Pagination,    filtro_ativa?: 'true'|'false'|'',  // Filtra por status

    'estatisticas': dict,    pagina?: number,           // Paginação (default: 1)

    'estados': List[dict]    por_pagina?: number        // Itens por página (default: 20)

}}

``````



---**Resposta**:

```html

### 2. `POST /escolas/cadastrar`Status: 200 OK

**Descrição**: Cadastra uma nova escola no sistemaTemplate: templates/escolas/listar.html

Contexto: {

**Autenticação**: Requerida (Administrador)    'escolas': List[Escola],

    'total': int,

**Corpo da Requisição** (multipart/form-data):    'pagina': int,

```json    'por_pagina': int,

{    'filtros': dict

    "nome": "string (obrigatório, max 200)",}

    "email": "string (obrigatório, único para tipo escola)",```

    "telefone": "string (opcional)",

    "cnpj": "string (obrigatório, 14 dígitos, único)",---

    "razao_social": "string (obrigatório, max 200)",

    "endereco": "string (obrigatório)",#### 2. `POST /escolas/cadastrar`

    "cidade": "string (obrigatório, max 100)",**Descrição**: Processa cadastro de nova escola

    "estado": "string (obrigatório, 2 letras)",

    "cep": "string (obrigatório, formato 99999-999)"**Corpo da Requisição** (multipart/form-data):

}```json

```{

    "nome_escola": "string (obrigatório, max 255)",

**Validações**:    "razao_social": "string (obrigatório, max 255)",

1. **CNPJ**: 14 dígitos, dígitos verificadores válidos, unicidade    "cnpj": "string (obrigatório, 14 dígitos, único)",

2. **Email**: RFC 5322, único para tipo 'escola'    "endereco": "string (obrigatório)",

3. **CEP**: Formato 99999-999    "cidade": "string (obrigatório)",

4. **Estado**: Sigla UF válida (2 letras)    "estado": "string (obrigatório, 2 letras)",

    "cep": "string (obrigatório, formato 99999-999)",

**Resposta de Sucesso**:    "telefone": "string (obrigatório)",

```json    "email_contato": "string (obrigatório)",

Status: 302 Redirect    "ativa": "boolean (opcional, default: true)"

Location: /escolas/listar}

Flash: "Escola cadastrada com sucesso"```

```

**Validações**:

---1. **CNPJ**: 14 dígitos, dígitos verificadores, unicidade

2. **Email**: RFC 5322, domínio válido

### 3. `GET /escolas/visualizar/<int:id>`3. **CEP**: Formato 99999-999

**Descrição**: Visualiza detalhes completos de uma escola4. **Estado**: Sigla UF válida



**Autenticação**: Requerida**Resposta de Sucesso**:

```json

**Resposta**:Status: 302 Redirect

```htmlLocation: /escolas/listar

Status: 200 OKFlash: "Escola cadastrada com sucesso"

Template: templates/escolas/visualizar.html```

Contexto: {

    'escola': Escola,---

    'gestores': List[GestorEscolar],

    'fornecedores': List[FornecedorHomologado]#### 3. `GET /escolas/visualizar/<int:id>`

}**Descrição**: Visualiza detalhes completos de uma escola

```

**Resposta**:

---```html

Status: 200 OK

### 4. `GET/POST /escolas/editar/<int:id>`Template: templates/escolas/visualizar.html

**Descrição**: Edita dados de uma escola existenteContexto: {

    'escola': Escola,

**Autenticação**: Requerida (Administrador ou Escola proprietária)    'gestores': List[GestorEscolar],

    'fornecedores_homologados': List[Fornecedor],

**Permissões**:    'total_pedidos': int

- Administrador: pode editar qualquer escola e alterar status}

- Escola: pode editar apenas seus próprios dados, não pode alterar status```



------



### 5. `POST /escolas/excluir/<int:id>`### GESTORES ESCOLARES

**Descrição**: Exclui uma escola do sistema

#### 4. `POST /escolas/<int:escola_id>/gestores/adicionar`

**Autenticação**: Requerida (Administrador)**Descrição**: Vincula usuário tipo 'Escola' como gestor



**Validações de Dependência**:**Corpo da Requisição**:

- Verifica se há fornecedores homologados```json

- Verifica se há produtos vinculados{

- Verifica se há pedidos vinculados    "usuario_id": "int (FK em usuarios)",

    "cargo": "string (ex: Diretor, Coordenador)"

Se houver dependências, sugere inativação ao invés de exclusão.}

```

---

**Validações**:

### 6. `GET/POST /escolas/homologar/<int:escola_id>`- Usuário deve ser tipo 'Escola'

**Descrição**: Homologa um fornecedor para vender à escola- Não pode já ser gestor da mesma escola

- Escola deve estar ativa

**Autenticação**: Requerida (Administrador)

---

**Comportamento**:

- Cria registro em `homologacao_fornecedores`### HOMOLOGAÇÃO DE FORNECEDORES

- Reativa se já existir mas estiver inativo

- Define `data_homologacao` automática#### 5. `POST /escolas/<int:escola_id>/homologar/<int:fornecedor_id>`

**Descrição**: Homologa fornecedor para vender à escola

---

**Comportamento**:

### 7. `POST /escolas/homologacao/<int:escola_id>/<int:fornecedor_id>/status`- Cria registro em `homologacao_fornecedores`

**Descrição**: Ativa/Inativa uma homologação existente (toggle)- Reativa se já existir mas inativo

- Define `data_homologacao` automática

**Autenticação**: Requerida (Administrador)

**Resposta**:

---```json

Status: 302 Redirect

## 📊 Modelos de DadosFlash: "Fornecedor homologado com sucesso"

```

### Tabela `escolas` (PostgreSQL)

```sql---

CREATE TABLE escolas (

    id SERIAL PRIMARY KEY,## 📊 Modelos de Dados

    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id),

    cnpj VARCHAR(18) UNIQUE,### Escola (Dataclass)

    razao_social VARCHAR(200),```python

    endereco TEXT,@dataclass

    cidade VARCHAR(100),class Escola:

    estado VARCHAR(2),    id: Optional[int] = None

    cep VARCHAR(10),    nome_escola: str = ''

    ativo BOOLEAN DEFAULT TRUE,    razao_social: str = ''

    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP    cnpj: str = ''

);    endereco: str = ''

```    cidade: str = ''

    estado: str = ''

---    cep: str = ''

    telefone: str = ''

## 🔐 Autenticação e Autorização    email_contato: str = ''

    data_homologacao: Optional[datetime] = None

### Matriz de Permissões    ativa: bool = True

```

| Rota | Administrador | Escola (Própria) | Fornecedor | Responsável |

|------|---------------|------------------|------------|-------------|### Tabela `escolas` (PostgreSQL)

| `/escolas/listar` | ✅ | ✅ | ✅ | ✅ |```sql

| `/escolas/cadastrar` | ✅ | ❌ | ❌ | ❌ |CREATE TABLE escolas (

| `/escolas/visualizar/:id` | ✅ | ✅ | ✅ | ✅ |    id SERIAL PRIMARY KEY,

| `/escolas/editar/:id` | ✅ | ✅ (própria) | ❌ | ❌ |    nome_escola VARCHAR(255) NOT NULL,

| `/escolas/excluir/:id` | ✅ | ❌ | ❌ | ❌ |    razao_social VARCHAR(255) NOT NULL,

| `/escolas/homologar/:id` | ✅ | ❌ | ❌ | ❌ |    cnpj VARCHAR(14) UNIQUE NOT NULL,

    endereco TEXT NOT NULL,

---    cidade VARCHAR(100) NOT NULL,

    estado VARCHAR(2) NOT NULL,

## 📝 Regras de Negócio    cep VARCHAR(9) NOT NULL,

    telefone VARCHAR(20) NOT NULL,

### 1. Cadastro de Escolas    email_contato VARCHAR(255) NOT NULL,

- Apenas Administradores podem cadastrar escolas    data_homologacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

- CNPJ deve ser válido e único    ativa BOOLEAN DEFAULT TRUE

- Email deve ser único para o tipo 'escola');

- Cada escola é vinculada a um usuário do tipo 'escola'```



### 2. Homologação de Fornecedores---

- Apenas Administradores podem homologar fornecedores

- Uma escola pode ter múltiplos fornecedores homologados## 🔐 Autenticação e Autorização

- Um fornecedor pode ser homologado por múltiplas escolas

- Homologação pode ser ativada/desativada### Matriz de Permissões



### 3. Exclusão| Rota | Administrador | Escola (Própria) | Fornecedor | Responsável |

- Soft delete: `ativo = false` (preferencial)|------|---------------|------------------|------------|-------------|

- Hard delete: apenas se não houver dependências| `/escolas/listar` | ✅ | ✅ | ❌ | ❌ |

- Dependências verificadas: fornecedores homologados, produtos, pedidos| `/escolas/cadastrar` | ✅ | ❌ | ❌ | ❌ |

| `/escolas/visualizar/:id` | ✅ | ✅ | ❌ | ❌ |

### 4. Edição| `/escolas/editar/:id` | ✅ | ❌ | ❌ | ❌ |

- Administrador: pode editar qualquer campo, incluindo status| `/escolas/:id/homologar` | ✅ | ✅ | ❌ | ❌ |

- Escola: pode editar apenas seus próprios dados, exceto status

---

---

## 📝 Regras de Negócio

## 🔗 Relacionamentos com Outros Módulos

### 1. Homologação de Escolas

- **Gestores**: Uma escola pode ter múltiplos gestores (ver módulo `gestores`)- Apenas Administradores cadastram escolas

- **Fornecedores**: Relacionamento N:M via `homologacao_fornecedores`- CNPJ deve ser válido e único

- **Produtos**: Produtos são vinculados a escolas específicas- `data_homologacao` automática no cadastro

- **Pedidos**: Pedidos são realizados no contexto de uma escola

### 2. Gestores Escolares

---- Um usuário pode gerir múltiplas escolas

- Uma escola pode ter múltiplos gestores

## 📦 Dependências- Mínimo de 1 gestor ativo por escola

- Apenas tipo 'Escola' pode ser gestor

- `core.repositories.EscolaRepository`

- `core.repositories.UsuarioRepository`### 3. Homologação de Fornecedores

- `core.repositories.GestorEscolarRepository`- Gestores decidem fornecedores autorizados

- `core.services.AutenticacaoService`- Homologação pode ser ativada/desativada

- `core.services.CRUDService`- Responsáveis só veem produtos homologados

- `core.services.ValidacaoService`

- `core.services.LogService`### 4. Exclusão Lógica

- `core.database.Database`- Soft delete: `ativa = false`

- `core.pagination`- Gestores vinculados são desativados

- Histórico preservado

