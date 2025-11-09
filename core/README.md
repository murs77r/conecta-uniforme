# 📦 Core - Camada de Infraestrutura

## Visão Geral

O diretório `core/` contém a camada de infraestrutura do sistema, implementando padrões de design que promovem reutilização de código, manutenibilidade e testabilidade.

## Arquivos

### 1. `database.py` - Gerenciamento de Banco de Dados

**Classe principal**: `Database`

Gerencia todas as interações com o PostgreSQL de forma centralizada.

```python
from core.database import Database

# Executar query
resultado = Database.executar("SELECT * FROM usuarios", fetchall=True)

# Inserir registro
novo_id = Database.inserir('usuarios', {'nome': 'João', 'email': 'joao@email.com'})

# Atualizar registro
sucesso = Database.atualizar('usuarios', 123, {'nome': 'João Silva'})

# Excluir registro
sucesso = Database.excluir('usuarios', 123)

# Buscar por ID
usuario = Database.buscar_por_id('usuarios', 123)
```

**Métodos**:
- `conectar()`: Cria conexão com banco
- `executar(query, parametros, fetchall, fetchone, commit)`: Executa query SQL
- `inserir(tabela, dados)`: Insere registro e retorna ID
- `atualizar(tabela, id, dados)`: Atualiza registro
- `excluir(tabela, id)`: Exclui registro
- `buscar_por_id(tabela, id)`: Busca registro por ID

### 2. `models.py` - Modelos de Dados

**Dataclasses** que representam entidades do domínio.

```python
from core.models import Usuario, Escola, Produto

# Criar instância
usuario = Usuario(
    nome='João Silva',
    email='joao@email.com',
    tipo='escola',
    ativo=True
)

# Acessar atributos
print(usuario.nome)  # João Silva
print(usuario.tipo)  # escola
```

**Modelos disponíveis**:
- `Usuario`: Usuários do sistema
- `Escola`: Escolas homologadas
- `GestorEscolar`: Gestores de escolas
- `Fornecedor`: Fornecedores cadastrados
- `Produto`: Produtos à venda
- `Pedido`: Pedidos realizados
- `ItemPedido`: Itens de um pedido
- `Responsavel`: Responsáveis por alunos
- `LogAcesso`: Logs de acesso (login/logout)

### 3. `repositories.py` - Padrão Repository

**Padrão de Design**: Repository Pattern

Encapsula acesso a dados e queries complexas.

#### BaseRepository

Classe base com operações CRUD genéricas:

```python
from core.repositories import BaseRepository

class MeuRepository(BaseRepository):
    def __init__(self):
        super().__init__('minha_tabela')

# Usar métodos herdados
repo = MeuRepository()
registro = repo.buscar_por_id(123)
novo_id = repo.inserir({'campo': 'valor'})
sucesso = repo.atualizar(123, {'campo': 'novo valor'})
sucesso = repo.excluir(123)
registros = repo.listar({'campo': 'valor'})
```

#### Repositórios Específicos

**UsuarioRepository**:
```python
from core.repositories import UsuarioRepository

usuario_repo = UsuarioRepository()

# Buscar por email e tipo
usuario = usuario_repo.buscar_por_email_tipo('joao@email.com', 'escola')

# Listar com filtros
usuarios = usuario_repo.listar_com_filtros({
    'tipo': 'escola',
    'busca': 'João'
})
```

**EscolaRepository**:
```python
from core.repositories import EscolaRepository

escola_repo = EscolaRepository()

# Buscar escola com dados do usuário
escola = escola_repo.buscar_com_usuario(123)

# Listar com filtros
escolas = escola_repo.listar_com_filtros({
    'busca': 'Municipal',
    'ativo': 'true'
})

# Buscar por usuario_id
escola = escola_repo.buscar_por_usuario_id(456)
```

**GestorEscolarRepository**:
```python
from core.repositories import GestorEscolarRepository

gestor_repo = GestorEscolarRepository()

# Listar gestores de uma escola
gestores = gestor_repo.listar_por_escola(escola_id)

# Excluir todos gestores de uma escola
gestor_repo.excluir_por_escola(escola_id)
```

