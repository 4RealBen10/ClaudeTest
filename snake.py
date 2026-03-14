import pygame
import random
import sys

# Konstanten
BREITE = 600
HOEHE = 600
ZELLEN_GROESSE = 20
ZELLEN_X = BREITE // ZELLEN_GROESSE
ZELLEN_Y = HOEHE // ZELLEN_GROESSE
FPS = 10

# Farben
SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)
GRUEN = (0, 200, 0)
DUNKELGRUEN = (0, 150, 0)
ROT = (200, 0, 0)
BANANENGELB = (255, 225, 50)
BANANENDUNKEL = (180, 140, 0)
GRAU = (40, 40, 40)
GELB = (255, 220, 0)

# Richtungen
OBEN = (0, -1)
UNTEN = (0, 1)
LINKS = (-1, 0)
RECHTS = (1, 0)


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        start_x = ZELLEN_X // 2
        start_y = ZELLEN_Y // 2
        self.koerper = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.richtung = RECHTS
        self.naechste_richtung = RECHTS
        self.gewachsen = False

    def richtung_setzen(self, neue_richtung):
        # Verhindere 180-Grad-Wendung
        entgegengesetzt = (-self.richtung[0], -self.richtung[1])
        if neue_richtung != entgegengesetzt:
            self.naechste_richtung = neue_richtung

    def bewegen(self):
        self.richtung = self.naechste_richtung
        kopf_x, kopf_y = self.koerper[0]
        neuer_kopf = (kopf_x + self.richtung[0], kopf_y + self.richtung[1])
        self.koerper.insert(0, neuer_kopf)
        if not self.gewachsen:
            self.koerper.pop()
        self.gewachsen = False

    def wachsen(self):
        self.gewachsen = True

    def kollision_wand(self):
        kopf_x, kopf_y = self.koerper[0]
        return not (0 <= kopf_x < ZELLEN_X and 0 <= kopf_y < ZELLEN_Y)

    def kollision_selbst(self):
        return self.koerper[0] in self.koerper[1:]

    def zeichnen(self, flaeche):
        for i, (x, y) in enumerate(self.koerper):
            rect = pygame.Rect(x * ZELLEN_GROESSE, y * ZELLEN_GROESSE, ZELLEN_GROESSE, ZELLEN_GROESSE)
            farbe = GRUEN if i == 0 else DUNKELGRUEN
            pygame.draw.rect(flaeche, farbe, rect)
            pygame.draw.rect(flaeche, SCHWARZ, rect, 1)

        # Augen auf dem Kopf
        kopf_x, kopf_y = self.koerper[0]
        auge_offset = {
            RECHTS: [(14, 5), (14, 13)],
            LINKS:  [(4, 5), (4, 13)],
            OBEN:   [(5, 4), (13, 4)],
            UNTEN:  [(5, 14), (13, 14)],
        }
        for ox, oy in auge_offset.get(self.richtung, []):
            pygame.draw.circle(
                flaeche, WEISS,
                (kopf_x * ZELLEN_GROESSE + ox, kopf_y * ZELLEN_GROESSE + oy), 2
            )


