-- ============================================
-- CONECTA UNIFORME - SCHEMA DO BANCO DE DADOS
-- ============================================
-- Este arquivo contém todas as tabelas necessárias para o sistema
-- Execute este script no PostgreSQL para criar o banco de dados

-- Criar o banco de dados (execute separadamente se necessário)
-- CREATE DATABASE conecta_uniforme;

-- ============================================
-- TABELA: usuarios
-- Armazena todos os usuários do sistema
-- Tipos: 'administrador', 'escola', 'fornecedor', 'responsavel'
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('administrador', 'escola', 'fornecedor', 'responsavel')),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
-- TABELA: sessoes
-- Armazena as sessões ativas dos usuários
-- ============================================
CREATE TABLE IF NOT EXISTS sessoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    token VARCHAR(100) UNIQUE NOT NULL,
    data_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
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
-- TABELA: repasses_financeiros
-- Armazena os repasses financeiros para fornecedores
-- Status: 'pendente', 'processando', 'concluido', 'cancelado'
-- ============================================
CREATE TABLE IF NOT EXISTS repasses_financeiros (
    id SERIAL PRIMARY KEY,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE RESTRICT,
    pedido_id INTEGER REFERENCES pedidos(id) ON DELETE RESTRICT,
    valor DECIMAL(10, 2) NOT NULL,
    taxa_plataforma DECIMAL(10, 2) DEFAULT 0.00,
    valor_liquido DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'processando', 'concluido', 'cancelado')),
    data_repasse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP,
    observacoes TEXT
);

-- ============================================
-- TABELA: logs_alteracoes
-- Registra todas as alterações importantes no sistema
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
-- ÍNDICES PARA MELHORAR PERFORMANCE
-- ============================================
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_tipo ON usuarios(tipo);
CREATE INDEX idx_codigos_acesso_usuario ON codigos_acesso(usuario_id);
CREATE INDEX idx_sessoes_usuario ON sessoes(usuario_id);
CREATE INDEX idx_sessoes_token ON sessoes(token);
CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_produtos_escola ON produtos(escola_id);
CREATE INDEX idx_pedidos_responsavel ON pedidos(responsavel_id);
CREATE INDEX idx_pedidos_status ON pedidos(status);
CREATE INDEX idx_itens_pedido_pedido ON itens_pedido(pedido_id);
CREATE INDEX idx_repasses_fornecedor ON repasses_financeiros(fornecedor_id);
CREATE INDEX idx_logs_usuario ON logs_alteracoes(usuario_id);
CREATE INDEX idx_logs_tabela ON logs_alteracoes(tabela);

-- ============================================
-- INSERIR USUÁRIO ADMINISTRADOR PADRÃO
-- ============================================
-- Email: admin@conectauniforme.com.br
-- O código de acesso será enviado por email ao fazer login
INSERT INTO usuarios (nome, email, telefone, tipo, ativo) 
VALUES ('Administrador', 'admin@conectauniforme.com.br', '(00) 00000-0000', 'administrador', TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- INSERIR USUÁRIOS DE EXEMPLO (ESCOLA, FORNECEDOR, RESPONSÁVEL)
-- ============================================
-- Escola
INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
VALUES ('Escola Municipal Central', 'diretoria@emcentral.edu.br', '(11) 2345-6789', 'escola', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Fornecedor
INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
VALUES ('Uniformes Alpha Ltda', 'contato@uniformesalpha.com.br', '(11) 99876-5432', 'fornecedor', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Responsável
INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
VALUES ('Maria dos Santos', 'maria.santos+responsavel@example.com', '(11) 91234-5678', 'responsavel', TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- PERFIS VINCULADOS (detalhes) USANDO os usuários acima
-- Esses inserts usam subselect para obter o id do usuário por email
-- São idempotentes por causa do UNIQUE (usuario_id) e chaves únicas secundárias
-- ============================================

-- Detalhes da escola
INSERT INTO escolas (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
SELECT u.id, '12.345.678/0001-90', 'Escola Municipal Central', 'Rua das Flores, 123', 'São Paulo', 'SP', '01000-000', TRUE
FROM usuarios u WHERE u.email = 'diretoria@emcentral.edu.br'
ON CONFLICT (usuario_id) DO NOTHING;

-- Detalhes do fornecedor
INSERT INTO fornecedores (usuario_id, cnpj, razao_social, endereco, cidade, estado, cep, ativo)
SELECT u.id, '98.765.432/0001-10', 'Uniformes Alpha Ltda', 'Av. Industrial, 456', 'São Paulo', 'SP', '02000-000', TRUE
FROM usuarios u WHERE u.email = 'contato@uniformesalpha.com.br'
ON CONFLICT (usuario_id) DO NOTHING;

-- Detalhes do responsável
INSERT INTO responsaveis (usuario_id, cpf, endereco, cidade, estado, cep)
SELECT u.id, '123.456.789-09', 'Rua das Acácias, 789', 'São Paulo', 'SP', '03000-000'
FROM usuarios u WHERE u.email = 'maria.santos+responsavel@example.com'
ON CONFLICT (usuario_id) DO NOTHING;

-- Opcional: homologar o fornecedor para a escola (facilita navegação)
INSERT INTO homologacao_fornecedores (escola_id, fornecedor_id, ativo, observacoes)
SELECT e.id, f.id, TRUE, 'Fornecedor homologado para 2025.'
FROM escolas e
JOIN fornecedores f ON TRUE
WHERE e.razao_social = 'Escola Municipal Central' AND f.razao_social = 'Uniformes Alpha Ltda'
ON CONFLICT (escola_id, fornecedor_id) DO NOTHING;

-- ============================================
-- FIM DO SCHEMA
-- ============================================
