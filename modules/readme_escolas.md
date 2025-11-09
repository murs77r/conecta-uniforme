# RF04 - Gerenciar Escolas Homologadas (REFATORADO)

## 📋 Visão Geral
Este módulo gerencia o cadastro, consulta, edição e exclusão de escolas homologadas no sistema, além dos gestores escolares vinculados a cada escola.

## 🏗️ Arquitetura Refatorada

### Camadas da Aplicação
```
modules/escolas.py (Blueprint - Rotas e Controllers)
    ↓
core/services.py (Lógica de Negócio)
    ↓
core/repositories.py (Acesso a Dados)
    ↓
core/database.py (Conexão com BD)
```

### Principais Componentes

#### 1. **Repositórios** (`core/repositories.py`)
- `EscolaRepository`: Operações de banco relacionadas a escolas
- `UsuarioRepository`: Gerenciamento de usuários
- `GestorEscolarRepository`: Gerenciamento de gestores

#### 2. **Serviços** (`core/services.py`)
- `AutenticacaoService`: Verificação de sessão e permissões
- `CRUDService`: Operações genéricas com logging automático
- `ValidacaoService`: Validações de dados (CNPJ, CEP, telefone, etc.)
- `LogService`: Registro de auditoria

#### 3. **Modelos** (`core/models.py`)
- `Escola`: Dataclass representando uma escola
- `Usuario`: Dataclass representando um usuário
- `GestorEscolar`: Dataclass representando um gestor

## 🔄 Principais Melhorias

### Antes (Código Original)
```python
# Múltiplas chamadas diretas ao banco
executar_query(query, parametros, fetchall=True)
registrar_log(...)
validar_cnpj(cnpj)
verificar_sessao()
```

### Depois (Código Refatorado)
```python
# Uso de serviços e repositórios
escolas = escola_repo.listar_com_filtros(filtros)
validacao.validar_cnpj(dados_escola['cnpj'])
usuario_logado = auth_service.verificar_sessao()
crud_service.criar_com_log(dados, usuario_logado['id'])
```

## 📦 Benefícios da Refatoração

### 1. **Redução de Código**
- ✅ Eliminação de código repetitivo
- ✅ Funções reutilizáveis
- ✅ Menos linhas de código (redução ~40%)

### 2. **Manutenibilidade**
- ✅ Separação de responsabilidades
- ✅ Fácil localização de bugs
- ✅ Testes mais simples

### 3. **Escalabilidade**
- ✅ Fácil adicionar novos recursos
- ✅ Repositórios reutilizáveis
- ✅ Serviços compartilhados

### 4. **Qualidade**
- ✅ Validações centralizadas
- ✅ Logging automático
- ✅ Tratamento consistente de erros

## 🎯 Funcionalidades Mantidas

Todas as funcionalidades originais foram preservadas:

### RF04.1 - Cadastrar Escola
- ✅ Validação de CNPJ
- ✅ Verificação de duplicidade
- ✅ Cadastro de gestores escolares
- ✅ Logging automático

### RF04.2 - Consultar Escola
- ✅ Listagem com filtros (busca, status)
- ✅ Visualização detalhada
- ✅ Exibição de fornecedores homologados
- ✅ Listagem de gestores

### RF04.3 - Editar Escola
- ✅ Atualização de dados
- ✅ Gerenciamento de gestores
- ✅ Controle de permissões
- ✅ Validações de dados

### RF04.4 - Excluir Escola
- ✅ Verificação de dependências
- ✅ Prevenção de exclusões inválidas
- ✅ Logging de exclusões

### RF04.5-8 - Gestores Escolares
- ✅ CRUD completo de gestores
- ✅ Vinculação com escolas
- ✅ Validações de CPF e telefone

## 🔒 Controle de Acesso

