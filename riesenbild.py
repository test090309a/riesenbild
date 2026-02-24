#!/usr/bin/env python3
"""
💀 MOSAIC GENERATOR - GPU 💀
Maske definieren und Ausgabeverzeichnis.
JEDES BILD NUR EINMAL VERSION!
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
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
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
DEFAULT_EDGE_THICKNESS = 0
DEFAULT_EDGE_CONTRAST_MULTIPLIER = 3.0
DEFAULT_THRESHOLD_VALUE = 128
DEFAULT_POST_SHARPEN_FACTOR = 2.0

# ========================================
# FARB-OPTIONEN
# ========================================
ENABLE_COLOR_ENHANCEMENT = True     # Farbverstärkung einschalten
COLOR_SATURATION_FACTOR = 1.3       # 1.0 = normal, 1.3 = 30% intensiver
ENABLE_LEVELS = True                 # Levels anpassen (Schwarz-/Weißpunkt)
BLACK_LEVEL = 0                      # Schwarzpunkt (0-255)
WHITE_LEVEL = 245                    # Weißpunkt (0-255) - etwas reduzieren für mehr Tiefe
ENABLE_CURVES = True                  # Kurven anpassen für mehr Kontrast
CURVE_MIDTONE = 1.2                   # Mittenkontrast (>1 = mehr Kontrast)
ENABLE_VIBRANCE = True                 # Vibrance (intelligente Sättigung)
VIBRANCE_FACTOR = 1.2                  # Vibrance-Stärke

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
  python riesenbild.py --mask farbig.png --output intensiv.jpg --saturation 1.5 --vibrance 1.3
        """
    )
       
    # Pflichtargumente
    # parser.add_argument('--batch-size', type=int, default=64, help='Batch-Size für GPU Analyse')
    parser.add_argument('--batch-size', '-bs', type=int, default=64, help='Batch size für GPU Analyse')
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
    
    # Farb-Optionen
    parser.add_argument('--saturation', '-sat', 
                       type=float, 
                       default=COLOR_SATURATION_FACTOR,
                       help=f'Sättigungsfaktor 0.0-2.0 (Standard: {COLOR_SATURATION_FACTOR})')
    
    parser.add_argument('--vibrance', '-vib', 
                       type=float, 
                       default=VIBRANCE_FACTOR,
                       help=f'Vibrance-Faktor 0.0-2.0 (Standard: {VIBRANCE_FACTOR})')
    
    parser.add_argument('--black-level', '-bl', 
                       type=int, 
                       default=BLACK_LEVEL,
                       help=f'Schwarzpunkt 0-255 (Standard: {BLACK_LEVEL})')
    
    parser.add_argument('--white-level', '-wl', 
                       type=int, 
                       default=WHITE_LEVEL,
                       help=f'Weißpunkt 0-255 (Standard: {WHITE_LEVEL})')
    
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
    
    # Farboptionen Schalter
    parser.add_argument('--no-color', 
                       action='store_false', 
                       dest='enable_color',
                       help='Farbverstärkung AUSSCHALTEN')
    
    parser.add_argument('--no-levels', 
                       action='store_false', 
                       dest='enable_levels',
                       help='Levels-Anpassung AUSSCHALTEN')
    
    parser.add_argument('--no-curves', 
                       action='store_false', 
                       dest='enable_curves',
                       help='Curves-Anpassung AUSSCHALTEN')
    
    # WICHTIG: NEUE OPTION FÜR EINMALIGE VERWENDUNG
    parser.add_argument('--unique', '-u',
                       action='store_true',
                       help='JEDES BILD NUR EINMAL VERWENDEN (maximale Vielfalt)')
    
    # Vorschau-Modus
    parser.add_argument('--preview', '-p',
                       action='store_true',
                       help='VORSCHAU-MODUS: Schnelle Berechnung mit kleinen Tiles')
    
    # Hochqualitativ-Modus
    parser.add_argument('--high-quality', '-hq',
                       action='store_true',
                       help='HOCHQUALITATIV-MODUS: Maximale Qualität mit großen Tiles')
    
    # Debug
    parser.add_argument('--debug', '-d',
                       action='store_true',
                       help='Debug-Modus: Speichert zusätzliche Informationen')
    
    parser.add_argument('--version', '-v',
                       action='version',
                       version='💀 Totenkopf Mosaic Generator v5.0 - Jedes Bild nur einmal!')
    
    return parser.parse_args()

# ========================================
# HILFE-FUNKTION
# ========================================

