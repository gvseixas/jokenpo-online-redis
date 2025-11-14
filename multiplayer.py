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
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
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
        print(f"\n🎮 Sala criada com sucesso! Código: {sala}")
        print(f"📊 Chave criada: sala:{sala}:status")
    except Exception as e:
        print(f"❌ Erro ao criar sala: {e}")
        sys.exit()

    return sala, "1"


def entrar_sala():
    sala = input("Digite o código da sala para entrar: ").strip()
    try:
        if not r.exists(f"sala:{sala}:status"):
            print("❌ Sala não encontrada!")
            # Lista todas as salas disponíveis
            todas_salas = r.keys("sala:*:status")
            print(f"📋 Salas disponíveis: {todas_salas}")
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
    print(f"🔍 Aguardando chave: {chave}")
    check_count = 0
    while True:
        try:
            existe = r.exists(chave)
            check_count += 1
            if check_count % 10 == 0:  # Mostra a cada 10 verificações
                tempo_decorrido = time.time() - start_time
                print(f"   [Tentativa {check_count}] {tempo_decorrido:.1f}s - Checando {chave}... existe={existe}")
            if existe:
                print(f"   ✅ Chave encontrada após {check_count} tentativas!")
                return
        except Exception as e:
            print(f"❌ Erro ao aguardar jogada: {e}")
            sys.exit()

        if time.time() - start_time > TIMEOUT:
            print(f"⏰ Timeout! O outro jogador não respondeu após {check_count} tentativas.")
            print(f"⏰ Tempo decorrido: {time.time() - start_time:.1f}s")
            
            # Debug: listar chaves da sala
            try:
                todas_chaves = r.keys(f"sala:*:jogada")
                print(f"📋 Chaves de jogada no Redis: {todas_chaves}")
            except:
                pass
            
            sys.exit()
        time.sleep(0.5)


def sincronizar_inicio_rodada(sala, player):
    ready_self = f"sala:{sala}:ready:{player}"
    ready_other = f"sala:{sala}:ready:{'2' if player == '1' else '1'}"

    print(f"\n🔄 SINCRONIZANDO RODADA")
    print(f"   Jogador: {player}")
    print(f"   Chave própria: {ready_self}")
    print(f"   Chave do oponente: {ready_other}")

    try:
        r.set(ready_self, "ok", ex=TIMEOUT)
        print(f"✅ Sinalizou prontidão: {ready_self}")
        
        # Verificar imediatamente se foi gravado
        verificacao = r.get(ready_self)
        print(f"   Verificação: {ready_self} = {verificacao}")
    except Exception as e:
        print(f"❌ Erro ao sinalizar prontidão: {e}")
        sys.exit()

    print("⏳ Aguardando o outro jogador ficar pronto...")
    start_time = time.time()
    check_count = 0
    while True:
        try:
            existe = r.exists(ready_other)
            check_count += 1
            if check_count % 10 == 0:
                print(f"   [Tentativa {check_count}] Checando {ready_other}... existe={existe}")
            
            if existe:
                print(f"   ✅ Oponente pronto após {check_count} tentativas!")
                break
        except Exception as e:
            print(f"❌ Erro ao verificar prontidão do oponente: {e}")
            sys.exit()

        if time.time() - start_time > TIMEOUT:
            print(f"⏰ Timeout! Oponente não ficou pronto após {check_count} tentativas.")
            try:
                r.delete(ready_self)
            except:
                pass
            sys.exit()
        time.sleep(0.5)

    # ✅ CORREÇÃO: Apenas o Jogador 1 deleta ambas as chaves
    if player == "1":
        try:
            print("🧹 Limpando sinalizadores...")
            r.delete(ready_self)
            r.delete(ready_other)
            print("✅ Sinalizadores limpos. Iniciando rodada...\n")
        except Exception as e:
            print(f"❌ Erro ao limpar sinalizadores: {e}")
            sys.exit()
    else:
        # Jogador 2 apenas aguarda um pouco para Jogador 1 deletar
        print("⏳ Aguardando limpeza dos sinalizadores...")
        time.sleep(1)
        print("✅ Pronto! Iniciando rodada...\n") 


