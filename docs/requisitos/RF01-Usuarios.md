# [RF01] Manter cadastro de Usuário

Resumo: Registrar e gerir usuários do sistema, com autenticação própria (e-mail/senha) e opção de autenticação federada (OAuth 2.0 / OpenID Connect), como "Entrar com Google" ou "Login com Apple". Inclui verificação de e-mail via código de 6 caracteres alfanuméricos, com validade de 15 minutos e possibilidade de reenvio.

Atores: Usuário, Administrador

Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável


## RF01.1 - CONSULTAR Usuário

Na tela de apresentação padrão ao acessar o sistema, é possível acessar as funcionalidades de Consulta.
A tela mostra os usuários cadastrados, onde é possível filtrar (buscar) os usuários.
O usuário, ao efetuar o logon no sistema, é direcionado para TELA [RF01] Gestão cadastro de Usuário - Dashboard.
O sistema realiza a busca de usuários cadastrados no banco de dados e os mostra de acordo com o filtro selecionado (o padrão é trazer todos os usuários cadastrados).
O sistema deve exibir uma tela com os principais dados dos usuários.
Na tela deve haver acesso ao botão/link para CADASTRAR USUÁRIO (RF01.2) e, a partir desta, o VALIDAR usuário (RF01.3).
O sistema mostra para cada usuário 2 opções: ALTERAR USUÁRIO (RF01.4) e DESATIVAR (Excluir) USUÁRIO (RF01.5).
Os nomes são mostrados em ordem alfabética e em página com 20 usuários no máximo.
A partir do link de listagem de usuários, podem ser realizados filtros de busca, por exemplo, por nome, ID, status ao se clicar no topo da página de nomes.

A partir desta tela é possível acessar as funções de:
- CADASTRAR usuário (RF01.2) e, a partir desta, o VALIDAR usuário (RF01.3)
- ALTERAR usuário (RF01.4)
- DESATIVAR (Excluir) usuário (RF01.5)

[IMAGEM DO RF01, TELA DE GESTÃO DE USUÁRIOS]
TELA [RF01] gestão de cadastro de Usuário. Não é pra ter nada além disso, NADA. SEM TABELAS, POR EXEMPLO.

## RF01.2 - CADASTRAR Usuário

Fluxo detalhado do caso de uso de cadastro de usuário.

1. O usuário (administrador autenticado) clica no botão "Novo Usuário" na tela de listagem de usuários (TELA [RF01] Manter cadastro de Usuário).
2. O sistema direciona para a tela de cadastro, exibindo os campos obrigatórios: Nome Completo, Email, Tipo de Usuário; campos opcionais: Telefone.
3. O usuário preenche os campos e clica em "Cadastrar".
4. O sistema valida obrigatoriedade dos campos (nome, email, tipo) e o formato do email. Se faltar algo ou o formato for inválido, mantém o usuário na tela e apresenta mensagem de erro.
5. Se informado telefone, o sistema valida o formato. Em caso de falha, permanece na tela e exibe mensagem.
6. O sistema valida se o tipo de usuário está entre os valores permitidos: administrador, escola, fornecedor, responsavel.
7. O sistema verifica duplicidade de email para o mesmo tipo. Se já existir:
	- Exibe a mensagem "Já existe um usuário com este email para o mesmo tipo selecionado." e permanece na tela de cadastro.
8. Não havendo erros, o sistema cria o registro do usuário ativo, salvando: nome, email normalizado (lowercase), telefone, tipo e ativo.
 	- Regra: email é armazenado em letras minúsculas para consistência.
 	- Regra: combinação (email, tipo) deve ser única permitindo múltiplos tipos para mesmo email.
9. Após a criação bem-sucedida, o sistema redireciona para a listagem de usuários.
10. A listagem passa a exibir o novo usuário entre os demais registros.
11. O caso de uso é encerrado.

Observações (restritas ao fluxo):
- Não inclui verificação de email nem criação de senha; autenticação é tratada em requisito separado.

Mensagens de erro envolvidas no fluxo:
- "Preencha todos os campos obrigatórios." (campos faltando)
- "Telefone inválido." (formato telefone)
- "Email inválido." (formato email)
- "Tipo de usuário inválido." (tipo fora da lista)
- "Já existe um usuário com este email para o mesmo tipo selecionado." (duplicidade)
- Mensagens genéricas caso falhe a criação: permanece na tela de cadastro.

## RF01.3 - CONSULTAR Usuário (Listar / Visualizar)

Este subrequisito cobre a listagem e a visualização de detalhes de usuários.

