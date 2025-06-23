# Marketplace Application

- This project provides a basic mock marketplace application, demonstrating a backend API (Flask + PostgreSQL) containerized with Docker
- A Python client that integrates tool calling (using gemini-2.0-flash) with the OpenAI Library for multi-modal compatibility.

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
marketplace-backend/
├── server/
│   ├── Dockerfile             # Defines how to build the Flask app Docker image
│   ├── app.py                 # Flask application with API endpoints
│   ├── database.py            # Database connection utility
│   └── requirements.txt       # Python dependencies for the Flask app
├── postgres/
│   └── init.sql               # SQL script for initial database schema setup
├── client.py                  # gemini client using OpenAI library, implements function calling
└── docker-compose.yml         # Defines and links the 'app' and 'db' services

## Setup (local for now)

![Screenshot from 2025-06-23 13-24-04](https://github.com/user-attachments/assets/bed1133b-9548-46ad-9430-7b5950e8135e)
![Screenshot from 2025-06-23 13-24-10](https://github.com/user-attachments/assets/af915d6e-73a9-4e04-a9b0-0a1e6e96f240)
![Screenshot from 2025-06-23 13-24-23](https://github.com/user-attachments/assets/ee7849f4-0779-4457-a51f-ecc09cea4375)
![Screenshot from 2025-06-23 13-24-27](https://github.com/user-attachments/assets/6974305b-b1be-4e86-b449-bb7297162b33)










