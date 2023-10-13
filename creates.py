CREATE = """
CREATE TABLE IF NOT EXISTS Usuarios 
( 
 Id integer PRIMARY KEY AUTOINCREMENT, 
 Nome varchar(30) not null,  
 Email varchar(30) unique,  
 Senha varchar(30) not null,
 Telefone varchar(13),
 IP varchar(12),
 DataHoraUltimoLogin datetime
);

CREATE TABLE IF NOT EXISTS Contatos
(
Id integer PRIMARY KEY,
Email varchar(30) not null,
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
