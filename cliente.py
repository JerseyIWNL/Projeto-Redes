#!/usr/bin/python
import socket
from _thread import *
import hashlib
import random
import string
import sys
import os
import time

# Constantes
SERVER_IP = sys.argv[1]
PORTA_UDP = 13377

# Variáveis globais
client_dir = sys.argv[2]
porta_tcp = None
senha = None
imagens = []

# Função para configurar o ambiente - Criar o diretório que conterá as imagens
def configurar_ambiente():
    print("\nConfigurando o ambiente...")
    
    global client_dir
    
    # Verifica se 'imagens_salvas' está presente no caminho do diretório
    if 'imagens_salvas' not in client_dir:
        if not client_dir.endswith(os.sep):
            client_dir += os.sep
        client_dir = os.path.join(client_dir, 'imagens_salvas')

    # Garante que o caminho final termina com um separador
    if not client_dir.endswith(os.sep):
        client_dir += os.sep

    # Verifica se o diretório existe
    if not os.path.exists(client_dir):
        # Cria o diretório se ele não existir
        os.makedirs(client_dir)
        print(f"Diretório '{client_dir}' criado com sucesso!")
    else:
        print(f"O diretório '{client_dir}' já existe.")

    print("Configuração concluída!\n")

# Função para achar uma porta disponível
def descobre_porta_disponivel():
    print("Descobrindo porta disponível...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))  # Deixa o SO escolher uma porta disponível
    porta_disponivel = s.getsockname()[1]
    s.close()
    print(f"Porta {porta_disponivel} está disponível!\n")
    return porta_disponivel

# Função para gerar senha aleatória
def gerar_senha(comprimento=16):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha = ''.join(random.choice(caracteres) for i in range(comprimento))
    return senha

def formatar_imagens():
    resultado = "'" + "';'".join(imagens) + "'"
    return resultado

# Função para adicionar as imagens presentes no diretório "imagens_salvas"
def listar_imagens_diretorio():
    imagens = []

    diretorio = os.path.expanduser(client_dir)

    # Verifica se o diretório existe
    if not os.path.exists(diretorio):
        print(f"Erro: O diretório '{diretorio}' não existe.")
        return imagens  # Retorna uma lista vazia em caso de erro

    # Percorre todos os arquivos no diretório
    for nome_arquivo in os.listdir(diretorio):
        caminho_arquivo = os.path.join(diretorio, nome_arquivo)

        # Verifica se é um arquivo (e não um diretório)
        if os.path.isfile(caminho_arquivo):
            try:
                # Calcula o hash MD5 da imagem
                with open(caminho_arquivo, 'rb') as f:
                    md5_hash = hashlib.md5()
                    # Lê o arquivo em pedaços para não sobrecarregar a memória
                    for byte_block in iter(lambda: f.read(4096), b""):
                        md5_hash.update(byte_block)
                    
                    # Formata o MD5 e o nome da imagem
                    md5 = md5_hash.hexdigest()
                    imagens.append(f"{md5},{nome_arquivo}")
            except Exception as e:
                print(f"Erro ao processar o arquivo '{nome_arquivo}': {e}")

    return imagens

# Função que recebe a requisição de uma imagem e a envia a um cliente
def servico_tcp(client):
    try:
        # Recebe a mensagem do cliente solicitante
        mensagem = client.recv(1024).decode().strip()

        # Verifica se a mensagem está no formato "GET <MD5>"
        if not mensagem.startswith("GET ") or len(mensagem.split()) != 2:
            print("Formato de mensagem inválido.")
            client.send(b"ERR Invalid message format")
            return

        # Extrai o hash MD5 solicitado
        md5_requisitado = mensagem.split()[1]

        # Define o diretório onde as imagens compartilhadas estão armazenadas
        diretorio_imagens = os.path.expanduser(client_dir)

        # Verifica se há algum arquivo que corresponde ao hash MD5 solicitado
        encontrado = False
        for nome_arquivo in os.listdir(diretorio_imagens):
            caminho_arquivo = os.path.join(diretorio_imagens, nome_arquivo)
            if os.path.isfile(caminho_arquivo):
                # Calcula o hash MD5 do arquivo
                with open(caminho_arquivo, "rb") as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
                # Verifica se o hash corresponde ao solicitado
                if md5 == md5_requisitado:
                    encontrado = True
                    print(f"Enviando imagem '{nome_arquivo}' para o cliente.")
                    # Envia o conteúdo do arquivo
                    with open(caminho_arquivo, "rb") as f:
                        client.sendall(f.read())
                    break

        # Caso o arquivo não seja encontrado
        if not encontrado:
            print("Arquivo não encontrado.")
            client.send(b"ERR File not found")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        client.send(b"ERR Internal server error")

    finally:
        client.close()

# Função para realizar a conexão TCP com outro cliente
def controle_tcp():
    global porta_tcp
    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _socket.bind(('', porta_tcp))
    _socket.listen(4096)
    print(f"Utilizando a porta {porta_tcp}.\n")
    while True:
        client, addr = _socket.accept()
        start_new_thread(servico_tcp, (client, ))

# Função para enviar mensagens UDP ao servidor e obter resposta
def controle_udp(mensagem):
    def send_udp():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.sendto(mensagem.encode(), (SERVER_IP, PORTA_UDP))
            resposta, _ = udp_socket.recvfrom(16384)
            print(f"Resposta do servidor para '{mensagem}':\n{resposta.decode()}")
    
    # Cria uma nova thread para enviar a mensagem UDP
    start_new_thread(send_udp, ())

# Função para registrar o cliente no servidor
def registro_cliente(senha, porta):
    # Formata a mensagem de registro
    mensagem = f"REG {senha} {porta} {formatar_imagens()}"
    controle_udp(mensagem)

# Função para atualizar o registro de algum cliente no servidor
def atualizar_cliente(senha, porta):
    # Formata a mensagem de atualização
    mensagem = f"UPD {senha} {porta} {formatar_imagens()}"
    controle_udp(mensagem)

# Função para desconectar um cliente do servidor
def desconectar_cliente(senha, porta):
    # Formata a mensagem de desconexão
    mensagem = f"END {senha} {porta}"
    controle_udp(mensagem)

# Função para listar as imagens presentes no servidor
def listar_imagens():
    # Formata a mensagem de listagem
    mensagem = "LST"
    controle_udp(mensagem)

# Função para baixar a imagem e atualizar a lista de imagens
def baixar_imagem():
    global imagens  # Referência à variável global imagens

    # Solicita as informações ao usuário
    md5_imagem = input("Digite o hash MD5 da imagem que deseja baixar: ")
    ip_cliente = input("Digite o IP do cliente que possui a imagem: ")
    porta_cliente = int(input("Digite a porta TCP do cliente que possui a imagem: "))

    mensagem = f"GET {md5_imagem}"

    try:
        # Conecta ao cliente remoto via TCP para baixar a imagem
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((ip_cliente, porta_cliente))
            tcp_socket.send(mensagem.encode())
            
            # Recebe os dados da imagem
            imagem_dados = b""
            while True:
                data = tcp_socket.recv(16384)
                if not data:
                    break
                imagem_dados += data

            if imagem_dados:
                # Salva a imagem no diretório
                caminho_imagem = os.path.join(client_dir, f"{md5_imagem}.jpg")
                with open(caminho_imagem, "wb") as f:
                    f.write(imagem_dados)
                print(f"Imagem {md5_imagem}.jpg baixada e salva em {client_dir}.")

            else:
                print("Erro: Nenhum dado recebido para a imagem.")

    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")

    finally:
        imagens = listar_imagens_diretorio()
        print(f"A imagem {md5_imagem}.jpg foi adicionada à lista de imagens.")

# Menu de opções do cliente
def menu():
    while True:
        try:
            print('MENU:')
            print('    1 - Registrar cliente no servidor')
            print('    2 - Atualizar registro do cliente')
            print('    3 - Remover registro do servidor')
            print('    4 - Listar imagens')
            print('    5 - Baixar imagens')
            print('    6 - Sair\n')

            op = int(input('Escolha uma opção: '))

            if op == 1:
                registro_cliente(senha, porta_tcp)
            elif op == 2:
                atualizar_cliente(senha, porta_tcp)
            elif op == 3:
                desconectar_cliente(senha, porta_tcp)
            elif op == 4:
                listar_imagens()
            elif op == 5:
                baixar_imagem()
            elif op == 6:
                desconectar_cliente(senha, porta_tcp)
                print("Saindo...")
                break  # Encerra o loop e finaliza o programa
            else:
                print('Opção inválida')

            time.sleep(0.1)  # Espera um pouco antes de exibir o menu novamente

        except KeyboardInterrupt:
            # Quando o Ctrl+C for pressionado
            print("\nInterrupção do programa detectada.")
            desconectar_cliente(senha, porta_tcp)  # Garante que o cliente seja desconectado
            print("Cliente desconectado. Saindo...")
            break  # Encerra o loop e finaliza o programa

# Função principal do código
def main():
    # Conferindo se o cliente foi executado com o comando correto
    if len(sys.argv) < 3:
        print("Erro: É necessário fornecer um IP e um diretório na linha de execução")
        sys.exit(1)

    # Configurando o ambiente (Criando diretório)
    configurar_ambiente()

    # Dando o valor correto às variáveis globais
    global porta_tcp, senha, imagens, ip_client
    porta_tcp = descobre_porta_disponivel()
    senha = gerar_senha()
    imagens = listar_imagens_diretorio()

    # Listando as imagens que o cliente deseja compartilhar com outros clientes
    print(f"Imagens:\n{imagens}\n")

    # Abrindo uma conexão TCP em uma nova thread
    start_new_thread(controle_tcp, ())
    time.sleep(0.1)

    # Mostrando as opções de ação para o cliente
    menu()

if __name__ == '__main__':
    main()
