import pygame
import random
import sys
import math
import heapq

# CONFIGURAÇÕES GERAIS
BASE_TAMANHO = 21
TELA_LARGURA = 620
TELA_ALTURA = 620
MAX_NIVEIS = 5 

# CORES 
FUNDO = (30, 30, 30)
PAREDE = (60, 60, 60)
CAMINHO_1 = (20, 20, 20)
CAMINHO_2 = (25, 25, 25)
SAIDA_COR = (0, 255, 255)  
TEXTO_COR_PADRAO = (255, 255, 255)

# Cores Tema Arcade
ARCADE_AZUL_ESCURO = (0, 0, 100)
ARCADE_AZUL_MEDIO = (0, 50, 180)
ARCADE_CIANO = (0, 200, 255)
ARCADE_AMARELO = (255, 255, 0)
ARCADE_LARANJA = (255, 165, 0)
ARCADE_VERDE = (0, 200, 0)
ARCADE_VERMELHO = (200, 0, 0)
ARCADE_BRANCO = (240, 240, 240)

# INICIALIZAÇÃO DO PYGAME
pygame.init() 
tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
pygame.display.set_caption("SmartMaze Arcade!")
relogio = pygame.time.Clock()

# FONTES
fonte_arcade_titulo = pygame.font.SysFont("Impact", 52)
fonte_arcade_subtitulo = pygame.font.SysFont("Courier New", 30, bold=True)
fonte_arcade_botao = pygame.font.SysFont("Courier New", 24, bold=True)
fonte_arcade_texto = pygame.font.SysFont("Courier New", 22)


# EVENTO PERSONALIZADO PARA MÚSICA
MUSICA_TERMINOU = pygame.USEREVENT + 1

# CARREGAMENTO DE IMAGENS
try:
    jogador_img_original = pygame.image.load("runner.png")
    inimigo_img_original = pygame.image.load("enemy.png")
except pygame.error as e:
    sys.exit()

# CARREGAMENTO DE MÚSICA DE FUNDO
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        print("Pygame Mixer inicializado.")

    musica_fundo_path = "castlevaniaBloodyTears.mp3" 
    pygame.mixer.music.load(musica_fundo_path)
    print(f"Música '{musica_fundo_path}' carregada.")
    pygame.mixer.music.set_volume(0.3) 
    pygame.mixer.music.set_endevent(MUSICA_TERMINOU) # Configura o evento para fim da música
    pygame.mixer.music.play(0) # Toca uma vez, o evento MUSICA_TERMINOU cuidará do loop
except pygame.error as e:
    print(f"Erro música de fundo")

# CARREGAMENTO DE EFEITOS SONOROS
som_passar_fase = None
som_morrer = None
som_ganhar_jogo = None
som_botao_clique = None 

try:
    som_passar_fase = pygame.mixer.Sound("passoudefase.wav")
    som_morrer = pygame.mixer.Sound("perdeu.wav")
    som_ganhar_jogo = pygame.mixer.Sound("venceu.wav")
    som_botao_clique = pygame.mixer.Sound("botao.wav") 

    if som_passar_fase: som_passar_fase.set_volume(0.6)
    if som_morrer: som_morrer.set_volume(0.7)
    if som_ganhar_jogo: som_ganhar_jogo.set_volume(0.8)
    if som_botao_clique: som_botao_clique.set_volume(0.5)
    print("Efeitos sonoros carregados.")
except pygame.error as e:
    print(f"Erro ao carregar SFX: {e}. Verifique os arquivos .wav.")

# Variáveis Globais para dimensões do labirinto (número de células)
LARGURA_CELULAS = 0
ALTURA_CELULAS = 0

