# Campus Connect - Technical Documentation

## Overview

Campus Connect is a comprehensive web application built with a microservices architecture to serve college students with various features for campus life management.

## Architecture

### Microservices Architecture

The application consists of the following microservices:

1. **API Gateway** - Central routing and authentication
2. **Auth Service** - User authentication and profile management
3. **Meetups Service** - Event creation and management
4. **Marketplace Service** - Buy/sell items with real-time chat
5. **Stolen & Found Service** - Lost/found item reporting
6. **Rooms & Roommates Service** - Accommodation listings
7. **Rental Hub Service** - Gadget rentals
8. **Clubs & Communities Service** - Club management
9. **Jobs & Internships Service** - Job postings
10. **Notes & Printing Service** - Document sharing
11. **Food Service** - Cafes and food services

### Technology Stack

- **Backend**: Python FastAPI microservices
- **Database**: MySQL with separate schemas per service
- **Frontend**: React.js with Material UI
- **Authentication**: JWT tokens
- **Real-time**: WebSockets for chat
- **Deployment**: Docker & Docker Compose
- **External Services**: Firebase (notifications), Google Maps, AWS S3/Cloudinary

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Docker & Docker Compose

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd campus-connect
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Alternative)

1. **Database Setup**
   ```bash
   mysql -u root -p < database/init.sql
   ```

2. **Backend Services**
   ```bash
   # API Gateway
   cd backend/api-gateway
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

   # Auth Service
   cd backend/services/auth
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8001
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## API Documentation

Each microservice provides its own API documentation:

- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- And so on for each service...

## Database Schema

The application uses separate MySQL databases for each microservice:

- `auth_db` - User authentication and profiles
- `meetups_db` - Events and meetups
- `marketplace_db` - Items for sale
- `stolen_found_db` - Lost/found reports
- `rooms_db` - Accommodation listings
- `rental_db` - Rental items
- `clubs_db` - Clubs and communities
- `jobs_db` - Job postings
- `notes_db` - Notes and printing services
- `food_db` - Food outlets and menus

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (student/admin)
- Input validation and sanitization
- CORS configuration

## Deployment

### Production Deployment

1. **Environment Variables**
   Set all required environment variables in production

2. **Docker Deployment**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Cloud Deployment**
   - Backend services: Render
   - Frontend: Vercel
   - Database: AWS RDS or PlanetScale

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write comprehensive docstrings
- Use type hints in Python

### Testing

- Unit tests for each service
- Integration tests for API endpoints
- Frontend component tests

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Ensure MySQL is running
   - Check database credentials in .env
   - Verify database initialization

2. **Service Communication**
   - Check service URLs in docker-compose.yml
   - Verify API Gateway routing
   - Check network connectivity

3. **Frontend Issues**
   - Clear browser cache
   - Check console for errors
   - Verify API endpoints

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Contact the development team

## License

This project is licensed under the MIT License.