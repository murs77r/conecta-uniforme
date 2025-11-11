# [RF06] Manter Cadastro de Produto

Descrição: Este requisito cobre a manutenção do catálogo de produtos associados a fornecedores: criação de itens com informações essenciais, listagem para consulta, edição para ajustes e exclusão quando não forem mais disponibilizados. O objetivo é garantir clareza sobre o que pode ser ofertado, com dados consistentes para identificação e acompanhamento.

Atores: Administrador, Fornecedor
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF06.1 - Listar Produtos

[COLOCAR IMAGEM DA TELA DE LISTAGEM DE PRODUTOS AQUI]

1. O usuário acessa a área de produtos.
2. O sistema apresenta a listagem com identificação do produto e informações principais (por exemplo, nome e situação).
3. A tela oferece ações compatíveis com o perfil do usuário: cadastrar novo produto, visualizar, editar ou excluir.
4. Se não existirem produtos cadastrados, o sistema informa a ausência de registros.
5. O caso de uso é encerrado.

## RF06.2 - Cadastrar Produto

[COLOCAR IMAGEM DA TELA DE CADASTRO DE PRODUTO AQUI]

1. Um ator autorizado solicita cadastrar um novo produto.
2. O sistema apresenta o formulário com campos obrigatórios (por exemplo, nome, preço e fornecedor vinculado) e campos opcionais.
3. O ator preenche os campos e confirma a criação.
4. O sistema verifica a presença dos obrigatórios e consistência mínima dos valores informados (por exemplo, preço preenchido corretamente):
	- Se houver ausência ou inconsistência, o sistema informa e permanece na tela de cadastro. O caso de uso é encerrado.
	- Com dados válidos, o sistema registra o produto como disponível.
 	- Regra: produto nasce ativo salvo orientação contrária do negócio.
5. O sistema confirma a criação e retorna à listagem.
6. O caso de uso é encerrado.

## RF06.3 - Editar Produto

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DE PRODUTO AQUI]

1. Um ator autorizado solicita editar um produto existente.
2. O sistema verifica se o produto solicitado existe:
	- Se o produto não existir, o sistema informa e encerra. O caso de uso é encerrado.
	- Se existir, o sistema apresenta os dados atuais para edição.
3. O ator altera os campos desejados e confirma.
4. O sistema valida a presença dos campos essenciais e a consistência mínima dos novos valores (por exemplo, preço):
	- Em caso de falha na validação, o sistema informa e mantém na tela de edição. O caso de uso é encerrado.
	- Com as informações válidas, o sistema registra as alterações.
 	- Regra: edição restrita a perfis autorizados (administrador ou fornecedor proprietário).
5. O sistema confirma a atualização e retorna à listagem.
6. O caso de uso é encerrado.

## RF06.4 - Excluir Produto

[COLOCAR IMAGEM DA TELA DE EDIÇÃO/EXCLUSÃO DE PRODUTO AQUI]

1. Um ator autorizado solicita excluir um produto.
2. O sistema verifica se o produto existe.
3. Se não existir, o sistema informa e encerra. O caso de uso é encerrado.
4. O sistema verifica se há impedimentos (por exemplo, uso do produto em registros dependentes):
	- Havendo impedimentos, o sistema informa os motivos e encerra a solicitação sem exclusão. O caso de uso é encerrado.
	- Na ausência de impedimentos, o sistema realiza a exclusão do produto.
 	- Regra: exclusão bloqueada enquanto existir vínculo impeditivo declarado.
5. O sistema confirma a operação e retorna à listagem.
6. O caso de uso é encerrado.

