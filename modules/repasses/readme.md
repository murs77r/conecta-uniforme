# Módulo de Repasses Financeiros

## 📋 Visão Geral

O módulo de **Repasses Financeiros** gerencia a distribuição de valores recebidos de pedidos pagos para os fornecedores, aplicando a taxa da plataforma e controlando o fluxo de pagamentos. É essencial para a sustentabilidade financeira do ecossistema Conecta Uniforme.

### Propósito
- Gerar repasses automaticamente a partir de pedidos pagos
- Calcular taxa da plataforma e valor líquido
- Controlar status de repasses (pendente, processado, cancelado)
- Fornecer transparência financeira para fornecedores

---

## 🏗️ Arquitetura

### Padrões Utilizados
- **Repository Pattern**: `RepasseFinanceiroRepository`, `FornecedorRepository`
- **Service Layer**: `AutenticacaoService`, `LogService`
- **Transaction Script**: Cálculos financeiros precisos
- **Observer Pattern**: Geração automática após mudança de status do pedido

### Fluxo de Repasse
```
1. Pedido muda status para 'pago'
2. Sistema calcula valor por fornecedor
3. Aplica taxa da plataforma (%)
4. Cria repasse com status 'pendente'
5. Admin processa repasse → 'processado'
6. Fornecedor visualiza histórico
```

---

## 🔌 Endpoints (Rotas)

### 1. `GET /repasses/listar`
**Descrição**: Lista repasses financeiros com filtro por usuário

**Autenticação**: Requerida (Administrador ou Fornecedor)

**Lógica de Acesso**:
- **Fornecedor**: Vê apenas seus próprios repasses
- **Administrador**: Vê todos os repasses do sistema

**Resposta**:
```html
Status: 200 OK
Template: templates/repasses/listar.html
Contexto: {
    'repasses': [{
        'id': int,
        'fornecedor_id': int,
        'fornecedor_nome': str,
        'pedido_id': int,
        'valor': Decimal,
        'taxa_plataforma': Decimal,
        'valor_liquido': Decimal,
        'status': str,  # pendente, processado, cancelado
        'data_geracao': datetime,
        'data_processamento': datetime (opcional)
    }, ...],
    'total_pendente': Decimal,
    'total_processado': Decimal
}
```

**SQL para Fornecedor**:
```sql
SELECT 
    r.id, r.pedido_id, r.valor, r.taxa_plataforma, 
    r.valor_liquido, r.status, r.data_geracao, r.data_processamento,
    f.nome_fantasia as fornecedor_nome,
    u.nome as fornecedor_responsavel
FROM repasses_financeiros r
JOIN fornecedores f ON r.fornecedor_id = f.id
JOIN usuarios u ON f.usuario_id = u.id
WHERE r.fornecedor_id = {fornecedor_id}
ORDER BY r.data_geracao DESC
```

**Totalizadores**:
```python
total_pendente = sum(r['valor_liquido'] for r in repasses if r['status'] == 'pendente')
total_processado = sum(r['valor_liquido'] for r in repasses if r['status'] == 'processado')
```

---

### 2. `POST /repasses/gerar/<int:pedido_id>`
**Descrição**: Gera repasses automaticamente para pedido pago

**Autenticação**: Requerida (Administrador)

**Parâmetros de Rota**:
- `pedido_id`: ID do pedido que teve pagamento confirmado

**Pré-Requisitos**:
1. Pedido deve existir
2. Status do pedido deve ser `'pago'`
3. Não podem existir repasses já gerados para este pedido

**Lógica de Geração**:
```python
# 1. Busca pedido
pedido = Database.executar("""
    SELECT * FROM pedidos 
    WHERE id = %s AND status = 'pago'
""", (pedido_id,), fetchone=True)

if not pedido:
    flash('Pedido não encontrado ou não pago', 'danger')
    return redirect(url_for('pedidos.listar'))

# 2. Agrupa itens por fornecedor
query_itens = """
    SELECT 
        p.fornecedor_id, 
        SUM(i.subtotal) as valor_total
    FROM itens_pedido i
    JOIN produtos p ON i.produto_id = p.id
    WHERE i.pedido_id = %s
    GROUP BY p.fornecedor_id
"""
itens_por_fornecedor = Database.executar(query_itens, (pedido_id,), fetchall=True)

# 3. Cria repasse para cada fornecedor
for item in itens_por_fornecedor:
    valor = float(item['valor_total'])
    taxa = valor * (TAXA_PLATAFORMA_PERCENTUAL / 100)
    valor_liquido = valor - taxa
    
    dados_repasse = {
        'fornecedor_id': item['fornecedor_id'],
        'pedido_id': pedido_id,
        'valor': valor,
        'taxa_plataforma': taxa,
        'valor_liquido': valor_liquido,
        'status': 'pendente',
        'data_geracao': datetime.now()
    }
    
    repasse_id = repasse_repo.inserir(dados_repasse)
    
    # Log
    LogService.registrar(
        usuario_id=session['usuario_id'],
        tabela='repasses_financeiros',
        registro_id=repasse_id,
        operacao='INSERT',
        dados_novos=dados_repasse,
        descricao='Repasse gerado automaticamente'
    )
```

