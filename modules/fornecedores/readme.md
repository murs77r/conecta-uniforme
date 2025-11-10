# Módulo de Fornecedores

============================================
RF05 - MANTER CADASTRO DE FORNECEDOR
============================================
Este módulo é responsável por:
- RF05.1: Listar fornecedores
- RF05.2: Criar fornecedor
- RF05.3: Editar fornecedor
- RF05.4: Apagar fornecedor

Controla o processo de controle de fornecedores no sistema.

---

## 📋 Visão Geral

O módulo de **Fornecedores** gerencia empresas que vendem uniformes escolares na plataforma Conecta Uniforme. Cada fornecedor está vinculado a um usuário e possui cadastro completo com informações comerciais (CNPJ, razão social, endereço).

### Propósito
- Cadastrar e gerenciar fornecedores de uniformes
- Vincular fornecedores a usuários do sistema
- Validar dados comerciais (CNPJ, endereço)
- Controlar ativação/desativação de fornecedores

---

## 🏗️ Arquitetura

### Padrões Utilizados
- **Repository Pattern**: `FornecedorRepository`, `UsuarioRepository`
- **Service Layer**: `CRUDService`, `ValidacaoService`, `AutenticacaoService`
- **Composition**: Fornecedor compõe Usuario (relacionamento 1:1)

### Estrutura de Dados
```
Usuario (tipo='fornecedor')
    ↓ (1:1)
Fornecedor (dados comerciais)
    ↓ (1:N)
Produtos
```

---

## 🔌 Endpoints (Rotas)

### 1. `GET /fornecedores/listar`
**Descrição**: Lista fornecedores cadastrados

**Autenticação**: Requerida (Todos)

**Parâmetros Query**:
```json
{
    "busca": "string (opcional, busca em nome/razão social/CNPJ)"
}
```

**Resposta**:
```html
Status: 200 OK
Template: templates/fornecedores/listar.html
Contexto: {
    'fornecedores': [{
        'id': int,
        'usuario_id': int,
        'usuario_nome': str,
        'usuario_email': str,
        'razao_social': str,
        'cnpj': str,
        'endereco': str,
        'cidade': str,
        'estado': str,
        'cep': str,
        'ativo': bool
    }, ...],
    'filtro_busca': str
}
```

**SQL**:
```sql
SELECT 
    f.id, f.usuario_id, f.cnpj, f.razao_social, f.endereco,
    f.cidade, f.estado, f.cep, f.ativo,
    u.nome as usuario_nome, u.email as usuario_email
FROM fornecedores f
JOIN usuarios u ON f.usuario_id = u.id
WHERE (
    u.nome ILIKE '%{busca}%' OR
    f.razao_social ILIKE '%{busca}%' OR
    f.cnpj ILIKE '%{busca}%'
)
ORDER BY u.nome ASC
```

---

### 2. `POST /fornecedores/cadastrar`
**Descrição**: Cadastra novo fornecedor (cria usuário + dados comerciais)

**Autenticação**: Requerida (Administrador)

**Corpo (form-data)**:
```json
{
    "nome": "string (obrigatório, nome fantasia)",
    "email": "string (obrigatório, único)",
    "telefone": "string (obrigatório)",
    "cnpj": "string (obrigatório, 14 dígitos, único)",
    "razao_social": "string (obrigatório)",
    "endereco": "string (obrigatório)",
    "cidade": "string (obrigatório)",
    "estado": "string (obrigatório, UF)",
    "cep": "string (obrigatório, 99999-999)"
}
```

**Validações**:
1. **CNPJ**: 14 dígitos, dígitos verificadores, unicidade
2. **Email**: Formato válido, unicidade
3. **CEP**: Formato 99999-999
4. **Estado**: Sigla UF válida (2 caracteres)

