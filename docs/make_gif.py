"""Turn the frames from record_gif.js into figures/explorer.gif."""
import glob
from PIL import Image

ims = [Image.open(f).convert("RGB") for f in sorted(glob.glob("data/gif_frames/f*.png"))]
w, h = ims[0].size
ims = [im.resize((800, int(h * 800 / w)), Image.LANCZOS) for im in ims]
pal = ims[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
# make the lightest palette entry pure white so the background isn't slightly gray
p = q[0].getpalette()
for i in range(len(p) // 3):
    r, g, b = p[3 * i:3 * i + 3]
    if min(r, g, b) >= 245 and max(r, g, b) - min(r, g, b) <= 4:   # near-white grays
        p[3 * i:3 * i + 3] = [255, 255, 255]
for im in q:
    im.putpalette(p)
dur = [140] * len(q); dur[0] = 900; dur[-1] = 2500
q[0].save("figures/explorer.gif", save_all=True, append_images=q[1:], duration=dur, loop=0, optimize=True)
print("figures/explorer.gif written")
