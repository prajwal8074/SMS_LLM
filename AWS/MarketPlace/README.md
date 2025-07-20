# Marketplace Application

## Website
*Open html file in 'frontend' folder*

<img width="1902" height="971" alt="Screenshot from 2025-07-20 02-16-48" src="https://github.com/user-attachments/assets/dfe77f28-016e-4559-92b9-f3aa058b3d33" />

---

- This project provides a basic mock marketplace application, demonstrating a backend API (Flask + PostgreSQL) containerized with Docker
- A Python client that integrates tool calling (using gemini-2.0-flash) with the OpenAI Library for multi-LLM compatibility.

## Features
* **Add Listing**: Add new items for sale to the marketplace.
* **Sell Item**: Mark existing items as sold.
* **Get All Listings**: Retrieve a list of all active items on the marketplace.
* **AI Integration**: A Python client capable of interacting with the OpenAI API to trigger these marketplace functions through natural language prompts.
* **View Listings**: Mock Marketplace website to view listings in the database
* **Buy Now** button sends an sms like this to seller's phone number
   * <img width="330" height="100" alt="Screenshot_20250720-090848" src="https://github.com/user-attachments/assets/29dd56c8-a4f3-41d5-a311-3f7b22774702" />

## Technologies Used

* **Backend**:
    * **Python**: Programming language.
    * **Flask**: Web framework for building the API.
    * **PostgreSQL**: Relational database for storing listings.
    * **psycopg2-binary**: PostgreSQL adapter for Python.
    * **Gunicorn**: WSGI HTTP Server for Python web applications (production-ready server).
* **Containerization**:
    * **Docker**: For containerizing the application and database.
    * **Docker Compose**: For defining and running multi-container Docker applications.
* **AI Integration**:
    * **OpenAI Python Client**: To interact with OpenAI's Chat Completion API.
    * **Requests**: Python HTTP library for making API calls to the Flask backend.

## Project Structure
```
MarketPlace/
├── frontend/
│   └── FarmBasket.html           # Mock Marketplace website
└── backend/
   ├── server/
   │   ├── Dockerfile             # Defines how to build the Flask app Docker image
   │   ├── app.py                 # Flask application with API endpoints
   │   ├── database.py            # Database connection utility
   │   └── requirements.txt       # Python dependencies for the Flask app
   ├── postgres/
   │   └── init.sql               # SQL script for initial database schema setup
   ├── client.py                  # gemini client using OpenAI library, implements function calling
   └── docker-compose.yml         # Defines and links the 'app' and 'db' services
```
## Demo

### Start Docker container
<img src="https://github.com/user-attachments/assets/c0eadcbb-2db3-44ba-9b78-5e58830aa0a5" height="480">

### Check if both containers are running
<img src="https://github.com/user-attachments/assets/af915d6e-73a9-4e04-a9b0-0a1e6e96f240" height="480">

### Check Database before function call
<img src="https://github.com/user-attachments/assets/824760a5-b7fd-47c4-b078-62d05f3d9724" height="480">

### Run client which should create a function call

<details>
  <summary><b>Client.py (removed later)</b></summary>

```python
import json
import requests # Used for making HTTP requests
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from openai import OpenAI
import os
from dotenv import load_dotenv

# --- Configuration for your deployed server ---
# Replace with the actual public IP/DNS of your EC2 instance and the port your Flask app is exposed on
FLASK_SERVER_BASE_URL = "http://localhost:5000"
DEMO_SELLER_NAME = 'DEMO SELLER'
DEMO_SELLER_CONTACT = "9876543210"

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- Define the actual functions (HTTP clients for your API) ---
# These functions will now make network requests to your deployed Flask server.

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
    """Makes an API call to mark an existing item listing as sold."""
    print(f"\n--- Making API Call: sell_item ---")
    url = f"{FLASK_SERVER_BASE_URL}/sell_item"
    payload = {
        "listing_id": listing_id,
        "buyer_id": buyer_id
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling sell_item API: {e}")
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
    # Use .tool_calls directly from the message object
    tool_calls = ai_response.choices[0].message.tool_calls

    if not tool_calls:
        print("No tool calls found in the AI response.")
        return

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
            else:
                print(f"  Error: Tool '{function_name}' is not defined in available_tools.")

messages = [{"role": "user", "content": "List an item for sale: 'Collectible Capture Card', price $50.00. It's a rare card in excellent condition."}]
response = client.chat.completions.create(
  model="gemini-2.0-flash",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)
process_tool_calls(response)
```
</details>

<img src="https://github.com/user-attachments/assets/70444895-81be-4e60-8547-2e729639433a" height="480">

### Check Database after function call
<img src="https://github.com/user-attachments/assets/fdf9500a-0e1e-4276-8ef3-56fb9360de8d" height="480">
