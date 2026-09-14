from PIL import Image, ImageDraw


def droplet_image(size=256, color=(56, 161, 230, 255), highlight=(255, 255, 255, 130)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    top = size * 0.08
    bottom = size * 0.92
    left = size * 0.18
    right = size * 0.82
    mid_y = size * 0.55
    draw.polygon(
        [(size / 2, top), (right, mid_y * 0.95), (size / 2, bottom), (left, mid_y * 0.95)],
        fill=color,
    )
    draw.ellipse((left, mid_y - size * 0.02, right, bottom), fill=color)
    draw.ellipse(
        (size * 0.36, size * 0.42, size * 0.36 + size * 0.16, size * 0.42 + size * 0.16),
        fill=highlight,
    )
    return img


def save_icon_files(assets_dir):
    img = droplet_image()
    png_path = f"{assets_dir}/icon.png"
    ico_path = f"{assets_dir}/icon.ico"
    img.save(png_path)
    img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return png_path, ico_path
