from flask import Flask, request, jsonify
from flask_cors import CORS # Flask-CORS library ko import karein

app = Flask(__name__)

# CORS ko configure karein
# Yeh sabhi origins se requests ki ijazat dega.
# Development ke liye yeh theek hai. Production mein, aapko specific origins set karne chahiye.
# Misal ke taur par:
# CORS(app, resources={r"/*": {"origins": ["https://frontend-henna-nine-34.vercel.app", "http://localhost:5173"]}})
# Jahan "https://frontend-henna-nine-34.vercel.app" aapki Vercel frontend app ka URL hai.
# "http://localhost:5173" local development ke liye hai.
CORS(app)

# Dummy data store karne ke liye (real database ki jagah)
# Production mein aapko MongoDB, PostgreSQL, ya koi aur database use karna hoga.
clients_db = {}
# =============================================================================
# Yahan invoices_db mein abhi dummy data hai.
# Isko theek karne ke liye, aapko asal mein invoices ko database mein save karna hoga.
# =============================================================================
invoices_db = [
    {"invoice_no": "INV-01", "customer_name": "Al Flex Art", "date": "2025-07-22", "total_amount": "4687.50", "remaining_amount": "687.50"},
    {"invoice_no": "INV-02", "customer_name": "Client B", "date": "2025-07-20", "total_amount": "1000.00", "remaining_amount": "0.00"},
    {"invoice_no": "INV-03", "customer_name": "Client A", "date": "2025-07-18", "total_amount": "2500.00", "remaining_amount": "500.00"}
]

# =============================================================================
# Client Management Routes (Jaisa pehle tha)
# =============================================================================

@app.route('/clients', methods=['GET'])
def get_clients():
    """
    Saare clients ki list return karta hai.
    """
    return jsonify(list(clients_db.values()))

@app.route('/save_client', methods=['POST'])
def save_client():
    """
    Naya client add karta hai ya existing client ko update karta hai.
    """
    data = request.get_json()
    name = data.get('name')
    mobile_number = data.get('mobile_number')
    email = data.get('email', '')
    address = data.get('address', '')

    if not name or not mobile_number:
        return jsonify({"message": "Client Name and Mobile Number are required"}), 400

    if mobile_number in clients_db:
        clients_db[mobile_number].update({
            "name": name,
            "email": email,
            "address": address
        })
        return jsonify({"message": "Client updated successfully", "client": clients_db[mobile_number]}), 200
    else:
        new_client = {
            "name": name,
            "mobile_number": mobile_number,
            "email": email,
            "address": address
        }
        clients_db[mobile_number] = new_client
        return jsonify({"message": "Client saved successfully", "client": new_client}), 201

@app.route('/clients/<mobile_number>', methods=['PUT'])
def update_client(mobile_number):
    """
    Existing client ko update karta hai mobile number ke zariye.
    """
    data = request.get_json()
    if mobile_number not in clients_db:
        return jsonify({"message": "Client not found"}), 404

    clients_db[mobile_number].update({
        "name": data.get('name', clients_db[mobile_number]['name']),
        "email": data.get('email', clients_db[mobile_number]['email']),
        "address": data.get('address', clients_db[mobile_number]['address'])
    })
    return jsonify({"message": "Client updated successfully", "client": clients_db[mobile_number]}), 200

@app.route('/clients/<mobile_number>', methods=['DELETE'])
def delete_client(mobile_number):
    """
    Client ko delete karta hai mobile number ke zariye.
    """
    if mobile_number not in clients_db:
        return jsonify({"message": "Client not found"}), 404
    
    del clients_db[mobile_number]
    return jsonify({"message": "Client deleted successfully"}), 200

# =============================================================================
# Invoice Management Routes
# =============================================================================

@app.route('/invoices', methods=['GET'])
@app.route('/dashboard/invoices', methods=['GET']) # Naya route add kiya gaya hai
def get_invoices():
    """
    Invoices ki list return karta hai.
    Agar aap asal invoices save karna chahte hain, to is function ko update karein
    taake woh database se data fetch kare.
    """
    # Abhi yeh dummy data return kar raha hai.
    # Agar aapko asal invoices chahiye, to aapko inko database mein save karna hoga
    # aur phir yahan se fetch karna hoga.
    return jsonify(invoices_db)

@app.route('/save_invoice', methods=['POST'])
def save_invoice():
    """
    Naya invoice save karta hai.
    """
    data = request.get_json()
    # Yahan aap invoice data ko validate aur process kar sakte hain
    # Misal ke taur par: invoice_no, customer_name, items, total_amount, etc.

    # Abhi ke liye, hum sirf data ko invoices_db list mein add kar rahe hain.
    # Asal mein, aapko is data ko database mein save karna hoga.
    invoices_db.append(data)
    return jsonify({"message": "Invoice saved successfully", "invoice": data}), 201


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)
