# Conecta Uniforme

Plataforma para gestão integrada do ciclo de uniformes escolares, conectando escolas, fornecedores e responsáveis.

## Perfis de acesso disponíveis

- **Administrador**: cria, edita e remove escolas e fornecedores em todo o ecossistema, além de consultar alunos cadastrados.
- **Gestor Escolar**: gerencia alunos e homologações de fornecedores vinculadas à própria escola.
- **Fornecedor**: administra catálogo de produtos, estoque e pedidos.
- **Responsável**: acessa o catálogo autorizado da escola para realizar pedidos.

Todos os perfis utilizam o fluxo de login por código temporário enviado por e-mail (`/login-novo`), mas estão com acesso livre por qualquer código para validação.

### Contas de exemplo (dados-iniciais.sql)

| Perfil | Nome | E-mail |
| --- | --- | --- |
| Administrador | Administrador Geral | `admin@conectauniforme.com.br` |
| Gestor | Maria Santos | `maria.ge
maria.Gestor@escolaexemplo.com.br` |
| Fornecedor | Uniformes Alpha Ltda | `contato@uniformesalpha.com.br` |
| Responsável | Carlos Silva | `carlos.silva@email.com` |

## Fluxos principais

1. **Administrador**: acessa o painel `/dashboard-administrador` para cadastrar/atualizar escolas e fornecedores e visualizar alunos cadastrados.
2. **Gestor**: em `/alunos-gestor` pode importar, editar e manter alunos e respectivos responsáveis.
3. **Fornecedor**: mantém catálogo de produtos, pedidos e estoque.
4. **Responsável**: navega pelo catálogo homologado e fecha pedidos para retirada.
