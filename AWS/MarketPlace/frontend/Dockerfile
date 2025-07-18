# Use a lightweight Python base image
FROM python:3.9-slim-buster

WORKDIR /app

COPY index.html .

EXPOSE 80

CMD ["python3", "-m", "http.server", "80"]