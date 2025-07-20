from flask import Flask, render_template, request
from io import BytesIO
from PIL import Image, ImageDraw
from collections import Counter
import base64

app = Flask(__name__)

DISTINCT_COLORS = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8',
    '#f58231', '#911eb4', '#46f0f0', '#f032e6',
    '#bcf60c', '#fabebe', '#008080', '#e6beff',
    '#9a6324', '#fffac8', '#800000', '#aaffc3',
    '#808000', '#ffd8b1', '#000075', '#808080',
    '#ffffff', '#000000'
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

    # Шаг 1: ресайз оригинала до width×height
    img = Image.open(file).convert('RGB')
    grid = img.resize((width, height), Image.NEAREST)
    pixels = list(grid.getdata())

    # Шаг 2: нумерация цветов
    color_map = {}
    counts = Counter(pixels)
    pixel_nums = []
    nxt = 1
    for c in pixels:
        if c not in color_map:
            color_map[c] = nxt; nxt += 1
        pixel_nums.append(color_map[c])

    # Шаг 3: большой PNG для просмотра (заливка)
    out_large = Image.new('RGB', (width*cell_size, height*cell_size))
    dl = ImageDraw.Draw(out_large)
    for y in range(height):
        for x in range(width):
            num = pixel_nums[y*width + x]
            dl.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size],
                         fill=get_distinct_color(num))
    buf_l = BytesIO()
    out_large.save(buf_l, 'PNG')
    png_b64_large = base64.b64encode(buf_l.getvalue()).decode()

    # Шаг 4: маленький PNG (fill grid) 1×1 клетки для конвертера
    out_small = Image.new('RGB', (width, height))
    ds = ImageDraw.Draw(out_small)
    for y in range(height):
        for x in range(width):
            num = pixel_nums[y*width + x]
            ds.point((x, y), fill=get_distinct_color(num))
    buf_s = BytesIO()
    out_small.save(buf_s, 'PNG')
    png_b64_small = base64.b64encode(buf_s.getvalue()).decode()

    # Подготовка для Jinja: Original Grid + легенды
    grid_rows, idx = [], 0
    for _ in range(height):
        row = []
        for _ in range(width):
            num = pixel_nums[idx]
            orig = list(color_map.keys())[list(color_map.values()).index(num)]
            row.append({'num': num, 'hex': '#%02X%02X%02X' % orig})
            idx += 1
        grid_rows.append(row)

    legend_real = []
    for num in sorted(set(pixel_nums)):
        c = list(color_map.keys())[list(color_map.values()).index(num)]
        legend_real.append({
            'num': num,
            'hex': '#%02X%02X%02X' % c,
            'count': counts[c]
        })

    legend_fill = [{'num': num, 'hex': get_distinct_color(num)} for num in sorted(set(pixel_nums))]

    return render_template('result.html',
        width=width, height=height, cell_size=cell_size,
        png_b64_large=png_b64_large,
        png_b64_small=png_b64_small,
        grid_rows=grid_rows,
        legend_real=legend_real,
        legend_fill=legend_fill
    )

if __name__ == '__main__':
    app.run(debug=True)
