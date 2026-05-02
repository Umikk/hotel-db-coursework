CREATE TABLE hotels (
    hotel_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stars INT,
    address VARCHAR(200)
);

CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    position_name VARCHAR(100) NOT NULL
);

CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    hotel_id INT,
    person_inn VARCHAR(20) UNIQUE,
    full_name VARCHAR(100),
    position_id INT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    hotel_id INT,
    room_description VARCHAR(200),
    capacity INT,
    price_per_day NUMERIC(10,2),
    status VARCHAR(20),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE TABLE guests (
    guest_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    passport VARCHAR(50),
    phone VARCHAR(20),
    hotel_id INT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    room_id INT,
    guest_id INT,
    arrival_date DATE,
    departure_date DATE,
    advance_payment NUMERIC(10,2),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (guest_id) REFERENCES guests(guest_id)
);


--Ограничения (ALTER TABLE)--
ALTER TABLE rooms
ALTER COLUMN status SET DEFAULT 'free';

ALTER TABLE rooms
ADD CONSTRAINT capacity_check
CHECK (capacity > 0);

ALTER TABLE rooms
ADD CONSTRAINT price_check
CHECK (price_per_day > 0);

ALTER TABLE bookings
ADD CONSTRAINT date_check
CHECK (departure_date > arrival_date);

ALTER TABLE bookings
ADD CONSTRAINT advance_payment_check
CHECK (advance_payment >= 0);

ALTER TABLE staff
ADD CONSTRAINT unique_staff_inn UNIQUE(person_inn);


--Индексы--
CREATE INDEX idx_bookings_guest
ON bookings(guest_id);

CREATE INDEX idx_bookings_room
ON bookings(room_id);

CREATE INDEX idx_rooms_hotel
ON rooms(hotel_id);


--Представления (VIEW)--
CREATE VIEW free_rooms AS
SELECT room_id, room_description, capacity, price_per_day
FROM rooms
WHERE status = 'free';

CREATE VIEW booking_info AS
SELECT
b.booking_id,
g.full_name,
r.room_id,
b.arrival_date,
b.departure_date
FROM bookings b
JOIN guests g ON b.guest_id = g.guest_id
JOIN rooms r ON b.room_id = r.room_id;

CREATE VIEW room_booking_stats AS
SELECT
room_id,
COUNT(*) AS total_bookings
FROM bookings
GROUP BY room_id
HAVING COUNT(*) > 0;


--Функция триггера--
CREATE OR REPLACE FUNCTION update_room_status()
RETURNS TRIGGER AS $$
BEGIN
UPDATE rooms
SET status = 'occupied'
WHERE room_id = NEW.room_id;

RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--Триггер--
CREATE TRIGGER booking_trigger
AFTER INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION update_room_status();
