# Use a smaller base image
FROM python:3.10-slim
# Set the working directory inside the container
WORKDIR /app
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
# Install dependencies without cache and unnecessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Copy the rest of the application code
COPY . .
# Expose the Flask port
EXPOSE 8080
# Run the Flask application
CMD ["python", "main.py"]