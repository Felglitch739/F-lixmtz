import pygame
import random
import sys
import os
import math

# --- CONFIGURACIÓN ---
ANCHO, ALTO = 1000, 700
VERDE_MESA = (0, 81, 44)
ORO = (255, 215, 0)
BLANCO = (255, 255, 255)
ROJO_FICHA = (220, 20, 60)
ZONA_LUCKY = (200, 450)
ZONA_MAIN = (500, 450)
ZONA_BUSTER = (800, 450)
RADIO_APUESTA = 45

# --- CLASES MEJORADAS ---
class Carta:
    def __init__(self, imagen, valor, rango, palo):
        self.imagen = imagen
        self.valor = valor
        self.rango = rango # Ej: "6", "7", "As"
        self.palo = palo   # Ej: "Corazones"
        self.nombre = f"{rango} de {palo}"

class Jugador:
    def __init__(self):
        self.mano = []
        self.puntaje = 0
        
    def recibir_carta(self, carta):
        self.mano.append(carta)
        self.actualizar_puntaje()
        
    def actualizar_puntaje(self):
        total = sum(c.valor for c in self.mano)
        ases = sum(1 for c in self.mano if c.rango == "As")
        while total > 21 and ases > 0:
            total -= 10
            ases -= 1
        self.puntaje = total

# --- MOTORES DE REGLAS (SIDE BETS) ---
def evaluar_lucky(mano_jugador, carta_visible_crupier):
    """Devuelve el multiplicador de pago para el Lucky Lucky"""
    c1, c2 = mano_jugador[0], mano_jugador[1]
    c3 = carta_visible_crupier
    
    rangos = sorted([c1.rango, c2.rango, c3.rango])
    mismo_palo = (c1.palo == c2.palo == c3.palo)

    # Reglas específicas
    if rangos == ["6", "7", "8"]:
        return 100 if mismo_palo else 30
    if rangos == ["7", "7", "7"]:
        return 30 # Suited 7-7-7 no lo especificaste, pero suele pagar más, aquí lo dejamos en 30:1 general
        
    # Reglas de suma
    total = c1.valor + c2.valor + c3.valor
    ases = sum(1 for c in [c1, c2, c3] if c.rango == "As")
    while total > 21 and ases > 0:
        total -= 10
        ases -= 1

    if total == 21: return 3
    if total == 20: return 2
    if total == 19: return 1
    
    return 0 # Pierde

def evaluar_buster(crupier):
    """Devuelve el multiplicador si el crupier se pasa"""
    if crupier.puntaje > 21:
        cartas = len(crupier.mano)
        if cartas >= 8: return 250
        if cartas == 7: return 50
        if cartas == 6: return 15
        if cartas == 5: return 4
        if cartas in [3, 4]: return 2
    return 0 # Pierde o no se pasó

