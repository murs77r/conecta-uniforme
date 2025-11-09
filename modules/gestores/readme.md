# Módulo de Gestores Escolares

============================================
RF04 - MANTER CADASTRO DE GESTOR ESCOLA
============================================
Este módulo é responsável por:
- RF04.1: Criar gestor escolar
- RF04.2: Apagar gestor escolar
- RF04.3: Editar gestor escolar
- RF04.4: Consultar gestor escolar

Controla o processo de gestão de gestores escolares no sistema.

---

## 📋 Visão Geral

O módulo de **Gestores Escolares** gerencia os contatos e responsáveis administrativos das escolas cadastradas no sistema Conecta Uniforme. Cada escola pode ter múltiplos gestores (diretores, coordenadores, financeiros, etc.).

### Propósito
- Cadastrar e gerenciar gestores escolares
- Vincular múltiplos gestores a uma escola
- Manter informações de contato dos responsáveis
- Facilitar comunicação com as escolas

---

## 🏗️ Arquitetura

### Padrões de Design Utilizados
- **Repository Pattern**: `GestorEscolarRepository`
- **Service Layer**: `ValidacaoService`, `AutenticacaoService`, `LogService`
- **Blueprint Pattern**: Separação de rotas por contexto

### Camadas da Aplicação
```
┌─────────────────────────────────────┐
│  Apresentação (module.py)           │
│  - Blueprints de rotas              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Serviços (core/services.py)        │
│  - ValidacaoService                 │
│  - AutenticacaoService              │
│  - LogService                       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Repositórios (core/repositories)   │
│  - GestorEscolarRepository          │
│  - EscolaRepository                 │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Database (core/database.py)        │
└─────────────────────────────────────┘
```

### Diagrama de Relacionamentos
```
┌──────────────┐
│   Escola     │
└──────┬───────┘
       │ 1
       │
       │ N
┌──────┴────────────────┐
│  GestorEscolar        │
│  - escola_id (FK)     │
│  - nome               │
│  - email              │
│  - telefone           │
│  - cpf                │
│  - tipo_gestor        │
└───────────────────────┘
```

---

## 🔌 Endpoints (Rotas)

### 1. `GET /gestores/escola/<int:escola_id>/listar`
**Descrição**: Lista todos os gestores de uma escola específica

**Autenticação**: Requerida (Administrador ou Escola proprietária)

**Parâmetros de Rota**:
- `escola_id`: ID da escola

**Resposta**:
```html
Status: 200 OK
Template: templates/gestores/listar.html
Contexto: {
    'escola': Escola,
    'gestores': List[GestorEscolar]
}
```

**Permissões**:
- Administrador: pode visualizar gestores de qualquer escola
- Escola: pode visualizar apenas gestores da própria escola

---

### 2. `GET/POST /gestores/escola/<int:escola_id>/cadastrar`
**Descrição**: Cadastra um novo gestor escolar para uma escola

**Autenticação**: Requerida (Administrador ou Escola proprietária)

**Corpo da Requisição** (POST - multipart/form-data):
```json
{
    "nome": "string (obrigatório, max 200)",
    "email": "string (opcional, validação de formato)",
    "telefone": "string (opcional, validação de formato)",
    "cpf": "string (opcional, validação de formato e dígitos)",
    "tipo_gestor": "string (opcional, ex: diretor, coordenador, financeiro)"
}
```

**Validações**:
1. **Nome**: Obrigatório, não pode ser vazio
2. **Telefone**: Se fornecido, deve estar no formato válido
3. **CPF**: Se fornecido, deve ser válido (11 dígitos + verificadores)
4. **Email**: Se fornecido, deve estar em formato válido

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /gestores/escola/{escola_id}/listar
Flash: "Gestor cadastrado com sucesso!"
```

---

### 3. `GET/POST /gestores/editar/<int:id>`
**Descrição**: Edita um gestor escolar existente

**Autenticação**: Requerida (Administrador ou Escola proprietária)

**Parâmetros de Rota**:
- `id`: ID do gestor

**Permissões**:
- Administrador: pode editar qualquer gestor
- Escola: pode editar apenas gestores da própria escola

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /gestores/escola/{escola_id}/listar
Flash: "Gestor atualizado com sucesso!"
```

---

### 4. `POST /gestores/excluir/<int:id>`
**Descrição**: Exclui um gestor escolar

**Autenticação**: Requerida (Administrador ou Escola proprietária)

**Parâmetros de Rota**:
- `id`: ID do gestor

