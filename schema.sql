-- ============================================
-- CONECTA UNIFORME - SCHEMA DO BANCO DE DADOS
-- ============================================
-- Este arquivo contém todas as tabelas necessárias para o sistema

-- ============================================
-- TABELA: usuarios
-- Armazena todos os usuários do sistema
-- Tipos: 'administrador', 'escola', 'fornecedor', 'responsavel'
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('administrador', 'escola', 'fornecedor', 'responsavel')),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (email, tipo)
);

-- ============================================
-- TABELA: codigos_acesso
-- Armazena os códigos temporários de acesso (autenticação)
-- Cada código tem validade de 24 horas
-- ============================================
CREATE TABLE IF NOT EXISTS codigos_acesso (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    codigo VARCHAR(6) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE
);

-- ============================================
-- TABELA: escolas
-- Armazena informações das escolas cadastradas
-- ============================================
CREATE TABLE IF NOT EXISTS escolas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    cnpj VARCHAR(18) UNIQUE,
    razao_social VARCHAR(200),
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: fornecedores
-- Armazena informações dos fornecedores de uniformes
-- ============================================
CREATE TABLE IF NOT EXISTS fornecedores (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    cnpj VARCHAR(18) UNIQUE,
    razao_social VARCHAR(200),
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: responsaveis
-- Armazena informações dos pais/responsáveis
-- ============================================
CREATE TABLE IF NOT EXISTS responsaveis (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    cpf VARCHAR(14) UNIQUE,
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: gestores_escolares
-- Permite cadastrar múltiplos gestores para cada escola
-- ============================================
CREATE TABLE IF NOT EXISTS gestores_escolares (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER NOT NULL REFERENCES escolas(id) ON DELETE CASCADE,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    telefone VARCHAR(20),
    cpf VARCHAR(14),
    tipo_gestor VARCHAR(50), -- ex: diretor, coordenador, financeiro
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: homologacao_fornecedores
-- Relaciona escolas com fornecedores homologados
-- Uma escola pode ter vários fornecedores homologados
-- ============================================
CREATE TABLE IF NOT EXISTS homologacao_fornecedores (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER NOT NULL REFERENCES escolas(id) ON DELETE RESTRICT,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE RESTRICT,
    data_homologacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    UNIQUE(escola_id, fornecedor_id)
);

-- ============================================
-- TABELA: produtos
-- Armazena os produtos (uniformes) cadastrados pelos fornecedores
-- ============================================
CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE RESTRICT,
    escola_id INTEGER REFERENCES escolas(id) ON DELETE RESTRICT,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(100),
    tamanho VARCHAR(20),
    cor VARCHAR(50),
    preco DECIMAL(10, 2) NOT NULL,
    estoque INTEGER DEFAULT 0,
    imagem_url VARCHAR(500),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: pedidos
-- Armazena os pedidos realizados pelos responsáveis
-- Status: 'carrinho', 'pendente', 'pago', 'enviado', 'entregue', 'cancelado'
-- ============================================
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    responsavel_id INTEGER NOT NULL REFERENCES responsaveis(id) ON DELETE RESTRICT,
    escola_id INTEGER REFERENCES escolas(id) ON DELETE RESTRICT,
    valor_total DECIMAL(10, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('carrinho', 'pendente', 'pago', 'enviado', 'entregue', 'cancelado')),
    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT
);

-- ============================================
-- TABELA: itens_pedido
-- Armazena os itens de cada pedido
-- ============================================
CREATE TABLE IF NOT EXISTS itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: logs_alteracoes
-- Registra todas as alterações importantes no sistema (INSERT, UPDATE, DELETE)
-- Para auditoria e rastreabilidade
-- ============================================
CREATE TABLE IF NOT EXISTS logs_alteracoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    tabela VARCHAR(100) NOT NULL,
    registro_id INTEGER NOT NULL,
    acao VARCHAR(20) NOT NULL CHECK (acao IN ('INSERT', 'UPDATE', 'DELETE')),
    dados_antigos TEXT,
    dados_novos TEXT,
    data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_usuario VARCHAR(50),
    descricao TEXT
);

-- ============================================
-- TABELA: logs_acesso
-- Registra eventos de LOGIN e LOGOFF dos usuários
-- Separado dos logs de alterações para melhor organização
-- ============================================
CREATE TABLE IF NOT EXISTS logs_acesso (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    acao VARCHAR(20) NOT NULL CHECK (acao IN ('LOGIN', 'LOGOFF')),
    tipo_autenticacao VARCHAR(50), -- 'codigo'
    data_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_usuario VARCHAR(50),
    user_agent TEXT,
    sucesso BOOLEAN DEFAULT TRUE,
    descricao TEXT
);

-- ============================================
-- ÍNDICES PARA MELHORAR PERFORMANCE
-- ============================================
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_tipo ON usuarios(tipo);
CREATE INDEX idx_codigos_acesso_usuario ON codigos_acesso(usuario_id);
CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_produtos_escola ON produtos(escola_id);
CREATE INDEX idx_pedidos_responsavel ON pedidos(responsavel_id);
CREATE INDEX idx_pedidos_status ON pedidos(status);
CREATE INDEX idx_itens_pedido_pedido ON itens_pedido(pedido_id);
CREATE INDEX idx_logs_usuario ON logs_alteracoes(usuario_id);
CREATE INDEX idx_logs_tabela ON logs_alteracoes(tabela);
CREATE INDEX IF NOT EXISTS idx_gestores_escola ON gestores_escolares(escola_id);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_usuario ON logs_acesso(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_data ON logs_acesso(data_acesso);

-- ============================================
-- DADOS INICIAIS: usuários por email e tipo (evita duplicidade por conflito)
-- ============================================
INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
VALUES
    ('João Paulo Freitas da Silva', 'jpfreitass2005@gmail.com', NULL, 'administrador', TRUE),
    ('João Paulo Freitas da Silva', 'jpfreitass2005@gmail.com', NULL, 'escola', TRUE),
    ('João Paulo Freitas da Silva', 'jpfreitass2005@gmail.com', NULL, 'fornecedor', TRUE),
    ('João Paulo Freitas da Silva', 'jpfreitass2005@gmail.com', NULL, 'responsavel', TRUE),

    ('João Paulo Nunes da Silva', 'joaondss@class-one.com.br', NULL, 'administrador', TRUE),
    ('João Paulo Nunes da Silva', 'joaondss@class-one.com.br', NULL, 'escola', TRUE),
    ('João Paulo Nunes da Silva', 'joaondss@class-one.com.br', NULL, 'fornecedor', TRUE),
    ('João Paulo Nunes da Silva', 'joaondss@class-one.com.br', NULL, 'responsavel', TRUE),

    ('Murilo Souza Ramos', 'murilosr@outlook.com.br', NULL, 'administrador', TRUE),
    ('Murilo Souza Ramos', 'murilosr@outlook.com.br', NULL, 'escola', TRUE),
    ('Murilo Souza Ramos', 'murilosr@outlook.com.br', NULL, 'fornecedor', TRUE),
    ('Murilo Souza Ramos', 'murilosr@outlook.com.br', NULL, 'responsavel', TRUE),

    ('Yuri Henrique Rodrigues Silva', 'yurihenriquersilva343@gmail.com', NULL, 'administrador', TRUE),
    ('Yuri Henrique Rodrigues Silva', 'yurihenriquersilva343@gmail.com', NULL, 'escola', TRUE),
    ('Yuri Henrique Rodrigues Silva', 'yurihenriquersilva343@gmail.com', NULL, 'fornecedor', TRUE),
    ('Yuri Henrique Rodrigues Silva', 'yurihenriquersilva343@gmail.com', NULL, 'responsavel', TRUE),

    ('Victor de Castro Canela', 'victorccanela@gmail.com', NULL, 'administrador', TRUE),
    ('Victor de Castro Canela', 'victorccanela@gmail.com', NULL, 'escola', TRUE),
    ('Victor de Castro Canela', 'victorccanela@gmail.com', NULL, 'fornecedor', TRUE),
    ('Victor de Castro Canela', 'victorccanela@gmail.com', NULL, 'responsavel', TRUE)
ON CONFLICT (email, tipo) DO NOTHING;

-- ============================================
-- DADOS SIMULADOS: Fornecedores
-- ============================================
INSERT INTO fornecedores (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
SELECT usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo
FROM (VALUES
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'fornecedor'), '12.345.678/0001-90', 'Uniformes Class One LTDA', 'Rua das Américas, 1500', 'São Paulo', 'SP', '01234-567', TRUE),
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'fornecedor'), '98.765.432/0001-10', 'Confecções Moderna LTDA', 'Av. Paulista, 2500', 'São Paulo', 'SP', '01310-100', TRUE),
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), '11.222.333/0001-44', 'Uniformes Premium ME', 'Rua Augusta, 800', 'São Paulo', 'SP', '01305-000', TRUE)
) AS v(usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
WHERE NOT EXISTS (SELECT 1 FROM fornecedores WHERE usuario_id = v.usuario_id);

-- ============================================
-- DADOS SIMULADOS: Escolas
-- ============================================
INSERT INTO escolas (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
SELECT usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo
FROM (VALUES
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'escola'), '22.333.444/0001-55', 'Escola Estadual Visconde de São Leopoldo', 'Rua da Educação, 100', 'São Paulo', 'SP', '02345-678', TRUE),
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'escola'), '33.444.555/0001-66', 'Colégio Municipal Dom Pedro I', 'Av. Brasil, 3000', 'Rio de Janeiro', 'RJ', '20000-000', TRUE),
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'escola'), '44.555.666/0001-77', 'Instituto de Educação Anísio Teixeira', 'Rua do Saber, 500', 'Belo Horizonte', 'MG', '30130-000', TRUE),
    ((SELECT id FROM usuarios WHERE email = 'yurihenriquersilva343@gmail.com' AND tipo = 'escola'), '55.666.777/0001-88', 'Escola Técnica José de Freitas', 'Av. das Nações, 1200', 'Brasília', 'DF', '70000-000', TRUE)
) AS v(usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
WHERE NOT EXISTS (SELECT 1 FROM escolas WHERE usuario_id = v.usuario_id);

-- ============================================
-- DADOS SIMULADOS: Responsáveis
-- ============================================
INSERT INTO responsaveis (usuario_id, cpf, endereco, cidade, estado, cep)
SELECT usuario_id, cpf, endereco, cidade, estado, cep
FROM (VALUES
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'responsavel'), '123.456.789-00', 'Rua das Flores, 123', 'São Paulo', 'SP', '01234-567'),
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'responsavel'), '987.654.321-00', 'Av. Atlântica, 456', 'Rio de Janeiro', 'RJ', '22011-000'),
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'responsavel'), '111.222.333-44', 'Rua Bahia, 789', 'Belo Horizonte', 'MG', '30160-011'),
    ((SELECT id FROM usuarios WHERE email = 'yurihenriquersilva343@gmail.com' AND tipo = 'responsavel'), '555.666.777-88', 'SQN 305 Bloco A', 'Brasília', 'DF', '70735-010'),
    ((SELECT id FROM usuarios WHERE email = 'victorccanela@gmail.com' AND tipo = 'responsavel'), '444.555.666-77', 'Rua Oscar Freire, 321', 'São Paulo', 'SP', '01426-001')
) AS v(usuario_id, cpf, endereco, cidade, estado, cep)
WHERE NOT EXISTS (SELECT 1 FROM responsaveis WHERE usuario_id = v.usuario_id);

