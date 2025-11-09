# Módulo de Produtos

## 📋 Visão Geral

O módulo de **Produtos** gerencia o catálogo de uniformes escolares disponíveis para venda na plataforma Conecta Uniforme. Fornecedores cadastram produtos vinculados a escolas específicas, criando um marketplace segmentado.

### Propósito
- Gerenciar catálogo de uniformes (camisas, calças, sapatos, etc.)
- Vincular produtos a fornecedores e escolas
- Controlar estoque e precificação
- Exibir vitrine filtrada por categoria/escola

---

## 🏗️ Arquitetura

### Padrões Utilizados
- **Repository Pattern**: `ProdutoRepository`, `FornecedorRepository`
- **Service Layer**: `CRUDService`, `AutenticacaoService`, `LogService`
- **Filter Pattern**: Múltiplos filtros na vitrine

### Estrutura de Dados
```
Fornecedor
    ↓ (1:N)
Produto (categoria, tamanho, cor, preço, estoque)
    ↓ (M:1)
Escola (produtos específicos para cada escola)
```

---

## 🔌 Endpoints (Rotas)

### 1. `GET /produtos/vitrine`
**Descrição**: Exibe catálogo público de produtos

**Autenticação**: Opcional (acesso público)

**Parâmetros Query**:
```json
{
    "categoria": "string (opcional: Camisa, Calça, Sapato, Agasalho, Acessório)",
    "escola": "int (opcional, ID da escola)",
    "busca": "string (opcional, busca em nome/descrição)"
}
```

**Resposta**:
```html
Status: 200 OK
Template: templates/produtos/vitrine.html
Contexto: {
    'produtos': [{
        'id': int,
        'nome': str,
        'descricao': str,
        'categoria': str,
        'tamanho': str,
        'cor': str,
        'preco': Decimal,
        'estoque': int,
        'imagem': str,
        'fornecedor_nome': str,
        'escola_nome': str,
        'ativo': bool
    }, ...],
    'escolas': [{'id': int, 'nome': str}, ...],
    'filtro_categoria': str,
    'filtro_escola': str,
    'filtro_busca': str
}
```

**SQL Otimizado**:
```sql
SELECT 
    p.id, p.nome, p.descricao, p.categoria, p.tamanho, p.cor,
    p.preco, p.estoque, p.imagem, p.ativo,
    f.razao_social as fornecedor_nome,
    u_escola.nome as escola_nome
FROM produtos p
JOIN fornecedores f ON p.fornecedor_id = f.id
LEFT JOIN escolas e ON p.escola_id = e.id
LEFT JOIN usuarios u_escola ON e.usuario_id = u_escola.id
WHERE p.ativo = TRUE
  AND f.ativo = TRUE
  AND (p.categoria = %s OR %s = '')
  AND (p.escola_id = %s OR %s IS NULL)
  AND (p.nome ILIKE %s OR p.descricao ILIKE %s OR %s = '')
ORDER BY p.nome ASC
```

---

### 2. `POST /produtos/cadastrar`
**Descrição**: Cadastra novo produto no catálogo

**Autenticação**: Requerida (Administrador ou Fornecedor)

**Corpo (form-data)**:
```json
{
    "nome": "string (obrigatório, ex: Camisa Polo Branca)",
    "descricao": "string (opcional)",
    "categoria": "string (obrigatório: Camisa|Calça|Sapato|Agasalho|Acessório)",
    "tamanho": "string (obrigatório: PP|P|M|G|GG|36|38|40...)",
    "cor": "string (obrigatório: Branco|Azul|Preto...)",
    "preco": "decimal (obrigatório, ex: 49.90)",
    "estoque": "int (obrigatório, >= 0)",
    "escola_id": "int (opcional, ID da escola)",
    "fornecedor_id": "int (obrigatório, auto-preenchido se fornecedor logado)",
    "imagem": "string (opcional, URL ou base64)"
}
```

**Validações**:
1. **Preço**: Deve ser > 0
2. **Estoque**: Deve ser >= 0
3. **Categoria**: Deve estar na lista permitida
4. **Fornecedor**: Deve estar ativo
5. **Escola**: Se informada, deve estar ativa

