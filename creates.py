CREATE = """
CREATE TABLE IF NOT EXISTS Usuarios 
( 
 Id integer PRIMARY KEY AUTOINCREMENT, 
 Login varchar(30) not null unique,
 Senha varchar(30) not null,
 Nome varchar(30) not null,  
 Email varchar(30),  
 Telefone varchar(13),
 IP varchar(12)
);

CREATE TABLE IF NOT EXISTS Contatos
(
Id integer PRIMARY KEY,
Login varchar(30) not null,
Nome varchar(30) not null
);

CREATE TABLE IF NOT EXISTS Conversas
(
Id integer PRIMARY KEY AUTOINCREMENT,
IdContato integer not null,
Horario datetime not null,
Text varchar(500) not null
);
"""
