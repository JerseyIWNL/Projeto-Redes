# Projeto: Protocolo IDP2PI - Compartilhamento de Imagens

Este projeto implementa um sistema de compartilhamento de imagens baseado no protocolo **IDP2PI**, utilizando uma arquitetura **Peer-to-Peer (P2P)**. O objetivo é capacitar o uso de conceitos de redes de computadores e programação em sockets.

## Funcionalidades Principais

- **Servidor:**
  - Gerencia a comunicação entre clientes via protocolo UDP.
  - Mantém uma lista de clientes conectados e imagens compartilhadas.
  - Responde a comandos específicos, como registro de clientes, atualização de informações, listagem de imagens e desconexão.

- **Cliente:**
  - Conecta-se ao servidor e interage com outros clientes via protocolo TCP.
  - Permite listar imagens disponíveis, baixar arquivos de outros clientes e compartilhar suas próprias imagens.
  - Realiza comunicação paralela utilizando threads.

## Estrutura de Arquivos

- `servidor.py`: Implementação do servidor, responsável pela comunicação centralizada via UDP.
- `cliente.py`: Implementação do cliente, responsável pela interação direta com outros clientes e o servidor.
- `cliente_base.py`: Base para a implementação do cliente, incluindo funcionalidades de controle TCP e UDP.

## Tecnologias Utilizadas

- Linguagem: Python 3.8+
- Protocolos: UDP (Servidor) e TCP (Cliente)
- Threads para execução paralela de tarefas no cliente.

## Como Executar

### Servidor
1. Execute o servidor com o comando:
   ```bash
   python3 servidor.py
   ```

### Cliente
1. Execute o cliente com o comando:
   ```bash
   python3 cliente.py <IP_SERVIDOR> <DIRETORIO_IMAGENS>
   ```
   - `<IP_SERVIDOR>`: Endereço IP do servidor.
   - `<DIRETORIO_IMAGENS>`: Diretório contendo as imagens a serem compartilhadas e armazenadas.

2. O cliente permite as seguintes interações:
   - Listar imagens disponíveis na rede.
   - Baixar imagens de outros clientes.
   - Desconectar-se do servidor.

## Observações

- Para execução bem-sucedida, garanta que as portas de comunicação estejam disponíveis e não bloqueadas pelo firewall.
- Certifique-se de utilizar imagens válidas no diretório do cliente e que os hashes MD5 estejam corretos.

---

