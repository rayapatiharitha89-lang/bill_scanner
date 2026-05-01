import re

def parse_bill(text):
    data = {
        "store_name": "Unknown",
        "date": "",
        "total": "0.00",
        "items": []
    }

    lines = text.split("\n")

    for line in lines:
        clean = line.strip()

        # STORE
        if data["store_name"] == "Unknown" and "aldi" in clean.lower():
            data["store_name"] = "ALDI"

        # DATE
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean)
        if date_match:
            data["date"] = date_match.group()

        # TOTAL
        if "total" in clean.lower():
            match = re.search(r'\d+\.\d{2}', clean)
            if match:
                data["total"] = match.group()

        # SKIP unwanted lines
        if any(word in clean.lower() for word in ["total", "tax", "cash", "change", "subtotal"]):
            continue

        # ITEMS
        item_match = re.search(r'^([A-Za-z ]+)\s+(\d+\.\d{2})$', clean)

        if item_match:
            name = item_match.group(1).strip()
            price = item_match.group(2)

            if len(name) > 2:
                data["items"].append({
                    "name": name,
                    "price": price,
                    "quantity": 1
                })

    return data