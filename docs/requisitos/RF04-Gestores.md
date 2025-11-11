# [RF04] Manter Cadastro de Gestor Escolar

Descrição: Este requisito define como cadastrar, visualizar, editar e excluir gestores vinculados a uma escola. O objetivo é permitir que a unidade escolar mantenha contatos responsáveis atualizados, assegurando informações básicas para comunicação e gestão. Os fluxos validam a presença do nome e consistência mínima de contatos quando informados.

Atores: Administrador, Escola
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF04.1 - Listar Gestores de Escola

[COLOCAR IMAGEM DA TELA DE LISTAGEM DE GESTORES POR ESCOLA AQUI]

1. O usuário acessa a seção de gestores a partir de uma escola selecionada.
2. O sistema verifica se há sessão ativa:
	- Se não houver sessão, o sistema informa a necessidade de login e retorna à autenticação. O caso de uso é encerrado.
	- Havendo sessão ativa, o sistema prossegue.
3. O sistema verifica se a escola informada existe:
	- Se a escola não existir, o sistema informa a inexistência e retorna à área de escolas. O caso de uso é encerrado.
	- Se a escola existir, o sistema prossegue.
4. O sistema verifica se o perfil do usuário permite acessar os gestores daquela escola (administrador ou a própria escola):
	- Se não houver permissão, o sistema informa o bloqueio e retorna à área principal. O caso de uso é encerrado.
	- Havendo permissão, o sistema apresenta a lista de gestores vinculados à escola, com seus dados principais.
5. O caso de uso é encerrado.

## RF04.2 - Cadastrar Gestor Escolar

[COLOCAR IMAGEM DA TELA DE CADASTRO DE GESTOR AQUI]

1. Um ator autorizado solicita cadastrar um gestor para uma escola específica.
2. O sistema verifica se há sessão ativa e se a escola existe:
	- Se não houver sessão ou a escola não existir, o sistema informa e encerra. O caso de uso é encerrado.
	- Havendo sessão e escola válida, o sistema prossegue.
3. O sistema confirma se o perfil do ator está autorizado (administrador ou a própria escola):
	- Se não estiver autorizado, o sistema informa e encerra. O caso de uso é encerrado.
	- Estando autorizado, o sistema prossegue.
4. O sistema apresenta formulário com campos do gestor (nome obrigatório e contatos/identificação opcionais).
5. O ator preenche os dados e confirma.
6. O sistema valida a presença do nome e a consistência mínima dos demais campos informados:
	- Em caso de inconsistência, o sistema informa e permanece na tela para correções. O caso de uso é encerrado.
	- Com dados válidos, o sistema registra o gestor vinculado à escola.
 	- Regra: nome do gestor é sempre obrigatório.
7. O sistema confirma a criação e retorna à lista de gestores daquela escola.
8. O caso de uso é encerrado.

## RF04.3 - Editar Gestor Escolar

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DE GESTOR AQUI]

1. Um ator autorizado solicita editar um gestor existente.
2. O sistema verifica se há sessão ativa e tenta localizar o gestor informado:
	- Se não houver sessão ou o gestor não existir, o sistema informa e encerra. O caso de uso é encerrado.
	- Havendo sessão e gestor localizado, o sistema prossegue.
3. O sistema verifica se o ator tem permissão (administrador ou escola proprietária do cadastro):
	- Se não tiver permissão, o sistema informa e encerra. O caso de uso é encerrado.
	- Havendo permissão, o sistema apresenta os dados atuais para edição.
4. O ator altera as informações desejadas e confirma.
5. O sistema valida a presença do nome e a consistência mínima dos demais campos:
	- Em caso de falha de validação, o sistema informa e mantém na tela de edição. O caso de uso é encerrado.
	- Estando válidas as alterações, o sistema registra a atualização do gestor.
 	- Regra: nome continua obrigatório em qualquer atualização.
6. O sistema confirma a atualização e retorna à listagem de gestores.
7. O caso de uso é encerrado.

## RF04.4 - Excluir Gestor Escolar

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DE GESTOR AQUI]

1. Um ator autorizado solicita excluir um gestor.
2. O sistema verifica se há sessão ativa e tenta localizar o gestor:
	- Se não houver sessão ou o gestor não existir, o sistema informa e encerra. O caso de uso é encerrado.
	- Havendo sessão e gestor localizado, o sistema prossegue.
3. O sistema verifica se o ator possui autorização (administrador ou escola proprietária):
	- Se não houver autorização, o sistema informa e encerra. O caso de uso é encerrado.
	- Havendo autorização, o sistema efetiva a exclusão do gestor.
 	- Regra: somente administrador ou escola proprietária podem excluir gestor.
4. O sistema apresenta confirmação e retorna à listagem de gestores da escola correspondente.
5. O caso de uso é encerrado.

