# Marketplace Application

- This project provides a basic mock marketplace application, demonstrating a backend API (Flask + PostgreSQL) containerized with Docker
- A Python client that integrates tool calling (using gemini-2.0-flash) with the OpenAI Library for multi-LLM compatibility.

## Features

* **Add Listing**: Add new items for sale to the marketplace.
* **Sell Item**: Mark existing items as sold.
* **Get All Listings**: Retrieve a list of all active items on the marketplace.
* **AI Integration**: A Python client capable of interacting with the OpenAI API to trigger these marketplace functions through natural language prompts.

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
backend/
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
## Setup (local for now)
### Start Docker container
<img src="https://github.com/user-attachments/assets/c0eadcbb-2db3-44ba-9b78-5e58830aa0a5" height="480">

### Check if both containers are running
<img src="https://github.com/user-attachments/assets/af915d6e-73a9-4e04-a9b0-0a1e6e96f240" height="480">

### Check Database before function call
<img src="https://github.com/user-attachments/assets/824760a5-b7fd-47c4-b078-62d05f3d9724" height="480">

### Run client which should create a function call
<img src="https://github.com/user-attachments/assets/70444895-81be-4e60-8547-2e729639433a" height="480">

### Check Database after function call
<img src="https://github.com/user-attachments/assets/fdf9500a-0e1e-4276-8ef3-56fb9360de8d" height="480">

### Website after function call
![Screenshot (8)](https://github.com/user-attachments/assets/3556c633-9abb-4620-9e84-7c669f9efd2e)