**Exemplo de Cálculo**:
```
Pedido #123: R$ 500,00
  - Fornecedor A: R$ 300,00
  - Fornecedor B: R$ 200,00

Taxa da plataforma: 10%

Repasse Fornecedor A:
  Valor bruto: R$ 300,00
  Taxa: R$ 30,00 (10%)
  Valor líquido: R$ 270,00

Repasse Fornecedor B:
  Valor bruto: R$ 200,00
  Taxa: R$ 20,00 (10%)
  Valor líquido: R$ 180,00

Total retido pela plataforma: R$ 50,00
Total repassado aos fornecedores: R$ 450,00
```

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /repasses/listar
Flash: "Repasses gerados com sucesso!"
Log: INSERT em repasses_financeiros (múltiplos)
```

**Resposta de Erro (Pedido Não Pago)**:
```json
Status: 302 Redirect
Location: /pedidos/listar
Flash: "Pedido não encontrado ou não pago"
```

---

### 3. `POST /repasses/processar/<int:repasse_id>`
**Descrição**: Marca repasse como processado (pagamento efetuado)

**Autenticação**: Requerida (Administrador)

**Comportamento**:
```python
# 1. Busca repasse
repasse = repasse_repo.buscar_por_id(repasse_id)

if not repasse or repasse['status'] != 'pendente':
    flash('Repasse não encontrado ou já processado', 'warning')
    return redirect(url_for('repasses.listar'))

# 2. Atualiza status
dados_atualizacao = {
    'status': 'processado',
    'data_processamento': datetime.now()
}
repasse_repo.atualizar(repasse_id, dados_atualizacao)

# 3. Log
LogService.registrar(
    usuario_id=session['usuario_id'],
    tabela='repasses_financeiros',
    registro_id=repasse_id,
    operacao='UPDATE',
    dados_antigos={'status': 'pendente'},
    dados_novos={'status': 'processado'},
    descricao='Repasse processado manualmente'
)

flash('Repasse processado com sucesso!', 'success')
```

**Validações**:
- Repasse deve existir
- Status deve ser `'pendente'`
- Apenas administrador pode processar

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /repasses/listar
Flash: "Repasse processado com sucesso!"
Log: UPDATE em repasses_financeiros
```

---

### 4. `POST /repasses/cancelar/<int:repasse_id>`
**Descrição**: Cancela repasse pendente

**Autenticação**: Requerida (Administrador)

**Comportamento**:
```python
# Atualiza status
dados_cancelamento = {
    'status': 'cancelado',
    'data_processamento': datetime.now()
}
repasse_repo.atualizar(repasse_id, dados_cancelamento)

# Log
LogService.registrar(
    usuario_id=session['usuario_id'],
    tabela='repasses_financeiros',
    registro_id=repasse_id,
    operacao='UPDATE',
    dados_novos={'status': 'cancelado'},
    descricao='Repasse cancelado'
)
```

**Casos de Uso para Cancelamento**:
1. Pedido foi estornado
2. Fornecedor solicitou suspensão temporária
3. Erro no valor calculado (será regerado)
4. Problema com dados bancários do fornecedor

**Resposta de Sucesso**:
```json
Status: 302 Redirect
Location: /repasses/listar
Flash: "Repasse cancelado"
Log: UPDATE em repasses_financeiros
```

---

## 📊 Modelos de Dados

