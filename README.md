# CONECTA UNIFORME

Sistema de gerenciamento de uniformes escolares desenvolvido em Python/Flask com PostgreSQL.

## 📋 Descrição

O **Conecta Uniforme** é uma plataforma de e-commerce (marketplace) que conecta digitalmente:
- **Instituições de Ensino** - Gerenciam fornecedores homologados
- **Fornecedores de Uniformes** - Cadastram e vendem produtos
- **Pais/Responsáveis** - Compram uniformes escolares

## 🎯 Funcionalidades

### RF01 - Manter Cadastro de Usuário
- Cadastrar, consultar, editar e excluir usuários
- Log de alterações para auditoria

### RF02 - Gerenciar Autenticação e Acesso
- Sistema de login por código de acesso enviado via email
- Código válido por 24 horas
- Sessões seguras

### RF03 - Gerenciar Produtos e Vitrine
- Cadastro de produtos (uniformes)
- Vitrine com filtros automáticos
- Controle de estoque

### RF04 - Gerenciar Escolas
- CRUD completo de escolas
- Gestão de fornecedores homologados

### RF05 - Gerenciar Fornecedores
- CRUD completo de fornecedores
- Vinculação com escolas

### RF06 - Gerenciar Pedidos
- Carrinho de compras
- Finalização de pedidos
- Histórico de compras

### RF07 - Gerenciar Repasses Financeiros
- Controle de repasses para fornecedores
- Cálculo automático de taxas

## 🚀 Tecnologias

- **Python 3.8+**
- **Flask** - Framework web
- **PostgreSQL** - Banco de dados
- **Bootstrap 5** - Interface responsiva
- **SMTP** - Envio de emails

## 📦 Instalação

### 1. Pré-requisitos

- Python 3.8 ou superior
- PostgreSQL 12 ou superior
- Conta de email com SMTP (Gmail, etc.)

### 2. Clone/Download do Projeto

```bash
cd conecta_uniforme
```

### 3. Crie um Ambiente Virtual

```bash
python -m venv venv
```

### 4. Ative o Ambiente Virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 5. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 6. Configure o Banco de Dados

Edite o arquivo `config.py` e configure suas credenciais do PostgreSQL:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'conecta_uniforme',
    'user': 'seu_usuario',
    'password': 'sua_senha'
}
```

### 7. Execute o Script SQL

No PostgreSQL, execute o arquivo `schema.sql`:

```bash
psql -U postgres -d postgres -f schema.sql
```

Ou crie o banco manualmente e execute o script dentro dele.

### 8. Configure o SMTP

Edite o arquivo `config.py` e configure o servidor SMTP:

```python
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'use_tls': True,
    'username': 'seu-email@gmail.com',
    'password': 'sua-senha-de-app',  # Use senha de app do Gmail
    'from_email': 'seu-email@gmail.com',
    'from_name': 'Conecta Uniforme'
}
```

**Importante para Gmail:**
- Acesse: https://myaccount.google.com/apppasswords
- Gere uma "Senha de App"
- Use essa senha no config.py

### 9. Inicie a Aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 👤 Usuário Padrão

Após executar o `schema.sql`, um usuário administrador é criado:

- **Email:** admin@conectauniforme.com.br
- **Tipo:** Administrador

Para fazer login:
1. Acesse `http://localhost:5000`
2. Digite o email do administrador
3. Verifique o código no email
4. Digite o código para entrar

## 📁 Estrutura do Projeto

```
conecta_uniforme/
├── app.py                 # Aplicação principal Flask
├── config.py              # Configurações do sistema
├── utils.py               # Funções utilitárias
├── schema.sql             # Script de criação do banco
├── requirements.txt       # Dependências Python
├── modules/               # Módulos (microfront-ends)
│   ├── autenticacao.py    # RF02 - Autenticação
│   ├── usuarios.py        # RF01 - Usuários
│   ├── escolas.py         # RF04 - Escolas
│   ├── fornecedores.py    # RF05 - Fornecedores
│   ├── produtos.py        # RF03 - Produtos
│   ├── pedidos.py         # RF06 - Pedidos
│   └── repasses.py        # RF07 - Repasses
├── templates/             # Templates HTML
│   ├── base.html          # Template base
│   ├── home.html          # Página inicial
│   ├── auth/              # Templates de autenticação
│   ├── usuarios/          # Templates de usuários
│   ├── escolas/           # Templates de escolas
│   ├── fornecedores/      # Templates de fornecedores
│   ├── produtos/          # Templates de produtos
│   ├── pedidos/           # Templates de pedidos
│   └── repasses/          # Templates de repasses
└── static/                # Arquivos estáticos
```

## 🏗️ Arquitetura

O sistema foi desenvolvido em **arquitetura de microfront-ends**, onde:

- Cada requisito funcional é um módulo independente (Blueprint do Flask)
- Os módulos compartilham apenas o banco de dados PostgreSQL
- Cada módulo pode ser desenvolvido e testado separadamente
- Facilita manutenção e escalabilidade

## 🔒 Segurança

- Autenticação por código temporário (24h de validade)
- Sessões seguras com tokens únicos
- Validação de permissões por tipo de usuário
- Log completo de alterações para auditoria

## 📝 Tipos de Usuário

1. **Administrador**: Acesso completo ao sistema
2. **Escola**: Gerencia fornecedores homologados
3. **Fornecedor**: Cadastra produtos e visualiza repasses
4. **Responsável**: Compra uniformes na vitrine

## 💡 Dicas de Uso

- Sempre inicie criando usuários através do painel administrativo
- Configure corretamente o SMTP para o sistema de autenticação funcionar
- Faça backups regulares do banco de dados
- Monitore os logs de alteração para auditoria

## 🐛 Resolução de Problemas

### Erro ao conectar ao banco de dados
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais em `config.py`
- Verifique se o banco `conecta_uniforme` foi criado

### Email não está sendo enviado
- Verifique as configurações SMTP em `config.py`
- Para Gmail, use senha de app (não a senha normal)
- Verifique se a porta 587 está liberada no firewall

### Erro 500 ao acessar páginas
- Verifique os logs no terminal
- Confirme se todas as dependências foram instaladas
- Verifique se o schema.sql foi executado corretamente

## 📄 Licença

Projeto desenvolvido para fins educacionais.

## 👥 Autores

Desenvolvido como trabalho acadêmico.

## 📞 Suporte

Em caso de dúvidas, consulte:
- A documentação inline no código (comentários extensivos)
- Os requisitos funcionais no início deste documento
- O professor Edilberto

---

**Conecta Uniforme** - Simplificando a compra de uniformes escolares! 🎒👕
