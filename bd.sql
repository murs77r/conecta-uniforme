CREATE DATABASE IF NOT EXISTS conecta_uniforme;

USE conecta_uniforme;

-- Tabela de escolas
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

-- Tabela de Gestores escolares
CREATE TABLE IF NOT EXISTS Gestor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    escola_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_Gestor_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE
);

-- Tabela de administradores do sistema
CREATE TABLE IF NOT EXISTS Administrador (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Fornecedores
CREATE TABLE IF NOT EXISTS Fornecedor (
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
    Fornecedor_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    data_homologacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_homologacao_escola FOREIGN KEY (escola_id) REFERENCES escola(id) ON DELETE CASCADE,
    CONSTRAINT fk_homologacao_Fornecedor FOREIGN KEY (Fornecedor_id) REFERENCES Fornecedor(id) ON DELETE CASCADE,
    UNIQUE (escola_id, Fornecedor_id)
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
CREATE TABLE IF NOT EXISTS Responsável (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    telefone VARCHAR(40),
    aluno_id INT NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_Responsável_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id) ON DELETE CASCADE
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
    Fornecedor_id INT NOT NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL,
    ativo TINYINT(1) DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_produto_Fornecedor FOREIGN KEY (Fornecedor_id) REFERENCES Fornecedor(id) ON DELETE CASCADE
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
    Responsável_id INT NOT NULL,
    aluno_id INT NOT NULL,
    escola_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    comissao DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('Pendente', 'Aprovado', 'Em Produção', 'Disponível para Retirar', 'Entregue', 'Cancelado') DEFAULT 'Pendente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedido_Responsável FOREIGN KEY (Responsável_id) REFERENCES Responsável(id),
    CONSTRAINT fk_pedido_aluno FOREIGN KEY (aluno_id) REFERENCES aluno(id),
    CONSTRAINT fk_pedido_escola FOREIGN KEY (escola_id) REFERENCES escola(id)
);

-- Tabela de itens do pedido
CREATE TABLE IF NOT EXISTS pedido_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,
    variacao_id INT NOT NULL,
    Fornecedor_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_item_pedido FOREIGN KEY (pedido_id) REFERENCES pedido(id) ON DELETE CASCADE,
    CONSTRAINT fk_item_produto FOREIGN KEY (produto_id) REFERENCES produto(id),
    CONSTRAINT fk_item_variacao FOREIGN KEY (variacao_id) REFERENCES produto_variacao(id),
    CONSTRAINT fk_item_Fornecedor FOREIGN KEY (Fornecedor_id) REFERENCES Fornecedor(id)
);

-- Tabela de carrinho temporário
CREATE TABLE IF NOT EXISTS carrinho (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Responsável_id INT NOT NULL,
    produto_id INT NOT NULL,
    variacao_id INT NOT NULL,
    quantidade INT NOT NULL,
    adicionado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrinho_Responsável FOREIGN KEY (Responsável_id) REFERENCES Responsável(id) ON DELETE CASCADE,
    CONSTRAINT fk_carrinho_produto FOREIGN KEY (produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    CONSTRAINT fk_carrinho_variacao FOREIGN KEY (variacao_id) REFERENCES produto_variacao(id) ON DELETE CASCADE
);

-- Tabela de comissões
CREATE TABLE IF NOT EXISTS comissao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Fornecedor_id INT NOT NULL,
    mes_referencia DATE NOT NULL,
    total_vendas DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_comissao DECIMAL(10,2) NOT NULL DEFAULT 0,
    valor_liquido DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('Pendente', 'Pago') DEFAULT 'Pendente',
    data_pagamento DATE NULL,
    valor_Pago DECIMAL(10,2) NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comissao_Fornecedor FOREIGN KEY (Fornecedor_id) REFERENCES Fornecedor(id),
    UNIQUE (Fornecedor_id, mes_referencia)
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
    Responsável VARCHAR(255) NOT NULL
);


