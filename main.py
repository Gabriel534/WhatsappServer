import socket
from sqlCommands import SqlReader
from variaveis import (DADOS, FILA_DE_ESPERA_MAXIMA, IP, PORTA,
                       LARGURA_DADOS, SENHACLIENTESGERAL,
                       RESPOSTACONEXAOACEITA, LOG, TIMEOUT,
                       RESPOSTA_LOGIN_NAO_ENCONTRADO, RESPOSTA_SENHA_INCORRETA,
                       RESPOSTA_DESSINCRONIZACAO, RESPOSTA_SOLICITACAO_LOGIN,
                       RESPOSTA_SOLICITACAO_CADASTRO,
                       RESPOSTA_USUARIO_JA_CADASTRADO,
                       RESPOSTA_CADASTRO_BEM_SUCEDIDO, MAIN)
from creates import CREATE
import os
from threading import Thread, Lock
import time
import datetime
import re
import pickle


class Servidor():
    def __init__(self):
        self.boolean = True
        self.clientes: dict[str, Thread] = {}

        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.bind((IP, PORTA))
        self.servidor.listen(int(FILA_DE_ESPERA_MAXIMA))

        self.armazenaLog("Servidor iniciado", (IP, PORTA))

        print(f"IP: {IP}")
        print(f"Porta: {PORTA}")

        self.threadcomando = Thread(target=self.comando)
        self.threadcomando.start()
        self.terminal()
        time.sleep(0.1)
        self.armazenaLog("Servidor desligado", (IP, PORTA))

    def comando(self):
        while self.boolean:
            try:
                client, ip = self.servidor.accept()
            except OSError:
                print("Resposta a novas solicitações de clientes fechada")
                return

            self.clientes[ip[1]] = Thread(
                target=self.requisicaoCliente, args=(client, ip))
            self.clientes[ip[1]].start()

    def terminal(self):
        while self.boolean:
            resp = input().lower()
            if resp == "exit":
                self.boolean = False
                self.servidor.close()
                return
            elif resp == "restart":
                self.boolean = False
                self.servidor.close()
                Thread(target=self.restart).start()
                return
            else:
                print("Comando inválido")

    def restart(self):
        os.system("cls")
        os.system(f"python {MAIN}\\\\main.py")

    def armazenaLog(self, text, ip: tuple[str, str | int]):
        print(f"IP {ip[0]} {text}")
        self.log = open(LOG, "+a")
        data = time.localtime()
        linha = f"\n{ip[0]}:{ip[1]} {text} {data.tm_mday}/{data.tm_mon}/\
{data.tm_year} {data.tm_hour}:{data.tm_min}"
        self.log.write(linha)
        self.log.close()

    def requisicaoCliente(self, client: socket.socket,
                          ip: tuple[str, str | int]) -> None:

        client.settimeout(TIMEOUT)

        lock = Lock()

        # Verifica se a senha para clientes é verdadeira
        senha = client.recv(LARGURA_DADOS).decode("UTF-8")
        if senha != SENHACLIENTESGERAL:
            print(f"Conexão negada\nIP {ip[0]} com senha geral incorreta")
            self.armazenaLog("Conexao negada", ip)
            client.close()

            return

        # Retorna ao cliente informando que foi autenticado com sucesso
        self.outputCliente(RESPOSTACONEXAOACEITA, client, ip, lock)

        # Mostra informações no terminal
        print(f"IP {ip[0]} conectado")
        print(f"Porta {ip[1]}")
        self.armazenaLog("Conectado", ip)

        solicitacao = self.inputCliente(client, ip, lock)

        info: dict[str, str] | None = None

        # Procura um login até ser encontrado ou dar timeout
        if solicitacao == RESPOSTA_SOLICITACAO_LOGIN:
            self.outputCliente(RESPOSTA_SOLICITACAO_LOGIN, client, ip, lock)

            login = self.inputCliente(client, ip, lock)
            if login == "ERROR":
                client.close()
                return
            info = self.login(login, client, ip, lock)

            if info is None:
                client.close()
                return

            client.send(pickle.dumps(info))
            self.armazenaLog("Logado", ip)

        elif solicitacao == RESPOSTA_SOLICITACAO_CADASTRO:
            self.outputCliente(RESPOSTA_SOLICITACAO_CADASTRO, client, ip, lock)

            # A string recebida é filtrada e transforma suas informações em
            # uma lista. Ex da string: f"\"{nome}\" \"{telefone}\" \"{email}\"
            #  \"{login}\" \"{senha}\""

            dados = self.inputCliente(client, ip, lock)

            dados_filtrados: list = re.findall(r'\"([\w\W]+?)\"', dados)

            # Se houver exatamente 4 dados, o servidor continua com o cadastro,
            # evitando o recebimento de campos vazios
            if len(dados_filtrados) == 4:
                # Função de cadastro
                self.cadastrar(client, ip, lock, dados_filtrados)
            else:
                self.dessincronizacaoError(client, ip, lock)
                return

        else:
            self.dessincronizacaoError(client, ip, lock)
            return

        client.close()
        self.armazenaLog("Desconectado", ip)

    def dessincronizacaoError(self, client, ip, lock):
        # Retorna erro por dessincronização e armazena no log
        self.outputCliente(RESPOSTA_DESSINCRONIZACAO, client, ip, lock)
        self.armazenaLog("Desconectado por dessincronizacao", ip)
        client.close()

    def inputCliente(self, client: socket.socket,
                     ip: tuple[str, str | int], lock: Lock) -> str:
        # Recebe os input do cliente e trata seus erros, alem de liberar o
        # cadeado da thread
        try:
            info = client.recv(LARGURA_DADOS).decode()
        except TimeoutError:
            self.armazenaLog("Timeout", ip)
            client.close()

            return ""
        except OSError:
            self.armazenaLog("Erro OS no input", ip)
            return "ERROR"
        return info

    def outputCliente(self, text: str, client: socket.socket,
                      ip: tuple[str, str | int], lock: Lock) -> int:
        """
        Envia algum dado ao cliente e trata possíveis erros
        """
        try:
            client.send(text.encode())
        except TimeoutError:
            self.armazenaLog("Timeout", ip)
            client.close()

            return 0
        except OSError:
            self.armazenaLog("Erro OS no output", ip)
            client.close()

            return 0
        return 1

    def login(self, login: str, cliente: socket.socket,
              ip: tuple[str, str | int], lock: Lock) -> dict[str, str] | None:
        # Verifica se o usuário existe e resgata as informações do mesmo,
        # devolvendo em um dicionário, ou retorna None quando não for
        # encontrado

        # Colocar os lock mais tarde-------------------------------------------------------------------------------------

        # Filtra o usuário para receber o login e a senha
        usuario = re.findall(r'"([\w\W]+?)" "([\w\W]+?)"', login)

        with SqlReader(DADOS, CREATE) as reader:
            if usuario != []:
                dadosUsuario = reader.getInfo(
                    "Usuarios", key=["Email", usuario[0][0]])
            else:
                return None

            # Se não encontrar o login, ele responde ao cliente que o login não
            # foi encontrado
            if dadosUsuario == []:
                self.outputCliente(
                    RESPOSTA_LOGIN_NAO_ENCONTRADO, cliente, ip, lock)
                self.armazenaLog("Email nao encontrado", ip)
                return None
            cabecalhos = reader.getCabec("Usuarios")

            # Organiza os dados recebidos do banco de dados em um dicionário
            info = {}
            for a in cabecalhos:
                info[a[1]] = dadosUsuario[0][cabecalhos.index(a)]

            # Se a senha obtida no banco de dados for diferente da senha
            # recebida, ele não fornecerá as informações de login
            # Caso contrário, ele responderá com os dados de usuário
            if info["Senha"] == usuario[0][1]:
                self.registrarIp(info["Id"], ip)
                self.registrarHorario(info["Id"])
                return info
            else:
                self.outputCliente(
                    RESPOSTA_SENHA_INCORRETA, cliente, ip, lock)
                self.armazenaLog("Senha incorreta", ip)
                return None

    def registrarIp(self, idUsuario: int, ip: tuple[str, str | int]):
        """
        Registra o ip no login correspondente
        """
        with SqlReader(DADOS, CREATE) as reader:
            reader.alterInfo("Usuarios", idUsuario, "IP", ip[0])

    def registrarHorario(self, idUsuario: int):
        """
        Registra o horário do último login no banco de dados
        """
        datahora = datetime.datetime.now()

        with SqlReader(DADOS, CREATE) as reader:
            reader.alterInfo("Usuarios", idUsuario,
                             "DataHoraUltimoLogin", str(datahora))

    def cadastrar(self, cliente: socket.socket,
                  ip: tuple[str, str | int], lock: Lock, dados: list) -> int:
        """
        Pega os valores recebidos e filtrados, e, caso não exista outro login 
        igual, ele cadastra o novo usuário
        Exemplo da variável dados: f"\"{nome}\" \"{telefone}\" \"{email}\" 
        \"{senha}\""
        """

        with SqlReader(DADOS, CREATE) as reader:
            dado = reader.getInfo("Usuarios", key=["Email", dados[2]])

            # Se o usuário já existir, ele retorna um erro
            if dado != []:
                self.armazenaLog(
                    "Tentativa de cadastro - Usuario já existe", ip)
                self.outputCliente(
                    RESPOSTA_USUARIO_JA_CADASTRADO, cliente, ip, lock)
                return 0

            reader.addInfo(
                "Usuarios", Nome=dados[0], Telefone=dados[1], Email=dados[2],
                Senha=dados[3])
            self.armazenaLog("Usuário cadastrado com sucesso", ip)
            self.outputCliente(
                RESPOSTA_CADASTRO_BEM_SUCEDIDO, cliente, ip, lock)
            print(dados)
            return 1


if __name__ == "__main__":
    server = Servidor()
