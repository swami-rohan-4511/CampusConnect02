# Campus Connect

## Overview
Campus Connect is a full-stack campus life management platform for college students. It provides features for meetups, marketplace, lost & found, rooms/roommates, rental hub, clubs & communities, jobs & internships, notes sharing, and food services.

## Architecture
- **Frontend**: React 18 with Material UI, Redux Toolkit, React Router v6
  - Located in `CampusConnect/frontend/`
  - Runs on port 5000 (development)
  - Uses CRA (create-react-app) with react-scripts
  - Proxy configured to forward API requests to backend on port 8000

- **Backend**: FastAPI (Python)
  - Located in `CampusConnect/backend/api-gateway/`
  - Runs on port 8000 (localhost)
  - Provides REST API for all features
  - Uses PostgreSQL database via psycopg2
  - JWT-based authentication with bcrypt password hashing

- **Database**: PostgreSQL (Replit built-in)
  - Tables: users, meetups, meetup_participants, items, reports, rooms, rental_items, clubs, club_members, jobs, notes, food_outlets, menus

## Workflows
- **Start application**: `cd CampusConnect/frontend && PORT=5000 HOST=0.0.0.0 DANGEROUSLY_DISABLE_HOST_CHECK=true npm start` (port 5000, webview)
- **Backend API**: `cd CampusConnect/backend/api-gateway && python main.py` (port 8000, console)

## Key Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (set by Replit)
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - DB credentials
- `JWT_SECRET_KEY` - Optional; auto-generated if not set

## Deployment
- Build step builds the React frontend then serves everything via FastAPI on port 8000
- The FastAPI backend serves the built React app as static files in production
