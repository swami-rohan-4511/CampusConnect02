"""
Campus Connect - Unified FastAPI Backend
Handles all modules: Auth, Meetups, Marketplace, Stolen & Found,
Rooms, Rental Hub, Clubs, Jobs, Notes, and Food.
"""

import json
import logging
import os
import secrets
import shutil
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as bcryptlib
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from jose import jwt
from pydantic import BaseModel

# Load .env file (no-op if not present)
load_dotenv()

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)
if not os.getenv("JWT_SECRET_KEY"):
    logger.warning("JWT_SECRET_KEY not set — using auto-generated key (not safe for production).")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

# Build DATABASE_URL from individual vars if not provided directly
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pg_host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost"))
    pg_port = os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))
    pg_user = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "campus"))
    pg_pass = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "campus123"))
    pg_db   = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "campusconnect"))
    DATABASE_URL = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

SEED_DATA = os.getenv("SEED_DATA", "false").lower() == "true"
FORCE_RESEED = os.getenv("FORCE_RESEED", "false").lower() == "true"

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Path to the built React frontend (used in production)
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "../../frontend/build")
_frontend_ready = (
    os.path.isdir(FRONTEND_BUILD)
    and os.path.exists(os.path.join(FRONTEND_BUILD, "index.html"))
)

# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────
@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not already exist."""
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name     VARCHAR(255) NOT NULL,
        phone         VARCHAR(50),
        role          VARCHAR(50)  DEFAULT 'student',
        is_active     BOOLEAN      DEFAULT TRUE,
        created_at    TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS meetups (
        id                SERIAL PRIMARY KEY,
        title             VARCHAR(255) NOT NULL,
        description       TEXT,
        host_name         VARCHAR(255),
        social_handle     VARCHAR(100),
        location          VARCHAR(255),
        event_date        VARCHAR(100),
        max_participants  INT,
        participant_count INT          DEFAULT 0,
        created_by        INT REFERENCES users(id) ON DELETE SET NULL,
        created_at        TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS meetup_participants (
        id          SERIAL PRIMARY KEY,
        meetup_id   INT REFERENCES meetups(id) ON DELETE CASCADE,
        user_id     INT REFERENCES users(id)   ON DELETE CASCADE,
        rsvp_status VARCHAR(20),
        created_at  TIMESTAMP DEFAULT NOW(),
        UNIQUE(meetup_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS items (
        id               SERIAL PRIMARY KEY,
        title            VARCHAR(255) NOT NULL,
        description      TEXT         DEFAULT '',
        price            DECIMAL(10,2),
        category         VARCHAR(100),
        condition_status VARCHAR(50)  DEFAULT 'used',
        location         VARCHAR(255) DEFAULT '',
        contact_info     VARCHAR(255) DEFAULT '',
        is_negotiable    BOOLEAN      DEFAULT TRUE,
        seller_id        INT REFERENCES users(id) ON DELETE SET NULL,
        seller_name      VARCHAR(255),
        status           VARCHAR(50)  DEFAULT 'available',
        images           JSONB        DEFAULT '[]',
        created_at       TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS reports (
        id            SERIAL PRIMARY KEY,
        item_name     VARCHAR(255) NOT NULL,
        description   TEXT         DEFAULT '',
        category      VARCHAR(100),
        report_type   VARCHAR(20),
        location      VARCHAR(255) DEFAULT '',
        contact_info  VARCHAR(255) DEFAULT '',
        reported_by   INT REFERENCES users(id) ON DELETE SET NULL,
        reporter_name VARCHAR(255),
        status        VARCHAR(50)  DEFAULT 'active',
        images        JSONB        DEFAULT '[]',
        created_at    TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS rooms (
        id               SERIAL PRIMARY KEY,
        title            VARCHAR(255) NOT NULL,
        description      TEXT         DEFAULT '',
        location         VARCHAR(255) NOT NULL,
        rent_amount      DECIMAL(10,2),
        deposit_amount   DECIMAL(10,2) DEFAULT 0,
        room_type        VARCHAR(100),
        gender_preference VARCHAR(20) DEFAULT 'any',
        furnished        BOOLEAN      DEFAULT FALSE,
        amenities        JSONB        DEFAULT '[]',
        images           JSONB        DEFAULT '[]',
        owner_id         INT REFERENCES users(id) ON DELETE SET NULL,
        owner_name       VARCHAR(255),
        contact_info     VARCHAR(255),
        status           VARCHAR(50)  DEFAULT 'available',
        created_at       TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS rental_items (
        id                 SERIAL PRIMARY KEY,
        name               VARCHAR(255) NOT NULL,
        description        TEXT         DEFAULT '',
        category           VARCHAR(100),
        daily_rate         DECIMAL(10,2),
        weekly_rate        DECIMAL(10,2),
        security_deposit   DECIMAL(10,2) DEFAULT 0,
        location           VARCHAR(255) DEFAULT '',
        contact_info       VARCHAR(255) DEFAULT '',
        min_rental_days    INT          DEFAULT 1,
        condition_status   VARCHAR(50)  DEFAULT 'good',
        availability_status BOOLEAN     DEFAULT TRUE,
        images             JSONB        DEFAULT '[]',
        owner_id           INT REFERENCES users(id) ON DELETE SET NULL,
        owner_name         VARCHAR(255),
        created_at         TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS clubs (
        id               SERIAL PRIMARY KEY,
        name             VARCHAR(255) NOT NULL,
        description      TEXT         DEFAULT '',
        category         VARCHAR(100),
        faculty_advisor  VARCHAR(255) DEFAULT '',
        meeting_schedule VARCHAR(255) DEFAULT '',
        contact_email    VARCHAR(255) DEFAULT '',
        is_recruiting    BOOLEAN      DEFAULT FALSE,
        image_url        VARCHAR(500),
        president_id     INT REFERENCES users(id) ON DELETE SET NULL,
        president_name   VARCHAR(255),
        member_count     INT          DEFAULT 0,
        created_at       TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS club_members (
        id        SERIAL PRIMARY KEY,
        club_id   INT REFERENCES clubs(id) ON DELETE CASCADE,
        user_id   INT REFERENCES users(id) ON DELETE CASCADE,
        role      VARCHAR(50)  DEFAULT 'member',
        joined_at TIMESTAMP    DEFAULT NOW(),
        UNIQUE(club_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id                   SERIAL PRIMARY KEY,
        title                VARCHAR(255) NOT NULL,
        company_name         VARCHAR(255),
        description          TEXT         DEFAULT '',
        requirements         TEXT         DEFAULT '',
        job_type             VARCHAR(100),
        location             VARCHAR(255) DEFAULT '',
        salary_range         VARCHAR(100) DEFAULT '',
        application_deadline VARCHAR(100),
        contact_email        VARCHAR(255) DEFAULT '',
        apply_link           VARCHAR(500) DEFAULT '',
        experience_level     VARCHAR(50)  DEFAULT 'entry',
        skills_required      TEXT         DEFAULT '',
        posted_by            INT REFERENCES users(id) ON DELETE SET NULL,
        poster_name          VARCHAR(255),
        status               VARCHAR(50)  DEFAULT 'active',
        created_at           TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS notes (
        id             SERIAL PRIMARY KEY,
        title          VARCHAR(255) NOT NULL,
        subject        VARCHAR(255),
        description    TEXT         DEFAULT '',
        file_type      VARCHAR(50)  DEFAULT 'pdf',
        semester       INT,
        branch         VARCHAR(255) DEFAULT '',
        tags           JSONB        DEFAULT '[]',
        uploaded_by    INT REFERENCES users(id) ON DELETE SET NULL,
        uploader_name  VARCHAR(255),
        file_url       VARCHAR(500),
        upvotes        INT          DEFAULT 0,
        views          INT          DEFAULT 0,
        download_count INT          DEFAULT 0,
        created_at     TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS food_outlets (
        id                 SERIAL PRIMARY KEY,
        name               VARCHAR(255) NOT NULL,
        type               VARCHAR(100),
        description        TEXT         DEFAULT '',
        location           VARCHAR(255),
        contact_info       VARCHAR(255),
        operating_hours    VARCHAR(255),
        delivery_available BOOLEAN      DEFAULT FALSE,
        image_url          VARCHAR(500),
        owner_id           INT REFERENCES users(id) ON DELETE SET NULL,
        owner_name         VARCHAR(255),
        created_at         TIMESTAMP    DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS menus (
        id           SERIAL PRIMARY KEY,
        outlet_id    INT REFERENCES food_outlets(id) ON DELETE CASCADE,
        item_name    VARCHAR(255) NOT NULL,
        description  TEXT         DEFAULT '',
        price        DECIMAL(10,2),
        category     VARCHAR(100),
        is_vegetarian BOOLEAN     DEFAULT FALSE,
        is_available  BOOLEAN     DEFAULT TRUE,
        image_url    VARCHAR(500),
        created_at   TIMESTAMP    DEFAULT NOW()
    );
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(schema)
    logger.info("Database tables initialised.")


def seed_db():
    """Seed the database with demo data."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        if count > 0 and not FORCE_RESEED:
            logger.info("Database already has data — skipping seed. Set FORCE_RESEED=true to override.")
            return
        if FORCE_RESEED and count > 0:
            logger.info("FORCE_RESEED enabled — clearing existing data...")
            cur.execute("""
                TRUNCATE menus, food_outlets, notes, jobs, club_members, clubs,
                         rental_items, rooms, reports, meetup_participants,
                         meetups, items, users RESTART IDENTITY CASCADE
            """)

    pw_hash = bcryptlib.hashpw(b"campus123", bcryptlib.gensalt()).decode()

    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # ── Users (IDs 1-10) ────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, phone, role) VALUES
            ('admin@campus.com',         %s, 'Campus Admin',    '+91-9000000000', 'admin'),
            ('john.doe@campus.edu',      %s, 'John Doe',        '+91-9000000001', 'student'),
            ('jane.smith@campus.edu',    %s, 'Jane Smith',      '+91-9000000002', 'student'),
            ('bob.wilson@campus.edu',    %s, 'Bob Wilson',      '+91-9000000003', 'student'),
            ('alice.brown@campus.edu',   %s, 'Alice Brown',     '+91-9000000004', 'student'),
            ('raj.patel@campus.edu',     %s, 'Raj Patel',       '+91-9000000005', 'student'),
            ('priya.sharma@campus.edu',  %s, 'Priya Sharma',    '+91-9000000006', 'student'),
            ('mike.chen@campus.edu',     %s, 'Mike Chen',       '+91-9000000007', 'student'),
            ('sarah.jones@campus.edu',   %s, 'Sarah Jones',     '+91-9000000008', 'student'),
            ('dev.kumar@campus.edu',     %s, 'Dev Kumar',       '+91-9000000009', 'student')
        """, [pw_hash] * 10)

        # ── Meetups ─────────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO meetups (title, description, host_name, social_handle, location, event_date, max_participants, participant_count, created_by) VALUES
            ('Campus Hackathon 2025',
             '48-hour coding marathon with ₹2 lakh prize pool. Build anything — apps, AI, IoT. Free food and swag!',
             'CS Club','@csclub','Main Auditorium','2025-05-10 09:00:00',120,87,2),

            ('Spring Career Fair',
             'Meet 40+ top recruiters from Google, Infosys, TCS, and more. Bring your resume and portfolio.',
             'Placement Cell','@placementcell','Sports Complex','2025-05-18 10:00:00',300,214,3),

            ('Indie Music Night',
             'Campus bands and solo performers take the stage. Free entry. Acoustic, rock, jazz — all genres welcome.',
             'Music Club','@campusmusic','Open Air Amphitheatre','2025-05-24 18:30:00',200,162,4),

            ('Machine Learning Study Circle',
             'Weekly deep dive into ML concepts — neural networks, transformers, LLMs. Bring your laptop!',
             'John Doe','@johndoe_ml','Library Room 201','2025-05-07 15:00:00',25,18,2),

            ('DSLR Photography Masterclass',
             'Learn composition, lighting, and post-processing from award-winning campus photographer Priya Sharma.',
             'Photo Club','@campusphoto','Art Studio','2025-05-15 10:00:00',30,24,7),

            ('Startup Pitch Night',
             'Present your startup idea to a panel of investors and alumni. Top 3 teams win mentorship grants.',
             'E-Cell','@campusecell','Innovation Hub','2025-05-22 17:00:00',50,43,6),

            ('Yoga & Mindfulness Morning',
             'Start your day right. Certified instructor leads a 90-min session. Mats provided. Open to all.',
             'Wellness Club','@wellnessclub','Rooftop Garden','2025-05-09 06:30:00',40,31,8),

            ('Robotics Showdown',
             'Line followers, maze solvers, combat bots. Watch the best robots battle it out live!',
             'Robotics Club','@campusrobotics','Engineering Block Courtyard','2025-05-17 13:00:00',150,98,3),

            ('Book Club: Monthly Meetup',
             'This month: "Atomic Habits" by James Clear. Come discuss, debate, and recommend your next read.',
             'Literary Society','@campuslitsoc','Library Reading Hall','2025-05-06 17:00:00',20,14,9),

            ('Inter-Hostel Cricket Tournament',
             'Block A vs Block B vs Block C vs Block D. Cheer for your hostel. Prizes for top scorers.',
             'Sports Committee','@campussports','Cricket Ground','2025-05-11 08:00:00',null,200,5),

            ('Data Science Bootcamp — Day 1',
             '3-day intensive bootcamp. Python, pandas, matplotlib, sklearn. Beginners welcome. Certificate on completion.',
             'Data Science Club','@dsc_campus','CS Lab 3','2025-05-20 09:00:00',60,55,7),

            ('Cultural Fiesta — Ethnic Day',
             'Celebrate diversity! Dress in your traditional attire, enjoy folk dance and cuisine stalls.',
             'Cultural Committee','@campusculture','Central Plaza','2025-05-23 11:00:00',500,420,6),

            ('Resume Building & LinkedIn Workshop',
             'HR experts from top MNCs guide you through crafting the perfect resume and optimising your LinkedIn.',
             'Career Club','@careerclub','Seminar Hall B','2025-05-08 14:00:00',80,72,8),

            ('Open-Source Contribution Sprint',
             'Pick a real GitHub issue and fix it in 3 hours with mentors. First PR merged = free t-shirt!',
             'Dev Community','@campusdev','Computer Lab 1','2025-05-14 11:00:00',45,38,2),

            ('Night Cycling Ride',
             'Campus to the lake and back — 12 km. Helmet and lights mandatory. All fitness levels welcome.',
             'Adventure Club','@adventureclub','Main Gate','2025-05-16 20:30:00',30,22,9)
        """)

        cur.execute("""
            INSERT INTO meetup_participants (meetup_id, user_id, rsvp_status) VALUES
            (1,2,'yes'),(1,3,'yes'),(1,4,'yes'),(1,5,'maybe'),(1,6,'yes'),(1,7,'yes'),
            (2,3,'yes'),(2,4,'yes'),(2,5,'yes'),(2,6,'yes'),(2,8,'yes'),(2,9,'yes'),
            (3,2,'yes'),(3,5,'yes'),(3,7,'yes'),(3,8,'yes'),
            (4,3,'yes'),(4,5,'maybe'),(4,6,'yes'),(4,9,'yes'),
            (5,2,'yes'),(5,4,'yes'),(5,7,'yes'),(5,10,'yes'),
            (6,6,'yes'),(6,3,'yes'),(6,8,'yes'),(6,10,'yes'),
            (7,8,'yes'),(7,9,'yes'),(7,2,'yes'),
            (8,3,'yes'),(8,4,'yes'),(8,5,'yes'),(8,6,'maybe'),
            (9,9,'yes'),(9,2,'yes'),(9,7,'yes'),
            (10,2,'yes'),(10,3,'yes'),(10,4,'yes'),(10,5,'yes'),(10,6,'yes')
        """)

        # ── Marketplace ──────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO items (title, description, price, category, condition_status, location, contact_info, is_negotiable, seller_id, seller_name, status, images) VALUES

            ('MacBook Pro 14" M3 Pro',
             'Space Grey, 18GB RAM, 512GB SSD. Purchased 4 months ago. Apple Care+ valid till 2026. Comes with original box and 140W charger. Zero scratches.',
             142000.00,'Electronics','like_new','Block A Hostel, Room 214','john.doe@campus.edu',true,2,'John Doe','available',
             '["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600","https://images.unsplash.com/photo-1611186871525-e6f0ec1a1014?w=600"]'),

            ('Stewart Calculus 9th Edition',
             'Brand new, plastic wrap intact. Bought for reference but using digital. Ideal for 1st/2nd year maths.',
             1200.00,'Books','new','Library Block','jane.smith@campus.edu',false,3,'Jane Smith','available',
             '["https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600","https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600"]'),

            ('Sony WH-1000XM5 Headphones',
             'Flagship noise-cancelling headphones. Purchased 5 months ago. Excellent ANC and 30hr battery. Comes with carry case and 3 cables.',
             18500.00,'Electronics','excellent','Block B Hostel','bob.wilson@campus.edu',true,4,'Bob Wilson','available',
             '["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600","https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600"]'),

            ('Complete Engineering Drawing Set',
             'Staedtler compass, Rotring scales, protractor set, French curves, Drafter A3. Used one semester, perfect condition.',
             850.00,'Other','good','Engineering Block, Room 102','alice.brown@campus.edu',true,5,'Alice Brown','available',
             '["https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600"]'),

            ('Canon EOS 90D DSLR + 18-135mm Lens',
             '32.5MP APS-C sensor. 1 year old. Comes with 2 batteries, 64GB SD card, UV filter, and padded bag. Great for events.',
             58000.00,'Electronics','good','Photography Club Room','raj.patel@campus.edu',true,6,'Raj Patel','available',
             '["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600","https://images.unsplash.com/photo-1502982720700-bfff97f2ecac?w=600"]'),

            ('Foldable Aluminium Laptop Stand',
             'Adjustable 6 angles, compatible with 10-17" laptops, anti-slip pads. Never used — bought extra by mistake.',
             1299.00,'Electronics','new','Computer Lab','jane.smith@campus.edu',false,3,'Jane Smith','available',
             '["https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600"]'),

            ('MTB Cycle — Hero Sprint 27.5"',
             '21-speed Shimano gears, front disc brake, recently serviced. Minor handlebar scuff. Ideal for campus commute.',
             6500.00,'Bikes','good','Block C Parking','mike.chen@campus.edu',true,8,'Mike Chen','available',
             '["https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=600","https://images.unsplash.com/photo-1571188654248-7a89213a4072?w=600"]'),

            ('IKEA Study Desk + Chair Combo',
             'White MICKE desk (105×50 cm) + LÅNGFJÄLL office chair. Disassembled for easy transport. No damage.',
             5500.00,'Furniture','good','PG Quarters Block D','sarah.jones@campus.edu',true,9,'Sarah Jones','available',
             '["https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=600","https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600"]'),

            ('Bosch Induction Cooktop',
             'Single burner, 2000W, touch controls. Perfect for hostel room cooking. 8 months old, works perfectly.',
             3200.00,'Appliances','excellent','Block A Hostel','priya.sharma@campus.edu',true,7,'Priya Sharma','available',
             '["https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600"]'),

            ('Levi''s 511 Slim Jeans — 32x32',
             'Dark indigo, worn 3-4 times. Too big after weight loss. Machine washed gently, no fading.',
             900.00,'Clothing','excellent','Block B Hostel','dev.kumar@campus.edu',false,10,'Dev Kumar','available',
             '["https://images.unsplash.com/photo-1542272604-787c3835535d?w=600"]'),

            ('iPad Air 5th Gen (Wi-Fi, 64GB)',
             'Starlight colour, 2 years old, battery health 91%. Comes with Smart Folio cover, Apple Pencil 2 and cable.',
             38000.00,'Electronics','good','Block D Hostel','raj.patel@campus.edu',true,6,'Raj Patel','available',
             '["https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600","https://images.unsplash.com/photo-1587840171670-8b850147754e?w=600"]'),

            ('Organic Chemistry by Morrison Boyd',
             '6th edition, some pencil highlights in chapters 1-5, rest clean. Essential for Chem/Pharma students.',
             650.00,'Books','used','Science Block','alice.brown@campus.edu',false,5,'Alice Brown','available',
             '["https://images.unsplash.com/photo-1532012197267-da84d127e765?w=600"]'),

            ('JBL Clip 4 Bluetooth Speaker',
             'Waterproof, 10-hour battery, carabiner clip. 6 months old. Minor rubber scuff but fully functional.',
             2200.00,'Electronics','good','Block C Hostel','sarah.jones@campus.edu',true,9,'Sarah Jones','available',
             '["https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600"]'),

            ('Ergonomic Memory Foam Cushion',
             'Coccyx orthopedic design. Perfect for long study sessions. Used 2 months, washed cover. Like new.',
             799.00,'Furniture','excellent','PG Colony','mike.chen@campus.edu',false,8,'Mike Chen','available',
             '["https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600"]'),

            ('HP LaserJet M1005 Printer + Toner',
             'Prints 12 pages/min. USB + WiFi. Includes 2 spare toner cartridges. Minor exterior yellowing only.',
             4500.00,'Electronics','good','Block A Hostel','john.doe@campus.edu',true,2,'John Doe','available',
             '["https://images.unsplash.com/photo-1612815292847-9f2f72754fb1?w=600"]')
        """)

        # ── Stolen & Found ───────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO reports (item_name, description, category, report_type, location, contact_info, reported_by, reporter_name, status, images) VALUES

            ('iPhone 15 Pro — Natural Titanium',
             'Lost between Main Library and Cafeteria. Black leather MagSafe wallet attached. IMEI: 352xxxxxxx. Reward offered.',
             'electronics','lost','Main Library / Cafeteria Path','john.doe@campus.edu',2,'John Doe','active',
             '["https://images.unsplash.com/photo-1696446701796-da61225697cc?w=600"]'),

            ('Navy Blue Nike Air Max Backpack',
             'Found unattended near the Cafeteria entrance. Contains a laptop and textbooks. Contact to claim.',
             'accessories','found','Cafeteria Entrance','jane.smith@campus.edu',3,'Jane Smith','active',
             '["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"]'),

            ('Student ID + Library Card — Raj Patel',
             'ID card bundle in a clear card sleeve. Lost at Sports Complex after cricket match. Student No. 2021CE045.',
             'documents','lost','Sports Complex','raj.patel@campus.edu',6,'Raj Patel','active',
             '["https://images.unsplash.com/photo-1586892477838-2b96e85e0f96?w=600"]'),

            ('Apple AirPods Pro 2nd Gen',
             'White AirPods with MagSafe case. Found on a bench in Classroom Block C corridor. Fully charged.',
             'electronics','found','Classroom Block C, Corridor','alice.brown@campus.edu',5,'Alice Brown','active',
             '["https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600"]'),

            ('Green Fjallraven Kanken Backpack',
             'Mint green, small size. Left in Lab 204 after the Wednesday evening lab session. Contains stationery.',
             'accessories','found','Computer Lab 204','priya.sharma@campus.edu',7,'Priya Sharma','active',
             '["https://images.unsplash.com/photo-1622560480605-d83c661089a9?w=600"]'),

            ('Casio FX-991EX Scientific Calculator',
             'Lost during Maths exam in Hall 3. Name "Mike Chen" written on back with marker.',
             'stationery','lost','Exam Hall 3','mike.chen@campus.edu',8,'Mike Chen','active',
             '["https://images.unsplash.com/photo-1611117775350-ac3950990985?w=600"]'),

            ('Silver Dell XPS 13 Laptop',
             'Dell XPS 13 in silver found in Library study pods (Pod 7). Has a "Dev" sticker on lid. Handed to security desk.',
             'electronics','found','Main Library, Study Pod 7','dev.kumar@campus.edu',10,'Dev Kumar','active',
             '["https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600"]'),

            ('Red Swiss Army Wallet',
             'Victorinox red leather wallet. Contains ₹500 cash, metro card, and some cards. Lost near Canteen.',
             'accessories','lost','Central Canteen','sarah.jones@campus.edu',9,'Sarah Jones','active',
             '["https://images.unsplash.com/photo-1627123424574-724758594e93?w=600"]'),

            ('Sony WF-1000XM4 Earbuds + Case',
             'Black earbuds in case. Left on the table in Seminar Hall A after the 3 PM lecture.',
             'electronics','found','Seminar Hall A','bob.wilson@campus.edu',4,'Bob Wilson','active',
             '["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600"]'),

            ('Prescription Glasses — Thin Frame',
             'Black rectangular frame, -2.5 power. Found in the gym changing room. Stored at front desk.',
             'personal','found','Campus Gym','raj.patel@campus.edu',6,'Raj Patel','active',
             '["https://images.unsplash.com/photo-1574258495973-f010dfbb5371?w=600"]')
        """)

        # ── Rooms & Roommates ────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO rooms (title, description, location, rent_amount, deposit_amount, room_type, gender_preference, furnished, amenities, owner_id, owner_name, contact_info, status, images) VALUES

            ('Spacious AC Single Room',
             'Attached western bathroom, study desk with bookshelf, queen bed, large windows with campus view. 5-min walk to main gate.',
             'Block A, Room 301',12000.00,24000.00,'single','any',true,
             '["WiFi 100Mbps","AC","Attached Bathroom","Laundry","Hot Water","Parking","Study Desk","Wardrobe"]',
             2,'John Doe','john.doe@campus.edu','available',
             '["https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600","https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=600"]'),

            ('Furnished 2BHK — 1 Seat Available',
             'Share with 2 friendly CS students (male). Modular kitchen, 2 baths, living room. 3-min walk to campus. Strictly no smoking.',
             'Silver Oak Apartments, Near Main Gate',7500.00,15000.00,'shared','male',true,
             '["WiFi","Kitchen","2 Bathrooms","Gym","Laundry","Parking","Gas Stove","Refrigerator"]',
             3,'Jane Smith','jane.smith@campus.edu','available',
             '["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600","https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600"]'),

            ('Modern Studio — Female Preferred',
             'Ground-floor studio with private entrance, kitchenette, and attached bath. Excellent natural light. 24/7 security.',
             'Lotus Tower, Downtown Campus',10500.00,21000.00,'apartment','female',true,
             '["WiFi","AC","Kitchen","Attached Bathroom","Laundry","Parking","CCTV","Inverter"]',
             4,'Bob Wilson','bob.wilson@campus.edu','available',
             '["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600","https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600"]'),

            ('Double Sharing — Hostel Style',
             'Well-ventilated room with 2 single beds, individual study tables and lockers. Shared floor bathrooms. Mess access included.',
             'Block B, Room 205',5500.00,11000.00,'shared','male',false,
             '["WiFi","Laundry","Mess Access","Locker","Common Room","Generator Backup"]',
             5,'Alice Brown','alice.brown@campus.edu','available',
             '["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600","https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=600"]'),

            ('PG Room with Meals Included',
             'Comfortable single occupancy with home-cooked breakfast and dinner. Ideal for first-years. Owner stays on premises.',
             'Faculty Colony, Gate 3',9000.00,9000.00,'single','female',true,
             '["WiFi","Breakfast & Dinner","AC","Hot Water","Housekeeping","Parking","Inverter"]',
             7,'Priya Sharma','priya.sharma@campus.edu','available',
             '["https://images.unsplash.com/photo-1615874959474-d609969a20ed?w=600","https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600"]'),

            ('3BHK Flat — 2 Seats Available',
             'Premium flat with 3 bedrooms. 2 seats available for male students. Rooftop access, power backup, gated society.',
             'Greenfield Residency, 1.2 km from Campus',8500.00,17000.00,'shared','male',true,
             '["WiFi","AC","Kitchen","2 Bathrooms","Rooftop","Gym","Parking","Elevator"]',
             6,'Raj Patel','raj.patel@campus.edu','available',
             '["https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=600","https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600"]'),

            ('Budget Room Near Engineering Block',
             'Clean semi-furnished room. Shared bathroom (1:3 ratio). Best for engineering students — 2-min walk to labs.',
             'Block E, Near Robotics Lab',4500.00,9000.00,'single','any',false,
             '["WiFi","Shared Bathroom","Laundry","Fan","Study Table"]',
             8,'Mike Chen','mike.chen@campus.edu','available',
             '["https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=600"]'),

            ('Luxury 1BHK — All Inclusive',
             'Premium furnished apartment. AC, 50Mbps WiFi, Netflix subscription, weekly housekeeping. 500m from campus. Bills included in rent.',
             'The Residences, Campus View Tower',15000.00,30000.00,'apartment','any',true,
             '["WiFi 50Mbps","AC","Kitchen","Housekeeping","Netflix","Parking","Swimming Pool","Gym","24/7 Security"]',
             9,'Sarah Jones','sarah.jones@campus.edu','available',
             '["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600","https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?w=600"]')
        """)

        # ── Rental Hub ───────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO rental_items (name, description, category, daily_rate, weekly_rate, security_deposit, location, contact_info, min_rental_days, condition_status, availability_status, owner_id, owner_name, images) VALUES

            ('Canon EOS R6 Mark II Mirrorless Camera',
             '24.2MP full-frame, IBIS, 4K 60fps video. Includes RF 24-105mm f/4 lens, 2 batteries, 128GB CFexpress card, camera bag.',
             'camera',1200.00,7000.00,5000.00,'Photography Lab, 3rd Floor','john.doe@campus.edu',1,'excellent',true,2,'John Doe',
             '["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600","https://images.unsplash.com/photo-1502982720700-bfff97f2ecac?w=600"]'),

            ('MacBook Air M2 (16GB RAM, 512GB)',
             'Perfect for presentations, coding, video editing. Comes with charger. 100% battery health. Available for daily or weekly rental.',
             'laptop',800.00,4500.00,3000.00,'Computer Lab A','jane.smith@campus.edu',1,'excellent',true,3,'Jane Smith',
             '["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600","https://images.unsplash.com/photo-1611186871525-e6f0ec1a1014?w=600"]'),

            ('Epson EB-X51 HD Projector',
             '3800-lumen XGA projector with HDMI, VGA and USB. Ideal for presentations, movie nights, workshops. Screen and stand available.',
             'electronics',700.00,4000.00,2500.00,'AV Room, Seminar Block','bob.wilson@campus.edu',1,'good',true,4,'Bob Wilson',
             '["https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=600"]'),

            ('DJI Air 3 Drone + Smart Controller',
             '4K/60fps dual-camera drone. 46-min flight time. 3 batteries, ND filter set, carry bag included. ID proof required.',
             'electronics',1500.00,9000.00,8000.00,'Rooftop Lab, Engineering Block','alice.brown@campus.edu',1,'excellent',true,5,'Alice Brown',
             '["https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=600","https://images.unsplash.com/photo-1521405924368-64c7575a6ff4?w=600"]'),

            ('Wacom Cintiq 16 Drawing Tablet',
             '15.6" full-HD display tablet. Works with Photoshop, Illustrator, Procreate for iPad. Includes all pens and stands.',
             'electronics',500.00,2800.00,2000.00,'Design Studio, Art Block','raj.patel@campus.edu',1,'good',true,6,'Raj Patel',
             '["https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600"]'),

            ('Nikon D7500 DSLR + 50mm Prime',
             '20.9MP, 4K UHD, dual SD slot. Great portrait and event camera. Includes 50mm f/1.8 prime lens, strap, 2 batteries.',
             'camera',900.00,5500.00,4000.00,'Media Room, Journalism Dept','priya.sharma@campus.edu',1,'good',true,7,'Priya Sharma',
             '["https://images.unsplash.com/photo-1502982720700-bfff97f2ecac?w=600","https://images.unsplash.com/photo-1609081219090-a6d81d3085bf?w=600"]'),

            ('Rode NT-USB Microphone + Boom Stand',
             'Studio-quality USB condenser mic. Perfect for podcast recording, interviews, and online presentations.',
             'electronics',400.00,2200.00,1500.00,'Media Studio, Block C','mike.chen@campus.edu',1,'excellent',true,8,'Mike Chen',
             '["https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=600"]'),

            ('GoPro Hero 12 Black + Accessories Kit',
             'Waterproof 5.3K action cam. Kit includes chest mount, head strap, 3-way grip, 2 batteries, 128GB microSD.',
             'camera',600.00,3500.00,2500.00,'Sports Equipment Room','sarah.jones@campus.edu',1,'excellent',true,9,'Sarah Jones',
             '["https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600"]'),

            ('ASUS ROG Gaming Laptop (RTX 4070)',
             'Intel i9-13900H, 32GB DDR5, RTX 4070, 1TB NVMe. Ideal for GPU-heavy ML training or gaming tournaments.',
             'laptop',1200.00,7000.00,6000.00,'Gaming Room, Block D','dev.kumar@campus.edu',1,'excellent',true,10,'Dev Kumar',
             '["https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600","https://images.unsplash.com/photo-1587202372616-b43abea06c2a?w=600"]'),

            ('Canon ImagePROGRAF TC-20 Plotter',
             'A1 large-format printer. Perfect for printing engineering drawings, banners, and posters. Paper rolls included.',
             'electronics',800.00,4500.00,3000.00,'Print Lab, Architecture Block','john.doe@campus.edu',1,'good',true,2,'John Doe',
             '["https://images.unsplash.com/photo-1612815292847-9f2f72754fb1?w=600"]')
        """)

        # ── Clubs & Communities ───────────────────────────────────────────────
        cur.execute("""
            INSERT INTO clubs (name, description, category, faculty_advisor, meeting_schedule, contact_email, is_recruiting, president_id, president_name, member_count, image_url) VALUES

            ('Computer Science Club',
             'Campus tech hub for hackathons, coding competitions, and open-source projects. We''ve won 3 national hackathons.',
             'coding','Dr. Anil Sharma','Every Friday 5 PM, CS Lab 3','csclub@campus.edu',true,2,'John Doe',78,
             'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600'),

            ('Campus Music Society',
             'From classical to indie rock. Regular jam sessions, annual fests, and recording studio access for members.',
             'music','Prof. Kavita Nair','Wednesday 4 PM, Music Room','musicclub@campus.edu',true,4,'Bob Wilson',55,
             'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600'),

            ('Photography & Videography Club',
             'Award-winning club with a dedicated dark room and studio lighting gear. Monthly photowalks around campus.',
             'photography','Dr. Ritesh Meena','Saturday 10 AM, Art Studio','photoclub@campus.edu',true,7,'Priya Sharma',44,
             'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=600'),

            ('Robotics & Automation Club',
             'Building autonomous systems, participating in RoboWars, Technothon, and NASA Lunabotics competitions.',
             'robotics','Dr. Sanjay Kumar','Tuesday & Thursday 3 PM, Robotics Lab','robotics@campus.edu',true,3,'Jane Smith',38,
             'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600'),

            ('Entrepreneurship Cell (E-Cell)',
             'Connecting student innovators with investors and mentors. Hosts Startup Weekend, pitch nights, and bootcamps.',
             'entrepreneurship','Prof. Ravi Gupta','Monday 6 PM, Innovation Hub','ecell@campus.edu',true,6,'Raj Patel',62,
             'https://images.unsplash.com/photo-1556761175-4b46a572b786?w=600'),

            ('Literary Society',
             'Debates, creative writing, open-mic poetry, and a 2000+ book lending library. Annual literary fest attracts 500+.',
             'literature','Dr. Meena Joshi','Thursday 5 PM, Library Reading Hall','litsoc@campus.edu',true,9,'Sarah Jones',47,
             'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600'),

            ('Data Science & AI Club',
             'Kaggle competitions, paper reading sessions, ML model deployments, and guest lectures from industry professionals.',
             'coding','Dr. Priya Verma','Saturday 11 AM, CS Lab 1','dsaic@campus.edu',true,7,'Priya Sharma',51,
             'https://images.unsplash.com/photo-1527474305487-b87b222841cc?w=600'),

            ('Eco & Sustainability Club',
             'Campus garden, zero-waste drives, sustainability audits. Planted 500 trees on campus last year.',
             'environment','Dr. Sunita Rao','Sunday 9 AM, Campus Garden','ecoclub@campus.edu',false,8,'Mike Chen',33,
             'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=600'),

            ('Drama & Theatre Club',
             'Full-scale productions twice a year, improv workshops, and street theatre. No prior experience needed!',
             'arts','Prof. Amita Singh','Monday & Wednesday 5 PM, Open Air Stage','drama@campus.edu',true,5,'Alice Brown',41,
             'https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=600'),

            ('Sports & Adventure Club',
             'Trekking, rock climbing, night cycling, and inter-college sports leagues. All fitness levels welcome.',
             'sports','Mr. Vikram Nanda','Sunday 6 AM, Sports Ground','sportsclub@campus.edu',true,10,'Dev Kumar',69,
             'https://images.unsplash.com/photo-1517649763962-0c623066013b?w=600')
        """)

        cur.execute("""
            INSERT INTO club_members (club_id, user_id, role) VALUES
            (1,2,'president'),(1,3,'member'),(1,4,'member'),(1,5,'member'),(1,7,'member'),(1,10,'member'),
            (2,4,'president'),(2,5,'member'),(2,2,'member'),(2,9,'member'),
            (3,7,'president'),(3,2,'member'),(3,3,'member'),(3,6,'member'),
            (4,3,'president'),(4,4,'member'),(4,5,'member'),(4,8,'member'),
            (5,6,'president'),(5,3,'member'),(5,8,'member'),(5,10,'member'),
            (6,9,'president'),(6,2,'member'),(6,7,'member'),
            (7,7,'president'),(7,2,'member'),(7,6,'member'),(7,10,'member'),
            (8,8,'president'),(8,9,'member'),(8,5,'member'),
            (9,5,'president'),(9,3,'member'),(9,9,'member'),(9,7,'member'),
            (10,10,'president'),(10,2,'member'),(10,4,'member'),(10,6,'member'),(10,8,'member')
        """)

        # ── Jobs & Internships ────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO jobs (title, company_name, description, requirements, job_type, location, salary_range, contact_email, apply_link, experience_level, skills_required, posted_by, poster_name, status) VALUES

            ('Software Development Intern',
             'Google India',
             'Work on large-scale distributed systems with the Search Infrastructure team. Real ownership from day one. Relocation + housing allowance provided.',
             'B.Tech CS/IT (3rd or 4th year); strong DSA; 1 prior internship or open-source project preferred.',
             'internship','Hyderabad / Remote','₹80,000/month',
             'intern@google.com','https://careers.google.com/jobs/','entry',
             'Data Structures, Algorithms, C++/Java/Python, System Design',2,'John Doe','active'),

            ('Frontend Developer Intern',
             'Razorpay',
             'Join the Growth team building high-conversion payment UIs. Mentor-led, with dedicated career development sessions.',
             'React.js proficiency, CSS animations, API integration experience.',
             'internship','Bangalore','₹50,000/month',
             'campus@razorpay.com','https://razorpay.com/jobs/','entry',
             'React, JavaScript, CSS, REST APIs, Figma',3,'Jane Smith','active'),

            ('Machine Learning Research Intern',
             'IIT Research Lab (On-Campus)',
             'Assist faculty in NLP and computer vision research. Access to GPU cluster. Papers published get co-authorship credit.',
             '7.5+ CGPA; Python; coursework in ML/AI; bonus if familiar with PyTorch.',
             'internship','Campus — CS Department','₹15,000/month stipend',
             'mllab@campus.edu','','entry',
             'Python, PyTorch, NLP, Computer Vision, Research Writing',7,'Priya Sharma','active'),

            ('Campus Brand Ambassador',
             'Swiggy',
             'Promote Swiggy on campus, organise activations and referral drives. Flexible hours — 10 hrs/week.',
             'Excellent communication, social media presence, and on-campus network.',
             'part_time','On-Campus','₹8,000/month + performance bonus',
             'campus@swiggy.in','','entry',
             'Social Media, Communication, Event Management',6,'Raj Patel','active'),

            ('Teaching Assistant — Data Structures',
             'CS Department',
             'Conduct weekly tutorials, grade assignments and help students during office hours for the DS301 course.',
             'Completed DS301 with B+ or above. Strong communication and patience.',
             'part_time','CS Department, Room 110','₹10,000/month',
             'csdept@campus.edu','','entry',
             'C++, Data Structures, Algorithms, Teaching',2,'John Doe','active'),

            ('Content & SEO Intern',
             'The Campus Pulse (Student Media)',
             'Write 3 articles/week covering campus events, research news, and student spotlights. SEO and analytics training provided.',
             'Fluent English writing, curiosity, and a nose for a good story.',
             'part_time','Media Centre','₹6,000/month',
             'editor@campuspulse.edu','','entry',
             'Writing, SEO, WordPress, Social Media, Research',9,'Sarah Jones','active'),

            ('Graphic Design Intern',
             'Cultural Committee',
             'Create posters, social media creatives, and event banners for campus fests. Exciting portfolio opportunity.',
             'Proficiency in Adobe Illustrator/Photoshop or Figma. Portfolio required.',
             'part_time','Design Studio, Block C','₹7,500/month',
             'designteam@campus.edu','','entry',
             'Adobe Illustrator, Photoshop, Figma, Typography',5,'Alice Brown','active'),

            ('iOS App Developer Intern',
             'Startup Garage (Campus Incubator)',
             'Build the next version of the campus navigation app for iOS. Direct mentorship from a senior engineer.',
             'Swift/SwiftUI experience or willingness to learn fast. Side projects a huge plus.',
             'internship','Innovation Hub, Block F','₹25,000/month',
             'careers@campusstartups.in','https://campusstartups.in/careers','entry',
             'Swift, SwiftUI, Xcode, REST APIs, Git',10,'Dev Kumar','active'),

            ('Research Assistant — Battery Tech',
             'Electrical Engineering Department',
             'Assist PhD scholars in lithium-ion battery research. Lab work, data analysis, and literature reviews.',
             '3rd/4th year EE or ECE student. Chemistry background a plus. CGPA ≥ 7.0.',
             'part_time','EE Lab 6, Engineering Block','₹12,000/month',
             'eedept@campus.edu','','entry',
             'MATLAB, Data Analysis, Lab Safety, Technical Writing',4,'Bob Wilson','active'),

            ('Cloud Infrastructure Intern',
             'Infosys BPM',
             'Configure and monitor AWS/Azure cloud environments. Work with DevOps team on CI/CD pipelines.',
             'AWS Cloud Practitioner (preferred), Linux basics, scripting knowledge.',
             'internship','Remote / Pune Office','₹35,000/month',
             'campus.recruit@infosys.com','https://infosys.com/careers','entry',
             'AWS, Azure, Linux, Docker, Terraform, Python',8,'Mike Chen','active'),

            ('Video Editor & Reels Creator',
             'Student Affairs Office',
             'Produce short-form videos (Reels/YT Shorts) documenting campus life, fests, and achievements. 5-7 videos/week.',
             'DaVinci Resolve or Premiere Pro. Phone videography skills welcome too.',
             'part_time','Media Room, Admin Block','₹9,000/month',
             'studentaffairs@campus.edu','','entry',
             'DaVinci Resolve, Premiere Pro, After Effects, Storytelling',7,'Priya Sharma','active'),

            ('Finance & Accounting Intern',
             'Campus Credit Union',
             'Assist in bookkeeping, financial reporting, and student loan processing. Real hands-on accounting experience.',
             '2nd year Commerce/BBA student. MS Excel proficiency. Integrity and confidentiality required.',
             'internship','Administration Block, 1st Floor','₹10,000/month',
             'finance@campuscu.edu','','entry',
             'MS Excel, Tally, Accounting, Financial Reporting',3,'Jane Smith','active')
        """)

        # ── Notes & Resources ────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO notes (title, subject, description, file_type, semester, branch, tags, uploaded_by, uploader_name, download_count, upvotes) VALUES

            ('Data Structures & Algorithms — Complete Notes',
             'Computer Science',
             'Comprehensive 180-page notes covering arrays, linked lists, stacks, queues, trees, graphs, heaps, sorting, and searching. Includes time/space complexity tables.',
             'pdf',3,'Computer Science','["DSA","algorithms","CS","trees","graphs"]',2,'John Doe',342,128),

            ('Calculus — Formulas, Theorems & 100 Solved Problems',
             'Mathematics',
             'Stewart Calculus aligned. Limits, derivatives, integration, multivariable calculus. 100 fully solved exam-style problems with step-by-step solutions.',
             'pdf',1,'Mathematics','["calculus","math","limits","integration","derivatives"]',3,'Jane Smith',418,167),

            ('Circuit Analysis — Complete Study Guide',
             'Electrical Engineering',
             'DC/AC circuits, KVL, KCL, mesh & nodal analysis, Thevenin/Norton theorems, superposition, phasors, and filter design. 40+ solved examples.',
             'pdf',3,'Electrical Engineering','["circuits","EE","KVL","KCL","Thevenin"]',4,'Bob Wilson',215,84),

            ('Thermodynamics — All 4 Laws with Applications',
             'Mechanical Engineering',
             'First through fourth laws of thermodynamics, entropy, enthalpy, Carnot cycle, refrigeration cycles, and steam tables. Previous year question solutions included.',
             'pdf',5,'Mechanical Engineering','["thermodynamics","ME","carnot","entropy"]',5,'Alice Brown',189,71),

            ('Strategic Management — MBA Exam Notes',
             'Business Administration',
             'Porter''s Five Forces, SWOT/PESTLE, Blue Ocean Strategy, BCG Matrix, value chain analysis, and 15 case study summaries.',
             'pdf',7,'Business Administration','["management","strategy","MBA","Porter","SWOT"]',2,'John Doe',276,105),

            ('Operating Systems — Process & Memory Management',
             'Computer Science',
             'CPU scheduling algorithms (FCFS, SJF, RR, Priority), deadlock prevention, paging, segmentation, virtual memory. With diagrams and examples.',
             'pdf',5,'Computer Science','["OS","operating systems","scheduling","paging","memory"]',7,'Priya Sharma',298,112),

            ('Digital Electronics & Logic Design',
             'Electronics & Communication',
             'Boolean algebra, K-maps, combinational and sequential circuits, flip-flops, counters, registers, and FSMs. Lab manual included.',
             'pdf',4,'Electronics & Communication','["digital electronics","logic gates","flip-flops","VLSI"]',6,'Raj Patel',167,63),

            ('Engineering Mathematics — Linear Algebra',
             'Mathematics',
             'Matrices, determinants, eigenvalues/eigenvectors, vector spaces, linear transformations. GATE-oriented with 60 MCQs.',
             'pdf',2,'Mathematics','["linear algebra","matrices","eigenvalues","GATE","math"]',8,'Mike Chen',231,89),

            ('Human Resource Management — Notes & Cases',
             'Business Administration',
             'Recruitment, training, performance appraisal, compensation, labour laws, organisational behaviour. Real HR case studies from Indian companies.',
             'pdf',5,'Business Administration','["HRM","HR","MBA","recruitment","performance"]',9,'Sarah Jones',143,54),

            ('Computer Networks — OSI Model to TCP/IP',
             'Computer Science',
             'OSI layers, TCP/IP, IP addressing, subnetting, routing protocols (OSPF, BGP), HTTP/HTTPS, DNS, firewalls, and network security basics.',
             'pdf',6,'Computer Science','["networking","OSI","TCP/IP","routing","CN"]',10,'Dev Kumar',312,121),

            ('Structural Analysis — Beams & Trusses',
             'Civil Engineering',
             'Method of joints, method of sections, BMD/SFD for beams, influence lines, and deflection calculations. Includes hand-drawn diagrams.',
             'pdf',4,'Civil Engineering','["structural","beams","trusses","BMD","civil"]',4,'Bob Wilson',128,47),

            ('Machine Learning — From Regression to CNNs',
             'Computer Science',
             'Linear/logistic regression, decision trees, SVM, k-means, neural networks, CNNs, RNNs, and transformer basics. Python code snippets included.',
             'pdf',7,'Computer Science','["ML","machine learning","neural networks","deep learning","AI"]',7,'Priya Sharma',389,154),

            ('Fluid Mechanics — Key Concepts & Solved Problems',
             'Mechanical Engineering',
             'Bernoulli, continuity equation, Reynolds number, pipe flow, boundary layer theory, pumps & turbines. 35 solved university exam problems.',
             'pdf',5,'Mechanical Engineering','["fluid mechanics","Bernoulli","pipe flow","ME"]',6,'Raj Patel',156,59),

            ('Financial Accounting — Double Entry to Final Accounts',
             'Commerce',
             'Journal entries, ledger, trial balance, P&L statement, balance sheet, depreciation methods, and cash flow analysis. BBA/BCom oriented.',
             'pdf',1,'Commerce','["accounting","finance","journal","balance sheet","BBA"]',3,'Jane Smith',198,76),

            ('Immunology & Microbiology — Lecture Notes',
             'Life Sciences',
             'Innate/adaptive immunity, antigen-antibody reactions, vaccines, microbial pathogens, and lab techniques (PCR, ELISA). Ideal for Biotech students.',
             'pdf',6,'Life Sciences','["immunology","microbiology","biology","vaccines","biotech"]',9,'Sarah Jones',112,41)
        """)

        # ── Food Outlets & Menus ─────────────────────────────────────────────
        cur.execute("""
            INSERT INTO food_outlets (name, type, description, location, contact_info, operating_hours, delivery_available, owner_id, owner_name, image_url) VALUES

            ('The Campus Brew',
             'cafe',
             'Specialty coffee, artisan sandwiches, and wholesome snacks. Cosy seating with fast WiFi — your second study spot.',
             'Library Ground Floor','brew@campus.edu','7:00 AM – 10:00 PM',false,2,'John Doe',
             'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600'),

            ('Aahar Main Mess',
             'mess',
             'Nutritious home-style meals every day. Vegetarian and non-vegetarian options. Unlimited rice, dal, and roti.',
             'Hostel Block A, Ground Floor','mess@campus.edu','7:00 AM – 9:30 PM',false,3,'Jane Smith',
             'https://images.unsplash.com/photo-1567521464027-f127ff144326?w=600'),

            ('Campus Food Court',
             'food_court',
             '8-stall food court: Indian, Chinese, South Indian, Lebanese, Rolls, Juice bar, Ice cream. Seating for 200.',
             'Central Campus Plaza','foodcourt@campus.edu','10:00 AM – 11:00 PM',true,4,'Bob Wilson',
             'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600'),

            ('Pizza Lab',
             'delivery',
             'Hand-tossed artisan pizzas, pastas, and garlic bread. Order online for 30-min campus delivery.',
             'Block D, Near Dormitories','pizzalab@campus.edu','11:00 AM – 11:30 PM',true,5,'Alice Brown',
             'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600'),

            ('Spice Route — South Indian Kitchen',
             'restaurant',
             'Authentic dosas, idlis, uttapam, and meals. Fresh coconut chutney made every morning. Caters to large groups.',
             'Academic Block, Gate 2 Side','spiceroute@campus.edu','7:30 AM – 3:30 PM',false,7,'Priya Sharma',
             'https://images.unsplash.com/photo-1630383249896-424e482df921?w=600'),

            ('Fitness Fuel — Health Bar',
             'cafe',
             'Protein shakes, fresh juices, açaí bowls, and granola bars. Post-gym nutrition and vegan options available.',
             'Near Campus Gymnasium','healthbar@campus.edu','6:00 AM – 9:00 PM',false,8,'Mike Chen',
             'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=600'),

            ('Burger Hub',
             'delivery',
             'Loaded smash burgers, loaded fries, and thick shakes. Customise your patty — chicken, veg, or paneer.',
             'Block B, Ground Floor','burgerhub@campus.edu','12:00 PM – 12:00 AM',true,6,'Raj Patel',
             'https://images.unsplash.com/photo-1550547660-d9450f859349?w=600'),

            ('Night Owl Canteen',
             'canteen',
             'Open till 2 AM for late-night study fuel. Maggi, sandwiches, chai, coffee, and quick bites. Cash only.',
             'Block C, Behind Computer Lab','nightcanteen@campus.edu','8:00 PM – 2:00 AM',false,9,'Sarah Jones',
             'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600')
        """)

        cur.execute("""
            INSERT INTO menus (outlet_id, item_name, description, price, category, is_vegetarian, is_available) VALUES
            -- Campus Brew (1)
            (1,'Flat White',          'Velvety espresso with microfoam steamed milk',                  180.00,'beverages',  true,  true),
            (1,'Cold Brew',           'Slow-steeped 18-hr cold brew, served over ice',                 200.00,'beverages',  true,  true),
            (1,'Avocado Toast',       'Sourdough, smashed avo, cherry tomatoes, sea salt',             280.00,'snacks',     true,  true),
            (1,'Club Sandwich',       'Triple-decker chicken, lettuce, tomato, mayo, fries',           320.00,'sandwiches', false, true),
            (1,'Blueberry Cheesecake','New York-style slice with blueberry compote',                   180.00,'bakery',     true,  true),
            (1,'Veggie Wrap',         'Hummus, grilled veggies, feta, spinach tortilla',              220.00,'wraps',      true,  true),

            -- Aahar Main Mess (2)
            (2,'Chicken Biryani',     'Aromatic basmati rice with tender chicken and fried onions',    130.00,'main_course',false, true),
            (2,'Paneer Butter Masala','Cottage cheese in rich tomato-cream gravy',                     110.00,'main_course',true,  true),
            (2,'Dal Tadka',           'Yellow lentils tempered with cumin, garlic and dried chilli',    70.00,'main_course',true,  true),
            (2,'Veg Pulao',           'Fragrant basmati rice with seasonal vegetables and whole spices', 90.00,'main_course',true,  true),
            (2,'Egg Curry',           'Boiled eggs in a spiced onion-tomato gravy',                    100.00,'main_course',false, true),
            (2,'Gulab Jamun',         'Soft milk dumplings in rose-flavoured sugar syrup',              40.00,'desserts',   true,  true),
            (2,'Raita',               'Chilled yoghurt with cucumber, cumin and coriander',             30.00,'sides',      true,  true),

            -- Food Court (3)
            (3,'Margherita Pizza',    'Thin-crust with San Marzano tomato and mozzarella',             190.00,'pizza',      true,  true),
            (3,'Chicken Tikka Wrap',  'Tandoor-marinated chicken, mint chutney, onion in a roti',     180.00,'wraps',      false, true),
            (3,'Veg Hakka Noodles',   'Stir-fried noodles with mixed veggies in soy-ginger sauce',    130.00,'chinese',    true,  true),
            (3,'Masala Dosa',         'Crispy rice crepe stuffed with spiced potato, sambar, chutney', 100.00,'south_indian',true, true),
            (3,'Falafel Bowl',        'Baked falafel, hummus, tabouleh, pita and harissa',             220.00,'lebanese',   true,  true),
            (3,'Mango Lassi',         'Thick chilled yoghurt drink with Alphonso mango pulp',           80.00,'beverages',  true,  true),

            -- Pizza Lab (4)
            (4,'Pepperoni Feast',     'Double pepperoni, mozzarella, tomato on hand-tossed crust',     380.00,'pizza',      false, true),
            (4,'BBQ Chicken Pizza',   'Smoky BBQ sauce, grilled chicken, red onions, jalapeño',        360.00,'pizza',      false, true),
            (4,'Farm Fresh Veg Pizza','Capsicum, olives, mushrooms, corn, pesto base, mozzarella',     300.00,'pizza',      true,  true),
            (4,'Penne Arrabbiata',    'Al-dente penne in spicy garlic-tomato sauce with fresh basil',  260.00,'pasta',      true,  true),
            (4,'Stuffed Garlic Bread','Herb butter, cheese stuffed baguette baked to golden',          150.00,'appetizers', true,  true),
            (4,'Tiramisu',            'Classic Italian espresso-soaked ladyfingers and mascarpone',     200.00,'desserts',   true,  true),

            -- Spice Route (5)
            (5,'Masala Dosa',         'Extra-crispy, served with three chutneys and sambar',           100.00,'south_indian',true, true),
            (5,'Idli Sambar (3 pcs)', 'Steamed rice cakes with lentil sambar and coconut chutney',     80.00,'south_indian',true, true),
            (5,'Uttapam',             'Thick rice pancake topped with onion, tomato, and green chilli', 90.00,'south_indian',true, true),
            (5,'Vada (2 pcs)',        'Crispy urad dal fritters served hot with chutney',               60.00,'south_indian',true, true),
            (5,'Filter Coffee',       'Freshly brewed south Indian decoction with warm milk',           50.00,'beverages',  true,  true),

            -- Fitness Fuel (6)
            (6,'Whey Protein Shake',  'Chocolate or vanilla, 25g protein, blended with almond milk',   220.00,'beverages',  true,  true),
            (6,'Açaí Bowl',           'Blended açaí, banana, topped with granola and fresh berries',   280.00,'bowls',      true,  true),
            (6,'Green Detox Juice',   'Spinach, cucumber, ginger, lemon and apple pressed fresh',      150.00,'beverages',  true,  true),
            (6,'Peanut Butter Toast', 'Multigrain bread, natural PB, banana slices and chia seeds',    160.00,'snacks',     true,  true),

            -- Burger Hub (7)
            (7,'Classic Smash Burger','Double beef smash patty, cheddar, pickles, special sauce',      350.00,'burgers',    false, true),
            (7,'Crispy Chicken Burger','Buttermilk-brined fried chicken, sriracha slaw, brioche bun',  320.00,'burgers',    false, true),
            (7,'Paneer Tikka Burger', 'Spiced paneer, mint mayo, lettuce, caramelised onions',         270.00,'burgers',    true,  true),
            (7,'Loaded Fries',        'Shoestring fries, cheese sauce, jalapeños, spring onions',      180.00,'sides',      true,  true),
            (7,'Oreo Thick Shake',    'Blended Oreo, vanilla ice cream and whole milk — 500ml',        200.00,'beverages',  true,  true),

            -- Night Owl Canteen (8)
            (8,'Masala Maggi',        'Instant noodles with onion, tomato, capsicum and spices',        60.00,'snacks',     true,  true),
            (8,'Grilled Cheese Toast','Butter-grilled bread loaded with processed and cheddar cheese',  80.00,'snacks',     true,  true),
            (8,'Cutting Chai (2 cups)','Strong ginger-cardamom tea — the classic campus night fuel',    30.00,'beverages',  true,  true),
            (8,'Egg Bhurji Roll',     'Scrambled eggs with spices wrapped in paratha',                 100.00,'snacks',     false, true),
            (8,'Classic Black Coffee','Instant dark roast, strong and unsweetened',                     40.00,'beverages',  true,  true)
        """)

    logger.info("Demo data seeded successfully. Login: any demo email / password: campus123")


