import socket

# Lista para acompanhar os clientes conectados: cada cliente é identificado por IP, porta, senha e imagens que compartilha
clientes = []
# Lista global para acompanhar as imagens compartilhadas e os clientes que as possuem
imagens_compartilhadas = []
# Porta UDP
PORTA_SERVER = 13377

def obter_ip_servidor():
    # Conecta ao servidor externo (como o Google DNS) para determinar o IP na rede local
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('8.8.8.8', 80))  # Conecta ao Google DNS
        ip_servidor = s.getsockname()[0]  # Obtém o IP da interface de rede
    except Exception:
        ip_servidor = '127.0.0.1'  # Caso não consiga se conectar, retorna o IP local
    finally:
        s.close()
    return ip_servidor

# Função para enviar uma mensagem de erro via UDP
def enviar_erro(servidor, endereco, mensagem):
    servidor.sendto(f"ERR {mensagem}".encode(), endereco)

# Atualiza a lista global de imagens compartilhadas
def atualizar_imagens_globais():
    global imagens_compartilhadas
    # Percorre os clientes para garantir que cada imagem deles está atualizada
    for ip, porta, senha, imagens_cliente in clientes:
        for md5, nome in imagens_cliente:
            # Verifica se a imagem já existe na lista global
            for imagem in imagens_compartilhadas:
                if imagem['md5'] == md5:
                    # Se a imagem já existe, garante que o cliente está listado
                    cliente_info = f"{ip}:{porta}"
                    if cliente_info not in imagem['clientes']:
                        imagem['clientes'].append(cliente_info)
                    break
            else:
                # Se a imagem ainda não existe, adiciona à lista global
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

        # Verifica se a lista de imagens está vazia
        if not imagens_cliente.strip():  # Lista vazia ou só espaços
            imagens_cliente = []  # Define uma lista vazia
        else:
            try:
                # Coleta as imagens do cliente e organiza em uma lista de tuplas (MD5, nome da imagem)
                imagens_lista = imagens_cliente.split(';')
                imagens_cliente = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]
            except IndexError:
                enviar_erro(servidor, endereco, 'INVALID_IMAGE_FORMAT')
                return

        # Guarda o cliente com o IP, porta, senha e lista de imagens compartilhadas (mesmo que vazia)
        clientes.append((endereco[0], porta, senha, imagens_cliente))

        # Atualiza a lista global de imagens
        atualizar_imagens_globais()

        # Confirmação para o cliente com a quantidade de imagens registradas (0 caso esteja vazio)
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
                # Remover as imagens antigas do cliente da lista global
                cliente_info = f"{ip}:{p}"
                imagens_compartilhadas = [
                    img for img in imagens_compartilhadas
                    if cliente_info not in img['clientes']
                ]

                # Atualizar a lista de imagens do cliente
                if not imagens_cliente.strip():  # Caso não tenha imagens
                    novas_imagens = []
                else:
                    try:
                        imagens_lista = imagens_cliente.split(';')
                        novas_imagens = [(img.split(',')[0], img.split(',')[1]) for img in imagens_lista]
                    except IndexError:
                        enviar_erro(servidor, endereco, 'INVALID_IMAGE_FORMAT')
                        return
                
                # Atualizar o cliente na lista de clientes
                clientes[i] = (ip, p, senha, novas_imagens)

                # Adicionar as novas imagens à lista global
                for md5, nome in novas_imagens:
                    # Verifica se já existe na lista global
                    for imagem in imagens_compartilhadas:
                        if imagem['md5'] == md5:
                            imagem['clientes'].append(cliente_info)
                            break
                    else:
                        # Adiciona a nova imagem caso ela não exista
                        imagens_compartilhadas.append({
                            'md5': md5,
                            'nome': nome,
                            'clientes': [cliente_info]
                        })

                # Confirmação para o cliente com o número de arquivos registrados
                servidor.sendto(f"OK {len(novas_imagens)}_REGISTERED_FILES".encode(), endereco)
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
            resposta.append(f"[ {md5} - {nome} - clientes: {clientes_imagem} ]")

        resposta = "\n".join(resposta).encode()
        servidor.sendto(resposta, endereco)

    # Se o cliente quer encerrar sua conexão
    elif comando == 'END':
        if len(partes) != 3:
            enviar_erro(servidor, endereco, 'INVALID_MESSAGE_FORMAT')
            return
        senha, porta = partes[1], int(partes[2])

        # Desconecta o cliente e confirma
        for i, (ip, p, s, imgs) in enumerate(clientes):
            if s == senha and ip == endereco[0]:
                # Remover o cliente da lista de clientes
                cliente_removido = clientes.pop(i)

                # Remover as imagens associadas a esse cliente
                for md5, nome in cliente_removido[3]:
                    # Itera pela lista global de imagens e remove as imagens desse cliente
                    for imagem in imagens_compartilhadas:
                        if imagem['md5'] == md5 and nome == imagem['nome']:
                            # Remove o cliente da lista de clientes dessa imagem
                            if f"{ip}:{porta}" in imagem['clientes']:
                                imagem['clientes'].remove(f"{ip}:{porta}")
                            # Se não houver mais clientes compartilhando a imagem, remove a imagem da lista global
                            if not imagem['clientes']:
                                imagens_compartilhadas.remove(imagem)
                            break

                # Atualiza a lista global de imagens
                atualizar_imagens_globais()

                # Envia confirmação de que o cliente foi desconectado
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
    servidor.bind(('', PORTA_SERVER))  # Liga o socket à porta 13377
    print(f"IP do Servidor: {obter_ip_servidor()}")
    print(f"Porta do servidor: {PORTA_SERVER}")
    print("Servidor aguardando mensagens...")

    try:
        while True:
            # Recebe mensagem e endereço de um cliente
            mensagem, endereco = servidor.recvfrom(1024)  # Tamanho máximo de mensagem: 1024 bytes
            print(f"\nMensagem oriunda do cliente:\n{mensagem.decode()}\n")
            processar_mensagem(servidor, mensagem, endereco)
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    finally:
        servidor.close()  # Fecha o socket UDP
        print("Socket fechado, servidor encerrado.")

# Função principal para inicializar o servidor
def main():
    ouvir_cliente()

if __name__ == "__main__":
    main()
