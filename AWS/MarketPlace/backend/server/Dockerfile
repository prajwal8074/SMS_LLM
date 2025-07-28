# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code into the container

COPY MarketPlace/backend/server/ .
COPY cache.py .
COPY marketplace_tools.py .

# Expose the port the app runs on
EXPOSE 5002

# Run the Flask application
# Use gunicorn for a production-ready WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--timeout", "300", "app:app"]