**FornecedorRepository**:
```python
from core.repositories import FornecedorRepository

fornecedor_repo = FornecedorRepository()

# Buscar fornecedor com dados do usuário
fornecedor = fornecedor_repo.buscar_com_usuario(123)

# Listar com usuário
fornecedores = fornecedor_repo.listar_com_usuario({
    'busca': 'Uniformes'
})
```

**ProdutoRepository**:
```python
from core.repositories import ProdutoRepository

produto_repo = ProdutoRepository()

# Listar vitrine com filtros
produtos = produto_repo.listar_vitrine({
    'categoria': 'uniforme',
    'escola': 123,
    'busca': 'camisa'
})
```

**PedidoRepository**:
```python
from core.repositories import PedidoRepository

pedido_repo = PedidoRepository()

# Buscar carrinho ativo
carrinho = pedido_repo.buscar_carrinho(responsavel_id)

# Listar pedidos de um responsável
pedidos = pedido_repo.listar_por_responsavel(responsavel_id)
```

### 4. `services.py` - Lógica de Negócio

#### AutenticacaoService

Gerencia autenticação e autorização:

```python
from core.services import AutenticacaoService

auth_service = AutenticacaoService()

# Verificar se usuário está logado
usuario_logado = auth_service.verificar_sessao()
if not usuario_logado:
    # Redirecionar para login

# Verificar permissão específica
usuario_logado = auth_service.verificar_permissao(['administrador', 'escola'])
if not usuario_logado:
    # Acesso negado
```

#### ValidacaoService

Centraliza validações de dados:

```python
from core.services import ValidacaoService

validacao = ValidacaoService()

# Validar email
if not validacao.validar_email('joao@email.com'):
    flash('Email inválido.', 'danger')

# Validar CPF
if not validacao.validar_cpf('123.456.789-00'):
    flash('CPF inválido.', 'danger')

# Validar CNPJ
if not validacao.validar_cnpj('12.345.678/0001-00'):
    flash('CNPJ inválido.', 'danger')

# Validar CEP
if not validacao.validar_cep('12345-678'):
    flash('CEP inválido.', 'danger')

# Validar telefone
if not validacao.validar_telefone('(11) 98765-4321'):
    flash('Telefone inválido.', 'danger')
```

#### LogService

Gerencia logging e auditoria:

```python
from core.services import LogService

# Registrar operação
LogService.registrar(
    usuario_id=123,
    tabela='usuarios',
    registro_id=456,
    acao='UPDATE',
    dados_antigos={'nome': 'João'},
    dados_novos={'nome': 'João Silva'},
    descricao='Atualização de nome de usuário'
)
```

#### CRUDService

Serviço genérico para operações CRUD com logging automático:

```python
from core.services import CRUDService
from core.repositories import EscolaRepository

escola_repo = EscolaRepository()
crud_service = CRUDService(escola_repo, 'Escola')

# Criar com log automático
dados = {'razao_social': 'Escola ABC', 'cnpj': '12.345.678/0001-00'}
novo_id = crud_service.criar_com_log(dados, usuario_logado['id'])
# Flash: "Escola cadastrada com sucesso!"
# Log registrado automaticamente

# Atualizar com log automático
novos_dados = {'razao_social': 'Escola ABC Ltda'}
crud_service.atualizar_com_log(id, novos_dados, dados_antigos, usuario_logado['id'])
# Flash: "Escola atualizada com sucesso!"
# Log registrado automaticamente

# Excluir com log automático
crud_service.excluir_com_log(id, dados_antigos, usuario_logado['id'])
# Flash: "Escola excluída com sucesso!"
# Log registrado automaticamente

# Verificar dependências antes de excluir
bloqueios = crud_service.verificar_dependencias(id, [
    {'tabela': 'produtos', 'campo': 'escola_id', 'mensagem': 'produtos'},
    {'tabela': 'pedidos', 'campo': 'escola_id', 'mensagem': 'pedidos'}
])
if bloqueios:
    flash('Não é possível excluir: ' + ' '.join(bloqueios), 'warning')
```

## Padrões de Uso

### Padrão 1: Controller Simples

