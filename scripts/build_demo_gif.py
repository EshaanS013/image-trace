"""Assemble Playwright walkthrough frames into a portable animated demo."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frames", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = sorted(args.frames.glob("*.png"))
    if not paths:
        raise SystemExit(f"No PNG frames found in {args.frames}")
    source = [Image.open(path).convert("RGB") for path in paths]
    width = max(image.width for image in source)
    height = max(image.height for image in source)
    frames: list[Image.Image] = []
    for image in source:
        canvas = Image.new("RGB", (width, height), "#0e151c")
        canvas.paste(ImageOps.contain(image, (width, height)), (0, 0))
        frames.append(canvas)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True,
    )
    print(f"wrote {args.output} ({len(frames)} frames, {width}x{height})")


if __name__ == "__main__":
    main()
