import os
import webbrowser
from flask import Flask, render_template_string, send_from_directory, request, jsonify
from pathlib import Path
import threading
from PIL import Image

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Rutas: Asegúrate de que estas rutas sean correctas para tu sistema
RUTA_DESCARGAS = Path.home() / "Downloads"
RUTA_GENERADOS = Path.cwd() / "generated_images"
os.makedirs(RUTA_GENERADOS, exist_ok=True)
EXTENSIONES_IMAGEN = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# --- PLANTILLA HTML PRINCIPAL (Sin cambios) ---
HTML_PRINCIPAL = """
<!DOCTYPE html>
<html lang="es">
<head>
    <link rel="icon" type="image/jpeg" href="https://media.licdn.com/dms/image/v2/D4E0BAQE-P2CgFGPjJA/company-logo_200_200/B4EZYh5564HYAQ-/0/1744325550134/clientesanonimos_logo?e=2147483647&v=beta&t=iLsxUpYM-BzkwX8pc-NC4VW1BFCaoL8PlFpgtYDu-ss">
    <meta charset="UTF-8"><title>Editor de Imágenes</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #eef2f7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 24px; box-sizing: border-box; }
        .container { display: grid; grid-template-columns: 2fr 1fr; gap: 90px; width: 100%; max-width: 1100px; height: 90vh; max-height: 650px; }
        .preview-wrapper { display: flex; flex-direction: column; gap: 15px; }
        .preview-area { height: 100%; width: 100%; cursor: crosshair; }
        #preview-canvas { max-width: 100%; max-height: 100%; object-fit: contain; }
        .preview-placeholder { color: #007bff; font-weight: 500; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; }
        .preview-placeholder svg { width: 64px; margin-bottom: 16px; }
        .upload-column { display: flex; flex-direction: column; gap: 24px; }
        .upload-slot { flex-grow: 1; cursor: pointer; }
        .card { background-color: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 24px; display: flex; justify-content: center; align-items: center; flex-direction: column; text-align: center; position: relative; overflow: hidden; }
        .upload-slot h3 { margin: 0 0 16px 0; color: #333; font-weight: 600; }
        .plus-button { width: 40px; height: 40px; border-radius: 50%; background-color: #007bff; color: white; font-size: 24px; border: none; display: flex; align-items: center; justify-content: center; line-height: 1;}
        .card .slot-image-container { width: 100%; height: 100%; position: absolute; top: 0; left: 0; }
        .card .slot-image-container img { width: 100%; height: 100%; object-fit: cover; }
        .action-buttons { display: flex; gap: 10px; justify-content: center; }
        .action-buttons button { font-size: 1em; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; transition: background-color 0.2s; }
        #clear-button { background-color: #ffc107; color: #333; }
        #download-button { background-color: #28a745; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="preview-wrapper">
            <div id="preview-box" class="card preview-area">
                <canvas id="preview-canvas"></canvas>
                <div id="preview-placeholder" class="preview-placeholder">
                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M21.9998 3.99998C21.9998 3.4477 21.5521 2.99998 20.9998 2.99998H2.9998C2.44752 2.99998 1.9998 3.4477 1.9998 3.99998V19.9999C1.9998 20.5522 2.44752 20.9999 2.9998 20.9999H20.9998C21.5521 20.9999 21.9998 20.5522 21.9998 19.9999V3.99998ZM2.9998 4.99998H19.9998V18.9999H2.9998V4.99998ZM8.4998 10.4999C7.67139 10.4999 6.9998 11.1715 6.9998 11.9999C6.9998 12.8283 7.67139 13.4999 8.4998 13.4999C9.32822 13.4999 9.9998 12.8283 9.9998 11.9999C9.998 11.1715 9.32822 10.4999 8.4998 10.4999ZM4.9998 18.9999H18.9998L14.9998 13.9999L11.4998 18.4999L9.4998 15.9999L4.9998 18.9999Z"></path></svg>
                    <p>Vista Previa</p>
                </div>
            </div>
            <div id="editor-controls" class="action-buttons" style="display: none;">
                <button id="clear-button">Limpiar Cuadros</button>
                <button id="download-button">Descargar Imagen</button>
            </div>
        </div>
        <div class="upload-column">
            <div id="upload-slot-1" class="card upload-slot" onclick="openGallery(1)"><h3>Imagen 1</h3><div class="plus-button">+</div></div>
            <div id="upload-slot-2" class="card upload-slot" onclick="openGallery(2)"><h3>Imagen 2</h3><div class="plus-button">+</div></div>
        </div>
    </div>
    <script>
        let currentSlot = 0;
        let selectedImages = { 1: null, 2: null };
        const canvas = document.getElementById('preview-canvas');
        const ctx = canvas.getContext('2d');
        const placeholder = document.getElementById('preview-placeholder');
        const editorControls = document.getElementById('editor-controls');
        let originalCombinedImage = null; let drawnRects = []; let isDrawing = false; let startX, startY;

        function loadImageToCanvas(imageUrl) {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.src = imageUrl;
            img.onload = () => {
                placeholder.style.display = 'none';
                const previewBox = document.getElementById('preview-box');
                const maxW = previewBox.clientWidth - 48;
                const maxH = previewBox.clientHeight - 48;
                const ratio = Math.min(maxW / img.width, maxH / img.height);
                canvas.width = img.width;
                canvas.height = img.height;
                canvas.style.width = (img.width * ratio) + 'px';
                canvas.style.height = (img.height * ratio) + 'px';
                ctx.drawImage(img, 0, 0);
                originalCombinedImage = img;
                drawnRects = [];
                editorControls.style.display = 'flex';
            };
        }

        function getMousePos(e) { const rect = canvas.getBoundingClientRect(); const scaleX = canvas.width / rect.width; const scaleY = canvas.height / rect.height; return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY }; }
        canvas.addEventListener('mousedown', e => { if (!originalCombinedImage) return; isDrawing = true; const pos = getMousePos(e); startX = pos.x; startY = pos.y; });
        canvas.addEventListener('mousemove', e => { if (!isDrawing) return; const pos = getMousePos(e); redrawCanvas(); ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'; ctx.fillRect(startX, startY, pos.x - startX, pos.y - startY); });
        canvas.addEventListener('mouseup', e => { if (!isDrawing) return; isDrawing = false; const pos = getMousePos(e); drawnRects.push({ x: startX, y: startY, w: pos.x - startX, h: pos.y - startY }); redrawCanvas(); });
        
        function resetAll() {
            selectedImages = { 1: null, 2: null };
            originalCombinedImage = null;
            drawnRects = [];
            document.getElementById('upload-slot-1').innerHTML = '<h3>Imagen 1</h3><div class="plus-button">+</div>';
            document.getElementById('upload-slot-2').innerHTML = '<h3>Imagen 2</h3><div class="plus-button">+</div>';
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.style.width = '0px'; canvas.style.height = '0px';
            placeholder.style.display = 'flex';
            editorControls.style.display = 'none';
        }
        document.getElementById('clear-button').addEventListener('click', resetAll);
        
        document.getElementById('download-button').addEventListener('click', () => { const l = document.createElement('a'); l.download = 'imagen-editada.png'; l.href = canvas.toDataURL('image/png'); l.click(); });
        
        openGallery = (slotId) => { currentSlot = slotId; const w=900, h=500, l=(screen.width/2)-(w/2), t=(screen.height/2)-(h/2); window.open('/gallery', 'galleryWindow', `width=${w},height=${h},top=${t},left=${l}`); };
        selectImage = (imageUrl, imageName) => { selectedImages[currentSlot] = imageName; document.getElementById(`upload-slot-${currentSlot}`).innerHTML = `<div class="slot-image-container"><img src="${imageUrl}"></div>`; updatePreview(); };
        updatePreview = async () => { if (selectedImages[1] && selectedImages[2]) { const res = await fetch(`/combine?img1=${selectedImages[1]}&img2=${selectedImages[2]}`); const data = await res.json(); if(data.url) loadImageToCanvas(data.url); } else if (selectedImages[1]) { loadImageToCanvas(`/images/${selectedImages[1]}`); } else if (selectedImages[2]) { loadImageToCanvas(`/images/${selectedImages[2]}`); }};
        redrawCanvas = () => { if (!originalCombinedImage) return; ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.drawImage(originalCombinedImage, 0, 0); ctx.fillStyle = 'white'; drawnRects.forEach(rect => { ctx.fillRect(rect.x, rect.y, rect.w, rect.h); }); };
    </script>
</body>
</html>
"""