### RepasseFinanceiro (Dataclass)
```python
@dataclass
class RepasseFinanceiro:
    """Representa um repasse financeiro a fornecedor"""
    id: Optional[int] = None
    fornecedor_id: int = 0
    pedido_id: int = 0
    valor: Decimal = Decimal('0.00')
    taxa_plataforma: Decimal = Decimal('0.00')
    valor_liquido: Decimal = Decimal('0.00')
    status: str = 'pendente'  # pendente, processado, cancelado
    data_geracao: Optional[datetime] = None
    data_processamento: Optional[datetime] = None
```

### Tabela `repasses_financeiros` (PostgreSQL)
```sql
CREATE TABLE repasses_financeiros (
    id SERIAL PRIMARY KEY,
    fornecedor_id INT NOT NULL REFERENCES fornecedores(id),
    pedido_id INT NOT NULL REFERENCES pedidos(id),
    valor DECIMAL(10,2) NOT NULL CHECK (valor >= 0),
    taxa_plataforma DECIMAL(10,2) NOT NULL CHECK (taxa_plataforma >= 0),
    valor_liquido DECIMAL(10,2) NOT NULL CHECK (valor_liquido >= 0),
    status VARCHAR(20) DEFAULT 'pendente' 
        CHECK (status IN ('pendente', 'processado', 'cancelado')),
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP
);

CREATE INDEX idx_repasses_fornecedor ON repasses_financeiros(fornecedor_id);
CREATE INDEX idx_repasses_pedido ON repasses_financeiros(pedido_id);
CREATE INDEX idx_repasses_status ON repasses_financeiros(status);
CREATE INDEX idx_repasses_data ON repasses_financeiros(data_geracao);
```

### Constraints de Integridade
```sql
-- Garante que valor líquido = valor - taxa
ALTER TABLE repasses_financeiros ADD CONSTRAINT chk_valor_liquido
CHECK (valor_liquido = valor - taxa_plataforma);

-- Garante que não existam repasses duplicados para mesmo pedido/fornecedor
CREATE UNIQUE INDEX idx_repasse_unico 
ON repasses_financeiros(pedido_id, fornecedor_id) 
WHERE status != 'cancelado';
```

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Fornecedor | Escola | Responsável |
|------|---------------|------------|--------|-------------|
| `/repasses/listar` | ✅ (todos) | ✅ (próprios) | ❌ | ❌ |
| `/repasses/gerar/:pedido_id` | ✅ | ❌ | ❌ | ❌ |
| `/repasses/processar/:id` | ✅ | ❌ | ❌ | ❌ |
| `/repasses/cancelar/:id` | ✅ | ❌ | ❌ | ❌ |

### Verificação de Propriedade (Fornecedor)
```python
def verificar_acesso_repasse(repasse_id: int) -> bool:
    """Verifica se fornecedor logado pode acessar repasse"""
    tipo_usuario = session.get('tipo_usuario')
    
    if tipo_usuario == 'Administrador':
        return True
    
    if tipo_usuario == 'Fornecedor':
        fornecedor = FornecedorRepository().buscar_por_usuario_id(
            session['usuario_id']
        )
        repasse = RepasseFinanceiroRepository().buscar_por_id(repasse_id)
        return repasse['fornecedor_id'] == fornecedor['id']
    
    return False
```

---

## 📝 Regras de Negócio

### 1. Cálculo de Taxa da Plataforma
- Taxa configurável em `config.py`: `TAXA_PLATAFORMA_PERCENTUAL`
- Padrão: **10%** sobre o valor bruto
- Fórmula:
  ```python
  taxa = valor_bruto * (TAXA_PLATAFORMA_PERCENTUAL / 100)
  valor_liquido = valor_bruto - taxa
  ```

### 2. Geração Automática
- Repasses são gerados quando pedido muda para `status='pago'`
- Um repasse é criado para cada fornecedor que tenha produtos no pedido
- Valores são agrupados por fornecedor
- Data de geração é timestamp atual

### 3. Processamento Manual
- Apenas Administradores podem processar repasses
- Status passa de `'pendente'` → `'processado'`
- `data_processamento` é registrada
- Operação é irreversível (não pode voltar para pendente)

### 4. Cancelamento
- Repasses cancelados não contam em totalizadores
- Podem ser regerados se necessário
- Mantém histórico para auditoria

### 5. Integridade Financeira
- Valores sempre com 2 casas decimais (DECIMAL(10,2))
- Soma dos repasses = valor total do pedido - taxa total
- Validação: `valor_liquido = valor - taxa_plataforma`