#!/usr/bin/env python3
"""
ASCII animation player based on the supplied reference video.

Repository setup:
    ascii-cat/
      main.py
      reference.mp4

Install:
    python -m pip install -r requirements.txt

Run:
    python main.py
    python main.py --video reference.mp4 --width 110 --fps 15

The program converts each video frame into colored terminal ASCII. The source
video is needed because it contains the exact sequence of poses/camera moves
shown in the reference.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np


# Characters chosen to echo the reference's repeated-character ASCII style.
# The color is sampled from the source frame; the glyph adds texture/density.
GLYPHS = {
    "white": "@",
    "blue": "$",
    "pink": "@",
    "brown": "$",
    "green": "a",
    "dark": " ",
    "other": "#",
}

RESET = "\033[0m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def classify_color(rgb: np.ndarray) -> str:
    """Classify an RGB pixel into the main colors used by the artwork."""
    r, g, b = (int(v) for v in rgb)

    # Preserve the black background as terminal background.
    if max(r, g, b) < 35:
        return "dark"

    # Pink cheeks/details.
    if r > 105 and r > g * 1.22 and r > b * 1.05 and g > 35:
        return "pink"

    # Blue ears.
    if b > 85 and b > r * 1.12 and b > g * 1.02:
        return "blue"

    # Green foliage.
    if g > 55 and g > r * 1.12 and g > b * 1.05:
        return "green"

    # Warm brown tree stump.
    if r > 75 and g > 35 and r > b * 1.2 and g > b * 1.05:
        return "brown"

    # Cat fur and other light details.
    if max(r, g, b) > 100:
        return "white"

    return "other"


def terminal_size(requested_width: int) -> tuple[int, int]:
    """Return a safe render size, accounting for tall terminal characters."""
    term = shutil.get_terminal_size((120, 45))
    width = max(40, min(requested_width, max(40, term.columns - 1)))
    # A terminal cell is roughly twice as tall as it is wide.
    height = max(18, min(int(width * 0.48), max(18, term.lines - 2)))
    return width, height


def frame_to_ansi(frame: np.ndarray, width: int, height: int) -> str:
    """
    Resize a frame and turn it into ANSI-colored ASCII.

    The original video already contains the ASCII artwork. This samples its
    colors and recreates the same broad palette in a terminal-friendly form.
    """
    # The supplied screen recording is portrait: the artwork occupies the
    # upper ~700 px and the code editor occupies the lower portion. Crop the
    # artwork viewport so the editor is not turned into ASCII.
    h, w = frame.shape[:2]
    if h > 800 and w < h:
        frame = frame[: min(700, h), :, :]

    resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    lines: list[str] = []
    for row in rgb:
        pieces: list[str] = []
        last_color = None
        for pixel in row:
            category = classify_color(pixel)
            if category == "dark":
                if last_color != "dark":
                    pieces.append("\033[0m")
                    last_color = "dark"
                pieces.append(" ")
                continue

            r, g, b = (int(v) for v in pixel)
            color_code = f"\033[38;2;{r};{g};{b}m"
            if color_code != last_color:
                pieces.append(color_code)
                last_color = color_code
            pieces.append(GLYPHS[category])

        pieces.append(RESET)
        lines.append("".join(pieces))

    return "\n".join(lines)


def play(video_path: Path, width: int, fps_override: float | None,
         start: float, end: float | None, loop: bool) -> None:
    if not video_path.is_file():
        raise FileNotFoundError(
            f"Could not find {video_path}. Put the reference video next to "
            "main.py and name it reference.mp4, or pass --video PATH."
        )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open the video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    fps = fps_override if fps_override and fps_override > 0 else source_fps
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / source_fps if source_fps else 0

    start = max(0.0, start)
    stop = duration if end is None else min(duration, max(start, end))
    frame_width, frame_height = terminal_size(width)

    start_frame = int(start * source_fps)
    stop_frame = int(stop * source_fps)

    print(HIDE_CURSOR, end="", flush=True)
    try:
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            frame_number = start_frame
            next_frame_time = time.perf_counter()

            while frame_number < stop_frame:
                ok, frame = cap.read()
                if not ok:
                    break

                art = frame_to_ansi(frame, frame_width, frame_height)
                sys.stdout.write(CLEAR + art)
                sys.stdout.flush()

                frame_number += 1
                next_frame_time += 1.0 / fps
                delay = next_frame_time - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)

            if not loop:
                break
    finally:
        cap.release()
        print(SHOW_CURSOR + RESET, end="", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play the reference cat animation as colored terminal ASCII."
    )
    parser.add_argument(
        "--video", type=Path, default=Path("reference.mp4"),
        help="Path to the reference video (default: reference.mp4)."
    )
    parser.add_argument(
        "--width", type=int, default=110,
        help="ASCII render width in terminal characters (default: 110)."
    )
    parser.add_argument(
        "--fps", type=float, default=None,
        help="Playback frame rate. Defaults to the video's frame rate."
    )
    parser.add_argument(
        "--start", type=float, default=0.0,
        help="Start time in seconds (default: 0)."
    )
    parser.add_argument(
        "--end", type=float, default=None,
        help="Optional end time in seconds."
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Loop the animation continuously."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        play(args.video, args.width, args.fps, args.start, args.end, args.loop)
    except KeyboardInterrupt:
        print(SHOW_CURSOR + RESET)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