def show_help():
    """Zeigt eine ausführliche Hilfeseite an"""
    help_text = r"""
╔════════════════════════════════════════════════════════════════╗
║    💀 TOTENKOPF MOSAIC GENERATOR - JEDES BILD NUR EINMAL 💀   ║
╚════════════════════════════════════════════════════════════════╝

Dieses Skript erstellt aus vielen Einzelbildern ein großes Mosaik,
das einen Totenkopf (oder ein anderes Motiv) zeigt.

NEU: Mit --unique verwendet JEDES Bild nur EINMAL im Mosaik!

────────────────────────────────────────────────────────────────
📋 GRUNDLEGENDE VERWENDUNG:
────────────────────────────────────────────────────────────────

  python riesenbild.py --mask MASKE.png --output ERGEBNIS.png

  • MASKE.png     : Ihr Totenkopf-Bild (Schwarz/Weiß ideal)
  • ERGEBNIS.png  : Name der Ausgabedatei

────────────────────────────────────────────────────────────────
🎯 NEU: MAXIMALE BILDVIELFALT:
────────────────────────────────────────────────────────────────

  --unique, -u   JEDES Bild nur EINMAL verwenden!
  
  Beispiel:
    python riesenbild.py --mask totenkopf.png --output einmalig.png --unique
  
  So wird garantiert, dass jedes Bild maximal einmal vorkommt.
  Perfekt für Sammlungen mit vielen verschiedenen Bildern!

────────────────────────────────────────────────────────────────
🚀 SPEZIAL-MODI:
────────────────────────────────────────────────────────────────

  --preview, -p     VORSCHAU-MODUS: Schnelle Berechnung mit kleinen Tiles
  --high-quality, -hq HOCHQUALITATIV-MODUS: Maximale Qualität

────────────────────────────────────────────────────────────────
🎨 FARB-OPTIONEN:
────────────────────────────────────────────────────────────────

  --saturation, -sat   Sättigung (1.0 = normal, 1.3 = 30% intensiver)
  --vibrance, -vib     Intelligente Sättigung (schont Hauttöne)
  --black-level, -bl   Schwarzpunkt (0-255, niedriger = mehr Tiefe)
  --white-level, -wl   Weißpunkt (0-255, niedriger = mehr Kontrast)
  --no-color           Farbverstärkung komplett ausschalten
  --no-levels          Levels-Anpassung ausschalten
  --no-curves          Curves-Anpassung ausschalten

────────────────────────────────────────────────────────────────
"""
    print(help_text)
    sys.exit(0)

# ========================================
# KONFIGURATION BASIEREND AUF MODUS
# ========================================

def configure_mode(args):
    """Konfiguriert Parameter basierend auf Preview/High-Quality Modus"""
    if args.preview:
        print("🔍 VORSCHAU-MODUS AKTIVIERT - Schnelle Berechnung")
        if not args.tile_width or args.tile_width == DEFAULT_TILE_WIDTH:
            args.tile_width = 40
        if not args.tile_height or args.tile_height == DEFAULT_TILE_HEIGHT:
            args.tile_height = 25
        if not args.tiles or args.tiles == DEFAULT_MAX_TILES:
            args.tiles = 500
        if not args.contrast or args.contrast == DEFAULT_CONTRAST_BOOST_FACTOR:
            args.contrast = 2.0
        args.enable_postprocess = False
    
    elif args.high_quality:
        print("✨ HOCHQUALITATIV-MODUS AKTIVIERT - Maximale Qualität")
        if not args.tile_width or args.tile_width == DEFAULT_TILE_WIDTH:
            args.tile_width = 250
        if not args.tile_height or args.tile_height == DEFAULT_TILE_HEIGHT:
            args.tile_height = 160
        if not args.tiles or args.tiles == DEFAULT_MAX_TILES:
            args.tiles = 15000
        if not args.contrast or args.contrast == DEFAULT_CONTRAST_BOOST_FACTOR:
            args.contrast = 3.0
        if not args.edge_thickness or args.edge_thickness == DEFAULT_EDGE_THICKNESS:
            args.edge_thickness = 3
        if not args.sharpen or args.sharpen == DEFAULT_POST_SHARPEN_FACTOR:
            args.sharpen = 2.5
        if not args.saturation or args.saturation == COLOR_SATURATION_FACTOR:
            args.saturation = 1.5
        if not args.vibrance or args.vibrance == VIBRANCE_FACTOR:
            args.vibrance = 1.3
    
    return args

# ========================================
# GRID-FUNKTIONEN
# ========================================

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
    
    total_pixels = min(num_images, args.tiles)
    
    height = int(math.sqrt(total_pixels / aspect_ratio))
    width = int(height * aspect_ratio)
    
    while width * height < total_pixels:
        height += 1
        width = int(height * aspect_ratio)
    
    print(f"📐 Original PNG: {orig_width}×{orig_height} = {orig_width*orig_height:,} Pixel")
    print(f"📐 Automatisch skaliert auf: {width}×{height} = {width*height:,} Tiles")
    
    return width, height

# ========================================
# BILD-FUNKTIONEN MIT SHUFFLE
# ========================================

