# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for psycopg2 (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # Clean up APT when done
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the Flask application
# Use gunicorn for a production-ready WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
