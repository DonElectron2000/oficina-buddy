# Oficina Buddy — Instrucciones

Todo lo que necesitás para ver, publicar y cambiar la oficina virtual.

**Link para el equipo:** https://play.workadventu.re/@/tienda-buddy/oficinas-buddy/oficina-buddy

Los comandos se escriben en la app **Terminal** de la Mac, parado en esta carpeta. Para llegar:

```bash
cd ~/Desktop/"OFI VIRTUAL"
```

> Si algo de esto te traba, abrí Claude Code en esta carpeta y pedile el paso ("agregá a Juan en el cowork", "poné un tablero de Notion en la Sala de Embarque"). Los pasos están pensados para que los pueda hacer por vos.

---

## Qué hay en la oficina

| Zona | Qué es |
|---|---|
| **Content room** (arriba a la izquierda) | Estudio de edición: 3 puestos, fondo verde, cámara y luces. |
| **Sala de Embarque** | Sala de reuniones. Al entrar se abre la videollamada con todos los que estén adentro. |
| **Founders** | Pablo y Sofi, con una mesita para charlar. |
| **Experiencia del cliente** | Vero y el mostrador de atención. |
| **Ardiflet** (arriba a la derecha) | Ivan y Camilo, con la estética de ardiflet.com. |
| **Cowork** (izquierda) | 8 puestos compartidos en una fila de 4 mesas; el primero es el de Mateo. |
| **Patio interno** (centro) | Pasto, fuente, arbolitos y un banco. Se entra por arriba y por los costados. |
| **Café** (derecha) | Barra con banquetas, cafetera y una mesita. |
| **Modo foco** (abajo a la izquierda) | Sala de silencio: adentro nadie te arranca una charla. |
| **Recepción / showroom** (abajo) | Donde aparecés. Logo, estante con bolsos, pantalla de la tienda y cuadro. |
| **Sala de estar** (abajo a la derecha) | Sillón y mesita, pegada a la recepción. |
| **Jardín** (arriba de todo) | Decorativo, no se camina. Está ahí para que la barra de botones de WorkAdventure quede encima del jardín y no tape las oficinas. |

> **Sobre el zoom:** si alejás la cámara al máximo, el mapa queda chico en una esquina con fondo oscuro. Es cómo calcula WorkAdventure el tope del zoom en pantallas grandes (pasa con cualquier mapa); no se puede cambiar desde el mapa. Con un zoom normal no se nota.

---

## 1. Ver el mapa en tu compu (antes de publicar)

```bash
npm run dev
```

Se abre una página en `http://localhost:5173`. Para caminar por la oficina, abrí este link en Chrome **mientras el comando sigue corriendo**:

**https://play.workadventu.re/_/global/localhost:5173/oficina.tmj**

Para cortar, volvé a la Terminal y apretá `Ctrl + C`.

---

## 2. GitHub y GitHub Pages

> ✅ **Ya está hecho.** El repo es https://github.com/DonElectron2000/oficina-buddy y Pages publica desde la rama `gh-pages`. Cada cambio que subís se publica solo.

Si algún día hay que armarlo de cero: repositorio **público** (GitHub Pages gratis lo exige), `UPLOAD_MODE=GH_PAGES` en `.env`, y en **Settings → Pages** elegir la rama **gh-pages** y **/ (root)**. No subas los archivos arrastrándolos a la web de GitHub: la Mac esconde las carpetas que empiezan con punto (`.github`, `.env`) y sin ellas el mapa no se publica.

---

## 3. El link del mapa y WorkAdventure

El mapa publicado es:

```
https://donelectron2000.github.io/oficina-buddy/oficina.tmj
```

> ✅ **Ya está conectado.** En admin.workadventu.re, el mundo "Oficinas Buddy" tiene la sala **Oficina Buddy** con este mapa, marcada como sala por defecto. Como el link del mapa nunca cambia, cada cambio que publicás aparece solo en esa sala.
>
> La sala vieja "Small office" quedó de respaldo. Si no la querés, borrala desde el admin con "Edit Room" → "Delete".

