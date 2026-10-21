"""Turn the frames from record_gif.js into figures/explorer.gif."""
import glob
from PIL import Image

ims = [Image.open(f).convert("RGB") for f in sorted(glob.glob("data/gif_frames/f*.png"))]
w, h = ims[0].size
ims = [im.resize((800, int(h * 800 / w)), Image.LANCZOS) for im in ims]
pal = ims[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
dur = [140] * len(q); dur[0] = 900; dur[-1] = 2500
q[0].save("figures/explorer.gif", save_all=True, append_images=q[1:], duration=dur, loop=0, optimize=True)
print("figures/explorer.gif written")