# ─────────────────────────────────────────────
# App lifecycle
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if SEED_DATA or FORCE_RESEED:
        seed_db()
    yield


app = FastAPI(
    title="Campus Connect API",
    description="Unified backend for the Campus Connect platform.",
    version="2.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# SPA routing — serve index.html for browser navigations on known frontend paths
_SPA_PATHS = {
    "/", "/meetups", "/marketplace", "/stolen-found", "/rooms", "/rental",
    "/clubs", "/jobs", "/notes", "/food", "/profile", "/login", "/signup", "/admin",
}


@app.middleware("http")
async def spa_middleware(request: Request, call_next):
    if _frontend_ready:
        path = request.url.path
        accept = request.headers.get("accept", "")
        if "text/html" in accept and path in _SPA_PATHS:
            return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))
    return await call_next(request)


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


def create_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _remove_upload(image_url: str):
    """Delete a locally-stored upload file by its URL path."""
    try:
        filename = image_url.split("/uploads/")[-1]
        fp = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(fp):
            os.remove(fp)
    except Exception:
        pass


# ─────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None


class MeetupCreate(BaseModel):
    title: str
    description: Optional[str] = None
    host_name: str
    social_handle: Optional[str] = None
    location: str
    event_date: str
    max_participants: Optional[int] = None


