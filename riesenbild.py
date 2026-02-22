#!/usr/bin/env python3
"""
💀 TOTENKOPF MOSAIC GENERATOR - SCHARFE MASKE 💀
Mit präzisen Kanten und kontrastreicher Abgrenzung

USAGE:
    python riesenbild.py --mask <pfad_zur_mask.png> --output <name.png> [optionen]

BEISPIELE:
    python riesenbild.py --mask dtf.png --output dtf_scharf.png
    python riesenbild.py --mask totenkopf.png --output ergebnis.jpg --tiles 2000
    python riesenbild.py --mask emoji.png --output mosaik.png --width 150 --height 100
    python riesenbild.py --mask bild.jpg --output test.png --help
    python riesenbild.py --mask logo.png --output fertig.jpg --input "C:\\meine_bilder" --output "D:\\ergebnisse"
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import glob, os, time, random
from collections import deque, defaultdict
import math
from scipy.ndimage import gaussian_filter, sobel, binary_erosion, binary_dilation
import colorsys
import argparse
import sys

# ========================================
# STANDARD KONFIGURATION
# ========================================
# Standard-Ordner (werden durch Kommandozeilen-Argumente überschrieben)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FOLDER = os.path.join(BASE_DIR, "input")
OUTPUT_FOLDER = BASE_DIR
OUTPUT_NAME = "riesenbild_mosaik.png"
DEFAULT_INPUT_FOLDER = r"M:\\projekte_2026\\riesenbild\\input"
DEFAULT_OUTPUT_FOLDER = r"M:\\projekte_2026\\riesenbild"#!/usr/bin/env python3
"""
💀 TOTENKOPF MOSAIC GENERATOR - SCHARFE MASKE 💀
Mit präzisen Kanten und kontrastreicher Abgrenzung

USAGE:
    python riesenbild.py --mask <pfad_zur_mask.png> --output <name.png> [optionen]

BEISPIELE:
    python riesenbild.py --mask dtf.png --output dtf_scharf.png
    python riesenbild.py --mask totenkopf.png --output ergebnis.jpg --tiles 2000
    python riesenbild.py --mask emoji.png --output mosaik.png --width 150 --height 100
    python riesenbild.py --mask bild.jpg --output test.png --help
    python riesenbild.py --mask logo.png --output fertig.jpg --input "C:\\meine_bilder" --output "D:\\ergebnisse"
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import glob, os, time, random
from collections import deque, defaultdict
import math
from scipy.ndimage import gaussian_filter, sobel, binary_erosion, binary_dilation
import colorsys
import argparse
import sys

# ========================================
# STANDARD KONFIGURATION
# ========================================
# Das Verzeichnis, in dem das Skript ausgeführt wird
SCRIPT_DIR = os.getcwd()

# Standard-Ordner (relativ zum Skript-Verzeichnis)
DEFAULT_INPUT_FOLDER = os.path.join(SCRIPT_DIR, "input")
DEFAULT_OUTPUT_FOLDER = SCRIPT_DIR

# Standard Tile-Größe
DEFAULT_TILE_WIDTH = 100
DEFAULT_TILE_HEIGHT = 64

# Standard maximale Tiles
DEFAULT_MAX_TILES = 3000

# ========================================
# SCHARFE MASKEN-OPTIONEN (Standard)
# ========================================
DEFAULT_CONTRAST_BOOST_FACTOR = 2.5
DEFAULT_EDGE_THICKNESS = 2
DEFAULT_EDGE_CONTRAST_MULTIPLIER = 3.0
DEFAULT_THRESHOLD_VALUE = 128
DEFAULT_POST_SHARPEN_FACTOR = 2.0