**Cómo se hizo (por si hay que repetirlo):** en admin.workadventu.re → tu mundo → **Create New Room** → pestaña **Custom** → pegar el link `.tmj` → **Select your custom map** → **Save**. Después, **Edit Room** → **Set as default**. Aparece un aviso de "unknown property name" en "Chunk 1": son los créditos de los tiles y se puede ignorar.

---

## 4. Cambiar cosas sin romper nada

Todo lo propio de la oficina se arma con un solo archivo: `herramientas/construir.py`. Arriba de todo tiene una sección **CONFIGURACIÓN**, y es lo único que hay que tocar. Abrilo con TextEdit o cualquier editor. Después de cada cambio, guardá y corré:

```bash
python3 herramientas/construir.py
```

Revisalo con el paso 1 y publicalo con el paso 6.

### Nombres de los escritorios

Hay tres listas:

- **`NOMBRES`**: los escritorios fijos (Pablo, Sofi, Vero, Ivan, Camilo). Cambiá solo lo que está a la derecha de los dos puntos y dejá las comillas: `"camilo": "Camilo",`.
- **`COWORK`**: los 8 puestos compartidos, en orden (fila de arriba de izquierda a derecha, después la de abajo). `""` es un puesto libre sin placa. Para sumar a alguien, reemplazá un `""` por su nombre: `COWORK = ["Mateo", "Juan", "", "", "", "", "", ""]`.
- **`CONTENT_ROOM`**: los 3 puestos de edición, igual que el cowork. Hoy están los tres sin placa.

### Agregar una pantalla que abra un link (por ejemplo, un tablero de Notion)

1. En `PANTALLAS` hay una línea de ejemplo que empieza con `#`. Borrale el `#` y cambiá la `url` por tu link:
   ```python
   {"lugar": "reuniones", "texto": "Notion", "url": "https://www.notion.so/tu-tablero", "abrir": "pestaña"},
   ```
2. Campos:
   - `lugar`: dónde va la pantalla. Hay dos huecos libres: `"reuniones"` (pared de la Sala de Embarque) y `"content"` (pared de la Content room). Hoy los dos tienen una tele de adorno que la pantalla reemplaza. `"recepcion"` ya lo usa la tienda.
   - `texto`: lo que se lee en la pantalla. Corto, unos 15 caracteres como máximo.
   - `abrir`: dejá `"pestaña"`. Con `"adentro"` se abre al costado del mapa, pero muchas páginas no lo permiten (Tiendanube no lo permite).

Para usarla, parate adelante de la pantalla y apretá **ESPACIO**.

### Cambiar los colores

Los colores de la marca están en `construir.py`, en las líneas debajo de "Paleta de la marca" (`VERDE = `, `SALVIA = `, `MADERA = `, etc.). Los de Ardiflet están justo abajo, en "Paleta de Ardiflet". Por ejemplo, para aclarar el piso cambiá `MADERA = c("#7F6D5F")` por otro código de color.

### Lo que conviene no hacer

- No edites `oficina.tmj` a mano ni con Tiled si vas a seguir usando el script: cada vez que lo corras, lo pisa con lo que dice `construir.py`.
- No borres las comas ni las comillas de las listas.

---

## 5. "Sentarte" en tu puesto

WorkAdventure **no tiene una función para sentarse**: los personajes solo caminan o se quedan quietos (lo chequeamos en la documentación y en el código). Por eso la oficina usa un truco:

- Las sillas se pueden pisar; los escritorios, no.
- Caminá hasta tu silla desde abajo, así quedás mirando la computadora.
- El respaldo de la silla se dibuja por encima de tu personaje y te tapa las piernas, así que parece que estás sentado.

---

## 6. Publicar un cambio

```bash
git add -A && git commit -m "Cambio en la oficina" && git push
```

GitHub lo vuelve a armar solo (mirá el tilde verde en la pestaña **Actions** del repo). A los 2 o 3 minutos lo ves en WorkAdventure. Si no aparece, recargá la página con `Cmd + Shift + R`.