-- ============================================
-- DADOS SIMULADOS: Gestores Escolares
-- ============================================
INSERT INTO gestores_escolares (escola_id, nome, email, telefone, cpf, tipo_gestor)
SELECT escola_id, nome, email, telefone, cpf, tipo_gestor
FROM (VALUES
    ((SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Maria da Silva Santos', 'maria.santos@escola.sp.gov.br', '(11) 98765-4321', '111.222.333-44', 'diretor'),
    ((SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'José Carlos Oliveira', 'jose.oliveira@escola.sp.gov.br', '(11) 98765-4322', '222.333.444-55', 'coordenador'),
    ((SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 'Ana Paula Costa', 'ana.costa@escola.rj.gov.br', '(21) 97654-3210', '333.444.555-66', 'diretor'),
    ((SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 'Roberto Almeida', 'roberto.almeida@escola.mg.gov.br', '(31) 96543-2109', '444.555.666-77', 'financeiro'),
    ((SELECT id FROM escolas WHERE cnpj = '55.666.777/0001-88'), 'Fernanda Lima', 'fernanda.lima@escola.df.gov.br', '(61) 95432-1098', '555.666.777-88', 'coordenador')
) AS v(escola_id, nome, email, telefone, cpf, tipo_gestor)
WHERE v.escola_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM gestores_escolares WHERE cpf = v.cpf);

-- ============================================
-- DADOS SIMULADOS: Homologação de Fornecedores
-- ============================================
INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, data_homologacao, ativo, observacoes)
SELECT escola_id, fornecedor_id, CAST(data_homologacao AS TIMESTAMP), ativo, observacoes
FROM (VALUES
    ((SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), (SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), '2025-01-15 10:30:00', TRUE, 'Fornecedor homologado após análise de documentação e amostras'),
    ((SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), (SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), '2025-02-01 14:00:00', TRUE, 'Homologação aprovada'),
    ((SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), (SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), '2025-01-20 09:00:00', TRUE, 'Fornecedor aprovado para uniformes escolares'),
    ((SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), (SELECT id FROM fornecedores WHERE cnpj = '11.222.333/0001-44'), '2025-02-10 11:30:00', TRUE, 'Produtos de qualidade premium aprovados'),
    ((SELECT id FROM escolas WHERE cnpj = '55.666.777/0001-88'), (SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), '2025-03-01 16:00:00', TRUE, 'Homologado após período de teste')
) AS v(escola_id, fornecedor_id, data_homologacao, ativo, observacoes)
WHERE v.escola_id IS NOT NULL AND v.fornecedor_id IS NOT NULL;

-- ============================================
-- DADOS SIMULADOS: Produtos
-- ============================================
INSERT INTO produtos (fornecedor_id, escola_id, nome, descricao, categoria, tamanho, cor, preco, estoque, ativo)
SELECT fornecedor_id, escola_id, nome, descricao, categoria, tamanho, cor, preco, estoque, ativo
FROM (VALUES
    -- Produtos do Fornecedor Class One
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Camisa Polo Escolar', 'Camisa polo em malha PV com bordado', 'Camisa', 'P', 'Azul Marinho', 45.90, 150, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Camisa Polo Escolar', 'Camisa polo em malha PV com bordado', 'Camisa', 'M', 'Azul Marinho', 45.90, 200, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Camisa Polo Escolar', 'Camisa polo em malha PV com bordado', 'Camisa', 'G', 'Azul Marinho', 45.90, 180, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Calça Escolar', 'Calça em sarja com elastano', 'Calça', 'P', 'Cinza', 65.00, 100, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Calça Escolar', 'Calça em sarja com elastano', 'Calça', 'M', 'Cinza', 65.00, 120, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Calça Escolar', 'Calça em sarja com elastano', 'Calça', 'G', 'Cinza', 65.00, 95, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 'Camiseta Educação Física', 'Camiseta em dry fit', 'Camiseta', 'M', 'Branca', 38.50, 200, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '12.345.678/0001-90'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 'Bermuda Educação Física', 'Bermuda em tactel', 'Bermuda', 'M', 'Preta', 42.00, 150, TRUE),
    
    -- Produtos do Fornecedor Confecções Moderna
    ((SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 'Camisa Social Escolar', 'Camisa social manga longa', 'Camisa', 'M', 'Branca', 52.00, 80, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 'Saia Escolar', 'Saia pregueada em tecido tropical', 'Saia', 'P', 'Azul Marinho', 48.90, 60, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 'Saia Escolar', 'Saia pregueada em tecido tropical', 'Saia', 'M', 'Azul Marinho', 48.90, 70, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '98.765.432/0001-10'), (SELECT id FROM escolas WHERE cnpj = '55.666.777/0001-88'), 'Jaqueta Escolar', 'Jaqueta em moletom com capuz', 'Agasalho', 'G', 'Azul', 89.90, 50, TRUE),
    
    -- Produtos do Fornecedor Uniformes Premium
    ((SELECT id FROM fornecedores WHERE cnpj = '11.222.333/0001-44'), (SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 'Camisa Polo Premium', 'Camisa polo premium em piquet', 'Camisa', 'P', 'Bordô', 75.00, 90, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '11.222.333/0001-44'), (SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 'Camisa Polo Premium', 'Camisa polo premium em piquet', 'Camisa', 'M', 'Bordô', 75.00, 110, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '11.222.333/0001-44'), (SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 'Calça Social Premium', 'Calça social alfaiataria', 'Calça', 'M', 'Preta', 95.00, 70, TRUE),
    ((SELECT id FROM fornecedores WHERE cnpj = '11.222.333/0001-44'), (SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 'Mochila Escolar', 'Mochila reforçada com porta notebook', 'Acessório', 'Único', 'Cinza', 120.00, 40, TRUE)
) AS v(fornecedor_id, escola_id, nome, descricao, categoria, tamanho, cor, preco, estoque, ativo)
WHERE v.fornecedor_id IS NOT NULL AND v.escola_id IS NOT NULL;

-- ============================================
-- DADOS SIMULADOS: Pedidos
-- ============================================
INSERT INTO pedidos (responsavel_id, escola_id, valor_total, status, data_pedido, observacoes)
SELECT responsavel_id, escola_id, valor_total, status, CAST(data_pedido AS TIMESTAMP), observacoes
FROM (VALUES
    ((SELECT id FROM responsaveis WHERE cpf = '123.456.789-00'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 111.80, 'entregue', '2025-03-15 10:30:00', 'Pedido entregue conforme prazo'),
    ((SELECT id FROM responsaveis WHERE cpf = '123.456.789-00'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 130.00, 'pago', '2025-10-20 14:15:00', 'Aguardando separação'),
    ((SELECT id FROM responsaveis WHERE cpf = '987.654.321-00'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 80.50, 'enviado', '2025-10-18 09:00:00', 'Em rota de entrega'),
    ((SELECT id FROM responsaveis WHERE cpf = '111.222.333-44'), (SELECT id FROM escolas WHERE cnpj = '44.555.666/0001-77'), 215.00, 'entregue', '2025-09-10 11:20:00', 'Cliente satisfeito'),
    ((SELECT id FROM responsaveis WHERE cpf = '555.666.777-88'), (SELECT id FROM escolas WHERE cnpj = '55.666.777/0001-88'), 89.90, 'pago', '2025-11-05 16:45:00', 'Pagamento confirmado'),
    ((SELECT id FROM responsaveis WHERE cpf = '444.555.666-77'), (SELECT id FROM escolas WHERE cnpj = '22.333.444/0001-55'), 91.80, 'pendente', '2025-11-08 08:30:00', 'Aguardando pagamento'),
    ((SELECT id FROM responsaveis WHERE cpf = '987.654.321-00'), (SELECT id FROM escolas WHERE cnpj = '33.444.555/0001-66'), 52.00, 'cancelado', '2025-10-01 12:00:00', 'Cancelado a pedido do cliente')
) AS v(responsavel_id, escola_id, valor_total, status, data_pedido, observacoes)
WHERE v.responsavel_id IS NOT NULL AND v.escola_id IS NOT NULL;

-- ============================================
-- DADOS SIMULADOS: Itens de Pedido
-- ============================================
INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
SELECT pedido_id, produto_id, quantidade, preco_unitario, subtotal
FROM (VALUES
    -- Pedido 1 (Responsável João Paulo)
    (1, (SELECT id FROM produtos WHERE nome = 'Camisa Polo Escolar' AND tamanho = 'M' LIMIT 1), 1, 45.90, 45.90),
    (1, (SELECT id FROM produtos WHERE nome = 'Calça Escolar' AND tamanho = 'M' LIMIT 1), 1, 65.00, 65.00),
    
    -- Pedido 2 (Responsável João Paulo - segundo pedido)
    (2, (SELECT id FROM produtos WHERE nome = 'Calça Escolar' AND tamanho = 'M' LIMIT 1), 2, 65.00, 130.00),
    
    -- Pedido 3 (Responsável João Nunes)
    (3, (SELECT id FROM produtos WHERE nome = 'Camiseta Educação Física' LIMIT 1), 1, 38.50, 38.50),
    (3, (SELECT id FROM produtos WHERE nome = 'Bermuda Educação Física' LIMIT 1), 1, 42.00, 42.00),
    
    -- Pedido 4 (Responsável Murilo)
    (4, (SELECT id FROM produtos WHERE nome = 'Camisa Polo Premium' AND tamanho = 'M' LIMIT 1), 1, 75.00, 75.00),
    (4, (SELECT id FROM produtos WHERE nome = 'Calça Social Premium' LIMIT 1), 1, 95.00, 95.00),
    (4, (SELECT id FROM produtos WHERE nome = 'Camisa Polo Escolar' AND tamanho = 'P' LIMIT 1), 1, 45.90, 45.90),
    
    -- Pedido 5 (Responsável Yuri)
    (5, (SELECT id FROM produtos WHERE nome = 'Jaqueta Escolar' LIMIT 1), 1, 89.90, 89.90),
    
    -- Pedido 6 (Responsável Victor)
    (6, (SELECT id FROM produtos WHERE nome = 'Camisa Polo Escolar' AND tamanho = 'G' LIMIT 1), 2, 45.90, 91.80),
    
    -- Pedido 7 (Cancelado)
    (7, (SELECT id FROM produtos WHERE nome = 'Camisa Social Escolar' LIMIT 1), 1, 52.00, 52.00)
) AS v(pedido_id, produto_id, quantidade, preco_unitario, subtotal)
WHERE v.pedido_id IS NOT NULL AND v.produto_id IS NOT NULL;

-- ============================================
-- DADOS SIMULADOS: Logs de Acesso
-- ============================================
INSERT INTO logs_acesso (usuario_id, acao, tipo_autenticacao, data_acesso, ip_usuario, user_agent, sucesso, descricao)
SELECT usuario_id, acao, tipo_autenticacao, CAST(data_acesso AS TIMESTAMP), ip_usuario, user_agent, sucesso, descricao
FROM (VALUES
    -- Acessos do administrador João Paulo
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'LOGIN', 'codigo', '2025-11-09 08:00:00', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', TRUE, 'Login bem-sucedido via código'),
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'LOGOFF', NULL, '2025-11-09 12:30:00', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', TRUE, 'Logout normal'),
    
    -- Acessos do fornecedor Murilo
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), 'LOGIN', 'codigo', '2025-11-08 09:15:00', '192.168.1.105', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', TRUE, 'Acesso para cadastrar produtos'),
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), 'LOGOFF', NULL, '2025-11-08 11:45:00', '192.168.1.105', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', TRUE, 'Sessão encerrada'),
    
    -- Acessos da escola João Nunes
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'escola'), 'LOGIN', 'codigo', '2025-11-07 10:00:00', '192.168.1.110', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', TRUE, 'Acesso para homologar fornecedor'),
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'escola'), 'LOGOFF', NULL, '2025-11-07 10:45:00', '192.168.1.110', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', TRUE, 'Logout'),
    
    -- Acessos do responsável Yuri
    ((SELECT id FROM usuarios WHERE email = 'yurihenriquersilva343@gmail.com' AND tipo = 'responsavel'), 'LOGIN', 'codigo', '2025-11-05 16:30:00', '192.168.1.120', 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)', TRUE, 'Login via mobile'),
    ((SELECT id FROM usuarios WHERE email = 'yurihenriquersilva343@gmail.com' AND tipo = 'responsavel'), 'LOGOFF', NULL, '2025-11-05 16:50:00', '192.168.1.120', 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)', TRUE, 'Logout após realizar pedido'),
    
    -- Tentativa de login falhada
    ((SELECT id FROM usuarios WHERE email = 'victorccanela@gmail.com' AND tipo = 'responsavel'), 'LOGIN', 'codigo', '2025-11-08 20:00:00', '192.168.1.130', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', FALSE, 'Código inválido'),
    ((SELECT id FROM usuarios WHERE email = 'victorccanela@gmail.com' AND tipo = 'responsavel'), 'LOGIN', 'codigo', '2025-11-08 20:05:00', '192.168.1.130', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', TRUE, 'Login bem-sucedido após segunda tentativa')
) AS v(usuario_id, acao, tipo_autenticacao, data_acesso, ip_usuario, user_agent, sucesso, descricao)
WHERE v.usuario_id IS NOT NULL;

-- ============================================
-- DADOS SIMULADOS: Logs de Alterações
-- ============================================
INSERT INTO logs_alteracoes (usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, data_alteracao, ip_usuario, descricao)
SELECT usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, CAST(data_alteracao AS TIMESTAMP), ip_usuario, descricao
FROM (VALUES
    -- Cadastro de fornecedor
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'fornecedores', 1, 'INSERT', NULL, '{"razao_social": "Uniformes Class One LTDA", "cnpj": "12.345.678/0001-90"}', '2025-01-10 10:00:00', '192.168.1.100', 'Cadastro de novo fornecedor'),
    
    -- Cadastro de escola
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'escolas', 1, 'INSERT', NULL, '{"razao_social": "Escola Estadual Visconde de São Leopoldo", "cnpj": "22.333.444/0001-55"}', '2025-01-12 11:30:00', '192.168.1.100', 'Nova escola cadastrada no sistema'),
    
    -- Homologação de fornecedor
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'escola'), 'homologacao_fornecedores', 1, 'INSERT', NULL, '{"escola_id": 1, "fornecedor_id": 1, "ativo": true}', '2025-01-15 10:30:00', '192.168.1.110', 'Fornecedor homologado pela escola'),
    
    -- Cadastro de produto
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), 'produtos', 1, 'INSERT', NULL, '{"nome": "Camisa Polo Escolar", "preco": 45.90, "estoque": 150}', '2025-02-01 09:00:00', '192.168.1.105', 'Novo produto cadastrado'),
    
    -- Atualização de estoque
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), 'produtos', 1, 'UPDATE', '{"estoque": 150}', '{"estoque": 148}', '2025-03-15 10:35:00', '192.168.1.105', 'Estoque atualizado após pedido'),
    
    -- Criação de pedido
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'responsavel'), 'pedidos', 1, 'INSERT', NULL, '{"valor_total": 111.80, "status": "pendente"}', '2025-03-15 10:30:00', '192.168.1.100', 'Novo pedido criado'),
    
    -- Atualização de status de pedido
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'pedidos', 1, 'UPDATE', '{"status": "pendente"}', '{"status": "pago"}', '2025-03-15 14:00:00', '192.168.1.100', 'Status do pedido atualizado para pago'),
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'pedidos', 1, 'UPDATE', '{"status": "pago"}', '{"status": "enviado"}', '2025-03-18 09:00:00', '192.168.1.100', 'Pedido enviado para entrega'),
    ((SELECT id FROM usuarios WHERE email = 'jpfreitass2005@gmail.com' AND tipo = 'administrador'), 'pedidos', 1, 'UPDATE', '{"status": "enviado"}', '{"status": "entregue"}', '2025-03-20 15:30:00', '192.168.1.100', 'Pedido entregue ao cliente'),
    
    -- Cancelamento de pedido
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'responsavel'), 'pedidos', 7, 'UPDATE', '{"status": "pendente"}', '{"status": "cancelado"}', '2025-10-01 12:30:00', '192.168.1.110', 'Pedido cancelado a pedido do cliente'),
    
    -- Edição de dados de escola
    ((SELECT id FROM usuarios WHERE email = 'joaondss@class-one.com.br' AND tipo = 'escola'), 'escolas', 2, 'UPDATE', '{"telefone": null}', '{"telefone": "(21) 3333-4444"}', '2025-10-15 10:00:00', '192.168.1.110', 'Telefone da escola atualizado'),
    
    -- Atualização de preço de produto
    ((SELECT id FROM usuarios WHERE email = 'murilosr@outlook.com.br' AND tipo = 'fornecedor'), 'produtos', 5, 'UPDATE', '{"preco": 65.00}', '{"preco": 62.50}', '2025-11-01 08:00:00', '192.168.1.105', 'Preço atualizado - promoção')
) AS v(usuario_id, tabela, registro_id, acao, dados_antigos, dados_novos, data_alteracao, ip_usuario, descricao)
WHERE v.usuario_id IS NOT NULL;