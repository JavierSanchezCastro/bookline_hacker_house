# Start from a Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on (optional, for documentation)
EXPOSE 8000

# The command to run the application will be specified in docker-compose.yml
# For local development, Uvicorn with --reload is often used via docker-compose
# For a production-like scenario, you might have:
# CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
