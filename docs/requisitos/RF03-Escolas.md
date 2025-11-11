# [RF03] Manter Cadastro de Escola

Descrição: Este requisito estabelece o ciclo de vida do cadastro de escolas na plataforma: criação com identificação institucional e contato, exibição organizada para consulta, atualização de informações e exclusão controlada quando cabível. Os fluxos garantem consistência mínima, unicidade de contato e a preservação do relacionamento com demais elementos do sistema, quando houver.

Atores: Administrador, Escola
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF03.1 - Listar Escolas

[COLOCAR IMAGEM DA TELA DE LISTAGEM DE ESCOLAS AQUI]

1. O usuário acessa a área de escolas.
2. O sistema verifica se há sessão ativa.
3. Se não houver sessão, informa a necessidade de login e retorna à tela de autenticação. O caso de uso é encerrado.
4. Se autenticado, o sistema apresenta a listagem com identificação da escola e informações principais.
5. A tela oferece ações: cadastrar nova escola, visualizar detalhes, editar informações ou solicitar exclusão (quando permitido).
6. Se não houver escolas cadastradas, o sistema informa a ausência de registros naquele momento.
7. O caso de uso é encerrado.

## RF03.2 - Cadastrar Escola

[COLOCAR IMAGEM DA TELA DE CADASTRO DE ESCOLA AQUI]

1. O administrador escolhe a opção de adicionar nova escola a partir da listagem.
2. O sistema apresenta formulário com campos institucionais (por exemplo: razão social, CNPJ) e contato principal.
3. O administrador preenche os campos obrigatórios e confirma a criação.
4. O sistema verifica presença e consistência mínima dos campos obrigatórios:
	- Se houver ausência ou inconsistência, o sistema informa os pontos a corrigir e permanece na tela de cadastro. O caso de uso é encerrado.
5. O sistema verifica se o email de contato já está em uso para escola:
	- Se houver duplicidade, o sistema informa a ocorrência e mantém na tela de cadastro para ajuste. O caso de uso é encerrado.
	- Estando os dados válidos e inéditos, o sistema registra a escola e o vínculo com seu contato principal.
 	- Regra: email de contato deve ser único entre escolas ativas.
6. Quando informados, o sistema registra os gestores da escola, vinculando-os ao cadastro recém-criado.
 	- Regra: gestores podem ser vinculados no cadastro ou posteriormente via edição.
7. O sistema confirma a criação e retorna à listagem com a nova escola disponível.
8. O caso de uso é encerrado.

## RF03.3 - Visualizar Escola

[COLOCAR IMAGEM DA TELA DE DETALHES DA ESCOLA AQUI]

1. O usuário seleciona uma escola para visualizar.
2. O sistema verifica se há sessão ativa.
3. Se não houver sessão, informa a necessidade de login e retorna à página de autenticação. O caso de uso é encerrado.
4. O sistema tenta localizar a escola solicitada.
5. Se a escola não existir, o sistema informa e retorna à listagem. O caso de uso é encerrado.
6. Sendo localizada, o sistema apresenta os dados da escola e a relação de gestores vinculados.
7. O usuário pode retornar à listagem ou seguir para ações permitidas (editar, excluir) conforme perfil.
8. O caso de uso é encerrado.

## RF03.4 - Editar Escola

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DA ESCOLA AQUI]

1. Um ator autorizado (administrador ou a própria escola) solicita edição.
2. O sistema verifica autenticação e permissões para alterar aquele cadastro.
3. Se não houver permissão, o sistema informa o bloqueio e retorna à área principal. O caso de uso é encerrado.
4. O sistema tenta localizar a escola.
5. Se não localizar, o sistema informa e retorna à listagem. O caso de uso é encerrado.
6. Localizada, o sistema apresenta os dados atuais para edição.
7. O ator realiza os ajustes necessários e confirma.
8. O sistema valida novamente presença e consistência mínima dos campos obrigatórios:
	- Havendo inconsistências, o sistema informa e mantém na tela para correção. O caso de uso é encerrado.
	- Com dados válidos, o sistema registra as alterações e atualiza gestores quando informados.
 	- Regra: atualização de gestores pode ocorrer durante edição.
9. O sistema confirma a atualização e retorna à listagem de escolas.
10. O caso de uso é encerrado.

## RF03.5 - Excluir Escola

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DA ESCOLA AQUI]

1. O administrador solicita a exclusão de uma escola.
2. O sistema verifica autenticação e autorização.
3. Se o perfil não for autorizado, o sistema informa o bloqueio e retorna à área principal. O caso de uso é encerrado.
4. O sistema tenta localizar a escola.
5. Se não localizar, o sistema informa a inexistência e retorna à listagem. O caso de uso é encerrado.
6. O sistema verifica se existem vínculos que impeçam a exclusão (por exemplo, elementos relacionados que dependam daquela escola):
	- Havendo impedimentos, o sistema apresenta os motivos e encerra a solicitação sem remover o registro. O caso de uso é encerrado.
	- Não havendo impedimentos, o sistema efetiva a exclusão da escola.
 	- Regra: apenas administrador pode excluir escola e somente se não houver vínculos impeditivos.
7. O sistema confirma a operação e retorna à listagem.
8. O caso de uso é encerrado.

