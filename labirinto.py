import pygame
import random
import sys
import math
import heapq

# configuracoes
BASE_TAMANHO = 21
TELA_LARGURA = 620
TELA_ALTURA = 620

# cores
FUNDO = (30, 30, 30)  # fundo grafite neutro
PAREDE = (60, 60, 60)  # cinza escuro
CAMINHO_1 = (20, 20, 20) # piso escuro 1
CAMINHO_2 = (25, 25, 25) # piso escuro 2
SAIDA = (0, 255, 255) # ciano
TEXTO = (255, 255, 255) # texto branco
GRADE = (50, 50, 50) # grade opcional (desativada por padrão)

# inicializacao
pygame.init()
tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
pygame.display.set_caption("SmartMaze - Níveis")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("Courier New", 18)

# imagens e audio
jogador_img = pygame.image.load("runner.png")
inimigo_img = pygame.image.load("enemy.png")
jogador_img = pygame.transform.scale(jogador_img, (20, 20))
inimigo_img = pygame.transform.scale(inimigo_img, (20, 20))

try:
    pygame.mixer.music.load("castlevaniaBloodyTears.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except:
    print("Erro ao carregar música.")


# funcoes de labirinto e IA
def gerar_labirinto(largura, altura):
    labirinto = [[1 for _ in range(largura)] for _ in range(altura)]
    
    def cavar(x, y):
        direcoes = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(direcoes)

        for dx, dy in direcoes:
            nx, ny = x + dx, y + dy
            if 1 <= nx < largura - 1 and 1 <= ny < altura - 1 and labirinto[ny][nx] == 1:
                labirinto[ny][nx] = 0
                labirinto[y + dy // 2][x + dx // 2] = 0
                cavar(nx, ny)

    labirinto[1][1] = 0
    cavar(1, 1)
    return labirinto


def encontrar_saida(labirinto):

    altura, largura = len(labirinto), len(labirinto[0])

    for y in range(altura - 2, 0, -1):
        for x in range(largura - 2, 0, -1):
            if labirinto[y][x] == 0:
                return (x, y)
    return None


def heuristica(a, b):

    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(labirinto, inicio, objetivo):

    fila = [(0, inicio)]
    visitado = {inicio: None}
    custo = {inicio: 0}

    while fila:
        _, atual = heapq.heappop(fila)

        if atual == objetivo:
            caminho = []

            while atual != inicio:
                caminho.append(atual)
                atual = visitado[atual]
            caminho.reverse()
            return caminho
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            vizinho = (atual[0] + dx, atual[1] + dy)

            if (0 <= vizinho[0] < len(labirinto[0]) and
                0 <= vizinho[1] < len(labirinto) and
                labirinto[vizinho[1]][vizinho[0]] == 0):
                novo_custo = custo[atual] + 1

                if vizinho not in custo or novo_custo < custo[vizinho]:
                    custo[vizinho] = novo_custo
                    prioridade = novo_custo + heuristica(objetivo, vizinho)
                    heapq.heappush(fila, (prioridade, vizinho))
                    visitado[vizinho] = atual
    return []


def encontrar_posicao_inimigo(labirinto, jogador, destino):

    altura, largura = len(labirinto), len(labirinto[0])  # pega o tamanho do labirinto (linhas e colunas)
    max_dist = -1 # guarda a maior distancia encontrada ate o jogador
    melhor_pos = jogador  # comeca assumindo que a melhor posicao e a do jogador (sera substituida)
    
    caminho_jogador_saida = a_star(labirinto, jogador, destino) # calcula o caminho princial do jogador ate a saida

    for y in range(altura): # percorre cada linha
        for x in range(largura): # percorre cada coluna

            if labirinto[y][x] == 0 and (x, y) != jogador and (x, y) != destino:  # verifica se a posicao e caminho (0), nao e o jogador, nem a saida
                if (x, y) in caminho_jogador_saida: # verifica se a posicao e um espaco vazio e nao e o jogador nem a saida
                    continue

                caminho_para_jogador = a_star(labirinto, (x, y), jogador) # caminho do ponto ate o jogador
                caminho_para_saida = a_star(labirinto, jogador, destino) # caminho do jogador ate a saida
                caminho_inimigosate_saida = a_star(labirinto, (x, y), destino) # caminho do inimigo ate a saida
                
                if (caminho_para_jogador and caminho_para_saida and (x, y) not in caminho_para_saida and caminho_inimigo_ate_saida and len(caminho_inimigo_ate_saida) > 15): 
                    # garante que ambas rotas existem e que o inimigo nao vai bloquear a saida logo no inicio e evita que o inimigo fique muito perto da saida
                    
                    if len(caminho_para_jogador) > max_dist: # se a distancia ate o jogador for a maior ate agora
                        max_dist = len(caminho_para_jogador)  # atualiza a maior distancia
                        melhor_pos = (x, y) # guarda essa posicao como a melhor
   
    return melhor_pos  # retorna a posicao onde o inimigo sera colocado inicialmente


def reiniciar_jogo(nivel):

    global LARGURA, ALTURA, TAMANHO_BLOCO
    tamanho = BASE_TAMANHO + 2 * (nivel - 1)
    LARGURA = tamanho
    ALTURA = tamanho
    TAMANHO_BLOCO = min(TELA_LARGURA // LARGURA, TELA_ALTURA // ALTURA)

    while True:
        lab = gerar_labirinto(LARGURA, ALTURA)
        jogador = (1, 1)
        destino = encontrar_saida(lab)

        if destino and a_star(lab, jogador, destino):
            inimigo = encontrar_posicao_inimigo(lab, jogador, destino)

            if inimigo != jogador and inimigo != destino:
                return lab, jogador, destino, inimigo


def desenhar(lab, jogador, destino, inimigo, nivel, game_over=False):

    tela.fill(FUNDO)

    for y in range(ALTURA):
        for x in range(LARGURA):
            rect = pygame.Rect(x * TAMANHO_BLOCO, y * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO)

            if lab[y][x] == 1:
                pygame.draw.rect(tela, PAREDE, rect)
            else:
                cor = CAMINHO_1 if (x + y) % 2 == 0 else CAMINHO_2
                pygame.draw.rect(tela, cor, rect)

    tela.blit(pygame.transform.scale(jogador_img, (TAMANHO_BLOCO, TAMANHO_BLOCO)),
               (jogador[0] * TAMANHO_BLOCO, jogador[1] * TAMANHO_BLOCO))
    tela.blit(pygame.transform.scale(inimigo_img, (TAMANHO_BLOCO, TAMANHO_BLOCO)),
               (inimigo[0] * TAMANHO_BLOCO, inimigo[1] * TAMANHO_BLOCO))
    pygame.draw.rect(tela, SAIDA, (destino[0] * TAMANHO_BLOCO, destino[1] * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO), 2)

    texto_nivel = fonte.render(f"NÍVEL {nivel}", True, TEXTO)
    tela.blit(texto_nivel, (10, 10))

    pygame.draw.rect(tela, (80, 80, 80), (TELA_LARGURA - 120, 40, 100, 25))
    tela.blit(fonte.render("Reiniciar", True, TEXTO), (TELA_LARGURA - 110, 45))
    pygame.draw.rect(tela, (80, 80, 80), (TELA_LARGURA - 120, 70, 100, 25))
    tela.blit(fonte.render("Sair", True, TEXTO), (TELA_LARGURA - 110, 75))

    if game_over:
        msg = fonte.render("VOCÊ PERDEU! Clique em Reiniciar.", True, (255, 0, 0))
        tela.blit(msg, (TELA_LARGURA // 2 - 150, TELA_ALTURA // 2))

    pygame.display.flip()


def checar_clique_botao(pos):

    botoes = {
        "reiniciar": pygame.Rect(TELA_LARGURA - 120, 40, 100, 25),
        "sair": pygame.Rect(TELA_LARGURA - 120, 70, 100, 25)
    }
    for nome, rect in botoes.items():
        if rect.collidepoint(pos):
            return nome
    return None

nivel = 1
labirinto, jogador, destino, inimigo = reiniciar_jogo(nivel)
jogo_perdido = False
movimento_pendente = None
contador_frames = 0

jogando = True
while jogando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_r:
                nivel = 1
                labirinto, jogador, destino, inimigo = reiniciar_jogo(nivel)
                jogo_perdido = False
            elif evento.key == pygame.K_ESCAPE:
                jogando = False
            elif evento.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                movimento_pendente = evento.key
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            acao = checar_clique_botao(evento.pos)
            if acao == "reiniciar":
                labirinto, jogador, destino, inimigo = reiniciar_jogo(nivel)
                jogo_perdido = False
            elif acao == "sair":
                jogando = False

    if not jogo_perdido:
        if movimento_pendente:
            novo_x, novo_y = jogador
            if movimento_pendente == pygame.K_LEFT: novo_x -= 1
            elif movimento_pendente == pygame.K_RIGHT: novo_x += 1
            elif movimento_pendente == pygame.K_UP: novo_y -= 1
            elif movimento_pendente == pygame.K_DOWN: novo_y += 1
            if 0 <= novo_x < LARGURA and 0 <= novo_y < ALTURA and labirinto[novo_y][novo_x] == 0:
                jogador = (novo_x, novo_y)
            movimento_pendente = None

        # movimento automatico do inimigo a cada X frames
        contador_frames += 1
        if contador_frames >= 15:
            caminho = a_star(labirinto, inimigo, jogador)
            if caminho:
                inimigo = caminho[0]
            contador_frames = 0

        if jogador == destino:
            nivel += 1
            labirinto, jogador, destino, inimigo = reiniciar_jogo(nivel)

        if jogador == inimigo:
            jogo_perdido = True

    desenhar(labirinto, jogador, destino, inimigo, nivel, jogo_perdido)
    relogio.tick(30)

pygame.quit()
