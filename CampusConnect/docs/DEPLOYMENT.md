# Campus Connect - Deployment Guide

This guide provides comprehensive instructions for deploying Campus Connect to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Render Deployment](#render-deployment)
5. [Vercel Deployment](#vercel-deployment)
6. [Database Setup](#database-setup)
7. [Environment Configuration](#environment-configuration)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Docker & Docker Compose** (for local development)
- **Git** (for version control)
- **Node.js 16+** (for frontend development)
- **Python 3.9+** (for backend development)

### Cloud Accounts
- **Render** account (for backend services)
- **Vercel** account (for frontend)
- **MySQL Database** (AWS RDS, Google Cloud SQL, or PlanetScale)
- **Redis** (for caching and sessions)
- **Cloudinary** (for file uploads)
- **Firebase** (for push notifications)

### External Services Setup

#### 1. Cloudinary (File Storage)
```bash
# Sign up at cloudinary.com
# Get your cloud name, API key, and API secret
```

#### 2. Firebase (Push Notifications)
```bash
# Create project at console.firebase.google.com
# Enable Cloud Messaging
# Generate service account key
```

#### 3. Google Maps API
```bash
# Enable at console.cloud.google.com
# Create API key with Maps JavaScript API enabled
```

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd campus-connect
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your local configuration
nano .env
```

### 3. Start Services
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Verify Installation
```bash
# Run integration tests
python test_integration.py

# Check service health
curl http://localhost:8000/health
```

### 5. Access Application
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Production Deployment

### Option 1: Automated Deployment Script

```bash
# Make script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment menu
./deploy.sh
```

### Option 2: Manual Deployment

## Render Deployment

### 1. Backend Services Setup

#### Create Render Account
1. Sign up at [render.com](https://render.com)
2. Connect your GitHub repository

#### Deploy Services Using render.yaml

1. **Push code to GitHub**
```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

2. **Deploy on Render**
   - Go to Render dashboard
   - Click "New" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Configure environment variables
   - Deploy all services

3. **Service URLs**
After deployment, you'll get URLs like:
- `https://campus-connect-api-gateway.onrender.com`
- `https://campus-connect-auth.onrender.com`
- etc.

### 2. Environment Variables Setup

In Render dashboard, set these environment variables:

#### Required for All Services
```bash
JWT_SECRET_KEY=your_secure_jwt_secret
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
REDIS_URL=your_redis_url
```

#### Service-Specific Variables
```bash
# API Gateway
AUTH_SERVICE_URL=https://campus-connect-auth.onrender.com
MEETUPS_SERVICE_URL=https://campus-connect-meetups.onrender.com
# ... etc for all services

# Services requiring external APIs
GOOGLE_MAPS_API_KEY=your_google_maps_key
CLOUDINARY_CLOUD_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
FIREBASE_PROJECT_ID=your_firebase_project
FIREBASE_PRIVATE_KEY=your_firebase_key
FIREBASE_CLIENT_EMAIL=your_firebase_email
```

## Vercel Deployment

### 1. Frontend Deployment

#### Install Vercel CLI
```bash
npm install -g vercel
```

#### Deploy Frontend
```bash
# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Or link existing project
vercel link
vercel env add REACT_APP_API_URL
```

#### Environment Variables for Vercel
```bash
REACT_APP_API_URL=https://campus-connect-api-gateway.onrender.com
REACT_APP_WEBSOCKET_URL=wss://campus-connect-websocket.onrender.com
REACT_APP_ENVIRONMENT=production
```

### 2. Custom Domain (Optional)
```bash
# Add custom domain
vercel domains add yourdomain.com

# Configure DNS settings as instructed
```

## Database Setup

### Option 1: AWS RDS MySQL

1. **Create RDS Instance**
   - Go to AWS RDS Console
   - Create MySQL instance
   - Note the endpoint, username, password

2. **Configure Security Group**
   - Allow inbound connections from Render services
   - Port: 3306
   - Source: Render IP ranges (0.0.0.0/0 for development)

3. **Initialize Database**
```bash
# Connect to your RDS instance
mysql -h your-rds-endpoint -u admin -p

# Run initialization script
source database/init.sql
```

### Option 2: PlanetScale

1. **Create PlanetScale Account**
   - Sign up at [planetscale.com](https://planetscale.com)

2. **Create Database**
```bash
# Install PlanetScale CLI
npm install -g @planetscale/cli

# Login
pscale auth login

# Create database
pscale database create campus-connect

# Create branches for each service
pscale branch create campus-connect auth-db
pscale branch create campus-connect meetups-db
# ... etc for all services
```

## Environment Configuration

### Production Environment File

Create `.env.production` with:

```bash
# Database
MYSQL_HOST=your_production_db_host
MYSQL_USER=your_production_db_user
MYSQL_PASSWORD=your_secure_db_password
MYSQL_DATABASE=campus_connect

# JWT
JWT_SECRET_KEY=your_64_character_secure_jwt_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service URLs
AUTH_SERVICE_URL=https://campus-connect-auth.onrender.com
MEETUPS_SERVICE_URL=https://campus-connect-meetups.onrender.com
MARKETPLACE_SERVICE_URL=https://campus-connect-marketplace.onrender.com
STOLEN_FOUND_SERVICE_URL=https://campus-connect-stolen-found.onrender.com
ROOMS_SERVICE_URL=https://campus-connect-rooms.onrender.com
RENTAL_SERVICE_URL=https://campus-connect-rental.onrender.com
CLUBS_SERVICE_URL=https://campus-connect-clubs.onrender.com
JOBS_SERVICE_URL=https://campus-connect-jobs.onrender.com
NOTES_SERVICE_URL=https://campus-connect-notes.onrender.com
FOOD_SERVICE_URL=https://campus-connect-food.onrender.com

# External Services
GOOGLE_MAPS_API_KEY=your_google_maps_key
FIREBASE_PROJECT_ID=your_firebase_project
FIREBASE_PRIVATE_KEY=your_firebase_private_key
FIREBASE_CLIENT_EMAIL=your_firebase_client_email
CLOUDINARY_CLOUD_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret

# Redis
REDIS_URL=redis://your_redis_host:6379

# WebSocket
WEBSOCKET_URL=wss://campus-connect-websocket.onrender.com

# Security
CORS_ORIGINS=https://your-frontend-domain.com
FORCE_HTTPS=true
```

## Monitoring & Maintenance

### 1. Error Tracking (Sentry)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Configure in each service
import sentry_sdk
sentry_sdk.init(
    dsn="your_sentry_dsn",
    environment="production"
)
```

### 2. Performance Monitoring (New Relic)

```bash
# Install New Relic agent
pip install newrelic

# Configure
export NEW_RELIC_LICENSE_KEY=your_license_key
newrelic-admin run-program uvicorn main:app
```

### 3. Log Management

```bash
# View Render logs
render logs campus-connect-api-gateway

# View Vercel logs
vercel logs
```

### 4. Database Backups

```bash
# AWS RDS automated backups
# Configure in AWS Console:
# - Backup retention: 7-30 days
# - Backup window: During low-traffic hours
# - Enable automated backups
```

### 5. SSL/TLS Certificates

- **Render**: Automatic SSL certificates
- **Vercel**: Automatic SSL certificates
- **Custom Domain**: Configure DNS settings

## Troubleshooting

### Common Issues

#### 1. Service Connection Issues
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs api-gateway

# Test API connectivity
curl https://your-api-gateway-url/health
```

#### 2. Database Connection Issues
```bash
# Test database connection
mysql -h your-db-host -u your-user -p

# Check database credentials in environment
echo $MYSQL_HOST
echo $MYSQL_USER
```

#### 3. WebSocket Connection Issues
```bash
# Check WebSocket service
curl https://your-websocket-url/health

# Test WebSocket connection in browser console
const ws = new WebSocket('wss://your-websocket-url/ws/1');
ws.onopen = () => console.log('Connected');
```

#### 4. File Upload Issues
```bash
# Check Cloudinary configuration
curl https://api.cloudinary.com/v1_1/your-cloud-name/ping

# Verify API keys
echo $CLOUDINARY_API_KEY
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_meetups_date ON meetups(event_date);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_reports_status ON reports(status);
```

#### 2. Caching Strategy
```python
# Implement Redis caching
import redis
redis_client = redis.from_url(os.getenv("REDIS_URL"))

# Cache frequently accessed data
@cache(expire=300)
def get_popular_items():
    # Your database query here
    pass
```

#### 3. CDN Setup
```bash
# Configure CloudFront or similar CDN
# Cache static assets and API responses
```

### Scaling Considerations

#### Horizontal Scaling
- Deploy multiple instances of each service
- Use load balancer (Render provides this automatically)
- Implement database read replicas

#### Vertical Scaling
- Upgrade Render service plans as needed
- Increase database instance size
- Optimize memory usage

## Support & Resources

### Documentation Links
- [Render Documentation](https://docs.render.com)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://reactjs.org/docs)

### Community Support
- GitHub Issues for bug reports
- Render Community Forums
- Vercel Community Forums

### Emergency Contacts
- Database admin: [your-db-admin@company.com]
- DevOps team: [devops@company.com]
- Security team: [security@company.com]

---

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database initialized and accessible
- [ ] External services (Cloudinary, Firebase) configured
- [ ] SSL certificates active
- [ ] Domain configured (if using custom domain)
- [ ] Monitoring and logging active
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] Performance optimization applied
- [ ] Integration tests passing
- [ ] Documentation updated

**Happy Deploying! 🚀**