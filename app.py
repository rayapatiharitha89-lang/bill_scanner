from flask import Flask, request, jsonify, render_template
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import uuid
from bill_parser import parse_bill
from database import db, Receipt, ReceiptItem

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

with app.app_context():
    db.create_all()

def preprocess_image(image):
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.LANCZOS)
    image = image.convert('L')
    image = image.filter(ImageFilter.SHARPEN)
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(3.0)
    return image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_bill():
    if 'bill' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['bill']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    ext = os.path.splitext(file.filename)[1] or '.jpg'
    unique_filename = str(uuid.uuid4()) + ext
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    try:
        image = Image.open(filepath)
        processed = preprocess_image(image)
        config = '--oem 3 --psm 6 -l eng'
        extracted_text = pytesseract.image_to_string(processed, config=config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    if not extracted_text.strip():
        return jsonify({'extracted_text': 'No text found!'})
    parsed = parse_bill(extracted_text)
    try:
        total_val = float(parsed['total'].replace(',', '.')) if parsed['total'] else 0.0
    except:
        total_val = 0.0
    existing = Receipt.query.filter_by(
        store_name=parsed['store_name'],
        total=total_val
    ).first()
    if existing:
        return jsonify({
            'extracted_text': extracted_text,
            'parsed': parsed,
            'saved': False,
            'message': 'duplicate'
        })
    receipt = Receipt(
        store_name=parsed['store_name'],
        date=parsed['date'],
        total=total_val,
        raw_text=extracted_text
    )
    db.session.add(receipt)
    db.session.flush()
    for item in parsed['items']:
        try:
            price_val = float(item['price'].replace(',', '.'))
        except:
            price_val = 0.0
        ri = ReceiptItem(
            receipt_id=receipt.id,
            name=item['name'],
            quantity=int(item['quantity']),
            price=price_val
        )
        db.session.add(ri)
    db.session.commit()
    return jsonify({
        'extracted_text': extracted_text,
        'parsed': parsed,
        'saved': True,
        'receipt_id': receipt.id
    })

@app.route('/api/receipts')
def api_receipts():
    receipts = Receipt.query.order_by(Receipt.scanned_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'store_name': r.store_name,
        'date': r.date,
        'total': r.total,
        'scanned_at': r.scanned_at.strftime('%Y-%m-%d %H:%M')
    } for r in receipts])

@app.route('/api/dashboard')
def api_dashboard():
    receipts = Receipt.query.order_by(Receipt.scanned_at.asc()).all()
    line_data = [{
        'date': r.scanned_at.strftime('%d/%m/%Y %H:%M'),
        'total': r.total,
        'store': r.store_name
    } for r in receipts]
    store_totals = {}
    for r in receipts:
        store = r.store_name or 'Unknown'
        store_totals[store] = round(store_totals.get(store, 0) + r.total, 2)
    all_items = ReceiptItem.query.all()
    item_totals = {}
    for item in all_items:
        item_totals[item.name] = round(item_totals.get(item.name, 0) + item.price, 2)
    top_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({
        'line_data': line_data,
        'store_totals': store_totals,
        'top_items': [{'name': k, 'total': v} for k, v in top_items]
    })

@app.route('/api/delete/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    ReceiptItem.query.filter_by(receipt_id=receipt_id).delete()
    db.session.delete(receipt)
    db.session.commit()
    return jsonify({'deleted': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')