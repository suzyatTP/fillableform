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

def draw_labeled_box(p, x, y, label, value, width, page_height, font_size=10):
    p.setFont("Helvetica-Bold", font_size)
    label_height = get_wrapped_text_height(label, width - 10)
    value_height = get_wrapped_text_height(value, width - 10)
    total_height = label_height + value_height + 10

    if y - total_height < 50:
        p.showPage()
        y = page_height - 50

    p.rect(x, y - total_height, width, total_height)
    y1, _ = draw_wrapped_text(p, x + 5, y - 5, label, max_width=width - 10)
    draw_wrapped_text(p, x + 5, y1 - 5, value, max_width=width - 10)
    return y - total_height - 10

def draw_wrapped_table(p, table_data, x_start, y, col_widths, page_height, line_height=14):
    font_name = "Helvetica"
    font_size = 10
    p.setFont(font_name, font_size)

    for row in table_data:
        cell_heights = []
        for col_idx, cell in enumerate(row):
            width = col_widths[col_idx]
            h = get_wrapped_text_height(cell, width - 6, font_name, font_size, line_height)
            cell_heights.append(h)

        row_height = max(cell_heights) + 10

        if y - row_height < 50:
            p.showPage()
            y = page_height - 50
            p.setFont(font_name, font_size)

        for col_idx, cell in enumerate(row):
            x = x_start + sum(col_widths[:col_idx])
            width = col_widths[col_idx]
            p.rect(x, y - row_height, width, row_height)
            draw_wrapped_text(p, x + 3, y - 5, cell, max_width=width - 6, line_height=line_height, font_name=font_name, font_size=font_size)

        y -= row_height
    return y

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFillColorRGB(0.15, 0.18, 0.25)
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 30, "Turning Point for God")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Strategic / Ad hoc Topic Summary")

    logo_path = os.path.join("static", "header_logo.png")
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width - 70, height - 60, width=40, height=40, mask='auto')

    p.setFillColor(colors.black)
    y = height - 90

    # Labeled Top Boxes
    top_fields = [
        ("Topic", data.get("Topic", "")),
        ("Point Person", data.get("PointPerson", "")),
        ("Role of Exec Team", data.get("Role", "")),
        ("Executive Sponsor", data.get("Sponsor", "")),
        ("Problem Definition", data.get("Problem", "")),
        ("Outcome Description", data.get("Outcome", "")),
        ("Primary Recommendation", data.get("Recommendation", ""))
    ]

    for label, value in top_fields:
        y = draw_labeled_box(p, 50, y, label, value, width=500, page_height=height)

    # Options Table
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

    col_widths = [120, 130, 130, 130]
    y = draw_wrapped_table(p, table_data, 50, y, col_widths=col_widths, page_height=height)

    # Final Decision Box
    p.setFont("Helvetica-Bold", 10)
    y -= 10
    y = draw_labeled_box(p, 50, y, "Final Decision", data.get("Decision", ""), width=500, page_height=height)

    # Key Actions
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Key Actions:")
    y -= 20
    p.setFont("Helvetica", 10)
    for i in range(1, 6):
        action = data.get(f"Action{i}", "")
        y, _ = draw_wrapped_text(p, 70, y, f"{i}. {action}", max_width=450)
        y -= 5
        if y < 100:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Strategic_Topic_Summary.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)