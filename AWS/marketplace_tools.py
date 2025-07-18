import json
import requests # Used for making HTTP requests
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

FLASK_SERVER_BASE_URL = os.getenv('FLASK_SERVER_BASE_URL')
DEMO_SELLER_NAME = 'DEMO SELLER'
DEMO_SELLER_CONTACT = "9876543210"

print(f"FLASK_SERVER_BASE_URL: {FLASK_SERVER_BASE_URL}")

def add_listing_api(item_name: str, price: float, description: str = None):
    """Makes an API call to add a new item listing to the marketplace."""
    print(f"\n--- Making API Call: add_listing ---")
    url = f"{FLASK_SERVER_BASE_URL}/add_listing"
    payload = {
        "item_name": item_name,
        "price": price,
        "description": description,
        "seller_name" : DEMO_SELLER_NAME,
        "seller_contact" : DEMO_SELLER_CONTACT,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling add_listing API: {e}")
        return {"status": "error", "message": str(e)}

def sell_item_api(listing_id: str, buyer_id: str = None):
    """Mark item as sold and notify seller via SMS."""
    url = f"{os.getenv('FLASK_SERVER_BASE_URL')}/sell_item"
    payload = {"listing_id": listing_id, "buyer_id": buyer_id}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

        # Send SMS if sale succeeds
        if result.get("status") == "success":
            item_name = result.get("item_name", "an item")
            sms_message = f"🛍️ Order Received! '{item_name}' (ID: {listing_id}) was sold."
            send_sms(os.getenv('DEMO_SELLER_CONTACT'), sms_message)
        
        return result
    except Exception as e:
        print(f"Error in sell_item_api: {e}")
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
          "description": {
            "type": "string",
            "description": "A detailed description of the item.",
            "nullable": True
          }
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
      "name": "sell_item",
      "description": "Marks an existing item listing as sold using its unique listing ID. Can optionally record the buyer's ID.",
      "parameters": {
        "type": "object",
        "properties": {
          "listing_id": {
            "type": "string",
            "description": "The unique ID of the listing to be marked as sold."
          },
          "buyer_id": {
            "type": "string",
            "description": "The ID of the buyer who purchased the item (optional).",
            "nullable": True
          }
        },
        "required": [
          "listing_id"
        ]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_all_listings",
      "description": "Retrieves all currently active item listings available on the marketplace.",
      "parameters": {
        "type": "object",
        "properties": {},
        "required": []
      }
    }
  }
]


# --- Map tool names (strings) to their corresponding API client functions ---
available_tools = {
    "add_listing": add_listing_api,
    "sell_item": sell_item_api,
    "get_all_listings": get_all_listings_api,
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
