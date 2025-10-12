# Conecta Uniforme

Plataforma para gestão integrada do ciclo de uniformes escolares, conectando escolas, fornecedores e responsáveis.

## Perfis de acesso disponíveis

- **Administrador**: cria, edita e remove escolas e fornecedores em todo o ecossistema, além de consultar alunos cadastrados.
- **Gestor Escolar**: gerencia alunos e homologações de fornecedores vinculadas à própria escola.
- **Fornecedor**: administra catálogo de produtos, estoque e pedidos.
- **Responsável**: acessa o catálogo autorizado da escola para realizar pedidos.

Todos os perfis utilizam o fluxo de login por código temporário enviado por e-mail (`/login-novo`).

### Contas de exemplo (dados-iniciais.sql)

| Perfil | Nome | E-mail |
| --- | --- | --- |
| Administrador | Administrador Geral | `admin@conectauniforme.com.br` |
| Gestor | Maria Santos | `maria.gestor@escolaexemplo.com.br` |
| Fornecedor | Uniformes Alpha Ltda | `contato@uniformesalpha.com.br` |
| Responsável | Carlos Silva | `carlos.silva@email.com` |

## Fluxos principais

1. **Administrador**: acessa o painel `/dashboard-administrador` para cadastrar/atualizar escolas e fornecedores e visualizar alunos cadastrados.
2. **Gestor**: em `/alunos-gestor` pode importar, editar e manter alunos e respectivos responsáveis.
3. **Fornecedor**: mantém catálogo de produtos, pedidos e estoque.
4. **Responsável**: navega pelo catálogo homologado e fecha pedidos para retirada.

## Requisitos

- PHP 8.1+
- MySQL/MariaDB 10+
- Extensões mysqli e curl habilitadas

## Configuração rápida

1. Crie o banco de dados executando `bd.sql` e depois `dados-iniciais.sql`.
2. Duplique `config.php.example` (se existir) ou ajuste `config.php` com as credenciais do banco.
3. Defina as variáveis de e-mail no `.env` para envio do código de acesso (ou rode em modo desenvolvimento para log interno).
4. Inicie o servidor PHP embutido: `php -S localhost:8000 router.php`.

## Novidades

- Edição completa de responsáveis ao atualizar um aluno (inclusive remoção e inclusão de novos contatos).
- Novo perfil **Administrador** com painel dedicado para gestão de escolas e fornecedores e visão geral de alunos.
- Ajustes na navegação e na página inicial para acesso direto ao novo perfil.