# --- PLANTILLA HTML DE LA GALERÍA (Sin cambios) ---
HTML_GALERIA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Seleccionar Imagen</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: #f0f2f5; 
            margin: 0;
            color: #1c1e21;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        h1 {
            text-align: center; 
            padding: 20px; 
            background-color: #ffffff; 
            margin: 0; 
            font-size: 1.5em;
            font-weight: 600;
            border-bottom: 1px solid #dddfe2;
            width: 100%;
            box-sizing: border-box;
            flex-shrink: 0;
        }
        .carousel-container {
            flex-grow: 1;
            width: 100%;
            overflow: hidden; /* Oculta el desbordamiento del track */
            cursor: grab;
            display: flex;
            align-items: center;
        }
        .carousel-container.active {
            cursor: grabbing;
        }
        .carousel-track {
            display: flex;
            /* Evita que los items de flex se encojan */
            flex-shrink: 0; 
            /* Para que la transición sea suave si se añade en el futuro */
            transition: transform 0.2s ease-out; 
            will-change: transform;
        }
        .gallery-item {
            flex: 0 0 auto; /* No permitir que crezca o se encoja */
            width: 300px; /* Ancho fijo para cada imagen */
            padding: 15px;
            box-sizing: border-box;
            user-select: none; /* Evitar la selección de texto al arrastrar */
        }
        .gallery-item-inner {
            border: 1px solid #dddfe2;
            border-radius: 12px;
            overflow: hidden;
            background-color: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            transition: box-shadow 0.2s ease, transform 0.2s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .gallery-item-inner:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }
        .gallery-item img {
            width: 100%;
            height: 280px;
            object-fit: contain; 
            display: block;
            background-color: #f8f9fa;
            pointer-events: none; /* Evita que la imagen intercepte eventos de arrastre */
        }
        .gallery-item p {
            margin: 12px;
            font-size: 14px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Selecciona una imagen (arrastra para ver más)</h1>
    
    <div id="carousel-container" class="carousel-container">
        <div id="carousel-track" class="carousel-track">
            {% for imagen in imagenes %}
            <div class="gallery-item" onclick="selectAndClose('{{ imagen.url }}','{{ imagen.nombre }}')">
                <div class="gallery-item-inner">
                    <img src="{{ imagen.url }}" alt="{{ imagen.nombre }}">
                    <p title="{{ imagen.nombre }}">{{ imagen.nombre }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        let wasDragged = false;
        function selectAndClose(imageUrl, imageName) {
            // Solo ejecuta la selección si no hubo un arrastre
            if (wasDragged) {
                return;
            }
            if (window.opener && !window.opener.closed) {
                window.opener.selectImage(imageUrl, imageName);
            }
            window.close();
        }

        // --- SCRIPT DE ARRASTRE DEL CARRUSEL ---
        document.addEventListener('DOMContentLoaded', () => {
            const container = document.getElementById('carousel-container');
            const track = document.getElementById('carousel-track');
            
            if (!track || track.children.length === 0) return;

            let isDown = false;
            let startX;
            let scrollLeft;

            container.addEventListener('mousedown', (e) => {
                isDown = true;
                wasDragged = false; // Reinicia el flag en cada clic
                container.classList.add('active');
                startX = e.pageX - container.offsetLeft;
                scrollLeft = container.scrollLeft;
                e.preventDefault(); // Prevenir comportamiento por defecto
            });

            container.addEventListener('mouseleave', () => {
                isDown = false;
                container.classList.remove('active');
            });

            container.addEventListener('mouseup', () => {
                isDown = false;
                container.classList.remove('active');
            });

            container.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                wasDragged = true; // Si el mouse se mueve, se considera un arrastre
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const walk = (x - startX) * 2; // Multiplicador para un arrastre más rápido
                container.scrollLeft = scrollLeft - walk;
            });
        });
    </script>
