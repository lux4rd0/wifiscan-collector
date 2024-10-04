# Use the official Python image as the base image
FROM python:3.12.6-slim

# Set the working directory inside the container
WORKDIR /app/wifiscan-collector

# Update system packages, install the required tools (iw), and remove unnecessary files to keep the image small
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y iw && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and the main Python script into the container
COPY requirements.txt ./src/wifiscan-collector.py ./

# Upgrade pip and install the Python packages listed in requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Run the Python script
CMD ["python3", "./wifiscan-collector.py"]
