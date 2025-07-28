# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script and input/output folders
COPY extractor.py .
COPY app ./app

# Default run command
CMD ["python", "extractor.py"]
