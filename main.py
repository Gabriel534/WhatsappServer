import socket
from sqlCommands import SqlReader
from variaveis import (DADOS, FILA_DE_ESPERA_MAXIMA, IP, PORTA,
                       LARGURA_DADOS, SENHACLIENTESGERAL,
                       RESPOSTACONEXAOACEITA, LOG, TIMEOUT,
                       RESPOSTA_LOGIN_NAO_ENCONTRADO, RESPOSTA_SENHA_INCORRETA,
                       RESPOSTA_DESSINCRONIZACAO, RESPOSTA_SOLICITACAO_LOGIN,
                       RESPOSTA_SOLICITACAO_CADASTRO,
                       RESPOSTA_USUARIO_JA_CADASTRADO,
                       RESPOSTA_CADASTRO_BEM_SUCEDIDO, MAIN,
                       RESPOSTA_CADASTRO_INVALIDO,
                       RESPOSTA_SOLICITACAO_NOVO_CONTATO,
                       RESPOSTA_CONTATO_INVALIDO,
                       RESPOSTA_CONTATO_JA_EXISTENTE,
                       RESPOSTA_CONTATO_NAO_EXISTE,
                       RESPOSTA_CADASTRO_CONTATO_REALIZADO,
                       EXPRESSAO_REGULAR_VALIDA_EMAIL,
                       EXPRESSAO_REGULAR_VALIDA_SENHA,
                       RESPOSTA_CREDENCIAIS_INVALIDAS)
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

        # Procura um login até ser encontrado ou dar timeout
        if solicitacao == RESPOSTA_SOLICITACAO_LOGIN:
            self.loginUsuario(client, ip, lock)

        # Faz o cadastro de um novo usuário
        elif solicitacao == RESPOSTA_SOLICITACAO_CADASTRO:
            self.cadastrarUsuario(client, ip, lock)

        elif solicitacao == RESPOSTA_SOLICITACAO_NOVO_CONTATO:
            self.cadastrarContato(client, ip, lock)

        else:
            self.dessincronizacaoError(client, ip, lock)
            return

        client.close()
        self.armazenaLog("Desconectado", ip)

    def dessincronizacaoError(self, client, ip, lock):
        # Retorna erro por dessincronização e armazena no log
        self.outputCliente(RESPOSTA_DESSINCRONIZACAO, client, ip, lock)
        self.armazenaLog("Erro de dessincronização", ip)

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

    def loginUsuario(self, cliente: socket.socket,
                     ip: tuple[str, str | int], lock: Lock) -> None:
        # Verifica se o usuário existe e resgata as informações do mesmo,
        # devolvendo em um dicionário, ou retorna None quando não for
        # encontrado

        self.outputCliente(RESPOSTA_SOLICITACAO_LOGIN, cliente, ip, lock)

        login = self.inputCliente(cliente, ip, lock)

        if login == "ERROR":
            self.armazenaLog("Erro de recebimento de dados do cliente", ip)
            return

        # Colocar os lock mais tarde-------------------------------------------------------------------------------------

       # Filtra o usuário para receber o login e a senha
        usuario = re.findall(r'"([\w\W]+?)"', login)

        if usuario == [] or len(usuario) != 2:
            return

        info = self.logar(cliente, ip, lock, usuario[0], usuario[1])
        if isinstance(info, dict):
            self.registrarIp(info["Id"], ip)
            self.registrarHorario(info["Id"])

            cliente.send(pickle.dumps(info))
            self.armazenaLog("Logado", ip)

        if info == 0:
            self.outputCliente(
                RESPOSTA_LOGIN_NAO_ENCONTRADO, cliente, ip, lock)
            self.armazenaLog("Email nao encontrado", ip)
            return
        elif info == 1:
            self.outputCliente(
                RESPOSTA_SENHA_INCORRETA, cliente, ip, lock)
            self.armazenaLog("Senha incorreta", ip)
            return

    def logar(self, cliente: socket.socket,
              ip: tuple[str, str | int], lock: Lock, login: str, senha: str) -> int | dict:
        """
        Responde 0 se não achar o login
        Responde 1 se a senha estiver incorreta
        Responde com um dicionário de dados caso for encontrado login com senha
        correta
        """

        with SqlReader(DADOS, CREATE) as reader:
            dadosUsuario = reader.getInfo(
                "Usuarios", key=["Email", login])
            # Se não encontrar o login, ele responde ao cliente que o login não
            # foi encontrado
            if dadosUsuario == []:
                return 0
            cabecalhos = reader.getCabec("Usuarios")

            # Organiza os dados recebidos do banco de dados em um dicionário
            info = {}
            for a in cabecalhos:
                info[a[1]] = dadosUsuario[0][cabecalhos.index(a)]

            # Se a senha obtida no banco de dados for diferente da senha
            # recebida, ele não fornecerá as informações de login
            # Caso contrário, ele responderá com os dados de usuário
            if info["Senha"] == senha:
                return info
            else:
                return 1

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

    def cadastrarUsuario(self, cliente: socket.socket,
                         ip: tuple[str, str | int], lock: Lock) -> None:
        """
        Pega os valores recebidos e filtrados, e, caso não exista outro login 
        igual, ele cadastra o novo usuário
        Exemplo da variável dados: f"\"{nome}\" \"{telefone}\" \"{email}\" 
        \"{senha}\""
        """

        self.outputCliente(RESPOSTA_SOLICITACAO_CADASTRO, cliente, ip, lock)

        # A string recebida é filtrada e transforma suas informações em
        # uma lista.

        dadosRecebidos = self.inputCliente(cliente, ip, lock)

        if dadosRecebidos == "ERROR":
            self.armazenaLog("Erro de recebimento de dados do cliente", ip)
            return

        dados: list = re.findall(r'\"([\w\W]+?)\"', dadosRecebidos)

        # Verifica se os dados são válidos
        if not self.validaDados(dados):
            self.armazenaLog("Tentativa de cadastro - Dados inválidos", ip)
            self.outputCliente(
                RESPOSTA_CADASTRO_INVALIDO, cliente, ip, lock)
            return

        with SqlReader(DADOS, CREATE) as reader:
            dado = reader.getInfo("Usuarios", key=["Email", dados[2]])

            # Se o usuário já existir, ele retorna um erro
            if dado != []:
                self.armazenaLog(
                    "Tentativa de cadastro - Usuario já existe", ip)
                self.outputCliente(
                    RESPOSTA_USUARIO_JA_CADASTRADO, cliente, ip, lock)
                return

            reader.addInfo(
                "Usuarios", Nome=dados[0], Telefone=dados[1], Email=dados[2],
                Senha=dados[3])
            self.armazenaLog("Usuário cadastrado com sucesso", ip)
            self.outputCliente(
                RESPOSTA_CADASTRO_BEM_SUCEDIDO, cliente, ip, lock)
            print(dados)
            return

    def validaDados(self, dados: list[str]) -> bool:
        """
        Valida os dados recebidos pelo cliente
        Caso forem válidos, retorna True
        Caso contrário retorna false
        """

        # Se houver exatamente 4 dados, o servidor continua com o cadastro,
        # evitando o recebimento de campos vazios
        if not (len(dados) == 4):
            return False

        # Verifica se o email é valido
        email = re.findall(EXPRESSAO_REGULAR_VALIDA_EMAIL, dados[2])
        if email == [] or len(email) != 1:
            return False

        """
        Verifica se a senha é valida
        Requisitos de senha:
        - Conter no mínimo oito caracteres;

        - Obedecer três dos quatro requisitos: 
            1- letras maiúsculas (A-Z); 
            2- letras minúsculas (a-z); 
            3- números; 
            4- caracteres não alfabéticos ($, &, %, @).
        """
        requisitos = re.findall(EXPRESSAO_REGULAR_VALIDA_SENHA, dados[3])
        if requisitos == []:
            return False

        return True

    def cadastrarContato(self, cliente, ip, lock):
        """
        Cadastra um contato relacionando com o cliente
        """
        self.outputCliente(
            RESPOSTA_SOLICITACAO_NOVO_CONTATO, cliente, ip, lock)

        # Recebe o apelido e o email do contato no formato
        # f"\"{nome}\" \"{email}\" \"{usuario}\" \"{senha}\""
        dadosRecebidos = self.inputCliente(cliente, ip, lock)

        # filtra os dados no formato [nome, email, usuario, senha]
        expressaoFiltraCadastroContato = re.compile(r'\"([\w\W]+?)\"')
        dadosRecebidosFiltrados = re.findall(
            expressaoFiltraCadastroContato, dadosRecebidos)

        # Verifica se os dados estão no tamanho certo
        if len(dadosRecebidosFiltrados) != 4 or dadosRecebidosFiltrados == []:
            self.outputCliente(RESPOSTA_CONTATO_INVALIDO, cliente, ip, lock)
            self.armazenaLog("Armazenamento de contato - dados inválidos", ip)
            return

        # Verifica se as credenciais do usuário são validas
        dadosUsuario = self.logar(cliente, ip, lock, dadosRecebidosFiltrados[2],
                                  dadosRecebidosFiltrados[3])
        print(dadosUsuario)
        if not isinstance(dadosUsuario, dict):
            self.outputCliente(
                RESPOSTA_CREDENCIAIS_INVALIDAS, cliente, ip, lock)
            self.armazenaLog("Armazenamento de contato - credenciais de login \
inválidos", ip)
            return

        # Abre o banco de dados
        with SqlReader(DADOS, CREATE) as reader:
            # Verifica se existe o contasto no banco de dados, caso não informa
            # ao cliente
            dadosContatos = reader.getInfo("Usuarios", key=[
                "Email", dadosRecebidosFiltrados[1]])
            if dadosContatos == []:
                self.outputCliente(
                    RESPOSTA_CONTATO_NAO_EXISTE, cliente, ip, lock)
                self.armazenaLog(
                    "Armazenamento de contato - Contato não existe", ip)
                return

            # Verifica se o contato já está associado ao cliente, caso sim
            # informa ao cliente

            dadosContatosJaCadastrados = reader.getInfo("Contatos",
                                                        key=["EmailUsuario",
                                                             dadosRecebidosFiltrados[2]])
            print(dadosContatosJaCadastrados)
            for i in dadosContatosJaCadastrados:
                if i[2] == dadosRecebidosFiltrados[1]:
                    self.outputCliente(
                        RESPOSTA_CONTATO_JA_EXISTENTE, cliente, ip, lock)
                    self.armazenaLog(
                        "Armazenamento de contato - Contato já cadastrado no \
usuário", ip)
                    return

            reader.addInfo("Contatos", EmailUsuario=dadosUsuario["Email"],
                           EmailContato=dadosRecebidosFiltrados[1],
                           NomeContato=dadosRecebidosFiltrados[0])

            self.outputCliente(
                RESPOSTA_CADASTRO_CONTATO_REALIZADO, cliente, ip, lock)
            self.armazenaLog(
                "Armazenamento de contato - Contato cadastrado com sucesso",
                ip)


if __name__ == "__main__":
    server = Servidor()
