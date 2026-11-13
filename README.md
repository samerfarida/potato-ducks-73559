# Potato Ducks · FIRST LEGO League Team #73559

![Design preview showing the mascot on the coin front, the duck footprint on the reverse, and the standalone duck with its engraved stand](docs/design_preview.png)

A 60 mm team coin that doubles as two fridge magnets and a freestanding display mascot, designed for multicolor 3D printing. The coin has a flexing Potato Duck on the front and a webbed footprint beneath **FIRST LEGO LEAGUE** on the back, with **TEAM** stacked above **#73559**. Both faces use the same bold lettering size. The display stand is engraved with **#73559** and filled with yellow.

## Which file should I open?

| To print | Open in Bambu Studio | What's included |
| --- | --- | --- |
| Coin or fridge magnets | [Coin project](print/coin/Potato_Ducks_H2C_4color_CONFIGURED.3mf) | Both faces, each with one center magnet pocket |
| Standalone mascot | [Mascot and stand project](print/mascot/Potato_Duck_Mascot_H2C_4color.3mf) | Flat-backed duck and separate engraved stand |

Open the coin and mascot files **as projects** to keep the Bambu Lab H2C settings and color assignments. They use four PLA colors: **navy, brown, yellow, and orange**. Match the project colors to your loaded AMS spools and check the sliced preview before printing.

## Print the magnetic coin

1. Print both faces artwork up. Each face has one centered **Ø6.30 × 2.05 mm** pocket for a **Ø6 × 2 mm** disc magnet.
2. Dry-fit the magnets and mark their orientation so the faces attract back-to-back. Glue one magnet into each pocket with adhesive suitable for PLA and the magnet coating. Keep the magnets flush or just below the surface and let the glue cure fully.
3. Snap the halves together and rotate them by hand, or pull them apart to use them as fridge magnets. The coin halves themselves stay unglued.

The rim is **3.60 mm** thick per face, or **7.20 mm** assembled; the raised artwork adds **0.40 mm** per face. Test magnet fit and holding strength before batching.

## Print and assemble the mascot

Print the duck flat with the artwork facing up and the stand with its slot facing up. Once the parts have cooled, slide the plain tab into the beveled slot opening. Face the duck toward the engraved **#73559** so the team number is visible. Dry-fit the tab before using any adhesive.

## Browse the files

| Folder | Contents |
| --- | --- |
| [`print/`](print/) | Configured H2C projects for the coin, mascot and stand |
| [`models/3mf/`](models/3mf/) | Generic multipart 3MF exports for other printer setups |
| [`models/stl/`](models/stl/) | Color-separated STLs, monochrome alternatives |
| [`sources/`](sources/) | Editable model generator and coin artwork |
| [`docs/`](docs/) | Design preview |
| [`validation/`](validation/) | Geometry and Bambu Studio slicing reports |

For the color-separated STLs, import all parts for a given model together as one multipart object so they stay aligned. Assign each part a filament using the color in its filename. Use the same yellow spool for yellow and yellow-accent parts, and the same navy spool for navy and navy-detail parts. There is no separate gold or black filament. The fused monochrome STLs preserve the body and magnet pocket. Use the multipart models for the raised artwork and yellow stand number.

## Validation and rebuilding

The configured coin and mascot projects were sliced in Bambu Studio with a 0.4 mm nozzle and 0.20 mm layers. Both use a slower top-surface pass for a smoother finish. Coin lettering, duck, footprint and trim rise 0.40 mm above the navy field (two 0.20 mm layers). If navy still tints the lighter colors, check the navy-to-light flushing volumes in your AMS setup. The coin lettering was also checked against the sliced top-layer toolpaths. The geometry checks and slice results are in [`validation/`](validation/). The centered magnet pocket retains the fit tested on an earlier print. Test one assembled set before printing a batch.

To regenerate the generic models and artwork from the repo root:

```sh
python -m pip install -r sources/requirements.txt
python sources/build_models.py
```

The generator writes the generic exports, preview, and geometry report into the repository layout. The configured H2C coin and mascot projects are saved separately and are not rebuilt by this command.