class RSVPRequest(BaseModel):
    status: str


class MarketplaceItemCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    category: str
    condition_status: Optional[str] = "used"
    location: Optional[str] = ""
    contact_info: Optional[str] = ""
    is_negotiable: Optional[bool] = True


class ReportCreate(BaseModel):
    item_name: str
    description: Optional[str] = ""
    category: str
    report_type: str
    location: Optional[str] = ""
    contact_info: Optional[str] = ""


class RoomCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    location: str
    rent_amount: float
    deposit_amount: Optional[float] = 0
    room_type: str
    gender_preference: Optional[str] = "any"
    amenities: Optional[list] = []
    contact_info: Optional[str] = ""


class RentalItemCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    daily_rate: float
    weekly_rate: Optional[float] = None
    security_deposit: Optional[float] = 0
    location: Optional[str] = ""
    contact_info: Optional[str] = ""
    min_rental_days: Optional[int] = 1
    condition_status: Optional[str] = "good"


class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    faculty_advisor: Optional[str] = ""
    meeting_schedule: Optional[str] = ""
    contact_email: Optional[str] = ""
    is_recruiting: Optional[bool] = False


class JobCreate(BaseModel):
    title: str
    company_name: str
    description: Optional[str] = ""
    requirements: Optional[str] = ""
    job_type: str
    location: Optional[str] = ""
    salary_range: Optional[str] = ""
    application_deadline: Optional[str] = None
    contact_email: Optional[str] = ""
    apply_link: Optional[str] = ""
    experience_level: Optional[str] = "entry"
    skills_required: Optional[str] = ""