</body>
</html>
"""

# --- RUTAS DEL SERVIDOR WEB ---

@app.route('/')
def index():
    return render_template_string(HTML_PRINCIPAL)

@app.route('/gallery')
def gallery():
    imagenes = []
    try:
        # Ordenar archivos por fecha de modificación para ver los más recientes primero
        archivos = [(f, f.stat().st_mtime) for f in RUTA_DESCARGAS.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONES_IMAGEN]
        archivos.sort(key=lambda item: item[1], reverse=True)
        for ruta, _ in archivos:
            imagenes.append({'nombre': ruta.name, 'url': f"/images/{ruta.name}"})
    except Exception as e:
        print(f"Error al listar archivos: {e}")
    
    return render_template_string(HTML_GALERIA, imagenes=imagenes)

@app.route('/combine')
def combine_images():
    img1_name = request.args.get('img1')
    img2_name = request.args.get('img2')
    if not img1_name or not img2_name:
        return jsonify({'error': 'Faltan nombres de archivo'}), 400

    try:
        img1_path = RUTA_DESCARGAS / img1_name
        img2_path = RUTA_DESCARGAS / img2_name
        
        if not img1_path.exists() or not img2_path.exists():
            return jsonify({'error': 'Uno o ambos archivos no existen'}), 404

        image1 = Image.open(img1_path)
        image2 = Image.open(img2_path)
        
        # --- CAMBIO REALIZADO AQUÍ ---
        # Se establece el margen en 0 para que las imágenes queden pegadas
        MARGIN = 0 
        BACKGROUND_COLOR = (238, 242, 247) 

        # Se calcula el ancho total sin margen y se usa la altura máxima
        total_width = image1.width + MARGIN + image2.width
        max_height = max(image1.height, image2.height)

        # Se crea la nueva imagen. El color de fondo no se verá si el margen es 0, pero se mantiene por si se cambia en el futuro.
        combined_image = Image.new('RGB', (total_width, max_height), BACKGROUND_COLOR)
        
        # Se pegan las imágenes una al lado de la otra
        combined_image.paste(image1, (0, 0))
        combined_image.paste(image2, (image1.width + MARGIN, 0))
        
        # Se guarda la imagen combinada
        combined_filename = f"combined_{os.path.splitext(img1_name)[0]}_{os.path.splitext(img2_name)[0]}.jpg"
        combined_path = RUTA_GENERADOS / combined_filename
        combined_image.save(combined_path, "JPEG")
        
        return jsonify({'url': f"/generated/{combined_filename}"})

    except Exception as e:
        print(f"Error al combinar imágenes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(RUTA_DESCARGAS, filename)

@app.route('/generated/<path:filename>')
def serve_generated_image(filename):
    return send_from_directory(RUTA_GENERADOS, filename)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    print("Iniciando servidor local en http://127.0.0.1:5000/")
    threading.Timer(1, open_browser).start()
    app.run(port=5000, debug=False)