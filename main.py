import socket
from sqlCommands import SqlReader
from variaveis import (DADOS, FILA_DE_ESPERA_MAXIMA, IP, PORTA,
                       LARGURA_DADOS, SENHACLIENTESGERAL,
                       RESPOSTACONEXAOACEITA, LOG, TIMEOUT,
                       RESPOSTA_LOGIN_NAO_ENCONTRADO, RESPOSTA_SENHA_INCORRETA,
                       RESPOSTA_DESSINCRONIZACAO, RESPOSTA_SOLICITACAO_LOGIN,
                       RESPOSTA_SOLICITACAO_CADASTRO)
from creates import CREATE
import os
from threading import Thread, Lock
import time
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
        os.system("python main.py")

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
            dados = self.inputCliente(client, ip, lock)

            # Função de cadastro
            resp = self.cadastrar(client, ip, lock, dados)

            if resp == 0:
                client.close()
                return

            self.armazenaLog("Cadastro concluído com sucesso!!!", ip)
        else:
            self.dessincronizacaoError(client, ip, lock)
            return

        client.close()
        self.armazenaLog("Desconectado", ip)

    def dessincronizacaoError(self, client, ip, lock):
        # Retorna erro por dessincronização e armazena no log
        self.outputCliente("Servidor dessincronizado", client, ip, lock)
        self.armazenaLog("Desconectado por dessincronizacao", ip)
        self.outputCliente(RESPOSTA_DESSINCRONIZACAO, client, ip, lock)
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

    def login(self, login: str, cliente: socket.socket, ip: tuple[str, str | int],
              lock: Lock) -> dict[str, str] | None:
        # Verifica se o usuário existe e resgata as informações do mesmo,
        # devolvendo em um dicionário, ou retorna None quando não for
        # encontrado

        # Colocar os lock mais tarde-------------------------------------------------------------------------------------
        usuario = re.findall(r'"([\w\W]+?)" "([\w\W]+?)"', login)

        with SqlReader(DADOS, CREATE) as reader:
            if usuario != []:
                dadosUsuario = reader.getInfo(
                    "Usuarios", key=["Login", usuario[0][0]])
            else:
                return None

            if dadosUsuario == []:
                self.outputCliente(
                    RESPOSTA_LOGIN_NAO_ENCONTRADO, cliente, ip, lock)
                self.armazenaLog("Login nao encontrado", ip)
                return None
            cabecalhos = reader.getCabec("Usuarios")

            info = {}
            for a in cabecalhos:
                info[a[1]] = dadosUsuario[0][cabecalhos.index(a)]
            if info["Senha"] == usuario[0][1]:
                return info
            else:
                self.outputCliente(
                    RESPOSTA_SENHA_INCORRETA, cliente, ip, lock)
                self.armazenaLog("Senha incorreta", ip)
                return None

    def cadastrar(self, cliente: socket.socket,
                  ip: tuple[str, str | int], lock: Lock, dados: str) -> int:

        print(dados)


if __name__ == "__main__":
    server = Servidor()