class Spiel:
    def __init__(self):
        pygame.init()
        self.flaeche = pygame.display.set_mode((BREITE, HOEHE))
        pygame.display.set_caption("Snake")
        self.uhr = pygame.time.Clock()
        self.schrift_gross = pygame.font.SysFont("monospace", 48, bold=True)
        self.schrift_mittel = pygame.font.SysFont("monospace", 28)
        self.schrift_klein = pygame.font.SysFont("monospace", 20)
        self.snake = Snake()
        self.neues_spiel()

    def neues_spiel(self):
        self.snake.reset()
        self.punkte = 0
        self.laeuft = True
        self.game_over = False
        self.apfel_platzieren()

    def apfel_platzieren(self):
        while True:
            pos = (random.randint(0, ZELLEN_X - 1), random.randint(0, ZELLEN_Y - 1))
            if pos not in self.snake.koerper:
                self.apfel = pos
                break

    def gitter_zeichnen(self):
        for x in range(0, BREITE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (x, 0), (x, HOEHE))
        for y in range(0, HOEHE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (0, y), (BREITE, y))

    def banane_zeichnen(self):
        ax, ay = self.apfel
        cx = ax * ZELLEN_GROESSE + ZELLEN_GROESSE // 2
        cy = ay * ZELLEN_GROESSE + ZELLEN_GROESSE // 2
        # Banane: gebogener Körper als dicke Linie aus Kreisen
        import math
        punkte = []
        for i in range(11):
            t = i / 10  # 0..1
            winkel = math.pi * 0.15 + t * math.pi * 0.7
            r = 7
            px = int(cx + r * math.cos(winkel) * 1.1)
            py = int(cy - r * math.sin(winkel))
            punkte.append((px, py))
        # Schatten / Kontur
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENDUNKEL, punkte[i], punkte[i + 1], 5)
        # Hauptfarbe
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENGELB, punkte[i], punkte[i + 1], 3)
        # Enden der Banane (dunkle Spitzen)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[0], 2)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[-1], 2)

    def hud_zeichnen(self):
        punkte_text = self.schrift_klein.render(f"Punkte: {self.punkte}", True, WEISS)
        self.flaeche.blit(punkte_text, (8, 8))

    def game_over_bildschirm(self):
        overlay = pygame.Surface((BREITE, HOEHE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.flaeche.blit(overlay, (0, 0))

        titel = self.schrift_gross.render("GAME OVER", True, ROT)
        self.flaeche.blit(titel, titel.get_rect(center=(BREITE // 2, HOEHE // 2 - 60)))

        punkte_text = self.schrift_mittel.render(f"Punkte: {self.punkte}", True, GELB)
        self.flaeche.blit(punkte_text, punkte_text.get_rect(center=(BREITE // 2, HOEHE // 2)))

        neu_text = self.schrift_klein.render("ENTER = Neues Spiel   ESC = Beenden", True, WEISS)
        self.flaeche.blit(neu_text, neu_text.get_rect(center=(BREITE // 2, HOEHE // 2 + 60)))

    def startbildschirm(self):
        self.flaeche.fill(SCHWARZ)
        titel = self.schrift_gross.render("SNAKE", True, GRUEN)
        self.flaeche.blit(titel, titel.get_rect(center=(BREITE // 2, HOEHE // 2 - 80)))

        steuerung = [
            "Steuerung:",
            "Pfeiltasten oder WASD",
            "",
            "ENTER = Starten",
            "ESC   = Beenden",
        ]
        for i, zeile in enumerate(steuerung):
            farbe = GELB if zeile.startswith("ENTER") or zeile.startswith("ESC") else WEISS
            text = self.schrift_klein.render(zeile, True, farbe)
            self.flaeche.blit(text, text.get_rect(center=(BREITE // 2, HOEHE // 2 + i * 28)))

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def ereignisse_verarbeiten(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_RETURN:
                        self.neues_spiel()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                else:
                    tasten_richtung = {
                        pygame.K_UP: OBEN, pygame.K_w: OBEN,
                        pygame.K_DOWN: UNTEN, pygame.K_s: UNTEN,
                        pygame.K_LEFT: LINKS, pygame.K_a: LINKS,
                        pygame.K_RIGHT: RECHTS, pygame.K_d: RECHTS,
                    }
                    if event.key in tasten_richtung:
                        self.snake.richtung_setzen(tasten_richtung[event.key])
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def aktualisieren(self):
        if self.game_over:
            return
        self.snake.bewegen()
        if self.snake.kollision_wand() or self.snake.kollision_selbst():
            self.game_over = True
            return
        if self.snake.koerper[0] == self.apfel:
            self.snake.wachsen()
            self.punkte += 10
            self.apfel_platzieren()

    def zeichnen(self):
        self.flaeche.fill(SCHWARZ)
        self.gitter_zeichnen()
        self.banane_zeichnen()
        self.snake.zeichnen(self.flaeche)
        self.hud_zeichnen()
        if self.game_over:
            self.game_over_bildschirm()
        pygame.display.flip()

    def starten(self):
        self.startbildschirm()
        while True:
            self.ereignisse_verarbeiten()
            self.aktualisieren()
            self.zeichnen()
            self.uhr.tick(FPS)


if __name__ == "__main__":
    spiel = Spiel()
    spiel.starten()