**Lógica de Criação**:
```python
# 1. Valida CNPJ
if not ValidacaoService.validar_cnpj(cnpj):
    flash('CNPJ inválido', 'danger')
    return redirect(...)

# 2. Cria usuário tipo 'fornecedor'
dados_usuario = {
    'nome': nome,
    'email': email,
    'telefone': telefone,
    'tipo': 'fornecedor',
    'ativo': True
}
usuario_id = UsuarioRepository().inserir(dados_usuario)

# 3. Cria dados comerciais
dados_fornecedor = {
    'usuario_id': usuario_id,
    'cnpj': cnpj,
    'razao_social': razao_social,
    'endereco': endereco,
    'cidade': cidade,
    'estado': estado,
    'cep': cep,
    'ativo': True
}
fornecedor_id = FornecedorRepository().inserir(dados_fornecedor)

# 4. Log automático via CRUDService
LogService.registrar(...)
```

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /fornecedores/listar
Flash: "Fornecedor cadastrado com sucesso"
```

---

### 3. `POST /fornecedores/editar/<int:id>`
**Descrição**: Edita dados de fornecedor existente

**Autenticação**: Requerida (Administrador ou Fornecedor próprio)

**Corpo (form-data)**:
```json
{
    "nome": "string",
    "email": "string",
    "telefone": "string",
    "razao_social": "string",
    "endereco": "string"
}
```

**Observações**:
- CNPJ **não pode** ser alterado (imutável)
- Atualiza tanto `usuarios` quanto `fornecedores`
- Mantém logs das alterações

**Lógica**:
```python
# Atualiza usuário
UsuarioRepository().atualizar(fornecedor['usuario_id'], dados_usuario)

# Atualiza fornecedor (com log)
CRUDService.atualizar_com_log(
    id, dados_fornecedor, dados_antigos, usuario_logado_id
)
```

**Resposta**:
```json
Status: 302 Redirect
Location: /fornecedores/listar
Flash: "Fornecedor atualizado com sucesso"
```

---

### 4. `POST /fornecedores/excluir/<int:id>`
**Descrição**: Desativa fornecedor (soft delete)

**Autenticação**: Requerida (Administrador)

**Verificações de Dependência**:
```python
dependencias = [
    {
        'tabela': 'produtos', 
        'campo': 'fornecedor_id', 
        'mensagem': 'produtos'
    }
]

bloqueios = CRUDService.verificar_dependencias(id, dependencias)
if bloqueios:
    flash(f"Não é possível excluir: {' '.join(bloqueios)}", 'warning')
    return redirect(...)
```

**Comportamento**:
- Define `fornecedores.ativo = false`
- Define `usuarios.ativo = false`
- Produtos do fornecedor ficam inativos
- Histórico preservado

**Resposta**:
```json
Status: 302 Redirect
Location: /fornecedores/listar
Flash: "Fornecedor desativado com sucesso"
```

---

## 📊 Modelos de Dados

### Fornecedor (Dataclass)
```python
@dataclass
class Fornecedor:
    id: Optional[int] = None
    usuario_id: int = 0
    cnpj: str = ''
    razao_social: str = ''
    endereco: str = ''
    cidade: str = ''
    estado: str = ''
    cep: str = ''
    ativo: bool = True
```

### Tabela `fornecedores` (PostgreSQL)
```sql
CREATE TABLE fornecedores (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) UNIQUE,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(9),
    ativo BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_fornecedores_usuario ON fornecedores(usuario_id);
CREATE INDEX idx_fornecedores_cnpj ON fornecedores(cnpj);
```

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Fornecedor (Próprio) | Fornecedor (Outro) | Escola | Responsável |
|------|---------------|----------------------|--------------------|--------|-------------|
| `/fornecedores/listar` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/fornecedores/cadastrar` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/fornecedores/editar/:id` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/fornecedores/excluir/:id` | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 📝 Regras de Negócio

### 1. Relacionamento Usuario-Fornecedor
- Relação 1:1 (um usuário pode ser fornecedor de apenas uma empresa)
- Usuario deve ter `tipo='fornecedor'`
- `usuario_id` é UNIQUE em `fornecedores`

### 2. Validação de CNPJ
```python
def validar_cnpj(cnpj: str) -> bool:
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # CNPJs inválidos conhecidos
    if cnpj in ['00000000000000', '11111111111111', ...]:
        return False
    
    # Algoritmo de validação de dígitos verificadores
    # (implementado em ValidacaoService.validar_cnpj)
    return True
```

### 3. Imutabilidade de CNPJ
- CNPJ não pode ser alterado após cadastro
- Para corrigir CNPJ incorreto: excluir e recadastrar

### 4. Desativação em Cascata
Ao desativar fornecedor:
1. `fornecedores.ativo = false`
2. `usuarios.ativo = false`
3. Produtos associados ficam inativos
4. Não aparecem mais em listagens públicas