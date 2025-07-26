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
        
        # Extract existing invoice numbers that are digits for comparison
        existing_invoice_numbers = [
            inv['invoice_number'] for inv in invoices 
            if 'invoice_number' in inv and isinstance(inv['invoice_number'], str) and inv['invoice_number'].isdigit()
        ]
        
        # Generate a new sequential invoice number if the provided one is a duplicate or missing
        # Also ensure 'total_amount' and 'remaining_balance' are set for new invoices
        if 'invoice_number' not in data or data['invoice_number'] in existing_invoice_numbers:
            # Find the highest existing numeric invoice number
            numeric_invoice_numbers = [int(num) for num in existing_invoice_numbers]
            next_invoice_num = 1
            if numeric_invoice_numbers:
                next_invoice_num = max(numeric_invoice_numbers) + 1
            
            # Format as '01', '02', etc.
            data['invoice_number'] = str(next_invoice_num).zfill(2)
            print(f"Duplicate or missing invoice number detected. Assigning new number: {data['invoice_number']}")

        # Ensure total_amount and remaining_balance are floats and set for new invoices
        data['total_amount'] = float(data.get('total_amount', 0))
        data['remaining_balance'] = float(data.get('remaining_balance', data['total_amount'])) # Default remaining to total if not provided

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

# 💰 Add Payment to Invoice (UPDATED ROUTE)
@app.route('/invoices/<string:invoice_number>/add_payment', methods=['PUT']) # Changed to PUT
def add_payment_to_invoice(invoice_number):
    data = request.get_json()
    payment_amount = float(data.get('amount_paid', 0)) # Changed from 'payment_amount' to 'amount_paid' to match frontend

    if payment_amount <= 0:
        return jsonify({'status': 'error', 'message': 'Payment amount must be positive.'}), 400

    try:
        invoices = load_data(INVOICE_FILE)
        updated_invoice_data = None
        for i, inv in enumerate(invoices):
            if str(inv.get('invoice_number')) == invoice_number:
                current_remaining = float(inv.get('remaining_balance', 0)) # Consistent field name
                
                if current_remaining <= 0:
                    return jsonify({'status': 'error', 'message': 'Invoice is already fully paid.'}), 400
                
                if payment_amount > current_remaining:
                    return jsonify({'status': 'error', 'message': 'Payment amount exceeds remaining balance.'}), 400

                inv['remaining_balance'] = round(current_remaining - payment_amount, 2)
                updated_invoice_data = inv # Store the updated invoice
                break
        
        if updated_invoice_data:
            save_data(invoices, INVOICE_FILE)
            return jsonify(updated_invoice_data), 200 # Return the updated invoice object
        else:
            return jsonify({'status': 'error', 'message': f'Invoice {invoice_number} not found.'}), 404
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid payment amount format.'}), 400
    except Exception as e:
        print(f"Error adding payment: {e}")
        return jsonify({'error': str(e)}), 500


# 👥 Save client
@app.route('/save_client', methods=['POST'])
def save_client():
    data = request.get_json()
    try:
        clients = load_data(CLIENT_FILE)
        
        # Check for duplicate client by mobile number
        if any(client.get('mobile_number') == data.get('mobile_number') for client in clients):
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

# ✨ Get Dashboard Summary
@app.route('/dashboard_summary', methods=['GET']) # Frontend Dashboard Overview is likely calling this
@app.route('/invoice_summary', methods=['GET']) # Added for flexibility if frontend uses this
def get_dashboard_summary():
    try:
        invoices = load_data(INVOICE_FILE)
        clients = load_data(CLIENT_FILE) # Load clients data
        
        total_invoices = len(invoices)
        total_clients = len(clients) # Calculate total clients
        
        total_amount_all_invoices = sum(float(inv.get('total_amount', 0)) for inv in invoices if inv.get('total_amount') is not None)
        # Corrected: Use 'remaining_balance' for unpaid amount calculation
        total_unpaid_amount = sum(float(inv.get('remaining_balance', 0)) for inv in invoices if inv.get('remaining_balance') is not None)
        
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
