# CONECTA UNIFORME

Sistema de gerenciamento de uniformes escolares desenvolvido em Python/Flask com PostgreSQL.

## 📋 Descrição

O **Conecta Uniforme** é uma plataforma de e-commerce (marketplace) que conecta digitalmente:
- **Instituições de Ensino** - Gerenciam fornecedores homologados
- **Fornecedores de Uniformes** - Cadastram e vendem produtos
- **Pais/Responsáveis** - Compram uniformes escolares

---

## 🎯 Funcionalidades

### RF01 - Manter Cadastro de Usuário
- Cadastrar, consultar, editar e excluir usuários
- Log de alterações para auditoria
- Tipos: Administrador, Escola, Fornecedor, Responsável

### RF02 - Gerenciar Autenticação e Acesso
- Sistema de login por código de acesso enviado via email
- Código válido por 24 horas
- Sessões seguras
- Login com Passkey (WebAuthn) – use Windows Hello, Face/Touch ID ou chave de segurança

### RF03 - Gerenciar Produtos e Vitrine
- Cadastro de produtos (uniformes)
- Vitrine com filtros automáticos (escola, categoria, fornecedor)
- Controle de estoque
- Categorias: Camisa, Calça, Short, Calçado, Acessório

### RF04 - Gerenciar Escolas
- CRUD completo de escolas
- Gestão de fornecedores homologados
- Validação de CNPJ
- Gestores escolares

### RF05 - Gerenciar Fornecedores
- CRUD completo de fornecedores
- Vinculação com escolas (homologação)
- Validação de CNPJ

### RF06 - Gerenciar Pedidos
- Carrinho de compras
- Finalização de pedidos
- Histórico de compras
- Estados: carrinho → pendente → pago → cancelado

### RF07 - Gerenciar Repasses Financeiros
- Controle de repasses para fornecedores
- Cálculo automático de taxas (10% plataforma)
- Rastreamento de pagamentos

---

## 🏗️ Arquitetura Técnica

### Estrutura de Diretórios

```
conecta-uniforme/
├── core/                          # Camada de infraestrutura
│   ├── database.py               # Gerenciamento de conexões PostgreSQL
│   ├── models.py                 # Modelos de dados (dataclasses)
│   ├── repositories.py           # Acesso a dados (Repository Pattern)
│   └── services.py               # Lógica de negócio
│
├── modules/                       # Camada de aplicação (Blueprints)
│   ├── autenticacao/
│   │   ├── module.py             # Autenticação (código + WebAuthn)
│   │   └── readme.md             # Documentação técnica
│   ├── usuarios/
│   │   ├── module.py             # CRUD de usuários
│   │   └── readme.md
│   ├── escolas/
│   │   ├── module.py             # Gestão de escolas + gestores
│   │   └── readme.md
│   ├── fornecedores/
│   │   ├── module.py             # Gestão de fornecedores
│   │   └── readme.md
│   ├── produtos/
│   │   ├── module.py             # Catálogo de produtos
│   │   └── readme.md
│   ├── pedidos/
│   │   ├── module.py             # Carrinho + pedidos
│   │   └── readme.md
│   └── repasses/
│       ├── module.py             # Repasses financeiros
│       └── readme.md
│
├── templates/                     # Camada de apresentação (Jinja2)
├── static/                        # Recursos estáticos (CSS, JS, imagens)
├── app.py                         # Aplicação principal Flask
├── config.py                      # Configurações
├── schema.sql                     # Schema do banco de dados
└── requirements.txt               # Dependências Python
```

### Padrões de Design Aplicados

#### 1. **Repository Pattern**
Encapsula acesso a dados e queries complexas.

```python
# Exemplo de uso
escola_repo = EscolaRepository()
escolas = escola_repo.listar_com_filtros({'busca': 'Municipal', 'ativo': 'true'})
```

#### 2. **Service Layer Pattern**
Centraliza lógica de negócio reutilizável.

```python
# Exemplo: Criar usuário com log automático
crud_service = CRUDService(usuario_repo, 'Usuario')
novo_id = crud_service.criar_com_log(dados, usuario_logado['id'])
```

#### 3. **Blueprint Pattern (Flask)**
Modularização de rotas por contexto de negócio.

```python
# Cada módulo é um Blueprint independente
from modules.escolas import escolas_bp
from modules.produtos import produtos_bp
app.register_blueprint(escolas_bp)
app.register_blueprint(produtos_bp)
```

### Camadas da Aplicação

#### 1️⃣ **Camada de Dados** (`core/database.py`)
- Gerencia conexões PostgreSQL via psycopg2
- Métodos auxiliares: `conectar()`, `executar()`, `inserir()`, `atualizar()`, `excluir()`, `buscar_por_id()`
- RealDictCursor para resultados como dicionários

#### 2️⃣ **Camada de Modelos** (`core/models.py`)
- Dataclasses Python para entidades do domínio
- Modelos: `Usuario`, `Escola`, `GestorEscolar`, `Fornecedor`, `Produto`, `Pedido`, `ItemPedido`, `Responsavel`, `RepasseFinanceiro`
- Tipagem forte com `Optional` e valores padrão

