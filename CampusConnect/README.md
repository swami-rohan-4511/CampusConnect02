# Campus Connect

A production-ready full-stack web application for college students to connect and share resources, built with microservices architecture.

## Features

- **Meetups**: Create and join meetups with Google Maps integration
- **Marketplace**: Buy/sell items with real-time chat
- **Stolen & Found**: Report lost/found items with push notifications
- **Rooms & Roommates**: Find accommodation and roommates
- **Rental Hub**: Rent gadgets and equipment
- **Clubs & Communities**: Join college clubs and communities
- **Jobs & Internships**: Job listings and internship opportunities
- **Notes & Printing**: Share notes and printing services
- **Food**: Cafes, mess, and food delivery options

## Technology Stack

- **Backend**: Python FastAPI microservices
- **Database**: MySQL with separate schemas per service
- **Frontend**: React.js with Material UI
- **Authentication**: JWT with role-based access
- **Real-time**: WebSockets for chat
- **Security**: Rate limiting, CORS, input validation
- **Performance**: Gzip compression, caching, monitoring
- **Deployment**: Docker with docker-compose
- **Monitoring**: Health checks, performance metrics

## Architecture

The application follows a microservices architecture with:
- API Gateway for request routing
- Independent services for each module
- Separate MySQL databases per service
- React frontend with modern UI/UX

## Prerequisites

- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Docker & Docker Compose

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd campus-connect
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Testing

### Automated Integration Tests

Run the integration test suite to verify all services are working:

```bash
# Make sure all services are running
docker-compose up -d

# Run integration tests
python test_integration.py
```

### Manual Testing

1. **Health Checks**: Visit http://localhost:8000/health
2. **API Documentation**: Visit http://localhost:8000/docs
3. **Frontend**: Visit http://localhost:3000 and test all features
4. **WebSocket Chat**: Test real-time messaging in marketplace
5. **Performance Monitoring**: Run `python monitoring/health_check.py --report`

### Automated API Testing

Run the comprehensive API test suite:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/test_api_endpoints.py -v

# Run with coverage report
pytest tests/test_api_endpoints.py --cov=../backend --cov-report=html

# Run specific test
pytest tests/test_api_endpoints.py::TestCampusConnectAPI::test_health_check -v
```

### Integration Testing

```bash
# Run integration tests
python test_integration.py

# Run health monitoring
python monitoring/health_check.py --continuous --interval 30
```

### Test User Accounts

For testing purposes, you can create test accounts or use the default admin account:
- Email: admin@campus.com
- Password: admin123

### Sample Data

Load sample data for testing:
```bash
# Connect to MySQL and run
source database/sample_data.sql
```

## Security & Performance

### Security Features
- **Rate Limiting**: 100 requests/minute per IP address
- **CORS Protection**: Configured allowed origins
- **Input Validation**: Comprehensive validation on all endpoints
- **JWT Security**: Secure token management with expiration
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Content security policies

### Performance Optimizations
- **Gzip Compression**: Automatic response compression
- **Database Indexing**: Optimized queries with proper indexes
- **Connection Pooling**: Efficient database connections
- **Caching Ready**: Redis integration prepared
- **Health Monitoring**: Real-time service monitoring

### Monitoring
```bash
# Run health monitoring
python monitoring/health_check.py --continuous --interval 30

# Generate health report
python monitoring/health_check.py --report
```

## Development Setup

See detailed setup instructions in the docs folder.

## API Documentation

Available at `/docs` endpoint of each microservice when running locally.