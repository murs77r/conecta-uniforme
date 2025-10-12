# Conecta Uniforme

Sistema completo de e-commerce para venda de uniformes escolares com foco em gestão de múltiplos perfis de usuários, catálogo personalizado e comissionamento.

## 📋 Índice

- [Sobre o Sistema](#sobre-o-sistema)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
- [Fluxo Operacional](#fluxo-operacional)
- [Perfis de Usuário](#perfis-de-usuário)
- [Integração Mailersend](#integração-mailersend)

## 🎯 Sobre o Sistema

O **Conecta Uniforme** é uma plataforma que conecta escolas, fornecedores de uniformes e responsáveis (pais/alunos), facilitando o processo de compra de uniformes escolares através de um sistema de "clique e retire". 

### Principais Diferenciais

- **Login sem senha**: Autenticação via código temporário enviado por e-mail
- **Catálogo personalizado**: Cada responsável vê apenas os uniformes da série e gênero do seu aluno
- **Homologação de fornecedores**: Escolas controlam quais fornecedores podem vender para seus alunos
- **Comissionamento automático**: 15% de comissão calculada automaticamente em cada venda
- **Gestão de estoque**: Controle de variações (tamanho, cor, gênero) por produto

## ✨ Funcionalidades

### Login e Autenticação
- Login via e-mail com código de acesso temporário (10 minutos de validade)
- Integração com API Mailersend para envio de códigos
- Possibilidade de solicitar novo código

### Gestão de Usuários
- **Gestor Escolar**: Cadastrado pela equipe administrativa
- **Fornecedor**: Cadastrado pela equipe administrativa
- **Responsável**: Auto-cadastro simplificado com validação via lista escolar

### Gestão de Produtos (Fornecedor)
- Cadastro de uniformes com fotos, descrição e preço
- Definição de variações (tamanho, cor, gênero)
- Homologação para escolas e séries específicas
- Controle de estoque por variação
- Ativação/desativação temporária de produtos

### Gestão Escolar
- Importação de lista de alunos (individual ou CSV)
- Habilitação/desabilitação de fornecedores
- Visualização de pedidos da escola
- Gerenciamento de ponto de coleta

### Catálogo e Compras (Responsável)
- Visualização automática de produtos da série e gênero do aluno
- Detalhamento de produtos com fotos e descrição
- Carrinho de compras com atualização de quantidades
- Finalização com retirada na escola (clique e retire)
- Acompanhamento de status dos pedidos

### Gestão de Pedidos
- Atualização de status pelo fornecedor:
  - Pendente → Aprovado → Em Produção → Pronto para Retirada → Entregue
- Visualização por perfil (responsável, fornecedor, gestor)
- Detalhamento completo de itens do pedido

### Relatórios e Comissões
- Cálculo automático de 15% de comissão por venda
- Geração de relatórios mensais por fornecedor
- Detalhamento de vendas do período
- Registro de pagamentos pela administração

## 🔧 Requisitos

- PHP 7.4 ou superior
- MySQL 5.7 ou superior
- Servidor web (Apache/Nginx)
- Extensões PHP:
  - mysqli
  - curl (para integração Mailersend)
  - json

## 📦 Instalação

### 1. Clone ou baixe o repositório

```bash
cd /caminho/do/servidor/web
# Extrair arquivos do projeto
```

### 2. Criar o banco de dados

Execute o arquivo `bd.sql` no MySQL:

```bash
mysql -u root -p < bd.sql
```

Ou pelo phpMyAdmin:
- Acesse o phpMyAdmin
- Crie um banco chamado `conecta_uniformes`
- Importe o arquivo `bd.sql`

### 3. Configurar conexão com banco de dados

Edite o arquivo `conexao.php`:

```php
<?php
try {
    if ($con = new mysqli("localhost", "seu_usuario", "sua_senha", "conecta_uniformes")) {
        // Conexão estabelecida
    } else {
        throw new Exception();
    }
}
catch(Exception $e) {
    $con = new mysqli("localhost", "seu_usuario", "sua_senha", "conecta_uniformes");
}
```

### 4. Configurar o arquivo .htaccess

Renomeie `htaccess.txt` para `.htaccess` e ajuste se necessário.

### 2. Configuração do Ambiente (.env)

### Configuração do Mailersend

#### 1. Criar conta no Mailersend

Acesse [Mailersend](https://www.mailersend.com/) e crie uma conta gratuita.

#### 2. Obter API Key

- No painel do Mailersend, vá em **API Tokens**
- Clique em **Generate new token**
- Dê um nome descritivo (ex: "Conecta Uniforme")
- Copie a API Key gerada

#### 3. Configurar no sistema

Edite o arquivo `classes/CodigoAcesso.php` na linha 12:

```php
$this->mailersendApiKey = 'sua_api_key_aqui';
```

**Recomendação**: Para ambientes de produção, use variáveis de ambiente:

No seu servidor, defina a variável:
```bash
export MAILERSEND_API_KEY="mlsn.sua_chave_aqui"
```

O código já está preparado para ler a variável de ambiente:
```php
$this->mailersendApiKey = getenv('MAILERSEND_API_KEY') ?: 'sua_chave_api_aqui';
```

#### 4. Verificar domínio de envio

No painel do Mailersend:
- Adicione e verifique seu domínio de envio
- Atualize o e-mail remetente em `classes/CodigoAcesso.php` (linha 89):

```php
'from' => [
    'email' => 'noreply@seudominio.com.br',
    'name' => 'Conecta Uniforme'
],
```

## 8. Primeiros Passos

### Principais Tabelas

- **escola**: Dados das instituições de ensino
- **gestor**: Gestores escolares vinculados às escolas
- **fornecedor**: Fornecedores de uniformes
- **homologacao**: Vínculo entre escolas e fornecedores autorizados
- **aluno**: Alunos cadastrados por escola
- **responsavel**: Responsáveis vinculados aos alunos
- **codigo_acesso**: Códigos temporários para login
- **produto**: Uniformes cadastrados pelos fornecedores
- **produto_foto**: Fotos dos produtos
- **produto_homologacao**: Produtos homologados por escola/série
- **produto_variacao**: Variações de produtos (tamanho, cor, gênero)
- **carrinho**: Carrinho temporário dos responsáveis
- **pedido**: Pedidos finalizados
- **pedido_item**: Itens de cada pedido
- **comissao**: Relatórios mensais de comissão por fornecedor
- **auditoria**: Log automático de alterações

## 📊 Fluxo Operacional

### 1. Configuração Inicial (Administração)

1. Cadastrar escolas no banco de dados
2. Cadastrar gestores escolares vinculados às escolas
3. Cadastrar fornecedores no sistema

### 2. Gestão Escolar

1. Gestor faz login com e-mail cadastrado
2. Recebe código por e-mail e valida
3. Importa lista de alunos (CSV ou individual)
4. Habilita fornecedores para vender na escola
5. Monitora pedidos e ponto de coleta

### 3. Gestão do Fornecedor

1. Fornecedor faz login com e-mail cadastrado
2. Recebe código por e-mail e valida
3. Cadastra produtos com fotos e descrição
4. Define variações (tamanhos, cores, gêneros)
5. Homologa produtos para escolas/séries
6. Atualiza estoque conforme necessário
7. Recebe pedidos e atualiza status
8. Visualiza relatórios financeiros

### 4. Compra pelo Responsável

1. Responsável se cadastra informando dados básicos e vínculo com aluno
2. Faz login digitando e-mail
3. Recebe código por e-mail e valida
4. Acessa catálogo personalizado (apenas produtos da série e gênero do aluno)
5. Adiciona produtos ao carrinho
6. Finaliza pedido (retirada na escola)
7. Acompanha status do pedido

### 5. Comissionamento

1. Sistema calcula automaticamente 15% de comissão em cada venda
2. No final do mês, administrador gera relatório de comissões
3. Visualiza total de vendas, comissão e valor líquido por fornecedor
4. Registra data e valor do pagamento realizado

## 👥 Perfis de Usuário

### Gestor Escolar

**Acesso**: `/conecta-uniforme/login-novo` (tipo: gestor)

**Funcionalidades**:
- Gerenciar lista de alunos
- Habilitar/desabilitar fornecedores
- Visualizar pedidos da escola
- Monitorar ponto de retirada

**Rotas**:
- Dashboard: `/dashboard-gestor`
- Alunos: `/alunos-gestor`
- Pedidos: `/pedidos-gerenciar`

### Fornecedor

**Acesso**: `/conecta-uniforme/login-novo` (tipo: fornecedor)

**Funcionalidades**:
- Cadastrar e gerenciar produtos
- Definir variações e estoque
- Homologar produtos para escolas
- Atualizar status de pedidos
- Visualizar relatórios financeiros

**Rotas**:
- Dashboard: `/dashboard-fornecedor`
- Produtos: `/produtos-fornecedor`
- Pedidos: `/pedidos-gerenciar`
- Comissões: `/comissoes-relatorio`

### Responsável (Pai/Mãe)

**Acesso**: `/conecta-uniforme/login-novo` (tipo: responsavel)

**Funcionalidades**:
- Visualizar catálogo personalizado
- Adicionar produtos ao carrinho
- Finalizar pedidos
- Acompanhar status de pedidos

**Rotas**:
- Dashboard: `/dashboard-responsavel`
- Catálogo: `/catalogo-novo`
- Carrinho: `/carrinho-novo`
- Meus Pedidos: `/pedidos-gerenciar`

## 🔐 Integração Mailersend

### Funcionamento do Sistema de Login

1. Usuário digita e-mail e seleciona tipo (gestor/fornecedor/responsável)
2. Sistema verifica se e-mail existe e está ativo
3. Gera código alfanumérico de 6 caracteres
4. Envia código via API do Mailersend
5. Código expira em 10 minutos
6. Usuário digita código recebido
7. Sistema valida e cria sessão

### Código de Exemplo

```php
// Gerar código
$codigo = $codigoAcesso->criarCodigo($email, $tipo_usuario);

// Enviar por email
$enviado = $codigoAcesso->enviarCodigoPorEmail($email, $codigo['codigo'], $nome);

// Validar código
$validacao = $codigoAcesso->validarCodigo($email, $codigo_digitado);
```

### Troubleshooting Mailersend

**Erro: Email não enviado**
- Verifique se a API Key está correta
- Confirme se o domínio está verificado no Mailersend
- Verifique limites da conta (plano gratuito tem limite de envios)

**Erro: Email na caixa de spam**
- Configure SPF, DKIM e DMARC no seu domínio
- Use um domínio verificado e com boa reputação

## 🚀 Primeiros Passos

### 1. Inserir dados iniciais

```sql
-- Inserir escola
INSERT INTO escola (email, nome, cnpj, telefone, ativo) 
VALUES ('escola@exemplo.com', 'Escola Exemplo', '12345678000190', '(11) 1234-5678', 1);

-- Inserir gestor
INSERT INTO gestor (nome, email, telefone, escola_id, ativo) 
VALUES ('João Silva', 'gestor@exemplo.com', '(11) 9 1234-5678', 1, 1);

-- Inserir fornecedor
INSERT INTO fornecedor (nome, email, telefone, cnpj, ativo) 
VALUES ('Uniformes XYZ', 'fornecedor@xyz.com', '(11) 9 8765-4321', '98765432000190', 1);
```

### 2. Habilitar fornecedor para escola

```sql
-- Criar homologação
INSERT INTO homologacao (escola_id, fornecedor_id, ativo) 
VALUES (1, 1, 1);
```

### 3. Importar alunos

Crie um arquivo CSV com formato:
```
nome,matricula,serie,genero,responsavel_nome,responsavel_email,responsavel_telefone
Maria Silva,2024001,5º Ano,feminino,Ana Silva,ana@email.com,(11) 91234-5678
João Santos,2024002,5º Ano,masculino,Carlos Santos,carlos@email.com,(11) 98765-4321
```

Faça upload via interface do gestor em `/alunos-gestor`.

### 4. Fazer primeiro login

1. Acesse `/conecta-uniforme/login-novo`
2. Digite o e-mail do gestor/fornecedor
3. Receba o código por e-mail
4. Digite o código e acesse o sistema

## 📝 Notas Importantes

- **Sem estilo CSS**: As interfaces foram criadas SEM estilização para que outra pessoa possa aplicar o design
- **Segurança**: Em produção, use HTTPS e configure adequadamente as variáveis de ambiente
- **Estoque**: O sistema deduz automaticamente o estoque ao finalizar pedidos
- **Comissão**: Sempre 15% sobre o valor total da venda
- **Modalidade**: Sistema preparado apenas para "clique e retire" (sem entrega/frete)

## 🐛 Resolução de Problemas

### Erro de conexão com banco
- Verifique credenciais em `conexao.php`
- Confirme se o banco `conecta_uniformes` existe
- Verifique se o MySQL está rodando

### Código de acesso não chega
- Confirme configuração do Mailersend
- Verifique caixa de spam
- Teste API Key no painel do Mailersend

### Produtos não aparecem no catálogo
- Verifique se fornecedor está homologado para a escola
- Confirme se produto está homologado para a série correta
- Verifique se existem variações com estoque para o gênero do aluno

## 📄 Licença

Sistema desenvolvido para fins educacionais e comerciais.

## 👨‍💻 Suporte

Para dúvidas e suporte, entre em contato com a equipe de desenvolvimento.