**Permissões**:
- Administrador: pode excluir qualquer gestor
- Escola: pode excluir apenas gestores da própria escola

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /gestores/escola/{escola_id}/listar
Flash: "Gestor excluído com sucesso!"
```

---

### 5. `GET /gestores/meus-gestores`
**Descrição**: Atalho para a escola visualizar seus próprios gestores

**Autenticação**: Requerida (Tipo: Escola)

**Comportamento**:
- Busca a escola do usuário logado
- Redireciona para `/gestores/escola/{escola_id}/listar`

**Resposta**:
```json
Status: 302 Redirect
Location: /gestores/escola/{escola_id}/listar
```

---

## 📊 Modelos de Dados

### Tabela `gestores_escolares` (PostgreSQL)
```sql
CREATE TABLE gestores_escolares (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER NOT NULL REFERENCES escolas(id) ON DELETE CASCADE,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    telefone VARCHAR(20),
    cpf VARCHAR(14),
    tipo_gestor VARCHAR(50), -- ex: diretor, coordenador, financeiro
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gestores_escola ON gestores_escolares(escola_id);
```

### Campos
- **id**: Identificador único do gestor
- **escola_id**: Referência à escola (FK com CASCADE DELETE)
- **nome**: Nome completo do gestor (obrigatório)
- **email**: E-mail de contato (opcional)
- **telefone**: Telefone de contato (opcional)
- **cpf**: CPF do gestor (opcional)
- **tipo_gestor**: Tipo/cargo do gestor (opcional)
- **data_cadastro**: Data de criação do registro

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Escola (Própria) | Fornecedor | Responsável |
|------|---------------|------------------|------------|-------------|
| `/gestores/escola/:id/listar` | ✅ | ✅ (própria) | ❌ | ❌ |
| `/gestores/escola/:id/cadastrar` | ✅ | ✅ (própria) | ❌ | ❌ |
| `/gestores/editar/:id` | ✅ | ✅ (própria) | ❌ | ❌ |
| `/gestores/excluir/:id` | ✅ | ✅ (própria) | ❌ | ❌ |
| `/gestores/meus-gestores` | ❌ | ✅ | ❌ | ❌ |

---

## 📝 Regras de Negócio

### 1. Cadastro de Gestores
- Apenas Administradores e a Escola proprietária podem cadastrar gestores
- Nome é obrigatório
- Email, telefone, CPF e tipo_gestor são opcionais
- Múltiplos gestores podem ser cadastrados para a mesma escola

### 2. Edição de Gestores
- Apenas Administradores e a Escola proprietária podem editar
- Escola só pode editar gestores da própria escola
- Validações são aplicadas em campos fornecidos

### 3. Exclusão de Gestores
- Apenas Administradores e a Escola proprietária podem excluir
- Exclusão é em cascata (se a escola for excluída, gestores são removidos automaticamente)
- Não há verificação de dependências (gestores são dados auxiliares)

### 4. Visualização
- Administradores podem ver gestores de todas as escolas
- Escolas podem ver apenas seus próprios gestores
- Gestores são exibidos na tela de visualização de escola

### 5. Tipos de Gestores
Exemplos comuns de tipos:
- `diretor`: Diretor(a) da escola
- `coordenador`: Coordenador(a) pedagógico(a)
- `financeiro`: Responsável financeiro
- `secretario`: Secretário(a) escolar
- Pode ser qualquer string livre

---

## 🔗 Relacionamentos com Outros Módulos

- **Escolas**: Cada gestor pertence a uma única escola (relacionamento N:1)
- **Usuários**: Gestores são dados de contato, não são usuários do sistema

---

## 📦 Dependências

- `core.repositories.GestorEscolarRepository`
- `core.repositories.EscolaRepository`
- `core.services.AutenticacaoService`
- `core.services.ValidacaoService`
- `core.services.LogService`
- `core.database.Database`

---

## 🔄 Logs e Auditoria

Todas as operações de gestores são registradas na tabela `logs_alteracoes`:

- **INSERT**: Cadastro de novo gestor
- **UPDATE**: Atualização de dados do gestor
- **DELETE**: Exclusão de gestor

Campos registrados:
- `usuario_id`: Quem realizou a operação
- `tabela`: 'gestores_escolares'
- `registro_id`: ID do gestor
- `acao`: 'INSERT', 'UPDATE' ou 'DELETE'
- `dados_antigos`: Estado anterior (UPDATE/DELETE)
- `dados_novos`: Estado novo (INSERT/UPDATE)
- `descricao`: Descrição da operação

---

## 💡 Casos de Uso

### Caso de Uso 1: Escola Cadastra Gestor
1. Escola faz login no sistema
2. Acessa "Meus Gestores" no menu
3. Clica em "Cadastrar Novo Gestor"
4. Preenche dados: nome, email, telefone, tipo (diretor)
5. Sistema valida e salva
6. Gestor aparece na listagem

### Caso de Uso 2: Administrador Visualiza Gestores
1. Admin faz login
2. Acessa listagem de escolas
3. Clica em "Visualizar" em uma escola
4. Vê lista de gestores cadastrados
5. Pode editar ou excluir gestores

### Caso de Uso 3: Atualização de Contato
1. Escola acessa seus gestores
2. Clica em "Editar" no gestor desejado
3. Atualiza telefone ou email
4. Sistema registra alteração no log
5. Dados atualizados ficam disponíveis

---

## 🚀 Melhorias Futuras

1. **Validação de Email Único**: Adicionar validação para evitar emails duplicados
2. **Validação de CPF Único**: Garantir que um CPF não seja usado por múltiplos gestores
3. **Notificações**: Enviar email ao gestor quando cadastrado
4. **Hierarquia**: Implementar hierarquia de gestores (gestor principal, secundário)
5. **Permissões Granulares**: Permitir que gestores tenham diferentes níveis de acesso
6. **Histórico de Gestores**: Manter histórico de gestores antigos (soft delete)
7. **Upload de Documentos**: Permitir anexar documentos ao gestor
