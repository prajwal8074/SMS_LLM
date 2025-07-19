import psycopg2
from database import get_db_connection # Assuming database.py contains this function

def create_listing_in_db(item_name: str, price: float, seller_name: str, seller_contact: str, description: str = ""):
	"""Directly inserts a new item listing into the database."""
	try:
		conn = get_db_connection()
		cur = conn.cursor()
		cur.execute(
			"""
			INSERT INTO listings (item_name, price, description, seller_name, seller_contact, status)
			VALUES (%s, %s, %s, %s, %s, 'active')
			RETURNING id;
			""",
			(item_name, price, description, seller_name, seller_contact)
		)
		new_listing_id = cur.fetchone()[0]
		conn.commit()
		cur.close()
		conn.close()
		return {
			"status": "success",
			"message": f"Listing for '{item_name}' added.",
			"listing_id": str(new_listing_id)
		}
	except Exception as e:
		print(f"Error in create_listing_in_db: {e}")
		# In a real app, you might want to rollback the transaction
		return {"status": "error", "message": str(e)}

def remove_listing_from_db(listing_id: str):
	"""Directly deletes an item listing from the database."""
	try:
		conn = get_db_connection()
		cur = conn.cursor()
		cur.execute(
			"""
			DELETE FROM listings
			WHERE id = %s
			RETURNING id;
			""",
			(listing_id,)
		)
		deleted_row = cur.fetchone()
		conn.commit()
		cur.close()
		conn.close()

		if deleted_row:
			return {
				"status": "success",
				"message": f"Listing '{listing_id}' deleted."
			}
		else:
			return {
				"status": "not_found",
				"message": f"Listing '{listing_id}' not found."
			}
	except Exception as e:
		print(f"Error in remove_listing_from_db: {e}")
		return {"status": "error", "message": str(e)}