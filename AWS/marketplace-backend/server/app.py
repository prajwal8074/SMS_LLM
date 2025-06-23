from flask import Flask, request, jsonify
import uuid
from database import get_db_connection
import json # Import json for parsing internal arguments if needed, though not directly in this server logic

app = Flask(__name__)

# Dummy functions that interact with the PostgreSQL database
# These mirror the tool definitions you provided earlier.

@app.route('/add_listing', methods=['POST'])
def add_listing():
    """API endpoint to add a new item listing."""
    data = request.json
    item_name = data.get('item_name')
    price = data.get('price')
    description = data.get('description')

    if not item_name or price is None:
        return jsonify({"error": "item_name and price are required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Generate UUID in Python, or let DB handle it with DEFAULT gen_random_uuid()
        # For this example, we'll let the DB handle it for simplicity
        cur.execute(
            """
            INSERT INTO listings (item_name, price, description, status)
            VALUES (%s, %s, %s, 'active')
            RETURNING id;
            """,
            (item_name, price, description)
        )
        new_listing_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Listing for '{item_name}' added.", "listing_id": str(new_listing_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sell_item', methods=['POST'])
def sell_item():
    """API endpoint to mark an existing item listing as sold."""
    data = request.json
    listing_id = data.get('listing_id')
    buyer_id = data.get('buyer_id') # Optional

    if not listing_id:
        return jsonify({"error": "listing_id is required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE listings
            SET status = 'sold', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'active'
            RETURNING id, item_name;
            """,
            (listing_id,)
        )
        updated_row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if updated_row:
            return jsonify({"status": "success", "message": f"Listing '{listing_id}' for '{updated_row[1]}' marked as sold.", "buyer_id": buyer_id}), 200
        else:
            return jsonify({"status": "not_found", "message": f"Listing '{listing_id}' not found or already sold."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_all_listings', methods=['GET'])
def get_all_listings():
    """API endpoint to retrieve all active item listings."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, item_name, price, description, status FROM listings WHERE status = 'active' ORDER BY created_at DESC;")
        columns = [col[0] for col in cur.description]
        listings = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()

        # Convert UUID objects to strings for JSON serialization
        for listing in listings:
            if 'id' in listing:
                listing['id'] = str(listing['id'])
            if 'price' in listing:
                listing['price'] = float(listing['price']) # Convert Decimal to float for JSON

        return jsonify({"status": "success", "listings": listings}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # init_db() # No need to call here, init.sql handles it for Docker compose
    app.run(debug=True, host='0.0.0.0', port=5000)
