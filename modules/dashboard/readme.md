# Módulo de Dashboard

============================================
RF07 - MANTER CADASTRO DE DASHBOARD
============================================
Este módulo é responsável por:
- RF07.1: Criar dashboard
- RF07.2: Apagar dashboard
- RF07.3: Editar dashboard
- RF07.4: Consultar dashboard

Controla o processo de controle de dashboard no sistema.

---

## 📋 Visão Geral

O módulo de **Dashboard** fornece uma visão consolidada e personalizada dos dados do sistema Conecta Uniforme, adaptada ao tipo de usuário logado.

### Propósito
- Exibir indicadores e métricas relevantes por perfil de usuário
- Fornecer acesso rápido às funcionalidades principais
- Apresentar resumos estatísticos do sistema
- Facilitar a navegação e tomada de decisão

---

## 🏗️ Arquitetura

### Padrões Utilizados
- **Dashboard Pattern**: Diferentes visualizações por tipo de usuário
- **Service Layer**: `AutenticacaoService` para controle de acesso
- **Blueprint Pattern**: Modularização Flask

### Estrutura de Dados
```
Usuario (tipo)
    ↓
Dashboard Personalizado
    - Administrador: Métricas gerais do sistema
    - Fornecedor: Vendas e produtos
    - Escola: Pedidos e homologações
    - Responsável: Histórico de compras
```

---

## 🔌 Endpoints (Rotas)

### 1. `GET /dashboard`
**Descrição**: Exibe dashboard personalizado conforme tipo de usuário

**Autenticação**: Requerida (Todos os tipos)

**Resposta para Administrador**:
```html
Status: 200 OK
Template: templates/dashboard/index.html
Contexto: {
    'total_usuarios': int,
    'total_escolas': int,
    'total_fornecedores': int,
    'total_produtos': int,
    'total_pedidos': int,
    'pedidos_pendentes': int,
    'pedidos_hoje': int,
    'faturamento_mes': Decimal
}
```

**Resposta para Fornecedor**:
```html
Status: 200 OK
Template: templates/dashboard/index.html
Contexto: {
    'total_produtos': int,
    'produtos_estoque_baixo': int,
    'total_vendas_mes': int,
    'faturamento_mes': Decimal,
    'pedidos_recentes': List[Pedido]
}
```

**Resposta para Escola**:
```html
Status: 200 OK
Template: templates/dashboard/index.html
Contexto: {
    'total_alunos': int,
    'fornecedores_homologados': int,
    'pedidos_mes': int,
    'pedidos_recentes': List[Pedido]
}
```

**Resposta para Responsável**:
```html
Status: 200 OK
Template: templates/dashboard/index.html
Contexto: {
    'pedidos_abertos': int,
    'ultimo_pedido': Pedido,
    'historico_pedidos': List[Pedido],
    'total_gasto': Decimal
}
```

---

## 📊 Modelos de Dados

O módulo Dashboard não possui modelos próprios, apenas agrega dados de outros módulos.

---

## 🔐 Autenticação e Autorização

### Matriz de Permissões

| Rota | Administrador | Fornecedor | Escola | Responsável |
|------|---------------|------------|--------|-------------|
| `/dashboard` | ✅ | ✅ | ✅ | ✅ |

**Nota**: O conteúdo exibido varia conforme o tipo de usuário.

---

## 📝 Regras de Negócio

### 1. Personalização por Perfil
- Cada tipo de usuário vê métricas relevantes ao seu contexto
- Dados sensíveis são filtrados por permissão

### 2. Métricas em Tempo Real
- Indicadores atualizados a cada acesso
- Cache opcional para melhor performance

### 3. Acesso Rápido
- Links diretos para funcionalidades principais
- Atalhos contextuais por perfil

---

## 💡 Exemplos de Uso

### Dashboard do Administrador
```python
# Consultas para métricas gerais
total_usuarios = Database.executar(
    "SELECT COUNT(*) as total FROM usuarios WHERE ativo = TRUE",
    fetchone=True
)['total']

total_pedidos = Database.executar(
    "SELECT COUNT(*) as total FROM pedidos WHERE status != 'carrinho'",
    fetchone=True
)['total']

faturamento = Database.executar(
    """SELECT COALESCE(SUM(valor_total), 0) as total 
       FROM pedidos 
       WHERE status = 'pago' 
       AND EXTRACT(MONTH FROM data_pedido) = EXTRACT(MONTH FROM CURRENT_DATE)""",
    fetchone=True
)['total']
```

### Dashboard do Fornecedor
```python
# Produtos com estoque baixo
produtos_estoque_baixo = Database.executar(
    """SELECT COUNT(*) as total 
       FROM produtos 
       WHERE fornecedor_id = %s AND estoque < 10 AND ativo = TRUE""",
    (fornecedor_id,),
    fetchone=True
)['total']
```

---

## 📈 Métricas

### Performance
- Tempo de carregamento: < 200ms (com cache)
- Consultas otimizadas: Máximo 5 queries por dashboard

### Manutenibilidade
- Dashboard modular e extensível
- Fácil adição de novos indicadores

---

**Versão**: 1.0  
**Última Atualização**: 09/11/2025  
**Status**: ✅ Documentado