def find_all_images(input_folder):
    """Findet alle Bilder im Input-Ordner, bereinigt sie und mischt sie durch"""
    # Alle gängigen Endungen abdecken
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]
    paths = []
    
    # Bilder einsammeln (case-insensitive)
    for ext in extensions:
        paths.extend(glob.glob(os.path.join(input_folder, ext)))
        paths.extend(glob.glob(os.path.join(input_folder, ext.upper())))

    # Duplikate entfernen und nur Dateien > 0 Bytes behalten
    paths = list(set([p for p in paths if os.path.getsize(p) > 0]))
    
    if not paths:
        print(f"❌ FEHLER: Keine Bilder in {input_folder} gefunden!")
        return []

    # --- DER SHUFFLE ---
    random.shuffle(paths) 
    
    print(f"🎲 {len(paths):,d} Bilder gefunden und für maximale Vielfalt gemischt.")
    return paths

# ========================================
# MASKEN-FUNKTIONEN
# ========================================

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

def create_sharp_mask_gpu(mask_array, args):
    """Erstellt eine scharfe Maske mit PyTorch-GPU-Beschleunigung"""
    print("⚔️  Erstelle scharfe Maske auf der GPU...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Maske in Tensor umwandeln und auf GPU schieben
    # Shape: [1, 1, height, width]
    mask_tensor = torch.from_numpy(mask_array).float().to(device).unsqueeze(0).unsqueeze(0)
    
    # 1. BINÄREN SCHWELLWERT ANWENDEN
    threshold = args.threshold / 255.0  # Normalisieren auf [0,1] Bereich
    binary = (mask_tensor / 255.0 > threshold).float()
    
    # 2. MORPHOLOGISCHE REINIGUNG (Erosion/Dilation via MaxPool/MinPool)
    if args.enable_morphology:
        padding = 1
        kernel_size = 3
        binary = F.max_pool2d(binary, kernel_size=kernel_size, stride=1, padding=padding)  # Dilation
        binary = -F.max_pool2d(-binary, kernel_size=kernel_size, stride=1, padding=padding)  # Erosion

    # 3. KANTEN DETEKTIEREN - NEUE KORREKTE VERSION
    # 3. KANTEN DETEKTIEREN - FIX: Sicherstellen, dass Dimensionen exakt matchen
    edges_h = torch.zeros_like(binary)
    edges_v = torch.zeros_like(binary)

    # Horizontale Kanten (Unterschiede zwischen Zeilen)
    # Vergleiche Zeile 0 bis N-1 mit Zeile 1 bis N
    h_diff = (binary[:, :, :-1, :] != binary[:, :, 1:, :]).float()
    edges_h[:, :, :-1, :] = h_diff
    
    # Vertikale Kanten (Unterschiede zwischen Spalten)
    # Vergleiche Spalte 0 bis M-1 mit Spalte 1 bis M
    v_diff = (binary[:, :, :, :-1] != binary[:, :, :, 1:]).float()
    edges_v[:, :, :, :-1] = v_diff
    
    # Jetzt sind beide Tensoren garantiert wieder in der Größe der Maske (71x54)
    edges = torch.clamp(edges_h + edges_v, 0, 1)
    
    if args.enable_edge and args.edge_thickness > 1:
        et = args.edge_thickness
        padding = et // 2

        edges = F.max_pool2d(
            edges,
            kernel_size=et,
            stride=1,
            padding=padding
        )

        # 🔒 SHAPE-FIX: exakt auf Originalgröße beschneiden
        edges = edges[:, :, :binary.shape[2], :binary.shape[3]]

    # 5. KONTRASTVERSTÄRKUNG
    if args.enable_contrast:
        weight = 1.0 + edges * (args.contrast - 1.0)
        enhanced_binary = binary * weight
        
        if args.enable_edge:
            enhanced_binary = torch.where(edges > 0, enhanced_binary * args.edge_multiplier, enhanced_binary)
        
        binary_result = (enhanced_binary > 0.5).float()
    else:
        binary_result = (binary > 0.5).float()

    # Zurück zu NumPy für den Rest des Skripts
    binary_np = binary_result.squeeze().cpu().numpy()
    edges_np = edges.squeeze().cpu().numpy()
    
    print(f"✅ Maske auf GPU berechnet (Helle Tiles: {int(np.sum(binary_np)):,d})")
    
    return {
        'binary': binary_np,
        'edges': edges_np,
        'original': mask_array
    }

# ========================================
# FARB-FUNKTIONEN
# ========================================

def apply_levels(image, black_level=0, white_level=255):
    """Wendet Levels-Anpassung an (Schwarzpunkt/Weißpunkt)"""
    if black_level == 0 and white_level == 255:
        return image
    
    img_array = np.array(image).astype(float)
    
    # Lineare Skalierung von [black_level, white_level] nach [0, 255]
    scale = 255.0 / (white_level - black_level) if white_level > black_level else 1.0
    img_array = (img_array - black_level) * scale
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)

