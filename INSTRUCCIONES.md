# Oficina Buddy — Instrucciones

Todo lo que necesitás para ver, publicar y cambiar la oficina virtual.
Los comandos se escriben en la app **Terminal** de la Mac, parado en esta carpeta. Para llegar:

```bash
cd ~/Desktop/"OFI VIRTUAL"
```

> Si algo de esto te traba, abrí Claude Code en esta carpeta y pedile el paso ("subí la oficina a GitHub", "cambiá el nombre de Lucho por Luciano"). Los pasos están pensados para que los pueda hacer por vos.

---

## 1. Ver el mapa en tu compu (antes de publicar)

```bash
npm run dev
```

Se abre una página en `http://localhost:5173`. Para caminar por la oficina, abrí este link en Chrome **mientras el comando sigue corriendo**:

**https://play.workadventu.re/_/global/localhost:5173/oficina.tmj**

Para cortar, volvé a la Terminal y apretá `Ctrl + C`.

---

## 2. Subirlo a GitHub y activar GitHub Pages

> ✅ **Ya está hecho.** El repo es https://github.com/DonElectron2000/oficina-buddy y Pages publica desde la rama `gh-pages`. Esta sección queda como referencia por si algún día hay que armarlo de cero.

GitHub Pages gratis solo funciona con repositorios **públicos**. Cualquiera con el link puede ver el dibujo del mapa, pero no lo que pasa ni lo que se habla en la oficina.

**a) Crear el repositorio y subir los archivos** (una sola vez). Con la app `gh` ya logueada en tu cuenta:

```bash
git init -b main && git add -A && git commit -m "Oficina Buddy"
```

```bash
gh repo create oficina-buddy --public --source=. --push
```

No subas los archivos arrastrándolos a la web de GitHub: la Mac esconde las carpetas que empiezan con punto (`.github`, `.env`) y sin ellas el mapa no se publica.

**b) Esperar el primer armado.** En la página del repo, entrá a la pestaña **Actions**. Vas a ver "Build and deploy" corriendo. Tarda 1 o 2 minutos y tiene que terminar con un tilde verde ✅.

**c) Activar Pages.** En el repo: **Settings → Pages**. En "Source" elegí **Deploy from a branch**, en "Branch" elegí **gh-pages** y **/ (root)**, y tocá **Save**. Esperá un par de minutos.

---

## 3. El link final y cómo ponerlo en WorkAdventure

El link del mapa es:

```
https://donelectron2000.github.io/oficina-buddy/oficina.tmj
```

Si lo abrís en el navegador y ves un montón de texto, está funcionando.

**Probarlo antes de tocar tu mundo** (es una sala pública de prueba, no la de tu equipo):
https://play.workadventu.re/_/global/donelectron2000.github.io/oficina-buddy/oficina.tmj

> ✅ **Ya está conectado.** En admin.workadventu.re, el mundo "Oficinas Buddy" tiene la sala **Oficina Buddy** con este mapa, marcada como sala por defecto. Link para el equipo:
> **https://play.workadventu.re/@/tienda-buddy/oficinas-buddy/oficina-buddy**
>
> La sala vieja "Small office" quedó de respaldo. Si no la querés, borrala desde el admin con "Edit Room" → "Delete".

**Cómo se hizo (por si hay que repetirlo):** en admin.workadventu.re → tu mundo → **Create New Room** → pestaña **Custom** → pegar el link `.tmj` → **Select your custom map** → **Save**. Después, **Edit Room** → **Set as default**. Aparece un aviso de "unknown property name" en "Chunk 1": son los créditos de los tiles y se puede ignorar.

**Ponerlo en tu mundo (forma general):** entrá a **admin.workadventu.re**, abrí tu mundo y la sala que hoy usa la plantilla. En su configuración buscá el campo de la **URL del mapa** (puede decir "Map URL"), pegá el link `.tmj` de arriba y guardá. Los nombres de los menús a veces cambian: si no lo encontrás, buscá dónde figura la URL de la plantilla actual y reemplazala.

---

## 4. Cambiar cosas sin romper nada

Todo lo propio de la oficina se arma con un solo archivo: `herramientas/construir.py`. Arriba de todo tiene una sección **CONFIGURACIÓN**, y es lo único que hay que tocar. Abrilo con TextEdit o cualquier editor.

### Cambiar un nombre de escritorio

1. En `NOMBRES`, cambiá solo lo que está a la derecha de los dos puntos y dejá las comillas:
   `"lucho": "Luciano",`
2. Guardá y regenerá la oficina:
   ```bash
   python3 herramientas/construir.py
   ```
3. Revisalo con el paso 1 y publicalo (paso 5).

### Agregar una pantalla que abra un link (por ejemplo, un tablero de Notion)

1. En `PANTALLAS` hay una línea de ejemplo que empieza con `#`. Borrale el `#` y cambiá la `url` por tu link:
   ```python
   {"lugar": "reuniones", "texto": "Notion", "url": "https://www.notion.so/tu-tablero", "abrir": "pestaña"},
   ```
2. Campos:
   - `lugar`: dónde va la pantalla. Hay dos huecos libres: `"reuniones"` (pared de la sala de reuniones) y `"estudio"` (pared del estudio). `"recepcion"` ya lo usa la tienda.
   - `texto`: lo que se lee en la pantalla. Corto, unos 15 caracteres como máximo.
   - `abrir`: dejá `"pestaña"`. Con `"adentro"` se abre al costado del mapa, pero muchas páginas no lo permiten (Tiendanube no lo permite).
3. Guardá, corré `python3 herramientas/construir.py`, revisá y publicá.

Para usarla, parate adelante de la pantalla y apretá **ESPACIO**.

### Lo que conviene no hacer

- No edites `oficina.tmj` a mano ni con Tiled si vas a seguir usando el script: cada vez que lo corras, lo pisa con lo que dice `construir.py`.
- No borres las comas del final de cada línea en `NOMBRES` y `PANTALLAS`.

---

## 5. Publicar un cambio

```bash
git add -A && git commit -m "Cambio en la oficina" && git push
```

GitHub lo vuelve a armar solo (mirá el tilde verde en **Actions**). A los 2 o 3 minutos lo ves en WorkAdventure. Si no aparece, recargá la página con `Cmd + Shift + R`.
