import re

def clean_store_name(name):
    name = re.sub(r'[^a-zA-Z0-9\s&]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.title()

    corrections = {
        'Almart': 'Walmart',
        'Walmart': 'Walmart',
        'Aldi': 'ALDI',
        'Costco Wholesale': 'Costco',
        'Costco': 'Costco',
        'Mee': 'Costco',
        'Berghotel': 'Berghotel',
    }
    for wrong, correct in corrections.items():
        if wrong.lower() in name.lower():
            return correct
    return name

def parse_bill(text):
    result = {
        'store_name': '',
        'date': '',
        'total': '',
        'items': []
    }

    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    # Store name
    for line in lines:
        clean = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        if len(clean) >= 3:
            result['store_name'] = clean_store_name(line.strip())
            break

    # Date pattern
    date_pattern = r'\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b'
    for line in lines:
        match = re.search(date_pattern, line)
        if match:
            result['date'] = match.group(1)
            break

    # Total pattern - improved
    total_pattern = r'(?i)(total|tot|amount due|subtotal|sum|gesamt|CHF|Tout|Grand Total)[^\d]*(\d+[.,]\d{2})'
    for line in lines:
        match = re.search(total_pattern, line.strip())
        if match:
            result['total'] = match.group(2)
            break

    # Items
    skip_words = ['total', 'subtotal', 'amount', 'cash', 'change',
                  'tax', 'items', 'debit', 'visa', 'approval',
                  'terminal', 'validation', 'payment', 'thank',
                  'customer', 'copy', 'manager', 'save', 'money',
                  'coupon', 'signature', 'trans', 'ref', 'aid']

    walmart_pattern = r'^([A-Z][A-Z0-9\s]{2,}?)\s+\d{9,}\s+(\d+\.\d{2})'
    simple_pattern = r'^([A-Za-z][A-Za-z\s&]{3,}?)\s+(\d+[.,]\d{2})'

    for line in lines:
        low = line.lower()
        if any(skip in low for skip in skip_words):
            continue

        match = re.match(walmart_pattern, line.strip())
        if match:
            name = match.group(1).strip()
            price = match.group(2)
            if float(price) < 200:
                result['items'].append({
                    'quantity': '1',
                    'name': name,
                    'price': price
                })
            continue

        match = re.match(simple_pattern, line.strip())
        if match:
            name = match.group(1).strip()
            price = match.group(2)
            if len(name) > 3 and float(price.replace(',', '.')) < 200:
                result['items'].append({
                    'quantity': '1',
                    'name': name,
                    'price': price
                })

    return result