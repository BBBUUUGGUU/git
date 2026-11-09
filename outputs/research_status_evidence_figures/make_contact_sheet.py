from pathlib import Path

from PIL import Image, ImageDraw


folder = Path(__file__).parent
files = sorted(
    path
    for path in folder.iterdir()
    if path.suffix.lower() in {".png", ".jpg", ".webp"}
    and path.name != "contact_sheet.jpg"
)

cell_width, cell_height = 440, 280
sheet = Image.new("RGB", (cell_width * 3, cell_height * 3), "white")
draw = ImageDraw.Draw(sheet)

for index, path in enumerate(files):
    image = Image.open(path).convert("RGB")
    image.thumbnail((cell_width - 20, cell_height - 55))
    x = (index % 3) * cell_width + (cell_width - image.width) // 2
    y = (index // 3) * cell_height + 38
    sheet.paste(image, (x, y))
    draw.text(
        ((index % 3) * cell_width + 10, (index // 3) * cell_height + 8),
        path.name[:48],
        fill="black",
    )

sheet.save(folder / "contact_sheet.jpg", quality=95)
