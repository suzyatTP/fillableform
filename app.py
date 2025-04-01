from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import io

app = Flask(__name__)

def draw_wrapped_text(p, x, y, text, max_width, font_name="Helvetica", font_size=10, line_height=14):
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

def get_text_box_height(text, max_width, font_name="Helvetica", font_size=10, line_height=14):
    dummy = canvas.Canvas(io.BytesIO())
    dummy.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if dummy.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return line_height * len(lines) + 10

def draw_labeled_box(p, x, y, width, label, text, page_height):
    height = get_text_box_height(text, width - 10)
    if y - height < 50:
        p.showPage()
        y = page_height - 50

    p.setFont("Helvetica-Bold", 10)
    p.drawString(x + 5, y - 15, label)
    p.rect(x, y - height, width, height, stroke=1, fill=0)
    p.setFont("Helvetica", 10)
    draw_wrapped_text(p, x + 5, y - 30, text, width - 10)
    return y - height - 10

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- HEADER ---
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

    # --- TOP FIELDS ---
    top_fields = [
        ("Topic", data.get("Topic", "")),
        ("Point Person", data.get("PointPerson", "")),
        ("Role of Exec Team", data.get("Role", "")),
        ("Executive Sponsor", data.get("Sponsor", "")),
        ("Problem Definition", data.get("Problem", "")),
        ("Outcome Description", data.get("Outcome", "")),
        ("Primary Recommendation", data.get("Recommendation", ""))
    ]

    for label, text in top_fields:
        y = draw_labeled_box(p, 50, y, width - 100, label, text, height)

    # --- OPTIONS TABLE ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Options Table")
    y -= 20

    option_rows = [
        ("Description", [data.get("Option1Desc", ""), data.get("Option2Desc", ""), data.get("Option3Desc", "")]),
        ("Pros", [data.get("Option1Pros", ""), data.get("Option2Pros", ""), data.get("Option3Pros", "")]),
        ("Cons", [data.get("Option1Cons", ""), data.get("Option2Cons", ""), data.get("Option3Cons", "")]),
        ("Benefit/Revenue", [data.get("Option1Benefit", ""), data.get("Option2Benefit", ""), data.get("Option3Benefit", "")]),
        ("Obstacles", [data.get("Option1Obstacles", ""), data.get("Option2Obstacles", ""), data.get("Option3Obstacles", "")]),
    ]

    col_width = (width - 100) / 3
    for label, values in option_rows:
        for i in range(3):
            y = draw_labeled_box(p, 50 + i * col_width, y, col_width - 5, label if i == 0 else "", values[i], height)

    # --- FINAL DECISION ---
    y = draw_labeled_box(p, 50, y, width - 100, "Final Decision", data.get("Decision", ""), height)

    # --- KEY ACTIONS ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Key Actions:")
    y -= 20
    for i in range(1, 6):
        action = data.get(f"Action{i}", "")
        y = draw_labeled_box(p, 70, y, width - 120, f"{i}.", action, height)

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Strategic_Topic_Summary.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)