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
"""
