Jokenpô Multiplayer (Python + Redis)

Este projeto implementa um jogo de Jokenpô multiplayer via terminal utilizando Redis como mecanismo de sincronização entre dois jogadores.
Funciona localmente ou entre máquinas diferentes conectadas ao mesmo servidor Redis.


Funcionalidades:

Criação e entrada em salas

Registro automático como Jogador 1 ou Jogador 2

Sincronização entre jogadores usando Redis

Jogadas simultâneas

Determinação automática do vencedor

Suporte a rematch (nova partida)

Limpeza automática das chaves da sala

Timeout para evitar travamentos

Tecnologias

Python 3.x

Redis

Biblioteca redis para Python



Instalação:

pip install redis

Como executar
1. Inicie o servidor Redis
redis-server

2. Execute o jogo
python jogo.py

Como jogar

Escolha entre:

1: Criar sala

2: Entrar em sala

O programa exibirá (ou pedirá) um código de sala, como:

a3f9b12c


Escolha sua jogada:

1 = Pedra

2 = Papel

3 = Tesoura

Após o resultado, escolha se deseja jogar novamente:

Jogar novamente? (s/n)

Comunicação via Redis

O jogo utiliza o Redis para coordenar eventos e sincronizar o estado entre os dois jogadores.

Principais chaves utilizadas:

Chave	Função
sala:{id}:player1/2	Registro dos jogadores
sala:{id}:jogada:1/2	Jogadas dos players
sala:{id}:sync:*	Controle de sincronização
sala:{id}:rematch:*	Decisão de rematch
sala:{id}:status	Status geral da sala

A sincronização funciona como uma barreira: cada jogador sinaliza que chegou a uma etapa e aguarda o outro antes de continuar.


Estrutura do código:

Funções utilitárias: criação/entrada de sala, limpeza e registro de jogadores

Sincronização: espera por chaves, barreiras, timeout

Lógica do jogo: registrar jogadas, ler jogada do oponente, determinar vencedor

Loop principal: controla rodadas, exibe resultado e gerencia rematch

Possíveis melhorias

Interface gráfica (Tkinter ou versão web)

API REST para criação e gerenciamento de partidas

Suporte a mais jogadores (torneios)

Logs persistentes das partidas

Melhor tratamento de desconexão


Licença:

Uso livre para fins de estudo e modificações.
