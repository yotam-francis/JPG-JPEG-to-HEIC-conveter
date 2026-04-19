#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
from pathlib import Path

JPG_EXTS = {".jpg", ".jpeg"}
HEIC_EXTS = {".heic"}

def ensure_unique_path(path: Path) -> Path:
    """If path exists, add _1, _2, ... before suffix."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def convert_heic(src: Path, dst: Path, quality: int) -> None:
    """
    Try ImageMagick first: magick input.heic -quality 92 output.jpg
    Fallback to libheif tool: heif-convert -q 92 input.heic output.jpg
    """
    # 1) ImageMagick
    try:
        run_cmd(["magick", str(src), "-quality", str(quality), str(dst)])
        return
    except FileNotFoundError:
        pass
    except subprocess.CalledProcessError as e:
        # If magick exists but fails, we'll try fallback.
        pass

    # 2) heif-convert (libheif examples) supports -q QUALITY (0-100). :contentReference[oaicite:2]{index=2}
    try:
        run_cmd(["heif-convert", "-q", str(quality), str(src), str(dst)])
        return
    except FileNotFoundError as e:
        raise RuntimeError(
            "No HEIC converter found.\n"
            "Install ImageMagick (recommended) or install a libheif build that provides heif-convert."
        ) from e
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"Conversion failed for {src.name}:\n{err}") from e

def build_output_name(src: Path, in_dir: Path, flatten: bool) -> str:
    """
    If flattening and the file is in a subfolder, prefix with folder names to reduce collisions.
    Example: Sub\Trip\IMG_1.HEIC -> Sub__Trip__IMG_1.jpg
    """
    rel = src.relative_to(in_dir)
    parents = rel.parts[:-1]
    prefix = "__".join(parents) + "__" if (flatten and parents) else ""
    return prefix + src.stem

def main():
    p = argparse.ArgumentParser(
        description="Create a new folder containing ALL JPGs: copy existing JPG/JPEG and convert HEIC -> JPG (keep originals)."
    )
    p.add_argument("input_folder", nargs="?", default=".", help="Folder containing photos")
    p.add_argument("-o", "--output-folder", default="JPG_Output", help="Output folder name/path")
    p.add_argument("--recursive", action="store_true", help="Include subfolders too")
    p.add_argument("--keep-structure", action="store_true",
                   help="When using --recursive, mirror the folder structure in the output (default: flatten into one folder).")
    p.add_argument("--quality", type=int, default=92, help="JPEG quality 1-100 (default: 92)")
    p.add_argument("--open", action="store_true", help="Open the output folder in File Explorer when done")
    args = p.parse_args()

    in_dir = Path(args.input_folder).expanduser().resolve()
    if not in_dir.exists() or not in_dir.is_dir():
        raise SystemExit(f"Input folder not found or not a directory: {in_dir}")

    out_dir = Path(args.output_folder).expanduser()
    if not out_dir.is_absolute():
        out_dir = (in_dir / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(in_dir.rglob("*")) if args.recursive else list(in_dir.iterdir())
    files = [f for f in files if f.is_file()]

    copied = converted = 0
    for src in files:
        ext = src.suffix.lower()

        # Decide destination subfolder behavior
        if args.recursive and args.keep_structure:
            rel_parent = src.relative_to(in_dir).parent
            dst_parent = out_dir / rel_parent
        else:
            dst_parent = out_dir

        dst_parent.mkdir(parents=True, exist_ok=True)

        if ext in JPG_EXTS:
            # Copy existing JPEG and standardize extension to .jpg
            base = build_output_name(src, in_dir, flatten=not args.keep_structure)
            dst = ensure_unique_path(dst_parent / f"{base}.jpg")
            shutil.copy2(src, dst)
            copied += 1
            print(f"COPY   {src.name} -> {dst.relative_to(out_dir)}")

        elif ext in HEIC_EXTS:
            base = build_output_name(src, in_dir, flatten=not args.keep_structure)
            dst = ensure_unique_path(dst_parent / f"{base}.jpg")
            convert_heic(src, dst, args.quality)
            converted += 1
            print(f"HEIC→JPG {src.name} -> {dst.relative_to(out_dir)}")

    print(f"\nDone.\nOutput: {out_dir}\nCopied JPG/JPEG: {copied}\nConverted HEIC:  {converted}")

    if args.open:
        os.startfile(out_dir)  # Windows only

if __name__ == "__main__":
    main()
