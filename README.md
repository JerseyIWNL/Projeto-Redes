Projeto Redes - Protocolo IDP2PI

Este projeto implementa um sistema de compartilhamento de imagens baseado no protocolo IDP2PI. A solução foi desenvolvida utilizando Python e sockets para explorar conceitos de redes de computadores, incluindo arquitetura P2P, comunicação via UDP e TCP, e gerenciamento de mensagens.

Funcionalidades

Servidor

Geração e controle de uma lista de clientes conectados.

Gerenciamento de imagens compartilhadas.

Resposta a mensagens de:

Registro (REG)

Atualização de imagens (UPD)

Listagem de imagens (LST)

Desconexão de clientes (END)

Cliente

Registro no servidor com informações de imagens e porta TCP.

Listagem de imagens compartilhadas na rede.

Download de imagens de outros clientes.

Operações paralelas utilizando threads para:

Envio de imagens via TCP.

Interação com o servidor via UDP.

Como Executar

Requisitos

Python 3.8 ou superior

Passos

Clone o repositório:

git clone https://github.com/JerseyIWNL/Projeto-Redes.git
cd Projeto-Redes

Execute o servidor:

python3 servidor.py

Execute o cliente:

python3 cliente.py <IP_DO_SERVIDOR> <DIRETORIO_DE_IMAGENS>

Substitua <IP_DO_SERVIDOR> pelo IP onde o servidor está rodando.

Substitua <DIRETORIO_DE_IMAGENS> pelo caminho para o diretório contendo as imagens que o cliente deseja compartilhar.

Comandos do Cliente

Listar imagens disponíveis:
Exibe todas as imagens compartilhadas na rede.

Download de imagem:
Permite baixar uma imagem de outro cliente conectado.

Desconectar:
Finaliza a conexão do cliente com o servidor.

Estrutura de Arquivos

servidor.py: Implementação do servidor.

cliente.py: Implementação do cliente.
