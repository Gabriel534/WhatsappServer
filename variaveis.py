from pathlib import Path
import socket

# Endereço do servidor

# Variáveis apenas do servidor
TIMEOUT = 20
FILA_DE_ESPERA_MAXIMA = 200

MAIN = Path(__file__).parent.resolve()
DATA = MAIN / "data"
DADOS = DATA / "dados.sqlite3"
LOG = DATA / "log.txt"

# Variáveis comuns com o cliente
IP = "127.0.0.1"  # socket.gethostbyname(socket.gethostname())
PORTA = 12345
LARGURA_DADOS = 1024

TAMANHO_MAXIMO_LOGIN = 30
TAMANHO_MAXIMO_SENHA = 30
SENHACLIENTESGERAL = "PEDIDODECONEXÃO"
RESPOSTA_SOLICITACAO_LOGIN = "Login"
RESPOSTA_SOLICITACAO_CADASTRO = "Cadastrar"
RESPOSTACONEXAOACEITA = "TRUE"
RESPOSTA_LOGIN_NAO_ENCONTRADO = "UserNotFound"
RESPOSTA_SENHA_INCORRETA = "InvalidPassword"
RESPOSTA_USUARIO_JA_CADASTRADO = "UserAlreadyExists"
RESPOSTA_CADASTRO_BEM_SUCEDIDO = "Cadastro_berm_sucedisdo"
RESPOSTA_DESSINCRONIZACAO = "DessincronizationError"
RESPOSTA_CADASTRO_INVALIDO = "INVALIDERROR"
RESPOSTA_SOLICITACAO_NOVO_CONTATO = "NovoConTaTo"
RESPOSTA_CONTATO_INVALIDO = "ConTAToInvaliDo"
RESPOSTA_CADASTRO_CONTATO_REALIZADO = "sjkbksjd"
RESPOSTA_CONTATO_JA_EXISTENTE = "jnbsdfnb"  # Fala que tu já cadastrou o contato
RESPOSTA_CONTATO_NAO_EXISTE = "jkdfnjksdfn"  # Fala que o contato não existe
