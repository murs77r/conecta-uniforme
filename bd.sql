CREATE DATABASE IF NOT EXISTS conecta_uniforme;

USE conecta_uniforme;

CREATE TABLE IF NOT EXISTS escola (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(18) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    cep VARCHAR(9),
    estado VARCHAR(2),
    cidade VARCHAR(100),
    endereco VARCHAR(200),
    complemento VARCHAR(100),
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de gestores escolares
CREATE TABLE IF NOT EXISTS gestor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    escola_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_gestor_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE
);

-- Tabela de administradores do sistema
CREATE TABLE IF NOT EXISTS administrador (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de fornecedores
CREATE TABLE IF NOT EXISTS fornecedor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    cnpj VARCHAR(18),
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de homologação (escola x Fornecedor)
CREATE TABLE IF NOT EXISTS homologacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    escola_id INT NOT NULL,
    fornecedor_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    data_homologacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_homologacao_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE,
    CONSTRAINT fk_homologacao_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES fornecedor(id) ON DELETE CASCADE,
    UNIQUE (escola_id, fornecedor_id)
);

-- Tabela de alunos
CREATE TABLE IF NOT EXISTS aluno (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    matricula VARCHAR(50) NOT NULL,
    escola_id INT NOT NULL,
    serie VARCHAR(50) NOT NULL,
    genero ENUM('Masculino', 'Feminino', 'Unissex') NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_aluno_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE,
    UNIQUE (escola_id, matricula)
);

-- Tabela de responsáveis
CREATE TABLE IF NOT EXISTS responsavel (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    aluno_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_responsavel_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id) ON DELETE CASCADE
);

-- Tabela de códigos de acesso (login sem senha)
CREATE TABLE IF NOT EXISTS codigo_acesso (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    tipo_usuario ENUM('Gestor', 'Fornecedor', 'Responsável', 'Administrador') NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expira_em TIMESTAMP NOT NULL,
    usado TINYINT(1) DEFAULT 0,
    INDEX idx_email_codigo (email, codigo),
    INDEX idx_expira (expira_em)
);

-- Tabela de produtos (uniformes)
CREATE TABLE IF NOT EXISTS produto (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fornecedor_id INT NOT NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_produto_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES fornecedor(id) ON DELETE CASCADE
);

-- Tabela de homologação de produtos (produto x escola x série)
CREATE TABLE IF NOT EXISTS produto_homologacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    produto_id INT NOT NULL,
    escola_id INT NOT NULL,
    serie VARCHAR(50) NOT NULL,
    CONSTRAINT fk_prod_homolog_produto FOREIGN KEY (produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    CONSTRAINT fk_prod_homolog_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE,
    UNIQUE (produto_id, escola_id, serie)
);

-- Tabela de variações de produtos (tamanho, cor, gênero)
CREATE TABLE IF NOT EXISTS produto_variacao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    produto_id INT NOT NULL,
    tamanho VARCHAR(10) NOT NULL,
    cor VARCHAR(50),
    genero ENUM('Masculino', 'Feminino', 'Unissex') NOT NULL,
    quantidade_estoque INT DEFAULT 0,
    CONSTRAINT fk_variacao_produto FOREIGN KEY (produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    UNIQUE (produto_id, tamanho, cor, genero)
);

-- Tabela de pedidos
CREATE TABLE IF NOT EXISTS pedido (
    id INT PRIMARY KEY AUTO_INCREMENT,
    responsavel_id INT NOT NULL,
    aluno_id INT NOT NULL,
    escola_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    comissao DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('Pendente', 'Aprovado', 'Em Produção', 'Disponível para Retirar', 'Entregue', 'Cancelado') DEFAULT 'Pendente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedido_responsavel FOREIGN KEY (responsavel_id) REFERENCES responsavel(id),
    CONSTRAINT fk_pedido_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id),
    CONSTRAINT fk_pedido_escola FOREIGN KEY (escola_id) REFERENCES escola(id)
);

