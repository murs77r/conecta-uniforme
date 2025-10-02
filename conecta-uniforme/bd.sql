create database conecta_uniformes;

use conecta_uniformes;

create table escola (
    id int primary key auto_increment not null,
    email varchar(80) not null,
    nome varchar(80) not null,
    cnpj varchar(14) not null,

    cep varchar(8),
    estado varchar(2),
    cidade varchar(80),
    endereco varchar(80),
    complemento varchar(80),

    cod_acesso char(11) not null /* Código gerado que permite acesso aos alunos */
);