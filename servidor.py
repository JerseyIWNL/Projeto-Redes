import socket
import hashlib
import threading

# Listas para acompanhar clientes e imagens compartilhadas: cada cliente é identificado por IP, porta, senha e imagens que compartilha
clientes = []
imagens = []

# Função para enviar uma mensagem de erro e encerrar a conexão com o cliente
def enviar_erro(cliente, mensagem):
    cliente.send(f"ERR {mensagem}".encode())
    cliente.close()

# Função principal para interpretar e responder às mensagens dos clientes
def processar_mensagem(cliente, mensagem):
    global clientes, imagens

    # Divide a mensagem recebida em partes, para analisar qual é o comando
    partes = mensagem.decode().split()
    if len(partes) < 1:
        return

    comando = partes[0]

    # Se o cliente está se registrando
    if comando == 'REG':
        if len(partes) != 4:
            enviar_erro(cliente, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta, imagens_cliente = partes[1], int(partes[2]), partes[3]

        # Coleta as imagens do cliente e organiza em uma lista de tuplas (MD5, nome da imagem)
        imagens_lista = imagens_cliente.split(';')
        imagens_cliente = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]

        # Guarda o cliente com o IP, porta, senha e lista de imagens compartilhadas
        clientes.append((cliente.getpeername()[0], porta, senha, imagens_cliente))

        # Confirmação para o cliente com a quantidade de imagens registradas
        cliente.send(f"OK {len(imagens_cliente)}_REGISTERED_IMAGES".encode())

    # Se o cliente quer atualizar suas informações
    elif comando == 'UPD':
        if len(partes) != 4:
            enviar_erro(cliente, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta, imagens_cliente = partes[1], int(partes[2]), partes[3]

        # Procura pelo cliente com a senha fornecida e atualiza as imagens
        for i, (ip, p, s, imgs) in enumerate(clientes):
            if s == senha:
                imagens_lista = imagens_cliente.split(';')
                imagens_cliente = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]
                clientes[i] = (ip, p, senha, imagens_cliente)
                cliente.send(f"OK {len(imagens_cliente)}_REGISTERED_FILES".encode())
                return

        # Se a senha não combina com nenhum cliente registrado
        enviar_erro(cliente, 'IP_REGISTERED_WITH_DIFFERENT_PASSWORD')

    # Se o cliente quer ver a lista de imagens disponíveis
    elif comando == 'LST':
        resposta = ""
        for md5, nome, clientes_imagem in imagens:
            resposta += f"{md5},{nome},{','.join(clientes_imagem)};"
        cliente.send(resposta.encode())

    # Se o cliente quer encerrar sua conexão
    elif comando == 'END':
        if len(partes) != 3:
            enviar_erro(cliente, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta = partes[1], int(partes[2])

        # Desconecta o cliente e confirma
        for i, (ip, p, s, imgs) in enumerate(clientes):
            if s == senha:
                del clientes[i]
                cliente.send(f"OK CLIENT_FINISHED".encode())
                return

        # Caso a senha esteja incorreta
        enviar_erro(cliente, 'IP_REGISTERED_WITH_DIFFERENT_PASSWORD')

    # Se o comando não é reconhecido, devolve erro
    else:
        enviar_erro(cliente, 'INVALID_MESSAGE_FORMAT')

# Função que fica "ouvindo" por conexões e mensagens dos clientes
def ouvir_cliente():
    global clientes
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind(('', 13377))
    print("Servidor aguardando conexões...")

    while True:
        # Recebe mensagem e endereço de um cliente
        mensagem, endereco = servidor.recvfrom(1024)
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(endereco)
        threading.Thread(target=processar_mensagem, args=(cliente, mensagem)).start()

# Função principal para inicializar o servidor
def main():
    ouvir_cliente()

if __name__ == "__main__": 
    main()
