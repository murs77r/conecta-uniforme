-- Script de dados iniciais para teste do sistema Conecta Uniforme
-- Execute este script após criar o banco de dados com bd.sql

USE conecta_uniformes;

-- Inserir escola de exemplo
INSERT INTO escola (email, nome, cnpj, telefone, cep, estado, cidade, endereco, ativo) 
VALUES (
    'contato@escolaexemplo.com.br',
    'Escola Municipal Exemplo',
    '12345678000190',
    '(11) 3456-7890',
    '01310-100',
    'SP',
    'São Paulo',
    'Av. Paulista, 1000',
    1
);

SET @escola_id = LAST_INSERT_ID();

-- Inserir gestor escolar
INSERT INTO gestor (nome, email, telefone, escola_id, ativo) 
VALUES (
    'Maria Santos',
    'maria.gestor@escolaexemplo.com.br',
    '(11) 98765-4321',
    @escola_id,
    1
);

-- Inserir fornecedores de exemplo
INSERT INTO fornecedor (nome, email, telefone, cnpj, ativo) 
VALUES 
    ('Uniformes Alpha Ltda', 'contato@uniformesalpha.com.br', '(11) 3333-4444', '98765432000101', 1),
    ('Beta Confecções', 'vendas@betaconfeccoes.com.br', '(11) 5555-6666', '11223344000155', 1);

SET @fornecedor1_id = 1;
SET @fornecedor2_id = 2;

-- Criar homologações (fornecedores autorizados para a escola)
INSERT INTO homologacao (escola_id, fornecedor_id, ativo) 
VALUES 
    (@escola_id, @fornecedor1_id, 1),
    (@escola_id, @fornecedor2_id, 1);

-- Inserir alunos de exemplo
INSERT INTO aluno (nome, matricula, escola_id, serie, genero, ativo) 
VALUES 
    ('João Silva', '2024001', @escola_id, '5º Ano', 'masculino', 1),
    ('Maria Oliveira', '2024002', @escola_id, '5º Ano', 'feminino', 1),
    ('Pedro Santos', '2024003', @escola_id, '4º Ano', 'masculino', 1),
    ('Ana Costa', '2024004', @escola_id, '6º Ano', 'feminino', 1);

SET @aluno1_id = 1;
SET @aluno2_id = 2;
SET @aluno3_id = 3;
SET @aluno4_id = 4;

-- Inserir responsáveis
INSERT INTO responsavel (nome, email, telefone, aluno_id, ativo) 
VALUES 
    ('Carlos Silva', 'carlos.silva@email.com', '(11) 91111-2222', @aluno1_id, 1),
    ('Fernanda Oliveira', 'fernanda.oliveira@email.com', '(11) 93333-4444', @aluno2_id, 1),
    ('Roberto Santos', 'roberto.santos@email.com', '(11) 95555-6666', @aluno3_id, 1),
    ('Juliana Costa', 'juliana.costa@email.com', '(11) 97777-8888', @aluno4_id, 1);

-- Inserir produtos de exemplo (Fornecedor 1)
INSERT INTO produto (fornecedor_id, nome, descricao, preco, ativo) 
VALUES 
    (@fornecedor1_id, 'Camiseta Polo Escolar', 'Camiseta polo manga curta com logo da escola. Tecido 100% algodão.', 45.90, 1),
    (@fornecedor1_id, 'Bermuda Escolar', 'Bermuda tactel com bolsos. Cores variadas.', 39.90, 1),
    (@fornecedor1_id, 'Calça Escolar', 'Calça social escolar em tecido resistente.', 59.90, 1);

SET @produto1_id = 1;
SET @produto2_id = 2;
SET @produto3_id = 3;

-- Homologar produtos para escola e séries
INSERT INTO produto_homologacao (produto_id, escola_id, serie) 
VALUES 
    (@produto1_id, @escola_id, '4º Ano'),
    (@produto1_id, @escola_id, '5º Ano'),
    (@produto1_id, @escola_id, '6º Ano'),
    (@produto2_id, @escola_id, '4º Ano'),
    (@produto2_id, @escola_id, '5º Ano'),
    (@produto2_id, @escola_id, '6º Ano'),
    (@produto3_id, @escola_id, '5º Ano'),
    (@produto3_id, @escola_id, '6º Ano');

-- Adicionar fotos dos produtos (URLs de exemplo)
INSERT INTO produto_foto (produto_id, caminho_foto, ordem) 
VALUES 
    (@produto1_id, '/uploads/produtos/camiseta-polo-1.jpg', 1),
    (@produto1_id, '/uploads/produtos/camiseta-polo-2.jpg', 2),
    (@produto2_id, '/uploads/produtos/bermuda-1.jpg', 1),
    (@produto3_id, '/uploads/produtos/calca-1.jpg', 1);

