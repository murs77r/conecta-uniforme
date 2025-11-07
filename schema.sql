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
CREATE INDEX IF NOT EXISTS idx_gestores_escola ON gestores_escolares(escola_id);

-- ============================================
-- TABELA: webauthn_credentials
-- Armazena credenciais Passkey/WebAuthn vinculadas a usuários
-- Cada usuário pode ter múltiplas credenciais (ex: notebook, celular)
-- ============================================
CREATE TABLE IF NOT EXISTS webauthn_credentials (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    credential_id VARCHAR(200) UNIQUE NOT NULL, -- Base64URL do ID da credencial
    public_key VARCHAR(500) NOT NULL,           -- Base64URL da chave pública (COSE public key)
    sign_count INTEGER DEFAULT 0,               -- Contador para proteção de replay
    transports VARCHAR(200),                    -- JSON com transports (ex: ["internal"])
    backup_eligible BOOLEAN DEFAULT FALSE,      -- Se o autenticador é elegível a backup
    backup_state BOOLEAN DEFAULT FALSE,         -- Se o backup está efetivamente em uso
    aaguid VARCHAR(50),                         -- Identificador do autenticador
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_uso TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_webauthn_usuario ON webauthn_credentials(usuario_id);

-- ============================================
-- DADOS INICIAIS: usuários por email e tipo (evita duplicidade por conflito)
-- ============================================
INSERT INTO usuarios (nome, email, telefone, tipo, ativo)
VALUES
    ('jpfreitass2005', 'jpfreitass2005@gmail.com', NULL, 'administrador', TRUE),
    ('jpfreitass2005', 'jpfreitass2005@gmail.com', NULL, 'escola', TRUE),
    ('jpfreitass2005', 'jpfreitass2005@gmail.com', NULL, 'fornecedor', TRUE),
    ('jpfreitass2005', 'jpfreitass2005@gmail.com', NULL, 'responsavel', TRUE),

    ('joaondss', 'joaondss@class-one.com.br', NULL, 'administrador', TRUE),
    ('joaondss', 'joaondss@class-one.com.br', NULL, 'escola', TRUE),
    ('joaondss', 'joaondss@class-one.com.br', NULL, 'fornecedor', TRUE),
    ('joaondss', 'joaondss@class-one.com.br', NULL, 'responsavel', TRUE),

    ('murilosr', 'murilosr@outlook.com.br', NULL, 'administrador', TRUE),
    ('murilosr', 'murilosr@outlook.com.br', NULL, 'escola', TRUE),
    ('murilosr', 'murilosr@outlook.com.br', NULL, 'fornecedor', TRUE),
    ('murilosr', 'murilosr@outlook.com.br', NULL, 'responsavel', TRUE),

    ('yurihenriquersilva343', 'yurihenriquersilva343@gmail.com', NULL, 'administrador', TRUE),
    ('yurihenriquersilva343', 'yurihenriquersilva343@gmail.com', NULL, 'escola', TRUE),
    ('yurihenriquersilva343', 'yurihenriquersilva343@gmail.com', NULL, 'fornecedor', TRUE),
    ('yurihenriquersilva343', 'yurihenriquersilva343@gmail.com', NULL, 'responsavel', TRUE),

    ('victorccanela', 'victorccanela@gmail.com', NULL, 'administrador', TRUE),
    ('victorccanela', 'victorccanela@gmail.com', NULL, 'escola', TRUE),
    ('victorccanela', 'victorccanela@gmail.com', NULL, 'fornecedor', TRUE),
    ('victorccanela', 'victorccanela@gmail.com', NULL, 'responsavel', TRUE)
ON CONFLICT (email, tipo) DO NOTHING;