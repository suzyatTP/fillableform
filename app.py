from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import io

app = Flask(__name__)

def draw_wrapped_text(p, x, y, text, max_width, line_height=14, font_name="Helvetica", font_size=10):
    p.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if p.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for line in lines:
        p.drawString(x, y, line)
        y -= line_height

    return y, len(lines) * line_height

def get_wrapped_text_height(text, max_width, font_name="Helvetica", font_size=10, line_height=14):
    dummy_buffer = io.BytesIO()
    dummy_canvas = canvas.Canvas(dummy_buffer)
    dummy_canvas.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if dummy_canvas.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    return line_height * len(lines)

def draw_wrapped_table(p, table_data, x_start, y, col_width, page_height, line_height=14):
    font_name = "Helvetica"
    font_size = 10
    num_cols = len(table_data[0])

    p.setFont(font_name, font_size)
    for row in table_data:
        # Calculate row height
        cell_heights = []
        for cell in row:
            if cell:
                h = get_wrapped_text_height(cell, col_width - 150, font_name, font_size, line_height)
            else:
                h = line_height
            cell_heights.append(h)
        row_height = max(cell_heights) + 50

        # Page break if needed
        if y - row_height < 50:
            p.showPage()
            y = page_height - 50
            p.setFont(font_name, font_size)

        # Draw row boxes
        for col_idx, cell in enumerate(row):
            x = x_start + col_idx * col_width
            p.rect(x, y - row_height, col_width, row_height)
            text_y = y - 5
            draw_wrapped_text(p, x + 3, text_y, cell, col_width - 6, line_height, font_name, font_size)

        y -= row_height
    return y

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/test')
def test_page():
    return render_template('test.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFillColorRGB(0.15, 0.18, 0.25)
    p.rect(0, height - 60, width, 60, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 30, "Turning Point for God")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 45, "Strategic / Ad hoc Topic Summary")

    logo_path = os.path.join("static", "header_logo.png")
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width - 70, height - 55, width=40, height=40, mask='auto')

    p.setFillColor(colors.black)
    y = height - 80

    # Top Fields
    fields = [
        ("Topic", "Topic"),
        ("PointPerson", "Point Person"),
        ("Role", "Role of Exec Team"),
        ("Sponsor", "Executive Sponsor"),
        ("Problem", "Problem Definition"),
        ("Outcome", "Outcome Description"),
        ("Recommendation", "Primary Recommendation")
    ]

    for key, label in fields:
        val = data.get(key, "")
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, f"{label}:")
        y -= 15
        y, _ = draw_wrapped_text(p, 70, y, val, max_width=450)
        y -= 10
        if y < 100:
            p.showPage()
            y = height - 50

    # Table
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Options Table")
    y -= 20

    table_data = [
        ["", "Option 1", "Option 2", "Option 3"],
        ["Description", data.get("Option1Desc", ""), data.get("Option2Desc", ""), data.get("Option3Desc", "")],
        ["Pros", data.get("Option1Pros", ""), data.get("Option2Pros", ""), data.get("Option3Pros", "")],
        ["Cons", data.get("Option1Cons", ""), data.get("Option2Cons", ""), data.get("Option3Cons", "")],
        ["Benefit/Revenue", data.get("Option1Benefit", ""), data.get("Option2Benefit", ""), data.get("Option3Benefit", "")],
        ["Obstacles", data.get("Option1Obstacles", ""), data.get("Option2Obstacles", ""), data.get("Option3Obstacles", "")]
    ]

    y = draw_wrapped_table(p, table_data, 50, y, col_width=130, page_height=height)

    # Final Decision
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Final Decision:")
    y -= 15
    y, _ = draw_wrapped_text(p, 70, y, data.get("Decision", ""), max_width=450)
    y -= 20

    # Key Actions
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Key Actions:")
    y -= 20
    p.setFont("Helvetica", 10)
    for i in range(1, 6):
        action = data.get(f"Action{i}", "")
        p.drawString(70, y, f"{i}. {action}")
        y -= 15
        if y < 100:
            p.showPage()
            y = height - 50

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Strategic_Topic_Summary.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)