# Use an official Python base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY Backend/ /app/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]



COPY ackend/ /app/