-- Tabela de itens do pedido
CREATE TABLE IF NOT EXISTS pedido_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,
    variacao_id INT NOT NULL,
    fornecedor_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_item_pedido FOREIGN KEY (pedido_id) REFERENCES pedido(id) ON DELETE CASCADE,
    CONSTRAINT fk_item_produto FOREIGN KEY (produto_id) REFERENCES produto(id),
    CONSTRAINT fk_item_variacao FOREIGN KEY (variacao_id) REFERENCES produto_variacao(id),
    CONSTRAINT fk_item_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES fornecedor(id)
);

-- Tabela de carrinho temporário
CREATE TABLE IF NOT EXISTS carrinho (
    id INT PRIMARY KEY AUTO_INCREMENT,
    responsavel_id INT NOT NULL,
    produto_id INT NOT NULL,
    variacao_id INT NOT NULL,
    quantidade INT NOT NULL,
    adicionado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrinho_responsavel FOREIGN KEY (responsavel_id) REFERENCES responsavel(id) ON DELETE CASCADE,
    CONSTRAINT fk_carrinho_produto FOREIGN KEY (produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    CONSTRAINT fk_carrinho_variacao FOREIGN KEY (variacao_id) REFERENCES produto_variacao(id) ON DELETE CASCADE
);

-- Tabela de comissões
CREATE TABLE IF NOT EXISTS comissao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fornecedor_id INT NOT NULL,
    mes_referencia DATE NOT NULL,
    total_vendas DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_comissao DECIMAL(10,2) NOT NULL DEFAULT 0,
    valor_liquido DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('Pendente', 'Pago') DEFAULT 'Pendente',
    data_pagamento DATE NULL,
    valor_pago DECIMAL(10,2) NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comissao_fornecedor FOREIGN KEY (fornecedor_id) REFERENCES fornecedor(id),
    UNIQUE (fornecedor_id, mes_referencia)
);

-- Tabela de auditoria
CREATE TABLE IF NOT EXISTS auditoria (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tabela VARCHAR(100) NOT NULL,
    operacao ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    registro_id VARCHAR(255),
    dados_anteriores JSON,
    dados_atualizados JSON,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responsavel VARCHAR(255) NOT NULL
);


