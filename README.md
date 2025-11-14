Jokenpô Multiplayer (Python + Redis)

Este projeto implementa um jogo de Jokenpô (Pedra, Papel e Tesoura) para dois jogadores utilizando Python e Redis.
A comunicação entre os jogadores é feita por meio de chaves no Redis, permitindo que cada um jogue em máquinas diferentes conectadas ao mesmo servidor.

Requisitos:

Python 3.x

Redis em execução

Biblioteca redis:

pip install redis


Como executar:

Inicie o servidor Redis:

redis-server


Execute o script:

python multiplayer.py


Escolha entre criar uma sala ou entrar em uma já existente.

O programa define automaticamente se você será o Jogador 1 ou 2.

Faça sua jogada (1 = Pedra, 2 = Papel, 3 = Tesoura) e aguarde o oponente.

Após o resultado, ambos devem escolher se desejam jogar novamente.

Funcionamento:
Estrutura no Redis

O jogo utiliza chaves para:

Registrar jogadores (player1, player2)

Armazenar jogadas (jogada:1, jogada:2)

Sincronizar etapas do jogo

Armazenar decisão de rematch 

Armazenar status da sala

Todas as chaves possuem timeout para evitar acúmulo de dados.

Sincronização:

O jogo usa um sistema simples em que cada jogador cria uma chave de sincronização e aguarda a do outro antes de continuar.
O Jogador 1 é responsável por limpar as chaves de cada etapa.

Fluxo do jogo:

Criar/entrar em sala

Registrar jogador

Sincronizar início da rodada

Cada jogador envia sua jogada

O código lê a jogada do oponente

Determinação do vencedor

Ambos confirmam que viram o resultado

Jogador 1 limpa as jogadas

Rematch opcional

Nova rodada ou encerramento

Licença:

uso para fins educacionais.