-- Adicionar variações dos produtos (tamanhos e estoque)
-- Camiseta Polo
INSERT INTO produto_variacao (produto_id, tamanho, cor, genero, quantidade_estoque) 
VALUES 
    (@produto1_id, 'P', 'Branca', 'masculino', 20),
    (@produto1_id, 'M', 'Branca', 'masculino', 25),
    (@produto1_id, 'G', 'Branca', 'masculino', 15),
    (@produto1_id, 'P', 'Branca', 'feminino', 18),
    (@produto1_id, 'M', 'Branca', 'feminino', 22),
    (@produto1_id, 'G', 'Branca', 'feminino', 12);

-- Bermuda
INSERT INTO produto_variacao (produto_id, tamanho, cor, genero, quantidade_estoque) 
VALUES 
    (@produto2_id, 'P', 'Azul', 'masculino', 15),
    (@produto2_id, 'M', 'Azul', 'masculino', 20),
    (@produto2_id, 'G', 'Azul', 'masculino', 10),
    (@produto2_id, 'P', 'Azul', 'feminino', 12),
    (@produto2_id, 'M', 'Azul', 'feminino', 18),
    (@produto2_id, 'G', 'Azul', 'feminino', 8);

-- Calça
INSERT INTO produto_variacao (produto_id, tamanho, cor, genero, quantidade_estoque) 
VALUES 
    (@produto3_id, 'P', 'Cinza', 'masculino', 10),
    (@produto3_id, 'M', 'Cinza', 'masculino', 15),
    (@produto3_id, 'G', 'Cinza', 'masculino', 8),
    (@produto3_id, 'P', 'Cinza', 'feminino', 10),
    (@produto3_id, 'M', 'Cinza', 'feminino', 12),
    (@produto3_id, 'G', 'Cinza', 'feminino', 7);

-- Inserir produtos do Fornecedor 2
INSERT INTO produto (fornecedor_id, nome, descricao, preco, ativo) 
VALUES 
    (@fornecedor2_id, 'Mochila Escolar Grande', 'Mochila com compartimento para notebook, impermeável.', 89.90, 1),
    (@fornecedor2_id, 'Jaqueta Escolar', 'Jaqueta de frio com logo bordado.', 79.90, 1);

SET @produto4_id = 4;
SET @produto5_id = 5;

-- Homologar produtos do fornecedor 2
INSERT INTO produto_homologacao (produto_id, escola_id, serie) 
VALUES 
    (@produto4_id, @escola_id, '4º Ano'),
    (@produto4_id, @escola_id, '5º Ano'),
    (@produto4_id, @escola_id, '6º Ano'),
    (@produto5_id, @escola_id, '5º Ano'),
    (@produto5_id, @escola_id, '6º Ano');

-- Variações fornecedor 2
INSERT INTO produto_variacao (produto_id, tamanho, cor, genero, quantidade_estoque) 
VALUES 
    (@produto4_id, 'Único', 'Azul', 'unissex', 30),
    (@produto5_id, 'P', 'Azul Marinho', 'unissex', 15),
    (@produto5_id, 'M', 'Azul Marinho', 'unissex', 20),
    (@produto5_id, 'G', 'Azul Marinho', 'unissex', 12);

SELECT 'Dados iniciais inseridos com sucesso!' as Status;

SELECT 
    'Escola criada:' as Info,
    nome as Nome,
    email as Email
FROM escola WHERE id = @escola_id;

SELECT 
    'Gestor criado:' as Info,
    nome as Nome,
    email as Email
FROM gestor WHERE escola_id = @escola_id;

SELECT 
    'Fornecedores criados:' as Info,
    COUNT(*) as Total
FROM fornecedor;

SELECT 
    'Alunos criados:' as Info,
    COUNT(*) as Total
FROM aluno;

SELECT 
    'Responsáveis criados:' as Info,
    COUNT(*) as Total
FROM responsavel;

SELECT 
    'Produtos criados:' as Info,
    COUNT(*) as Total
FROM produto;

SELECT 
    '=== CREDENCIAIS PARA TESTE ===' as Info;

SELECT 
    'GESTOR' as Tipo,
    email as Email,
    'Use o sistema de login com código' as Senha
FROM gestor 
UNION ALL
SELECT 
    'FORNECEDOR' as Tipo,
    email as Email,
    'Use o sistema de login com código' as Senha
FROM fornecedor
UNION ALL
SELECT 
    'RESPONSAVEL' as Tipo,
    email as Email,
    'Use o sistema de login com código' as Senha
FROM responsavel;
