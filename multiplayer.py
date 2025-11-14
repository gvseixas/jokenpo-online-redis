import redis
import time
import uuid
import sys

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
TIMEOUT = 120

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# ============================================================
# UTILIDADES
# ============================================================

def limpar_sala(sala):
    """Remove todas as chaves da sala."""
    keys = r.keys(f"sala:{sala}:*")
    for k in keys:
        r.delete(k)


def escolher_modo():
    print("\n=== JOKENPÔ ONLINE ===")
    print("1️⃣ Criar sala")
    print("2️⃣ Entrar em sala")
    while True:
        m = input("Opção (1/2): ").strip()
        if m in ("1", "2"):
            return m


def criar_sala():
    sala = str(uuid.uuid4())[:8]
    limpar_sala(sala)
    r.set(f"sala:{sala}:status", "aguardando")
    print(f"\n🎮 Sala criada: {sala}")
    return sala


def entrar_sala():
    sala = input("Código da sala: ").strip()

    if not r.exists(f"sala:{sala}:status"):
        print("❌ Sala não existe!")
        sys.exit()

    return sala


def registrar_jogador(sala):
    """Atribui player 1 ou 2 automaticamente."""

    if not r.exists(f"sala:{sala}:player1"):
        r.set(f"sala:{sala}:player1", "ocupado")
        print("Você é o Jogador 1")
        return "1"

    elif not r.exists(f"sala:{sala}:player2"):
        r.set(f"sala:{sala}:player2", "ocupado")
        print("Você é o Jogador 2")
        return "2"

    else:
        print("❌ Sala cheia!")
        sys.exit()


# ============================================================
# BLOQUEIO / SINCRONIZAÇÃO
# ============================================================

def esperar_chave(chave, timeout=TIMEOUT):
    """Espera até que uma chave exista e tenha valor."""
    t0 = time.time()
    while True:
        val = r.get(chave)
        if val is not None:
            return val

        if time.time() - t0 > timeout:
            print(f"⏰ Timeout esperando chave {chave}")
            sys.exit()

        time.sleep(0.3)


def sincronizar(sala, etapa, player):
    """Sincroniza os dois jogadores.
       etapa: 'inicio', 'resultado_lido', 'nova_rodada', etc."""
    me = f"sala:{sala}:sync:{etapa}:{player}"
    other = f"sala:{sala}:sync:{etapa}:{'2' if player == '1' else '1'}"

    r.set(me, "ok", ex=TIMEOUT)

    esperar_chave(other)

    if player == "1":  # só o player 1 limpa
        r.delete(me)
        r.delete(other)


# ============================================================
# JOGO
# ============================================================

def determinar_vencedor(j1, j2):
    if j1 == j2:
        return "Empate!"

    regras = {
        "1": "3",  # Pedra vence Tesoura
        "2": "1",  # Papel vence Pedra
        "3": "2"   # Tesoura vence Papel
    }

    if regras[j1] == j2:
        return "🎉 Você venceu!"
    return "😢 Você perdeu!"


def registrar_jogada(sala, player, jogada):
    r.set(f"sala:{sala}:jogada:{player}", jogada, ex=TIMEOUT)


def ler_jogada(sala, player):
    other = "2" if player == "1" else "1"
    return esperar_chave(f"sala:{sala}:jogada:{other}")


def limpar_jogadas(sala):
    r.delete(f"sala:{sala}:jogada:1")
    r.delete(f"sala:{sala}:jogada:2")


def rematch(sala, player):
    me = f"sala:{sala}:rematch:{player}"
    other_p = "2" if player == "1" else "1"
    other = f"sala:{sala}:rematch:{other_p}"

    d = input("\nJogar novamente? (s/n): ").strip().lower()
    while d not in ("s", "n"):
        d = input("Opção inválida. Jogar novamente? (s/n): ").strip().lower()

    r.set(me, d, ex=TIMEOUT)

    other_decision = esperar_chave(other)

    if player == "1":  # só J1 limpa
        r.delete(me)
        r.delete(other)

    if d == "s" and other_decision == "s":
        return True

    print("\n👋 Alguém não quis continuar. Encerrando...")
    return False


# ============================================================
# MAIN
# ============================================================

modo = escolher_modo()
sala = criar_sala() if modo == "1" else entrar_sala()
player = registrar_jogador(sala)

print(f"\n📌 Sala: {sala} | Jogador {player}")

rodada = 1

while True:
    print(f"\n==============================")
    print(f"🎮 RODADA {rodada}")
    print(f"==============================")

    # 🔄 sincroniza início da rodada
    sincronizar(sala, "inicio", player)

    # escolha jogada
    jog = input("Sua jogada (1=Pedra, 2=Papel, 3=Tesoura): ").strip()
    while jog not in ("1", "2", "3"):
        jog = input("Inválido. Escolha 1/2/3: ")

    registrar_jogada(sala, player, jog)
    jog_oponente = ler_jogada(sala, player)

    # mostrar resultado
    print("\n📊 RESULTADO:")
    print(f"Você: {jog}")
    print(f"Oponente: {jog_oponente}")
    print(determinar_vencedor(jog, jog_oponente))

    # 🔄 Agora ambos precisam ver o resultado antes de limpar
    sincronizar(sala, "resultado_lido", player)

    # 🧹 Somente o player 1 limpa
    if player == "1":
        limpar_jogadas(sala)

    # rematch
    if not rematch(sala, player):
        break

    rodada += 1
    sincronizar(sala, "nova_rodada", player)

print("\n🏁 Fim da partida.")