| Operação | Administrador | Escola | Outros |
|----------|--------------|--------|--------|
| Listar Escolas | ✅ | ✅ | ✅ |
| Cadastrar Escola | ✅ | ❌ | ❌ |
| Editar Escola | ✅ | ✅ (própria) | ❌ |
| Excluir Escola | ✅ | ❌ | ❌ |
| Gerenciar Gestores | ✅ | ✅ (própria) | ❌ |

## 📝 Exemplo de Uso

```python
# Listar escolas com filtros
filtros = {
    'busca': 'Escola Municipal',
    'ativo': 'true'
}
escolas = escola_repo.listar_com_filtros(filtros)

# Criar escola com log automático
dados_escola = {
    'usuario_id': usuario_id,
    'cnpj': '12.345.678/0001-00',
    'razao_social': 'Escola ABC',
    'ativo': True
}
escola_id = crud_service.criar_com_log(dados_escola, admin_id)

# Validar dados
if not validacao.validar_cnpj(cnpj):
    flash('CNPJ inválido.', 'danger')
```

## 🔧 Dependências

- `core.database`: Acesso ao banco de dados
- `core.repositories`: Camada de dados
- `core.services`: Lógica de negócio
- `core.models`: Modelos de dados

## 📚 Documentação Adicional

- Ver `core/README.md` para detalhes da arquitetura
- Ver `readme_escolas_completo.md` para especificações detalhadas
 (modules/escolas.py)

Gerencia o ciclo de vida de escolas: cadastro, consulta, edição, exclusão e homologação de fornecedores.

- Blueprint: `escolas_bp`
- Prefixo de rota: `/escolas`
- Tabelas: `usuarios`, `escolas`, `homologacao_fornecedores`, `fornecedores`, `produtos`, `pedidos`
- Dependências:
  - `utils.py`: `executar_query`, `validar_cnpj`, `registrar_log`
  - `modules.autenticacao`: `verificar_sessao`, `verificar_permissao`
  - Templates: `templates/escolas/*.html`

## RF04.2 — Consultar (Listar)

- Rotas: `GET /escolas/` e `GET /escolas/listar`
- Tela: `templates/escolas/listar.html`
- Filtros (query string):
  - `busca` (nome da escola/razão social/CNPJ)
  - `ativo` (`true`/`false`)
- SQL base e filtros:
  ```sql
  SELECT e.*, u.nome, u.email, u.telefone, u.ativo
  FROM escolas e
  JOIN usuarios u ON e.usuario_id = u.id
  WHERE 1=1
  -- se busca
  AND (u.nome ILIKE %s OR e.razao_social ILIKE %s OR e.cnpj ILIKE %s)
  -- se ativo
  AND e.ativo = %s
  ORDER BY u.nome
  ```
- Requer login (`verificar_sessao`).

## RF04.1 — Cadastrar Escola

- Rota: `GET|POST /escolas/cadastrar`
- Tela: `templates/escolas/cadastrar.html`
- Permissão: apenas `administrador`.
- Entrada (POST): `nome`, `email`, `telefone`, `cnpj`, `razao_social`, `endereco`, `cidade`, `estado`, `cep`.
- Validações:
  - Campos obrigatórios (`nome`, `email`, `cnpj`, `razao_social`).
  - `cnpj` via `utils.validar_cnpj`.
  - Unicidade de `email` e `cnpj`.
- SQLs:
  - Verificar e-mail:
    ```sql
    SELECT id FROM usuarios WHERE email = %s
    ```
  - Verificar CNPJ:
    ```sql
    SELECT id FROM escolas WHERE cnpj = %s
    ```
  - Inserir usuário (perfil escola):
    ```sql
    INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
    VALUES (%s, %s, %s, 'escola', TRUE)
    RETURNING id
    ```
  - Inserir escola:
    ```sql
    INSERT INTO escolas (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    RETURNING id
    ```
- Log: `registrar_log(..., 'escolas', escola_id, 'INSERT', dados_novos=JSON)`.

## RF04.2 — Visualizar Escola

