-- Campus Connect Sample Data
-- This script populates the database with sample data for testing and demonstration

USE auth_db;

-- Sample users
INSERT INTO users (email, phone, password_hash, full_name, role, is_active) VALUES
('admin@campus.com', '+1234567890', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uSk8pyyUrBq', 'Campus Admin', 'admin', true),
('john.doe@campus.edu', '+1234567891', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uSk8pyyUrBq', 'John Doe', 'student', true),
('jane.smith@campus.edu', '+1234567892', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uSk8pyyUrBq', 'Jane Smith', 'student', true),
('bob.wilson@campus.edu', '+1234567893', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uSk8pyyUrBq', 'Bob Wilson', 'student', true),
('alice.brown@campus.edu', '+1234567894', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uSk8pyyUrBq', 'Alice Brown', 'student', true);

-- Sample user profiles
INSERT INTO user_profiles (user_id, branch, year_of_study, hostel_name, room_number, bio, interests) VALUES
(2, 'Computer Science', 3, 'Block A', '301', 'Passionate about coding and AI', '["coding", "AI", "robotics"]'),
(3, 'Electrical Engineering', 2, 'Block B', '205', 'Love electronics and IoT projects', '["electronics", "IoT", "embedded systems"]'),
(4, 'Mechanical Engineering', 4, 'Block C', '401', 'Car enthusiast and design lover', '["automotive", "design", "3D printing"]'),
(5, 'Business Administration', 1, 'Block D', '102', 'Entrepreneur at heart', '["business", "marketing", "finance"]');

USE meetups_db;

-- Sample meetups
INSERT INTO meetups (title, description, host_name, social_handle, location, latitude, longitude, event_date, max_participants, created_by) VALUES
('Campus Hackathon 2024', 'Join us for an exciting 24-hour coding competition! Prizes worth $5000 to be won.', 'CS Club', '@csclub', 'Main Auditorium', 40.7128, -74.0060, '2024-12-15 09:00:00', 100, 2),
('Career Fair 2024', 'Meet top companies and explore internship opportunities', 'Placement Cell', '@placement', 'Sports Complex', 40.7589, -73.9851, '2024-11-20 10:00:00', 200, 3),
('Music Festival', 'Campus music festival featuring local bands and artists', 'Music Club', '@musicclub', 'Open Ground', 40.7505, -73.9934, '2024-11-25 18:00:00', 150, 4),
('Study Group: Machine Learning', 'Weekly study group for ML enthusiasts', 'John Doe', '@johndoe', 'Library Room 201', 40.7282, -73.7949, '2024-11-18 14:00:00', 20, 2),
('Photography Workshop', 'Learn professional photography techniques', 'Photo Club', '@photoclub', 'Art Studio', 40.7614, -73.9776, '2024-11-22 15:00:00', 25, 5);

-- Sample RSVPs
INSERT INTO meetup_participants (meetup_id, user_id, rsvp_status) VALUES
(1, 2, 'yes'), (1, 3, 'yes'), (1, 4, 'maybe'),
(2, 3, 'yes'), (2, 4, 'yes'), (2, 5, 'yes'),
(3, 2, 'yes'), (3, 5, 'yes'),
(4, 3, 'yes'), (4, 5, 'maybe'),
(5, 2, 'yes'), (5, 4, 'yes');

USE marketplace_db;

-- Sample marketplace items
INSERT INTO items (title, description, price, category, condition_status, seller_id, contact_info) VALUES
('MacBook Pro 2023', 'Latest MacBook Pro with M3 chip, barely used', 1999.99, 'electronics', 'new', 2, 'john.doe@campus.edu'),
('Calculus Textbook', 'Brand new Calculus textbook, never opened', 89.99, 'books', 'new', 3, 'jane.smith@campus.edu'),
('Wireless Headphones', 'Sony WH-1000XM4, excellent condition', 249.99, 'electronics', 'used', 4, 'bob.wilson@campus.edu'),
('Engineering Drawing Set', 'Complete set with compass, scales, and templates', 45.99, 'stationery', 'used', 5, 'alice.brown@campus.edu'),
('DSLR Camera', 'Canon EOS Rebel T7i with kit lens', 599.99, 'electronics', 'used', 2, 'john.doe@campus.edu'),
('Laptop Stand', 'Adjustable aluminum laptop stand', 29.99, 'electronics', 'new', 3, 'jane.smith@campus.edu');

USE stolen_found_db;

-- Sample lost/found reports
INSERT INTO reports (item_name, description, category, report_type, location, latitude, longitude, reported_by, contact_info) VALUES
('iPhone 13 Pro', 'Black iPhone 13 Pro lost in library yesterday', 'electronics', 'lost', 'Main Library', 40.7128, -74.0060, 2, 'john.doe@campus.edu'),
('Blue Backpack', 'Nike backpack with laptop inside, found near cafeteria', 'accessories', 'found', 'Cafeteria', 40.7589, -73.9851, 3, 'jane.smith@campus.edu'),
('Student ID Card', 'Lost university ID card, name: John Doe', 'documents', 'lost', 'Sports Complex', 40.7505, -73.9934, 4, 'bob.wilson@campus.edu'),
('Wireless Earbuds', 'Found AirPods in classroom 101', 'electronics', 'found', 'Classroom 101', 40.7282, -73.7949, 5, 'alice.brown@campus.edu');

USE rooms_db;

-- Sample room listings
INSERT INTO rooms (title, description, location, rent_amount, deposit_amount, room_type, gender_preference, amenities, owner_id, contact_info) VALUES
('Spacious Single Room', 'Beautiful single room with attached bathroom and study area', 'Block A, Room 301', 800.00, 1600.00, 'single', 'any', '["wifi", "laundry", "parking"]', 2, 'john.doe@campus.edu'),
('Shared Apartment', '2BHK apartment perfect for 3 students', 'Near Campus Gate', 450.00, 900.00, 'shared', 'any', '["wifi", "kitchen", "parking", "gym"]', 3, 'jane.smith@campus.edu'),
('Studio Apartment', 'Modern studio with great view', 'Downtown Campus', 650.00, 1300.00, 'apartment', 'female', '["wifi", "laundry", "parking", "ac"]', 4, 'bob.wilson@campus.edu'),
('Double Room', 'Comfortable room for two roommates', 'Block B, Room 205', 375.00, 750.00, 'shared', 'male', '["wifi", "laundry"]', 5, 'alice.brown@campus.edu');

USE rental_db;

-- Sample rental items
INSERT INTO rental_items (name, description, category, daily_rate, security_deposit, owner_id, location) VALUES
('DSLR Camera', 'Canon EOS R5 professional camera', 'camera', 25.00, 100.00, 2, 'Photography Lab'),
('Laptop', 'MacBook Air M2, perfect for presentations', 'laptop', 15.00, 50.00, 3, 'Computer Lab'),
('Projector', 'HD projector for presentations', 'electronics', 20.00, 75.00, 4, 'Auditorium'),
('Drone', 'DJI Mini 3 Pro drone for aerial photography', 'electronics', 30.00, 150.00, 5, 'Engineering Block'),
('Graphics Tablet', 'Wacom Intuos drawing tablet', 'electronics', 8.00, 25.00, 2, 'Art Studio');

USE clubs_db;

-- Sample clubs
INSERT INTO clubs (name, description, category, president_id, social_links) VALUES
('Computer Science Club', 'Programming, hackathons, and tech events', 'coding', 2, '{"website": "csclub.campus.edu", "instagram": "@csclub"}'),
('Music Club', 'Bringing melody and rhythm to campus life', 'music', 4, '{"website": "music.campus.edu", "instagram": "@musicclub"}'),
('Photography Club', 'Capturing moments and learning photography', 'photography', 5, '{"website": "photo.campus.edu", "instagram": "@photoclub"}'),
('Robotics Club', 'Building robots and competing in competitions', 'robotics', 3, '{"website": "robotics.campus.edu", "instagram": "@roboticsclub"}');

-- Sample club members
INSERT INTO club_members (club_id, user_id, role) VALUES
(1, 2, 'president'), (1, 3, 'member'), (1, 4, 'member'),
(2, 4, 'president'), (2, 5, 'member'), (2, 2, 'member'),
(3, 5, 'president'), (3, 2, 'member'), (3, 3, 'member'),
(4, 3, 'president'), (4, 4, 'member'), (4, 5, 'member');

USE jobs_db;

-- Sample job postings
INSERT INTO jobs (title, company_name, description, requirements, job_type, location, salary_range, posted_by) VALUES
('Software Engineer Intern', 'TechCorp', 'Summer internship for computer science students', 'JavaScript, React, Node.js', 'internship', 'Remote', '$25-35/hour', 2),
('Marketing Assistant', 'Campus Events', 'Part-time marketing role for campus events', 'Social media experience, creative thinking', 'part_time', 'On-campus', '$15/hour', 3),
('Research Assistant', 'Engineering Dept', 'Help with mechanical engineering research', 'CAD experience preferred', 'part_time', 'Engineering Building', '$18/hour', 4),
('Content Writer', 'Student Newspaper', 'Write articles for campus newspaper', 'Writing skills, journalism experience', 'part_time', 'Media Center', '$12/hour', 5),
('Lab Assistant', 'Chemistry Lab', 'Assist in chemistry lab experiments', 'Basic chemistry knowledge', 'part_time', 'Science Building', '$16/hour', 2);

USE notes_db;

-- Sample notes
INSERT INTO notes (title, subject, description, uploaded_by, tags) VALUES
('Data Structures Notes', 'Computer Science', 'Complete notes on data structures and algorithms', 2, '["data structures", "algorithms", "CS"]'),
('Calculus Formulas', 'Mathematics', 'Important calculus formulas and theorems', 3, '["calculus", "math", "formulas"]'),
('Circuit Analysis Guide', 'Electrical Engineering', 'Comprehensive guide to circuit analysis', 4, '["circuits", "electrical", "engineering"]'),
('Thermodynamics Notes', 'Mechanical Engineering', 'Thermodynamics principles and applications', 5, '["thermodynamics", "mechanical", "physics"]'),
('Business Strategy Notes', 'Business', 'Strategic management and business planning', 2, '["business", "strategy", "management"]');

-- Sample printing services
INSERT INTO printing_services (service_name, description, contact_info, pricing, location) VALUES
('Campus Print Center', 'High-quality printing services for students', 'print@campus.edu', '{"bw_a4": 0.10, "color_a4": 0.50, "binding": 2.00}', 'Library Basement'),
('Engineering Lab Printers', 'Specialized printing for engineering drawings', 'englab@campus.edu', '{"bw_a3": 0.20, "color_a3": 1.00, "large_format": 5.00}', 'Engineering Block');

USE food_db;

-- Sample food outlets
INSERT INTO food_outlets (name, type, description, location, contact_info, delivery_available) VALUES
('Campus Cafe', 'cafe', 'Coffee, sandwiches, and snacks', 'Library Ground Floor', 'cafe@campus.edu', true),
('Main Mess', 'mess', 'Traditional meals and vegetarian options', 'Hostel Block A', 'mess@campus.edu', false),
('Food Court', 'food_court', 'Multiple cuisines and fast food', 'Central Campus', 'foodcourt@campus.edu', true),
('Pizza Corner', 'delivery', 'Fresh pizzas and Italian cuisine', 'Near Dormitories', 'pizza@campus.edu', true);

-- Sample menu items
INSERT INTO menus (outlet_id, item_name, description, price, category, is_vegetarian) VALUES
(1, 'Cappuccino', 'Rich espresso with steamed milk', 3.50, 'beverages', true),
(1, 'Club Sandwich', 'Triple decker sandwich with fries', 8.99, 'sandwiches', false),
(1, 'Caesar Salad', 'Fresh greens with caesar dressing', 6.99, 'salads', true),
(2, 'Chicken Biryani', 'Aromatic rice dish with chicken', 7.99, 'main_course', false),
(2, 'Paneer Butter Masala', 'Creamy curry with cottage cheese', 6.99, 'main_course', true),
(2, 'Vegetable Pulao', 'Fragrant rice with mixed vegetables', 5.99, 'main_course', true),
(3, 'Margherita Pizza', 'Classic cheese pizza', 9.99, 'pizza', true),
(3, 'Chicken Burger', 'Grilled chicken burger with fries', 7.99, 'burgers', false),
(4, 'Pepperoni Pizza', 'Spicy pepperoni pizza', 12.99, 'pizza', false),
(4, 'Garlic Bread', 'Fresh garlic bread with herbs', 4.99, 'appetizers', true);

-- Sample reviews
INSERT INTO reviews (outlet_id, user_id, rating, comment) VALUES
(1, 2, 5, 'Great coffee and friendly staff!'),
(1, 3, 4, 'Good sandwiches, but a bit pricey'),
(2, 4, 5, 'Authentic flavors, highly recommended'),
(2, 5, 4, 'Good food, but portions could be larger'),
(3, 2, 5, 'Amazing variety and quick service'),
(4, 3, 4, 'Delicious pizzas, fast delivery');

-- Create some sample indexes for better performance
USE auth_db;
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

USE meetups_db;
CREATE INDEX idx_meetups_date ON meetups(event_date);
CREATE INDEX idx_meetups_location ON meetups(location);

USE marketplace_db;
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_price ON items(price);

USE rooms_db;
CREATE INDEX idx_rooms_rent ON rooms(rent_amount);
CREATE INDEX idx_rooms_location ON rooms(location);
CREATE INDEX idx_rooms_type ON rooms(room_type);

USE jobs_db;
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_location ON jobs(location);

USE food_db;
CREATE INDEX idx_menus_price ON menus(price);
CREATE INDEX idx_reviews_rating ON reviews(rating);