def apply_curves(image, midtone=1.0):
    """Wendet Kurven-Anpassung an (Mittenkontrast)"""
    if midtone == 1.0:
        return image
    
    img_array = np.array(image).astype(float) / 255.0
    
    # Gamma-Korrektur-ähnliche Kurve
    if midtone > 1:
        img_array = np.power(img_array, 1.0/midtone)
    else:
        img_array = np.power(img_array, midtone)
    
    img_array = (img_array * 255).astype(np.uint8)
    
    return Image.fromarray(img_array)

def apply_vibrance(image, vibrance_factor=1.2):
    """Intelligente Sättigung: Weniger gesättigte Farben werden mehr verstärkt"""
    if vibrance_factor == 1.0:
        return image
    
    # In HSV konvertieren
    img = image.convert('HSV')
    h, s, v = img.split()
    
    s_array = np.array(s).astype(float)
    
    # Vibrance: Weniger gesättigte Pixel werden stärker verstärkt
    saturation_boost = 1.0 + (vibrance_factor - 1.0) * (1.0 - s_array / 255.0)
    s_array = np.clip(s_array * saturation_boost, 0, 255).astype(np.uint8)
    
    # Zurück zu RGB
    s_boosted = Image.fromarray(s_array)
    img_boosted = Image.merge('HSV', (h, s_boosted, v))
    
    return img_boosted.convert('RGB')

def apply_saturation(image, saturation_factor=1.3):
    """Einfache Sättigungserhöhung"""
    if saturation_factor == 1.0:
        return image
    
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(saturation_factor)

def apply_color_enhancement(image, args):
    """Wendet alle Farbverbesserungen in sinnvoller Reihenfolge an"""
    if not args.enable_color:
        return image
    
    print("   🎨 Verbessere Farben...")
    
    # 1. Zuerst Levels anpassen
    if args.enable_levels:
        image = apply_levels(image, args.black_level, args.white_level)
    
    # 2. Dann Vibrance
    image = apply_vibrance(image, args.vibrance)
    
    # 3. Dann normale Sättigung
    image = apply_saturation(image, args.saturation)
    
    # 4. Zum Schluss Curves
    if args.enable_curves:
        image = apply_curves(image, CURVE_MIDTONE)
    
    return image

# ========================================
# BILDANALYSE-FUNKTIONEN
# ========================================

def analyze_image_colors_sharp(image_paths, max_analysis=None):
    """Analysiert ALLE Bilder im Ordner (kein Limit mehr)"""
    if max_analysis is None:
        max_analysis = len(image_paths)
        
    print(f"📊 Analysiere Bilder für scharfe Kanten...")
    print(f"   Nutze den gesamten Pool von {max_analysis} Bildern.")
    
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

def analyze_image_colors_gpu(image_paths, batch_size=64):
    """Analysiert Bilder massiv parallel auf der GPU mit Debug-Ausgabe"""
    if not torch.cuda.is_available():
        print("⚠️  GPU angefordert, aber CUDA ist nicht verfügbar. Fallback auf CPU...")
        return None

    # --- DEBUG AUSGABE ---
    device_id = torch.cuda.current_device()
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(device_id)
    vram_total = torch.cuda.get_device_properties(device_id).total_memory / 1e9
    
    print("\n" + "="*50)
    print(f"🚀 GPU INITIALISIERT")
    print(f"   Gerät:  {gpu_name}")
    print(f"   VRAM:   {vram_total:.2f} GB")
    print(f"   Status: Berechne mit PyTorch/CUDA")
    print("="*50 + "\n")
    # ---------------------

    #device = torch.device("cuda")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Transformation: Bild auf kleine Größe bringen für schnelle Analyse
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
    ])

    image_data = []
    total = len(image_paths)
    
    # print(f"📊 Analysiere {total} Bilder in Batches auf {device}...")
    print(f"📊 Analysiere {total} Bilder in Batches von {batch_size} auf {device}...")

    for i in range(0, total, batch_size):
        batch_paths = image_paths[i:i + batch_size]
        batch_tensors = []
        valid_paths = []

        # Bilder laden und vorbereiten
        for p in batch_paths:
            try:
                img = Image.open(p).convert("RGB")
                batch_tensors.append(transform(img))
                valid_paths.append(p)
            except:
                continue

        if not batch_tensors:
            continue

        # Stapel auf GPU schieben (Batch Shape: [B, 3, 64, 64])
        batch_stack = torch.stack(batch_tensors).to(device)

        # Helligkeit berechnen (Luminanz-Formel gewichtet)
        # r*0.299 + g*0.587 + b*0.114
        weights = torch.tensor([0.299, 0.587, 0.114], device=device).view(1, 3, 1, 1)
        brightness_map = (batch_stack * weights).sum(dim=1)
        
        # Durchschnittliche Helligkeit pro Bild im Batch
        avg_b = brightness_map.mean(dim=[1, 2]) * 255
        
        # Kontrast (Standardabweichung der Helligkeit)
        std_b = brightness_map.std(dim=[1, 2]) * 255

        # Ergebnisse zurück auf die CPU und speichern
        avg_b = avg_b.cpu().numpy()
        std_b = std_b.cpu().numpy()

        for idx, path in enumerate(valid_paths):
            image_data.append({
                'path': path,
                'brightness': float(avg_b[idx]),
                'contrast': float(std_b[idx])
            })

        if (i + batch_size) % (batch_size * 5) == 0 or (i + batch_size) >= total:
            print(f"   {min(i + batch_size, total)}/{total} Bilder verarbeitet")

    image_data.sort(key=lambda x: x['contrast'], reverse=True)
    return image_data

