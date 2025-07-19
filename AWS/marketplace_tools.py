import json
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from openai import OpenAI
import os
from dotenv import load_dotenv

try:
    from database_logic import create_listing_in_db, remove_listing_from_db
except ImportError:
    print("Skipped database_logic module import")

load_dotenv()

FLASK_SERVER_BASE_URL = os.getenv('FLASK_SERVER_BASE_URL')

print(f"FLASK_SERVER_BASE_URL: {FLASK_SERVER_BASE_URL}")

def add_listing(item_name: str, price: float, seller_name: str, seller_contact: str, description: str = ""):
    """Makes an API call to add a new item listing to the marketplace."""
    print(f"\n--- Making API Call: add_listing ---")
    return create_listing_in_db(
        item_name=item_name,
        price=price,
        description=description,
        seller_name=seller_name,
        seller_contact=seller_contact
    )

def delete_listing(listing_id: str):
    """Makes an API call to delete an item listing from the marketplace."""
    print(f"\n--- Making API Call: delete_listing ---")
    return remove_listing_from_db(listing_id)

def add_listing_api(item_name: str, price: float, seller_name: str, seller_contact: str, description: str = ""):
    """Makes an API call to add a new item listing to the marketplace."""
    print(f"\n--- Making API Call: add_listing ---")
    url = f"{FLASK_SERVER_BASE_URL}/add_listing"
    payload = {
        "item_name": item_name,
        "price": price,
        "description": description,
        "seller_name" : seller_name,
        "seller_contact" : seller_contact,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling add_listing API: {e}")
        return {"status": "error", "message": str(e)}

def delete_listing_api(listing_id: str):
    """Makes an API call to delete an item listing from the marketplace."""
    print(f"\n--- Making API Call: delete_listing ---")
    url = f"{FLASK_SERVER_BASE_URL}/delete_listing"
    payload = {"listing_id": listing_id}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling delete_listing API: {e}")
        return {"status": "error", "message": str(e)}

def get_all_listings_api():
    """Makes an API call to retrieve all active item listings."""
    print(f"\n--- Making API Call: get_all_listings ---")
    url = f"{FLASK_SERVER_BASE_URL}/get_all_listings"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling get_all_listings API: {e}")
        return {"status": "error", "message": str(e)}


tools = [
  {
    "type": "function",
    "function": {
      "name": "add_listing",
      "description": "Adds a new item listing to the marketplace with its name, price, and an optional description.",
      "parameters": {
        "type": "object",
        "properties": {
          "item_name": {
            "type": "string",
            "description": "The name of the item to be listed."
          },
          "price": {
            "type": "number",
            "description": "The price of the item."
          },
          "seller_name": {
            "type": "string",
            "description": "Seller's name",
            "nullable": True
          },
          "seller_contact": {
            "type": "string",
            "description": "Seller's 10 digit phone number without any prefix.",
            "nullable": True
          },
          "description": {
            "type": "string",
            "description": "A detailed description of the item.",
            "nullable": True
          },
        },
        "required": [
          "item_name",
          "price"
        ]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "delete_listing",
      "description": "Deletes an existing item listing using its unique listing ID.",
      "parameters": {
        "type": "object",
        "properties": {
          "listing_id": {
            "type": "string",
            "description": "The unique ID of the listing to be marked as sold."
          }
        },
        "required": [
          "listing_id"
        ]
      }
    }
  }
]


# --- Map tool names (strings) to their corresponding API client functions ---
available_tools = {
    "add_listing": add_listing,
    "delete_listing": delete_listing,
}

# --- Function to process the AI's tool call response (remains largely the same) ---
def process_tool_calls(ai_response: ChatCompletion):
    """
    Extracts tool calls from an AI response and executes the corresponding functions.
    """
    tool_calls = ai_response.choices[0].message.tool_calls

    if not tool_calls:
        print("No tool calls found in the AI response.")
        return False

    function_called = False

    for tool_call in tool_calls:
        if tool_call.type == 'function':
            function_name = tool_call.function.name
            arguments_str = tool_call.function.arguments

            print(f"\nProcessing tool call for '{function_name}'...")
            print(f"  Arguments (string from AI): {arguments_str}")

            try:
                function_args = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                print(f"  Error parsing arguments for '{function_name}': {e}")
                continue

            if function_name in available_tools:
                function_to_call = available_tools[function_name]
                print(f"  Attempting to call API client function: {function_to_call.__name__} with {function_args}")
                try:
                    tool_output = function_to_call(**function_args)
                    print(f"  API Client Function Output: {json.dumps(tool_output, indent=2)}")
                    # You would typically send this tool_output back to the AI model
                    # for it to continue the conversation, describing the result of the tool.
                except Exception as e:
                    print(f"  An error occurred during API client function call: {e}")
                finally:
                    function_called = True
            else:
                print(f"  Error: Tool '{function_name}' is not defined in available_tools.")

    return function_called