class NoteCreate(BaseModel):
    title: str
    subject: str
    description: Optional[str] = ""
    file_type: Optional[str] = "pdf"
    semester: Optional[int] = None
    branch: Optional[str] = ""
    tags: Optional[list] = []


class FoodOutletCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    location: Optional[str] = None
    contact_info: Optional[str] = None
    operating_hours: Optional[str] = None
    delivery_available: Optional[bool] = False


class MenuItemCreate(BaseModel):
    item_name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_vegetarian: Optional[bool] = True
    is_available: Optional[bool] = True


# ─────────────────────────────────────────────
# GENERAL
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    if _frontend_ready:
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))
    return {"message": "Campus Connect API", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterRequest):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = bcryptlib.hashpw(req.password.encode(), bcryptlib.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name, phone, role) "
            "VALUES (%s, %s, %s, %s, 'student') RETURNING id, email, full_name, role",
            (req.email, hashed, req.full_name, req.phone),
        )
        user = dict(cur.fetchone())
        return {"access_token": create_token(user["id"], user["email"], user["role"]), "user": user}


@app.post("/auth/login")
async def login(req: LoginRequest):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, email, password_hash, full_name, role, is_active FROM users WHERE email = %s",
            (req.email,),
        )
        user = cur.fetchone()
        if not user or not bcryptlib.checkpw(req.password.encode(), user["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Account disabled")
        token = create_token(user["id"], user["email"], user["role"])
        return {
            "access_token": token,
            "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]},
        }


@app.get("/auth/verify-token")
async def verify_token(user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, full_name, role FROM users WHERE id = %s", (user["user_id"],))
        db_user = cur.fetchone()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(db_user)


@app.get("/auth/users")
async def get_users(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


@app.delete("/auth/users/{user_id}")
async def delete_user(user_id: int, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return {"message": "User deleted"}


@app.patch("/auth/users/{user_id}/role")
async def update_user_role(user_id: int, body: dict, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    new_role = body.get("role")
    if new_role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'admin'")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "UPDATE users SET role = %s WHERE id = %s RETURNING id, email, full_name, role",
            (new_role, user_id),
        )
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(updated)


@app.get("/profile/activity")
async def get_my_activity(user=Depends(get_current_user)):
    uid = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, type, location, image_url, created_at FROM food_outlets WHERE owner_id=%s ORDER BY created_at DESC", (uid,))
        food_stalls = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, title, description, location, event_date, created_at FROM meetups WHERE created_by=%s ORDER BY created_at DESC", (uid,))
        meetups = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, title, price, category, status, created_at FROM items WHERE seller_id=%s ORDER BY created_at DESC", (uid,))
        marketplace = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, title, room_type, rent_amount, location, status, created_at FROM rooms WHERE owner_id=%s ORDER BY created_at DESC", (uid,))
        rooms = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, name, category, daily_rate, availability_status, created_at FROM rental_items WHERE owner_id=%s ORDER BY created_at DESC", (uid,))
        rentals = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, name, category, created_at FROM clubs WHERE president_id=%s ORDER BY created_at DESC", (uid,))
        clubs = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, title, company_name, job_type, status, created_at FROM jobs WHERE posted_by=%s ORDER BY created_at DESC", (uid,))
        jobs = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id, title, subject, file_type, download_count, created_at FROM notes WHERE uploaded_by=%s ORDER BY created_at DESC", (uid,))
        notes = [dict(r) for r in cur.fetchall()]
        return dict(food_stalls=food_stalls, meetups=meetups, marketplace=marketplace,
                    rooms=rooms, rentals=rentals, clubs=clubs, jobs=jobs, notes=notes)


# ─────────────────────────────────────────────
# MEETUPS
# ─────────────────────────────────────────────
@app.get("/meetups")
async def get_meetups():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM meetups ORDER BY event_date DESC")
        return [dict(r) for r in cur.fetchall()]


@app.post("/meetups")
async def create_meetup(meetup: MeetupCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO meetups (title, description, host_name, social_handle, location,
               event_date, max_participants, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (meetup.title, meetup.description, meetup.host_name, meetup.social_handle,
             meetup.location, meetup.event_date, meetup.max_participants, user["user_id"]),
        )
        return dict(cur.fetchone())


@app.post("/meetups/{meetup_id}/rsvp")
async def rsvp_meetup(meetup_id: int, rsvp: RSVPRequest, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO meetup_participants (meetup_id, user_id, rsvp_status) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            (meetup_id, user["user_id"], rsvp.status),
        )
        if rsvp.status == "yes":
            cur.execute("UPDATE meetups SET participant_count = participant_count + 1 WHERE id=%s", (meetup_id,))
    return {"message": "RSVP recorded"}


@app.delete("/meetups/{meetup_id}")
async def delete_meetup(meetup_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT created_by FROM meetups WHERE id=%s", (meetup_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meetup not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM meetups WHERE id=%s", (meetup_id,))
    return {"message": "Meetup deleted"}


# ─────────────────────────────────────────────
# MARKETPLACE
# ─────────────────────────────────────────────
@app.get("/marketplace")
async def get_marketplace(category: Optional[str] = None, status: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT i.*, u.full_name AS seller_display_name, u.email AS seller_email,
                   u.created_at AS seller_joined
            FROM items i LEFT JOIN users u ON i.seller_id = u.id
        """
        conditions, params = [], []
        if category and category != "all":
            conditions.append("i.category = %s"); params.append(category)
        if status and status != "all":
            conditions.append("i.status = %s"); params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.created_at DESC"
        cur.execute(query, params)
        result = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result


@app.post("/marketplace")
async def create_marketplace_item(item: MarketplaceItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        seller_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO items (title, description, price, category, condition_status,
               location, contact_info, is_negotiable, seller_id, seller_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'available') RETURNING *""",
            (item.title, item.description, item.price, item.category, item.condition_status,
             item.location, item.contact_info, item.is_negotiable, user["user_id"], seller_name),
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row


@app.patch("/marketplace/{item_id}/status")
async def update_marketplace_status(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE items SET status=%s WHERE id=%s RETURNING *", (body.get("status", "available"), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.patch("/marketplace/{item_id}")
async def update_marketplace_item(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["title", "description", "price", "category", "condition_status", "location", "contact_info", "is_negotiable"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE items SET {set_clause} WHERE id=%s RETURNING *", [*updates.values(), item_id])
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.post("/marketplace/{item_id}/image")
async def upload_marketplace_image(item_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id, images FROM items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"market_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(file.file, f)
        updated_images = (row["images"] or []) + [f"/uploads/{filename}"]
        cur.execute("UPDATE items SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/marketplace/{item_id}/image")
async def delete_marketplace_image(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id, images FROM items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        updated_images = [img for img in (row["images"] or []) if img != image_url]
        cur.execute("UPDATE items SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), item_id))
        _remove_upload(image_url)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/marketplace/{item_id}")
async def delete_marketplace_item(item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM items WHERE id=%s", (item_id,))
    return {"message": "Item removed"}


# ─────────────────────────────────────────────
# STOLEN & FOUND
# ─────────────────────────────────────────────
@app.get("/stolen-found")
async def get_reports(report_type: Optional[str] = None, category: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT r.*, u.full_name AS reporter_display_name, u.created_at AS reporter_joined
            FROM reports r LEFT JOIN users u ON r.reported_by = u.id
        """
        conditions, params = [], []
        if report_type and report_type != "all":
            conditions.append("r.report_type = %s"); params.append(report_type)
        if category and category != "all":
            conditions.append("r.category = %s"); params.append(category)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY r.created_at DESC"
        cur.execute(query, params)
        result = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result


@app.post("/stolen-found")
async def create_report(report: ReportCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        reporter_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO reports (item_name, description, category, report_type, location,
               contact_info, reported_by, reporter_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'active') RETURNING *""",
            (report.item_name, report.description, report.category, report.report_type,
             report.location, report.contact_info, user["user_id"], reporter_name),
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row


@app.post("/stolen-found/{report_id}/image")
async def upload_report_image(report_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by, images FROM reports WHERE id=%s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"report_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(file.file, f)
        updated_images = (row["images"] or []) + [f"/uploads/{filename}"]
        cur.execute("UPDATE reports SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), report_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.patch("/stolen-found/{report_id}/status")
async def update_report_status(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by FROM reports WHERE id=%s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE reports SET status=%s WHERE id=%s RETURNING *", (body.get("status", "active"), report_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.post("/stolen-found/{report_id}/mark-resolved")
async def resolve_report(report_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE reports SET status='resolved' WHERE id=%s RETURNING *", (report_id,))
        updated = cur.fetchone()
        if not updated: raise HTTPException(status_code=404, detail="Report not found")
        updated = dict(updated)
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.patch("/stolen-found/{report_id}")
async def update_report(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by FROM reports WHERE id=%s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["item_name", "description", "category", "report_type", "location", "contact_info"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE reports SET {set_clause} WHERE id=%s RETURNING *", [*updates.values(), report_id])
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/stolen-found/{report_id}/image")
async def delete_report_image(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by, images FROM reports WHERE id=%s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        updated_images = [img for img in (row["images"] or []) if img != image_url]
        cur.execute("UPDATE reports SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), report_id))
        _remove_upload(image_url)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/stolen-found/{report_id}")
async def delete_report(report_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT reported_by FROM reports WHERE id=%s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM reports WHERE id=%s", (report_id,))
    return {"message": "Report deleted"}


# ─────────────────────────────────────────────
# ROOMS
# ─────────────────────────────────────────────
@app.get("/rooms")
async def get_rooms(status: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if status:
            cur.execute("SELECT * FROM rooms WHERE status=%s ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM rooms ORDER BY created_at DESC")
        result = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("amenities") is None: d["amenities"] = []
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result


@app.post("/rooms")
async def create_room(room: RoomCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO rooms (title, description, location, rent_amount, deposit_amount,
               room_type, gender_preference, amenities, contact_info, owner_id, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'available') RETURNING *""",
            (room.title, room.description, room.location, room.rent_amount, room.deposit_amount,
             room.room_type, room.gender_preference, json.dumps(room.amenities),
             room.contact_info, user["user_id"]),
        )
        row = dict(cur.fetchone())
        if row.get("amenities") is None: row["amenities"] = []
        if row.get("images") is None: row["images"] = []
        return row


@app.patch("/rooms/{room_id}/status")
async def update_room_status(room_id: int, body: dict, user=Depends(get_current_user)):
    new_status = body.get("status")
    if new_status not in ("available", "taken"):
        raise HTTPException(status_code=400, detail="Status must be 'available' or 'taken'")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rooms WHERE id=%s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE rooms SET status=%s WHERE id=%s RETURNING *", (new_status, room_id))
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.patch("/rooms/{room_id}")
async def update_room(room_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rooms WHERE id=%s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["title", "description", "location", "rent_amount", "deposit_amount", "room_type", "gender_preference", "contact_info"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if "amenities" in body:
            updates["amenities"] = json.dumps(body["amenities"])
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE rooms SET {set_clause} WHERE id=%s RETURNING *", [*updates.values(), room_id])
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.post("/rooms/{room_id}/image")
async def upload_room_image(room_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rooms WHERE id=%s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"room_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(file.file, f)
        updated_images = (row["images"] or []) + [f"/uploads/{filename}"]
        cur.execute("UPDATE rooms SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), room_id))
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/rooms/{room_id}/image")
async def delete_room_image(room_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rooms WHERE id=%s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        updated_images = [img for img in (row["images"] or []) if img != image_url]
        cur.execute("UPDATE rooms SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), room_id))
        _remove_upload(image_url)
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/rooms/{room_id}")
async def delete_room(room_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT owner_id FROM rooms WHERE id=%s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM rooms WHERE id=%s", (room_id,))
    return {"message": "Room deleted"}


# ─────────────────────────────────────────────
# RENTAL HUB
# ─────────────────────────────────────────────
@app.get("/rental")
async def get_rentals(category: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT r.*, u.full_name AS owner_display_name, u.email AS owner_email,
                   u.created_at AS owner_joined
            FROM rental_items r LEFT JOIN users u ON r.owner_id = u.id
        """
        if category and category != "all":
            cur.execute(query + " WHERE r.category=%s ORDER BY r.created_at DESC", (category,))
        else:
            cur.execute(query + " ORDER BY r.created_at DESC")
        result = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result


@app.post("/rental")
async def create_rental(item: RentalItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        owner_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO rental_items (name, description, category, daily_rate, weekly_rate,
               security_deposit, location, contact_info, min_rental_days, condition_status,
               owner_id, owner_name, availability_status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true) RETURNING *""",
            (item.name, item.description, item.category, item.daily_rate, item.weekly_rate,
             item.security_deposit, item.location, item.contact_info, item.min_rental_days,
             item.condition_status, user["user_id"], owner_name),
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row


@app.patch("/rental/{item_id}/availability")
async def toggle_rental_availability(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rental_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE rental_items SET availability_status=%s WHERE id=%s RETURNING *",
                    (body.get("availability_status", True), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.patch("/rental/{item_id}")
async def update_rental(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rental_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["name", "description", "category", "daily_rate", "weekly_rate", "security_deposit",
                   "location", "contact_info", "min_rental_days", "condition_status"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE rental_items SET {set_clause} WHERE id=%s RETURNING *", [*updates.values(), item_id])
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.post("/rental/{item_id}/image")
async def upload_rental_image(item_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rental_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"rental_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(file.file, f)
        updated_images = (row["images"] or []) + [f"/uploads/{filename}"]
        cur.execute("UPDATE rental_items SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/rental/{item_id}/image")
async def delete_rental_image(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rental_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        updated_images = [img for img in (row["images"] or []) if img != image_url]
        cur.execute("UPDATE rental_items SET images=%s WHERE id=%s RETURNING *", (json.dumps(updated_images), item_id))
        _remove_upload(image_url)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated


@app.delete("/rental/{item_id}")
async def delete_rental(item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT owner_id FROM rental_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM rental_items WHERE id=%s", (item_id,))
    return {"message": "Item deleted"}


# ─────────────────────────────────────────────
# CLUBS
# ─────────────────────────────────────────────
@app.get("/clubs")
async def get_clubs():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.*, u.full_name AS president_display_name,
                   (SELECT COUNT(*) FROM club_members cm WHERE cm.club_id = c.id) AS actual_member_count
            FROM clubs c LEFT JOIN users u ON c.president_id = u.id
            ORDER BY c.name
        """)
        return [dict(r) for r in cur.fetchall()]


@app.post("/clubs")
async def create_club(club: ClubCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        president_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO clubs (name, description, category, faculty_advisor, meeting_schedule,
               contact_email, is_recruiting, president_id, president_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (club.name, club.description, club.category, club.faculty_advisor,
             club.meeting_schedule, club.contact_email, club.is_recruiting,
             user["user_id"], president_name),
        )
        return dict(cur.fetchone())


@app.post("/clubs/{club_id}/join")
async def join_club(club_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM club_members WHERE club_id=%s AND user_id=%s", (club_id, user["user_id"]))
        if cur.fetchone():
            cur.execute("DELETE FROM club_members WHERE club_id=%s AND user_id=%s", (club_id, user["user_id"]))
            cur.execute("UPDATE clubs SET member_count = GREATEST(member_count - 1, 0) WHERE id=%s", (club_id,))
            return {"message": "left"}
        cur.execute("INSERT INTO club_members (club_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (club_id, user["user_id"]))
        cur.execute("UPDATE clubs SET member_count = member_count + 1 WHERE id=%s", (club_id,))
    return {"message": "joined"}


@app.delete("/clubs/{club_id}")
async def delete_club(club_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT president_id FROM clubs WHERE id=%s", (club_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Club not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM clubs WHERE id=%s", (club_id,))
    return {"message": "Club deleted"}


# ─────────────────────────────────────────────
# JOBS
# ─────────────────────────────────────────────
@app.get("/jobs")
async def get_jobs(job_type: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        base = "SELECT j.*, u.full_name AS poster_display FROM jobs j LEFT JOIN users u ON j.posted_by=u.id WHERE j.status='active'"
        if job_type and job_type != "all":
            cur.execute(base + " AND j.job_type=%s ORDER BY j.created_at DESC", (job_type,))
        else:
            cur.execute(base + " ORDER BY j.created_at DESC")
        return [dict(r) for r in cur.fetchall()]


@app.post("/jobs")
async def create_job(job: JobCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        poster_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO jobs (title, company_name, description, requirements, job_type, location,
               salary_range, application_deadline, contact_email, apply_link, experience_level,
               skills_required, posted_by, poster_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active') RETURNING *""",
            (job.title, job.company_name, job.description, job.requirements, job.job_type,
             job.location, job.salary_range, job.application_deadline or None,
             job.contact_email, job.apply_link, job.experience_level,
             job.skills_required, user["user_id"], poster_name),
        )
        return dict(cur.fetchone())


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT posted_by FROM jobs WHERE id=%s", (job_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Job not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    return {"message": "Job deleted"}


@app.patch("/jobs/{job_id}/close")
async def close_job(job_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT posted_by FROM jobs WHERE id=%s", (job_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Job not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE jobs SET status='closed' WHERE id=%s", (job_id,))
    return {"message": "Job closed"}


# ─────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────
@app.get("/notes")
async def get_notes(branch: Optional[str] = None, semester: Optional[int] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        conditions, params = [], []
        if branch and branch != "all":
            conditions.append("n.branch = %s"); params.append(branch)
        if semester:
            conditions.append("n.semester = %s"); params.append(semester)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cur.execute(
            f"SELECT n.*, u.full_name AS uploader_display FROM notes n "
            f"LEFT JOIN users u ON n.uploaded_by=u.id{where} ORDER BY n.upvotes DESC, n.created_at DESC",
            params,
        )
        result = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("tags") is None: d["tags"] = []
            result.append(d)
        return result


@app.post("/notes")
async def create_note(note: NoteCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        uploader_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO notes (title, subject, description, file_type, semester, branch, tags,
               uploaded_by, uploader_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (note.title, note.subject, note.description, note.file_type, note.semester,
             note.branch, json.dumps(note.tags), user["user_id"], uploader_name),
        )
        row = dict(cur.fetchone())
        if row.get("tags") is None: row["tags"] = []
        return row


@app.post("/notes/{note_id}/file")
async def upload_note_file(note_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT uploaded_by FROM notes WHERE id=%s", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        if user.get("role") != "admin" and row["uploaded_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
        filename = f"note_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(file.file, f)
        cur.execute("UPDATE notes SET file_url=%s, file_type=%s WHERE id=%s RETURNING *", (f"/uploads/{filename}", ext, note_id))
        row = dict(cur.fetchone())
        if row.get("tags") is None: row["tags"] = []
        return row


@app.post("/notes/{note_id}/upvote")
async def upvote_note(note_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE notes SET upvotes = upvotes + 1 WHERE id=%s RETURNING *", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        return dict(row)


@app.post("/notes/{note_id}/view")
async def increment_note_views(note_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE notes SET views = views + 1, download_count = download_count + 1 WHERE id=%s", (note_id,))
    return {"ok": True}


@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT uploaded_by FROM notes WHERE id=%s", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM notes WHERE id=%s", (note_id,))
    return {"message": "Note deleted"}


# ─────────────────────────────────────────────
# FOOD
# ─────────────────────────────────────────────
def _assert_outlet_owner_or_admin(outlet_id: int, user: dict, cur) -> None:
    cur.execute("SELECT owner_id FROM food_outlets WHERE id=%s", (outlet_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Outlet not found")
    if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorised")


@app.get("/food")
async def get_food_outlets():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM food_outlets ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


@app.post("/food")
async def create_food_outlet(outlet: FoodOutletCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        owner_name = u["full_name"] if u else user.get("email", "")
        cur.execute(
            """INSERT INTO food_outlets (name, type, description, location, contact_info,
               operating_hours, delivery_available, owner_id, owner_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (outlet.name, outlet.type, outlet.description, outlet.location,
             outlet.contact_info, outlet.operating_hours, outlet.delivery_available,
             user["user_id"], owner_name),
        )
        return dict(cur.fetchone())


@app.post("/food/{outlet_id}/image")
async def upload_outlet_image(outlet_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        _assert_outlet_owner_or_admin(outlet_id, user, cur)
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"outlet_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        cur.execute("UPDATE food_outlets SET image_url=%s WHERE id=%s RETURNING *", (f"/uploads/{filename}", outlet_id))
        row = cur.fetchone()
        if not row:
            os.remove(filepath)
            raise HTTPException(status_code=404, detail="Outlet not found")
        return dict(row)


@app.delete("/food/{outlet_id}")
async def delete_food_outlet(outlet_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        _assert_outlet_owner_or_admin(outlet_id, user, cur)
        cur.execute("DELETE FROM food_outlets WHERE id=%s", (outlet_id,))
    return {"message": "Outlet deleted"}


@app.get("/food/{outlet_id}/menu")
async def get_menu(outlet_id: int):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM menus WHERE outlet_id=%s AND is_available=true ORDER BY category, item_name",
            (outlet_id,),
        )
        return [dict(r) for r in cur.fetchall()]


@app.post("/food/{outlet_id}/menu")
async def add_menu_item(outlet_id: int, item: MenuItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        _assert_outlet_owner_or_admin(outlet_id, user, cur)
        cur.execute(
            """INSERT INTO menus (outlet_id, item_name, description, price, category, is_vegetarian, is_available)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (outlet_id, item.item_name, item.description, item.price,
             item.category, item.is_vegetarian, item.is_available),
        )
        return dict(cur.fetchone())


@app.post("/food/{outlet_id}/menu/{item_id}/image")
async def upload_menu_item_image(outlet_id: int, item_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 5 MB")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        _assert_outlet_owner_or_admin(outlet_id, user, cur)
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"menu_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        cur.execute(
            "UPDATE menus SET image_url=%s WHERE id=%s AND outlet_id=%s RETURNING *",
            (f"/uploads/{filename}", item_id, outlet_id),
        )
        row = cur.fetchone()
        if not row:
            os.remove(filepath)
            raise HTTPException(status_code=404, detail="Menu item not found")
        return dict(row)


@app.delete("/food/{outlet_id}/menu/{item_id}")
async def delete_menu_item(outlet_id: int, item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        _assert_outlet_owner_or_admin(outlet_id, user, cur)
        cur.execute("DELETE FROM menus WHERE id=%s AND outlet_id=%s", (item_id, outlet_id))
    return {"message": "Menu item deleted"}


# ─────────────────────────────────────────────
# Serve built React frontend (production)
# ─────────────────────────────────────────────
if _frontend_ready:
    from starlette.staticfiles import StaticFiles as StarletteStatic

    app.mount("/static", StarletteStatic(directory=os.path.join(FRONTEND_BUILD, "static")), name="frontend-static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_BUILD, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", os.getenv("API_GATEWAY_PORT", 8000)))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
