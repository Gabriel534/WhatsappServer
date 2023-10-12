import sqlite3
from variaveis import DADOS
from creates import CREATE
from pathlib import Path
import re
import os


class SqlReader():
    def __init__(self, sql_path: str | Path, codigo_create: str | None = None) -> None:
        self.sql_path = Path(sql_path)
        try:
            connection = sqlite3.connect(self.sql_path)
        except sqlite3.OperationalError as error:
            if str(error) == "unable to open database file":
                os.mkdir(self.sql_path.parent)
                connection = sqlite3.connect(self.sql_path)
            else:
                raise error
        cursor = connection.cursor()
        if codigo_create is not None:
            comandos_create = re.findall(
                r'(?:CREATE TABLE IF NOT EXISTS).+?(?:\);)', codigo_create,
                flags=re.DOTALL)
            cont = 0
            for comando in comandos_create:
                cont += 1
                cursor.execute(comando)
                connection.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        # for comando in comandos_alter:
        #     cont += 1
        #     cursor.execute(comando)
        #     print(f"{cont}... ok")
        connection.commit()
        cursor.close()
        connection.close()

    def getInfo(self, table: str, id: int | None = None,
                key: list[str | int] | None = None) -> list[tuple]:
        """
        Retorna uma linha de uma tabela pelo Id.
        Se o id não for inserido, será retornado todas as linhas da tabela.
        Se quiser escolher qual chave buscar, coloque uma lista de 2 espaços na 
        "key=", sendo o primeiro o nome da coluna e o outro o valor que deseja 
        buscar
        """
        assert hasattr(self, "cursor"), "Favor inicializar a classe com \
 with para utilizar este comando"
        assert isinstance(table, str), "Formato de tabela deve ser uma string"
        assert isinstance(id, int | None), "ID deve ser um inteiro ou nada"
        assert isinstance(
            id, int | None), "key deve ser um dicionário ou nada"
        if key is not None:
            assert len(key) == 2, "Numero de argumentos incorretos"

        if id is None:
            if key:
                self.cursor.execute(
                    f'select * from "{table}" where {key[0]} = ?', [key[1]])
            else:
                self.cursor.execute(f'select * from "{table}"')
        elif id:
            self.cursor.execute(f'select * from "{table}" where Id = ?', [id])

        itens = list(self.cursor.fetchall())

        return itens

    def alterInfo(self, table: str, id: int, column: str, value: str) -> None:
        """
        Altera um valor de uma célula da tabela SQL escolhida pelo coluna e id 
        fornecidos.
        value: valor que deseja usar no lugar especificado
        """
        assert hasattr(self, "cursor"), "Favor inicializar a classe com \
 with para utilizar este comando"
        assert isinstance(table, str), "Formato de tabela deve ser uma string"
        assert isinstance(id, int), "ID deve ser um inteiro ou nada"
        assert isinstance(column, str), "column deve ser uma string"

        self.cursor.execute(
            f'update "{table}" set {column} = ? where Id = ?', [value, id])

    def delInfo(self, table: str, id: int) -> None:
        """
        Exclui uma linha da tabela pelo Id fornecido
        """
        assert hasattr(self, "cursor"), "Favor inicializar a classe com \
 with para utilizar este comando"
        assert isinstance(table, str), "Formato de tabela deve ser uma string"
        assert isinstance(id, int), "ID deve ser um inteiro ou nada"

        self.cursor.execute(
            f'delete from "{table}" where Id = ?', [id])

    def addInfo(self, table: str, **kwargs) -> None:
        """
        Adiciona informações a uma tabela escolhida pelos parâmetros fornecidos 
        a função Ex: addInfo(table="Clientes", Id=2, Nome="Gabriel") ou 
        addInfo(table="Cliehtes", Cpf=2, Idade=20, Telefone="283728172")
        """
        assert hasattr(self, "cursor"), "Favor inicializar a classe com \
 with para utilizar este comando"
        assert isinstance(table, str), "Formato de tabela deve ser uma string"
        assert len(
            kwargs) > 0, "Adicione os parâmetros para serem colocados na\
tabela"  # type: ignore

        comando = (f"insert into {table}(")
        keys = list(kwargs.keys())
        values = list(kwargs.values())

        for i in keys:
            comando += str(i)
            comando += ", "
        comando = comando[:-2] + ") values ("

        for i in values:
            if isinstance(i, int | float):
                comando += str(i)
            else:
                comando += f"\"{str(i)}\""
            comando += ", "
        comando = comando[:-2] + ")"
        self.cursor.execute(comando)

    def getCabec(self, table) -> list[tuple]:
        """
        Resgata os cabeçalhos de uma tabela específica.
        """
        assert hasattr(self, "cursor"), "Favor inicializar a classe com \
 with para utilizar este comando"
        assert isinstance(table, str), "Formato de tabela deve ser uma string"

        self.cursor.execute(f"PRAGMA table_info({table})")
        cabec = list(self.cursor.fetchall())
        return cabec

    def __enter__(self):
        self.connection = sqlite3.connect(self.sql_path)
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, *args):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()


if __name__ == "__main__":
    with SqlReader(DADOS, CREATE) as reader:
        reader.getCabec("Clientes")
