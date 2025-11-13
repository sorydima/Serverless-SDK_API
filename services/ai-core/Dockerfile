FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libboost-all-dev \
    libfmt-dev \
    libyaml-cpp-dev \
    libssl-dev \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for AI/ML
RUN pip3 install \
    numpy \
    scipy \
    scikit-learn \
    tensorflow \
    torch \
    transformers

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Build the service
RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Expose port
EXPOSE 8081

# Run the service
CMD ["./build/ai-core-service"]
