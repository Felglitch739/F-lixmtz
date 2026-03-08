import pygame
import random
import sys
import os

# --- INICIALIZACIÓN ---
pygame.init()
ANCHO, ALTO = 1000, 700
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Blackjack UTRGV - Debug Version")
fuente = pygame.font.SysFont("Arial", 25)

# --- CLASES ---
class Carta:
    def __init__(self, imagen, valor, nombre):
        self.imagen = imagen
        self.valor = valor
        self.nombre = nombre

class Jugador:
    def __init__(self):
        self.mano = []
        self.puntaje = 0
    
    def recibir_carta(self, carta):
        self.mano.append(carta)
        self.actualizar_puntaje()
        
    def actualizar_puntaje(self):
        total = sum(c.valor for c in self.mano)
        ases = sum(1 for c in self.mano if "As" in c.nombre)
        while total > 21 and ases > 0:
            total -= 10
            ases -= 1
        self.puntaje = total

# --- CARGA DE ASSETS ---
def cargar_todo():
    ruta = os.path.join(os.path.dirname(__file__), "cardsLarge_tilemap_packed.png")
    hoja = pygame.image.load(ruta).convert_alpha()
    
    baraja = []
    palos = ["corazones", "diamantes", "treboles", "picas"]
    nombres = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    valores = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]

    for f in range(4):
        for c in range(13):
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            surf.blit(hoja, (0, 0), (c*64, f*64, 64, 64))
            img = pygame.transform.scale(surf, (128, 128))
            baraja.append(Carta(img, valores[c], f"{nombres[c]} de {palos[f]}"))
    
    # Reverso (ajustado a la posición común en ese tilemap)
    surf_rev = pygame.Surface((64, 64), pygame.SRCALPHA)
    surf_rev.blit(hoja, (0, 0), (13*64, 0*64, 64, 64))
    reverso = pygame.transform.scale(surf_rev, (128, 128))
    
    return baraja, reverso

# --- FLUJO PRINCIPAL ---
def jugar():
    baraja_master, img_reverso = cargar_todo()
    random.shuffle(baraja_master)
    
    usuario = Jugador()
    casa = Jugador()
    
    # Reparto inicial obligatorio
    for _ in range(2):
        usuario.recibir_carta(baraja_master.pop())
        casa.recibir_carta(baraja_master.pop())

    turno_casa = False
    terminado = False
    msg = "ESPACIO: Pedir | P: Plantarse"
    reloj = pygame.time.Clock()

    while True:
        # 1. EVENTOS (Aquí es donde escuchamos el teclado)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if not terminado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        print("DEBUG: Usuario pidió carta")
                        usuario.recibir_carta(baraja_master.pop())
                        if usuario.puntaje > 21:
                            terminado = True
                            msg = "¡BUST! Te pasaste de 21."
                    
                    elif evento.key == pygame.K_p:
                        print("DEBUG: Usuario se plantó")
                        turno_casa = True
                        while casa.puntaje < 17:
                            casa.recibir_carta(baraja_master.pop())
                        
                        terminado = True
                        # Lógica final
                        if casa.puntaje > 21 or usuario.puntaje > casa.puntaje:
                            msg = "¡GANASTE!"
                        elif usuario.puntaje < casa.puntaje:
                            msg = "PERDISTE CONTRA LA CASA."
                        else:
                            msg = "EMPATE (PUSH)."

        # 2. DIBUJO
        pantalla.fill((0, 81, 44)) # Verde oscuro
        
        # Dibujar Casa
        for i, c in enumerate(casa.mano):
            x = 100 + (i * 140)
            if i == 0 and not turno_casa:
                pantalla.blit(img_reverso, (x, 50))
            else:
                pantalla.blit(c.image, (x, 50)) if hasattr(c, 'image') else pantalla.blit(c.imagen, (x, 50))
        
        # Dibujar Usuario
        for i, c in enumerate(usuario.mano):
            pantalla.blit(c.imagen, (100 + (i * 140), 400))
            
        # UI
        txt_u = fuente.render(f"Tu Total: {usuario.puntaje}", True, (255, 255, 255))
        pantalla.blit(txt_u, (750, 450))
        
        if turno_casa:
            txt_c = fuente.render(f"Casa: {casa.puntaje}", True, (255, 255, 255))
            pantalla.blit(txt_c, (750, 100))
            
        txt_m = fuente.render(msg, True, (255, 215, 0))
        pantalla.blit(txt_m, (ANCHO//2 - txt_m.get_width()//2, 320))

        pygame.display.flip()
        reloj.tick(60)

if __name__ == "__main__":
    jugar()