# Funções do Jogo
def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def gerar_labirinto_modificado(largura, altura, proporcao_loops=0.1):
    labirinto = [[1 for _ in range(largura)] for _ in range(altura)]
    def cavar(x, y):
        labirinto[y][x] = 0
        direcoes = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(direcoes)
        for dx, dy in direcoes:
            nx, ny = x + dx, y + dy
            parede_x, parede_y = x + dx // 2, y + dy // 2
            if 0 < nx < largura - 1 and 0 < ny < altura - 1 and labirinto[ny][nx] == 1:
                labirinto[parede_y][parede_x] = 0; cavar(nx, ny)
    cavar(1, 1)
    paredes_candidatas = []
    for r_loop in range(1, altura - 1):
        for c_loop in range(1, largura - 1):
            if labirinto[r_loop][c_loop] == 1:
                if r_loop % 2 == 1 and c_loop % 2 == 0:
                    if c_loop > 0 and c_loop < largura - 1 and labirinto[r_loop][c_loop-1] == 0 and labirinto[r_loop][c_loop+1] == 0:
                        paredes_candidatas.append((r_loop, c_loop))
                elif r_loop % 2 == 0 and c_loop % 2 == 1:
                    if r_loop > 0 and r_loop < altura - 1 and labirinto[r_loop-1][c_loop] == 0 and labirinto[r_loop+1][c_loop] == 0:
                        paredes_candidatas.append((r_loop, c_loop))
    random.shuffle(paredes_candidatas)
    num_loops_a_criar = int(len(paredes_candidatas) * proporcao_loops)
    for _ in range(num_loops_a_criar):
        if paredes_candidatas:
            r_parede, c_parede = paredes_candidatas.pop(); labirinto[r_parede][c_parede] = 0
    return labirinto