# ========================================
# NEUE VERBESSERTE BILDSUCHE - JEDES BILD NUR EINMAL
# ========================================

def find_unique_image_for_mask(target_brightness, is_edge, image_data, used_images, used_history, args):
    """
    Findet das beste Bild für eine Position - GARANTIERT dass jedes Bild nur EINMAL verwendet wird
    """
    if not image_data:
        return None
    
    # Alle noch NICHT verwendeten Bilder
    unused_images = [img for img in image_data if used_images.get(img['path'], 0) == 0]
    
    # Wenn der Unique-Modus aktiv ist und es noch ungenutzte Bilder gibt, NUR diese verwenden
    if args.unique and unused_images:
        search_pool = unused_images
        print(f"   DEBUG: Noch {len(unused_images)} ungenutzte Bilder verfügbar") if args.debug else None
    else:
        # Fallback: Wenn keine ungenutzten Bilder mehr da sind oder Unique-Modus aus
        if args.unique:
            print(f"⚠️  WARNUNG: Keine ungenutzten Bilder mehr! Verwende bereits genutzte Bilder (Notfall-Modus)")
        search_pool = image_data
    
    best_score = -float('inf')
    best_image = None
    
    for img_info in search_pool:
        # Helligkeitsunterschied berechnen
        brightness_diff = abs(img_info['brightness'] - target_brightness)
        brightness_score = 1.0 - (brightness_diff / 255.0)
        
        # Für Kanten: Höheres Gewicht auf Kontrast
        if is_edge and args.enable_edge:
            contrast_score = img_info['contrast'] / 255.0
            score = 0.3 * brightness_score + 0.7 * contrast_score
        else:
            score = 0.8 * brightness_score + 0.2 * (img_info['contrast'] / 255.0)
        
        # KEINE Usage Penalty im Unique-Modus - entweder Bild ist verfügbar oder nicht
        if not args.unique:
            # Normale Penalty für nicht-unique Modus
            usage_penalty = used_images.get(img_info['path'], 0) * 0.1
            score -= usage_penalty
        
        # Zusätzlicher Bonus für ungenutzte Bilder im Nicht-Unique-Modus
        if not args.unique and used_images.get(img_info['path'], 0) == 0:
            score += 0.2  # Bonus für Erstnutzung
        
        # History-Vermeidung (verhindert direkte Wiederholungen)
        if img_info['path'] in used_history:
            score *= 0.5  # Starke Reduzierung für kürzlich verwendete Bilder
        
        if score > best_score:
            best_score = score
            best_image = img_info
    
    return best_image

# ========================================
# GPU-BESCHLEUNIGTE BILDSUCHE (angepasst für Unique-Modus)
# ========================================

def find_unique_image_for_mask_gpu(target_brightness, is_edge, image_data, used_images, used_history, args, device):
    """GPU-beschleunigte Version der Bildsuche für maximale Geschwindigkeit"""
    if not image_data:
        return None
    
    # Für Unique-Modus: Nur ungenutzte Bilder durchsuchen
    if args.unique:
        # Indizes der ungenutzten Bilder finden
        unused_indices = [i for i, img in enumerate(image_data) if used_images.get(img['path'], 0) == 0]
        
        if unused_indices:
            # Nur ungenutzte Bilder betrachten
            search_indices = unused_indices
        else:
            # Notfall: Alle Bilder (aber das sollte nicht passieren)
            print(f"⚠️  WARNUNG: Keine ungenutzten Bilder mehr auf GPU!")
            search_indices = list(range(len(image_data)))
    else:
        search_indices = list(range(len(image_data)))
    
    if not search_indices:
        return None
    
    # Konvertiere relevante Bilddaten in Listen für GPU-Verarbeitung
    brightness_list = [image_data[i]['brightness'] for i in search_indices]
    contrast_list = [image_data[i]['contrast'] for i in search_indices]
    usage_list = [used_images.get(image_data[i]['path'], 0) for i in search_indices]
    path_list = [image_data[i]['path'] for i in search_indices]
    
    # Konvertiere zu Tensoren auf GPU
    brightness_values = torch.tensor(brightness_list, device=device)
    contrast_values = torch.tensor(contrast_list, device=device)
    usage_counts = torch.tensor(usage_list, device=device)
    
    # Berechne Scores auf GPU
    brightness_diff = torch.abs(brightness_values - target_brightness)
    brightness_score = 1.0 - (brightness_diff / 255.0)
    brightness_score = torch.clamp(brightness_score, 0, 1)
    
    if is_edge and args.enable_edge:
        contrast_score = contrast_values / 255.0
        contrast_score = torch.clamp(contrast_score, 0, 1)
        score = 0.3 * brightness_score + 0.7 * contrast_score
    else:
        score = 0.8 * brightness_score + 0.2 * (contrast_values / 255.0)
    
    # Keine Usage Penalty im Unique-Modus (da wir nur ungenutzte betrachten)
    if not args.unique:
        score -= usage_counts * 0.1
    
    # History-Vermeidung (CPU-seitig prüfen wir später)
    
    # Besten Index finden
    best_local_idx = torch.argmax(score).item()
    best_global_idx = search_indices[best_local_idx]
    best_image = image_data[best_global_idx]
    
    return best_image

