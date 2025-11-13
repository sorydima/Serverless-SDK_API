# Serverless-SDK_API

A comprehensive decentralized networking and AI platform for the REChain Blockchain Node Network, implementing a microservices architecture with userver framework.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Android (Kotlin) │ AuroraOS (Qt) │ HarmonyOS (C++) │    │
│  │ iOS (Swift)      │ Web (Flutter) │ Desktop (Rust)  │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Microservices Layer                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Mesh Gateway     │ AI Core        │ Storage         │    │
│  │ Device Discovery │ ML Inference   │ Database/Cache  │    │
│  │ Routing          │ Quantum Comp.  │ File Storage    │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ PostgreSQL       │ Redis Cluster   │ Monitoring      │    │
│  │ Master-Slave     │ Distributed     │ Prometheus/Graf │    │
│  │ Replication      │ Cache           │ Security         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Microservices

### Mesh Gateway Service (Port 8080)
- **Purpose**: Device discovery, mesh network routing, message forwarding
- **Features**:
  - Bluetooth LE Mesh discovery
  - AODV routing protocol
  - Real-time device status monitoring
  - Message routing and forwarding

### AI Core Service (Port 8081)
- **Purpose**: Machine learning inference, quantum computing, model management
- **Features**:
  - Graph ML training and inference
  - Quantum circuit simulation (32 qubits)
  - Federated learning support
  - Real-time AI processing

### Storage Service (Port 8082)
- **Purpose**: Distributed data persistence, caching, file storage
- **Features**:
  - PostgreSQL database operations
  - Redis distributed caching
  - File object storage
  - Data synchronization

## Infrastructure Components

### Database Layer
- **PostgreSQL Cluster**: Master-slave replication with automated failover
- **Connection Pooling**: PgBouncer for efficient connection management
- **High Availability**: Automatic backup and recovery

### Caching Layer
- **Redis Cluster**: Distributed caching across mesh nodes
- **State Synchronization**: Real-time data sharing between services
- **Session Management**: User session and authentication caching

### Monitoring & Observability
- **Prometheus**: Metrics collection from all services
- **Grafana**: Visualization dashboards for system monitoring
- **Alerting**: Automated alerts for system anomalies
- **Custom Metrics**: Mesh operations, AI performance, storage usage

### Security
- **TLS Encryption**: End-to-end encrypted service communication
- **Role-Based Access Control**: Fine-grained permission management
- **Container Security**: AppArmor, seccomp, and capability restrictions
- **Cryptographic Key Management**: Secure key storage and rotation

## Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM, 4 CPU cores recommended
- Linux/Windows/macOS with Docker support

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/Serverless-SDK_API.git
   cd Serverless-SDK_API
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your secure passwords
   ```

3. **Start the platform**
   ```bash
   docker-compose up -d
   ```

4. **Access services**
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin)
   - **Prometheus**: http://localhost:9090
   - **Mesh Gateway API**: http://localhost:8080
   - **AI Core API**: http://localhost:8081
   - **Storage API**: http://localhost:8082

### With Security Enhancements

For production deployment with enhanced security:

```bash
docker-compose -f docker-compose.yml -f infra/security/docker-compose.security.yml up -d
```

## API Endpoints

### Mesh Gateway Service

```bash
# Get mesh status
GET /mesh/status

# List devices
GET /devices

# Calculate route
POST /routes/calculate

# Send message
POST /messages/send
```

### AI Core Service

```bash
# List available models
GET /models

# Load model
POST /models/load

# Run inference
POST /inference

# Quantum circuit execution
POST /quantum/execute
```

### Storage Service

```bash
# Store object
POST /objects

# Get object
GET /objects/{key}

# Database operations
POST /records
GET /records/{id}

# Cache operations
POST /cache
GET /cache/{key}
```

## Development

### Building Individual Services

```bash
# Mesh Gateway
cd services/mesh-gateway
mkdir build && cd build
cmake .. && make -j$(nproc)

# AI Core
cd services/ai-core
mkdir build && cd build
cmake .. && make -j$(nproc)

# Storage
cd services/storage
mkdir build && cd build
cmake .. && make -j$(nproc)
```

### Testing

```bash
# Run unit tests
cd services/{service-name}/build
ctest

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Configuration

Each service uses YAML configuration files:

- `services/mesh-gateway/config.yaml`
- `services/ai-core/config.yaml`
- `services/storage/config.yaml`

Key configuration areas:
- Server settings (ports, timeouts)
- Database connections
- Redis cluster configuration
- Security policies
- Monitoring endpoints

## Monitoring

### Key Metrics

- **Service Health**: Uptime, response times, error rates
- **Mesh Performance**: Device count, route efficiency, message latency
- **AI Performance**: Inference latency, model accuracy, quantum execution time
- **Storage Performance**: Database connections, cache hit rates, storage usage

### Alerts

- Service downtime
- High latency (>95th percentile thresholds)
- Resource exhaustion (CPU, memory, disk)
- Security incidents

## Security Features

- **Mutual TLS**: Service-to-service authentication
- **JWT Tokens**: API authentication and authorization
- **Container Hardening**: Minimal privileges, read-only filesystems
- **Network Segmentation**: Isolated service networks
- **Audit Logging**: Comprehensive security event logging

## Performance Characteristics

- **Mesh Message Delivery**: <100ms local, <1s regional
- **AI Inference**: <50ms for real-time decisions
- **Database Queries**: <10ms average response time
- **Cache Operations**: <1ms average latency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the Affero General Public License (AGPL) version 3.

## Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: security@your-org.com

---

Built with ❤️ using userver framework, PostgreSQL, Redis, and modern C++.