/* CÓDIGO PARA GERAR, AUTOMATICAMENTE, AS TRIGGERS DE AUDITORIA. DEVE SER RODADO AO FINAL DE TUDO */
DELIMITER $$

CREATE PROCEDURE criar_gatilhos_auditoria()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE nome_tabela VARCHAR(100);
    DECLARE nome_pk VARCHAR(100);

    DECLARE cur_tabelas CURSOR FOR
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name != 'auditoria';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur_tabelas;

    loop_tabelas: LOOP
        FETCH cur_tabelas INTO nome_tabela;
        IF done THEN
            LEAVE loop_tabelas;
        END IF;

        SELECT kcu.column_name INTO nome_pk
        FROM information_schema.key_column_usage AS kcu
        JOIN information_schema.table_constraints AS tc
            ON kcu.constraint_name = tc.constraint_name
            AND kcu.table_schema = tc.table_schema
            AND kcu.table_name = tc.table_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND kcu.table_schema = DATABASE()
          AND kcu.table_name = nome_tabela
        LIMIT 1;

        IF nome_pk IS NULL THEN
            SET nome_pk = 'NULL';
        ELSE
            SET @pk_new = CONCAT('NEW.', nome_pk);
            SET @pk_old = CONCAT('OLD.', nome_pk);
        END IF;

        SET @colunas_new = (SELECT GROUP_CONCAT(CONCAT('\'', column_name, '\', ', 'NEW.', column_name))
                            FROM information_schema.columns
                            WHERE table_schema = DATABASE() AND table_name = nome_tabela);

        SET @colunas_old = (SELECT GROUP_CONCAT(CONCAT('\'', column_name, '\', ', 'OLD.', column_name))
                            FROM information_schema.columns
                            WHERE table_schema = DATABASE() AND table_name = nome_tabela);


        SET @sql_insert = CONCAT(
            'DROP TRIGGER IF EXISTS trig_audit_insert_', nome_tabela, ';',
            'CREATE TRIGGER trig_audit_insert_', nome_tabela, ' AFTER INSERT ON `', nome_tabela, '` FOR EACH ROW ',
            'BEGIN ',
            'INSERT INTO auditoria (tabela, operacao, registro_id, dados_atualizados, Responsável) ',
            'VALUES (\'', nome_tabela, '\', \'INSERT\', ', @pk_new, ', JSON_OBJECT(', @colunas_new, '), COALESCE(@app_user, USER()));',
            'END;'
        );
        PREPARE stmt FROM @sql_insert;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;


        SET @sql_update = CONCAT(
            'DROP TRIGGER IF EXISTS trig_audit_update_', nome_tabela, ';',
            'CREATE TRIGGER trig_audit_update_', nome_tabela, ' AFTER UPDATE ON `', nome_tabela, '` FOR EACH ROW ',
            'BEGIN ',
            'INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, dados_atualizados, Responsável) ',
            'VALUES (\'', nome_tabela, '\', \'UPDATE\', ', @pk_new, ', JSON_OBJECT(', @colunas_old, '), JSON_OBJECT(', @colunas_new, '), COALESCE(@app_user, USER()));',
            'END;'
        );
        PREPARE stmt FROM @sql_update;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;


        SET @sql_delete = CONCAT(
            'DROP TRIGGER IF EXISTS trig_audit_delete_', nome_tabela, ';',
            'CREATE TRIGGER trig_audit_delete_', nome_tabela, ' AFTER DELETE ON `', nome_tabela, '` FOR EACH ROW ',
            'BEGIN ',
            'INSERT INTO auditoria (tabela, operacao, registro_id, dados_anteriores, Responsável) ',
            'VALUES (\'', nome_tabela, '\', \'DELETE\', ', @pk_old, ', JSON_OBJECT(', @colunas_old, '), COALESCE(@app_user, USER()));',
            'END;'
        );
        PREPARE stmt FROM @sql_delete;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;    END LOOP;

    CLOSE cur_tabelas;
END$$

DELIMITER ;