from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

INVOICE_FILE = 'invoices.json'
CLIENT_FILE = 'clients.json'

# 🔧 Ensure files exist
for file in [INVOICE_FILE, CLIENT_FILE]:
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump([], f)

# --- Helper to load and save data ---
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                if content:
                    return json.loads(content)
                return []
            except json.JSONDecodeError:
                print(f"Warning: {filename} is corrupted or empty. Starting with empty list.")
                return []
    return []

def save_data(data_list, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2)

# 🧾 Save invoice
@app.route('/save_invoice', methods=['POST'])
def save_invoice():
    data = request.get_json()
    try:
        invoices = load_data(INVOICE_FILE)
        
        # Check if invoice_number exists and is a digit string before converting to int
        invoice_numbers = [int(inv['invoice_number']) for inv in invoices if isinstance(inv.get('invoice_number'), str) and inv['invoice_number'].isdigit()]
        
        # If the invoice number from the new data already exists, assign a new one
        if data.get('invoice_number') in [inv['invoice_number'] for inv in invoices]:
            new_invoice_num = str(max(invoice_numbers) + 1).zfill(2) if invoice_numbers else '01'
            data['invoice_number'] = new_invoice_num
            print(f"Duplicate invoice number detected. Assigning new number: {new_invoice_num}")

        invoices.append(data)
        save_data(invoices, INVOICE_FILE)
        return jsonify({'status': 'success', 'message': 'Invoice saved successfully!', 'invoice_number': data.get('invoice_number')}), 200
    except Exception as e:
        print(f"Error saving invoice: {e}")
        return jsonify({'error': str(e)}), 500

# 📁 Get all invoices
@app.route('/invoices', methods=['GET'])
@app.route('/dashboard/invoices', methods=['GET']) # Frontend calls this for Saved Invoices
def get_all_invoices():
    try:
        invoices = load_data(INVOICE_FILE)
        return jsonify(invoices), 200
    except Exception as e:
        print(f"Error getting invoices: {e}")
        return jsonify({'error': str(e)}), 500

# 🗑️ Delete invoice
@app.route('/invoices/<string:invoice_number>', methods=['DELETE'])
def delete_invoice(invoice_number):
    try:
        invoices = load_data(INVOICE_FILE)
        initial_length = len(invoices)
        
        updated_invoices = [inv for inv in invoices if str(inv.get('invoice_number')) != invoice_number]
        
        if len(updated_invoices) < initial_length:
            save_data(updated_invoices, INVOICE_FILE)
            return jsonify({'status': 'success', 'message': f'Invoice {invoice_number} deleted.'}), 200
        else:
            return jsonify({'status': 'error', 'message': f'Invoice {invoice_number} not found.'}), 404
    except Exception as e:
        print(f"Error deleting invoice: {e}")
        return jsonify({'error': str(e)}), 500

# 👥 Save client
@app.route('/save_client', methods=['POST'])
def save_client():
    data = request.get_json()
    try:
        clients = load_data(CLIENT_FILE)
        
        # Check for duplicate client by mobile number
        if any(client['mobile_number'] == data['mobile_number'] for client in clients):
            return jsonify({'status': 'error', 'message': 'Client with this mobile number already exists.'}), 409 # Conflict

        clients.append(data)
        save_data(clients, CLIENT_FILE)
        return jsonify({'status': 'success', 'message': 'Client added successfully!'}), 200
    except Exception as e:
        print(f"Error saving client: {e}")
        return jsonify({'error': str(e)}), 500

# ✨ Get all clients
@app.route('/clients', methods=['GET'])
def get_clients():
    try:
        clients = load_data(CLIENT_FILE)
        return jsonify(clients), 200
    except Exception as e:
        print(f"Error getting clients: {e}")
        return jsonify({'error': str(e)}), 500

# ✨ Delete client by mobile number
@app.route('/clients/<string:mobile_number>', methods=['DELETE'])
def delete_client(mobile_number):
    try:
        clients = load_data(CLIENT_FILE)
        initial_length = len(clients)
        
        updated_clients = [client for client in clients if client.get('mobile_number') != mobile_number]
        
        if len(updated_clients) < initial_length:
            save_data(updated_clients, CLIENT_FILE)
            return jsonify({'status': 'success', 'message': f'Client with mobile number {mobile_number} deleted.'}), 200
        else:
            return jsonify({'status': 'error', 'message': f'Client with mobile number {mobile_number} not found.'}), 404
    except Exception as e:
        print(f"Error deleting client: {e}")
        return jsonify({'error': str(e)}), 500

# ✨ Update client by mobile number
@app.route('/clients/<string:mobile_number>', methods=['PUT'])
def update_client(mobile_number):
    data = request.get_json()
    try:
        clients = load_data(CLIENT_FILE)
        found = False
        for i, client in enumerate(clients):
            if client.get('mobile_number') == mobile_number:
                clients[i] = {**client, **data} # Update existing client with new data
                found = True
                break
        
        if found:
            save_data(clients, CLIENT_FILE)
            return jsonify({'status': 'success', 'message': f'Client with mobile number {mobile_number} updated.'}), 200
        else:
            return jsonify({'status': 'error', 'message': f'Client with mobile number {mobile_number} not found.'}), 404
    except Exception as e:
        print(f"Error updating client: {e}")
        return jsonify({'error': str(e)}), 500

# ✨ Get Invoice Summary (UPDATED to include total clients)
@app.route('/dashboard_summary', methods=['GET']) # Frontend Dashboard Overview is likely calling this
@app.route('/invoice_summary', methods=['GET']) # Added for flexibility if frontend uses this
def get_dashboard_summary():
    try:
        invoices = load_data(INVOICE_FILE)
        clients = load_data(CLIENT_FILE) # Load clients data
        
        total_invoices = len(invoices)
        total_clients = len(clients) # Calculate total clients
        
        total_amount_all_invoices = sum(float(inv.get('total_amount', 0)) for inv in invoices if inv.get('total_amount') is not None)
        total_unpaid_amount = sum(float(inv.get('remaining_amount', 0)) for inv in invoices if inv.get('remaining_amount') is not None)
        
        summary = {
            "total_clients": total_clients,
            "total_invoices": total_invoices,
            "total_paid_amount": round(total_amount_all_invoices - total_unpaid_amount, 2), # Paid amount calculation
            "total_unpaid_amount": round(total_unpaid_amount, 2)
        }
        return jsonify(summary), 200
    except Exception as e:
        print(f"Error getting invoice summary: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)