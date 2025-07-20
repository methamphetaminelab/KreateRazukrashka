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
    return DISTINCT_COLORS[(idx-1) % len(DISTINCT_COLORS)]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
                color_map[c] = nxt
                nxt += 1
            pixel_nums.append(color_map[c])

        out_png = Image.new('RGB', (width*cell_size, height*cell_size))
        draw = ImageDraw.Draw(out_png)
        for y in range(height):
            for x in range(width):
                num = pixel_nums[y*width + x]
                fill = get_distinct_color(num)
                x0, y0 = x*cell_size, y*cell_size
                draw.rectangle([x0, y0, x0+cell_size, y0+cell_size], fill=fill)

        buf = BytesIO()
        out_png.save(buf, format='PNG')
        png_b64 = base64.b64encode(buf.getvalue()).decode()

        grid_html = ''
        idx = 0
        for y in range(height):
            grid_html += '<tr>'
            for x in range(width):
                num = pixel_nums[idx]; idx += 1
                orig = list(color_map.keys())[list(color_map.values()).index(num)]
                hexc = '#{:02X}{:02X}{:02X}'.format(*orig)
                grid_html += f'<td style="background:{hexc};">{num}</td>'
            grid_html += '</tr>'

        orig_legend = ''
        for num in sorted(set(pixel_nums)):
            c = list(color_map.keys())[list(color_map.values()).index(num)]
            hexc = '#{:02X}{:02X}{:02X}'.format(*c)
            orig_legend += f'<tr><td>{num}</td><td style="background:{hexc}; width:20px;"></td><td>{hexc}</td><td>{counts[c]}</td></tr>'

        fill_legend = ''
        for num in sorted(set(pixel_nums)):
            fill = get_distinct_color(num)
            fill_legend += f'<tr><td>{num}</td><td style="background:{fill}; width:20px;"></td></tr>'

        return render_template(
            'result.html',
            width=width, height=height, cell_size=cell_size,
            png_b64=png_b64,
            grid_html=grid_html,
            orig_legend=orig_legend,
            fill_legend=fill_legend
        )
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
