from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Strategic / Ad Hoc Topic Summary")
    y -= 30

    # Section 1: Top Fields (before the table)
    p.setFont("Helvetica", 10)
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
        p.drawString(50, y, f"{label}: {val}")
        y -= 20
        if y < 100:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)

    # Section 2: Alternatives Table
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Options Table")
    y -= 20

    p.setFont("Helvetica", 10)
    table_data = [
        ["", "Option 1", "Option 2", "Option 3"],
        ["Description", data.get("Option1Desc", ""), data.get("Option2Desc", ""), data.get("Option3Desc", "")],
        ["Pros", data.get("Option1Pros", ""), data.get("Option2Pros", ""), data.get("Option3Pros", "")],
        ["Cons", data.get("Option1Cons", ""), data.get("Option2Cons", ""), data.get("Option3Cons", "")],
        ["Benefit/Revenue", data.get("Option1Benefit", ""), data.get("Option2Benefit", ""), data.get("Option3Benefit", "")],
        ["Obstacles", data.get("Option1Obstacles", ""), data.get("Option2Obstacles", ""), data.get("Option3Obstacles", "")]
    ]

    row_height = 40
    col_width = 130
    x_start = 50
    table_y = y

    # Track the actual bottom Y after the table
    rows_drawn = len(table_data)
    final_y = table_y - rows_drawn * row_height

    for row_idx, row in enumerate(table_data):
        for col_idx, cell in enumerate(row):
            x = x_start + col_idx * col_width
            y = table_y - row_idx * row_height
            if y < 100:
                p.showPage()
                table_y = height - 50
                y = table_y - row_idx * row_height
                final_y = y
            p.rect(x, y - row_height, col_width, row_height, stroke=1, fill=0)
            p.drawString(x + 5, y - row_height + 25, str(cell))

    # Set Y right below the table
    y = final_y - 30

    # Section 3: Final Decision
    p.setFont("Helvetica", 10)
    decision = data.get("Decision", "")
    p.drawString(50, y, f"Final Decision: {decision}")
    y -= 30

    # Section 4: Key Actions
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
            p.setFont("Helvetica", 10)

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="Strategic_Topic_Summary.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)