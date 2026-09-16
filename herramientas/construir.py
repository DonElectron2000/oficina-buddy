#!/usr/bin/env python3
"""
Oficina Buddy — generador del mapa de WorkAdventure.

Este script arma todo lo propio de la oficina:
  - tilesets/buddy_ambiente.png  paredes, pisos, alfombras, muebles y objetos dibujados a mano
  - tilesets/buddy_carteles.png  placas con nombres, carteles, pantallas y logo de Ardiflet
  - tilesets/buddy_logo.png      logo de Buddy para la recepción
  - tilesets/buddy_cuadro.png    cuadro con la foto de los bolsos
  - oficina.tmj                  el mapa
  - oficina.png                  la vista previa del mapa

Uso (desde la carpeta del proyecto):
    python3 herramientas/construir.py

Lo único que deberías tocar es la sección CONFIGURACIÓN de acá abajo.
Si editás oficina.tmj a mano con Tiled, no vuelvas a correr este script:
lo pisaría con lo que dice acá.
"""

import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# ════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════

# Escritorios fijos con placa. Cambiá solo lo que está a la derecha de los dos puntos.
NOMBRES = {
    "pablo": "Pablo",    # oficina Founders
    "sofi": "Sofi",      # oficina Founders
    "vero": "Vero",      # sala de Experiencia del cliente
    "ivan": "Ivan",      # oficina Ardiflet
    "camilo": "Camilo",  # oficina Ardiflet
}

# Cowork: 8 puestos compartidos. "" = puesto libre, sin placa.
# Orden: fila de arriba de izquierda a derecha, después la fila de abajo.
COWORK = ["Mateo", "", "", "", "", "", "", ""]

# Content room: 3 puestos de edición. "" = sin placa.
CONTENT_ROOM = ["", "", ""]

# Pantallas de pared que abren un link cuando te parás adelante y apretás ESPACIO.
#   lugar: "recepcion", "reuniones" (Sala de Embarque) o "content" (Content room)
#   texto: lo que se lee en la pantalla
#   url:   el link (tiene que empezar con https://)
#   abrir: "pestaña" = se abre en una pestaña nueva (funciona siempre)
#          "adentro" = se abre al costado, dentro de WorkAdventure
#                      (solo si la página lo permite; Tiendanube, por ejemplo, no)
PANTALLAS = [
    {"lugar": "recepcion", "texto": "tiendabuddy.ar", "url": "https://www.tiendabuddy.ar", "abrir": "pestaña"},
    # Ejemplo: borrá el "#" de la línea de abajo y poné tu link de Notion.
    # {"lugar": "reuniones", "texto": "Notion", "url": "https://www.notion.so/tu-tablero", "abrir": "pestaña"},
]

MAPA_NOMBRE = "Oficina Buddy"
MAPA_DESCRIPCION = "Tu compañero de viaje. Oficina virtual del equipo Buddy."
MAPA_COPYRIGHT = "Buddy"

# ════════════════════════════════════════════════════════════════════
#  De acá para abajo es la maquinaria. No hace falta tocarla.
# ════════════════════════════════════════════════════════════════════

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILESETS = os.path.join(RAIZ, "tilesets")
ORIGINALES = os.path.join(RAIZ, "originales")
T = 32
ANCHO, ALTO_EDIFICIO = 42, 22  # el edificio, en tiles
JARDIN = 3                     # filas de jardín arriba: ahí quedan los botones de WorkAdventure y no tapan oficinas
W, H = ANCHO, ALTO_EDIFICIO + JARDIN

# Coordenadas "del edificio": y=0 es la pared de arriba del edificio (debajo del jardín).
# Huecos de pared donde puede ir una pantalla (esquina superior izquierda, 3x2 tiles).
LUGARES_PANTALLA = {"recepcion": (21, 16), "reuniones": (11, 1), "content": (4, 1)}
EQUIPO_ARDIFLET = ("ivan", "camilo")
ENTRADA = (17, 19)  # donde aparece la gente (2 tiles: x y x+1)


