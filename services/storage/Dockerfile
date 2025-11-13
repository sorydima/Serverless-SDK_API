FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libboost-all-dev \
    libfmt-dev \
    libyaml-cpp-dev \
    libpq-dev \
    libhiredis-dev \
    libssl-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Build the service
RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Create storage directory
RUN mkdir -p /app/storage

# Expose port
EXPOSE 8082

# Run the service
CMD ["./build/storage-service"]
