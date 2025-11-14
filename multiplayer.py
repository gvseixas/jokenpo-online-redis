import redis
import time
import uuid
import sys

# ---------------------- CONFIGURAÇÃO ----------------------
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
TIMEOUT = 120  # segundos 

# ---------------------- CONEXÃO ----------------------
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    if not r.ping():
        print("❌ Não foi possível conectar ao Redis.")
        sys.exit()
    print("✅ Conectado ao servidor Redis com sucesso.")
except Exception as e:
    print(f"❌ Erro ao conectar no Redis: {e}")
    sys.exit()


# ---------------------- FUNÇÕES AUXILIARES ----------------------
def criar_sala():
    sala = str(uuid.uuid4())[:8]
    try:
        r.set(f"sala:{sala}:status", "em_jogo")
    except Exception as e:
        print(f"❌ Erro ao criar sala: {e}")
        sys.exit()

    print(f"\n🎮 Sala criada com sucesso! Código: {sala}")
    return sala, "1"


def entrar_sala():
    sala = input("Digite o código da sala para entrar: ").strip()
    try:
        if not r.exists(f"sala:{sala}:status"):
            print("❌ Sala não encontrada ou já finalizada.")
            sys.exit()
    except Exception as e:
        print(f"❌ Erro ao verificar sala: {e}")
        sys.exit()

    print(f"✅ Você entrou na sala {sala}")
    return sala, "2"


def escolher_modo():
    print("\n=== JOKENPÔ ONLINE ===")
    print("1️⃣ Criar uma nova sala")
    print("2️⃣ Entrar em uma sala existente")
    while True:
        escolha = input("Escolha (1 ou 2): ").strip()
        if escolha in ["1", "2"]:
            return escolha
        print("Opção inválida. Tente novamente.")


def aguardar_jogada(chave):
    start_time = time.time()
    while True:
        try:
            # use exists para checar sem depender do valor retornado
            if r.exists(chave):
                return
        except Exception as e:
            print(f"❌ Erro ao aguardar jogada: {e}")
            sys.exit()

        if time.time() - start_time > TIMEOUT:
            print("⏰ O outro jogador não respondeu a tempo. Encerrando partida.")
            sys.exit()
        time.sleep(0.5)


def sincronizar_inicio_rodada(sala, player):
    # usar namespace consistente "sala:{sala}:..."
    ready_self = f"sala:{sala}:ready:{player}"
    ready_other = f"sala:{sala}:ready:{'2' if player == '1' else '1'}"

    try:
        # definir com expiration para evitar flags antigas
        r.set(ready_self, "ok", ex=TIMEOUT)
    except Exception as e:
        print(f"❌ Erro ao sinalizar prontidão: {e}")
        sys.exit()

    print("⏳ Aguardando o outro jogador ficar pronto...")
    start_time = time.time()
    while True:
        try:
            if r.exists(ready_other):
                break
        except Exception as e:
            print(f"❌ Erro ao verificar prontidão do oponente: {e}")
            sys.exit()

        if time.time() - start_time > TIMEOUT:
            print("⏰ O outro jogador não ficou pronto a tempo.")
            # limpar flag própria antes de sair
            try:
                r.delete(ready_self)
            except:
                pass
            sys.exit()
        time.sleep(0.5)

    try:
        r.delete(ready_self)
        r.delete(ready_other)
    except Exception as e:
        print(f"❌ Erro ao limpar sinalizadores de prontidão: {e}")
        sys.exit()

    print("✅ Ambos os jogadores prontos! Vamos jogar!\n")

def determinar_vencedor(j1, j2):
    if j1 == j2:
        return "Empate!"
    elif (j1 == 1 and j2 == 3) or (j1 == 2 and j2 == 1) or (j1 == 3 and j2 == 2):
        return "Jogador 1 venceu!"
    else:
        return "Jogador 2 venceu!"


# ---------------------- PROGRAMA PRINCIPAL ----------------------
modo = escolher_modo()
if modo == "1":
    sala, player = criar_sala()
else:
    sala, player = entrar_sala()

key_self = f"sala:{sala}:j{player}"
key_other = f"sala:{sala}:j2" if player == "1" else f"sala:{sala}:j1"

# ---------------------- LOOP DO JOGO ----------------------
while True:
    sincronizar_inicio_rodada(sala, player)

    jogada = input("Escolha sua jogada (1=👊 Pedra, 2=🖐 Papel, 3=✌ Tesoura): ").strip()
    while jogada not in ["1", "2", "3"]:
        print("Opção inválida. Tente novamente.")
        jogada = input("Escolha sua jogada (1=👊 Pedra, 2=🖐 Papel, 3=✌ Tesoura): ").strip()

    try:
        r.set(f"{key_self}:jogada", jogada)
    except Exception as e:
        print(f"❌ Erro ao registrar jogada: {e}")
        sys.exit()

    print("⏳ Aguardando jogada do oponente...")
    aguardar_jogada(f"{key_other}:jogada")

    try:
        jogada_oponente = int(r.get(f"{key_other}:jogada").decode())
        jogada_atual = int(r.get(f"{key_self}:jogada").decode())
    except Exception as e:
        print(f"❌ Erro ao recuperar jogadas: {e}")
        sys.exit()

    print(f"Sua jogada: {jogada_atual}, Jogada do oponente: {jogada_oponente}")
    resultado = determinar_vencedor(jogada_atual, jogada_oponente)
    print(f"🎯 Resultado da rodada: {resultado}")

    try:
        r.delete(f"{key_self}:jogada")
        r.delete(f"{key_other}:jogada")
    except Exception as e:
        print(f"❌ Erro ao limpar jogadas: {e}")
        sys.exit()

    jogar_novamente = input("Deseja jogar novamente? (s/n): ").strip().lower()
    if jogar_novamente != "s":
        print("👋 Encerrando partida. Obrigado por jogar!")
        break