/* CÓDIGO PARA GERAR AS TRIGGERS DE AUDITORIA. DEVE SER RODADO AO FINAL DE TUDO */
-- =====================================================================
-- GATILHOS PARA A TABELA: administrador
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_administrador;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_administrador
AFTER INSERT ON `administrador`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, responsavel)
    VALUES (
    'administrador',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_administrador;
DELIMITER $$
CREATE TRIGGER trig_audit_update_administrador
AFTER UPDATE ON `administrador`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, responsavel)
    VALUES (
    'administrador',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_administrador;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_administrador
AFTER DELETE ON `administrador`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, responsavel)
    VALUES (
    'administrador',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: fornecedor
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_fornecedor;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_fornecedor
AFTER INSERT ON `fornecedor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, responsavel)
    VALUES (
    'fornecedor',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'cnpj', NEW.cnpj,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_fornecedor;
DELIMITER $$
CREATE TRIGGER trig_audit_update_fornecedor
AFTER UPDATE ON `fornecedor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, responsavel)
    VALUES (
    'fornecedor',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'cnpj', OLD.cnpj,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'cnpj', NEW.cnpj,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_fornecedor;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_fornecedor
AFTER DELETE ON `fornecedor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, responsavel)
    VALUES (
    'fornecedor',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'cnpj', OLD.cnpj,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: gestor
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_gestor;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_gestor
AFTER INSERT ON `gestor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, responsavel)
    VALUES (
    'gestor',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_gestor;
DELIMITER $$
CREATE TRIGGER trig_audit_update_gestor
AFTER UPDATE ON `gestor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, responsavel)
    VALUES (
    'gestor',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_gestor;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_gestor
AFTER DELETE ON `gestor`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, responsavel)
    VALUES (
    'gestor',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: responsavel
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_responsavel;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_responsavel
AFTER INSERT ON `responsavel`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
    'responsavel',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'aluno_id', NEW.aluno_id,
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_responsavel;
DELIMITER $$
CREATE TRIGGER trig_audit_update_responsavel
AFTER UPDATE ON `responsavel`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
    'responsavel',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'aluno_id', OLD.aluno_id,
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        JSON_OBJECT(
            'aluno_id', NEW.aluno_id,
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_responsavel;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_responsavel
AFTER DELETE ON `responsavel`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
    'responsavel',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'aluno_id', OLD.aluno_id,
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: aluno
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_aluno;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_aluno
AFTER INSERT ON `aluno`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'aluno',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'escola_id', NEW.escola_id,
            'genero', NEW.genero,
            'id', NEW.id,
            'matricula', NEW.matricula,
            'nome', NEW.nome,
            'serie', NEW.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_aluno;
DELIMITER $$
CREATE TRIGGER trig_audit_update_aluno
AFTER UPDATE ON `aluno`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'aluno',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'escola_id', OLD.escola_id,
            'genero', OLD.genero,
            'id', OLD.id,
            'matricula', OLD.matricula,
            'nome', OLD.nome,
            'serie', OLD.serie
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'escola_id', NEW.escola_id,
            'genero', NEW.genero,
            'id', NEW.id,
            'matricula', NEW.matricula,
            'nome', NEW.nome,
            'serie', NEW.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_aluno;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_aluno
AFTER DELETE ON `aluno`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'aluno',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'escola_id', OLD.escola_id,
            'genero', OLD.genero,
            'id', OLD.id,
            'matricula', OLD.matricula,
            'nome', OLD.nome,
            'serie', OLD.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: carrinho
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_carrinho;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_carrinho
AFTER INSERT ON `carrinho`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'carrinho',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'adicionado_em', NEW.adicionado_em,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'quantidade', NEW.quantidade,
            'responsavel_id', NEW.responsavel_id,
            'variacao_id', NEW.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_carrinho;
DELIMITER $$
CREATE TRIGGER trig_audit_update_carrinho
AFTER UPDATE ON `carrinho`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'carrinho',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'adicionado_em', OLD.adicionado_em,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'quantidade', OLD.quantidade,
            'responsavel_id', OLD.responsavel_id,
            'variacao_id', OLD.variacao_id
        ),
        JSON_OBJECT(
            'adicionado_em', NEW.adicionado_em,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'quantidade', NEW.quantidade,
            'responsavel_id', NEW.responsavel_id,
            'variacao_id', NEW.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_carrinho;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_carrinho
AFTER DELETE ON `carrinho`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'carrinho',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'adicionado_em', OLD.adicionado_em,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'quantidade', OLD.quantidade,
            'responsavel_id', OLD.responsavel_id,
            'variacao_id', OLD.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: codigo_acesso
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_codigo_acesso;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_codigo_acesso
AFTER INSERT ON `codigo_acesso`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'codigo_acesso',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'codigo', NEW.codigo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'expira_em', NEW.expira_em,
            'id', NEW.id,
            'tipo_usuario', NEW.tipo_usuario,
            'usado', NEW.usado
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_codigo_acesso;
DELIMITER $$
CREATE TRIGGER trig_audit_update_codigo_acesso
AFTER UPDATE ON `codigo_acesso`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'codigo_acesso',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'codigo', OLD.codigo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'expira_em', OLD.expira_em,
            'id', OLD.id,
            'tipo_usuario', OLD.tipo_usuario,
            'usado', OLD.usado
        ),
        JSON_OBJECT(
            'codigo', NEW.codigo,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'expira_em', NEW.expira_em,
            'id', NEW.id,
            'tipo_usuario', NEW.tipo_usuario,
            'usado', NEW.usado
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_codigo_acesso;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_codigo_acesso
AFTER DELETE ON `codigo_acesso`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'codigo_acesso',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'codigo', OLD.codigo,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'expira_em', OLD.expira_em,
            'id', OLD.id,
            'tipo_usuario', OLD.tipo_usuario,
            'usado', OLD.usado
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: comissao
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_comissao;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_comissao
AFTER INSERT ON `comissao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'comissao',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'criado_em', NEW.criado_em,
            'data_pagamento', NEW.data_pagamento,
            'fornecedor_id', NEW.fornecedor_id,
            'id', NEW.id,
            'mes_referencia', NEW.mes_referencia,
            'status', NEW.status,
            'total_comissao', NEW.total_comissao,
            'total_vendas', NEW.total_vendas,
            'valor_liquido', NEW.valor_liquido,
            'valor_pago', NEW.valor_pago
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_comissao;
DELIMITER $$
CREATE TRIGGER trig_audit_update_comissao
AFTER UPDATE ON `comissao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'comissao',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'criado_em', OLD.criado_em,
            'data_pagamento', OLD.data_pagamento,
            'fornecedor_id', OLD.fornecedor_id,
            'id', OLD.id,
            'mes_referencia', OLD.mes_referencia,
            'status', OLD.status,
            'total_comissao', OLD.total_comissao,
            'total_vendas', OLD.total_vendas,
            'valor_liquido', OLD.valor_liquido,
            'valor_pago', OLD.valor_pago
        ),
        JSON_OBJECT(
            'criado_em', NEW.criado_em,
            'data_pagamento', NEW.data_pagamento,
            'fornecedor_id', NEW.fornecedor_id,
            'id', NEW.id,
            'mes_referencia', NEW.mes_referencia,
            'status', NEW.status,
            'total_comissao', NEW.total_comissao,
            'total_vendas', NEW.total_vendas,
            'valor_liquido', NEW.valor_liquido,
            'valor_pago', NEW.valor_pago
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_comissao;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_comissao
AFTER DELETE ON `comissao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'comissao',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'criado_em', OLD.criado_em,
            'data_pagamento', OLD.data_pagamento,
            'fornecedor_id', OLD.fornecedor_id,
            'id', OLD.id,
            'mes_referencia', OLD.mes_referencia,
            'status', OLD.status,
            'total_comissao', OLD.total_comissao,
            'total_vendas', OLD.total_vendas,
            'valor_liquido', OLD.valor_liquido,
            'valor_pago', OLD.valor_pago
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: escola
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_escola;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_escola
AFTER INSERT ON `escola`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'escola',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'cep', NEW.cep,
            'cidade', NEW.cidade,
            'cnpj', NEW.cnpj,
            'complemento', NEW.complemento,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'endereco', NEW.endereco,
            'estado', NEW.estado,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_escola;
DELIMITER $$
CREATE TRIGGER trig_audit_update_escola
AFTER UPDATE ON `escola`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'escola',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'cep', OLD.cep,
            'cidade', OLD.cidade,
            'cnpj', OLD.cnpj,
            'complemento', OLD.complemento,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'endereco', OLD.endereco,
            'estado', OLD.estado,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'cep', NEW.cep,
            'cidade', NEW.cidade,
            'cnpj', NEW.cnpj,
            'complemento', NEW.complemento,
            'criado_em', NEW.criado_em,
            'email', NEW.email,
            'endereco', NEW.endereco,
            'estado', NEW.estado,
            'id', NEW.id,
            'nome', NEW.nome,
            'telefone', NEW.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_escola;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_escola
AFTER DELETE ON `escola`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'escola',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'cep', OLD.cep,
            'cidade', OLD.cidade,
            'cnpj', OLD.cnpj,
            'complemento', OLD.complemento,
            'criado_em', OLD.criado_em,
            'email', OLD.email,
            'endereco', OLD.endereco,
            'estado', OLD.estado,
            'id', OLD.id,
            'nome', OLD.nome,
            'telefone', OLD.telefone
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: homologacao
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_homologacao
AFTER INSERT ON `homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'homologacao',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'data_homologacao', NEW.data_homologacao,
            'escola_id', NEW.escola_id,
            'fornecedor_id', NEW.fornecedor_id,
            'id', NEW.id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_update_homologacao
AFTER UPDATE ON `homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'homologacao',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'data_homologacao', OLD.data_homologacao,
            'escola_id', OLD.escola_id,
            'fornecedor_id', OLD.fornecedor_id,
            'id', OLD.id
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'data_homologacao', NEW.data_homologacao,
            'escola_id', NEW.escola_id,
            'Fornecedor_id', NEW.Fornecedor_id,
            'id', NEW.id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_homologacao
AFTER DELETE ON `homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'homologacao',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'data_homologacao', OLD.data_homologacao,
            'escola_id', OLD.escola_id,
            'Fornecedor_id', OLD.Fornecedor_id,
            'id', OLD.id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: pedido
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_pedido;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_pedido
AFTER INSERT ON `pedido`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'pedido',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'aluno_id', NEW.aluno_id,
            'atualizado_em', NEW.atualizado_em,
            'comissao', NEW.comissao,
            'criado_em', NEW.criado_em,
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'responsavel_id', NEW.responsavel_id,
            'status', NEW.status,
            'total', NEW.total
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_pedido;
DELIMITER $$
CREATE TRIGGER trig_audit_update_pedido
AFTER UPDATE ON `pedido`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'pedido',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'aluno_id', OLD.aluno_id,
            'atualizado_em', OLD.atualizado_em,
            'comissao', OLD.comissao,
            'criado_em', OLD.criado_em,
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'responsavel_id', OLD.responsavel_id,
            'status', OLD.status,
            'total', OLD.total
        ),
        JSON_OBJECT(
            'aluno_id', NEW.aluno_id,
            'atualizado_em', NEW.atualizado_em,
            'comissao', NEW.comissao,
            'criado_em', NEW.criado_em,
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'responsavel_id', NEW.responsavel_id,
            'status', NEW.status,
            'total', NEW.total
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_pedido;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_pedido
AFTER DELETE ON `pedido`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'pedido',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'aluno_id', OLD.aluno_id,
            'atualizado_em', OLD.atualizado_em,
            'comissao', OLD.comissao,
            'criado_em', OLD.criado_em,
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'responsavel_id', OLD.responsavel_id,
            'status', OLD.status,
            'total', OLD.total
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: pedido_item
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_pedido_item;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_pedido_item
AFTER INSERT ON `pedido_item`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'pedido_item',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'Fornecedor_id', NEW.Fornecedor_id,
            'id', NEW.id,
            'pedido_id', NEW.pedido_id,
            'preco_unitario', NEW.preco_unitario,
            'produto_id', NEW.produto_id,
            'quantidade', NEW.quantidade,
            'subtotal', NEW.subtotal,
            'variacao_id', NEW.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_pedido_item;
DELIMITER $$
CREATE TRIGGER trig_audit_update_pedido_item
AFTER UPDATE ON `pedido_item`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'pedido_item',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'Fornecedor_id', OLD.Fornecedor_id,
            'id', OLD.id,
            'pedido_id', OLD.pedido_id,
            'preco_unitario', OLD.preco_unitario,
            'produto_id', OLD.produto_id,
            'quantidade', OLD.quantidade,
            'subtotal', OLD.subtotal,
            'variacao_id', OLD.variacao_id
        ),
        JSON_OBJECT(
            'Fornecedor_id', NEW.Fornecedor_id,
            'id', NEW.id,
            'pedido_id', NEW.pedido_id,
            'preco_unitario', NEW.preco_unitario,
            'produto_id', NEW.produto_id,
            'quantidade', NEW.quantidade,
            'subtotal', NEW.subtotal,
            'variacao_id', NEW.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_pedido_item;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_pedido_item
AFTER DELETE ON `pedido_item`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'pedido_item',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'Fornecedor_id', OLD.Fornecedor_id,
            'id', OLD.id,
            'pedido_id', OLD.pedido_id,
            'preco_unitario', OLD.preco_unitario,
            'produto_id', OLD.produto_id,
            'quantidade', OLD.quantidade,
            'subtotal', OLD.subtotal,
            'variacao_id', OLD.variacao_id
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: produto
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_produto;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_produto
AFTER INSERT ON `produto`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'produto',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'descricao', NEW.descricao,
            'Fornecedor_id', NEW.Fornecedor_id,
            'id', NEW.id,
            'nome', NEW.nome,
            'preco', NEW.preco
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_produto;
DELIMITER $$
CREATE TRIGGER trig_audit_update_produto
AFTER UPDATE ON `produto`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'produto',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'descricao', OLD.descricao,
            'Fornecedor_id', OLD.Fornecedor_id,
            'id', OLD.id,
            'nome', OLD.nome,
            'preco', OLD.preco
        ),
        JSON_OBJECT(
            'ativo', NEW.ativo,
            'criado_em', NEW.criado_em,
            'descricao', NEW.descricao,
            'Fornecedor_id', NEW.Fornecedor_id,
            'id', NEW.id,
            'nome', NEW.nome,
            'preco', NEW.preco
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_produto;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_produto
AFTER DELETE ON `produto`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'produto',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'ativo', OLD.ativo,
            'criado_em', OLD.criado_em,
            'descricao', OLD.descricao,
            'Fornecedor_id', OLD.Fornecedor_id,
            'id', OLD.id,
            'nome', OLD.nome,
            'preco', OLD.preco
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: produto_homologacao
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_produto_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_produto_homologacao
AFTER INSERT ON `produto_homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'produto_homologacao',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'serie', NEW.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_produto_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_update_produto_homologacao
AFTER UPDATE ON `produto_homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'produto_homologacao',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'serie', OLD.serie
        ),
        JSON_OBJECT(
            'escola_id', NEW.escola_id,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'serie', NEW.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_produto_homologacao;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_produto_homologacao
AFTER DELETE ON `produto_homologacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'produto_homologacao',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'escola_id', OLD.escola_id,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'serie', OLD.serie
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

-- =====================================================================
-- GATILHOS PARA A TABELA: produto_variacao
-- =====================================================================

DROP TRIGGER IF EXISTS trig_audit_insert_produto_variacao;
DELIMITER $$
CREATE TRIGGER trig_audit_insert_produto_variacao
AFTER INSERT ON `produto_variacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsavel)
    VALUES (
        'produto_variacao',
        'INSERT',
        NEW.id,
        JSON_OBJECT(
            'cor', NEW.cor,
            'genero', NEW.genero,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'quantidade_estoque', NEW.quantidade_estoque,
            'tamanho', NEW.tamanho
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_update_produto_variacao;
DELIMITER $$
CREATE TRIGGER trig_audit_update_produto_variacao
AFTER UPDATE ON `produto_variacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsavel)
    VALUES (
        'produto_variacao',
        'UPDATE',
        NEW.id,
        JSON_OBJECT(
            'cor', OLD.cor,
            'genero', OLD.genero,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'quantidade_estoque', OLD.quantidade_estoque,
            'tamanho', OLD.tamanho
        ),
        JSON_OBJECT(
            'cor', NEW.cor,
            'genero', NEW.genero,
            'id', NEW.id,
            'produto_id', NEW.produto_id,
            'quantidade_estoque', NEW.quantidade_estoque,
            'tamanho', NEW.tamanho
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trig_audit_delete_produto_variacao;
DELIMITER $$
CREATE TRIGGER trig_audit_delete_produto_variacao
AFTER DELETE ON `produto_variacao`
FOR EACH ROW
BEGIN
    INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsavel)
    VALUES (
        'produto_variacao',
        'DELETE',
        OLD.id,
        JSON_OBJECT(
            'cor', OLD.cor,
            'genero', OLD.genero,
            'id', OLD.id,
            'produto_id', OLD.produto_id,
            'quantidade_estoque', OLD.quantidade_estoque,
            'tamanho', OLD.tamanho
        ),
        COALESCE(@app_user, USER())
    );
END$$
DELIMITER ;