def c(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def tono(col, f):
    return tuple(max(0, min(255, int(v * f))) for v in col[:3]) + (col[3],)


# Paleta de la marca
VERDE = c("#173A37")
SALVIA = c("#5F7E7A")
MEDIO = c("#485955")
CREMA = c("#F3F0E3")
BEIGE = c("#D2C2B5")
MADERA = c("#7F6D5F")
MADERA_OSC = c("#564C43")
# Paleta de Ardiflet (tomada de ardiflet.com)
PETROLEO = c("#08272E")
PETROLEO2 = c("#0E3A43")
NARANJA = c("#D86621")
MOSTAZA = c("#F1BA62")
HUESO = c("#F5F3EE")
LINEA = c("#D8D6CF")
# Derivados
SUPERFICIE = tono(MADERA, 1.12)  # tapa de escritorios: la misma madera, un toque más clara
ROSA = c("#E7B2A6")
NEGRO = c("#262626")
AGUA = c("#8FB3AE")
SOMBRA = (0, 0, 0, 50)
NADA = (0, 0, 0, 0)


def fuente(tam):
    for ruta in (
        "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def texto_centrado(d, cx, cy, txt, col, tam_max, ancho_max):
    tam = tam_max
    while True:
        f = fuente(tam)
        b = d.textbbox((0, 0), txt, font=f)
        if b[2] - b[0] <= ancho_max or tam <= 7:
            break
        tam -= 1
    d.text((round(cx - (b[2] - b[0]) / 2 - b[0]), round(cy - (b[3] - b[1]) / 2 - b[1])), txt, font=f, fill=col)


def lienzo(w, h, fondo=NADA):
    im = Image.new("RGBA", (w * T, h * T), fondo)
    return im, ImageDraw.Draw(im)


# ─── Hoja de tiles: va acomodando dibujos de varios tiles en una sola imagen ───

class Hoja:
    def __init__(self, archivo, columnas):
        self.archivo = archivo
        self.cols = columnas
        self.items = {}
        self.cx = self.cy = self.alto_fila = 0

    def agregar(self, nombre, img):
        w, h = img.width // T, img.height // T
        if self.cx + w > self.cols:
            self.cx, self.cy, self.alto_fila = 0, self.cy + self.alto_fila, 0
        self.items[nombre] = (self.cx, self.cy, w, h, img)
        self.cx += w
        self.alto_fila = max(self.alto_fila, h)

    def guardar(self):
        filas = self.cy + self.alto_fila
        hoja = Image.new("RGBA", (self.cols * T, filas * T), NADA)
        self.ids = {}
        for nombre, (x, y, w, h, img) in self.items.items():
            hoja.alpha_composite(img, (x * T, y * T))
            self.ids[nombre] = [[(y + r) * self.cols + (x + k) for k in range(w)] for r in range(h)]
        hoja.save(os.path.join(TILESETS, self.archivo))
        return self


# ─── Dibujos: paredes y pisos ───

PAREDES = {
    # nombre: (color de pared, zócalo y marcos, línea del zócalo)
    "salvia": (SALVIA, VERDE, MEDIO),
    "ard": (PETROLEO2, NARANJA, MOSTAZA),
}


def tapa_pared(n, e, s, o):
    """Parte de arriba de la pared, en verde salvia con borde verde oscuro."""
    im, d = lienzo(1, 1, SALVIA)
    rnd = random.Random(7)
    for _ in range(16):
        d.point((rnd.randrange(T), rnd.randrange(T)), tono(SALVIA, 1.06))
    if not n:
        d.line([0, 3, T - 1, 3], fill=tono(SALVIA, 1.18))
        d.rectangle([0, 0, T - 1, 2], fill=VERDE)
    if not s:
        d.rectangle([0, T - 3, T - 1, T - 1], fill=VERDE)
    if not o:
        d.rectangle([0, 0, 2, T - 1], fill=VERDE)
    if not e:
        d.rectangle([T - 3, 0, T - 1, T - 1], fill=VERDE)
    return im


def cara_pared(paleta, sombra, zocalo, jamba_izq=False, jamba_der=False):
    """Frente de la pared, con zócalo y marco de puerta si corresponde."""
    base, marco, filete = PAREDES[paleta]
    im, d = lienzo(1, 1, base)
    rnd = random.Random(3)
    for _ in range(12):
        d.point((rnd.randrange(T), rnd.randrange(T)), tono(base, 1.06))
    if sombra:
        d.rectangle([0, 0, T - 1, 2], fill=tono(base, 0.78))
        d.line([0, 3, T - 1, 3], fill=tono(base, 0.9))
    if zocalo:
        d.line([0, 9, T - 1, 9], fill=tono(base, 1.18))
        d.line([0, 10, T - 1, 10], fill=tono(base, 0.86))
        for x in (0, 16):
            d.line([x, 11, x, 24], fill=tono(base, 0.93))
        d.rectangle([0, 25, T - 1, T - 1], fill=marco)
        d.line([0, 25, T - 1, 25], fill=filete)
    if jamba_izq:
        d.rectangle([0, 0, 3, T - 1], fill=marco)
        d.line([4, 0, 4, T - 1], fill=tono(base, 0.85))
    if jamba_der:
        d.rectangle([T - 4, 0, T - 1, T - 1], fill=marco)
        d.line([T - 5, 0, T - 5, T - 1], fill=tono(base, 0.85))
    return im


def piso_madera(variante):
    im, d = lienzo(1, 1)
    tonos = [tono(MADERA, 1.04), MADERA, tono(MADERA, 1.02), tono(MADERA, 0.98)]
    juntas = [[21], [7], [27], [14]] if variante == 0 else [[3], [24], [12], [30]]
    for i in range(4):
        y0, col = i * 8, tonos[i]
        d.rectangle([0, y0, T - 1, y0 + 7], fill=col)
        rnd = random.Random(100 + variante * 10 + i)
        for _ in range(6):
            x, y = rnd.randrange(T), y0 + rnd.randrange(2, 7)
            d.line([x, y, min(T - 1, x + rnd.randrange(3, 9)), y], fill=tono(col, 0.95))
        d.line([0, y0, T - 1, y0], fill=tono(col, 1.04))
        d.line([0, y0 + 7, T - 1, y0 + 7], fill=tono(col, 0.91))
        for jx in juntas[i]:
            d.line([jx, y0 + 1, jx, y0 + 6], fill=tono(col, 0.91))
    return im


def piso_crema():
    im, d = lienzo(1, 1, CREMA)
    junta = c("#E6DFCE")
    d.line([0, 0, T - 1, 0], fill=junta)
    d.line([0, 0, 0, T - 1], fill=junta)
    return im


def piso_ardiflet():
    """Piso de depósito prolijo: baldosón hueso con juntas grises."""
    im, d = lienzo(1, 1, HUESO)
    rnd = random.Random(11)
    for _ in range(14):
        d.point((rnd.randrange(T), rnd.randrange(T)), tono(HUESO, 0.95))
    d.line([0, 0, T - 1, 0], fill=LINEA)
    d.line([0, 0, 0, T - 1], fill=LINEA)
    return im


def piso_deck():
    im, d = lienzo(1, 1)
    tonos = [tono(MADERA, 1.03), MADERA, tono(MADERA, 1.06), tono(MADERA, 0.97)]
    for i in range(4):
        y0, col = i * 8, tonos[i]
        d.rectangle([0, y0, T - 1, y0 + 7], fill=col)
        d.line([0, y0, T - 1, y0], fill=tono(col, 1.08))
        d.line([0, y0 + 7, T - 1, y0 + 7], fill=MADERA_OSC)
        d.line([0, y0, 0, y0 + 6], fill=MADERA_OSC)
        for x in (4, 27):
            d.point((x, y0 + 3), fill=MADERA_OSC)
    return im


def alfombra():
    """Alfombra beige de 3x3 tiles: esquinas, bordes y centro repetible."""
    im, d = lienzo(3, 3)
    d.rectangle([3, 1, 92, 94], fill=BEIGE)
    d.rectangle([3, 1, 92, 94], outline=tono(BEIGE, 0.9), width=3)
    d.rectangle([8, 6, 87, 89], outline=CREMA)
    for ty in range(3):
        for tx in range(3):
            cx, cy = tx * T + 16, ty * T + 16
            for dx, dy in ((0, 0), (-3, 0), (3, 0), (0, -3), (0, 3)):
                d.point((cx + dx, cy + dy), fill=tono(BEIGE, 0.94))
    for y in range(3, 94, 3):
        d.line([0, y, 2, y], fill=CREMA)
        d.line([93, y, 95, y], fill=CREMA)
    return im


# ─── Dibujos: muebles ───

def escritorio_tile(fila, pos):
    """Pedazo de escritorio. fila: 'sup' (tapa) o 'fre' (frente). pos: 'i', 'm' o 'd'."""
    im, d = lienzo(1, 1)
    x0 = 2 if pos == "i" else 0
    x1 = T - 3 if pos == "d" else T - 1
    rnd = random.Random({"i": 1, "m": 2, "d": 3}[pos])
    if fila == "sup":
        d.rectangle([x0, 2, x1, T - 1], fill=SUPERFICIE)
        d.line([x0, 2, x1, 2], fill=MADERA_OSC)
        d.line([x0, 3, x1, 3], fill=tono(SUPERFICIE, 1.1))
        for _ in range(5):
            x, y = rnd.randrange(x0, x1), rnd.randrange(6, T - 2)
            d.line([x, y, min(x1, x + rnd.randrange(4, 10)), y], fill=tono(SUPERFICIE, 0.95))
        if pos == "i":
            d.line([x0, 2, x0, T - 1], fill=MADERA_OSC)
        if pos == "d":
            d.line([x1, 2, x1, T - 1], fill=MADERA_OSC)
    else:
        d.rectangle([x0, 0, x1, 8], fill=SUPERFICIE)
        d.line([x0, 8, x1, 8], fill=tono(SUPERFICIE, 1.15))
        d.rectangle([x0, 9, x1, 24], fill=MADERA_OSC)
        d.line([x0, 24, x1, 24], fill=tono(MADERA_OSC, 0.8))
        sx0 = x0 + (4 if pos == "i" else 0)
        sx1 = x1 - (4 if pos == "d" else 0)
        d.rectangle([sx0, 25, sx1, 28], fill=SOMBRA)
        if pos == "i":
            d.line([x0, 0, x0, 24], fill=MADERA_OSC)
            d.rectangle([x0, 25, x0 + 3, 30], fill=MADERA_OSC)
        if pos == "d":
            d.line([x1, 0, x1, 24], fill=MADERA_OSC)
            d.rectangle([x1 - 3, 25, x1, 30], fill=MADERA_OSC)
    return im


SILLAS = {"verde": (VERDE, MEDIO), "ard": (NARANJA, MOSTAZA)}


def silla(mira, color="verde", solo_respaldo=False):
    """Silla vista desde arriba. mira: hacia dónde queda mirando quien se sienta."""
    im, d = lienzo(1, 1)
    base, luz = SILLAS[color]
    asiento, resp_col, borde = base, tono(base, 1.25), tono(base, 0.65)
    formas = {
        "arriba": ((8, 5, 23, 20), (6, 19, 25, 26)),
        "abajo": ((8, 11, 23, 26), (6, 4, 25, 11)),
        "izq": ((5, 8, 20, 23), (19, 6, 26, 25)),
        "der": ((11, 8, 26, 23), (5, 6, 12, 25)),
    }
    seat, resp = formas[mira]

    def dibujar_asiento():
        d.ellipse([8, 26, 23, 30], fill=SOMBRA)
        d.rounded_rectangle(seat, radius=4, fill=asiento, outline=borde)
        d.line([seat[0] + 3, seat[1] + 2, seat[2] - 3, seat[1] + 2], fill=luz)

    def dibujar_respaldo():
        d.rounded_rectangle(resp, radius=3, fill=resp_col, outline=borde)

    if solo_respaldo:
        dibujar_respaldo()
    elif mira == "abajo":
        dibujar_respaldo()
        dibujar_asiento()
    else:
        dibujar_asiento()
        dibujar_respaldo()
    return im


def puerta_entrada():
    im, d = lienzo(2, 1, SALVIA)
    d.rectangle([0, 0, 63, 31], outline=VERDE, width=3)
    d.rectangle([0, 6, 63, 25], fill=VERDE)
    d.rectangle([4, 9, 59, 22], fill=c("#BFD6D1"))
    d.line([31, 9, 32, 22], fill=VERDE, width=2)
    for x0 in (7, 39):
        d.line([x0, 20, x0 + 8, 11], fill=(255, 255, 255, 140))
    d.point((28, 15), fill=CREMA)
    d.point((35, 15), fill=CREMA)
    return im


def camara():
    im, d = lienzo(1, 2)
    pata = c("#2B2B2B")
    d.ellipse([4, 59, 28, 63], fill=SOMBRA)
    for xf in (5, 27, 16):
        d.line([16, 30, xf, 61], fill=pata, width=2)
    d.rounded_rectangle([6, 14, 26, 29], radius=2, fill=c("#1F1F1F"))
    d.rectangle([9, 17, 21, 25], fill=c("#5B7C82"))
    d.line([9, 17, 21, 17], fill=c("#8FB1B5"))
    d.rectangle([11, 10, 19, 13], fill=c("#1F1F1F"))
    d.point((24, 16), fill=(220, 60, 50, 255))
    return im


def luz_estudio():
    im, d = lienzo(1, 2)
    pata = c("#2B2B2B")
    d.ellipse([6, 59, 26, 63], fill=SOMBRA)
    d.line([16, 24, 16, 56], fill=pata, width=2)
    d.line([16, 54, 7, 62], fill=pata, width=2)
    d.line([16, 54, 25, 62], fill=pata, width=2)
    d.polygon([(4, 5), (28, 5), (24, 24), (8, 24)], fill=c("#FFFDF4"), outline=c("#9A9A9A"))
    d.line([8, 8, 24, 8], fill=c("#E9E4D4"))
    d.rectangle([8, 24, 24, 26], fill=c("#3A3A3A"))
    return im


def lampara():
    """Lámpara de pie con luz cálida."""
    im, d = lienzo(1, 2)
    brillo = Image.new("RGBA", im.size, NADA)
    ImageDraw.Draw(brillo).ellipse([0, 0, 31, 34], fill=(255, 214, 150, 60))
    im.alpha_composite(brillo)
    d.ellipse([8, 58, 24, 63], fill=SOMBRA)
    d.ellipse([10, 56, 22, 61], fill=MADERA_OSC)
    d.line([16, 20, 16, 58], fill=MADERA_OSC, width=2)
    d.polygon([(9, 6), (23, 6), (27, 20), (5, 20)], fill=CREMA, outline=tono(CREMA, 0.8))
    d.line([6, 19, 26, 19], fill=(255, 214, 150, 255))
    return im


def fondo_croma():
    """Fondo verde de grabación con su estructura, 3x3 tiles."""
    im, d = lienzo(3, 3)
    croma = c("#2FA84F")
    fierro = c("#2B2B2B")
    d.rectangle([6, 88, 90, 93], fill=SOMBRA)
    for x in (4, 91):
        d.line([x, 2, x, 90], fill=fierro, width=3)
        d.line([x - 5, 91, x + 5, 91], fill=fierro, width=2)
    d.line([4, 3, 91, 3], fill=fierro, width=3)
    d.rectangle([8, 5, 87, 76], fill=croma)
    for x in range(14, 87, 12):
        d.line([x, 5, x, 76], fill=tono(croma, 0.9))
    d.polygon([(8, 76), (87, 76), (90, 88), (5, 88)], fill=tono(croma, 1.08))
    return im


def cantero():
    """Cantero de madera con arbustos: el borde del patio interno."""
    im, d = lienzo(1, 1)
    d.rectangle([1, 28, 30, 31], fill=SOMBRA)
    d.rectangle([1, 15, 30, 28], fill=MADERA_OSC)
    d.line([1, 15, 30, 15], fill=tono(MADERA_OSC, 1.35))
    d.line([1, 22, 30, 22], fill=tono(MADERA_OSC, 0.85))
    hoja, luz, sombra = c("#5C8A3C"), c("#7FAE52"), c("#44692C")
    for cx, cy, r in ((8, 13, 8), (22, 12, 9), (15, 8, 8)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hoja, outline=sombra)
        d.ellipse([cx - r + 3, cy - r + 2, cx + 1, cy - 1], fill=luz)
    return im


def fuente_agua():
    """Fuente de piedra para el centro del patio, 2x2 tiles."""
    im, d = lienzo(2, 2)
    piedra, borde = c("#B7B1A6"), c("#77716A")
    d.ellipse([4, 44, 60, 62], fill=SOMBRA)
    d.ellipse([3, 20, 60, 58], fill=piedra, outline=borde, width=2)
    d.ellipse([10, 26, 53, 52], fill=AGUA, outline=tono(AGUA, 0.8))
    for r in (6, 12):
        d.arc([31 - r * 1.5, 39 - r, 32 + r * 1.5, 39 + r], 200, 340, fill=tono(AGUA, 1.2))
    d.rectangle([28, 18, 35, 40], fill=piedra, outline=borde)
    d.ellipse([20, 12, 43, 22], fill=piedra, outline=borde)
    d.ellipse([24, 14, 39, 20], fill=AGUA)
    for dx in (-8, 0, 8):
        d.arc([24 + dx, 2, 40 + dx, 26], 200, 340, fill=(235, 245, 243, 255), width=1)
    return im


def bolso(d, x, y, w, h, cuerpo, asa, brillo, logo=None):
    arriba = y + int(h * 0.4)
    d.arc([x + w * 0.24, y, x + w * 0.76, y + (arriba - y) * 2], 180, 360, fill=asa, width=2)
    d.rounded_rectangle([x, arriba, x + w - 1, y + h - 1], radius=3, fill=cuerpo)
    d.line([x + 3, arriba + 2, x + w - 4, arriba + 2], fill=tono(cuerpo, 0.72))
    d.line([x + 2, arriba + 4, x + 2, y + h - 4], fill=brillo)
    d.line([x + 1, y + h - 5, x + w - 2, y + h - 5], fill=tono(cuerpo, 0.8))
    if logo:
        d.rectangle([x + w // 2 - 3, arriba + 6, x + w // 2 + 2, arriba + 7], fill=logo)


def cartera(d, x, y, w, h, cuerpo, asa, brillo):
    """Cartera tipo tote, más alta que un bolso."""
    arriba = y + int(h * 0.35)
    d.arc([x + 4, y, x + w - 5, y + (arriba - y) * 2 + 2], 180, 360, fill=asa, width=2)
    d.polygon([(x, arriba), (x + w - 1, arriba), (x + w - 3, y + h - 1), (x + 2, y + h - 1)], fill=cuerpo)
    d.line([x + 3, arriba + 2, x + 3, y + h - 3], fill=brillo)
    d.line([x + 1, arriba, x + w - 2, arriba], fill=tono(cuerpo, 0.8))
    d.rectangle([x + w // 2 - 4, arriba + 6, x + w // 2 + 3, arriba + 7], fill=c("#1E1E1E"))


def estante_bolsos():
    """Estante de pared con los productos, 3x2 tiles."""
    im, d = lienzo(3, 2)
    for y in (27, 52):
        d.rectangle([4, y + 4, 93, y + 6], fill=(0, 0, 0, 40))
        d.rectangle([2, y, 93, y + 3], fill=SUPERFICIE)
        d.line([2, y + 3, 93, y + 3], fill=MADERA_OSC)
        for x in (10, 82):
            d.polygon([(x, y + 4), (x + 5, y + 4), (x, y + 10)], fill=MADERA_OSC)
    rosa_asa, rosa_brillo = c("#1E1E1E"), c("#F7D9D0")
    cartera(d, 6, 2, 26, 25, ROSA, rosa_asa, rosa_brillo)
    bolso(d, 36, 7, 26, 20, NEGRO, c("#111111"), c("#4B4B4B"), c("#3A3A3A"))
    bolso(d, 66, 7, 24, 20, VERDE, c("#0E2624"), c("#2F5A55"), CREMA)
    bolso(d, 7, 33, 24, 19, BEIGE, MADERA_OSC, c("#E6DAD0"), VERDE)
    bolso(d, 36, 33, 24, 19, SALVIA, c("#2E403D"), c("#86A29E"), CREMA)
    cartera(d, 65, 30, 24, 22, ROSA, rosa_asa, rosa_brillo)
    return im


def exhibidor():
    """Pedestal crema con una cartera rosa arriba, 2x1 tiles."""
    im, d = lienzo(2, 1)
    d.rectangle([8, 28, 58, 31], fill=SOMBRA)
    d.rectangle([6, 15, 57, 18], fill=CREMA)
    d.rectangle([6, 19, 57, 29], fill=tono(CREMA, 0.9))
    d.rectangle([6, 15, 57, 29], outline=tono(CREMA, 0.72))
    cartera(d, 20, 0, 24, 16, ROSA, c("#1E1E1E"), c("#F7D9D0"))
    return im


def caja(d, x, y, w, h):
    """Caja de cartón con los colores de Ardiflet."""
    tapa = 6
    d.rectangle([x, y, x + w - 1, y + tapa], fill=tono(MOSTAZA, 1.08), outline=PETROLEO)
    d.rectangle([x, y + tapa, x + w - 1, y + h - 1], fill=MOSTAZA, outline=PETROLEO)
    cx = x + w // 2
    d.rectangle([cx - 2, y, cx + 1, y + tapa + 5], fill=NARANJA)
    d.rectangle([x + w - 9, y + h - 9, x + w - 4, y + h - 4], outline=PETROLEO)


def pila_cajas():
    """Pila de cajas listas para despachar, 2x2 tiles."""
    im, d = lienzo(2, 2)
    d.ellipse([2, 56, 62, 63], fill=SOMBRA)
    caja(d, 3, 30, 30, 30)
    caja(d, 34, 36, 27, 24)
    caja(d, 12, 6, 28, 25)
    return im


def caja_chica():
    im, d = lienzo(1, 1)
    d.ellipse([3, 26, 29, 31], fill=SOMBRA)
    caja(d, 4, 10, 24, 19)
    return im


# ─── Dibujos: carteles, pantallas, logos y cuadro ───

def placa_escritorio(nombre, estilo="buddy"):
    """Placa con el nombre, va pegada al frente del escritorio."""
    im, d = lienzo(2, 1)
    if estilo == "ard":
        d.rounded_rectangle([7, 11, 56, 23], radius=2, fill=PETROLEO)
        d.rectangle([7, 11, 10, 23], fill=NARANJA)
        texto_centrado(d, 33, 17, nombre, HUESO, 10, 42)
    else:
        d.rounded_rectangle([7, 11, 56, 23], radius=2, fill=VERDE)
        d.rounded_rectangle([8, 12, 55, 22], radius=1, outline=MEDIO)
        texto_centrado(d, 31.5, 17, nombre, CREMA, 10, 44)
    return im


def cartel_puerta(texto, ancho=3):
    """Cartelito de sala, al lado de la puerta, ancho x 1 tiles."""
    im, d = lienzo(ancho, 1)
    x1 = ancho * T - 4
    d.rounded_rectangle([5, 6, x1 + 2, 22], radius=2, fill=SOMBRA)
    d.rounded_rectangle([3, 4, x1, 20], radius=2, fill=VERDE)
    d.rounded_rectangle([5, 6, x1 - 2, 18], radius=1, outline=CREMA)
    texto_centrado(d, (3 + x1) / 2, 12, texto, CREMA, 11, x1 - 16)
    return im


def cartel_grande(lineas, ancho=3):
    """Cartel de ancho x 2 tiles. lineas: lista de (texto, tamaño)."""
    im, d = lienzo(ancho, 2)
    x1 = ancho * T - 4
    d.rounded_rectangle([5, 8, x1 + 2, 52], radius=3, fill=SOMBRA)
    d.rounded_rectangle([3, 6, x1, 50], radius=3, fill=VERDE)
    d.rounded_rectangle([6, 9, x1 - 3, 47], radius=2, outline=CREMA)
    paso = 36 / (len(lineas) + 1)
    for i, (linea, tam) in enumerate(lineas):
        texto_centrado(d, (3 + x1) / 2, 10 + paso * (i + 1), linea, CREMA, tam, x1 - 20)
    return im


def pantalla_link(texto, con_bolso):
    im, d = lienzo(3, 2)
    d.rectangle([6, 9, 94, 56], fill=SOMBRA)
    d.rounded_rectangle([3, 5, 92, 53], radius=3, fill=c("#1B1D1D"))
    d.rectangle([6, 8, 89, 50], fill=VERDE)
    if con_bolso:
        bolso(d, 37, 12, 21, 17, ROSA, c("#1E1E1E"), c("#F7D9D0"), c("#1E1E1E"))
        texto_centrado(d, 47.5, 40, texto, CREMA, 12, 78)
    else:
        texto_centrado(d, 47.5, 29, texto, CREMA, 15, 78)
    d.line([81, 46, 86, 41], fill=CREMA)
    d.line([83, 41, 86, 41], fill=CREMA)
    d.line([86, 41, 86, 44], fill=CREMA)
    d.point((47, 51), fill=(120, 220, 140, 255))
    return im


def partes_logo_ardiflet():
    """Separa la ardilla y el texto del logo completo (que ya viene sobre fondo petróleo)."""
    logo = Image.open(os.path.join(ORIGINALES, "ardiflet_logo.png")).convert("RGB")
    fondo = logo.getpixel((5, 5))
    ardilla = logo.crop((295, 200, 875, 700))
    texto = logo.crop((100, 728, 1068, 925))
    return fondo, ardilla, texto


def encajar(img, ancho, alto):
    esc = min(ancho / img.width, alto / img.height)
    return img.resize((max(1, round(img.width * esc)), max(1, round(img.height * esc))), Image.LANCZOS)


def cartel_ardiflet():
    """Cartel de 5x2 tiles: ardilla con el paquete + ARDIFLET, sobre petróleo."""
    fondo, ardilla, texto = partes_logo_ardiflet()
    im, d = lienzo(5, 2)
    panel = fondo + (255,)
    d.rounded_rectangle([3, 4, 159, 55], radius=3, fill=SOMBRA)
    d.rounded_rectangle([1, 2, 157, 53], radius=3, fill=panel)
    d.rectangle([1, 50, 157, 53], fill=NARANJA)
    a = encajar(ardilla, 56, 46).convert("RGBA")
    im.alpha_composite(a, (6, 3 + (46 - a.height) // 2))
    t = encajar(texto, 88, 22).convert("RGBA")
    im.alpha_composite(t, (64, 14))
    texto_centrado(d, 108, 41, "mensajería en el AMBA", MOSTAZA, 8, 88)
    return im


def cartel_puerta_ardiflet():
    fondo, _, texto = partes_logo_ardiflet()
    im, d = lienzo(3, 1)
    d.rounded_rectangle([5, 6, 94, 24], radius=2, fill=SOMBRA)
    d.rounded_rectangle([3, 4, 92, 22], radius=2, fill=fondo + (255,))
    d.rectangle([3, 20, 92, 22], fill=NARANJA)
    t = encajar(texto, 74, 13).convert("RGBA")
    im.alpha_composite(t, ((96 - t.width) // 2, 5 + (14 - t.height) // 2))
    return im


def logo_recepcion():
    """192x64: panel verde oscuro con el logo en crema, colgado sobre la pared salvia."""
    im = Image.new("RGBA", (6 * T, 2 * T), NADA)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([5, 6, 191, 56], radius=3, fill=SOMBRA)
    d.rounded_rectangle([2, 3, 189, 54], radius=3, fill=VERDE)
    d.rounded_rectangle([5, 6, 186, 51], radius=2, outline=MEDIO)
    src = Image.open(os.path.join(ORIGINALES, "BUDDY_isologo_bn.jpg")).convert("L")
    mascara = src.point(lambda v: 255 - v)
    mascara = mascara.crop(mascara.point(lambda v: 255 if v > 60 else 0).getbbox())
    escala = min(166 / mascara.width, 38 / mascara.height)
    tam = (round(mascara.width * escala), round(mascara.height * escala))
    mascara = mascara.resize(tam, Image.LANCZOS).point(lambda v: 0 if v < 60 else (255 if v > 190 else v))
    capa = Image.new("RGBA", tam, CREMA)
    capa.putalpha(mascara)
    im.alpha_composite(capa, ((192 - tam[0]) // 2, 29 - tam[1] // 2))
    return im


def cuadro_bolsos():
    """96x64: la foto de los bolsos pixelada, con marco de madera."""
    im, d = lienzo(3, 2)
    d.rectangle([6, 5, 95, 57], fill=SOMBRA)
    d.rectangle([3, 2, 92, 55], fill=MADERA_OSC)
    d.rectangle([5, 4, 90, 53], fill=MADERA)
    d.line([5, 4, 90, 4], fill=tono(MADERA, 1.25))
    d.rectangle([7, 6, 88, 51], fill=tono(MADERA_OSC, 0.8))
    foto = Image.open(os.path.join(ORIGINALES, "foto_bolsos.png")).convert("RGB")
    ancho, alto = 80, 44
    fw = foto.width
    fh = round(fw * alto / ancho)
    cy = int(foto.height * 0.5)
    foto = foto.crop((0, cy - fh // 2, fw, cy - fh // 2 + fh)).resize((ancho, alto), Image.LANCZOS)
    foto = foto.quantize(colors=20, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    im.alpha_composite(foto, (8, 7))
    return im


# ════════════════════════════════════════════════════════════════════
#  1) Generar los tilesets propios
# ════════════════════════════════════════════════════════════════════

def generar_tilesets():
    amb = Hoja("buddy_ambiente.png", 8)
    for m in range(16):
        amb.agregar(f"tapa{m}", tapa_pared(m & 1, m & 2, m & 4, m & 8))
    for paleta in PAREDES:
        for tipo, sombra, zocalo in (("alta", True, False), ("baja", False, True), ("unica", True, True)):
            for ji, jd in ((False, False), (True, False), (False, True)):
                amb.agregar(f"cara_{paleta}_{tipo}_{int(ji)}{int(jd)}", cara_pared(paleta, sombra, zocalo, ji, jd))
    amb.agregar("madera0", piso_madera(0))
    amb.agregar("madera1", piso_madera(1))
    amb.agregar("crema", piso_crema())
    amb.agregar("piso_ard", piso_ardiflet())
    amb.agregar("deck", piso_deck())
    amb.agregar("cantero", cantero())
    for fila in ("sup", "fre"):
        for pos in ("i", "m", "d"):
            amb.agregar(f"esc_{fila}_{pos}", escritorio_tile(fila, pos))
    for color in SILLAS:
        for mira in ("arriba", "abajo", "izq", "der"):
            amb.agregar(f"silla_{color}_{mira}", silla(mira, color))
        amb.agregar(f"silla_{color}_respaldo", silla("arriba", color, solo_respaldo=True))
    amb.agregar("puerta", puerta_entrada())
    amb.agregar("exhibidor", exhibidor())
    amb.agregar("camara", camara())
    amb.agregar("luz", luz_estudio())
    amb.agregar("lampara", lampara())
    amb.agregar("caja_chica", caja_chica())
    amb.agregar("alfombra", alfombra())
    amb.agregar("croma", fondo_croma())
    amb.agregar("estante", estante_bolsos())
    amb.agregar("cajas", pila_cajas())
    amb.agregar("fuente", fuente_agua())
    amb.guardar()

    car = Hoja("buddy_carteles.png", 8)
    for clave, nombre in NOMBRES.items():
        car.agregar(f"placa_{clave}", placa_escritorio(nombre, "ard" if clave in EQUIPO_ARDIFLET else "buddy"))
    for i, nombre in enumerate(COWORK):
        if nombre.strip():
            car.agregar(f"placa_cowork{i}", placa_escritorio(nombre.strip()))
    for i, nombre in enumerate(CONTENT_ROOM):
        if nombre.strip():
            car.agregar(f"placa_content{i}", placa_escritorio(nombre.strip()))
    car.agregar("puerta_content", cartel_puerta("CONTENT ROOM"))
    car.agregar("puerta_embarque", cartel_puerta("SALA DE EMBARQUE"))
    car.agregar("puerta_founders", cartel_puerta("FOUNDERS"))
    car.agregar("puerta_experiencia", cartel_puerta("EXPERIENCIA DEL CLIENTE", ancho=4))
    car.agregar("puerta_ardiflet", cartel_puerta_ardiflet())
    car.agregar("cartel_content", cartel_grande([("CONTENT ROOM", 14), ("estudio de edición", 10)]))
    car.agregar("cartel_embarque", cartel_grande([("SALA DE EMBARQUE", 15), ("reuniones y dailys", 10)], ancho=4))
    car.agregar("cartel_foco", cartel_grande([("MODO FOCO", 16), ("silencio, por favor", 10)]))
    car.agregar("cartel_founders", cartel_grande([("FOUNDERS", 16), ("Pablo & Sofi", 10)]))
    car.agregar("cartel_experiencia", cartel_grande([("EXPERIENCIA", 15), ("DEL CLIENTE", 15)], ancho=4))
    car.agregar("cartel_ardiflet", cartel_ardiflet())
    for i, p in enumerate(PANTALLAS):
        car.agregar(f"pantalla{i}", pantalla_link(p["texto"], "tiendabuddy" in p["url"]))
    car.guardar()

    logo_recepcion().save(os.path.join(TILESETS, "buddy_logo.png"))
    cuadro_bolsos().save(os.path.join(TILESETS, "buddy_cuadro.png"))
    return amb, car


# ════════════════════════════════════════════════════════════════════
#  2) Armar el mapa
# ════════════════════════════════════════════════════════════════════

KIT = ["WA_Special_Zones", "WA_Decoration", "WA_Miscellaneous", "WA_Other_Furniture",
       "WA_Seats", "WA_Tables", "WA_Exterior"]
CREDITO_WA = "Credits: WorkAdventure (https://WorkAdventu.re)\nLicense: CC-BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)"


def armar_mapa(amb, car):
    # Tilesets embebidos (WorkAdventure no acepta tilesets externos)
    tilesets, primer = [], {}
    gid = 1
    fuentes = [(n, f"tilesets/{n}.png", CREDITO_WA) for n in KIT] + [
        ("buddy_ambiente", "tilesets/buddy_ambiente.png", "Buddy"),
        ("buddy_carteles", "tilesets/buddy_carteles.png", "Buddy / Ardiflet"),
        ("buddy_logo", "tilesets/buddy_logo.png", "Buddy"),
        ("buddy_cuadro", "tilesets/buddy_cuadro.png", "Buddy"),
    ]
    for nombre, ruta, credito in fuentes:
        iw, ih = Image.open(os.path.join(RAIZ, ruta)).size
        ts = {"columns": iw // T, "firstgid": gid, "image": ruta, "imageheight": ih, "imagewidth": iw,
              "margin": 0, "name": nombre, "spacing": 0, "tilecount": (iw // T) * (ih // T),
              "tileheight": T, "tilewidth": T,
              "properties": [{"name": "tilesetCopyright", "type": "string", "value": credito}]}
        if nombre == "WA_Special_Zones":
            ts["tiles"] = [{"id": 2, "properties": [{"name": "collides", "type": "bool", "value": True}]}]
        tilesets.append(ts)
        primer[nombre] = gid
        gid += ts["tilecount"]

    capas = ["start", "collisions", "floor1", "floor2", "walls1", "walls2",
             "furniture1", "furniture2", "furniture3", "above1", "above2"]
    L = {n: [0] * (W * H) for n in capas}
    choques = set()  # en coordenadas del mapa completo (con el jardín)

    def put_mapa(capa, x, y, ts, local):
        if 0 <= x < W and 0 <= y < H and local is not None:
            L[capa][y * W + x] = primer[ts] + local

    # De acá en adelante todo va en coordenadas del edificio: se corre JARDIN filas para abajo.
    def put(capa, x, y, ts, local):
        put_mapa(capa, x, y + JARDIN, ts, local)

    def poner(capa, x, y, ts, ids):
        for r, fila in enumerate(ids):
            for k, local in enumerate(fila):
                put(capa, x + k, y + r, ts, local)

    def choca(x0, y0, x1=None, y1=None):
        x1 = x0 if x1 is None else x1
        y1 = y0 if y1 is None else y1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                choques.add((x, y + JARDIN))

    A = lambda nombre: amb.ids[nombre]
    C = lambda nombre: car.ids[nombre]
    DEC, MISC, SEATS, EXT = "WA_Decoration", "WA_Miscellaneous", "WA_Seats", "WA_Exterior"

    def llenar(capa, x0, y0, x1, y1, ts, local):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(capa, x, y, ts, local)

    def arbol(x, y, col, capa_tronco="furniture3"):
        base = [[col, col + 1, col + 2], [col + 25, col + 26, col + 27], [col + 50, col + 51, col + 52]]
        poner("above2", x, y, EXT, base[:2])
        poner(capa_tronco, x, y + 2, EXT, [base[2]])
        choca(x + 1, y + 2)

    # ── Jardín de arriba (queda debajo de la barra de botones de WorkAdventure) ──
    for y in range(-JARDIN, 0):
        for x in range(W):
            put(capa="floor1", x=x, y=y, ts=EXT, local=628)
    for tx, col in ((1, 0), (13, 3), (27, 9), (37, 12)):
        arbol(tx, -JARDIN, col)
    for bx in (6, 18, 23, 33):
        poner("furniture1", bx, -1, EXT, [[450, 451]])
    poner("furniture1", 9, -2, EXT, [[533, 534], [558, 559]])
    poner("furniture1", 30, -2, EXT, [[531, 532], [556, 557]])
    for x in (4, 11, 21, 25, 35, 41):
        put("furniture1", x, -2, EXT, 506)
    for x in range(W):
        choca(x, -1)  # que nadie salga al jardín

    # ── Pisos del edificio ──
    for y in range(ALTO_EDIFICIO):
        for x in range(W):
            put("floor1", x, y, "buddy_ambiente", A("madera1" if (x * 7 + y * 3) % 5 == 0 else "madera0")[0][0])
    llenar("floor1", 10, 18, 27, 20, "buddy_ambiente", A("crema")[0][0])     # recepción / showroom
    llenar("floor1", 17, 21, 18, 21, "buddy_ambiente", A("crema")[0][0])
    llenar("floor1", 34, 3, 40, 7, "buddy_ambiente", A("piso_ard")[0][0])    # Ardiflet
    llenar("floor1", 23, 12, 29, 14, EXT, 628)                               # patio interno: pasto

    def alfombra_en(x0, y0, x1, y1):
        ids = A("alfombra")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                r = 0 if y == y0 else (2 if y == y1 else 1)
                k = 0 if x == x0 else (2 if x == x1 else 1)
                put("floor2", x, y, "buddy_ambiente", ids[r][k])

    alfombra_en(11, 3, 18, 7)     # Sala de Embarque
    alfombra_en(21, 6, 24, 7)     # Founders
    alfombra_en(28, 6, 31, 7)     # Experiencia del cliente
    alfombra_en(29, 18, 39, 20)   # sala de estar

    # ── Paredes ──
    puertas_arriba = (4, 5, 14, 15, 22, 23, 29, 30, 36, 37)
    tapas = set()
    tapas |= {(x, 0) for x in range(W)}
    tapas |= {(0, y) for y in range(ALTO_EDIFICIO)} | {(W - 1, y) for y in range(ALTO_EDIFICIO)}
    tapas |= {(x, ALTO_EDIFICIO - 1) for x in range(W) if x not in (17, 18)}   # entrada
    for xv in (10, 19, 26, 33):
        tapas |= {(xv, y) for y in range(9)}
    tapas |= {(x, 8) for x in range(W) if x not in puertas_arriba}
    tapas |= {(x, 15) for x in range(0, 10) if x not in (6, 7)}                # Modo foco (puerta al pasillo)
    tapas |= {(9, y) for y in range(15, ALTO_EDIFICIO)}
    tapas |= {(x, 15) for x in range(12, W - 1) if x not in (33, 34)}          # pared del logo y de la sala de estar

    caras = {}
    salas = [(1, 9, "salvia"), (11, 18, "salvia"), (20, 25, "salvia"), (27, 32, "salvia"), (34, 40, "ard")]
    for x0, x1, paleta in salas:
        for x in range(x0, x1 + 1):
            caras[(x, 1)], caras[(x, 2)] = ("alta", paleta), ("baja", paleta)
    for x in range(1, W - 1):
        if x not in puertas_arriba:
            caras[(x, 9)] = ("unica", "salvia")
    for x in [x for x in range(1, 9) if x not in (6, 7)] + [x for x in range(12, W - 1) if x not in (33, 34)]:
        caras[(x, 16)], caras[(x, 17)] = ("alta", "salvia"), ("baja", "salvia")

    def es_tapa(x, y):
        return (x, y) in tapas

    def es_hueco(x, y):
        return 0 < x < W - 1 and (x, y) not in tapas and (x, y) not in caras

    for (x, y) in tapas:
        m = (es_tapa(x, y - 1) * 1) | (es_tapa(x + 1, y) * 2) | (es_tapa(x, y + 1) * 4) | (es_tapa(x - 1, y) * 8)
        put("walls1", x, y, "buddy_ambiente", A(f"tapa{m}")[0][0])
        choca(x, y)
    for (x, y), (tipo, paleta) in caras.items():
        ji, jd = int(es_hueco(x - 1, y)), int(es_hueco(x + 1, y))
        put("walls1", x, y, "buddy_ambiente", A(f"cara_{paleta}_{tipo}_{ji}{jd}")[0][0])
        choca(x, y)

    poner("walls1", 17, ALTO_EDIFICIO - 1, "buddy_ambiente", A("puerta"))
    choca(17, ALTO_EDIFICIO - 1, 18, ALTO_EDIFICIO - 1)

    # ── Muebles ──
    def silla_en(x, y, mira, color="verde"):
        put("furniture2", x, y, "buddy_ambiente", A(f"silla_{color}_{mira}")[0][0])
        if mira == "arriba":
            # el respaldo va por encima del avatar: parado en la silla, parece sentado
            put("above1", x, y, "buddy_ambiente", A(f"silla_{color}_respaldo")[0][0])

    def escritorio(x, y, ancho, monitores=(), placas=(), sillas=(), cosas=(), color_silla="verde"):
        """Escritorio de madera clara. y = fila de la tapa; el frente queda en y+1."""
        for i in range(ancho):
            pos = "i" if i == 0 else ("d" if i == ancho - 1 else "m")
            put("furniture1", x + i, y, "buddy_ambiente", A(f"esc_sup_{pos}")[0][0])
            put("furniture1", x + i, y + 1, "buddy_ambiente", A(f"esc_fre_{pos}")[0][0])
        choca(x, y, x + ancho - 1, y + 1)
        for mx, local in monitores:
            put("furniture3", mx, y, MISC, local)
        for cx, ts, local in cosas:
            put("furniture3", cx, y, ts, local)
        for px, clave in placas:
            if clave in car.ids:
                poner("furniture3", px, y + 1, "buddy_carteles", C(clave))
        for sx in sillas:
            silla_en(sx, y + 2, "arriba", color_silla)

    def mesita(x, y, taza=None):
        put("furniture1", x, y, "WA_Tables", 143)
        if taza is not None:
            put("furniture3", x, y, MISC, taza)
        choca(x, y)
        silla_en(x - 1, y, "der")
        silla_en(x + 1, y, "izq")

    def planta(x, y, ids):
        poner("furniture2", x, y, DEC, ids)
        choca(x, y + len(ids) - 1)

    PLANTA_A = [[75], [87]]   # planta de hojas largas
    PLANTA_B = [[78], [90]]   # arbolito redondo
    PLANTA_C = [[79], [91]]   # planta de hojas anchas
    TELE = [[40, 41, 42], [50, 51, 52]]
    MACETA, FLORES, TAZA, TAZA_CHICA, LAPTOP = 93, 92, 58, 59, 23
    SILLON_CREMA = [[0, 1, 2], [13, 14, 15]]

    ocupados = {LUGARES_PANTALLA[p["lugar"]] for p in PANTALLAS}

    def tele_decorativa(lugar):
        if LUGARES_PANTALLA[lugar] not in ocupados:
            x, y = LUGARES_PANTALLA[lugar]
            poner("walls2", x, y, MISC, TELE)

    # ═══ Fila de arriba ═══

    # Content room (x1-9): 3 puestos de edición, fondo verde, cámara y luces
    poner("walls2", 1, 1, "buddy_carteles", C("cartel_content"))
    tele_decorativa("content")
    escritorio(1, 3, 6, monitores=[(1, 0), (3, 1), (5, 0)],
               placas=[(1 + 2 * i, f"placa_content{i}") for i in range(3)], sillas=[1, 3, 5],
               cosas=[(2, MISC, TAZA), (4, DEC, MACETA), (6, MISC, TAZA_CHICA)])
    poner("furniture2", 7, 1, "buddy_ambiente", A("croma"))
    choca(7, 3, 9, 3)
    poner("furniture2", 8, 4, SEATS, [[59], [72]])
    poner("furniture2", 8, 6, "buddy_ambiente", A("camara"))
    choca(8, 7)
    poner("furniture2", 7, 4, "buddy_ambiente", A("luz"))
    choca(7, 5)
    poner("furniture2", 9, 4, "buddy_ambiente", A("luz"))
    choca(9, 5)
    planta(1, 6, PLANTA_A)

    # Sala de Embarque (x11-18): mesa larga, 6 sillas y alfombra
    tele_decorativa("reuniones")
    poner("walls2", 15, 1, "buddy_carteles", C("cartel_embarque"))
    escritorio(12, 4, 6, cosas=[(12, MISC, TAZA), (14, MISC, LAPTOP), (17, MISC, TAZA_CHICA)])
    for sx in (13, 16):
        silla_en(sx, 3, "abajo")
        silla_en(sx, 6, "arriba")
    silla_en(11, 4, "der")
    silla_en(18, 4, "izq")
    planta(11, 6, PLANTA_C)
    planta(18, 6, PLANTA_C)

    # Founders (x20-25): Pablo y Sofi, con mesita para charlar
    poner("walls2", 21, 1, "buddy_carteles", C("cartel_founders"))
    escritorio(20, 3, 2, monitores=[(20, 1)], placas=[(20, "placa_pablo")], sillas=[20], cosas=[(21, DEC, MACETA)])
    escritorio(24, 3, 2, monitores=[(24, 0)], placas=[(24, "placa_sofi")], sillas=[24], cosas=[(25, DEC, FLORES)])
    mesita(22, 7, TAZA)
    planta(20, 6, PLANTA_C)
    planta(25, 6, PLANTA_A)

    # Experiencia del cliente (x27-32): Vero, mostrador de atención y mesita para videollamadas
    poner("walls2", 28, 1, "buddy_carteles", C("cartel_experiencia"))
    escritorio(27, 3, 2, monitores=[(27, 1)], placas=[(27, "placa_vero")], sillas=[27], cosas=[(28, MISC, TAZA_CHICA)])
    escritorio(30, 3, 3, monitores=[(31, 0)], sillas=[31], cosas=[(30, MISC, LAPTOP), (32, DEC, FLORES)])
    mesita(29, 7, TAZA)
    planta(27, 6, PLANTA_B)
    planta(32, 6, PLANTA_C)

    # Ardiflet (x34-40): paredes petróleo con zócalo naranja, cartel con la ardilla, cajas y pizarra
    poner("walls2", 35, 1, "buddy_carteles", C("cartel_ardiflet"))
    escritorio(34, 3, 2, monitores=[(34, 1)], placas=[(34, "placa_ivan")], sillas=[34],
               cosas=[(35, MISC, TAZA)], color_silla="ard")
    escritorio(39, 3, 2, monitores=[(39, 0)], placas=[(39, "placa_camilo")], sillas=[39],
               cosas=[(40, DEC, MACETA)], color_silla="ard")
    poner("furniture2", 38, 6, "buddy_ambiente", A("cajas"))
    choca(38, 7, 39, 7)
    poner("furniture2", 40, 7, "buddy_ambiente", A("caja_chica"))
    choca(40, 7)

    # Carteles de sala al lado de cada puerta (pasillo)
    poner("walls2", 1, 9, "buddy_carteles", C("puerta_content"))
    poner("walls2", 11, 9, "buddy_carteles", C("puerta_embarque"))
    poner("walls2", 19, 9, "buddy_carteles", C("puerta_founders"))
    poner("walls2", 25, 9, "buddy_carteles", C("puerta_experiencia"))
    poner("walls2", 33, 9, "buddy_carteles", C("puerta_ardiflet"))
    put("walls2", 8, 9, MISC, 78)                      # reloj
    poner("walls2", 39, 9, DEC, [[24, 25]])            # mapa del mundo

    # ═══ Banda del medio ═══

    # Cowork (x1-19): 4 mesas de 2 puestos, todas en una fila
    puestos = []
    for mesa_x in (1, 6, 11, 16):
        escritorio(mesa_x, 11, 4, monitores=[(mesa_x, 1), (mesa_x + 2, 0)],
                   sillas=[mesa_x, mesa_x + 2],
                   cosas=[(mesa_x + 1, MISC, TAZA), (mesa_x + 3, DEC, MACETA if mesa_x % 2 else FLORES)])
        puestos += [mesa_x, mesa_x + 2]
    for i, px in enumerate(puestos):
        clave = f"placa_cowork{i}"
        if clave in car.ids:
            poner("furniture3", px, 12, "buddy_carteles", C(clave))

    # Patio interno (x22-30): canteros, pasto, fuente, arbolitos y un banco
    for x in range(22, 31):
        if x != 26:
            put("furniture1", x, 11, "buddy_ambiente", A("cantero")[0][0])
            choca(x, 11)
    for y in (13, 14):
        for x in (22, 30):
            put("furniture1", x, y, "buddy_ambiente", A("cantero")[0][0])
            choca(x, y)
    poner("furniture2", 25, 13, "buddy_ambiente", A("fuente"))
    choca(25, 13, 26, 14)
    planta(23, 13, PLANTA_B)
    planta(29, 13, PLANTA_B)
    poner("furniture2", 27, 14, SEATS, [[143, 144]])  # banco de madera
    put("furniture2", 24, 14, DEC, FLORES)
    for (x, y) in ((24, 12), (28, 12)):
        put("furniture1", x, y, EXT, 506)

    # Café (x32-40): barra con banquetas, cafetera y una mesita
    escritorio(32, 11, 5, cosas=[(33, MISC, 57), (35, MISC, TAZA), (36, MISC, TAZA_CHICA)])
    for sx in (32, 34, 36):
        put("furniture2", sx, 13, SEATS, 151)
    poner("furniture2", 38, 11, MISC, [[46], [56]])    # cafetera
    choca(38, 12)
    planta(40, 11, PLANTA_B)
    mesita(39, 14, TAZA)

    # ═══ Fila de abajo ═══

    # Modo foco (x1-8): sala cerrada con puerta al pasillo, cartel y lámpara
    poner("walls2", 2, 16, "buddy_carteles", C("cartel_foco"))
    escritorio(1, 18, 2, monitores=[(1, 1)], sillas=[1], cosas=[(2, DEC, MACETA)])
    escritorio(4, 18, 2, monitores=[(4, 0)], sillas=[4], cosas=[(5, MISC, TAZA)])
    poner("furniture2", 8, 18, "buddy_ambiente", A("lampara"))
    choca(8, 19)

    # Recepción / showroom (x10-27): estante | logo | tienda | cuadro, frente a la entrada
    poner("walls2", 12, 16, "buddy_ambiente", A("estante"))
    poner("walls2", 15, 16, "buddy_logo", [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11]])
    poner("walls2", 24, 16, "buddy_cuadro", [[0, 1, 2], [3, 4, 5]])
    put("walls2", 27, 16, DEC, 3)
    poner("furniture2", 12, 19, "buddy_ambiente", A("exhibidor"))
    choca(12, 19, 13, 19)
    planta(15, 19, PLANTA_A)
    planta(20, 19, PLANTA_A)
    planta(26, 19, PLANTA_C)
    ex, ey = ENTRADA
    for x in (ex, ex + 1):
        put("start", x, ey, "WA_Special_Zones", 1)

    # Sala de estar (x28-40), pegada a la recepción
    poner("walls2", 29, 16, DEC, [[6, 7], [18, 19]])
    poner("walls2", 37, 16, DEC, [[0, 1]])
    poner("furniture2", 31, 18, SEATS, SILLON_CREMA)
    mesita(32, 20)
    poner("furniture2", 36, 18, "buddy_ambiente", A("lampara"))
    choca(36, 19)
    planta(39, 18, PLANTA_A)
    planta(28, 19, PLANTA_C)

    # Pantallas con link
    for i, p in enumerate(PANTALLAS):
        x, y = LUGARES_PANTALLA[p["lugar"]]
        poner("walls2", x, y, "buddy_carteles", C(f"pantalla{i}"))

    # ── Colisiones ──
    for (x, y) in choques:
        put_mapa("collisions", x, y, "WA_Special_Zones", 2)

    # ── Zonas (áreas) ──
    objetos = []

    def area(nombre, x, y, w, h, props):
        objetos.append({"height": h * T, "id": len(objetos) + 1, "name": nombre,
                        "properties": [{"name": n, "type": t, "value": v} for n, t, v in props],
                        "rotation": 0, "type": "area", "visible": True,
                        "width": w * T, "x": x * T, "y": (y + JARDIN) * T})

    area("salaDeEmbarque", 11, 3, 8, 5, [
        ("focusable", "bool", True),
        ("jitsiRoom", "string", "DailyBuddy"),
        ("meetingRoomLabel", "string", "Sala de Embarque"),
        ("zoom_margin", "float", 1.0),
    ])
    area("modoFoco", 1, 16, 8, 5, [("silent", "bool", True)])
    for i, p in enumerate(PANTALLAS):
        x, y = LUGARES_PANTALLA[p["lugar"]]
        clave = "openTab" if p["abrir"] == "pestaña" else "openWebsite"
        area(f"pantalla_{p['lugar']}", x, y + 2, 3, 1, [
            (clave, "string", p["url"]),
            ("openWebsiteTrigger", "string", "onaction"),
            ("openWebsiteTriggerMessage", "string", f"Apretá ESPACIO para abrir {p['texto']}"),
        ])

    # ── Archivo .tmj ──
    ids = iter(range(1, 100))

    def capa(nombre):
        # start y collisions tienen que quedar "visibles" para que WorkAdventure las tenga en cuenta,
        # pero con opacidad 0 para que no se vean los tiles de START/BLOCK.
        opacidad = 0 if nombre in ("start", "collisions") else 1
        return {"data": L[nombre], "height": H, "id": next(ids), "name": nombre, "opacity": opacidad,
                "type": "tilelayer", "visible": True, "width": W, "x": 0, "y": 0}

    def grupo(nombre, hijos):
        return {"id": next(ids), "layers": hijos, "name": nombre, "opacity": 1,
                "type": "group", "visible": True, "x": 0, "y": 0}

    layers = [
        capa("start"),
        capa("collisions"),
        grupo("floor", [capa("floor1"), capa("floor2")]),
        grupo("walls", [capa("walls1"), capa("walls2")]),
        grupo("furniture", [capa("furniture1"), capa("furniture2"), capa("furniture3")]),
        {"draworder": "topdown", "id": next(ids), "name": "floorLayer", "objects": objetos,
         "opacity": 1, "type": "objectgroup", "visible": True, "x": 0, "y": 0},
        grupo("above", [capa("above1"), capa("above2")]),
    ]
    mapa = {
        "compressionlevel": -1, "height": H, "infinite": False, "layers": layers,
        "nextlayerid": next(ids), "nextobjectid": len(objetos) + 1, "orientation": "orthogonal",
        "properties": [
            {"name": "mapCopyright", "type": "string", "value": MAPA_COPYRIGHT},
            {"name": "mapDescription", "type": "string", "value": MAPA_DESCRIPCION},
            {"name": "mapImage", "type": "string", "value": "oficina.png"},
            {"name": "mapName", "type": "string", "value": MAPA_NOMBRE},
            {"name": "script", "type": "string", "value": "src/main.ts"},
        ],
        "renderorder": "right-down", "tiledversion": "1.11.2", "tileheight": T, "tilesets": tilesets,
        "tilewidth": T, "type": "map", "version": "1.10", "width": W,
    }
    with open(os.path.join(RAIZ, "oficina.tmj"), "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=1)
    return mapa, choques, objetos


# ════════════════════════════════════════════════════════════════════
#  3) Vista previa
# ════════════════════════════════════════════════════════════════════

def renderizar(mapa):
    hojas = []
    for ts in mapa["tilesets"]:
        hojas.append((ts["firstgid"], ts["columns"], Image.open(os.path.join(RAIZ, ts["image"])).convert("RGBA")))
    hojas.sort(key=lambda h: h[0])
    cache = {}

    def tile(g):
        if g not in cache:
            fg, cols, img = [h for h in hojas if h[0] <= g][-1]
            i = g - fg
            cache[g] = img.crop(((i % cols) * T, (i // cols) * T, (i % cols + 1) * T, (i // cols + 1) * T))
        return cache[g]

    out = Image.new("RGBA", (W * T, H * T), (0, 0, 0, 255))

    def recorrer(capas):
        for l in capas:
            if l["type"] == "group":
                yield from recorrer(l["layers"])
            elif l["type"] == "tilelayer" and l["name"] not in ("start", "collisions"):
                yield l

    for l in recorrer(mapa["layers"]):
        for idx, g in enumerate(l["data"]):
            if g:
                out.alpha_composite(tile(g), ((idx % W) * T, (idx // W) * T))
    return out


# Un lugar de cada zona, en coordenadas del edificio, para revisar que se pueda llegar caminando.
LUGARES_A_REVISAR = {
    "Content room": (2, 5), "Sala de Embarque": (14, 7), "Founders": (22, 5),
    "Experiencia del cliente": (29, 5), "Ardiflet": (36, 5), "pasillo": (20, 10),
    "cowork": (3, 14), "patio interno": (25, 12), "café": (34, 14),
    "Modo foco": (3, 20), "recepción": (17, 19), "sala de estar": (35, 20),
}


def verificar_accesos(choques):
    """Camina el mapa desde la entrada y avisa si alguna zona quedó tapada por un mueble."""
    ex, ey = ENTRADA
    inicio = (ex, ey + JARDIN)
    vistos, cola = {inicio}, [inicio]
    while cola:
        x, y = cola.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in vistos and (nx, ny) not in choques:
                vistos.add((nx, ny))
                cola.append((nx, ny))
    problemas = [n for n, (x, y) in LUGARES_A_REVISAR.items() if (x, y + JARDIN) not in vistos]
    if problemas:
        print("⚠️  No se puede llegar caminando a: " + ", ".join(problemas))
    else:
        print("Accesos OK: se llega caminando a todas las zonas.")
    return problemas


def main():
    amb, car = generar_tilesets()
    mapa, choques, objetos = armar_mapa(amb, car)
    verificar_accesos(choques)
    plano = renderizar(mapa)

    miniatura = Image.new("RGBA", (512, 512), VERDE)
    esc = 512 / plano.width
    chica = plano.resize((512, round(plano.height * esc)), Image.LANCZOS)
    miniatura.alpha_composite(chica, (0, (512 - chica.height) // 2))
    miniatura.convert("RGB").save(os.path.join(RAIZ, "oficina.png"))

    # Opcional: python3 herramientas/construir.py --debug ruta.png
    # guarda el plano grande con colisiones (rojo) y zonas (colores) marcadas.
    if "--debug" in sys.argv:
        ruta = sys.argv[sys.argv.index("--debug") + 1]
        plano.save(ruta.replace(".png", "_limpio.png"))
        dbg = plano.copy()
        capa = Image.new("RGBA", dbg.size, NADA)
        d = ImageDraw.Draw(capa)
        for (x, y) in choques:
            d.rectangle([x * T, y * T, x * T + T - 1, y * T + T - 1], fill=(255, 0, 0, 70))
        colores = {"salaDeEmbarque": (60, 120, 255, 255), "modoFoco": (180, 60, 255, 255)}
        for o in objetos:
            col = colores.get(o["name"], (255, 150, 0, 255))
            d.rectangle([o["x"], o["y"], o["x"] + o["width"] - 1, o["y"] + o["height"] - 1], outline=col, width=3)
        ex, ey = ENTRADA
        for x in (ex, ex + 1):
            d.rectangle([x * T + 8, (ey + JARDIN) * T + 8, x * T + 23, (ey + JARDIN) * T + 23], fill=(0, 255, 0, 200))
        dbg.alpha_composite(capa)
        dbg.save(ruta)

    print("Listo: oficina.tmj, oficina.png y tilesets/buddy_*.png")


if __name__ == "__main__":
    main()
