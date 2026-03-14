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
SCHWARZ      = (0, 0, 0)
WEISS        = (255, 255, 255)
GRUEN        = (0, 200, 0)
DUNKELGRUEN  = (0, 150, 0)
ROT          = (200, 0, 0)
GRAU         = (40, 40, 40)
GELB         = (255, 220, 0)
BANANENGELB  = (255, 225, 50)
BANANENDUNKEL= (180, 140, 0)
PINK         = (255, 80, 180)
TURKIES      = (0, 210, 200)

# Früchte-Reihenfolge
FRUECHTE = ["apfel", "banane", "ananas", "kirsche"]

# Richtungen
OBEN   = (0, -1)
UNTEN  = (0,  1)
LINKS  = (-1, 0)
RECHTS = ( 1, 0)


def regenbogen_farbe(index, gesamt):
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
    def __init__(self, regenbogen=True, farbe=GRUEN, startpos=None, startrichtung=RECHTS):
        self.regenbogen = regenbogen
        self.farbe = farbe
        self._startpos = startpos
        self._startrichtung = startrichtung
        self.reset()

    def reset(self):
        sx, sy = self._startpos if self._startpos else (ZELLEN_X // 2, ZELLEN_Y // 2)
        dx, dy = self._startrichtung
        self.koerper = [(sx, sy), (sx - dx, sy - dy), (sx - 2 * dx, sy - 2 * dy)]
        self.richtung = self._startrichtung
        self.naechste_richtung = self._startrichtung
        self.gewachsen = False
        self.lebt = True

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

    def kopf_trifft(self, andere):
        """True wenn mein Kopf irgendein Segment der anderen Schlange berührt."""
        return self.koerper[0] in andere.koerper

    def zeichnen(self, flaeche):
        gesamt = len(self.koerper)
        for i, (x, y) in enumerate(self.koerper):
            rect = pygame.Rect(x * ZELLEN_GROESSE, y * ZELLEN_GROESSE,
                               ZELLEN_GROESSE, ZELLEN_GROESSE)
            if self.regenbogen:
                farbe = regenbogen_farbe(i, gesamt)
            else:
                farbe = self.farbe if i == 0 else tuple(max(0, c - 55) for c in self.farbe)
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
                flaeche, SCHWARZ,
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
        self.highscores = lade_highscores()
        self.spieler_anzahl = 1

    # ── Spieler-Auswahl ────────────────────────────────────────────────────

    def spieler_waehlen(self):
        auswahl = 1
        while True:
            self.flaeche.fill(SCHWARZ)

            titel = self.schrift_gross.render("SNAKE", True, GRUEN)
            self.flaeche.blit(titel, titel.get_rect(center=(BREITE // 2, 90)))

            frage = self.schrift_mittel.render("Wie viele Spieler?", True, WEISS)
            self.flaeche.blit(frage, frage.get_rect(center=(BREITE // 2, 185)))

            optionen = ["1 Spieler", "2 Spieler"]
            for i, label in enumerate(optionen):
                y = 255 + i * 70
                if i + 1 == auswahl:
                    pygame.draw.rect(self.flaeche, GELB,
                                     pygame.Rect(BREITE // 2 - 130, y - 8, 260, 54), 3)
                    farbe = GELB
                else:
                    farbe = GRAU
                txt = self.schrift_mittel.render(label, True, farbe)
                self.flaeche.blit(txt, txt.get_rect(center=(BREITE // 2, y + 19)))

            if auswahl == 2:
                infos = [
                    ("Spieler 1  (Pink):     Pfeiltasten", PINK),
                    ("Spieler 2  (Turkies):  W A S D",     TURKIES),
                ]
                for j, (zeile, farbe) in enumerate(infos):
                    t = self.schrift_winzig.render(zeile, True, farbe)
                    self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, 420 + j * 24)))

            hint = self.schrift_winzig.render(
                "Pfeiltasten: Auswahl   ENTER: Bestaetigen   ESC: Beenden",
                True, GRAU)
            self.flaeche.blit(hint, hint.get_rect(center=(BREITE // 2, 545)))

            pygame.display.flip()
            self.uhr.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        auswahl = 3 - auswahl  # Toggle 1 ↔ 2
                    elif event.key == pygame.K_RETURN:
                        self.spieler_anzahl = auswahl
                        return
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

    # ── Spielaufbau ────────────────────────────────────────────────────────

    def neues_spiel(self):
        mitte_y = ZELLEN_Y // 2
        if self.spieler_anzahl == 1:
            self.schlangen = [
                Snake(regenbogen=True,
                      startpos=(ZELLEN_X // 2, mitte_y),
                      startrichtung=RECHTS)
            ]
        else:
            self.schlangen = [
                Snake(regenbogen=False, farbe=PINK,
                      startpos=(ZELLEN_X // 4, mitte_y),
                      startrichtung=RECHTS),
                Snake(regenbogen=False, farbe=TURKIES,
                      startpos=(3 * ZELLEN_X // 4, mitte_y),
                      startrichtung=LINKS),
            ]
        self.punkte = [0] * self.spieler_anzahl
        self.frucht_index = 0
        self.game_over = False
        self.frucht_platzieren()

    def frucht_platzieren(self):
        alle_positionen = {seg for s in self.schlangen for seg in s.koerper}
        while True:
            pos = (random.randint(0, ZELLEN_X - 1), random.randint(0, ZELLEN_Y - 1))
            if pos not in alle_positionen:
                self.frucht_pos = pos
                break

    def aktuelle_frucht(self):
        return FRUECHTE[self.frucht_index % len(FRUECHTE)]

    # ── Frucht-Zeichenfunktionen ───────────────────────────────────────────

    def _apfel_zeichnen(self, cx, cy):
        pygame.draw.ellipse(self.flaeche, (200, 0, 0),
                            pygame.Rect(cx - 7, cy - 6, 14, 13))
        pygame.draw.ellipse(self.flaeche, (255, 80, 80),
                            pygame.Rect(cx - 4, cy - 5, 5, 5))
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx, cy - 7), (cx + 3, cy - 11), 2)

    def _banane_zeichnen(self, cx, cy):
        punkte = []
        for i in range(11):
            t = i / 10
            winkel = math.pi * 0.15 + t * math.pi * 0.7
            px = int(cx + 7 * math.cos(winkel) * 1.1)
            py = int(cy - 7 * math.sin(winkel))
            punkte.append((px, py))
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENDUNKEL, punkte[i], punkte[i + 1], 5)
        for i in range(len(punkte) - 1):
            pygame.draw.line(self.flaeche, BANANENGELB,   punkte[i], punkte[i + 1], 3)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[0],  2)
        pygame.draw.circle(self.flaeche, BANANENDUNKEL, punkte[-1], 2)

    def _ananas_zeichnen(self, cx, cy):
        pygame.draw.ellipse(self.flaeche, (255, 200, 0),
                            pygame.Rect(cx - 5, cy - 4, 10, 12))
        for row in range(3):
            for col in range(2):
                ox = -3 + col * 5 + (row % 2) * 2
                oy = -2 + row * 4
                pygame.draw.rect(self.flaeche, (200, 140, 0),
                                 pygame.Rect(cx + ox, cy + oy, 3, 3), 1)
        for bx, by in [(-3, -7), (0, -9), (3, -7)]:
            pygame.draw.line(self.flaeche, (0, 160, 0),
                             (cx, cy - 4), (cx + bx, cy + by), 2)

    def _kirsche_zeichnen(self, cx, cy):
        for dx in (-4, 4):
            pygame.draw.circle(self.flaeche, (180, 0, 30), (cx + dx, cy + 4), 4)
            pygame.draw.circle(self.flaeche, (255, 80, 80), (cx + dx - 1, cy + 2), 1)
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx - 4, cy),   (cx, cy - 6), 1)
        pygame.draw.line(self.flaeche, DUNKELGRUEN, (cx + 4, cy),   (cx, cy - 6), 1)
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

    # ── HUD ───────────────────────────────────────────────────────────────

    def gitter_zeichnen(self):
        for x in range(0, BREITE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (x, 0), (x, HOEHE))
        for y in range(0, HOEHE, ZELLEN_GROESSE):
            pygame.draw.line(self.flaeche, GRAU, (0, y), (BREITE, y))

    def hud_zeichnen(self):
        frucht_namen = {"apfel": "Apfel", "banane": "Banane",
                        "ananas": "Ananas", "kirsche": "Kirsche"}
        if self.spieler_anzahl == 1:
            t = self.schrift_klein.render(
                f"Punkte: {self.punkte[0]}   Frucht: {frucht_namen[self.aktuelle_frucht()]}",
                True, WEISS)
            self.flaeche.blit(t, (8, 8))
        else:
            p1_str = "GESTORBEN" if not self.schlangen[0].lebt else str(self.punkte[0])
            p2_str = "GESTORBEN" if not self.schlangen[1].lebt else str(self.punkte[1])
            t1 = self.schrift_klein.render(f"P1: {p1_str}", True, PINK)
            t2 = self.schrift_klein.render(f"P2: {p2_str}", True, TURKIES)
            tf = self.schrift_winzig.render(frucht_namen[self.aktuelle_frucht()], True, WEISS)
            self.flaeche.blit(t1, (8, 8))
            self.flaeche.blit(t2, (BREITE - t2.get_width() - 8, 8))
            self.flaeche.blit(tf, tf.get_rect(center=(BREITE // 2, 12)))

    # ── Ereignisse ────────────────────────────────────────────────────────

    def ereignisse_verarbeiten(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                s1 = self.schlangen[0]
                pfeiltasten = {
                    pygame.K_UP: OBEN, pygame.K_DOWN: UNTEN,
                    pygame.K_LEFT: LINKS, pygame.K_RIGHT: RECHTS,
                }
                wasd = {
                    pygame.K_w: OBEN, pygame.K_s: UNTEN,
                    pygame.K_a: LINKS, pygame.K_d: RECHTS,
                }

                if self.spieler_anzahl == 1:
                    # Pfeiltasten UND WASD steuern die eine Schlange
                    steuerung = {**pfeiltasten, **wasd}
                    if event.key in steuerung and s1.lebt:
                        s1.richtung_setzen(steuerung[event.key])
                else:
                    # P1 = Pfeiltasten, P2 = WASD
                    s2 = self.schlangen[1]
                    if event.key in pfeiltasten and s1.lebt:
                        s1.richtung_setzen(pfeiltasten[event.key])
                    if event.key in wasd and s2.lebt:
                        s2.richtung_setzen(wasd[event.key])

    # ── Spiellogik ────────────────────────────────────────────────────────

    def aktualisieren(self):
        if self.spieler_anzahl == 1:
            self._update_1spieler()
        else:
            self._update_2spieler()

    def _update_1spieler(self):
        s = self.schlangen[0]
        s.bewegen()
        if s.kollision_wand() or s.kollision_selbst():
            self.game_over = True
            return
        if s.koerper[0] == self.frucht_pos:
            s.wachsen()
            self.punkte[0] += 10
            self.frucht_index += 1
            self.frucht_platzieren()

    def _update_2spieler(self):
        s1, s2 = self.schlangen

        # Merke ob die Schlangen zu Beginn dieses Ticks noch lebten
        s1_lebt_vorher = s1.lebt
        s2_lebt_vorher = s2.lebt

        if s1.lebt:
            s1.bewegen()
        if s2.lebt:
            s2.bewegen()

        # Wand- und Selbstkollision
        if s1.lebt and (s1.kollision_wand() or s1.kollision_selbst()):
            s1.lebt = False
        if s2.lebt and (s2.kollision_wand() or s2.kollision_selbst()):
            s2.lebt = False

        # Kreuz-Kollision: Kopf trifft Körper der anderen Schlange
        # Nur prüfen wenn beide vorher noch lebten
        if s1_lebt_vorher and s2_lebt_vorher:
            s1_trifft = s1.lebt and s1.kopf_trifft(s2)
            s2_trifft = s2.lebt and s2.kopf_trifft(s1)
            if s1_trifft:
                s1.lebt = False
            if s2_trifft:
                s2.lebt = False

        # Frucht essen – erste lebende Schlange die drauf steht bekommt die Punkte
        for i, s in enumerate(self.schlangen):
            if s.lebt and s.koerper[0] == self.frucht_pos:
                s.wachsen()
                self.punkte[i] += 10
                self.frucht_index += 1
                self.frucht_platzieren()
                break  # Frucht kann nur einmal gegessen werden

        if not s1.lebt and not s2.lebt:
            self.game_over = True

    # ── Zeichnen ──────────────────────────────────────────────────────────

    def zeichnen(self):
        self.flaeche.fill(SCHWARZ)
        self.gitter_zeichnen()
        self.frucht_zeichnen()
        for s in self.schlangen:
            if s.lebt:
                s.zeichnen(self.flaeche)
        self.hud_zeichnen()
        pygame.display.flip()

    def gewinner_bildschirm(self):
        if self.punkte[0] > self.punkte[1]:
            msg, farbe = "SPIELER 1 GEWINNT!", PINK
        elif self.punkte[1] > self.punkte[0]:
            msg, farbe = "SPIELER 2 GEWINNT!", TURKIES
        else:
            msg, farbe = "UNENTSCHIEDEN!", GELB

        overlay = pygame.Surface((BREITE, HOEHE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.flaeche.blit(overlay, (0, 0))

        t = self.schrift_gross.render(msg, True, farbe)
        self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, HOEHE // 2 - 70)))

        p1t = self.schrift_mittel.render(f"P1: {self.punkte[0]}", True, PINK)
        p2t = self.schrift_mittel.render(f"P2: {self.punkte[1]}", True, TURKIES)
        self.flaeche.blit(p1t, p1t.get_rect(center=(BREITE // 2 - 90, HOEHE // 2)))
        self.flaeche.blit(p2t, p2t.get_rect(center=(BREITE // 2 + 90, HOEHE // 2)))

        weiter = self.schrift_winzig.render("Weiter in 3 Sekunden...", True, GRAU)
        self.flaeche.blit(weiter, weiter.get_rect(center=(BREITE // 2, HOEHE // 2 + 60)))
        pygame.display.flip()
        pygame.time.wait(3000)

    # ── Highscores ────────────────────────────────────────────────────────

    def highscore_qualifiziert(self, punkte):
        if punkte == 0:
            return False
        return len(self.highscores) < 10 or punkte > self.highscores[-1]["punkte"]

    def namen_eingabe(self, punkte, titel_farbe=GELB, spieler_label=""):
        buchstaben = [65, 65, 65]
        cursor = 0
        schrift_letter = pygame.font.SysFont("monospace", 56, bold=True)

        while True:
            self.flaeche.fill(SCHWARZ)

            header = f"NEUER HIGHSCORE!{spieler_label}"
            t = self.schrift_mittel.render(header, True, titel_farbe)
            self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, 160)))

            p = self.schrift_klein.render(f"Punkte: {punkte}", True, WEISS)
            self.flaeche.blit(p, p.get_rect(center=(BREITE // 2, 210)))

            hint = self.schrift_winzig.render(
                "Pfeiltasten: Buchstabe   Links/Rechts: Cursor   ENTER: OK",
                True, GRAU)
            self.flaeche.blit(hint, hint.get_rect(center=(BREITE // 2, 262)))

            start_x = BREITE // 2 - (3 * 60 + 2 * 20) // 2
            for i, code in enumerate(buchstaben):
                x = start_x + i * 80
                farbe_box = titel_farbe if i == cursor else GRAU
                pygame.draw.rect(self.flaeche, farbe_box,
                                 pygame.Rect(x, 305, 60, 70), 3)
                letter = schrift_letter.render(chr(code), True, WEISS)
                self.flaeche.blit(letter, letter.get_rect(center=(x + 30, 340)))

            pfeil = self.schrift_mittel.render("v", True, titel_farbe)
            self.flaeche.blit(pfeil, pfeil.get_rect(center=(start_x + cursor * 80 + 30, 388)))

            pygame.display.flip()
            self.uhr.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
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

    def highscores_verarbeiten(self):
        if self.spieler_anzahl == 1:
            if self.highscore_qualifiziert(self.punkte[0]):
                name = self.namen_eingabe(self.punkte[0])
                self.highscores.append({"name": name, "punkte": self.punkte[0]})
        else:
            farben  = [PINK, TURKIES]
            labels  = [" (Spieler 1)", " (Spieler 2)"]
            for i in range(2):
                if self.highscore_qualifiziert(self.punkte[i]):
                    name = self.namen_eingabe(self.punkte[i],
                                              titel_farbe=farben[i],
                                              spieler_label=labels[i])
                    self.highscores.append({"name": name, "punkte": self.punkte[i]})

        self.highscores.sort(key=lambda e: e["punkte"], reverse=True)
        self.highscores = self.highscores[:10]
        speichere_highscores(self.highscores)

    def highscore_anzeigen(self):
        aktuell = set(self.punkte)
        while True:
            self.flaeche.fill(SCHWARZ)

            t = self.schrift_gross.render("HIGHSCORES", True, GELB)
            self.flaeche.blit(t, t.get_rect(center=(BREITE // 2, 50)))

            for rang, eintrag in enumerate(self.highscores):
                farbe = GELB if eintrag["punkte"] in aktuell else WEISS
                zeile = f"{rang+1:2}. {eintrag['name']}   {eintrag['punkte']:>6}"
                txt = self.schrift_klein.render(zeile, True, farbe)
                self.flaeche.blit(txt, txt.get_rect(center=(BREITE // 2, 110 + rang * 34)))

            if not self.highscores:
                leer = self.schrift_klein.render("Noch keine Eintraege", True, GRAU)
                self.flaeche.blit(leer, leer.get_rect(center=(BREITE // 2, 200)))

            hint = self.schrift_winzig.render(
                "ENTER = Neues Spiel    ESC = Beenden", True, GRAU)
            self.flaeche.blit(hint, hint.get_rect(center=(BREITE // 2, 490)))
            pygame.display.flip()
            self.uhr.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

    # ── Hauptschleife ─────────────────────────────────────────────────────

    def starten(self):
        while True:
            self.spieler_waehlen()
            self.neues_spiel()

            while not self.game_over:
                self.ereignisse_verarbeiten()
                self.aktualisieren()
                self.zeichnen()
                self.uhr.tick(FPS)

            if self.spieler_anzahl == 2:
                self.zeichnen()  # letzter Spielzustand
                self.gewinner_bildschirm()

            self.highscores_verarbeiten()
            self.highscore_anzeigen()


if __name__ == "__main__":
    spiel = Spiel()
    spiel.starten()
