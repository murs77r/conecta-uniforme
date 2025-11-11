# [RF07] Manter Cadastro de Pedido

Descrição: Este requisito descreve o gerenciamento de pedidos: criação inicial com dados essenciais, consulta de pedidos existentes conforme perfil, edição de status ou valores permitidos e remoção quando justificável. Garante que cada participante veja apenas o que lhe é pertinente (por exemplo, responsável visualizando seus próprios pedidos), mantendo rastreabilidade básica do ciclo do pedido.

Atores: Responsável, Escola, Administrador
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF07.1 - Criar Pedido

[COLOCAR IMAGEM DA TELA DE CRIAÇÃO DE PEDIDO AQUI]

1. Um usuário autenticado solicita criar um novo pedido.
2. O sistema apresenta uma tela de criação com os campos necessários.
3. O usuário preenche os campos e confirma que deseja registrar o pedido.
4. O sistema verifica se as informações mínimas foram informadas:
	- Se houver ausência de informações obrigatórias, o sistema informa e permanece na tela de criação. O caso de uso é encerrado.
	- Estando os dados válidos, o sistema registra o pedido com um status inicial adequado.
 	- Regra: todo pedido inicia com status padrão definido pelo processo de negócio.
5. O sistema apresenta mensagem de confirmação e direciona para a área de pedidos.
6. O caso de uso é encerrado.

## RF07.2 - Apagar Pedido

[COLOCAR IMAGEM DA TELA DE EDIÇÃO DE PEDIDO AQUI]

1. Um ator autorizado solicita apagar um pedido específico.
2. O sistema verifica se há sessão ativa do usuário.
3. O sistema tenta localizar o pedido informado.
4. Se não localizar, o sistema informa a inexistência e retorna à listagem. O caso de uso é encerrado.
5. Localizado o pedido, o sistema avalia se pode remover (por exemplo, se não estiver em status bloqueado para exclusão):
	- Se o status impedir exclusão, o sistema informa o motivo e retorna à listagem sem remover. O caso de uso é encerrado.
	- Se o pedido puder ser excluído, o sistema realiza a remoção conforme a ação solicitada.
 	- Regra: cancelamentos e mudanças de status detalhados em fluxo próprio.
6. O sistema confirma a operação e retorna à listagem de pedidos.
7. O caso de uso é encerrado.

## RF07.3 - Editar Pedido

[COLOCAR IMAGEM DA TELA DE EDIÇÃO DE PEDIDO AQUI]

1. Um ator autorizado solicita editar um pedido existente.
2. O sistema verifica se há sessão ativa do usuário.
3. O sistema tenta localizar o pedido informado.
4. Se não localizar, o sistema informa e retorna à listagem. O caso de uso é encerrado.
5. Localizado o pedido, o sistema apresenta os dados atuais para edição.
6. O usuário altera os campos disponíveis e confirma a atualização.
7. O sistema verifica a consistência mínima das informações alteradas:
	- Se alguma informação estiver inconsistente, o sistema informa e mantém na tela de edição. O caso de uso é encerrado.
	- Estando válidas, o sistema registra as alterações solicitadas.
 	- Regra: alterações de status específicas seguem fluxo próprio.
8. O sistema confirma a atualização e retorna à listagem de pedidos.
9. O caso de uso é encerrado.

## RF07.4 - Consultar Pedidos

[COLOCAR IMAGEM DA TELA DE LISTAGEM DE PEDIDOS AQUI]

1. Um usuário autenticado solicita visualizar pedidos.
2. O sistema verifica se há sessão ativa.
3. Se não houver sessão, o sistema informa a necessidade de login e encerra. O caso de uso é encerrado.
4. O sistema apresenta a listagem de pedidos conforme o perfil do usuário (por exemplo, apenas os próprios pedidos quando aplicável, ou abrangência maior para perfis de gestão):
	- Se não houver pedidos visíveis para o perfil, o sistema informa a ausência de registros. O caso de uso é encerrado.
	- Havendo pedidos, o usuário pode selecionar um pedido para consultar seus detalhes e itens relacionados.
 	- Regra: perfis restritos só visualizam seus próprios pedidos; perfis de gestão enxergam conjunto ampliado.
5. O sistema apresenta as informações do pedido selecionado.
6. O caso de uso é encerrado.

