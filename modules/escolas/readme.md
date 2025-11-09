# Módulo de Escolas

============================================
RF03 - MANTER CADASTRO DE ESCOLA
============================================
Este módulo é responsável por:
- RF03.1: Criar escola
- RF03.2: Apagar escola
- RF03.3: Editar escola
- RF03.4: Consultar escola

Controla o processo de controle de escolas no sistema.

---

## 📋 Visão Geral

O módulo de **Escolas** gerencia instituições de ensino homologadas e seus gestores escolares no sistema Conecta Uniforme. Este módulo é fundamental para conectar escolas, fornecedores e responsáveis na plataforma, permitindo homologação de fornecedores e gestão de relacionamentos entre entidades.

### Propósito
- Cadastrar e gerenciar escolas homologadas
- Gerenciar gestores escolares vinculados às escolas
- Controlar homologação de fornecedores por escola
- Manter integridade referencial entre escolas e usuários

---

## 🏗️ Arquitetura

### Padrões de Design Utilizados
- **Repository Pattern**: `EscolaRepository` e `GestorEscolarRepository`
- **Service Layer**: `CRUDService`, `ValidacaoService`, `AutenticacaoService`
- **Aggregate Root**: Escola como entidade principal com agregados (gestores, fornecedores homologados)
- **Blueprint Pattern**: Separação de rotas por contexto (escolas, gestores, homologação)

### Camadas da Aplicação
```
┌─────────────────────────────────────┐
│  Apresentação (module.py)           │
│  - Blueprints de rotas              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Serviços (core/services.py)        │
│  - CRUDService                      │
│  - ValidacaoService                 │
│  - AutenticacaoService              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Repositórios (core/repositories)   │
│  - EscolaRepository                 │
│  - GestorEscolarRepository          │
│  - FornecedorRepository             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Database (core/database.py)        │
└─────────────────────────────────────┘
```

### Diagrama de Relacionamentos
```
┌──────────────┐
│   Usuario    │
└──────┬───────┘
       │ 1
       │
       │ N
┌──────┴────────────────┐
│  GestorEscolar        │
│  - usuario_id (FK)    │
│  - escola_id (FK)     │
└──────┬────────────────┘
       │ N
       │
       │ 1
┌──────┴───────┐       N:M      ┌─────────────────┐
│   Escola     │◄────────────────┤ Homologacao     │
│              │                 │ - escola_id     │
└──────────────┘                 │ - fornecedor_id │
                                 └─────────────────┘
```

---

## 🔌 Endpoints (Rotas)

### ESCOLAS

#### 1. `GET /escolas/listar`
**Descrição**: Lista todas as escolas homologadas com filtros

**Autenticação**: Requerida (Administrador ou Escola)

**Parâmetros Query String**:
```typescript
{
    filtro_nome?: string,      // Busca parcial em nome/razão social
    filtro_cnpj?: string,      // Busca exata em CNPJ
    filtro_cidade?: string,    // Busca parcial em cidade
    filtro_ativa?: 'true'|'false'|'',  // Filtra por status
    pagina?: number,           // Paginação (default: 1)
    por_pagina?: number        // Itens por página (default: 20)
}
```

**Resposta**:
```html
Status: 200 OK
Template: templates/escolas/listar.html
Contexto: {
    'escolas': List[Escola],
    'total': int,
    'pagina': int,
    'por_pagina': int,
    'filtros': dict
}
```

---

#### 2. `POST /escolas/cadastrar`
**Descrição**: Processa cadastro de nova escola

**Corpo da Requisição** (multipart/form-data):
```json
{
    "nome_escola": "string (obrigatório, max 255)",
    "razao_social": "string (obrigatório, max 255)",
    "cnpj": "string (obrigatório, 14 dígitos, único)",
    "endereco": "string (obrigatório)",
    "cidade": "string (obrigatório)",
    "estado": "string (obrigatório, 2 letras)",
    "cep": "string (obrigatório, formato 99999-999)",
    "telefone": "string (obrigatório)",
    "email_contato": "string (obrigatório)",
    "ativa": "boolean (opcional, default: true)"
}
```

