"""Turns script.yaml into: AI image/video prompt sheet, storyboard, SRT subtitles and a vertical MP4.
Placeholder frames are drawn locally; for a client, drop the AI-generated images into frames/scene_N.png
(Midjourney / DALL·E / Flux / Runway) and re-run, and add the voice-over track with --audio vo.mp3."""
import subprocess, sys, pathlib, yaml
from PIL import Image, ImageDraw, ImageFont
D = pathlib.Path(__file__).parent; S = yaml.safe_load((D/"script.yaml").read_text(encoding="utf-8"))
W, H, FPS = S["format"]["width"], S["format"]["height"], S["format"]["fps"]; B = S["brand"]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
fr = D/"frames"; fr.mkdir(exist_ok=True)
hexrgb = lambda h: tuple(int(h[i:i+2], 16) for i in (1, 3, 5))

def placeholder(sc):
    p = fr/f"scene_{sc['id']}.png"
    if p.exists() and "--fresh" not in sys.argv: return p
    im = Image.new("RGB", (W, H), hexrgb(B["bg"])); d = ImageDraw.Draw(im)
    d.ellipse((W*.1, H*.18, W*.9, H*.18 + W*.8), fill=hexrgb(B["accent"]))
    d.rounded_rectangle((W*.25, H*.27, W*.75, H*.27 + W*.5), 40, fill=hexrgb(B["primary"]))
    d.text((W/2, H*.27 + W*.25), f"SCENE {sc['id']}", font=ImageFont.truetype(F, 96), fill="white", anchor="mm")
    import textwrap
    d.multiline_text((W/2, H*.07), "AI image slot\n" + "\n".join(textwrap.wrap(sc["image_prompt"], 48)[:3]), font=ImageFont.truetype(F, 30),
                     fill=(130, 130, 130), anchor="ma", align="center", spacing=8)
    im.save(p); return p

def caption_png(sc):
    im = Image.new("RGBA", (W, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype(F, 72)
    words, lines, cur = sc["caption"].split(), [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=f) > W * .82: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    lines.append(cur); txt = "\n".join(lines)
    box = d.multiline_textbbox((W/2, 180), txt, font=f, anchor="mm", align="center", spacing=14)
    d.rounded_rectangle((box[0]-40, box[1]-30, box[2]+40, box[3]+30), 36, fill=(*hexrgb(B["primary"]), 235))
    d.multiline_text((W/2, 180), txt, font=f, fill="white", anchor="mm", align="center", spacing=14)
    p = fr/f"cap_{sc['id']}.png"; im.save(p); return p

MOTION = {"slow zoom in": "zoompan=z='min(zoom+0.0009,1.12)':d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
          "slow zoom out": "zoompan=z='if(eq(on,0),1.12,max(zoom-0.0009,1))':d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
          "pan right": "zoompan=z=1.1:d={n}:x='(iw-iw/zoom)*on/{n}':y='ih/2-(ih/zoom/2)'",
          "pan left": "zoompan=z=1.1:d={n}:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'",
          "static": "zoompan=z=1:d={n}"}
clips, t, srt = [], 0.0, []
ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x%1*1000):03d}"
for sc in S["scenes"]:
    n = int(sc["seconds"] * FPS); img, cap = placeholder(sc), caption_png(sc); out = fr/f"clip_{sc['id']}.mp4"
    vf = f"[0:v]scale={W*2}:{H*2},{MOTION[sc['motion']].format(n=n)}:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.3[v];[v][1:v]overlay=0:H-h-260[o]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img), "-i", str(cap), "-filter_complex", vf, "-map", "[o]",
                    "-t", str(sc["seconds"]), "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", str(out)], check=True)
    clips.append(out); srt.append(f"{sc['id']}\n{ts(t)} --> {ts(t+sc['seconds'])}\n{sc['voiceover']}\n"); t += sc["seconds"]
(fr/"list.txt").write_text("".join(f"file '{c.name}'\n" for c in clips))
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(fr/"list.txt")]
if "--audio" in sys.argv: cmd += ["-i", sys.argv[sys.argv.index("--audio") + 1], "-shortest", "-c:a", "aac"]
subprocess.run(cmd + ["-c:v", "copy", str(D/"reel.mp4")], check=True)
(D/"subtitles_tr.srt").write_text("\n".join(srt), encoding="utf-8")
sheet = [f"# Production sheet: {S['title']}\n", f"Format {W}×{H} · {t:.1f}s · voice: {S['voice']}\n",
         "| # | Sec | On-screen caption | Voice-over (TR) | Image prompt (Midjourney/Flux/DALL·E) | Motion |", "|---|---|---|---|---|---|"]
sheet += [f"| {s['id']} | {s['seconds']} | {s['caption']} | {s['voiceover']} | `{s['image_prompt']} --ar 9:16` | {s['motion']} |" for s in S["scenes"]]
(D/"PRODUCTION_SHEET.md").write_text("\n".join(sheet), encoding="utf-8")
# storyboard contact sheet
thumbs = [Image.open(fr/f"scene_{s['id']}.png").convert("RGB").resize((216, 384)) for s in S["scenes"]]
cs = Image.new("RGB", (216*len(thumbs) + 20*(len(thumbs)+1), 384 + 40), "white")
for i, th in enumerate(thumbs):
    th = th.copy(); ov = Image.open(fr/f"cap_{S['scenes'][i]['id']}.png").resize((216, 72)); th.paste(ov, (0, 384-72-52), ov); cs.paste(th, (20 + i*236, 20))
cs.save(D/"storyboard.png"); print(f"reel.mp4 ({t:.1f}s), storyboard.png, subtitles_tr.srt, PRODUCTION_SHEET.md")
