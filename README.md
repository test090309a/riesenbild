# Riesenbild Mosaik Generator
- agentic programing - jn@gemini&perplexity

Erstellt aus vielen kleinen Bildern ein großes Mosaik aus eine Maske.

# Benutzung
- ins input verzeichnis kommen eine ganze menge bilder rein, mind. 2500.
können von comfy oder so erstellt werden.

- python riesenbild.py -h

# Skript Ausgabe:
  python riesenbild.py --mask input-maske.png --output output.png 
  📁 2,146 originale Bilder gefunden in: M:\projekte_2026\riesenbild\input
  📐 Original PNG: 382×289 = 110,398 Pixel
  📐 Automatisch skaliert auf: 58×44 = 2,552 Tiles
  ⚔️  Erstelle scharfe Maske...
     - Harte Trennung bei 128
     - Morphologische Reinigung
     - Kontrastverstärkung Faktor 2.5
  💀 Masken-Verteilung (scharf):
     Helle Tiles: 531
     Dunkle Tiles: 2,021
     Kanten-Tiles: 486
  📊 Analysiere Bilder für scharfe Kanten...
     Analysiere 1000 repräsentative Bilder...
     100/1000 Bilder analysiert
     200/1000 Bilder analysiert
     300/1000 Bilder analysiert
     ...
     ✅ 1000 Bilder analysiert
     ⚔️  Baue Mosaik mit scharfen Kanten...
     5% (128/2552)
     10% (256/2552)
     15% (383/2552
     ...
        95% (2425/2552)
   100% (2552/2552)
   Schärfe-Nachbearbeitung...
  ✅ 2552 Tiles platziert
  💾 Speichere unter: M:\projekte_2026\riesenbild\output.png
  
  🎉 Fertig! Dateigröße: 25.1 MB
  ⏱️  Dauer: 72.8 Sekunden
  
  📊 STATISTIK:
     Mosaik-Größe: 5800×2816 Pixel
     Das sind etwa 16.3 Megapixel
     Input-Ordner: M:\projekte_2026\riesenbild\input
     Output-Ordner: M:\projekte_2026\riesenbild

     