- Rota: `GET /escolas/visualizar/<id>`
- Tela: `templates/escolas/visualizar.html`
- SQLs:
  - Detalhes da escola + usuário:
    ```sql
    SELECT e.*, u.nome, u.email, u.telefone, u.ativo, u.data_cadastro
    FROM escolas e
    JOIN usuarios u ON e.usuario_id = u.id
    WHERE e.id = %s
    ```
  - Fornecedores homologados:
    ```sql
    SELECT f.id, u.nome, f.razao_social, hf.data_homologacao, hf.ativo
    FROM homologacao_fornecedores hf
    JOIN fornecedores f ON hf.fornecedor_id = f.id
    JOIN usuarios u ON f.usuario_id = u.id
    WHERE hf.escola_id = %s
    ORDER BY u.nome
    ```
- Requer login (`verificar_sessao`).

## RF04.x — Homologar Fornecedor para Escola (Admin)

- Rota: `GET|POST /escolas/homologar/<escola_id>`
- Tela: `templates/escolas/homologar.html`
- Permissão: `administrador`.
- GET: lista fornecedores ativos para seleção:
  ```sql
  SELECT f.id, u.nome, f.razao_social
  FROM fornecedores f JOIN usuarios u ON f.usuario_id = u.id
  WHERE u.ativo = TRUE
  ORDER BY u.nome
  ```
- POST: insere homologação (ou reativa se já existir):
  - Evitar duplicidade:
    ```sql
    SELECT id FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s
    ```
  - Reativar se necessário:
    ```sql
    UPDATE homologacao_fornecedores SET ativo = TRUE WHERE id = %s
    ```
  - Inserção:
    ```sql
    INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, ativo, observacoes)
    VALUES (%s, %s, TRUE, %s)
    RETURNING id
    ```
- Log correspondente (INSERT/UPDATE) em `logs_alteracoes`.

### Alternar status de homologação
- Rota: `POST /escolas/homologacao/<escola_id>/<fornecedor_id>/status`
- Permissão: `administrador`.
- SQL:
  ```sql
  SELECT id, ativo FROM homologacao_fornecedores WHERE escola_id = %s AND fornecedor_id = %s;
  UPDATE homologacao_fornecedores SET ativo = %s WHERE id = %s;
  ```

## RF04.3 — Editar Escola

- Rota: `GET|POST /escolas/editar/<id>`
- Permissões: `administrador` ou a própria `escola` dona do registro (só edita a si).
- GET: carrega dados para `templates/escolas/editar.html`.
- SQLs:
  - Buscar:
    ```sql
    SELECT e.*, u.nome, u.email, u.telefone, u.ativo
    FROM escolas e
    JOIN usuarios u ON e.usuario_id = u.id
    WHERE e.id = %s
    ```
  - Atualizar `usuarios`:
    ```sql
    UPDATE usuarios 
    SET nome = %s, email = %s, telefone = %s, ativo = %s, data_atualizacao = CURRENT_TIMESTAMP
    WHERE id = %s
    ```
  - Atualizar `escolas`:
    ```sql
    UPDATE escolas 
    SET cnpj = %s, razao_social = %s, endereco = %s, cidade = %s, estado = %s, cep = %s, ativo = %s
    WHERE id = %s
    ```
- Log de atualização com `dados_antigos` e `dados_novos`.

## RF04.4 — Excluir Escola

- Rota: `POST /escolas/excluir/<id>`
- Permissão: `administrador`.
- Antes de excluir, impede se houver vínculos:
  ```sql
  SELECT COUNT(*) AS total FROM homologacao_fornecedores WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM produtos WHERE escola_id = %s;
  SELECT COUNT(*) AS total FROM pedidos WHERE escola_id = %s;
  ```
- Exclusão e log:
  ```sql
  DELETE FROM escolas WHERE id = %s;
  ```

## Observações e boas práticas
- `escolas.usuario_id` é `UNIQUE` (1:1 com `usuarios`).
- Use `utils.registrar_log` sempre que alterar dados críticos.
- `validar_cnpj` em `utils` é validação simplificada (pode ser trocada por validação completa no futuro).