**Validações**:
1. **CNPJ**: 14 dígitos, dígitos verificadores, unicidade
2. **Email**: RFC 5322, domínio válido
3. **CEP**: Formato 99999-999
4. **Estado**: Sigla UF válida

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /escolas/listar
Flash: "Escola cadastrada com sucesso"
```

---

#### 3. `GET /escolas/visualizar/<int:id>`
**Descrição**: Visualiza detalhes completos de uma escola

**Resposta**:
```html
Status: 200 OK
Template: templates/escolas/visualizar.html
Contexto: {
    'escola': Escola,
    'gestores': List[GestorEscolar],
    'fornecedores_homologados': List[Fornecedor],
    'total_pedidos': int
}
```

---

### GESTORES ESCOLARES

#### 4. `POST /escolas/<int:escola_id>/gestores/adicionar`
**Descrição**: Vincula usuário tipo 'Escola' como gestor

**Corpo da Requisição**:
```json
{
    "usuario_id": "int (FK em usuarios)",
    "cargo": "string (ex: Diretor, Coordenador)"
}
```

**Validações**:
- Usuário deve ser tipo 'Escola'
- Não pode já ser gestor da mesma escola
- Escola deve estar ativa

---

### HOMOLOGAÇÃO DE FORNECEDORES

#### 5. `POST /escolas/<int:escola_id>/homologar/<int:fornecedor_id>`
**Descrição**: Homologa fornecedor para vender à escola

**Comportamento**:
- Cria registro em `homologacao_fornecedores`
- Reativa se já existir mas inativo
- Define `data_homologacao` automática

**Resposta**:
```json
Status: 302 Redirect
Flash: "Fornecedor homologado com sucesso"
```

---

## 📊 Modelos de Dados

### Escola (Dataclass)
```python
@dataclass
class Escola:
    id: Optional[int] = None
    nome_escola: str = ''
    razao_social: str = ''
    cnpj: str = ''
    endereco: str = ''
    cidade: str = ''
    estado: str = ''
    cep: str = ''
    telefone: str = ''
    email_contato: str = ''
    data_homologacao: Optional[datetime] = None
    ativa: bool = True
```

### Tabela `escolas` (PostgreSQL)
```sql
CREATE TABLE escolas (
    id SERIAL PRIMARY KEY,
    nome_escola VARCHAR(255) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    endereco TEXT NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    cep VARCHAR(9) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email_contato VARCHAR(255) NOT NULL,
    data_homologacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativa BOOLEAN DEFAULT TRUE
);
```

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Escola (Própria) | Fornecedor | Responsável |
|------|---------------|------------------|------------|-------------|
| `/escolas/listar` | ✅ | ✅ | ❌ | ❌ |
| `/escolas/cadastrar` | ✅ | ❌ | ❌ | ❌ |
| `/escolas/visualizar/:id` | ✅ | ✅ | ❌ | ❌ |
| `/escolas/editar/:id` | ✅ | ❌ | ❌ | ❌ |
| `/escolas/:id/homologar` | ✅ | ✅ | ❌ | ❌ |

---

## 📝 Regras de Negócio

### 1. Homologação de Escolas
- Apenas Administradores cadastram escolas
- CNPJ deve ser válido e único
- `data_homologacao` automática no cadastro

### 2. Gestores Escolares
- Um usuário pode gerir múltiplas escolas
- Uma escola pode ter múltiplos gestores
- Mínimo de 1 gestor ativo por escola
- Apenas tipo 'Escola' pode ser gestor

### 3. Homologação de Fornecedores
- Gestores decidem fornecedores autorizados
- Homologação pode ser ativada/desativada
- Responsáveis só veem produtos homologados

### 4. Exclusão Lógica
- Soft delete: `ativa = false`
- Gestores vinculados são desativados
- Histórico preservado

