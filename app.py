from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import io
import json
import sqlite

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('drafts.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_name TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

import json

def save_draft_to_db(draft_name, content_dict):
    conn = sqlite3.connect('drafts.db')
    c = conn.cursor()

    # Convert the content dictionary to a JSON string
    json_data = json.dumps(content_dict)

    # Insert the draft data into the database
    c.execute("""
        INSERT INTO drafts (draft_name, data)
        VALUES (?, ?)
        ON CONFLICT(draft_name) DO UPDATE SET data = excluded.data
    """, (draft_name, json_data))

    conn.commit()
    conn.close()

def load_draft_from_db(draft_name):
    conn = sqlite3.connect('drafts.db')
    c = conn.cursor()
    c.execute("SELECT data FROM drafts WHERE draft_name = ?", (draft_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])  # Deserialize the data
    return {}

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
    return len(lines) * line_height

def get_text_height(text, max_width, font_name="Helvetica", font_size=10, line_height=14):
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

@app.route('/')
def form():
    data = {}
    if os.path.exists("saved_draft.json"):
        with open("saved_draft.json", "r") as f:
            data = json.load(f)
    return render_template('form.html', data=data)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()
    action = data.get("action")
    draft_name = data.get("draft_name")  # Get the draft name from the form

    if action == "save":
        if not draft_name:
            return "Please enter a draft name."

        # Save the draft data to the database
        save_draft_to_db(draft_name, data)
        return f"Draft '{draft_name}' saved! You can return later to continue."

    # Header
    p.setFillColorRGB(0.15, 0.18, 0.25)
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 30, "Turning Point for God")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Strategic / Ad hoc Topic Summary")
    logo_path = os.path.join("static", "overlay_icon.png")
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width - 70, height - 60, width=40, height=40, mask='auto')

    p.setFillColor(colors.black)
    y = height - 90

    # Top Fields
    top_fields = [
        ("Topic", data.get("Topic", "")),
        ("Point Person", data.get("PointPerson", "")),
        ("Role of Executive Team", data.get("Role", "")),
        ("Executive Sponsor", data.get("Sponsor", "")),
        ("Problem Definition", data.get("Problem", "")),
        ("Outcome Description", data.get("Outcome", "")),
        ("Primary Recommendation", data.get("Recommendation", ""))
    ]

    for label, val in top_fields:
        box_height = get_text_height(val, width - 100)
        if y - box_height < 60:
            p.showPage()
            y = height - 50
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, label)
        p.rect(50, y - box_height - 5, width - 100, box_height, stroke=1, fill=0)
        p.setFont("Helvetica", 10)
        draw_wrapped_text(p, 55, y - 10, val, width - 110)
        y -= (box_height + 20)

    # Options Table
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Options Table")
    y -= 20

    rows = [
        ("Description", [data.get("Option1Desc", ""), data.get("Option2Desc", ""), data.get("Option3Desc", "")]),
        ("Pros", [data.get("Option1Pros", ""), data.get("Option2Pros", ""), data.get("Option3Pros", "")]),
        ("Cons", [data.get("Option1Cons", ""), data.get("Option2Cons", ""), data.get("Option3Cons", "")]),
        ("Benefit/Revenue", [data.get("Option1Benefit", ""), data.get("Option2Benefit", ""), data.get("Option3Benefit", "")]),
        ("Obstacles", [data.get("Option1Obstacles", ""), data.get("Option2Obstacles", ""), data.get("Option3Obstacles", "")]),
    ]

    col_width = (width - 100) / 4
    first_row_heights = [get_text_height(txt, col_width - 10) for txt in rows[0][1]]
    first_row_height = max(first_row_heights) + 20
    header_row_height = 30

    if y - (first_row_height + header_row_height) < 60:
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 10)
    header_y = y
    p.rect(50, header_y - 20, col_width, 20, stroke=1, fill=0)

    for i, header in enumerate(["Option 1", "Option 2", "Option 3"]):
        x = 50 + col_width * (i + 1)
        p.rect(x, header_y - 20, col_width, 20, stroke=1, fill=0)
        p.drawCentredString(x + col_width / 2, header_y - 15, header)

    y -= 30
    col_w = (width - 100) / 4
    for label, options in rows:
        heights = [get_text_height(txt, col_w - 10) for txt in options]
        row_h = max(heights) + 20

        if y - row_h < 60:
            p.showPage()
            y = height - 50

        p.setFont("Helvetica-Bold", 10)
        p.rect(50, y - row_h, col_w, row_h, stroke=1, fill=0)
        draw_wrapped_text(p, 55, y - 20, label, col_w - 10)

        for i in range(3):
            x = 50 + (i + 1) * col_w
            p.setFont("Helvetica", 10)
            p.rect(x, y - row_h, col_w, row_h, stroke=1, fill=0)
            draw_wrapped_text(p, x + 5, y - 20, options[i], col_w - 10)
        y -= (row_h + 10)

    # Final Decision
    decision = data.get("Decision", "")
    box_height = get_text_height(decision, width - 100)
    if y - box_height < 60:
        p.showPage()
        y = height - 50
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Final Decision")
    p.rect(50, y - box_height - 5, width - 100, box_height, stroke=1, fill=0)
    p.setFont("Helvetica", 10)
    draw_wrapped_text(p, 55, y - 20, decision, width - 110)
    y -= (box_height + 20)

    # Key Actions
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Key Actions:")
    y -= 20

    for i in range(1, 6):
        action = data.get(f"Action{i}", "")
        box_height = get_text_height(action, width - 130)
        if y - box_height < 60:
            p.showPage()
            y = height - 50

        p.setFont("Helvetica-Bold", 10)
        p.drawString(55, y - 15, f"{i}.")

        p.rect(75, y - box_height - 5, width - 120, box_height, stroke=1, fill=0)
        p.setFont("Helvetica", 10)
        draw_wrapped_text(p, 80, y - 20, action, width - 130)
        y -= (box_height + 15)

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Strategic_Topic_Summary.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
