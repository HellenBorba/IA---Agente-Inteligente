import pygame
import random
import sys
import math
import heapq

# Configurações
TAMANHO_BLOCO = 20
LARGURA = 31
ALTURA = 31
TELA_LARGURA = LARGURA * TAMANHO_BLOCO
TELA_ALTURA = ALTURA * TAMANHO_BLOCO

# Cores retrô
FUNDO = (30, 30, 30)             # fundo grafite neutro
PAREDE = (60, 60, 60)            # cinza escuro
CAMINHO_1 = (20, 20, 20)         # piso escuro 1
CAMINHO_2 = (25, 25, 25)         # piso escuro 2
JOGADOR = (255, 255, 0)          # amarelo tipo Pac-Man
INIMIGO = (255, 0, 0)            # vermelho vivo
SAIDA = (0, 255, 255)            # ciano
GRADE = (50, 50, 50)             # grade opcional (desativada por padrão)

# Inicialização
pygame.init()
tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
pygame.display.set_caption("Labirinto Retrô")
relogio = pygame.time.Clock()

# Fonte retrô (ou fallback)
try:
    fonte = pygame.font.Font("PressStart2P-Regular.ttf", 18)  # Se tiver a fonte
except:
    fonte = pygame.font.SysFont("Courier New", 18)

# Geração do labirinto com Prim
def gerar_labirinto(larg, alt):
    maze = [[1 for _ in range(larg)] for _ in range(alt)]
    start_x, start_y = 1, 1
    maze[start_y][start_x] = 0
    paredes = [(start_x + dx, start_y + dy, start_x, start_y)
               for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]
               if 0 <= start_x+dx < larg and 0 <= start_y+dy < alt]

    while paredes:
        x, y, px, py = paredes.pop(random.randint(0, len(paredes)-1))
        if maze[y][x] == 1:
            mx, my = (x + px) // 2, (y + py) // 2
            maze[y][x] = 0
            maze[my][mx] = 0
            for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < larg and 0 <= ny < alt and maze[ny][nx] == 1:
                    paredes.append((nx, ny, x, y))
    return maze

labirinto = gerar_labirinto(LARGURA, ALTURA)

# Jogador e saída
jogador_x, jogador_y = 1, 1
for y in range(ALTURA - 1, 0, -1):
    for x in range(LARGURA - 1, 0, -1):
        if labirinto[y][x] == 0:
            destino_x, destino_y = x, y
            break
    else:
        continue
    break

# Inimigo longe do jogador
def encontrar_posicao_inimigo():
    max_dist = -1
    posicao = (1, 1)
    for y in range(ALTURA):
        for x in range(LARGURA):
            if labirinto[y][x] == 0:
                d = math.hypot(x - jogador_x, y - jogador_y) + math.hypot(x - destino_x, y - destino_y)
                if d > max_dist:
                    max_dist = d
                    posicao = (x, y)
    return posicao

inimigo_x, inimigo_y = encontrar_posicao_inimigo()

# A*
def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(maze, inicio, fim):
    heap = []
    heapq.heappush(heap, (0, inicio))
    came_from = {}
    custo_atual = {inicio: 0}

    while heap:
        _, atual = heapq.heappop(heap)
        if atual == fim:
            break
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = atual[0] + dx, atual[1] + dy
            if 0 <= nx < LARGURA and 0 <= ny < ALTURA and maze[ny][nx] == 0:
                novo_custo = custo_atual[atual] + 1
                vizinho = (nx, ny)
                if vizinho not in custo_atual or novo_custo < custo_atual[vizinho]:
                    custo_atual[vizinho] = novo_custo
                    prioridade = novo_custo + heuristica(fim, vizinho)
                    heapq.heappush(heap, (prioridade, vizinho))
                    came_from[vizinho] = atual
    caminho = []
    atual = fim
    while atual != inicio:
        if atual not in came_from:
            return []
        caminho.append(atual)
        atual = came_from[atual]
    caminho.reverse()
    return caminho

# Desenho
def desenhar():
    tela.fill(FUNDO)
    for y in range(ALTURA):
        for x in range(LARGURA):
            rect = pygame.Rect(x * TAMANHO_BLOCO, y * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO)
            if labirinto[y][x] == 1:
                pygame.draw.rect(tela, PAREDE, rect, border_radius=3)
            else:
                cor = CAMINHO_1 if (x + y) % 2 == 0 else CAMINHO_2
                pygame.draw.rect(tela, cor, rect)

    # Elementos principais
    pygame.draw.rect(tela, SAIDA, (destino_x * TAMANHO_BLOCO, destino_y * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO), border_radius=5)
    pygame.draw.rect(tela, JOGADOR, (jogador_x * TAMANHO_BLOCO, jogador_y * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO), border_radius=5)
    pygame.draw.rect(tela, INIMIGO, (inimigo_x * TAMANHO_BLOCO, inimigo_y * TAMANHO_BLOCO, TAMANHO_BLOCO, TAMANHO_BLOCO), border_radius=5)

    pygame.display.flip()

# Mensagem
def mostrar_mensagem(texto, cor):
    msg = fonte.render(texto, True, cor)
    rect = msg.get_rect(center=(TELA_LARGURA // 2, TELA_ALTURA // 2))
    tela.blit(msg, rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

# Loop principal
contador_passos = 0
while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif evento.type == pygame.KEYDOWN:  # Alteração para mover apenas uma casa
            novo_x, novo_y = jogador_x, jogador_y
            if evento.key == pygame.K_LEFT:
                novo_x -= 1
            elif evento.key == pygame.K_RIGHT:
                novo_x += 1
            elif evento.key == pygame.K_UP:
                novo_y -= 1
            elif evento.key == pygame.K_DOWN:
                novo_y += 1

            if 0 <= novo_x < LARGURA and 0 <= novo_y < ALTURA and labirinto[novo_y][novo_x] == 0:
                jogador_x, jogador_y = novo_x, novo_y

    contador_passos += 1
    if contador_passos % 10 == 0:
        caminho = a_star(labirinto, (inimigo_x, inimigo_y), (jogador_x, jogador_y))
        if caminho:
            inimigo_x, inimigo_y = caminho[0]

    if jogador_x == destino_x and jogador_y == destino_y:
        desenhar()
        mostrar_mensagem("VOCÊ VENCEU!", SAIDA)

    if jogador_x == inimigo_x and jogador_y == inimigo_y:
        desenhar()
        mostrar_mensagem("PEGARAM VOCÊ!", INIMIGO)

    desenhar()
    relogio.tick(30)