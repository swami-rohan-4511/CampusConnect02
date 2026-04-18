# Campus Connect

## Overview
Campus Connect is a full-stack campus life management platform built with React (frontend) and FastAPI (backend). It provides features for meetups, marketplace, lost & found, rooms, rental, clubs, jobs, notes, and food services.

## Architecture
- **Frontend**: React 18 with Material UI, Redux Toolkit, React Router
  - Located in `frontend/`
  - Runs on port 5000 (development)
  - Uses CRA (create-react-app) with react-scripts
  - Proxy configured to forward API requests to backend on port 8000

- **Backend**: FastAPI (Python)
  - Located in `backend/api-gateway/`
  - Runs on port 8000 (localhost)
  - Provides REST API for all features
  - Uses PostgreSQL database via psycopg2
  - JWT-based authentication with passlib/bcrypt

- **Database**: PostgreSQL (Replit built-in)
  - Tables: users, user_profiles, meetups, meetup_participants, items, reports, rooms, rental_items, clubs, club_members, jobs, notes, food_outlets, menus

## Project Structure
```
frontend/           - React frontend application
  src/
    components/     - Reusable components (Navbar, AdminPanel, Chat)
    features/       - Redux slices (authSlice, uiSlice)
    pages/          - Page components (Home, Login, Signup, Meetups, etc.)
backend/
  api-gateway/      - FastAPI backend API
database/           - Original SQL schema files (reference only)
```

## Running
- Start script: `bash start.sh` (runs both backend and frontend)
- Frontend: `cd frontend && npm start` (port 5000)
- Backend: `cd backend/api-gateway && python main.py` (port 8000)

## Key Configuration
- Frontend env: `frontend/.env` (PORT, HOST, DISABLE_ESLINT_PLUGIN)
- API proxy: Configured in `frontend/package.json` -> `http://localhost:8000`
- Database: Uses DATABASE_URL environment variable

## Completed Features (All Modules)
All 9 feature modules are fully built with real backend APIs and seeded data:

- **Meetups**: Create/browse/join meetups with participant count
- **Rooms**: Multi-image upload, Call + WhatsApp contact buttons, verified profile badge
- **Rental Hub**: Category pills, daily/weekly rates, condition badges, CRUD + image upload
- **Marketplace**: Negotiable chip, sold/reserved status, seller badge, CRUD + image upload
- **Stolen & Found**: LOST/FOUND badges, color-coded cards, resolve workflow, stats pills
- **Clubs**: Category filter pills, join/leave, recruiting badge, member count, detail dialog
- **Jobs & Internships**: Type/level filters, deadline urgency chips, skill tags, apply link/email
- **Notes**: Branch/semester filters, upvotes, download count, file upload, tags
- **Food**: Menu browsing, vegetarian filter, delivery badge

## API Endpoints Summary
- Auth: POST /register, POST /login, GET /me
- Meetups: GET/POST /meetups, POST /meetups/{id}/join
- Rooms: GET/POST /rooms, POST /rooms/{id}/image, DELETE /rooms/{id}
- Rental: GET/POST /rental-items, POST /rental-items/{id}/image, DELETE /rental-items/{id}
- Marketplace: GET/POST /items, POST /items/{id}/image, PATCH /items/{id}/status, DELETE /items/{id}
- Reports: GET/POST /reports, POST /reports/{id}/image, PATCH /reports/{id}/resolve, DELETE /reports/{id}
- Clubs: GET/POST /clubs, POST /clubs/{id}/join, DELETE /clubs/{id}
- Jobs: GET/POST /jobs, DELETE /jobs/{id}
- Notes: GET/POST /notes, POST /notes/{id}/file, POST /notes/{id}/upvote, POST /notes/{id}/view, DELETE /notes/{id}
- Food: GET/POST /food-outlets, GET /food-outlets/{id}/menu, POST /food-outlets/{id}/menu

## Key Notes
- JWT_SECRET_KEY auto-generates each restart (sessions clear on restart — set as env var to persist)
- File uploads stored in /uploads/, served as static files
- WebSocket/Chat not implemented (WS server missing)
- All pages show CTA hero banners to logged-out users