# ========================================
# MOSAIK-BAU-FUNKTIONEN (angepasst für Unique-Modus)
# ========================================

def build_unique_mosaic(image_paths, image_data, mask_info, grid_width, grid_height, args):
    """
    Baut das Mosaik - GARANTIERT dass jedes Bild nur EINMAL verwendet wird
    """
    canvas = Image.new("RGB", (grid_width * args.tile_width, grid_height * args.tile_height), "black")
    
    binary_mask = mask_info['binary']
    edge_mask = mask_info['edges']
    
    print(f"⚔️  Baue Mosaik mit scharfen Kanten...")
    if args.unique:
        print(f"🎯 UNIQUE-MODUS AKTIV: Jedes Bild wird NUR EINMAL verwendet!")
    
    placed = 0
    total_tiles = grid_width * grid_height
    used_images = defaultdict(int)  # Zählt wie oft jedes Bild verwendet wurde
    used_history = deque(maxlen=100)  # Letzte 100 verwendete Bilder (für Wiederholungsvermeidung)
    
    # Prüfe ob genug Bilder für Unique-Modus vorhanden sind
    if args.unique and len(image_data) < total_tiles:
        print(f"⚠️  WARNUNG: Nur {len(image_data)} Bilder für {total_tiles} Tiles verfügbar!")
        print(f"   Im Unique-Modus werden einige Bilder mehrfach verwendet werden müssen.")
        print(f"   Empfehlung: --tiles {len(image_data)} oder weniger verwenden.")
    
    # Statistiken
    if image_data:
        print(f"📊 Bildverteilung: {len(image_data)} Bilder für {total_tiles} Tiles")
        if args.unique:
            if len(image_data) >= total_tiles:
                print(f"   ✅ Genug Bilder für einmalige Verwendung!")
            else:
                print(f"   ⚠️  {total_tiles - len(image_data)} Bilder müssen mehrfach verwendet werden")
    
    last_progress = 0
    
    # Für bessere Verteilung: Positionen zufällig durchmischen
    positions = [(x, y) for y in range(grid_height) for x in range(grid_width)]
    random.shuffle(positions)
    
    for x, y in positions:
        is_edge = edge_mask[y, x] > 0
        target_brightness = mask_info['original'][y, x]
        
        # Bild suchen (mit Unique-Logik)
        best_img = find_unique_image_for_mask(
            target_brightness, is_edge, image_data, used_images, used_history, args
        )
        
        # Fallback falls kein Bild gefunden
        if not best_img and image_data:
            # Letzte Chance: irgendein Bild nehmen
            if used_images:
                # Am wenigsten verwendete Bilder bevorzugen
                usage_counts = [(img, used_images.get(img['path'], 0)) for img in image_data]
                usage_counts.sort(key=lambda x: x[1])
                best_img = usage_counts[0][0]
            else:
                best_img = random.choice(image_data)
        
        if best_img:
            img_path = best_img['path']
            used_images[img_path] += 1
            used_history.append(img_path)
            
            try:
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    
                    # SMART CROP - Proportional zuschneiden
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
                    
                    # Kantenschärfung für Edge-Bereiche
                    if is_edge and args.enable_edge:
                        enhancer = ImageEnhance.Sharpness(img_resized)
                        img_resized = enhancer.enhance(1.5)
                    
                    canvas.paste(img_resized, (x * args.tile_width, y * args.tile_height))
                    
                    placed += 1
                    
                    progress = int(placed / total_tiles * 100)
                    if progress >= last_progress + 5:
                        print(f"   {progress}% ({placed}/{total_tiles})")
                        if args.unique and args.debug:
                            unused = len([v for v in used_images.values() if v == 0])
                            print(f"      Noch {unused} ungenutzte Bilder")
                        last_progress = progress
                        
            except Exception as e:
                # Fallback-Farbe bei Fehler
                fallback_color = (255,255,255) if binary_mask[y, x] else (0,0,0)
                if is_edge:
                    fallback_color = (200,200,200) if binary_mask[y, x] else (55,55,55)
                fallback = Image.new("RGB", (args.tile_width, args.tile_height), fallback_color)
                canvas.paste(fallback, (x * args.tile_width, y * args.tile_height))
    
    # Nachbearbeitung
    if args.enable_postprocess:
        print("   Nachbearbeitung...")
        
        # 1. Zuerst schärfen
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(canvas)
        canvas = enhancer.enhance(args.sharpen)
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        
        # 2. Dann Farben verbessern
        canvas = apply_color_enhancement(canvas, args)
    
    print(f"✅ {placed} Tiles platziert")
    
    # Statistik zur Bildnutzung
    if args.unique:
        multiple_used = sum(1 for count in used_images.values() if count > 1)
        if multiple_used > 0:
            print(f"⚠️  {multiple_used} Bilder mussten mehrfach verwendet werden")
        else:
            print(f"🎉 ALLE Bilder wurden genau EINMAL verwendet!")
    
    print(f"📊 Tatsächliche Nutzung: {len(used_images)} verschiedene Bilder verwendet")
    
    return canvas