1. O usuário administrador acessa a tela de listagem de usuários.
2. O sistema verifica se o perfil tem permissão para visualizar a listagem.
3. Se não autorizado: o sistema informa "Acesso negado. Apenas administradores podem acessar esta página." e redireciona para a tela inicial. O caso de uso é encerrado.
4. Se autorizado: o sistema apresenta a lista de usuários com as principais informações (nome, email, tipo, status, data de cadastro) e ações disponíveis.
5. Para cada usuário são exibidos botões de ação: visualizar, editar, logs e excluir (quando aplicável).
6. O administrador pode clicar em "Novo Usuário" para acionar o subrequisito RF01.2 (Cadastrar). O caso de uso de consulta continua.
7. Ao selecionar a ação "Visualizar":
	- O sistema verifica se há sessão válida.
	- Se não autenticado: informa "Faça login para continuar." e direciona para a tela de autenticação (RF02). O caso de uso é encerrado.
	- Se autenticado: verifica se o perfil pode visualizar aquele usuário (administrador ou o próprio). Se não puder: informa "Você não tem permissão para visualizar este usuário." e retorna à tela inicial. O caso de uso é encerrado.
8. O sistema tenta localizar o usuário solicitado. Se não encontrar: informa "Usuário não encontrado." e volta à listagem. O caso de uso é encerrado.
9. Em caso de sucesso: o sistema exibe a tela de detalhes com nome, email, telefone, tipo, status, data de cadastro e opções de navegação.
10. O caso de uso é encerrado.

Observações (restritas ao fluxo):
- Ordenação atual por critérios internos; paginação poderá ser tratada em requisito próprio.

## RF01.4 - ALTERAR Usuário

Fluxo de edição de dados do usuário.

1. O usuário acessa a tela de edição do cadastro desejado.
2. O sistema verifica se há sessão ativa. Se não houver: informa "Faça login para continuar." e direciona para autenticação (RF02). O caso de uso é encerrado.
3. Se autenticado: o sistema verifica se é administrador ou o próprio usuário. Se não for: informa "Você não tem permissão para editar este usuário." e retorna à tela inicial. O caso de uso é encerrado.
4. O sistema tenta localizar o usuário solicitado. Se não encontrar: informa "Usuário não encontrado." e retorna à listagem. O caso de uso é encerrado.
5. Ao abrir a tela, o sistema exibe formulário com os dados atuais para edição.
6. Ao salvar, o sistema coleta os dados (nome, email, telefone) e, se o perfil for administrador, também tipo e status (ativo/inativo).
7. O sistema valida obrigatoriedade (nome, email), formato do email e do telefone (quando informado).
8. Regra especial: impedir a inativação caso isso torne inexistente um administrador ativo. Se ocorrer: informa o bloqueio e mantém na tela de edição.
9. Se as validações forem aprovadas: o sistema atualiza o cadastro e registra a alteração para auditoria.
 	- Regra: toda alteração relevante é registrada para auditoria.
10. Se o usuário editado é o próprio logado: o sistema direciona para a tela inicial; caso contrário, retorna à listagem.
11. O caso de uso é encerrado.

Observações (restritas ao fluxo):
- Fluxo não altera senha; redefinição é requisito distinto.
- Alterações são registradas para auditoria.

## RF01.5 - EXCLUIR Usuário

Fluxo de exclusão de usuário.

1. O administrador seleciona a ação de excluir na listagem.
2. O sistema verifica se o perfil tem permissão de administrador. Se não tiver: informa o bloqueio e direciona à tela inicial. O caso de uso é encerrado.
3. O sistema impede excluir o próprio usuário logado: informa "Você não pode excluir seu próprio usuário." e retorna à listagem. O caso de uso é encerrado.
4. O sistema tenta localizar o usuário. Se inexistente: informa "Usuário não encontrado." e retorna à listagem. O caso de uso é encerrado.
5. O sistema verifica dependências (ex.: se seria o último administrador ativo; vínculos com escola, fornecedor, responsável):
	- Havendo bloqueios, o sistema informa os motivos e recomenda inativar ao invés de excluir. O caso de uso é encerrado.
	- Não havendo bloqueios, o sistema executa a exclusão e registra o evento para auditoria.
 	- Regra: exclusão não pode deixar o sistema sem administrador ativo.
6. O sistema retorna à listagem.
7. O caso de uso é encerrado.

Observações (restritas ao fluxo):
- Exclusão é definitiva; alternativa de inativação pode existir em requisito futuro.

