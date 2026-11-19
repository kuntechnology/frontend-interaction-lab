#!/usr/bin/env python3
"""Generate original abstract, silent looping media assets with Pillow and local ffmpeg."""
from pathlib import Path
import math
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "media"
W, H, FPS, FRAMES = 320, 180, 12, 36
BG = (10, 18, 22)
LIME = (190, 242, 94)
TEAL = (53, 169, 157)
PALE = (219, 240, 206)


def canvas(phase):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            t = y / H
            px[x, y] = (int(9 + 8*t), int(17 + 12*t), int(23 + 13*t))
    return im


def connection(i):
    p = i / FRAMES * math.tau
    im = canvas(p)
    d = ImageDraw.Draw(im, "RGBA")
    # Calm, broad atmospheric orbit rings; pulse is slow and low contrast.
    for rad, alpha in ((59, 34), (47, 49), (35, 70)):
        r = rad + 1.4 * math.sin(p)
        d.ellipse((160-r, 89-r, 160+r, 89+r), outline=(*TEAL, alpha), width=1)
    # Three abstract network nodes with gently moving signal arcs.
    nodes = [(160, 89), (101, 61), (219, 117)]
    d.line((nodes[1], nodes[0], nodes[2]), fill=(*TEAL, 125), width=2)
    for j, (x, y) in enumerate(nodes):
        r = 9 if j == 0 else 6
        d.ellipse((x-r-4, y-r-4, x+r+4, y+r+4), fill=(*LIME, 24))
        d.ellipse((x-r, y-r, x+r, y+r), fill=BG, outline=(*LIME, 210), width=2)
        d.ellipse((x-2, y-2, x+2, y+2), fill=(*PALE, 235))
    # A traveling dot glides between the nodes as a visual connection signal.
    t = (i / FRAMES)
    if t < .5:
        q = t * 2
        x, y = nodes[1][0]*(1-q)+160*q, nodes[1][1]*(1-q)+89*q
    else:
        q = (t-.5)*2
        x, y = 160*(1-q)+nodes[2][0]*q, 89*(1-q)+nodes[2][1]*q
    d.ellipse((x-3, y-3, x+3, y+3), fill=(*LIME, 245))
    # Minimal quiet corner ticks frame the abstract signal.
    for x, y, sx, sy in ((20,20,1,1),(300,20,-1,1),(20,160,1,-1),(300,160,-1,-1)):
        d.line((x,y,x+sx*10,y), fill=(*TEAL,75), width=1)
        d.line((x,y,x,y+sy*10), fill=(*TEAL,75), width=1)
    return im


def play(i):
    p = i / FRAMES * math.tau
    im = canvas(p)
    d = ImageDraw.Draw(im, "RGBA")
    # Original layered geometric hills, gently shifted for seamless motion.
    shift = 2 * math.sin(p)
    d.polygon([(0,111),(45,68),(82,104),(126,52),(185,113),(231,72),(320,116),(320,180),(0,180)], fill=(29,72,72,255))
    d.polygon([(0,129),(55,94),(104,130),(163,79),(221,129),(275,98),(320,122),(320,180),(0,180)], fill=(22,54,58,255))
    d.polygon([(0,146),(70,118),(126,148),(196,110),(254,150),(320,121),(320,180),(0,180)], fill=(17,39,44,255))
    # Restrained lime ridge highlights.
    d.line([(44,69),(82,104),(126,52),(185,113)], fill=(*LIME,135), width=1)
    d.line([(231,72),(266,97),(286,105)], fill=(*TEAL,145), width=1)
    # Center reticle with a tiny slow breathing scale, no sharp flashes.
    cx, cy = 160 + shift, 91
    r = 12 + math.sin(p)*1.2
    d.ellipse((cx-r,cy-r,cx+r,cy+r), outline=(*LIME,190), width=1)
    d.line((cx-19,cy,cx-7,cy), fill=(*PALE,185), width=1)
    d.line((cx+7,cy,cx+19,cy), fill=(*PALE,185), width=1)
    d.line((cx,cy-19,cx,cy-7), fill=(*PALE,185), width=1)
    d.line((cx,cy+7,cx,cy+19), fill=(*PALE,185), width=1)
    d.ellipse((cx-2,cy-2,cx+2,cy+2), fill=(*LIME,225))
    # Abstract handheld interface controls, decorative and unbranded.
    d.rounded_rectangle((17,139,47,163), radius=7, outline=(*TEAL,150), width=1)
    d.line((24,151,40,151), fill=(*PALE,170), width=2)
    d.line((32,143,32,159), fill=(*PALE,170), width=2)
    for x,y in ((278,147),(289,141),(289,153)):
        d.ellipse((x-3,y-3,x+3,y+3), fill=(*LIME,160))
    d.rounded_rectangle((260,132,303,164), radius=11, outline=(*TEAL,95), width=1)
    # Small quiet HUD marks.
    d.line((18,23,56,23), fill=(*TEAL,100), width=1)
    d.line((264,23,302,23), fill=(*TEAL,100), width=1)
    return im


def encode(name, draw):
    dest = OUT / name
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "42", "-deadline", "good", "-cpu-used", "4", "-row-mt", "1", "-pix_fmt", "yuv420p", "-g", str(FRAMES), "-auto-alt-ref", "0", "-f", "webm", str(dest)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(FRAMES):
            proc.stdin.write(draw(i).tobytes())
        proc.stdin.close()
        code = proc.wait()
    except Exception:
        proc.kill()
        raise
    if code:
        raise SystemExit(f"ffmpeg failed while encoding {name}: {code}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    encode("connect.webm", connection)
    encode("play.webm", play)
    (OUT / "remote-zh.vtt").write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:01.500\n连接状态示意\n\n00:00:01.500 --> 00:00:03.000\n画面为原创概念图形\n",
        encoding="utf-8",
    )
    print(f"Generated assets in {OUT}")

if __name__ == "__main__":
    main()
