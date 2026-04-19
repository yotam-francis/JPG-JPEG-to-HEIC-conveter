# photo-to-jpg

Batch photo converter that copies JPG/JPEG files and converts HEIC to JPG into a new output folder. Originals are never touched.

## Requirements

A HEIC converter must be installed (only needed for HEIC conversion):

- **ImageMagick** (recommended): `winget install ImageMagick.ImageMagick` / `brew install imagemagick`
- **libheif** (fallback): provides `heif-convert`

Python 3.9+ (uses `list[str]` type hints).

## Usage

```
python photo_to_jpg.py [input_folder] [options]
```

`input_folder` defaults to the current directory.

### Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output-folder` | `JPG_Output` | Output folder path (relative to input folder or absolute) |
| `--recursive` | off | Process subfolders |
| `--keep-structure` | off | Mirror subfolder structure in output (requires `--recursive`) |
| `--quality` | `92` | JPEG quality 1–100 |
| `--open` | off | Open output folder in File Explorer when done (Windows only) |

### Examples

```bash
# Convert current directory
python photo_to_jpg.py

# Convert specific folder, recursive, preserve structure
python photo_to_jpg.py ~/Photos --recursive --keep-structure -o ~/Photos/JPG

# Flatten all subfolders into one output, quality 85
python photo_to_jpg.py ~/Photos --recursive --quality 85
```

## Behavior

- **JPG/JPEG**: copied as-is, extension normalized to `.jpg`
- **HEIC**: converted to JPG via ImageMagick or `heif-convert`
- **All other files**: ignored
- **Name collisions**: resolved by appending `_1`, `_2`, etc.
- **Flattened subfolders**: files from subdirectories are prefixed with their relative path (e.g., `Trip__IMG_1.jpg`) to avoid collisions

## Converter Priority

1. `magick` (ImageMagick)
2. `heif-convert` (libheif)

If neither is found, the script raises a `RuntimeError` with installation instructions.
