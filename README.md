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
- Login com Passkey (WebAuthn) – use Windows Hello, Face/Touch ID ou chave de segurança

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

- **Python**
- **Flask** - Framework web
- **PostgreSQL** - Banco de dados
- **Bootstrap 5** - Interface responsiva
- **SMTP** - Envio de emails
- **WebAuthn/Passkeys** – Autenticação sem senha

## 🔐 Passkeys (WebAuthn)

Agora você pode entrar usando Passkeys (chaves de segurança) em navegadores compatíveis:

- Cadastro de Passkey: após fazer login normalmente, acesse a página “Cadastrar/gerenciar Passkey” (link na Home) ou vá para /auth/passkeys e clique em “Cadastrar Passkey”.
- Login com Passkey: na tela de login, digite seu email e clique em “Entrar com Passkey”.

### Configuração necessária

No arquivo `.env`, configure os parâmetros (especialmente em produção):

```
WEBAUTHN_RP_ID=seu-dominio.com
WEBAUTHN_ORIGIN=https://seu-dominio.com
WEBAUTHN_RP_NAME=Conecta Uniforme
```

Para desenvolvimento local, os padrões já funcionam com `localhost`:

```
WEBAUTHN_RP_ID=localhost
WEBAUTHN_ORIGIN=http://localhost:5000
```

Certifique-se de instalar as dependências:

```
pip install -r requirements.txt
```

E aplicar as alterações de banco (nova tabela `webauthn_credentials`) com o `schema.sql`.

## 📄 Licença

Projeto desenvolvido para fins educacionais da *Faculdade de Tecnologia e Inovação SENAC-DF*

## 👥 Autores

Desenvolvido por João Paulo Freitas, João Paulo Nunes, Murilo Souza, Victor de Castro, Yuri Henrique.

---

**Conecta Uniforme** - Simplificando a compra de uniformes escolares! 🎒👕