def build_unique_mosaic_gpu(image_data, mask_info, grid_width, grid_height, args):
    """Baut das Mosaik mit GPU-Unterstützung - GARANTIERT dass jedes Bild nur EINMAL verwendet wird"""
    device = torch.device("cuda")
    print(f"⚔️  Baue Mosaik auf der GPU ({grid_width}x{grid_height} Tiles)...")
    
    if args.unique:
        print(f"🎯 UNIQUE-MODUS AKTIV: Jedes Bild wird NUR EINMAL verwendet!")
    
    # Ziel-Leinwand als Tensor
    canvas_h = grid_height * args.tile_height
    canvas_w = grid_width * args.tile_width
    canvas = torch.zeros((3, canvas_h, canvas_w), device=device)
    
    binary_mask = mask_info['binary']
    edge_mask = mask_info['edges']
    
    tile_transform = transforms.Compose([
        transforms.Resize((args.tile_height, args.tile_width)),
        transforms.ToTensor(),
    ])

    used_images = defaultdict(int)
    used_history = deque(maxlen=100)
    
    placed = 0
    total_tiles = grid_width * grid_height
    
    # Prüfe ob genug Bilder für Unique-Modus vorhanden sind
    if args.unique and len(image_data) < total_tiles:
        print(f"⚠️  WARNUNG: Nur {len(image_data)} Bilder für {total_tiles} Tiles verfügbar!")
        print(f"   Im Unique-Modus werden einige Bilder mehrfach verwendet werden müssen.")
    
    # Positionen mischen für bessere Verteilung
    positions = [(x, y) for y in range(grid_height) for x in range(grid_width)]
    random.shuffle(positions)

    for x, y in positions:
        is_edge = edge_mask[y, x] > 0
        target_brightness = mask_info['original'][y, x]
        
        # Verbesserte Auswahl-Logik mit Unique-Modus
        best_img = find_unique_image_for_mask_gpu(
            target_brightness, is_edge, image_data, used_images, used_history, args, device
        )
        
        # Fallback falls kein Bild gefunden
        if not best_img and image_data:
            # Am wenigsten verwendete Bilder bevorzugen
            if used_images:
                usage_counts = [(img, used_images.get(img['path'], 0)) for img in image_data]
                usage_counts.sort(key=lambda x: x[1])
                best_img = usage_counts[0][0]
            else:
                best_img = random.choice(image_data)
        
        if best_img:
            used_images[best_img['path']] += 1
            used_history.append(best_img['path'])
            
            try:
                with Image.open(best_img['path']) as img:
                    img = img.convert("RGB")
                    
                    # SMART CROP (Proportional halten)
                    img_ratio = img.width / img.height
                    target_ratio = args.tile_width / args.tile_height
                    if abs(img_ratio - target_ratio) > 0.05:
                        if img_ratio > target_ratio:
                            new_width = int(target_ratio * img.height)
                            left = (img.width - new_width) // 2
                            img = img.crop((left, 0, left + new_width, img.height))
                        else:
                            new_height = int(img.width / target_ratio)
                            top = (img.height - new_height) // 2
                            img = img.crop((0, top, img.width, top + new_height))
                    
                    tile_tensor = tile_transform(img).to(device)
                    
                    # Kantenschärfung
                    if is_edge and getattr(args, 'enable_edge', False):
                        kernel = torch.tensor(
                            [[[-1, -1, -1],
                            [-1,  9, -1],
                            [-1, -1, -1]]],
                            dtype=torch.float32,
                            device=device,
                        ).unsqueeze(0)  # -> (1, 1, 3, 3)
                        tile_tensor = F.conv2d(tile_tensor.unsqueeze(0), kernel, padding=1).squeeze(0)
                        tile_tensor = torch.clamp(tile_tensor, 0, 1)
                    
                    y_start, x_start = y * args.tile_height, x * args.tile_width
                    canvas[:, y_start:y_start+args.tile_height, x_start:x_start+args.tile_width] = tile_tensor
                    placed += 1
            except Exception:
                continue
        
        # Fortschritt anzeigen
        if placed % 500 == 0:
            print(f"   {placed}/{total_tiles} Tiles platziert...")
    
    print(f"✅ {placed} Tiles auf GPU platziert")
    
    # Statistik zur Bildnutzung
    if args.unique:
        multiple_used = sum(1 for count in used_images.values() if count > 1)
        if multiple_used > 0:
            print(f"⚠️  {multiple_used} Bilder mussten mehrfach verwendet werden")
        else:
            print(f"🎉 ALLE Bilder wurden genau EINMAL verwendet!")
    
    print(f"📊 Tatsächliche Nutzung: {len(used_images)} verschiedene Bilder verwendet")
    
    result_img = transforms.ToPILImage()(canvas.cpu())
    if getattr(args, 'enable_postprocess', True):
        result_img = apply_color_enhancement(result_img, args)
        
    return result_img

