import pygame
import random
import sys
import math
import json
import os
import colorsys

# Konstanten
BREITE = 600
HOEHE = 600
ZELLEN_GROESSE = 20
ZELLEN_X = BREITE // ZELLEN_GROESSE
ZELLEN_Y = HOEHE // ZELLEN_GROESSE
FPS = 10
HIGHSCORE_DATEI = os.path.join(os.path.dirname(__file__), "highscores.json")

# Farben
SCHWARZ    = (0, 0, 0)
WEISS      = (255, 255, 255)
GRUEN      = (0, 200, 0)
DUNKELGRUEN= (0, 150, 0)
ROT        = (200, 0, 0)
GRAU       = (40, 40, 40)
GELB       = (255, 220, 0)
BANANENGELB  = (255, 225, 50)
BANANENDUNKEL= (180, 140, 0)

# Früchte-Reihenfolge
FRUECHTE = ["apfel", "banane", "ananas", "kirsche"]

# Richtungen
OBEN   = (0, -1)
UNTEN  = (0,  1)
LINKS  = (-1, 0)
RECHTS = ( 1, 0)


def regenbogen_farbe(index, gesamt):
    """Gibt eine Regenbogenfarbe für ein Segment zurück."""
    hue = (index / max(gesamt, 1)) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 0.9)
    return (int(r * 255), int(g * 255), int(b * 255))


