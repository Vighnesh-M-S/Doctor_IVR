# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy all project files
COPY backend/ /app/

# Install dependencies
RUN apt-get update && apt-get install -y git && pip install --upgrade pip
RUN pip install -r requirements.txt

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]