# ========================================
# KOMMANDOZEILEN-ARGUMENTE
# ========================================
def parse_arguments():
    """Parst die Kommandozeilen-Argumente"""
    parser = argparse.ArgumentParser(
        description='💀 TOTENKOPF MOSAIC GENERATOR - Erstellt ein Mosaik aus vielen Bildern das einen Totenkopf zeigt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
BEISPIELE:
  python riesenbild.py --mask dtf.png --output dtf_scharf.png
  python riesenbild.py --mask totenkopf.png --output ergebnis.jpg --tiles 2000
  python riesenbild.py --mask emoji.png --output mosaik.png --width 150 --height 100
  python riesenbild.py --mask bild.jpg --output test.png --contrast 3.0 --edge-thickness 3
  python riesenbild.py --mask komplex.png --output fertig.jpg --threshold 100 --no-morphology
  python riesenbild.py --mask logo.png --output ergebnis.png --input "C:\\Users\\Bilder" --output-folder "D:\\Mosaike"

WEITERE OPTIONEN:
  Sie können alle Parameter auch direkt in der KONFIGURATION im Skript ändern.
        """
    )
    
    # Pflichtargumente
    parser.add_argument('--mask', '-m', 
                       required=True,
                       help='PFAD ZUR PNG-VORLAGE (z.B. "dtf.png" oder "C:\\bilder\\maske.png")')
    
    parser.add_argument('--output', '-o', 
                       required=True,
                       help='NAME DER AUSGABEDATEI (z.B. "ergebnis.png" oder "mosaik.jpg")')
    
    # Input/Output Ordner
    parser.add_argument('--input-folder', '-i',
                       default=DEFAULT_INPUT_FOLDER,
                       help=f'Input-Ordner mit den Bildern (Standard: {DEFAULT_INPUT_FOLDER} - also "input" im Skript-Verzeichnis)')
    
    parser.add_argument('--output-folder', '-of',
                       default=DEFAULT_OUTPUT_FOLDER,
                       help=f'Output-Ordner für das Ergebnis (Standard: {DEFAULT_OUTPUT_FOLDER} - also das Skript-Verzeichnis)')
    
    # Optionale Argumente für Grid-Größe
    parser.add_argument('--tiles', '-t', 
                       type=int, 
                       default=DEFAULT_MAX_TILES,
                       help=f'Maximale Anzahl Tiles (Standard: {DEFAULT_MAX_TILES})')
    
    parser.add_argument('--width', '-w', 
                       type=int,
                       help='Manuelle Grid-Breite (optional, sonst automatisch)')
    
    parser.add_argument('--height', '-hi', 
                       type=int,
                       help='Manuelle Grid-Höhe (optional, sonst automatisch)')
    
    # Optionale Argumente für Tile-Größe
    parser.add_argument('--tile-width', 
                       type=int, 
                       default=DEFAULT_TILE_WIDTH,
                       help=f'Breite jedes einzelnen Tiles in Pixeln (Standard: {DEFAULT_TILE_WIDTH})')
    
    parser.add_argument('--tile-height', 
                       type=int, 
                       default=DEFAULT_TILE_HEIGHT,
                       help=f'Höhe jedes einzelnen Tiles in Pixeln (Standard: {DEFAULT_TILE_HEIGHT})')
    
    # Schärfe-Optionen
    parser.add_argument('--contrast', '-c', 
                       type=float, 
                       default=DEFAULT_CONTRAST_BOOST_FACTOR,
                       help=f'Kontrastverstärkung Faktor 1.0-3.0 (Standard: {DEFAULT_CONTRAST_BOOST_FACTOR})')
    
    parser.add_argument('--edge-thickness', '-et', 
                       type=int, 
                       default=DEFAULT_EDGE_THICKNESS,
                       help=f'Dicke der Kantenlinie in Tiles (Standard: {DEFAULT_EDGE_THICKNESS})')
    
    parser.add_argument('--edge-multiplier', '-em', 
                       type=float, 
                       default=DEFAULT_EDGE_CONTRAST_MULTIPLIER,
                       help=f'Kanten-Kontrast Multiplier (Standard: {DEFAULT_EDGE_CONTRAST_MULTIPLIER})')
    
    parser.add_argument('--threshold', '-th', 
                       type=int, 
                       default=DEFAULT_THRESHOLD_VALUE,
                       help=f'Helligkeitsschwellwert 0-255 (Standard: {DEFAULT_THRESHOLD_VALUE})')
    
    parser.add_argument('--sharpen', '-s', 
                       type=float, 
                       default=DEFAULT_POST_SHARPEN_FACTOR,
                       help=f'Nachschärfungs-Faktor (Standard: {DEFAULT_POST_SHARPEN_FACTOR})')
    
    # Boolean-Optionen (Schalter)
    parser.add_argument('--no-contrast', 
                       action='store_false', 
                       dest='enable_contrast',
                       help='Kontrastverstärkung AUSSCHALTEN')
    
    parser.add_argument('--no-edge', 
                       action='store_false', 
                       dest='enable_edge',
                       help='Kantenschärfung AUSSCHALTEN')
    
    parser.add_argument('--no-binary', 
                       action='store_false', 
                       dest='enable_binary',
                       help='Binäre Trennung AUSSCHALTEN (weichere Übergänge)')
    
    parser.add_argument('--no-morphology', 
                       action='store_false', 
                       dest='enable_morphology',
                       help='Morphologische Reinigung AUSSCHALTEN')
    
    parser.add_argument('--no-postprocess', 
                       action='store_false', 
                       dest='enable_postprocess',
                       help='Nachbearbeitung AUSSCHALTEN')
    
    # Debug
    parser.add_argument('--debug', '-d',
                       action='store_true',
                       help='Debug-Modus: Speichert zusätzliche Informationen')
    
    parser.add_argument('--version', '-v',
                       action='version',
                       version='💀 Totenkopf Mosaic Generator v4.2 - Dynamische Ordner')
    
    return parser.parse_args()


# ========================================
# FUNKTIONEN
# ========================================

def show_help():
    """Zeigt eine ausführliche Hilfeseite an"""
    help_text = r"""
╔════════════════════════════════════════════════════════════════╗
║         💀 TOTENKOPF MOSAIC GENERATOR - HILFE 💀              ║
╚════════════════════════════════════════════════════════════════╝

Dieses Skript erstellt aus vielen Einzelbildern ein großes Mosaik,
das einen Totenkopf (oder ein anderes Motiv) zeigt.

────────────────────────────────────────────────────────────────
📋 GRUNDLEGENDE VERWENDUNG:
────────────────────────────────────────────────────────────────

  python riesenbild.py --mask MASKE.png --output ERGEBNIS.png

  • MASKE.png     : Ihr Totenkopf-Bild (Schwarz/Weiß ideal)
  • ERGEBNIS.png  : Name der Ausgabedatei

────────────────────────────────────────────────────────────────
📂 ORDNER DEFINIEREN:
────────────────────────────────────────────────────────────────

  python riesenbild.py --mask dtf.png --output ergebnis.jpg --input "C:\\meine_bilder" --output-folder "D:\\ergebnisse"

  • --input, -i      : Ordner mit den Eingabebildern
  • --output-folder, -of : Ordner für das fertige Mosaik

  Standard-Ordner:
    Input:  M:\\projekte_2026\\riesenbild\\input
    Output: M:\\projekte_2026\\riesenbild

────────────────────────────────────────────────────────────────
🎯 BEISPIELE:
────────────────────────────────────────────────────────────────

  # Einfachste Version:
  python riesenbild.py --mask dtf.png --output dtf_scharf.png

  # Mit benutzerdefinierten Ordnern:
  python riesenbild.py --mask totenkopf.png --output test.jpg --input "D:\\Bilder" --output-folder "E:\\Mosaike"

  # Mit benutzerdefinierter Tile-Anzahl:
  python riesenbild.py --mask totenkopf.png --output test.jpg --tiles 2000

  # Manuelle Grid-Größe:
  python riesenbild.py --mask emoji.png --output mosaik.png --width 150 --height 100

  # Mit angepasster Schärfe:
  python riesenbild.py --mask komplex.png --output fertig.jpg --contrast 3.0 --edge-thickness 3

  # Weichere Übergänge (keine binäre Trennung):
  python riesenbild.py --mask weich.png --output sanft.jpg --no-binary

  # Mit Debug-Informationen:
  python riesenbild.py --mask test.png --output debug.png --debug

────────────────────────────────────────────────────────────────
⚙️ ALLE OPTIONEN IM ÜBERBLICK:
────────────────────────────────────────────────────────────────

PFICHTANGABEN:
  --mask, -m         Pfad zur PNG-Vorlage (Totenkopf-Bild)
  --output, -o       Name der Ausgabedatei

ORDNER (NEU!):
  --input-folder, -i     Input-Ordner mit den Bildern
  --output-folder, -of   Output-Ordner für das Ergebnis

GRID-GRÖSSE:
  --tiles, -t        Maximale Anzahl Tiles (Standard: 3000)
  --width, -w        Manuelle Grid-Breite (optional)
  --height, -hi      Manuelle Grid-Höhe (optional)

TILE-GRÖSSE:
  --tile-width       Breite jedes Tiles in Pixeln (Standard: 100)
  --tile-height      Höhe jedes Tiles in Pixeln (Standard: 64)

SCHÄRFE-OPTIONEN:
  --contrast, -c     Kontrastverstärkung 1.0-3.0 (Standard: 2.5)
  --edge-thickness   Dicke der Kanten in Tiles (Standard: 2)
  --edge-multiplier  Kanten-Kontrast Multiplier (Standard: 3.0)
  --threshold, -th   Helligkeitsschwellwert 0-255 (Standard: 128)
  --sharpen, -s      Nachschärfungs-Faktor (Standard: 2.0)

SCHALTER (AN/AUS):
  --no-contrast      Kontrastverstärkung AUSSCHALTEN
  --no-edge          Kantenschärfung AUSSCHALTEN
  --no-binary        Binäre Trennung AUSSCHALTEN (weichere Übergänge)
  --no-morphology    Morphologische Reinigung AUSSCHALTEN
  --no-postprocess   Nachbearbeitung AUSSCHALTEN

SONSTIGES:
  --debug, -d        Debug-Modus (speichert Zwischenschritte)
  --version, -v      Zeigt Versionsnummer an
  --help, -h         Zeigt diese Hilfe an

────────────────────────────────────────────────────────────────
📝 WICHTIGE HINWEISE:
────────────────────────────────────────────────────────────────

• Die Eingabebilder sollten im --input-folder liegen
• Je mehr Bilder, desto detailreicher das Mosaik
• Schwarz/Weiß-Masken funktionieren am besten
• Bei --debug wird eine mask_debug.png gespeichert
• Die Dateigröße kann mehrere 100 MB erreichen!
• Bei Pfaden mit Backslashes können Sie normale oder doppelte 
  Backslashes verwenden: "C:\\bilder" oder "C:\\bilder"

────────────────────────────────────────────────────────────────
🔍 BEI PROBLEMEN:
────────────────────────────────────────────────────────────────

1. Keine Bilder gefunden? → Prüfen Sie --input-folder
2. Maske nicht gefunden? → Absoluten Pfad angeben
3. Zu langsam? → --tiles reduzieren
4. Zu unscharf? → --contrast erhöhen
5. Zu harte Kanten? → --no-binary verwenden

────────────────────────────────────────────────────────────────
"""
    print(help_text)
    sys.exit(0)

def calculate_grid_size(num_images, args, mask_path):
    """Berechnet optimale Grid-Größe"""
    
    # Wenn manuelle Größe angegeben
    if args.width and args.height:
        print(f"📐 Manuelle Grid-Größe: {args.width}×{args.height}")
        return args.width, args.height
    
    # Sonst automatisch basierend auf Masken-Seitenverhältnis
    mask_img = Image.open(mask_path).convert("L")
    orig_width, orig_height = mask_img.size
    aspect_ratio = orig_width / orig_height
    
    total_pixels = min(num_images * 1.2, args.tiles)
    
    height = int(math.sqrt(total_pixels / aspect_ratio))
    width = int(height * aspect_ratio)
    
    while width * height < num_images:
        height += 1
        width = int(height * aspect_ratio)
    
    print(f"📐 Original PNG: {orig_width}×{orig_height} = {orig_width*orig_height:,} Pixel")
    print(f"📐 Automatisch skaliert auf: {width}×{height} = {width*height:,} Tiles")
    
    return width, height

def find_all_images(input_folder):
    """Findet alle Bilder im Input-Ordner"""
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.PNG", "*.JPG", "*.JPEG", "*.BMP"]
    paths = []
    for ext in extensions:
        paths.extend(glob.glob(os.path.join(input_folder, ext)))
    
    paths = sorted(list(set([p for p in paths if os.path.getsize(p) > 0])))
    print(f"📁 {len(paths):,d} originale Bilder gefunden in: {input_folder}")
    
    return paths

def create_sharp_mask(mask_array, args):
    """Erstellt eine extrem scharfe Maske mit verstärkten Kanten"""
    print("⚔️  Erstelle scharfe Maske...")
    
    # 1. BINÄREN SCHWELLWERT ANWENDEN
    if args.enable_binary:
        print(f"   - Harte Trennung bei {args.threshold}")
        binary = mask_array > args.threshold
    else:
        binary = mask_array > 128
    
    # 2. MORPHOLOGISCHE REINIGUNG
    if args.enable_morphology:
        print(f"   - Morphologische Reinigung")
        binary = binary_erosion(binary, iterations=1)
        binary = binary_dilation(binary, iterations=1)
    
    # 3. KANTEN DETEKTIEREN
    edges = np.zeros_like(binary, dtype=float)
    edges[:-1, :] += (binary[:-1, :] != binary[1:, :]).astype(float)
    edges[:, :-1] += (binary[:, :-1] != binary[:, 1:]).astype(float)
    edges = np.clip(edges, 0, 1)
    
    # 4. KANTEN VERDICKEN
    if args.enable_edge and args.edge_thickness > 1:
        from scipy.ndimage import maximum_filter
        edges = maximum_filter(edges, size=args.edge_thickness)
    
    # 5. KONTRASTVERSTÄRKUNG
    if args.enable_contrast:
        print(f"   - Kontrastverstärkung Faktor {args.contrast}")
        weight = 1.0 + edges * (args.contrast - 1.0)
        enhanced_binary = binary.astype(float) * weight
        
        if args.enable_edge:
            edge_areas = edges > 0
            enhanced_binary[edge_areas] = np.clip(
                enhanced_binary[edge_areas] * args.edge_multiplier, 0, 1
            )
        
        binary = enhanced_binary > 0.5
    
    # 6. STATISTIK
    helle_tiles = np.sum(binary)
    dunkle_tiles = binary.size - helle_tiles
    
    print(f"💀 Masken-Verteilung (scharf):")
    print(f"   Helle Tiles: {helle_tiles:,d}")
    print(f"   Dunkle Tiles: {dunkle_tiles:,d}")
    print(f"   Kanten-Tiles: {np.sum(edges > 0):,d}")
    
    return {
        'binary': binary,
        'edges': edges,
        'original': mask_array
    }

def analyze_image_colors_sharp(image_paths, max_analysis=1000):
    """Analysiert Bilder mit Fokus auf Kontrast für scharfe Kanten"""
    print("📊 Analysiere Bilder für scharfe Kanten...")
    
    image_data = []
    
    if len(image_paths) > max_analysis:
        print(f"   Analysiere {max_analysis} repräsentative Bilder...")
        sample_paths = random.sample(image_paths, max_analysis)
    else:
        sample_paths = image_paths
    
    total = len(sample_paths)
    for i, path in enumerate(sample_paths):
        try:
            with Image.open(path) as img:
                img_array = np.array(img.convert("RGB"))
                
                # Helligkeit (Luminanz)
                brightness = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
                avg_brightness = np.mean(brightness)
                
                # KONTRAST
                contrast = np.std(brightness)
                
                image_data.append({
                    'path': path,
                    'brightness': avg_brightness,
                    'contrast': contrast
                })
            
            if (i + 1) % 100 == 0:
                print(f"   {i+1}/{total} Bilder analysiert")
                
        except Exception as e:
            continue
    
    # Sortiere nach Kontrast
    image_data.sort(key=lambda x: x['contrast'], reverse=True)
    
    print(f"✅ {len(image_data)} Bilder analysiert")
    return image_data

def find_best_image_for_sharp_mask(target_brightness, is_edge, image_data, used_images, args):
    """Findet das beste Bild für eine Position"""
    best_score = -float('inf')
    best_image = None
    
    search_data = image_data[:500] if len(image_data) > 500 else image_data
    
    for img_info in search_data:
        brightness_diff = abs(img_info['brightness'] - target_brightness)
        brightness_score = 1.0 - (brightness_diff / 255.0)
        
        if is_edge and args.enable_edge:
            contrast_score = img_info['contrast'] / 255.0
            score = 0.3 * brightness_score + 0.7 * contrast_score
        else:
            score = 0.8 * brightness_score + 0.2 * (img_info['contrast'] / 255.0)
        
        usage_penalty = used_images.get(img_info['path'], 0) * 0.05
        score -= usage_penalty
        
        if score > best_score:
            best_score = score
            best_image = img_info
    
    return best_image

def build_sharp_mosaic(image_paths, image_data, mask_info, grid_width, grid_height, args):
    """Baut das Mosaik mit scharfen Kanten"""
    canvas = Image.new("RGB", (grid_width * args.tile_width, grid_height * args.tile_height), "black")
    
    binary_mask = mask_info['binary']
    edge_mask = mask_info['edges']
    
    print(f"⚔️  Baue Mosaik mit scharfen Kanten...")
    
    placed = 0
    total_tiles = grid_width * grid_height
    used_images = defaultdict(int)
    
    # Separate Pools für Kanten und Flächen
    if image_data:
        split_point = len(image_data) // 3
        edge_images = image_data[:split_point]
        area_images = image_data[split_point:]
    else:
        edge_images = []
        area_images = []
    
    last_progress = 0
    
    for y in range(grid_height):
        for x in range(grid_width):
            is_edge = edge_mask[y, x] > 0
            target_brightness = mask_info['original'][y, x]
            
            if is_edge and edge_images:
                best_img = find_best_image_for_sharp_mask(
                    target_brightness, True, edge_images, used_images, args
                )
            else:
                best_img = find_best_image_for_sharp_mask(
                    target_brightness, False, area_images if area_images else image_data, 
                    used_images, args
                )
            
            if not best_img and image_data:
                best_img = random.choice(image_data)
            
            if best_img:
                img_path = best_img['path']
                used_images[img_path] += 1
                
                try:
                    with Image.open(img_path) as img:
                        img = img.convert("RGB")
                        
                        # SMART CROP
                        img_ratio = img.width / img.height
                        target_ratio = args.tile_width / args.tile_height
                        
                        if abs(img_ratio - target_ratio) > 0.1:
                            if img_ratio > target_ratio:
                                new_width = int(target_ratio * img.height)
                                left = (img.width - new_width) // 2
                                img = img.crop((left, 0, left + new_width, img.height))
                            else:
                                new_height = int(img.width / target_ratio)
                                top = (img.height - new_height) // 2
                                img = img.crop((0, top, img.width, top + new_height))
                        
                        img_resized = img.resize((args.tile_width, args.tile_height), Image.Resampling.LANCZOS)
                        
                        if is_edge and args.enable_edge:
                            enhancer = ImageEnhance.Sharpness(img_resized)
                            img_resized = enhancer.enhance(1.5)
                        
                        canvas.paste(img_resized, (x * args.tile_width, y * args.tile_height))
                        
                        placed += 1
                        
                        progress = int(placed / total_tiles * 100)
                        if progress >= last_progress + 5:
                            print(f"   {progress}% ({placed}/{total_tiles})")
                            last_progress = progress
                            
                except Exception as e:
                    fallback_color = (255,255,255) if binary_mask[y, x] else (0,0,0)
                    if is_edge:
                        fallback_color = (200,200,200) if binary_mask[y, x] else (55,55,55)
                    fallback = Image.new("RGB", (args.tile_width, args.tile_height), fallback_color)
                    canvas.paste(fallback, (x * args.tile_width, y * args.tile_height))
    
    # Nachbearbeitung
    if args.enable_postprocess:
        print("   Schärfe-Nachbearbeitung...")
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(canvas)
        canvas = enhancer.enhance(args.sharpen)
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    
    print(f"✅ {placed} Tiles platziert")
    return canvas

def visualize_mask_debug(mask_info, grid_width, grid_height, output_folder):
    """Erstellt eine Debug-Visualisierung der Maske"""
    debug_size = (grid_width * 10, grid_height * 10)
    debug_img = Image.new("RGB", debug_size, "black")
    draw = ImageDraw.Draw(debug_img)
    
    binary = mask_info['binary']
    edges = mask_info['edges']
    
    for y in range(grid_height):
        for x in range(grid_width):
            color = (255,255,255) if binary[y, x] else (0,0,0)
            if edges[y, x] > 0:
                color = (255,0,0)
            
            x0, y0 = x * 10, y * 10
            x1, y1 = x0 + 10, y0 + 10
            draw.rectangle([x0, y0, x1, y1], fill=color)
    
    debug_path = os.path.join(output_folder, "mask_debug.png")
    debug_img.save(debug_path)
    print(f"🔍 Debug-Maske gespeichert: {debug_path}")

def main():
    # Zeige Hilfe wenn --help oder kein Argument
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Argumente parsen
    args = parse_arguments()
    
    # Zeige Hilfe wenn --help
    # if args.help:
    #     show_help()
    #     return
    
    start_time = time.time()
    
    try:
        # Absoluten Pfad zur Maske erstellen
        if not os.path.isabs(args.mask):
            # Wenn relativ, im aktuellen Verzeichnis oder im Output-Ordner suchen
            if os.path.exists(os.path.join(os.getcwd(), args.mask)):
                mask_path = os.path.join(os.getcwd(), args.mask)
            else:
                mask_path = os.path.join(args.output_folder, args.mask)
        else:
            mask_path = args.mask
        
        if not os.path.exists(mask_path):
            print(f"❌ Maske nicht gefunden: {mask_path}")
            print(f"   Gesucht in: {mask_path}")
            return
        
        # Stelle sicher, dass Output-Ordner existiert
        os.makedirs(args.output_folder, exist_ok=True)
        
        # 1. Bilder finden
        image_paths = find_all_images(args.input_folder)
        num_images = len(image_paths)
        
        if num_images == 0:
            print("❌ Keine Bilder gefunden!")
            return
        
        # 2. Grid-Größe berechnen
        grid_width, grid_height = calculate_grid_size(num_images, args, mask_path)
        
        # 3. PNG-Maske laden
        mask_img = Image.open(mask_path).convert("L")
        mask_img = mask_img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
        mask_array = np.array(mask_img)
        
        # 4. Scharfe Maske erstellen
        mask_info = create_sharp_mask(mask_array, args)
        
        # 5. Debug-Maske speichern
        if args.debug:
            visualize_mask_debug(mask_info, grid_width, grid_height, args.output_folder)
        
        # 6. Bildanalyse
        image_data = analyze_image_colors_sharp(image_paths)
        
        # 7. Mosaik bauen
        mosaic = build_sharp_mosaic(image_paths, image_data, mask_info, grid_width, grid_height, args)
        
        # 8. Speichern
        out = os.path.join(args.output_folder, args.output)
        print(f"💾 Speichere unter: {out}")
        mosaic.save(out, optimize=False, quality=100, dpi=(300,300))
        
        file_size = os.path.getsize(out) / 1024 / 1024
        print(f"\n🎉 Fertig! Dateigröße: {file_size:.1f} MB")
        print(f"⏱️  Dauer: {time.time() - start_time:.1f} Sekunden")
        
        print(f"\n📊 STATISTIK:")
        print(f"   Mosaik-Größe: {grid_width*args.tile_width}×{grid_height*args.tile_height} Pixel")
        print(f"   Das sind etwa {(grid_width*args.tile_width*grid_height*args.tile_height)/1e6:.1f} Megapixel")
        print(f"   Input-Ordner: {args.input_folder}")
        print(f"   Output-Ordner: {args.output_folder}")
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return

if __name__ == "__main__":
    main()