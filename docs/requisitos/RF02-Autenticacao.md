# [RF02] Gerenciar Autenticação e Acesso

Descrição: Este requisito aborda os fluxos de entrada e saída de usuários na plataforma utilizando código de acesso temporário enviado ao contato informado. O objetivo é garantir que apenas pessoas com acesso ao canal de contato possam autenticar, sem expor dados sensíveis e mantendo uma experiência direta. Estão contemplados a solicitação do código, a validação para abertura de sessão e o encerramento da sessão pelo próprio usuário.

Atores: Usuário (todos perfis), Administrador
Prioridade: (X) Essencial  ( ) Importante  ( ) Desejável

## RF02.1 - Solicitar Código de Acesso

[COLOCAR IMAGEM DA TELA DE SOLICITAÇÃO DE CÓDIGO AQUI]

1. O usuário acessa a tela de autenticação e insere seu email no campo indicado.
2. O sistema verifica se o campo foi preenchido e se o email aparenta estar no formato correto.
3. O sistema identifica se existem perfis ativos associados a esse email:
	- Se não houver perfil associado, o sistema informa que o email não está cadastrado e mantém o usuário na mesma tela. O caso de uso é encerrado.
	- Havendo mais de um perfil, o sistema solicita que o usuário escolha com qual perfil deseja entrar; havendo apenas um perfil, o sistema prossegue automaticamente.
 	- Regra: quando houver mais de um perfil para o mesmo email, a escolha explícita é obrigatória.
4. O sistema gera um código de acesso temporário para o email e perfil selecionados.
5. O sistema registra o código com tempo de validade e controle de uso.
 	- Regra: código expira após período curto definido pelo negócio.
 	- Regra: código não pode ser reutilizado depois de validado.
6. O sistema tenta entregar o código ao email informado e exibe mensagem orientando a próxima etapa.
7. O usuário é direcionado à tela para digitar o código recebido, com opção para solicitar novo código quando necessário.
8. O caso de uso é encerrado.

## RF02.2 - Validar Código de Acesso (Login)

[COLOCAR IMAGEM DA TELA DE VALIDAÇÃO DE CÓDIGO AQUI]

1. O usuário acessa a tela de validação do código e informa o código recebido (e, quando necessário, confirma email e perfil).
2. O sistema verifica se os campos obrigatórios foram informados.
3. O sistema busca um código de acesso válido, associado ao email e perfil escolhidos, que ainda não tenha sido utilizado:
	- Se não encontrar um código válido ou ele já tiver sido utilizado, o sistema informa que o código é inválido e mantém o usuário na tela para nova tentativa. O caso de uso é encerrado.
	- Se encontrar um código válido e não utilizado, o sistema prossegue para a verificação de prazo.
4. O sistema verifica se o código ainda está dentro do prazo de validade:
	- Se o código estiver expirado, o sistema informa a expiração e direciona o usuário para solicitar um novo código. O caso de uso é encerrado.
	- Se o código estiver dentro do prazo, o sistema prossegue para a verificação de status do usuário.
5. O sistema confirma se o usuário associado ao código está ativo:
	- Se o usuário estiver inativo, o sistema informa a situação e mantém o usuário na tela sem permitir acesso. O caso de uso é encerrado.
	- Estando ativo, o sistema marca o código como utilizado para impedir reutilização.
 	- Regra: somente usuários ativos podem concluir autenticação.
6. O sistema cria a sessão do usuário e confirma a entrada no sistema.
7. O sistema exibe mensagem de boas-vindas e encaminha o usuário para a área principal apropriada.
8. O caso de uso é encerrado.

## RF02.3 - Encerrar Sessão (Logout)

[COLOCAR IMAGEM DE CONFIRMAÇÃO/SAÍDA (LOGOUT) AQUI]

1. O usuário solicita a saída do sistema por meio da opção apropriada.
2. O sistema identifica a sessão ativa do usuário.
3. O sistema registra o encerramento da sessão para referência futura.
4. O sistema remove da memória os dados associados à sessão daquele usuário.
5. O sistema informa que a saída foi concluída com sucesso e retorna à tela de autenticação.
6. O caso de uso é encerrado.