**Lógica de Cadastro**:
```python
# 1. Se usuário é fornecedor, usa seu próprio fornecedor_id
if usuario_logado['tipo'] == 'fornecedor':
    fornecedor = FornecedorRepository().buscar_por_usuario_id(
        usuario_logado['id']
    )
    dados['fornecedor_id'] = fornecedor['id']

# 2. Valida campos obrigatórios
if not dados['nome'] or not dados['fornecedor_id'] or not dados['preco']:
    flash('Preencha campos obrigatórios', 'danger')
    return redirect(...)

# 3. Insere produto com log automático
produto_id = CRUDService.criar_com_log(
    dados, usuario_logado['id']
)
```

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /produtos/vitrine
Flash: "Produto cadastrado com sucesso"
Log: INSERT em produtos + INSERT em logs_sistema
```

---

### 3. `POST /produtos/editar/<int:id>`
**Descrição**: Edita produto existente

**Autenticação**: Requerida (Administrador ou Fornecedor proprietário)

**Corpo (form-data)**:
```json
{
    "nome": "string",
    "preco": "decimal",
    "estoque": "int"
}
```

**Campos Editáveis**:
- ✅ Nome, descrição
- ✅ Preço, estoque
- ✅ Tamanho, cor
- ❌ Fornecedor (imutável)
- ❌ Categoria (imutável, recadastrar se necessário)

**Verificação de Propriedade** (Fornecedor):
```python
if usuario_logado['tipo'] == 'fornecedor':
    fornecedor = FornecedorRepository().buscar_por_usuario_id(
        usuario_logado['id']
    )
    if produto['fornecedor_id'] != fornecedor['id']:
        flash('Acesso negado', 'danger')
        return redirect(...)
```

**Resposta**:
```json
Status: 302 Redirect
Location: /produtos/vitrine
Flash: "Produto atualizado com sucesso"
Log: UPDATE em produtos
```

---

### 4. `POST /produtos/excluir/<int:id>`
**Descrição**: Desativa produto (soft delete)

**Autenticação**: Requerida (Administrador ou Fornecedor proprietário)

**Verificação de Dependência**:
```python
bloqueios = CRUDService.verificar_dependencias(id, [
    {
        'tabela': 'itens_pedido',
        'campo': 'produto_id',
        'mensagem': 'itens de pedido'
    }
])

if bloqueios:
    flash('Não é possível excluir: produto possui itens de pedido', 'warning')
    return redirect(...)
```

**Comportamento**:
- Define `ativo = false`
- Produto não aparece mais na vitrine
- Pedidos antigos são preservados
- Estoque mantido para histórico

**Resposta**:
```json
Status: 302 Redirect
Location: /produtos/vitrine
Flash: "Produto desativado com sucesso"
```

---

## 📊 Modelos de Dados

### Produto (Dataclass)
```python
@dataclass
class Produto:
    id: Optional[int] = None
    fornecedor_id: int = 0
    escola_id: Optional[int] = None
    nome: str = ''
    descricao: str = ''
    categoria: str = ''  # Camisa, Calça, Sapato, Agasalho, Acessório
    tamanho: str = ''
    cor: str = ''
    preco: Decimal = Decimal('0.00')
    estoque: int = 0
    imagem: str = ''
    ativo: bool = True
```

### Tabela `produtos` (PostgreSQL)
```sql
CREATE TABLE produtos (
    id SERIAL PRIMARY KEY,
    fornecedor_id INT NOT NULL REFERENCES fornecedores(id),
    escola_id INT REFERENCES escolas(id),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL 
        CHECK (categoria IN ('Camisa', 'Calça', 'Sapato', 'Agasalho', 'Acessório')),
    tamanho VARCHAR(10),
    cor VARCHAR(50),
    preco DECIMAL(10,2) NOT NULL CHECK (preco > 0),
    estoque INT DEFAULT 0 CHECK (estoque >= 0),
    imagem TEXT,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_produtos_escola ON produtos(escola_id);
CREATE INDEX idx_produtos_categoria ON produtos(categoria);
CREATE INDEX idx_produtos_ativo ON produtos(ativo);
```

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Fornecedor (Próprio) | Fornecedor (Outro) | Escola | Responsável |
|------|---------------|----------------------|--------------------|--------|-------------|
| `/produtos/vitrine` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/produtos/cadastrar` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/produtos/editar/:id` | ✅ | ✅ (próprio) | ❌ | ❌ | ❌ |
| `/produtos/excluir/:id` | ✅ | ✅ (próprio) | ❌ | ❌ | ❌ |

---

## 📝 Regras de Negócio

### 1. Categorias de Produtos
```python
CATEGORIAS_PERMITIDAS = [
    'Camisa',      # Camisas polo, regatas, camisetas
    'Calça',       # Calças, bermudas, shorts
    'Sapato',      # Calçados em geral
    'Agasalho',    # Moletons, jaquetas
    'Acessório'    # Meias, cintos, gravatas, etc.
]
```

### 2. Tamanhos Padrão
- **Roupas**: PP, P, M, G, GG, XG, XXG
- **Calçados**: 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45

### 3. Controle de Estoque
- Estoque decrementado ao finalizar pedido
- Estoque liberado se pedido for cancelado
- Produtos com estoque = 0 ainda aparecem na vitrine (com aviso)
- Estoque negativo não é permitido (constraint)

### 4. Precificação
- Preço definido pelo fornecedor
- Preço congelado no momento da adição ao carrinho
- Taxa da plataforma aplicada apenas nos repasses (invisível para responsável)

### 5. Vinculação Escola-Produto
- `escola_id` é opcional (NULL = produto genérico)
- Produtos vinculados aparecem destacados para alunos da escola
- Filtragem por escola na vitrine