def lade_highscores():
    if os.path.exists(HIGHSCORE_DATEI):
        try:
            with open(HIGHSCORE_DATEI, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def speichere_highscores(scores):
    with open(HIGHSCORE_DATEI, "w") as f:
        json.dump(scores, f)


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
        gesamt = len(self.koerper)
        for i, (x, y) in enumerate(self.koerper):
            rect = pygame.Rect(x * ZELLEN_GROESSE, y * ZELLEN_GROESSE,
                               ZELLEN_GROESSE, ZELLEN_GROESSE)
            farbe = regenbogen_farbe(i, gesamt)
            pygame.draw.rect(flaeche, farbe, rect)
            pygame.draw.rect(flaeche, SCHWARZ, rect, 1)

        # Augen auf dem Kopf
        kopf_x, kopf_y = self.koerper[0]
        auge_offset = {
            RECHTS: [(14, 5), (14, 13)],
            LINKS:  [(4,  5), (4,  13)],
            OBEN:   [(5,  4), (13,  4)],
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
        self.schrift_gross  = pygame.font.SysFont("monospace", 48, bold=True)
        self.schrift_mittel = pygame.font.SysFont("monospace", 28)
        self.schrift_klein  = pygame.font.SysFont("monospace", 20)
        self.schrift_winzig = pygame.font.SysFont("monospace", 16)
        self.snake = Snake()
        self.highscores = lade_highscores()
        self.neues_spiel()

    def neues_spiel(self):
        self.snake.reset()
        self.punkte = 0
        self.frucht_index = 0
        self.game_over = False
        self.frucht_platzieren()

    def frucht_platzieren(self):
        while True:
            pos = (random.randint(0, ZELLEN_X - 1), random.randint(0, ZELLEN_Y - 1))
            if pos not in self.snake.koerper:
                self.frucht_pos = pos
                break

    def aktuelle_frucht(self):
        return FRUECHTE[self.frucht_index % len(FRUECHTE)]

    # ── Frucht-Zeichenfunktionen ────────────────────────────────────────────

    def _apfel_zeichnen(self, cx, cy):
        rect = pygame.Rect(cx - 7, cy - 6, 14, 13)
        pygame.draw.ellipse(self.flaeche, (200, 0, 0), rect)
        pygame.draw.ellipse(self.flaeche, (255, 80, 80),
                            pygame.Rect(cx - 4, cy - 5, 5, 5))
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx, cy - 7), (cx + 3, cy - 11), 2)

    def _banane_zeichnen(self, cx, cy):
        punkte = []
        for i in range(11):
            t = i / 10
            winkel = math.pi * 0.15 + t * math.pi * 0.7
            r = 7
            px = int(cx + r * math.cos(winkel) * 1.1)
            py = int(cy - r * math.sin(winkel))
            punkte.append((px, py))
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENDUNKEL, punkte[i], punkte[i+1], 5)
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENGELB,   punkte[i], punkte[i+1], 3)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[0],  2)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[-1], 2)

    def _ananas_zeichnen(self, cx, cy):
        # Körper (gelb)
        body = pygame.Rect(cx - 5, cy - 4, 10, 12)
        pygame.draw.ellipse(self.flaeche, (255, 200, 0), body)
        # Rautenmuster
        for row in range(3):
            for col in range(2):
                ox = -3 + col * 5 + (row % 2) * 2
                oy = -2 + row * 4
                pygame.draw.rect(self.flaeche, (200, 140, 0),
                                 pygame.Rect(cx + ox, cy + oy, 3, 3), 1)
        # Blätter (grün)
        blaetter = [(-3, -7), (0, -9), (3, -7)]
        for bx, by in blaetter:
            pygame.draw.line(self.flaeche, (0, 160, 0),
                             (cx, cy - 4), (cx + bx, cy + by), 2)

    def _kirsche_zeichnen(self, cx, cy):
        # Zwei Kirschen nebeneinander
        for dx in (-4, 4):
            pygame.draw.circle(self.flaeche, (180, 0, 30), (cx + dx, cy + 4), 4)
            pygame.draw.circle(self.flaeche, (255, 80, 80), (cx + dx - 1, cy + 2), 1)
        # Stiel
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx - 4, cy),  (cx, cy - 6), 1)
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx + 4, cy),  (cx, cy - 6), 1)
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx,     cy - 6), (cx, cy - 9), 1)

    def frucht_zeichnen(self):
        ax, ay = self.frucht_pos
        cx = ax * ZELLEN_GROESSE + ZELLEN_GROESSE // 2
        cy = ay * ZELLEN_GROESSE + ZELLEN_GROESSE // 2
        {
            "apfel":   self._apfel_zeichnen,
            "banane":  self._banane_zeichnen,
            "ananas":  self._ananas_zeichnen,
            "kirsche": self._kirsche_zeichnen,
        }[self.aktuelle_frucht()](cx, cy)

    # ── HUD & Bildschirme ───────────────────────────────────────────────────

    def gitter_zeichnen(self):
        for x in range(0, BREITE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (x, 0), (x, HOEHE))
        for y in range(0, HOEHE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (0, y), (BREITE, y))

    def hud_zeichnen(self):
        frucht_namen = {"apfel": "Apfel", "banane": "Banane",
                        "ananas": "Ananas", "kirsche": "Kirsche"}
        text = self.schrift_klein.render(
            f"Punkte: {self.punkte}   Naechste: {frucht_namen[self.aktuelle_frucht()]}",
            True, WEISS)
        self.flaeche.blit(text, (8, 8))

    def highscore_qualifiziert(self):
        if len(self.highscores) < 10:
            return True
        return self.punkte > self.highscores[-1]["punkte"]

    def namen_eingabe(self):
        """Zeigt Namenseingabe (3 Buchstaben) und gibt den Namen zurück."""
        buchstaben = [65, 65, 65]  # AAA
        cursor = 0
        schrift_titel  = self.schrift_mittel
        schrift_letter = pygame.font.SysFont("monospace", 56, bold=True)

        while True:
            self.flaeche.fill(SCHWARZ)
            # Titel
            t = schrift_titel.render("NEUER HIGHSCORE!", True, GELB)
            self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, 160)))
            p = self.schrift_klein.render(f"Punkte: {self.punkte}", True, WEISS)
            self.flaeche.blit(p, p.get_rect(center=(BREITE // 2, 210)))

            hint = self.schrift_winzig.render(
                "Pfeiltasten: Buchstaben  Links/Rechts: Cursor  ENTER: Bestaetigen",
                True, GRAU)
            self.flaeche.blit(hint, hint.get_rect(center=(BREITE // 2, 260)))

            # Buchstaben-Slots
            gesamt_breite = 3 * 60 + 2 * 20
            start_x = BREITE // 2 - gesamt_breite // 2
            for i, code in enumerate(buchstaben):
                x = start_x + i * 80
                y = 310
                farbe_box = GELB if i == cursor else GRAU
                pygame.draw.rect(self.flaeche, farbe_box,
                                 pygame.Rect(x, y, 60, 70), 3)
                letter = schrift_letter.render(chr(code), True, WEISS)
                self.flaeche.blit(letter, letter.get_rect(center=(x + 30, y + 35)))

            # Pfeile
            pfeil = self.schrift_mittel.render("v", True, GELB)
            ax = start_x + cursor * 80 + 30
            self.flaeche.blit(pfeil, pfeil.get_rect(center=(ax, 395)))

            pygame.display.flip()
            self.uhr.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        cursor = (cursor - 1) % 3
                    elif event.key == pygame.K_RIGHT:
                        cursor = (cursor + 1) % 3
                    elif event.key == pygame.K_UP:
                        buchstaben[cursor] = (buchstaben[cursor] - 65 - 1) % 26 + 65
                    elif event.key == pygame.K_DOWN:
                        buchstaben[cursor] = (buchstaben[cursor] - 65 + 1) % 26 + 65
                    elif event.key == pygame.K_RETURN:
                        return "".join(chr(c) for c in buchstaben)
                    elif event.key == pygame.K_ESCAPE:
                        return "???"
                    elif pygame.K_a <= event.key <= pygame.K_z:
                        buchstaben[cursor] = event.key - pygame.K_a + 65
                        cursor = min(cursor + 1, 2)

    def highscore_eintragen(self):
        name = self.namen_eingabe()
        self.highscores.append({"name": name, "punkte": self.punkte})
        self.highscores.sort(key=lambda e: e["punkte"], reverse=True)
        self.highscores = self.highscores[:10]
        speichere_highscores(self.highscores)

    def highscore_anzeigen(self):
        while True:
            self.flaeche.fill(SCHWARZ)
            t = self.schrift_gross.render("HIGHSCORES", True, GELB)
            self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, 50)))

            for rang, eintrag in enumerate(self.highscores):
                farbe = GELB if eintrag["punkte"] == self.punkte else WEISS
                zeile = f"{rang+1:2}. {eintrag['name']}   {eintrag['punkte']:>6}"
                txt = self.schrift_klein.render(zeile, True, farbe)
                self.flaeche.blit(txt, txt.get_rect(center=(BREITE // 2, 110 + rang * 34)))

            hint = self.schrift_winzig.render(
                "ENTER = Neues Spiel    ESC = Beenden", True, GRAU)
            self.flaeche.blit(hint, hint.get_rect(center=(BREITE // 2, 480)))
            pygame.display.flip()
            self.uhr.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return True   # neues Spiel
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

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
                tasten_richtung = {
                    pygame.K_UP: OBEN,    pygame.K_w: OBEN,
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
        self.snake.bewegen()
        if self.snake.kollision_wand() or self.snake.kollision_selbst():
            self.game_over = True
            return
        if self.snake.koerper[0] == self.frucht_pos:
            self.snake.wachsen()
            self.punkte += 10
            self.frucht_index += 1
            self.frucht_platzieren()

    def zeichnen(self):
        self.flaeche.fill(SCHWARZ)
        self.gitter_zeichnen()
        self.frucht_zeichnen()
        self.snake.zeichnen(self.flaeche)
        self.hud_zeichnen()
        pygame.display.flip()

    def starten(self):
        self.startbildschirm()
        while True:
            self.neues_spiel()
            # Spielschleife
            while not self.game_over:
                self.ereignisse_verarbeiten()
                self.aktualisieren()
                self.zeichnen()
                self.uhr.tick(FPS)
            # Nach Game Over
            if self.highscore_qualifiziert():
                self.highscore_eintragen()
            self.highscore_anzeigen()


if __name__ == "__main__":
    spiel = Spiel()
    spiel.starten()