# ---------------------- FUNÇÃO: DETERMINAR VENCEDOR ----------------------
def determinar_vencedor(j1, j2):
    """
    Retorna o resultado a partir das jogadas:
    1 = Pedra, 2 = Papel, 3 = Tesoura.
    """
    try:
        a = int(j1)
        b = int(j2)
    except Exception:
        return "Erro: jogadas inválidas"

    if a == b:
        return "Empate!"
    if (a == 1 and b == 3) or (a == 2 and b == 1) or (a == 3 and b == 2):
        return "🎉 Você venceu!"
    return "😢 Você perdeu!"


# ---------------------- PROGRAMA PRINCIPAL ----------------------
modo = escolher_modo()
if modo == "1":
    sala, player = criar_sala()
else:
    sala, player = entrar_sala()

key_self = f"sala:{sala}:j{player}"
key_other = f"sala:{sala}:j2" if player == "1" else f"sala:{sala}:j1"

print(f"\n📌 INFORMAÇÕES DA PARTIDA:")
print(f"   Sala: {sala}")
print(f"   Você é: Jogador {player}")
print(f"   Sua chave: {key_self}")
print(f"   Chave do oponente: {key_other}\n")

# ---------------------- LOOP DO JOGO ----------------------
rodada = 0
while True:
    rodada += 1
    print(f"\n{'='*50}")
    print(f"🎮 RODADA {rodada}")
    print(f"{'='*50}\n")
    
    sincronizar_inicio_rodada(sala, player)

    jogada = input("Escolha sua jogada (1=👊 Pedra, 2=🖐 Papel, 3=✌ Tesoura): ").strip()
    while jogada not in ["1", "2", "3"]:
        jogada = input("Opção inválida! Escolha 1, 2 ou 3: ").strip()

    try:
        r.set(f"{key_self}:jogada", jogada, ex=TIMEOUT)
        print(f"✅ Sua jogada gravada: {jogada}")
        
        # Verificar imediatamente
        verificacao = r.get(f"{key_self}:jogada")
        print(f"   Verificação: {key_self}:jogada = {verificacao}")
    except Exception as e:
        print(f"❌ Erro ao gravar sua jogada: {e}")
        sys.exit()

    print("⏳ Aguardando jogada do oponente...")
    aguardar_jogada(f"{key_other}:jogada")

    try:
        jogada_atual = r.get(f"{key_self}:jogada")
        jogada_oponente = r.get(f"{key_other}:jogada")
        
        print(f"\n📊 RESULTADO:")
        print(f"   Sua jogada: {jogada_atual}")
        print(f"   Jogada do oponente: {jogada_oponente}")
        
        if jogada_atual is None or jogada_oponente is None:
            print("❌ Erro: não conseguiu recuperar uma das jogadas!")
            sys.exit()
        
        jogada_atual = int(jogada_atual)
        jogada_oponente = int(jogada_oponente)
    except Exception as e:
        print(f"❌ Erro ao recuperar jogadas: {e}")
        sys.exit()

    resultado = determinar_vencedor(jogada_atual, jogada_oponente)
    print(f"🎯 {resultado}\n")

    try:
        r.delete(f"{key_self}:jogada")
        r.delete(f"{key_other}:jogada")
        print("✅ Jogadas limpas para próxima rodada.")
    except Exception as e:
        print(f"❌ Erro ao limpar jogadas: {e}")
        sys.exit()

    jogar_novamente = input("\nDeseja jogar novamente? (s/n): ").strip().lower()
    if jogar_novamente != "s":
        print("👋 Obrigado por jogar! Encerrando...")
        sys.exit()
