from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import get_db_connection
import json
import os
import base64
import time
import sys

from database_logic import create_listing_in_db, remove_listing_from_db

app = Flask(__name__)
CORS(app)

@app.route('/add_listing', methods=['POST'])
def add_listing():
	"""API endpoint to add a new item listing."""
	data = request.json
	item_name = data.get('item_name')
	price = data.get('price')
	description = data.get('description')
	seller_name = data.get('seller_name') # New field
	seller_contact = data.get('seller_contact') # New field

	# Basic validation for required fields
	if not item_name or price is None or seller_contact is None:
		return jsonify({"error": "item_name, price, and seller_contact are required"}), 400

	result = create_listing_in_db(
		item_name=item_name,
		price=price,
		description=description,
		seller_name=seller_name,
		seller_contact=seller_contact
	)

	if result.get("status") == "success":
		return jsonify(result), 201
	else:
		return jsonify({"error": result.get("message")}), 500

@app.route('/delete_listing', methods=['POST'])
def delete_listing():
	"""API endpoint to delete an item listing."""
	data = request.json
	listing_id = data.get('listing_id')

	if not listing_id:
		return jsonify({"error": "listing_id is required"}), 400

	result = remove_listing_from_db(listing_id)
	
	if result.get("status") == "success":
		return jsonify(result), 200
	elif result.get("status") == "not_found":
		return jsonify(result), 404
	else:
		return jsonify({"error": result.get("message")}), 500

@app.route('/sell_item', methods=['POST'])
def sell_item():
	"""API endpoint to mark an existing item listing as sold."""
	data = request.json
	listing_id = data.get('listing_id')
	listing_name = data.get('listing_name')
	buyer_contact = data.get('buyer_contact')
	seller_contact = "9876543210"

	if not listing_id:
		return jsonify({"error": "listing_id is required"}), 400

	try:
		conn = get_db_connection()
		cur = conn.cursor()
		query = "SELECT seller_contact FROM listings WHERE id = %s;"
		cur.execute(query, (listing_id,))

		# Fetch the result
		result = cur.fetchone()

		if result:
			seller_contact = str(result[0])
		else:
			print(f"No listing found with ID: {listing_id}")

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
			return jsonify({
				"status": "success",
				"message": f"Listing '{listing_id}' for '{updated_row[1]}' marked as sold.",
				"buyer_id": buyer_id # Still passing buyer_id even if not stored
			}), 200
		else:
			return jsonify({
				"status": "not_found",
				"message": f"Listing '{listing_id}' not found or already sold."
			}), 404
	except Exception as e:
		print(f"Error selling item: {e}")
		return jsonify({"error": str(e)}), 500
	finally:
		sms_message = f"🛍️ Order Received! You have received an order for '{listing_name}'. Call buyer at {buyer_contact}"

		try:
			sms = sms_client.messages.create(
				body=sms_message,
				from_=TWILIO_PHONE_NUMBER,
				to="+91"+seller_contact
			)
			print(f"✅ SMS sent to {to_phone} (SID: {sms.sid})")
			return {"status": "success", "message_sid": sms.sid}
		except Exception as e:
			print(f"❌ SMS failed: {e}")
			return {"status": "error", "message": str(e)}

@app.route('/get_all_listings', methods=['GET'])
def get_all_listings():
	"""API endpoint to retrieve all active item listings."""
	try:
		conn = get_db_connection()
		cur = conn.cursor()
		# Fetch all columns including the new seller_name and seller_contact
		cur.execute("SELECT * FROM listings;")
		
		# Get column names from the cursor description
		columns = [col[0] for col in cur.description]
		
		# Fetch all rows and map them to dictionaries using column names
		listings = [dict(zip(columns, row)) for row in cur.fetchall()]
		
		cur.close()
		conn.close()

		# Convert UUID objects and Decimal objects to JSON-serializable types (string and float)
		for listing in listings:
			if 'id' in listing:
				listing['id'] = str(listing['id'])
			if 'price' in listing:
				listing['price'] = float(listing['price'])
			# seller_contact is NUMERIC in DB, will be int or float in Python; ensure it's simple
			if 'seller_contact' in listing and listing['seller_contact'] is not None:
				listing['seller_contact'] = str(int(listing['seller_contact'])) # Convert to string for phone numbers

		return jsonify({"status": "success", "listings": listings}), 200
	except Exception as e:
		print(f"Error fetching listings: {e}") # Log the error
		return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
	# Make sure your .env file is loaded correctly by database.py
	# and the Flask environment is set up.
	# For local development, debug=True is useful. Host 0.0.0.0 makes it accessible
	# from other devices on the network.
	app.run(debug=True, host='0.0.0.0', port=5002)
