from flask import Flask, render_template, request
import os
import easyocr

app = Flask(__name__)

# Create uploads folder if not exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load EasyOCR (only once)
reader = easyocr.Reader(['en'], gpu=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    # Save image
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    print("Saved file:", filepath)

    # OCR
    result = reader.readtext(filepath, detail=0)
    print("OCR RESULT:", result)

    if not result:
        return "No text detected ❌"

    # Show result
    return "<br>".join(result)


if __name__ == '__main__':
    app.run(debug=True)