# ========================================
# DEBUG-FUNKTIONEN
# ========================================

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

# ========================================
# MAIN-FUNKTION
# ========================================

def main():
    # Zeige Hilfe wenn --help oder kein Argument
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Argumente parsen
    args = parse_arguments()
    
    # Modus-basierte Konfiguration anwenden
    args = configure_mode(args)
    
    start_time = time.time()
    
    try:
        # Absoluten Pfad zur Maske erstellen
        # ===============================
        # MASKE LADEN
        # ===============================
        mask_arg = os.path.normpath(args.mask)

        search_dirs = [
            "",                     # direkt relativ zum Projekt
            args.input_folder,      # input/
            os.path.join(SCRIPT_DIR, "mask"),
            os.path.join(SCRIPT_DIR, "masks"),
        ]

        # Absoluter Pfad → direkt prüfen
        if os.path.isabs(mask_arg):
            candidate_paths = [mask_arg]
        else:
            candidate_paths = []

            # Falls Nutzer bereits einen Ordner angibt (input/..., mask/...)
            candidate_paths.append(os.path.join(SCRIPT_DIR, mask_arg))

            # Zusätzlich in bekannten Ordnern suchen (nur Dateiname)
            if os.path.basename(mask_arg) == mask_arg:
                for d in search_dirs:
                    candidate_paths.append(os.path.join(d, mask_arg))

        # Duplikate entfernen
        candidate_paths = list(dict.fromkeys(candidate_paths))

        # Erste existierende Maske nehmen
        mask_path = None
        for path in candidate_paths:
            if path and os.path.exists(path):
                mask_path = path
                break

        if mask_path is None:
            print("❌ Maske nicht gefunden.")
            print("   Gesucht in:")
            for p in candidate_paths:
                print("   -", p)
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
        
        # Prüfe ob Unique-Modus möglich ist
        total_tiles = grid_width * grid_height
        if args.unique and num_images < total_tiles:
            print(f"\n⚠️  ACHTUNG: Unique-Modus aktiv, aber nur {num_images} Bilder für {total_tiles} Tiles!")
            print(f"   Das Mosaik wird {total_tiles - num_images} Bilder mehrfach verwenden müssen.\n")
        
        # 3. PNG-Maske laden
        mask_img = Image.open(mask_path).convert("L")
        mask_img = mask_img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
        mask_array = np.array(mask_img)
        
        # 4. Scharfe Maske erstellen
        use_gpu = torch.cuda.is_available()
        if use_gpu:
            mask_info = create_sharp_mask_gpu(mask_array, args)
        else:
            mask_info = create_sharp_mask(mask_array, args)
        
        # 5. Debug-Maske speichern
        if args.debug:
            visualize_mask_debug(mask_info, grid_width, grid_height, args.output_folder)
        
        # 6. Bildanalyse
        print(f"🔍 Prüfe Hardware-Beschleunigung...")
        if use_gpu:
            device = torch.device("cuda") # Sicherstellen, dass device definiert ist
            print(f"\n📊 Starte Analyse von {len(image_paths)} Bildern (Batch-Size: {args.batch_size}) auf {device}...")
            image_data = analyze_image_colors_gpu(image_paths, batch_size=args.batch_size)
        else:
            print(f"ℹ️ Nutze CPU-Modus (keine GPU gefunden).")
            image_data = analyze_image_colors_sharp(image_paths)
        
        # 7. Mosaik bauen (mit Unique-Modus)
        if use_gpu:
            mosaic = build_unique_mosaic_gpu(image_data, mask_info, grid_width, grid_height, args)
        else:
            mosaic = build_unique_mosaic(image_paths, image_data, mask_info, grid_width, grid_height, args)
        
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