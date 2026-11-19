# Animated ASCII Cat

This project plays the animation from the supplied reference video as colored
ASCII in a terminal. The reference video is required because it supplies the
exact sequence of poses and zooms.

## Files

```text
ascii-cat/
├── main.py
├── requirements.txt
└── reference.mp4   # add your supplied video here
```

## Run locally

1. Put the supplied video in this folder and name it `reference.mp4`.
2. Install Python 3.10+.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run:

   ```bash
   python main.py
   ```

Optional:

```bash
python main.py --width 120 --fps 15 --loop
python main.py --start 4 --end 18
python main.py --video path/to/your-video.mp4
```

## GitHub

Create a repository and upload `main.py`, `requirements.txt`, and
`reference.mp4`. If GitHub rejects the video because it is too large, use
[Git LFS](https://git-lfs.com/) for `reference.mp4`.

**Note:** This recreates the video shown in the reference by converting its
frames into colored terminal ASCII. It is not a reconstruction of the
creator's original hand-authored ASCII source code; that source code is not
legible enough in the screen recording to transcribe reliably.