# --- SISTEMA PRINCIPAL ---
def cargar_recursos():
    ruta = os.path.join(os.path.dirname(__file__), "cardsLarge_tilemap_packed.png")
    hoja = pygame.image.load(ruta).convert_alpha()
    baraja = []
    valores = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
    rangos = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    palos = ["Corazones", "Diamantes", "Treboles", "Picas"]

    for f in range(4):
        for c in range(13):
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            surf.blit(hoja, (0, 0), (c*64, f*64, 64, 64))
            img = pygame.transform.scale(surf, (120, 120))
            # Ahora guardamos el rango y palo independientes
            baraja.append(Carta(img, valores[c], rangos[c], palos[f]))
    
    surf_rev = pygame.Surface((64, 64), pygame.SRCALPHA)
    surf_rev.blit(hoja, (0, 0), (13*64, 0*64, 64, 64))
    reverso = pygame.transform.scale(surf_rev, (120, 120))
    return baraja, reverso

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Blackjack Simulator Pro")
    fuente = pygame.font.SysFont("Consolas", 20, bold=True)
    fuente_grande = pygame.font.SysFont("Consolas", 35, bold=True)
    
    baraja_master, img_reverso = cargar_recursos()
    
    saldo = 1000
    apuesta_main = apuesta_lucky = apuesta_buster = 0
    jugador, crupier = Jugador(), Jugador()
    baraja_juego = []
    
    fase_apuestas = True
    terminado = False
    turno_crupier = False
    mensaje = "Haz clic en los círculos para apostar. ENTER para repartir."
    mensaje_sidebets = ""

    def resolver_apuestas(bust_jugador=False):
        nonlocal saldo, mensaje_sidebets
        textos_extra = []
        
        # 1. Evaluar Lucky Lucky (Solo importa las 2 del jugador y 1 del dealer)
        if apuesta_lucky > 0:
            multiplicador = evaluar_lucky(jugador.mano, crupier.mano[0])
            if multiplicador > 0:
                ganancia = apuesta_lucky + (apuesta_lucky * multiplicador)
                saldo += ganancia
                textos_extra.append(f"LUCKY PAGA: ${ganancia} ({multiplicador}:1)")
            else:
                textos_extra.append("Lucky: Perdió")

        # 2. Evaluar Buster (El dealer tiene que jugar para evaluarlo)
        # Si el jugador hizo Bust, en el casino real el dealer NO saca más cartas, así que el Buster pierde.
        if apuesta_buster > 0:
            if bust_jugador:
                textos_extra.append("Buster: Perdió (Tú te pasaste)")
            else:
                multiplicador = evaluar_buster(crupier)
                if multiplicador > 0:
                    ganancia = apuesta_buster + (apuesta_buster * multiplicador)
                    saldo += ganancia
                    textos_extra.append(f"BUSTER PAGA: ${ganancia} ({multiplicador}:1)")
                else:
                    textos_extra.append("Buster: Perdió")
                    
        mensaje_sidebets = " | ".join(textos_extra)

    def iniciar_ronda():
        nonlocal jugador, crupier, baraja_juego, terminado, turno_crupier, mensaje, fase_apuestas, mensaje_sidebets
        baraja_juego = baraja_master.copy()
        random.shuffle(baraja_juego)
        jugador, crupier = Jugador(), Jugador()
        mensaje_sidebets = ""
        
        for _ in range(2):
            jugador.recibir_carta(baraja_juego.pop())
            crupier.recibir_carta(baraja_juego.pop())
            
        terminado, turno_crupier, fase_apuestas = False, False, False
        mensaje = "ESPACIO: Pedir carta | P: Plantarse"

    reloj = pygame.time.Clock()

    while True:
        pos_mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                
            if ev.type == pygame.MOUSEBUTTONDOWN and fase_apuestas:
                if math.hypot(pos_mouse[0]-ZONA_MAIN[0], pos_mouse[1]-ZONA_MAIN[1]) < RADIO_APUESTA and saldo >= 10:
                    saldo -= 10; apuesta_main += 10
                elif math.hypot(pos_mouse[0]-ZONA_LUCKY[0], pos_mouse[1]-ZONA_LUCKY[1]) < RADIO_APUESTA and saldo >= 10:
                    saldo -= 10; apuesta_lucky += 10
                elif math.hypot(pos_mouse[0]-ZONA_BUSTER[0], pos_mouse[1]-ZONA_BUSTER[1]) < RADIO_APUESTA and saldo >= 10:
                    saldo -= 10; apuesta_buster += 10

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and fase_apuestas and apuesta_main > 0:
                    iniciar_ronda()
                    
                elif ev.key == pygame.K_r and terminado:
                    fase_apuestas = True
                    apuesta_main = apuesta_lucky = apuesta_buster = 0
                    jugador.mano.clear(); crupier.mano.clear()
                    mensaje = "Alinea tus apuestas. ENTER para repartir."
                    mensaje_sidebets = ""
                
                elif not terminado and not fase_apuestas:
                    if ev.key == pygame.K_SPACE:
                        jugador.recibir_carta(baraja_juego.pop())
                        if jugador.puntaje > 21:
                            terminado = True
                            mensaje = "¡BUST! Perdiste la principal. Presiona R"
                            resolver_apuestas(bust_jugador=True) # El dealer no juega
                    
                    elif ev.key == pygame.K_p:
                        turno_crupier = True
                        while crupier.puntaje < 17:
                            crupier.recibir_carta(baraja_juego.pop())
                        terminado = True
                        
                        # Resolución Principal
                        if crupier.puntaje > 21 or jugador.puntaje > crupier.puntaje:
                            mensaje = f"¡GANASTE LA MAIN! (+${apuesta_main * 2}) | Presiona R"
                            saldo += (apuesta_main * 2)
                        elif jugador.puntaje < crupier.puntaje:
                            mensaje = "GANA LA CASA LA MAIN. Presiona R"
                        else:
                            mensaje = "EMPATE MAIN. Se devuelve tu apuesta. Presiona R"
                            saldo += apuesta_main
                            
                        # Resolución Side Bets
                        resolver_apuestas(bust_jugador=False)

        # --- DIBUJO ---
        pantalla.fill(VERDE_MESA)
        
        pygame.draw.circle(pantalla, ORO, ZONA_LUCKY, RADIO_APUESTA, 3)
        pygame.draw.circle(pantalla, ORO, ZONA_MAIN, RADIO_APUESTA, 3)
        pygame.draw.circle(pantalla, ORO, ZONA_BUSTER, RADIO_APUESTA, 3)
        
        pantalla.blit(fuente.render("LUCKY", True, BLANCO), (ZONA_LUCKY[0]-30, ZONA_LUCKY[1]-55))
        pantalla.blit(fuente.render("MAIN", True, BLANCO), (ZONA_MAIN[0]-25, ZONA_MAIN[1]-55))
        pantalla.blit(fuente.render("BUSTER", True, BLANCO), (ZONA_BUSTER[0]-35, ZONA_BUSTER[1]-55))

        if apuesta_lucky > 0: 
            pygame.draw.circle(pantalla, ROJO_FICHA, ZONA_LUCKY, 25)
            pantalla.blit(fuente.render(f"${apuesta_lucky}", True, BLANCO), (ZONA_LUCKY[0]-15, ZONA_LUCKY[1]-10))
        if apuesta_main > 0:
            pygame.draw.circle(pantalla, ROJO_FICHA, ZONA_MAIN, 25)
            pantalla.blit(fuente.render(f"${apuesta_main}", True, BLANCO), (ZONA_MAIN[0]-15, ZONA_MAIN[1]-10))
        if apuesta_buster > 0:
            pygame.draw.circle(pantalla, ROJO_FICHA, ZONA_BUSTER, 25)
            pantalla.blit(fuente.render(f"${apuesta_buster}", True, BLANCO), (ZONA_BUSTER[0]-15, ZONA_BUSTER[1]-10))

        if not fase_apuestas or terminado:
            for i, c in enumerate(crupier.mano):
                img = img_reverso if (i == 0 and not turno_crupier and not terminado) else c.imagen
                pantalla.blit(img, (350 + (i*50), 50))
            for i, c in enumerate(jugador.mano):
                pantalla.blit(c.imagen, (400 + (i*50), 520))

            pantalla.blit(fuente.render(f"Tu Puntaje: {jugador.puntaje}", True, BLANCO), (400, 650))
            if turno_crupier or terminado:
                pantalla.blit(fuente.render(f"Puntaje Casa: {crupier.puntaje}", True, BLANCO), (400, 20))

        pantalla.blit(fuente_grande.render(f"Saldo: ${saldo}", True, ORO), (20, 20))
        
        # Textos de resolución
        pantalla.blit(fuente.render(mensaje, True, ORO), (ANCHO//2 - fuente.render(mensaje, True, ORO).get_width()//2, 330))
        if mensaje_sidebets != "":
            txt_side = fuente.render(mensaje_sidebets, True, (152, 251, 152)) # Verde claro para ganancias
            pantalla.blit(txt_side, (ANCHO//2 - txt_side.get_width()//2, 370))

        pygame.display.flip()
        reloj.tick(60)

if __name__ == "__main__":
    main()