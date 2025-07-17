# Use the official Python image as the base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Update system packages and install runtime tools
# Install gcc only on ARM platforms for building Python packages with C extensions
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y iw iproute2 && \
    if [ "$(dpkg --print-architecture)" = "arm64" ] || [ "$(dpkg --print-architecture)" = "armhf" ]; then \
        apt-get install -y gcc; \
    fi && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt ./

# Upgrade pip and install the Python packages listed in requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Remove gcc if it was installed (only on ARM)
RUN if [ "$(dpkg --print-architecture)" = "arm64" ] || [ "$(dpkg --print-architecture)" = "armhf" ]; then \
        apt-get remove -y gcc && \
        apt-get autoremove -y && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Copy the source code into the container
COPY src/ ./

# Build arguments for version info (added last to not invalidate cache)
ARG VERSION=1.0.0
ARG BUILD_TIME

# Set version info as environment variables
ENV WIFISCAN_COLLECTOR_VERSION=${VERSION}
ENV WIFISCAN_COLLECTOR_BUILD_TIME=${BUILD_TIME}

# Run the Python script
CMD ["python", "-u", "./wifiscan-collector.py"]