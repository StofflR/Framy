import hitherdither
from PIL import Image

class Device:
    WS7in = "WS7in"
    Inky = "inky"
    Unknown = "unknown"
class Converter:
    
    DESATURATED_PALETTE = [
        [0, 0, 0],
        [255, 255, 255],
        [0, 255, 0],
        [0, 0, 255],
        [255, 0, 0],
        [255, 255, 0],
        [255, 140, 0],
        [255, 255, 255],
    ]

    SATURATED_PALETTE = [
        [57, 48, 57],
        [255, 255, 255],
        [58, 91, 70],
        [61, 59, 94],
        [156, 72, 75],
        [208, 190, 71],
        [177, 106, 73],
        [255, 255, 255],
    ]

    def __init__(self, width, height, image, saturation=0.5, device=Device.WS7in) -> None:
        self.device = device
        self.resolution = (width, height)
        self.image = image
        self.saturation = saturation
        pass

    def _palette_blend(self, dtype="uint8"):
        palette = []
        for i in range(7):
            rs, gs, bs = [c * self.saturation for c in self.SATURATED_PALETTE[i]]
            rd, gd, bd = [
                c * (1.0 - self.saturation) for c in self.DESATURATED_PALETTE[i]
            ]
            if dtype == "uint8":
                palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
            if dtype == "uint24":
                palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
        if dtype == "uint8":
            palette += [255, 255, 255]
        if dtype == "uint24":
            palette += [0xFFFFFF]
        return palette

    def convert(self):
        subprocess.run(["./dither", self.image, "dithered.png"])
        return Image.open("dithered.png").convert("RGB").resize(self.resolution)


    #def convert(self):
    #    # Image size doesn't matter since it's just the palette we're using
    #    # Set our 7 colour palette (+ clear) and zero out the other 247 colours
    #    pallet_blend_waveshare =[0,0,0,  255,255,255,  0,255,0,   0,0,255,  255,0,0,  255,255,0, 255,128,0] + [0,0,0]*249
    #    image_7color = Image.open(self.image).convert("RGB").resize(self.resolution)
    #    # Force source image data to be loaded for `.im` to work
    #    palette = hitherdither.palette.Palette(self._palette_blend("uint24"))
    #    image_dithered = hitherdither.diffusion.error_diffusion_dithering(image_7color, palette, method="stucki", order=3)
    #    if self.device == Device.WS7in:
    #        image_dithered.putpalette(pallet_blend_waveshare)
    #    return image_dithered

if __name__ == "__main__":
    path =  "a colonized moon with rings, digital art.png"
    converter = Converter(800,448,path,0.5, Device.Inky)
    image = converter.convert()
    image.convert("RGB").show()