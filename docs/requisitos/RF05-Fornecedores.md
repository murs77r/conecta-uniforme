# [RF05] Manter Cadastro de Fornecedor

Descrição: Este requisito trata da gestão completa do fornecedor dentro da plataforma: identificação cadastral, atualização de dados, visualização organizada e remoção controlada. O objetivo é permitir que a administração garanta a qualidade e consistência dos dados de fornecedores, possibilitando seu relacionamento com demais elementos (como produtos ou futuros vínculos operacionais). Engloba a apresentação da lista de fornecedores, inclusão de novos registros, alteração de informações e exclusão quando não houver mais necessidade ou vínculos impeditivos. O fluxo assegura validações mínimas de identificação e unicidade do contato principal.

Atores: Administrador, Fornecedor
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF05.1 - Listar Fornecedores

[COLOCAR IMAGEM DA TELA PRINCIPAL DE LISTAGEM DE FORNECEDORES AQUI]

1. O usuário acessa a área de fornecedores a partir do menu ou acesso disponível.
2. O sistema verifica se há sessão válida.
3. Se não houver sessão ativa, informa a necessidade de autenticação e retorna à área de entrada. O caso de uso é encerrado.
4. Se autenticado, o sistema apresenta a tela de listagem contendo, para cada fornecedor, identificação principal e estado de disponibilidade.
5. A listagem oferece pontos de ação: cadastrar novo fornecedor, visualizar detalhes de um existente, iniciar edição ou solicitar exclusão.
6. Caso a listagem não possua registros, o sistema exibe indicação de ausência de fornecedores cadastrados.
7. O caso de uso é encerrado.

## RF05.2 - Cadastrar Fornecedor

[COLOCAR IMAGEM DA TELA DE CADASTRO DE FORNECEDOR AQUI]

1. O administrador aciona a ação de adicionar novo fornecedor a partir da listagem.
2. O sistema exibe formulário de cadastro com campos para identificação (ex.: nome de contato, email) e dados corporativos.
3. O administrador preenche os campos obrigatórios e confirma a intenção de registrar.
4. O sistema verifica presença de todos os campos marcados como obrigatórios:
	- Se existir ausência ou conteúdo inválido em campo obrigatório, o sistema informa a inconsistência e permanece na mesma tela aguardando correção. O caso de uso é encerrado.
5. O sistema verifica unicidade do contato principal (email) em relação a fornecedores já cadastrados:
	- Caso haja duplicidade, o sistema informa a ocorrência e mantém o usuário na tela para ajuste. O caso de uso é encerrado.
	- Estando os dados válidos e inéditos, o sistema registra o fornecedor e associa-o ao responsável administrativo interno.
 	- Regra: email do contato principal deve ser único entre fornecedores ativos.
6. O sistema confirma a conclusão do cadastro e retorna à listagem já contemplando o novo fornecedor.
7. O caso de uso é encerrado.

## RF05.3 - Editar Fornecedor

[COLOCAR IMAGEM DA TELA DE EDIÇÃO DE FORNECEDOR AQUI]

1. Um ator autorizado (administrador ou fornecedor) seleciona um fornecedor na listagem para alteração.
2. O sistema verifica se a sessão é válida e se o ator possui permissão adequada.
3. Se a sessão for inválida ou não houver permissão, o sistema informa a restrição e encerra. O caso de uso é encerrado.
4. O sistema tenta localizar o fornecedor solicitado.
5. Se não localizar, informa a inexistência e retorna à listagem. O caso de uso é encerrado.
6. Localizado o registro, o sistema apresenta os dados atuais em modo de edição.
7. O ator ajusta os campos necessários e confirma.
8. O sistema valida a presença dos campos obrigatórios e a consistência mínima das informações alteradas:
	- Se falhar na validação, o sistema comunica o problema e aguarda nova submissão. O caso de uso é encerrado.
	- Com as informações válidas, o sistema grava as alterações e atualiza a base.
 	- Regra: somente fornecedor proprietário ou administrador podem editar.
9. O sistema confirma a conclusão e retorna à listagem refletindo as mudanças.
10. O caso de uso é encerrado.

## RF05.4 - Excluir Fornecedor

[COLOCAR IMAGEM DA TELA DE CONFIRMAÇÃO/EXCLUSÃO DE FORNECEDOR AQUI]

1. O administrador aciona a opção de excluir um fornecedor específico.
2. O sistema verifica validade da sessão e perfil do ator.
3. Se não houver sessão ou o perfil não for autorizado, informa restrição e interrompe. O caso de uso é encerrado.
4. O sistema busca o fornecedor alvo.
5. Se o fornecedor não existir, comunica inexistência e retorna à listagem. O caso de uso é encerrado.
6. O sistema avalia se há vínculos ativos que impeçam a exclusão (por exemplo, relacionamentos operacionais ainda dependentes):
	- Havendo impedimentos, o sistema informa os motivos e encerra sem remover. O caso de uso é encerrado.
	- Na ausência de impedimentos, o sistema efetiva a remoção do fornecedor.
 	- Regra: exclusão apenas por administrador e condicionada à inexistência de vínculos impeditivos.
7. O sistema apresenta confirmação e retorna à listagem atualizada.
8. O caso de uso é encerrado.