def encontrar_saida_aleatoria(labirinto, jogador_pos):
    altura_lab, largura_lab = len(labirinto), len(labirinto[0])
    candidatos_saida = []
    min_dist_para_saida = (largura_lab + altura_lab) / 3.8
    for r_idx in range(1, altura_lab - 1):
        for c_idx in range(1, largura_lab - 1):
            if labirinto[r_idx][c_idx] == 0:
                pos_atual = (c_idx, r_idx)
                if pos_atual == jogador_pos: continue
                distancia_do_jogador = heuristica(jogador_pos, pos_atual)
                if distancia_do_jogador >= min_dist_para_saida:
                    candidatos_saida.append({'pos': pos_atual, 'dist': distancia_do_jogador})
    if not candidatos_saida:
        for r_idx in range(1, altura_lab - 1):
            for c_idx in range(1, largura_lab - 1):
                if labirinto[r_idx][c_idx] == 0:
                    pos_atual = (c_idx, r_idx)
                    if pos_atual == jogador_pos: continue
                    candidatos_saida.append({'pos': pos_atual, 'dist': heuristica(jogador_pos, pos_atual)})
    if candidatos_saida:
        candidatos_saida.sort(key=lambda c_sort: c_sort['dist'], reverse=True)
        num_top_candidatos = max(1, len(candidatos_saida) // 2)
        return random.choice(candidatos_saida[:num_top_candidatos])['pos']
    else:
        for r_fb in range(altura_lab - 2, 0, -1):
            for c_fb in range(largura_lab - 2, 0, -1):
                if labirinto[r_fb][c_fb] == 0 and (c_fb, r_fb) != jogador_pos: return (c_fb, r_fb)
        return (1,3) if (1,3) != jogador_pos and altura_lab > 3 and largura_lab > 3 and labirinto[3][1] == 0 else (largura_lab-2, altura_lab-2)

def a_star(labirinto, inicio, objetivo):
    altura_lab, largura_lab = len(labirinto), len(labirinto[0])
    if not (inicio and objetivo and 0 <= inicio[0] < largura_lab and 0 <= inicio[1] < altura_lab and
            0 <= objetivo[0] < largura_lab and 0 <= objetivo[1] < altura_lab and
            labirinto[inicio[1]][inicio[0]] == 0 and labirinto[objetivo[1]][objetivo[0]] == 0):
        return []
    fila = [(0, inicio)]; visitado_caminho = {inicio: None}; custo_g = {inicio: 0}
    while fila:
        _, atual = heapq.heappop(fila)
        if atual == objetivo:
            caminho = []; temp = atual
            while temp != inicio: caminho.append(temp); temp = visitado_caminho[temp]
            caminho.reverse(); return caminho
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            vizinho = (atual[0]+dx, atual[1]+dy)
            if (0 <= vizinho[0] < largura_lab and 0 <= vizinho[1] < altura_lab and labirinto[vizinho[1]][vizinho[0]] == 0):
                novo_custo_g = custo_g[atual] + 1
                if vizinho not in custo_g or novo_custo_g < custo_g[vizinho]:
                    custo_g[vizinho] = novo_custo_g
                    heapq.heappush(fila, (novo_custo_g + heuristica(objetivo, vizinho), vizinho)); visitado_caminho[vizinho] = atual
    return []

def encontrar_posicao_inimigo(labirinto, jogador_pos, destino_pos):
    altura_lab, largura_lab = len(labirinto), len(labirinto[0])
    candidatos_inimigo = []
    q_oposto_min_x = largura_lab * 2 // 3 ; q_oposto_min_y = altura_lab * 2 // 3 # Prioriza o terço oposto
    for r_cand in range(1, altura_lab - 1):
        for c_cand in range(1, largura_lab - 1):
            pos_potencial = (c_cand, r_cand)
            if labirinto[r_cand][c_cand] == 0 and pos_potencial != jogador_pos and pos_potencial != destino_pos:
                dist_do_jogador = heuristica(jogador_pos, pos_potencial)
                if dist_do_jogador < max(6, (largura_lab + altura_lab) // 6): continue # Distância mínima maior
                if not a_star(labirinto, pos_potencial, jogador_pos): continue
                pontuacao = dist_do_jogador * 2.5 # Valoriza mais a distância
                if c_cand >= q_oposto_min_x and r_cand >= q_oposto_min_y: pontuacao += (largura_lab + altura_lab) * 1.5 # Bônus maior
                caminho_jog_saida = a_star(labirinto, jogador_pos, destino_pos)
                if caminho_jog_saida and pos_potencial in caminho_jog_saida: pontuacao -= (largura_lab + altura_lab) 
                candidatos_inimigo.append({'pos': pos_potencial, 'score': pontuacao})
    if candidatos_inimigo:
        candidatos_inimigo.sort(key=lambda x: x['score'], reverse=True)
        top_n = min(len(candidatos_inimigo), 5) # Mais opções para aleatoriedade
        return random.choice(candidatos_inimigo[:top_n])['pos']
    else:
        for r_fb in range(altura_lab - 2, 0, -1):
            for c_fb in range(largura_lab - 2, 0, -1):
                pos_fb = (c_fb, r_fb)
                if labirinto[r_fb][c_fb] == 0 and pos_fb != jogador_pos and pos_fb != destino_pos:
                    if a_star(labirinto, pos_fb, jogador_pos): return pos_fb
        return (largura_lab - 2, altura_lab - 2)

def reiniciar_jogo(nivel_atual_param):
    global LARGURA_CELULAS, ALTURA_CELULAS, MAX_NIVEIS
    tamanho = BASE_TAMANHO + 2 * (nivel_atual_param - 1)
    tamanho = min(tamanho, BASE_TAMANHO + 2 * (MAX_NIVEIS + 2)) # Ajustado limite
    LARGURA_CELULAS, ALTURA_CELULAS = tamanho, tamanho
    prop_loops = 0.05 + (nivel_atual_param / 150.0); prop_loops = min(prop_loops, 0.15) 
    max_tentativas = 25
    for tentativa in range(max_tentativas):
        lab = gerar_labirinto_modificado(LARGURA_CELULAS, ALTURA_CELULAS, proporcao_loops=prop_loops)
        jogador_pos_inicial = (1, 1)
        destino_pos_gerado = encontrar_saida_aleatoria(lab, jogador_pos_inicial)
        if destino_pos_gerado and a_star(lab, jogador_pos_inicial, destino_pos_gerado):
            inimigo_pos_gerado = encontrar_posicao_inimigo(lab, jogador_pos_inicial, destino_pos_gerado)
            if (inimigo_pos_gerado and inimigo_pos_gerado != jogador_pos_inicial and 
                inimigo_pos_gerado != destino_pos_gerado and
                a_star(lab, inimigo_pos_gerado, jogador_pos_inicial)):
                print(f"N{nivel_atual_param} G(T{tentativa+1},L{prop_loops:.2f},S{LARGURA_CELULAS})")
                return lab, jogador_pos_inicial, destino_pos_gerado, inimigo_pos_gerado
    print(f"ALERTA: Falha ao gerar N{nivel_atual_param}. Usando fallback."); LARG_FB, ALT_FB = BASE_TAMANHO, BASE_TAMANHO
    lab_fb = [[1 for _ in range(LARG_FB)] for _ in range(ALT_FB)]
    for r_fb in range(1,ALT_FB-1,2):
        for c_fb in range(1,LARG_FB-1,2):
            lab_fb[r_fb][c_fb]=0
            if c_fb+1 < LARG_FB-1: lab_fb[r_fb][c_fb+1]=0
        if r_fb+1 < ALT_FB-1:
            for c_corr in range(1,LARG_FB-1):
                if lab_fb[r_fb][c_corr]==0 or (r_fb+2 < ALT_FB-1 and lab_fb[r_fb+2][c_corr]==0): lab_fb[r_fb+1][c_corr]=0
    LARGURA_CELULAS,ALTURA_CELULAS=LARG_FB,ALT_FB; jogador_fb=(1,1); lab_fb[1][1]=0
    destino_fb=(LARG_FB-2,ALT_FB-2); 
    if ALT_FB-2>=0 and LARG_FB-2>=0: lab_fb[ALT_FB-2][LARG_FB-2]=0
    if destino_fb==jogador_fb: destino_fb=(1,ALT_FB-2)
    if ALT_FB-2>=0 and lab_fb[ALT_FB-2][1]==1: lab_fb[ALT_FB-2][1]=0
    inimigo_fb=encontrar_posicao_inimigo(lab_fb,jogador_fb,destino_fb)
    if not inimigo_fb: inimigo_fb=(LARG_FB-2,1)
    if 1<LARG_FB-2 and lab_fb[1][LARG_FB-2]==1: lab_fb[1][LARG_FB-2]=0
    return lab_fb,jogador_fb,destino_fb,inimigo_fb

def get_cell_render_params(cell_c, cell_r, num_cols, num_rows, screen_w, screen_h):
    base_w = screen_w // num_cols; base_h = screen_h // num_rows
    remainder_w = screen_w % num_cols; remainder_h = screen_h % num_rows
    render_w = base_w + (1 if cell_c < remainder_w else 0)
    render_h = base_h + (1 if cell_r < remainder_h else 0)
    pos_x = cell_c * base_w + min(cell_c, remainder_w)
    pos_y = cell_r * base_h + min(cell_r, remainder_h)
    return pygame.Rect(pos_x, pos_y, render_w, render_h)

def desenhar(lab, jogador_pos, destino_pos, inimigo_pos, nivel_atual_param, game_over=False):
    global LARGURA_CELULAS, ALTURA_CELULAS 
    tela.fill(FUNDO)
    if LARGURA_CELULAS <= 0 or ALTURA_CELULAS <= 0: return None
    for r_draw in range(ALTURA_CELULAS):
        for c_draw in range(LARGURA_CELULAS):
            cell_rect = get_cell_render_params(c_draw, r_draw, LARGURA_CELULAS, ALTURA_CELULAS, TELA_LARGURA, TELA_ALTURA)
            if lab[r_draw][c_draw] == 1: pygame.draw.rect(tela, PAREDE, cell_rect)
            else: pygame.draw.rect(tela, CAMINHO_1 if (c_draw + r_draw) % 2 == 0 else CAMINHO_2, cell_rect)
    if jogador_pos:
        rect_jogador = get_cell_render_params(jogador_pos[0], jogador_pos[1], LARGURA_CELULAS, ALTURA_CELULAS, TELA_LARGURA, TELA_ALTURA)
        jogador_img_scaled = pygame.transform.scale(jogador_img_original, (rect_jogador.width, rect_jogador.height))
        tela.blit(jogador_img_scaled, rect_jogador.topleft)
    if inimigo_pos:
        rect_inimigo = get_cell_render_params(inimigo_pos[0], inimigo_pos[1], LARGURA_CELULAS, ALTURA_CELULAS, TELA_LARGURA, TELA_ALTURA)
        inimigo_img_scaled = pygame.transform.scale(inimigo_img_original, (rect_inimigo.width, rect_inimigo.height))
        tela.blit(inimigo_img_scaled, rect_inimigo.topleft)
    if destino_pos:
        rect_saida = get_cell_render_params(destino_pos[0], destino_pos[1], LARGURA_CELULAS, ALTURA_CELULAS, TELA_LARGURA, TELA_ALTURA)
        pygame.draw.rect(tela, SAIDA_COR, rect_saida, 3)  
    texto_nivel_render = fonte_arcade_texto.render(f"NÍVEL {nivel_atual_param}", True, ARCADE_AMARELO) 
    tela.blit(texto_nivel_render, (15, 15))
    if game_over: 
        s = pygame.Surface((TELA_LARGURA, TELA_ALTURA), pygame.SRCALPHA); s.fill((10,10,10,200)); tela.blit(s, (0,0)) 
        mensagem_perdeu = "GAME OVER"; texto_perdeu_render = fonte_arcade_titulo.render(mensagem_perdeu, True, ARCADE_VERMELHO)
        sub_msg_perdeu = "Você foi pego!"; sub_texto_perdeu_render = fonte_arcade_texto.render(sub_msg_perdeu, True, ARCADE_BRANCO)

        padding_x, padding_y = 40, 30
        rect_msg_largura = max(texto_perdeu_render.get_width(), sub_texto_perdeu_render.get_width()) + 2 * padding_x
        altura_textos_go = texto_perdeu_render.get_height() + sub_texto_perdeu_render.get_height() + 15
        rect_msg_altura = altura_textos_go + 2 * padding_y + 140 
        rect_msg_x = (TELA_LARGURA - rect_msg_largura) // 2; rect_msg_y = (TELA_ALTURA - rect_msg_altura) // 2
        rect_caixa_perdeu = pygame.Rect(rect_msg_x, rect_msg_y, rect_msg_largura, rect_msg_altura)
        
        pygame.draw.rect(tela, ARCADE_AZUL_ESCURO, rect_caixa_perdeu, border_radius=15)
        pygame.draw.rect(tela, ARCADE_CIANO, rect_caixa_perdeu, 4, border_radius=15)
        
        tela.blit(texto_perdeu_render, (rect_caixa_perdeu.centerx - texto_perdeu_render.get_width() // 2, rect_msg_y + padding_y))
        tela.blit(sub_texto_perdeu_render, (rect_caixa_perdeu.centerx - sub_texto_perdeu_render.get_width() // 2, rect_msg_y + padding_y + texto_perdeu_render.get_height() + 10))

        largura_btn, altura_btn = 220, 55; espaco_btn = 25
        y_botoes = rect_msg_y + padding_y + altura_textos_go + 40

        btn_reiniciar_rect = pygame.Rect(rect_caixa_perdeu.centerx - largura_btn // 2, y_botoes, largura_btn, altura_btn)
        pygame.draw.rect(tela, ARCADE_AZUL_MEDIO, btn_reiniciar_rect, border_radius=8); pygame.draw.rect(tela, ARCADE_AMARELO, btn_reiniciar_rect, 3, border_radius=8)
        texto_reiniciar = fonte_arcade_botao.render("Reiniciar", True, ARCADE_AMARELO)
        tela.blit(texto_reiniciar, (btn_reiniciar_rect.centerx - texto_reiniciar.get_width() // 2, btn_reiniciar_rect.centery - texto_reiniciar.get_height() // 2))
        
        btn_sair_rect = pygame.Rect(rect_caixa_perdeu.centerx - largura_btn // 2, y_botoes + altura_btn + espaco_btn, largura_btn, altura_btn)
        pygame.draw.rect(tela, ARCADE_VERMELHO, btn_sair_rect, border_radius=8); pygame.draw.rect(tela, ARCADE_LARANJA, btn_sair_rect, 3, border_radius=8)
        texto_sair = fonte_arcade_botao.render("Sair do Jogo", True, ARCADE_BRANCO)
        tela.blit(texto_sair, (btn_sair_rect.centerx - texto_sair.get_width() // 2, btn_sair_rect.centery - texto_sair.get_height() // 2))
        return btn_reiniciar_rect, btn_sair_rect
    return None

def tela_inicial():
    btn_larg, btn_alt = 260, 65 
    btn_y_offset = 90 

    while True:
        tela.fill(FUNDO) 

        titulo_render = fonte_arcade_titulo.render("SMART MAZE", True, ARCADE_AMARELO)  
        rect_titulo_largura = titulo_render.get_width() + 80 
        rect_titulo_altura = titulo_render.get_height() + 40 
        rect_titulo_x = (TELA_LARGURA - rect_titulo_largura) // 2 
        rect_titulo_y = 80 
        
        pygame.draw.rect(tela, ARCADE_AZUL_ESCURO, (rect_titulo_x, rect_titulo_y, rect_titulo_largura, rect_titulo_altura), border_radius=15) 
        pygame.draw.rect(tela, ARCADE_CIANO, (rect_titulo_x, rect_titulo_y, rect_titulo_largura, rect_titulo_altura), 5, border_radius=15) 
        tela.blit(titulo_render, (rect_titulo_x + (rect_titulo_largura - titulo_render.get_width()) // 2, 
                                  rect_titulo_y + (rect_titulo_altura - titulo_render.get_height()) // 2)) 

        btn_iniciar = pygame.Rect(TELA_LARGURA//2 - btn_larg//2, rect_titulo_y + rect_titulo_altura + btn_y_offset, btn_larg, btn_alt) 
        btn_sair_inicial = pygame.Rect(TELA_LARGURA//2 - btn_larg//2, btn_iniciar.bottom + 30, btn_larg, btn_alt) 

        pygame.draw.rect(tela, ARCADE_AZUL_MEDIO, btn_iniciar, border_radius=10) 
        pygame.draw.rect(tela, ARCADE_AMARELO, btn_iniciar, 3, border_radius=10) 
        pygame.draw.rect(tela, ARCADE_VERMELHO, btn_sair_inicial, border_radius=10) 
        pygame.draw.rect(tela, ARCADE_BRANCO, btn_sair_inicial, 3, border_radius=10) 

        texto_iniciar = fonte_arcade_botao.render("INICIAR", True, ARCADE_AMARELO) 
        texto_sair_menu = fonte_arcade_botao.render("SAIR", True, ARCADE_BRANCO) 

        tela.blit(texto_iniciar, (btn_iniciar.centerx - texto_iniciar.get_width()//2, btn_iniciar.centery - texto_iniciar.get_height()//2)) 
        tela.blit(texto_sair_menu, (btn_sair_inicial.centerx - texto_sair_menu.get_width()//2, btn_sair_inicial.centery - texto_sair_menu.get_height()//2)) 

        instr_texto = fonte_arcade_texto.render("Use as setas para mover seu personagem", True, ARCADE_CIANO) 
        tela.blit(instr_texto, (TELA_LARGURA//2 - instr_texto.get_width()//2, TELA_ALTURA - 60)) 


        for evento in pygame.event.get(): 
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit() 
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1: 
                if btn_iniciar.collidepoint(evento.pos): 
                    if som_botao_clique: som_botao_clique.play() 
                    return  
                if btn_sair_inicial.collidepoint(evento.pos): 
                    if som_botao_clique: som_botao_clique.play() 
                    pygame.quit(); sys.exit() 
        pygame.display.flip(); relogio.tick(30)

# TELA DE VITÓRIA
def tela_vitoria():
    padding_x_v, padding_y_v = 40, 30  
    espaco_entre_textos_v = 15        
    espaco_total_botoes_v = 140     
    
    btn_larg_v, btn_alt_v = 280, 60 
    espaco_btn_v = 25 # Espaço entre os botões

    loop_tela_vitoria = True
    while loop_tela_vitoria:
        tela.fill(FUNDO) 

        titulo_vitoria_render = fonte_arcade_titulo.render("VITÓRIA!", True, ARCADE_AMARELO)
        subtitulo_vitoria_render = fonte_arcade_subtitulo.render("Você é Mestre do Labirinto!", True, ARCADE_AMARELO) # Ciano para subtítulo

        largura_min_caixa_v = 450 
        largura_caixa = max(largura_min_caixa_v, 
                            titulo_vitoria_render.get_width() + 2 * padding_x_v, 
                            subtitulo_vitoria_render.get_width() + 2 * padding_x_v)  
        # Cálculo da altura da caixa
        altura_textos_v = titulo_vitoria_render.get_height() + subtitulo_vitoria_render.get_height() + espaco_entre_textos_v
        altura_caixa_v = altura_textos_v + (2 * padding_y_v) + espaco_total_botoes_v
   
        x_caixa = (TELA_LARGURA - largura_caixa) // 2
        y_caixa = (TELA_ALTURA - altura_caixa_v) // 2

        pygame.draw.rect(tela, ARCADE_AZUL_ESCURO, (x_caixa, y_caixa, largura_caixa, altura_caixa_v), border_radius=20)
        pygame.draw.rect(tela, ARCADE_AMARELO, (x_caixa, y_caixa, largura_caixa, altura_caixa_v), 5, border_radius=20) # Borda AMARELA

        # Posicionar textos dentro da caixa
        y_pos_titulo_v = y_caixa + padding_y_v
        tela.blit(titulo_vitoria_render, (x_caixa + (largura_caixa - titulo_vitoria_render.get_width()) // 2, y_pos_titulo_v))     
        y_pos_subtitulo_v = y_pos_titulo_v + titulo_vitoria_render.get_height() + espaco_entre_textos_v
        tela.blit(subtitulo_vitoria_render, (x_caixa + (largura_caixa - subtitulo_vitoria_render.get_width()) // 2, y_pos_subtitulo_v))

        # Posicionar botões
        y_base_botoes_v = y_pos_subtitulo_v + subtitulo_vitoria_render.get_height() + 40

        btn_jogar_novamente_rect = pygame.Rect(x_caixa + (largura_caixa - btn_larg_v) // 2, y_base_botoes_v, btn_larg_v, btn_alt_v)
        btn_sair_vitoria_rect = pygame.Rect(x_caixa + (largura_caixa - btn_larg_v) // 2, y_base_botoes_v + btn_alt_v + espaco_btn_v, btn_larg_v, btn_alt_v)

        pygame.draw.rect(tela, ARCADE_AZUL_MEDIO, btn_jogar_novamente_rect, border_radius=10)
        pygame.draw.rect(tela, ARCADE_AMARELO, btn_jogar_novamente_rect, 3, border_radius=10)
        pygame.draw.rect(tela, ARCADE_VERMELHO, btn_sair_vitoria_rect, border_radius=10)
        pygame.draw.rect(tela, ARCADE_BRANCO, btn_sair_vitoria_rect, 3, border_radius=10)

        texto_jogar_novamente = fonte_arcade_botao.render("Jogar novamente", True, ARCADE_AMARELO)  
        texto_sair_final = fonte_arcade_botao.render("Sair do jogo", True, ARCADE_BRANCO)

        tela.blit(texto_jogar_novamente, (btn_jogar_novamente_rect.centerx - texto_jogar_novamente.get_width()//2, btn_jogar_novamente_rect.centery - texto_jogar_novamente.get_height()//2))
        tela.blit(texto_sair_final, (btn_sair_vitoria_rect.centerx - texto_sair_final.get_width()//2, btn_sair_vitoria_rect.centery - texto_sair_final.get_height()//2))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if btn_jogar_novamente_rect.collidepoint(evento.pos):
                    if som_botao_clique: som_botao_clique.play()
                    return "JOGAR_NOVAMENTE" 
                if btn_sair_vitoria_rect.collidepoint(evento.pos):
                    if som_botao_clique: som_botao_clique.play()
                    pygame.quit(); sys.exit()
        pygame.display.flip()
        relogio.tick(30)

def main_game_loop():
    global LARGURA_CELULAS, ALTURA_CELULAS, MAX_NIVEIS
    tela_inicial()
    nivel_atual = 1
    labirinto_atual, jogador_pos, destino_pos, inimigo_pos = reiniciar_jogo(nivel_atual)
    jogo_esta_perdido = False
    movimento_jogador_pendente = None
    frames_inimigo_contador = 0
    velocidade_inimigo_frames = 15
    btn_reiniciar_nivel_rect = None
    btn_sair_jogo_rect = None
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: rodando = False
            # --- Tratamento de evento para loop da música ---
            elif evento.type == MUSICA_TERMINOU:
            
                pygame.mixer.music.play(0) # Toca mais uma vez para o loop manual

            if jogo_esta_perdido:
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if btn_reiniciar_nivel_rect and btn_reiniciar_nivel_rect.collidepoint(evento.pos):
                        if som_botao_clique: som_botao_clique.play()
                        labirinto_atual, jogador_pos, destino_pos, inimigo_pos = reiniciar_jogo(nivel_atual)
                        jogo_esta_perdido = False; movimento_jogador_pendente = None
                        btn_reiniciar_nivel_rect = None; btn_sair_jogo_rect = None
                        frames_inimigo_contador = 0
                    elif btn_sair_jogo_rect and btn_sair_jogo_rect.collidepoint(evento.pos):
                        if som_botao_clique: som_botao_clique.play()
                        rodando = False
            else: 
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_r:
                        if som_botao_clique: som_botao_clique.play() 
                        nivel_atual = 1
                        labirinto_atual, jogador_pos, destino_pos, inimigo_pos = reiniciar_jogo(nivel_atual)
                        jogo_esta_perdido = False; movimento_jogador_pendente = None
                        frames_inimigo_contador = 0
                    elif evento.key == pygame.K_ESCAPE: rodando = False
                    elif not jogo_esta_perdido and evento.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                        movimento_jogador_pendente = evento.key
        
        if not jogo_esta_perdido:
            if movimento_jogador_pendente:
                px, py = jogador_pos
                if movimento_jogador_pendente == pygame.K_LEFT: px -= 1
                elif movimento_jogador_pendente == pygame.K_RIGHT: px += 1
                elif movimento_jogador_pendente == pygame.K_UP: py -= 1
                elif movimento_jogador_pendente == pygame.K_DOWN: py += 1
                if 0 <= px < LARGURA_CELULAS and 0 <= py < ALTURA_CELULAS and labirinto_atual[py][px] == 0:
                    jogador_pos = (px, py)
                movimento_jogador_pendente = None

            frames_inimigo_contador += 1
            if frames_inimigo_contador >= velocidade_inimigo_frames:
                if inimigo_pos != jogador_pos:
                    caminho_inimigo_atual = a_star(labirinto_atual, inimigo_pos, jogador_pos)
                    if caminho_inimigo_atual: inimigo_pos = caminho_inimigo_atual[0]
                frames_inimigo_contador = 0

            if jogador_pos == destino_pos:
                if nivel_atual == MAX_NIVEIS: 
                    if som_ganhar_jogo: som_ganhar_jogo.play()
                    acao_vitoria = tela_vitoria() 
                    if acao_vitoria == "JOGAR_NOVAMENTE":
                        nivel_atual = 1 
                        labirinto_atual, jogador_pos, destino_pos, inimigo_pos = reiniciar_jogo(nivel_atual)
                        jogo_esta_perdido = False; movimento_jogador_pendente = None
                        frames_inimigo_contador = 0
                else: 
                    if som_passar_fase: som_passar_fase.play()
                    nivel_atual += 1
                    labirinto_atual, jogador_pos, destino_pos, inimigo_pos = reiniciar_jogo(nivel_atual)
                    frames_inimigo_contador = 0

            if jogador_pos == inimigo_pos:
                if som_morrer: som_morrer.play()
                jogo_esta_perdido = True; movimento_jogador_pendente = None
                
        retorno_botoes_tela_derrota = desenhar(labirinto_atual, jogador_pos, destino_pos, inimigo_pos, nivel_atual, game_over=jogo_esta_perdido)
        if jogo_esta_perdido and retorno_botoes_tela_derrota:
            btn_reiniciar_nivel_rect, btn_sair_jogo_rect = retorno_botoes_tela_derrota
        elif not jogo_esta_perdido:
            btn_reiniciar_nivel_rect = None; btn_sair_jogo_rect = None
            
        pygame.display.flip() 
        relogio.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main_game_loop()