#### 3️⃣ **Camada de Repositórios** (`core/repositories.py`)
- `BaseRepository`: CRUD genérico (`buscar_por_id`, `inserir`, `atualizar`, `excluir`, `listar`)
- Repositórios específicos:
  - `UsuarioRepository`: Busca por email/tipo, listagem com filtros
  - `EscolaRepository`: Busca com JOIN de usuário, listagem com filtros
  - `GestorEscolarRepository`: Gestores vinculados a escolas
  - `FornecedorRepository`: Fornecedores homologados
  - `ProdutoRepository`: Produtos com estoque
  - `PedidoRepository`: Carrinho e pedidos finalizados
  - `ResponsavelRepository`: Responsáveis por alunos
  - `RepasseFinanceiroRepository`: Repasses para fornecedores

#### 4️⃣ **Camada de Serviços** (`core/services.py`)
- **AutenticacaoService**: Verifica sessão e permissões
- **ValidacaoService**: Validação de CPF, CNPJ, email, telefone, CEP
- **LogService**: Registro de auditoria em JSONB (`logs_alteracoes`)
- **CRUDService**: Operações CRUD com logging automático e verificação de dependências

#### 5️⃣ **Camada de Aplicação** (`modules/*/module.py`)
- Blueprints Flask expondo rotas HTTP
- Controllers que orquestram repositories e services
- Renderização de templates Jinja2
- Tratamento de formulários e validações de entrada

---

## 📊 Métricas da Refatoração

A aplicação passou por uma refatoração completa para arquitetura em camadas orientada a objetos:

| Módulo | Antes | Depois | Redução |
|--------|-------|--------|---------|
| usuarios.py | 720 linhas | 380 linhas | **-47%** |
| escolas.py | 850 linhas | 420 linhas | **-51%** |
| pedidos.py | 280 linhas | 155 linhas | **-45%** |
| repasses.py | 180 linhas | 105 linhas | **-42%** |
| **TOTAL** | **2.030 linhas** | **1.060 linhas** | **-48%** |

### Benefícios Alcançados

✅ **Redução de código em 48%**  
✅ **Eliminação de duplicação** (validações, queries, logging)  
✅ **Manutenibilidade melhorada** (código organizado em camadas)  
✅ **Testabilidade** (componentes isolados)  
✅ **Reutilização** (serviços compartilhados)  
✅ **Escalabilidade** (fácil adicionar funcionalidades)

---

## 🚀 Tecnologias

- **Python 3.x**
- **Flask** - Framework web com Blueprints
- **PostgreSQL** - Banco de dados relacional
- **psycopg2** - Driver PostgreSQL
- **Bootstrap 5** - Interface responsiva
- **Jinja2** - Template engine
- **SMTP** - Envio de emails (códigos de acesso)
- **WebAuthn/Passkeys** - Autenticação sem senha (FIDO2)
- **JavaScript** - Utilitários e WebAuthn (`base.js`)

---

## 🔐 Passkeys (WebAuthn)

Autenticação moderna sem senha usando biometria ou chaves de segurança:

### Como usar

1. **Cadastro de Passkey**: 
   - Faça login normalmente com código de acesso
   - Acesse "Cadastrar/gerenciar Passkey" na Home
   - Ou vá para `/auth/passkeys`
   - Clique em "Cadastrar Passkey"
   - Use Windows Hello, Touch/Face ID ou chave de segurança física

2. **Login com Passkey**:
   - Na tela de login, digite seu email
   - Clique em "Entrar com Passkey"
   - Autentique com biometria ou chave de segurança

### Configuração (Produção)

No arquivo `.env`:

```env
WEBAUTHN_RP_ID=seu-dominio.com
WEBAUTHN_ORIGIN=https://seu-dominio.com
WEBAUTHN_RP_NAME=Conecta Uniforme
```

### Configuração (Desenvolvimento)

Padrões para desenvolvimento local com `localhost`:

```env
WEBAUTHN_RP_ID=localhost
WEBAUTHN_ORIGIN=http://localhost:5000
WEBAUTHN_RP_NAME=Conecta Uniforme
```

### Banco de Dados

Aplique as alterações de schema (tabela `webauthn_credentials`):

```bash
psql -U usuario -d conecta_uniforme -f schema.sql
```

---

## 📚 Documentação dos Módulos

Cada módulo possui documentação técnica detalhada em seu respectivo `readme.md`:

- **`modules/autenticacao/readme.md`** - WebAuthn + Código por E-mail (2 métodos de autenticação)
- **`modules/usuarios/readme.md`** - CRUD completo, validações, logs de auditoria
- **`modules/escolas/readme.md`** - Gestão de escolas, gestores e homologação
- **`modules/fornecedores/readme.md`** - CRUD de fornecedores e validação de CNPJ
- **`modules/produtos/readme.md`** - Catálogo, vitrine com filtros e controle de estoque
- **`modules/pedidos/readme.md`** - Carrinho de compras e finalização
- **`modules/repasses/readme.md`** - Cálculo de repasses e taxas financeiras

---

## 📄 Licença

Projeto desenvolvido para fins educacionais da **Faculdade de Tecnologia e Inovação SENAC-DF**

## 👥 Autores

Desenvolvido por João Paulo Freitas, João Paulo Nunes, Murilo Souza, Victor de Castro, Yuri Henrique.

---

**Conecta Uniforme** - Simplificando a compra de uniformes escolares! 🎒👕
