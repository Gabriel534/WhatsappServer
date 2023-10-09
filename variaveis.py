from pathlib import Path
import socket

# Endereço do servidor
IP = "127.0.0.1"  # socket.gethostbyname(socket.gethostname())
PORTA = 12345

TIMEOUT = 20
SENHACLIENTESGERAL = "PEDIDODECONEXÃO"
RESPOSTA_SOLICITACAO_LOGIN = "Login"
RESPOSTACONEXAOACEITA = "TRUE"
RESPOSTA_LOGIN_NAO_ENCONTRADO = "UserNotFound"
RESPOSTA_SENHA_INCORRETA = "InvalidPassword"
RESPOSTA_DESSINCRONIZACAO = "DessincronizationError"
RESPOSTA_SOLICITACAO_CADASTRO = "Cadastrar"
LARGURA_DADOS = 1024
FILA_DE_ESPERA_MAXIMA = 200

MAIN = Path(__file__).parent.resolve()
DATA = MAIN / "data"
DADOS = DATA / "dados.sqlite3"
LOG = DATA / "log.txt"
