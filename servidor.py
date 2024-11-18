import socket

# Lista para acompanhar os clientes conectados: cada cliente é identificado por IP, porta, senha e imagens que compartilha
clientes = []
# Lista global para acompanhar as imagens compartilhadas e os clientes que as possuem
imagens_compartilhadas = []

# Função para enviar uma mensagem de erro via UDP
def enviar_erro(servidor, endereco, mensagem):
    servidor.sendto(f"ERR {mensagem}".encode(), endereco)

# Atualiza a lista global de imagens compartilhadas
def atualizar_imagens_globais():
    global imagens_compartilhadas
    imagens_compartilhadas = []
    for ip, porta, senha, imagens_cliente in clientes:
        for md5, nome in imagens_cliente:
            encontrado = False
            for imagem in imagens_compartilhadas:
                if imagem['md5'] == md5:
                    imagem['clientes'].append(f"{ip}:{porta}")
                    encontrado = True
                    break
            if not encontrado:
                imagens_compartilhadas.append({
                    'md5': md5,
                    'nome': nome,
                    'clientes': [f"{ip}:{porta}"]
                })

# Função principal para interpretar e processar mensagens dos clientes
def processar_mensagem(servidor, mensagem, endereco):
    global clientes, imagens_compartilhadas

    # Divide a mensagem recebida em partes para identificar o comando
    partes = mensagem.decode().split()
    if len(partes) < 1:  # Verifica se a mensagem está vazia ou inválida
        return

    comando = partes[0]

    # Se o cliente está se registrando
    if comando == 'REG':
        if len(partes) != 4:
            enviar_erro(servidor, endereco, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta, imagens_cliente = partes[1], int(partes[2]), partes[3]

        # Coleta as imagens do cliente e organiza em uma lista de tuplas (MD5, nome da imagem)
        imagens_lista = imagens_cliente.split(';')
        imagens_cliente = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]

        # Guarda o cliente com o IP, porta, senha e lista de imagens compartilhadas
        clientes.append((endereco[0], porta, senha, imagens_cliente))

        # Atualiza a lista global de imagens
        atualizar_imagens_globais()

        # Confirmação para o cliente com a quantidade de imagens registradas
        servidor.sendto(f"OK {len(imagens_cliente)}_REGISTERED_IMAGES".encode(), endereco)

    # Se o cliente quer atualizar suas informações
    elif comando == 'UPD':
        if len(partes) != 4:
            enviar_erro(servidor, endereco, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta, imagens_cliente = partes[1], int(partes[2]), partes[3]

        # Procura pelo cliente com a senha fornecida e atualiza as imagens
        for i, (ip, p, s, imgs) in enumerate(clientes):
            if s == senha and ip == endereco[0]:
                imagens_lista = imagens_cliente.split(';')
                imagens_cliente = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]
                clientes[i] = (ip, p, senha, imagens_cliente)
                
                # Atualiza a lista global de imagens
                atualizar_imagens_globais()

                servidor.sendto(f"OK {len(imagens_cliente)}_REGISTERED_FILES".encode(), endereco)
                return

        # Se a senha não combina com nenhum cliente registrado
        enviar_erro(servidor, endereco, 'IP_REGISTERED_WITH_DIFFERENT_PASSWORD')

    # Se o cliente quer listar as imagens disponíveis
    elif comando == 'LST':
        resposta = []
        for imagem in imagens_compartilhadas:
            md5 = imagem['md5']
            nome = imagem['nome']
            clientes_imagem = ",".join(imagem['clientes'])
            resposta.append(f"{md5},{nome},{clientes_imagem}")
        servidor.sendto(";".join(resposta).encode(), endereco)

    # Se o cliente quer encerrar sua conexão
    elif comando == 'END':
        if len(partes) != 3:
            enviar_erro(servidor, endereco, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta = partes[1], int(partes[2])

        # Desconecta o cliente e confirma
        for i, (ip, p, s, imgs) in enumerate(clientes):
            if s == senha and ip == endereco[0]:
                del clientes[i]
                
                # Atualiza a lista global de imagens
                atualizar_imagens_globais()

                servidor.sendto("OK CLIENT_FINISHED".encode(), endereco)
                return

        # Caso a senha esteja incorreta
        enviar_erro(servidor, endereco, 'IP_REGISTERED_WITH_DIFFERENT_PASSWORD')

    # Se o comando não é reconhecido, devolve erro
    else:
        enviar_erro(servidor, endereco, 'INVALID_MESSAGE_FORMAT')

# Função principal que fica "ouvindo" mensagens dos clientes via UDP
def ouvir_cliente():
    global clientes
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria o socket UDP
    servidor.bind(('', 13377))  # Liga o socket à porta 13377
    print("Servidor aguardando mensagens...")

    while True:
        # Recebe mensagem e endereço de um cliente
        mensagem, endereco = servidor.recvfrom(1024)  # Tamanho máximo de mensagem: 1024 bytes
        processar_mensagem(servidor, mensagem, endereco)

# Função principal para inicializar o servidor
def main():
    ouvir_cliente()

if __name__ == "__main__":
    main()
