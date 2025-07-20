from flask import Flask, render_template, request
from io import BytesIO
from PIL import Image, ImageDraw
from collections import Counter
import base64

app = Flask(__name__)

# Палитра заливки PNG
DISTINCT_COLORS = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0',
    '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8',
    '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000'
]

def get_distinct_color(idx):
    return DISTINCT_COLORS[(idx - 1) % len(DISTINCT_COLORS)]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    file = request.files['image']
    width = int(request.form['width'])
    height = int(request.form['height'])
    cell_size = int(request.form['cell_size'])

    img = Image.open(file).convert('RGB')
    grid = img.resize((width, height), Image.NEAREST)
    pixels = list(grid.getdata())

    color_map = {}
    counts = Counter(pixels)
    pixel_nums = []
    nxt = 1
    for c in pixels:
        if c not in color_map:
            color_map[c] = nxt; nxt += 1
        pixel_nums.append(color_map[c])

    # PNG fill-only
    out = Image.new('RGB', (width * cell_size, height * cell_size))
    draw = ImageDraw.Draw(out)
    for y in range(height):
        for x in range(width):
            num = pixel_nums[y * width + x]
            draw.rectangle([
                x * cell_size, y * cell_size,
                (x + 1) * cell_size, (y + 1) * cell_size
            ], fill=get_distinct_color(num))
    buf = BytesIO()
    out.save(buf, 'PNG')
    png_b64 = base64.b64encode(buf.getvalue()).decode()

    # Подготовка данных для шаблона
    grid_rows = []
    idx = 0
    for _ in range(height):
        row = []
        for _ in range(width):
            num = pixel_nums[idx]
            orig = list(color_map.keys())[list(color_map.values()).index(num)]
            hexc = '#{:02X}{:02X}{:02X}'.format(*orig)
            row.append({'num': num, 'hex': hexc})
            idx += 1
        grid_rows.append(row)

    legend_real = []
    for num in sorted(set(pixel_nums)):
        orig = list(color_map.keys())[list(color_map.values()).index(num)]
        hexc = '#{:02X}{:02X}{:02X}'.format(*orig)
        legend_real.append({'num': num, 'hex': hexc, 'count': counts[orig]})

    legend_fill = []
    for num in sorted(set(pixel_nums)):
        legend_fill.append({'num': num, 'hex': get_distinct_color(num)})

    return render_template(
        'result.html', width=width, height=height,
        cell_size=cell_size, png_b64=png_b64,
        grid_rows=grid_rows,
        legend_real=legend_real, legend_fill=legend_fill
    )

if __name__ == '__main__':
    app.run(debug=True)