```python
from flask import Blueprint, render_template, redirect, url_for
from core.repositories import EscolaRepository
from core.services import AutenticacaoService

escolas_bp = Blueprint('escolas', __name__)
escola_repo = EscolaRepository()
auth_service = AutenticacaoService()

@escolas_bp.route('/listar')
def listar():
    usuario_logado = auth_service.verificar_sessao()
    if not usuario_logado:
        return redirect(url_for('autenticacao.solicitar_codigo'))
    
    escolas = escola_repo.listar({'ativo': True})
    return render_template('escolas/listar.html', escolas=escolas)
```

### Padrão 2: CRUD Completo com Logging

```python
from flask import Blueprint, request, redirect, url_for, flash
from core.repositories import EscolaRepository
from core.services import AutenticacaoService, CRUDService, ValidacaoService

escolas_bp = Blueprint('escolas', __name__)
escola_repo = EscolaRepository()
auth_service = AutenticacaoService()
crud_service = CRUDService(escola_repo, 'Escola')
validacao = ValidacaoService()

@escolas_bp.route('/cadastrar', methods=['POST'])
def cadastrar():
    usuario_logado = auth_service.verificar_permissao(['administrador'])
    if not usuario_logado:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    
    dados = {
        'razao_social': request.form.get('razao_social'),
        'cnpj': request.form.get('cnpj'),
        'ativo': True
    }
    
    if not validacao.validar_cnpj(dados['cnpj']):
        flash('CNPJ inválido.', 'danger')
        return redirect(url_for('escolas.cadastrar'))
    
    novo_id = crud_service.criar_com_log(dados, usuario_logado['id'])
    return redirect(url_for('escolas.listar'))
```

## Vantagens da Arquitetura

### 1. Reutilização de Código
```python
# Mesmos serviços em múltiplos módulos
from core.services import AutenticacaoService, ValidacaoService

# Múltiplos módulos usam os mesmos serviços
auth_service = AutenticacaoService()
validacao = ValidacaoService()
```

### 2. Testabilidade
```python
# Fácil mockar dependências
def test_listar_escolas():
    mock_repo = Mock(EscolaRepository)
    mock_repo.listar.return_value = [...]
    # Testar controller isoladamente
```

### 3. Manutenibilidade
```python
# Mudar validação de CNPJ em um só lugar
class ValidacaoService:
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        # Lógica atualizada afeta todo o sistema
```

### 4. Separação de Responsabilidades

| Camada | Responsabilidade |
|--------|------------------|
| Database | Conexão e queries |
| Models | Estrutura de dados |
| Repositories | Acesso a dados |
| Services | Lógica de negócio |
| Blueprints | Apresentação |

## Boas Práticas

### ✅ Fazer

```python
# Usar repositórios para acesso a dados
escolas = escola_repo.listar_com_filtros(filtros)

# Usar serviços para lógica de negócio
usuario = auth_service.verificar_sessao()

# Usar CRUD service para operações com log
crud_service.criar_com_log(dados, usuario_id)
```

### ❌ Evitar

```python
# NÃO fazer queries diretas nos controllers
Database.executar("SELECT * FROM escolas", fetchall=True)

# NÃO duplicar validações
if '@' not in email:  # Use validacao.validar_email()
    
# NÃO fazer logging manual
registrar_log(...)  # Use CRUDService
```

## Extensibilidade

### Adicionar Novo Repositório

```python
# 1. Criar repositório em repositories.py
class NovoRepository(BaseRepository):
    def __init__(self):
        super().__init__('nova_tabela')
    
    def metodo_especifico(self):
        query = "SELECT ..."
        return Database.executar(query, fetchall=True)

# 2. Usar no módulo
from core.repositories import NovoRepository
novo_repo = NovoRepository()
```

### Adicionar Novo Serviço

```python
# 1. Criar serviço em services.py
class NovoService:
    @staticmethod
    def metodo_util():
        # Lógica reutilizável
        pass

# 2. Usar no módulo
from core.services import NovoService
resultado = NovoService.metodo_util()
```

## Documentação Relacionada

- Ver `REFATORACAO.md` para visão geral da refatoração
- Ver READMEs dos módulos individuais para exemplos de uso
- Ver `modules/escolas.py` para exemplo completo de uso
