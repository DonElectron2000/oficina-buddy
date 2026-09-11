#!/usr/bin/env python3
"""
Oficina Buddy — generador del mapa de WorkAdventure.

Este script arma todo lo propio de la oficina:
  - tilesets/buddy_ambiente.png  paredes, pisos, alfombras y objetos dibujados a mano
  - tilesets/buddy_carteles.png  nombres de los escritorios, carteles y pantallas
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
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# ════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════

# Nombre que aparece en el cartel de cada escritorio.
# Cambiá solo lo que está a la derecha de los dos puntos.
NOMBRES = {
    "lucho": "Lucho",
    "ivan": "Ivan",
    "mateo": "Mateo",
    "pablo": "Pablo",
    "sofi": "Sofi",
    "vero": "Vero",
}

# Pantallas de pared que abren un link cuando te parás adelante y apretás ESPACIO.
#   lugar: "recepcion", "reuniones" o "estudio" (los huecos de pared preparados)
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
W, H = 32, 25  # tamaño del mapa en tiles

# Huecos de pared donde puede ir una pantalla (esquina superior izquierda, 3x2 tiles).
LUGARES_PANTALLA = {"recepcion": (9, 18), "reuniones": (10, 1), "estudio": (5, 1)}


def c(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def tono(col, f):
    return tuple(max(0, min(255, int(v * f))) for v in col[:3]) + (col[3],)


VERDE = c("#173A37")
SALVIA = c("#5F7E7A")
MEDIO = c("#485955")
CREMA = c("#F3F0E3")
BEIGE = c("#D2C2B5")
MADERA = c("#7F6D5F")
MADERA_OSC = c("#564C43")
SOMBRA = (0, 0, 0, 55)
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
        self.tamano = hoja.size
        return self


# ─── Dibujos: paredes y pisos ───

def tapa_pared(n, e, s, o):
    im, d = lienzo(1, 1, VERDE)
    rnd = random.Random(7)
    for _ in range(18):
        d.point((rnd.randrange(T), rnd.randrange(T)), tono(VERDE, 1.15))
    borde = tono(VERDE, 0.55)
    if not n:
        d.line([0, 2, T - 1, 2], fill=MEDIO)
        d.rectangle([0, 0, T - 1, 1], fill=borde)
    if not s:
        d.rectangle([0, T - 2, T - 1, T - 1], fill=borde)
    if not o:
        d.rectangle([0, 0, 1, T - 1], fill=borde)
    if not e:
        d.rectangle([T - 2, 0, T - 1, T - 1], fill=borde)
    return im


def cara_pared(base, sombra, zocalo):
    im, d = lienzo(1, 1, base)
    rnd = random.Random(3)
    for _ in range(14):
        d.point((rnd.randrange(T), rnd.randrange(T)), tono(base, 1.07))
    if sombra:
        d.rectangle([0, 0, T - 1, 2], fill=tono(base, 0.7))
        d.line([0, 3, T - 1, 3], fill=tono(base, 0.86))
    if zocalo:
        d.line([0, 8, T - 1, 8], fill=tono(base, 1.18))
        d.line([0, 9, T - 1, 9], fill=tono(base, 0.8))
        for x in (0, 16):
            d.line([x, 10, x, 25], fill=tono(base, 0.88))
        d.rectangle([0, 26, T - 1, T - 1], fill=MADERA_OSC)
        d.line([0, 26, T - 1, 26], fill=tono(MADERA_OSC, 1.35))
    return im


def piso_madera(variante):
    im, d = lienzo(1, 1)
    tonos = [c("#8B796A"), c("#85725F"), c("#897664"), c("#827060")]
    juntas = [[21], [7], [27], [14]] if variante == 0 else [[3], [24], [12], [30]]
    for i in range(4):
        y0, col = i * 8, tonos[i]
        d.rectangle([0, y0, T - 1, y0 + 7], fill=col)
        rnd = random.Random(100 + variante * 10 + i)
        for _ in range(7):
            x, y = rnd.randrange(T), y0 + rnd.randrange(2, 7)
            d.line([x, y, min(T - 1, x + rnd.randrange(3, 8)), y], fill=tono(col, 0.95))
        d.line([0, y0, T - 1, y0], fill=tono(col, 1.05))
        d.line([0, y0 + 7, T - 1, y0 + 7], fill=tono(col, 0.86))
        for jx in juntas[i]:
            d.line([jx, y0 + 1, jx, y0 + 6], fill=tono(col, 0.86))
    return im


def piso_crema():
    im, d = lienzo(1, 1, CREMA)
    alt = c("#EDE7D7")
    d.rectangle([16, 0, 31, 15], fill=alt)
    d.rectangle([0, 16, 15, 31], fill=alt)
    junta = c("#DDD2C4")
    for v in (0, 16):
        d.line([0, v, T - 1, v], fill=junta)
        d.line([v, 0, v, T - 1], fill=junta)
    return im


def piso_deck():
    im, d = lienzo(1, 1)
    tonos = [c("#5B5046"), c("#564C43"), c("#5F544A"), c("#52483F")]
    for i in range(4):
        y0, col = i * 8, tonos[i]
        d.rectangle([0, y0, T - 1, y0 + 7], fill=col)
        d.line([0, y0, T - 1, y0], fill=tono(col, 1.12))
        d.line([0, y0 + 7, T - 1, y0 + 7], fill=c("#3A322C"))
        d.line([0, y0, 0, y0 + 6], fill=c("#3A322C"))
        for x in (3, 28):
            d.point((x, y0 + 3), fill=c("#3A322C"))
    return im


def alfombra():
    """Alfombra beige de 3x3 tiles: esquinas, bordes y centro repetible."""
    im, d = lienzo(3, 3)
    d.rectangle([3, 1, 92, 94], fill=BEIGE)
    d.rectangle([3, 1, 92, 94], outline=tono(BEIGE, 0.86), width=3)
    d.rectangle([8, 6, 87, 89], outline=CREMA)
    for ty in range(3):
        for tx in range(3):
            cx, cy = tx * T + 16, ty * T + 16
            d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], fill=tono(BEIGE, 0.9))
            d.point((cx, cy), fill=CREMA)
    for y in range(3, 94, 3):
        d.line([0, y, 2, y], fill=CREMA)
        d.line([93, y, 95, y], fill=CREMA)
    return im


# ─── Dibujos: objetos ───

def felpudo():
    im, d = lienzo(2, 1)
    d.rounded_rectangle([3, 5, 60, 27], radius=3, fill=VERDE)
    d.rounded_rectangle([6, 8, 57, 24], radius=2, outline=MEDIO)
    texto_centrado(d, 31.5, 16, "HOLA", CREMA, 12, 44)
    return im


def puerta_entrada():
    im, d = lienzo(2, 1, tono(VERDE, 0.8))
    d.rectangle([0, 6, 63, 25], fill=MADERA_OSC)
    d.rectangle([3, 9, 60, 22], fill=c("#BFD6D1"))
    d.line([31, 9, 32, 22], fill=MADERA_OSC, width=2)
    for x0 in (6, 38):
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


def bolso(d, x, y, w, h, cuerpo, asa, brillo, logo=None):
    arriba = y + int(h * 0.4)
    d.arc([x + w * 0.24, y, x + w * 0.76, y + (arriba - y) * 2], 180, 360, fill=asa, width=2)
    d.rounded_rectangle([x, arriba, x + w - 1, y + h - 1], radius=3, fill=cuerpo)
    d.line([x + 3, arriba + 2, x + w - 4, arriba + 2], fill=tono(cuerpo, 0.72))
    d.line([x + 2, arriba + 4, x + 2, y + h - 4], fill=brillo)
    d.line([x + 1, y + h - 5, x + w - 2, y + h - 5], fill=tono(cuerpo, 0.8))
    if logo:
        d.rectangle([x + w // 2 - 3, arriba + 6, x + w // 2 + 2, arriba + 7], fill=logo)


def estante_bolsos():
    im, d = lienzo(3, 2)
    d.rectangle([4, 60, 95, 63], fill=SOMBRA)
    d.rectangle([2, 4, 93, 61], fill=MADERA_OSC)
    d.rectangle([5, 8, 90, 31], fill=tono(MADERA, 0.78))
    d.rectangle([5, 36, 90, 57], fill=tono(MADERA, 0.78))
    for y in (4, 32, 58):
        d.rectangle([2, y, 93, y + 3], fill=MADERA)
        d.line([2, y, 93, y], fill=tono(MADERA, 1.2))
    rosa, negro, verde = c("#E7B2A6"), c("#262626"), VERDE
    fila1 = [(rosa, c("#1E1E1E"), c("#F7D9D0"), c("#1E1E1E")), (negro, c("#111111"), c("#4B4B4B"), c("#3A3A3A")),
             (verde, c("#0E2624"), c("#2F5A55"), CREMA)]
    fila2 = [(BEIGE, c("#564C43"), c("#E6DAD0"), VERDE), (SALVIA, c("#2E403D"), c("#86A29E"), CREMA),
             (rosa, c("#1E1E1E"), c("#F7D9D0"), c("#1E1E1E"))]
    for i, (cu, asa, br, lg) in enumerate(fila1):
        bolso(d, 7 + i * 28, 10, 25, 21, cu, asa, br, lg)
    for i, (cu, asa, br, lg) in enumerate(fila2):
        bolso(d, 7 + i * 28, 38, 25, 20, cu, asa, br, lg)
    return im


def brasero():
    im, d = lienzo(2, 2)
    brillo = Image.new("RGBA", im.size, NADA)
    ImageDraw.Draw(brillo).ellipse([0, 20, 63, 63], fill=(255, 150, 60, 50))
    im.alpha_composite(brillo)
    d.ellipse([10, 32, 53, 57], fill=c("#6E6A64"))
    for k in range(12):
        a = 2 * math.pi * k / 12
        sx, sy = 31.5 + 19 * math.cos(a), 44.5 + 10.5 * math.sin(a)
        d.ellipse([sx - 4, sy - 3, sx + 4, sy + 3], fill=c("#9A958D"), outline=c("#5E5A55"))
    d.ellipse([17, 37, 46, 52], fill=c("#2E2622"))
    d.line([21, 48, 42, 40], fill=c("#6B4A33"), width=3)
    d.line([21, 40, 42, 48], fill=c("#5A3D2A"), width=3)
    d.polygon([(22, 46), (25, 28), (29, 36), (32, 14), (35, 34), (38, 25), (42, 46)], fill=(242, 132, 40, 255))
    d.polygon([(25, 46), (29, 32), (32, 23), (35, 34), (39, 46)], fill=(255, 196, 70, 255))
    d.polygon([(29, 46), (32, 34), (35, 46)], fill=(255, 240, 170, 255))
    for px, py in ((24, 22), (40, 18), (30, 9)):
        d.point((px, py), fill=(255, 200, 90, 255))
    return im


# ─── Dibujos: carteles, pantallas, logo y cuadro ───

def placa_nombre(nombre):
    im, d = lienzo(2, 1)
    cuerda = c("#3B3B3B")
    d.line([32, 1, 14, 7], fill=cuerda)
    d.line([32, 1, 50, 7], fill=cuerda)
    d.point((32, 1), fill=MADERA_OSC)
    d.rounded_rectangle([6, 8, 61, 26], radius=3, fill=SOMBRA)
    d.rounded_rectangle([4, 6, 59, 24], radius=3, fill=CREMA, outline=VERDE)
    texto_centrado(d, 31.5, 15.5, nombre, VERDE, 14, 48)
    return im


def cartel(lineas, alto=1):
    im, d = lienzo(3, alto)
    if alto == 1:
        d.rounded_rectangle([5, 6, 94, 26], radius=2, fill=SOMBRA)
        d.rounded_rectangle([3, 4, 92, 24], radius=2, fill=VERDE)
        d.rounded_rectangle([5, 6, 90, 22], radius=1, outline=CREMA)
        texto_centrado(d, 47.5, 14, lineas[0], CREMA, 12, 78)
    else:
        d.rounded_rectangle([5, 8, 94, 54], radius=3, fill=SOMBRA)
        d.rounded_rectangle([3, 6, 92, 52], radius=3, fill=VERDE)
        d.rounded_rectangle([6, 9, 89, 49], radius=2, outline=CREMA)
        paso = 38 / (len(lineas) + 1)
        for i, linea in enumerate(lineas):
            texto_centrado(d, 47.5, 10 + paso * (i + 1), linea, CREMA, 13, 76)
    return im


def pantalla_link(texto, con_bolso):
    im, d = lienzo(3, 2)
    d.rectangle([6, 9, 94, 58], fill=SOMBRA)
    d.rounded_rectangle([3, 5, 92, 55], radius=3, fill=c("#1B1D1D"))
    d.rectangle([6, 8, 89, 51], fill=VERDE)
    if con_bolso:
        bolso(d, 37, 13, 21, 17, c("#E7B2A6"), c("#1E1E1E"), c("#F7D9D0"), c("#1E1E1E"))
        texto_centrado(d, 47.5, 41, texto, CREMA, 12, 78)
    else:
        texto_centrado(d, 47.5, 29, texto, CREMA, 15, 78)
    # flechita de "abre un link"
    d.line([81, 47, 86, 42], fill=CREMA)
    d.line([83, 42, 86, 42], fill=CREMA)
    d.line([86, 42, 86, 45], fill=CREMA)
    d.point((47, 53), fill=(120, 220, 140, 255))
    return im


def logo_recepcion():
    """192x64: pared verde oscuro con el logo en crema, igual a la pared de recepción."""
    im = Image.new("RGBA", (6 * T, 2 * T), NADA)
    alta, baja = cara_pared(VERDE, True, False), cara_pared(VERDE, False, True)
    for i in range(6):
        im.alpha_composite(alta, (i * T, 0))
        im.alpha_composite(baja, (i * T, T))
    src = Image.open(os.path.join(ORIGINALES, "BUDDY_isologo_bn.jpg")).convert("L")
    mascara = src.point(lambda v: 255 - v)
    mascara = mascara.crop(mascara.point(lambda v: 255 if v > 60 else 0).getbbox())
    escala = min(170 / mascara.width, 48 / mascara.height)
    tam = (round(mascara.width * escala), round(mascara.height * escala))
    mascara = mascara.resize(tam, Image.LANCZOS).point(lambda v: 0 if v < 60 else (255 if v > 190 else v))
    capa = Image.new("RGBA", tam, CREMA)
    capa.putalpha(mascara)
    im.alpha_composite(capa, ((im.width - tam[0]) // 2, 6 + (50 - tam[1]) // 2))
    return im


def cuadro_bolsos():
    """96x64: la foto de los bolsos pixelada, con marco de madera."""
    im, d = lienzo(3, 2)
    d.rectangle([6, 5, 95, 61], fill=SOMBRA)
    d.rectangle([3, 2, 92, 58], fill=MADERA_OSC)
    d.rectangle([5, 4, 90, 56], fill=MADERA)
    d.line([5, 4, 90, 4], fill=tono(MADERA, 1.25))
    d.rectangle([7, 6, 88, 54], fill=tono(MADERA_OSC, 0.8))
    foto = Image.open(os.path.join(ORIGINALES, "foto_bolsos.png")).convert("RGB")
    ancho, alto = 80, 46
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
    amb.agregar("salvia_alta", cara_pared(SALVIA, True, False))
    amb.agregar("salvia_baja", cara_pared(SALVIA, False, True))
    amb.agregar("salvia_unica", cara_pared(SALVIA, True, True))
    amb.agregar("verde_alta", cara_pared(VERDE, True, False))
    amb.agregar("verde_baja", cara_pared(VERDE, False, True))
    amb.agregar("verde_unica", cara_pared(VERDE, True, True))
    amb.agregar("madera0", piso_madera(0))
    amb.agregar("madera1", piso_madera(1))
    amb.agregar("crema", piso_crema())
    amb.agregar("deck", piso_deck())
    amb.agregar("felpudo", felpudo())
    amb.agregar("puerta", puerta_entrada())
    amb.agregar("camara", camara())
    amb.agregar("luz", luz_estudio())
    amb.agregar("alfombra", alfombra())
    amb.agregar("estante", estante_bolsos())
    amb.agregar("brasero", brasero())
    amb.guardar()

    car = Hoja("buddy_carteles.png", 8)
    for clave, nombre in NOMBRES.items():
        car.agregar(f"placa_{clave}", placa_nombre(nombre))
    car.agregar("cartel_estudio", cartel(["ESTUDIO"]))
    car.agregar("cartel_reuniones", cartel(["REUNIONES"]))
    car.agregar("cartel_foco", cartel(["MODO FOCO"]))
    car.agregar("cartel_atencion", cartel(["ATENCIÓN", "AL CLIENTE"], alto=2))
    for i, p in enumerate(PANTALLAS):
        car.agregar(f"pantalla{i}", pantalla_link(p["texto"], "tiendabuddy" in p["url"]))
    car.guardar()

    logo = logo_recepcion()
    logo.save(os.path.join(TILESETS, "buddy_logo.png"))
    cuadro = cuadro_bolsos()
    cuadro.save(os.path.join(TILESETS, "buddy_cuadro.png"))
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
        ("buddy_carteles", "tilesets/buddy_carteles.png", "Buddy"),
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
    choques = set()

    def put(capa, x, y, ts, local):
        if 0 <= x < W and 0 <= y < H and local is not None:
            L[capa][y * W + x] = primer[ts] + local

    def poner(capa, x, y, ts, ids):
        for r, fila in enumerate(ids):
            for k, local in enumerate(fila):
                put(capa, x + k, y + r, ts, local)

    def choca(x0, y0, x1=None, y1=None):
        x1 = x0 if x1 is None else x1
        y1 = y0 if y1 is None else y1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                choques.add((x, y))

    A = lambda nombre: amb.ids[nombre]
    C = lambda nombre: car.ids[nombre]

    # ── Piso ──
    for y in range(H):
        for x in range(W):
            if x >= 24:
                put("floor1", x, y, "WA_Exterior", 628)
            else:
                put("floor1", x, y, "buddy_ambiente", A("madera1" if (x * 7 + y * 3) % 5 == 0 else "madera0")[0][0])

    def llenar(capa, x0, y0, x1, y1, ts, local):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(capa, x, y, ts, local)

    llenar("floor1", 9, 3, 15, 8, "buddy_ambiente", A("crema")[0][0])     # sala de reuniones
    llenar("floor1", 6, 20, 22, 23, "buddy_ambiente", A("crema")[0][0])   # recepción
    llenar("floor1", 14, 24, 15, 24, "buddy_ambiente", A("crema")[0][0])
    llenar("floor1", 24, 11, 30, 21, "buddy_ambiente", A("deck")[0][0])   # terraza

    def alfombra_en(x0, y0, x1, y1):
        ids = A("alfombra")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                r = 0 if y == y0 else (2 if y == y1 else 1)
                k = 0 if x == x0 else (2 if x == x1 else 1)
                put("floor2", x, y, "buddy_ambiente", ids[r][k])

    alfombra_en(5, 3, 7, 5)       # set de grabación del estudio
    alfombra_en(17, 6, 20, 8)     # sala de foco
    alfombra_en(25, 12, 29, 16)   # patio

    # ── Paredes ──
    tapas = set()
    tapas |= {(x, 0) for x in range(24)}
    tapas |= {(0, y) for y in range(H)}
    tapas |= {(23, y) for y in range(H) if y not in (15, 16)}          # puerta al patio
    tapas |= {(x, 24) for x in range(24) if x not in (14, 15)}          # entrada
    tapas |= {(8, y) for y in range(10)} | {(16, y) for y in range(10)}
    tapas |= {(x, 9) for x in range(24) if x not in (3, 4, 11, 12, 19, 20)}
    tapas |= {(x, 17) for x in range(0, 6)} | {(x, 17) for x in range(9, 21)}

    caras = {}
    for x in list(range(1, 8)) + list(range(9, 16)) + list(range(17, 23)):
        caras[(x, 1)], caras[(x, 2)] = "salvia_alta", "salvia_baja"
    for x in range(1, 23):
        if x not in (3, 4, 11, 12, 19, 20):
            caras[(x, 10)] = "salvia_unica"
    for x in range(1, 6):
        caras[(x, 18)], caras[(x, 19)] = "salvia_alta", "salvia_baja"
    for x in range(9, 21):
        caras[(x, 18)], caras[(x, 19)] = "verde_alta", "verde_baja"

    def es_tapa(x, y):
        return (x, y) in tapas or not (0 <= x < 24 and 0 <= y < H)

    for (x, y) in tapas:
        m = (es_tapa(x, y - 1) * 1) | (es_tapa(x + 1, y) * 2) | (es_tapa(x, y + 1) * 4) | (es_tapa(x - 1, y) * 8)
        put("walls1", x, y, "buddy_ambiente", A(f"tapa{m}")[0][0])
        choca(x, y)
    for (x, y), clave in caras.items():
        put("walls1", x, y, "buddy_ambiente", A(clave)[0][0])
        choca(x, y)

    poner("walls1", 14, 24, "buddy_ambiente", A("puerta"))
    choca(14, 24, 15, 24)
    poner("floor2", 14, 23, "buddy_ambiente", A("felpudo"))

    # ── Muebles ──
    def escritorio(x, y, ancho, compus=(), sillas=()):
        """Mesa apoyada contra la pared. y = fila del borde superior de la mesa."""
        arriba = [0] + [3] * (ancho - 2) + [1]
        medio = [10] + [13] * (ancho - 2) + [11]
        abajo = [20] + [23] * (ancho - 2) + [21]
        poner("above1", x, y, "WA_Tables", [arriba])
        poner("furniture1", x, y + 1, "WA_Tables", [medio, abajo])
        choca(x, y + 1, x + ancho - 1, y + 2)
        for cx in compus:
            poner("furniture3", cx, y + 1, "WA_Miscellaneous", [[2, 3], [12, 13]])
        for sx in sillas:
            poner("furniture2", sx, y + 2, "WA_Seats", [[123, 124], [136, 137]])

    def planta(x, y, ids, alto_choque=None):
        poner("furniture2", x, y, "WA_Decoration", ids)
        choca(x, y + len(ids) - 1)

    PLANTA_A = [[75], [87]]   # planta de hojas largas
    PLANTA_B = [[78], [90]]   # arbolito redondo
    PLANTA_C = [[79], [91]]   # planta de hojas anchas
    TELE = [[40, 41, 42], [50, 51, 52]]

    ocupados = {LUGARES_PANTALLA[p["lugar"]] for p in PANTALLAS}

    def tele_decorativa(lugar):
        if LUGARES_PANTALLA[lugar] not in ocupados:
            x, y = LUGARES_PANTALLA[lugar]
            poner("walls2", x, y, "WA_Miscellaneous", TELE)

    # Estudio de contenido
    poner("walls2", 1, 1, "buddy_carteles", C("cartel_estudio"))
    tele_decorativa("estudio")
    escritorio(1, 3, 3, sillas=(1,))
    poner("furniture3", 1, 4, "WA_Miscellaneous", [[0, 1, 0]])
    poner("furniture2", 6, 3, "WA_Seats", [[59], [72]])
    poner("furniture2", 6, 6, "buddy_ambiente", A("camara"))
    choca(6, 7)
    poner("furniture2", 7, 4, "buddy_ambiente", A("luz"))
    choca(7, 5)
    planta(1, 7, PLANTA_A)

    # Sala de reuniones
    tele_decorativa("reuniones")
    poner("walls2", 13, 1, "buddy_carteles", C("cartel_reuniones"))
    poner("furniture2", 11, 4, "WA_Seats", [[121, 122, 121, 122], [134, 135, 134, 135]])
    escritorio(11, 5, 4)
    poner("furniture2", 11, 7, "WA_Seats", [[123, 124, 123, 124], [136, 137, 136, 137]])
    put("furniture2", 10, 6, "WA_Seats", 119)
    put("furniture2", 15, 6, "WA_Seats", 120)
    put("furniture3", 12, 6, "WA_Miscellaneous", 58)
    put("furniture3", 14, 6, "WA_Miscellaneous", 23)
    planta(9, 3, PLANTA_C)
    planta(15, 3, PLANTA_C)

    # Sala de foco
    poner("walls2", 18, 1, "buddy_carteles", C("cartel_foco"))
    escritorio(17, 3, 2, compus=(17,), sillas=(17,))
    escritorio(21, 3, 2, compus=(21,), sillas=(21,))
    poner("furniture2", 21, 6, "WA_Other_Furniture", [[22, 23], [34, 35], [46, 47]])
    choca(21, 7, 22, 8)
    poner("furniture2", 19, 6, "WA_Seats", [[85], [98]])
    planta(17, 7, PLANTA_B)

    # Espacio abierto: escritorios con el nombre de cada uno en la pared
    poner("walls2", 1, 10, "buddy_carteles", C("placa_lucho"))
    poner("walls2", 5, 10, "buddy_carteles", C("placa_ivan"))
    poner("walls2", 7, 10, "buddy_carteles", C("placa_mateo"))
    poner("walls2", 13, 10, "buddy_carteles", C("placa_pablo"))
    poner("walls2", 15, 10, "buddy_carteles", C("placa_sofi"))
    escritorio(1, 11, 2, compus=(1,), sillas=(1,))                 # Lucho, al lado del estudio
    escritorio(5, 11, 4, compus=(5, 7), sillas=(5, 7))             # Ivan y Mateo
    escritorio(13, 11, 4, compus=(13, 15), sillas=(13, 15))        # Pablo y Sofi
    poner("walls2", 9, 10, "WA_Decoration", [[0, 1]])              # cuadro paisaje
    put("walls2", 17, 10, "WA_Miscellaneous", 78)                  # reloj
    poner("walls2", 21, 10, "WA_Decoration", [[24, 25]])           # mapa del mundo
    planta(10, 11, PLANTA_A)
    planta(21, 11, PLANTA_B)
    poner("furniture2", 22, 11, "WA_Miscellaneous", [[46], [56]])  # cafetera
    choca(22, 12)
    poner("furniture2", 1, 14, "WA_Decoration", [[64], [76], [88]])
    choca(1, 16)

    # Rincón de atención al cliente + escritorio de Vero
    poner("walls2", 1, 19, "buddy_carteles", C("placa_vero"))
    put("walls2", 2, 18, "WA_Decoration", 2)
    poner("walls2", 3, 18, "buddy_carteles", C("cartel_atencion"))
    escritorio(1, 20, 2, compus=(1,), sillas=(1,))
    escritorio(3, 20, 3, sillas=(3,))
    put("furniture3", 4, 21, "WA_Miscellaneous", 0)
    put("furniture3", 5, 21, "WA_Miscellaneous", 59)

    # Recepción
    poner("walls2", 12, 18, "buddy_logo", [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11]])
    poner("walls2", 18, 18, "buddy_cuadro", [[0, 1, 2], [3, 4, 5]])
    poner("above1", 6, 21, "WA_Decoration", [[60, 61, 62]])
    poner("furniture2", 6, 22, "WA_Decoration", [[72, 73, 74], [84, 85, 86]])
    choca(7, 23)
    poner("furniture2", 19, 22, "buddy_ambiente", A("estante"))
    choca(19, 22, 21, 23)
    put("furniture2", 13, 23, "WA_Decoration", 93)
    put("furniture2", 16, 23, "WA_Decoration", 93)
    for x in (14, 15):
        put("start", x, 22, "WA_Special_Zones", 1)

    # Pantallas con link
    for i, p in enumerate(PANTALLAS):
        x, y = LUGARES_PANTALLA[p["lugar"]]
        poner("walls2", x, y, "buddy_carteles", C(f"pantalla{i}"))

    # Patio / terraza
    poner("furniture2", 26, 12, "WA_Seats", [[0, 1, 2], [13, 14, 15]])
    poner("furniture1", 27, 14, "WA_Tables", [[177, 178], [187, 188]])
    choca(27, 15, 28, 15)
    put("furniture3", 27, 15, "WA_Miscellaneous", 58)
    put("furniture2", 25, 15, "WA_Seats", 166)
    put("furniture2", 29, 15, "WA_Seats", 164)
    poner("furniture2", 27, 18, "buddy_ambiente", A("brasero"))
    choca(27, 18, 28, 19)
    poner("furniture2", 25, 18, "WA_Seats", [[146], [159]])
    poner("furniture2", 30, 18, "WA_Seats", [[147], [160]])
    planta(24, 11, PLANTA_A)
    planta(30, 11, PLANTA_C)
    planta(24, 20, PLANTA_B)
    planta(30, 20, PLANTA_C)

    def arbol(x, y, col):
        base = [[col, col + 1, col + 2], [col + 25, col + 26, col + 27], [col + 50, col + 51, col + 52]]
        poner("above2", x, y, "WA_Exterior", base[:2])
        poner("furniture3", x, y + 2, "WA_Exterior", [base[2]])
        choca(x + 1, y + 2)

    arbol(24, 1, 0)
    arbol(28, 3, 9)
    arbol(25, 6, 3)
    arbol(28, 22, 12)
    poner("furniture1", 29, 8, "WA_Exterior", [[533, 534], [558, 559]])
    poner("furniture1", 30, 0, "WA_Exterior", [[531, 532], [556, 557]])
    poner("furniture1", 24, 23, "WA_Exterior", [[450, 451]])
    for (x, y) in ((31, 3), (27, 9), (31, 14), (26, 23), (31, 19), (24, 5)):
        put("furniture1", x, y, "WA_Exterior", 506)

    # ── Colisiones ──
    for (x, y) in choques:
        put("collisions", x, y, "WA_Special_Zones", 2)

    # ── Zonas (áreas) ──
    objetos = []

    def area(nombre, x, y, w, h, props):
        objetos.append({"height": h * T, "id": len(objetos) + 1, "name": nombre,
                        "properties": [{"name": n, "type": t, "value": v} for n, t, v in props],
                        "rotation": 0, "type": "area", "visible": True,
                        "width": w * T, "x": x * T, "y": y * T})

    area("salaDeReuniones", 9, 3, 7, 6, [
        ("focusable", "bool", True),
        ("jitsiRoom", "string", "DailyBuddy"),
        ("meetingRoomLabel", "string", "Sala de reuniones"),
        ("zoom_margin", "float", 1.0),
    ])
    area("modoFoco", 17, 3, 6, 6, [("silent", "bool", True)])
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


def main():
    amb, car = generar_tilesets()
    mapa, choques, objetos = armar_mapa(amb, car)
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
        colores = {"salaDeReuniones": (60, 120, 255, 255), "modoFoco": (180, 60, 255, 255)}
        for o in objetos:
            col = colores.get(o["name"], (255, 150, 0, 255))
            d.rectangle([o["x"], o["y"], o["x"] + o["width"] - 1, o["y"] + o["height"] - 1], outline=col, width=3)
        for x in (14, 15):
            d.rectangle([x * T + 8, 22 * T + 8, x * T + 23, 22 * T + 23], fill=(0, 255, 0, 200))
        dbg.alpha_composite(capa)
        dbg.save(ruta)

    print("Listo: oficina.tmj, oficina.png y tilesets/buddy_*.png")


if __name__ == "__main__":
    main()
