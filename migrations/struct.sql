-- Удаление всех таблиц (в порядке зависимости)
DROP TABLE IF EXISTS Rent_Service CASCADE;
DROP TABLE IF EXISTS Rent_Equipment CASCADE;
DROP TABLE IF EXISTS Vote_Common CASCADE;
DROP TABLE IF EXISTS Vote_VIP CASCADE;
DROP TABLE IF EXISTS Ticket CASCADE;
DROP TABLE IF EXISTS Customer CASCADE;
DROP TABLE IF EXISTS Part CASCADE;
DROP TABLE IF EXISTS Act CASCADE;
DROP TABLE IF EXISTS Show CASCADE;
DROP TABLE IF EXISTS Scenario CASCADE;
DROP TABLE IF EXISTS Hall CASCADE;
DROP TABLE IF EXISTS Theater CASCADE;
DROP TABLE IF EXISTS Franchise CASCADE;
DROP TABLE IF EXISTS Equipment CASCADE;
DROP TABLE IF EXISTS Service CASCADE;
DROP TABLE IF EXISTS RolePermission CASCADE;
DROP TABLE IF EXISTS Employee CASCADE;

-- ======= Пересоздание таблиц =======

CREATE TABLE Franchise (
    contract_id SERIAL PRIMARY KEY,
    contact_person VARCHAR(100),
    organization VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    royalty_percentage NUMERIC(5, 2),
    initial_fee NUMERIC(10, 2),
    monthly_fee NUMERIC(10, 2)
);

CREATE TABLE Theater (
    theater_id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES Franchise(contract_id),
    name VARCHAR(100),
    location TEXT
);

CREATE TABLE Hall (
    hall_id SERIAL PRIMARY KEY,
    theater_id INT REFERENCES Theater(theater_id),
    capacity INT
);

CREATE TABLE Scenario (
    scenario_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    tz_source_filename VARCHAR(500),
    tz_source_relpath TEXT,
    tz_result_filename VARCHAR(500),
    tz_result_relpath TEXT,
    tz_pipeline_status VARCHAR(50)
);

CREATE TABLE Act (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES Scenario(scenario_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE Part (
    id SERIAL PRIMARY KEY,
    act_id INTEGER REFERENCES Act(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE Show (
    show_id SERIAL PRIMARY KEY,
    hall_id INT REFERENCES Hall(hall_id),
    scenario_id INT REFERENCES Scenario(scenario_id) ON DELETE SET NULL,
    title VARCHAR(100),
    vote_type VARCHAR(100) CHECK (vote_type IN ('common', 'vip', 'both')),
    duration INTERVAL,
    show_date TIMESTAMP
);

CREATE TABLE Customer (
    email VARCHAR(100) PRIMARY KEY,
    phone VARCHAR(20)
);

CREATE TABLE Ticket (
    ticket_id SERIAL PRIMARY KEY,
    owner_id BIGINT,
    show_id INT REFERENCES Show(show_id) ON DELETE CASCADE,
    seat_number VARCHAR(20),
    price NUMERIC(10, 2),
    status VARCHAR(50) CHECK (status IN ('available', 'booked', 'sold', 'registered')),
    vip_status BOOLEAN DEFAULT FALSE,
    email VARCHAR(100) REFERENCES Customer(email) ON DELETE SET NULL
);

CREATE TABLE Vote_Common (
    ticket_id INT REFERENCES Ticket(ticket_id),
    vote_id SERIAL,
    value VARCHAR(50),
    PRIMARY KEY (ticket_id, vote_id)
);

CREATE TABLE Vote_VIP (
    vote_id SERIAL PRIMARY KEY,
    ticket_id INT REFERENCES Ticket(ticket_id) ON DELETE CASCADE,
    show_id INT REFERENCES Show(show_id) ON DELETE CASCADE,
    act_id INT REFERENCES Act(id) ON DELETE CASCADE,
    value VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE Equipment (
    equipment_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(10, 2),
    amount INT
);

CREATE TABLE Rent_Equipment (
    equipment_id INT REFERENCES Equipment(equipment_id),
    show_id INT REFERENCES Show(show_id),
    rent_start TIMESTAMP,
    rent_end TIMESTAMP,
    PRIMARY KEY (equipment_id, show_id)
);

CREATE TABLE Service (
    service_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(10, 2),
    amount INT
);

CREATE TABLE Rent_Service (
    service_id INT REFERENCES Service(service_id),
    show_id INT REFERENCES Show(show_id),
    rent_start TIMESTAMP,
    rent_end TIMESTAMP,
    PRIMARY KEY (service_id, show_id)
);

CREATE TABLE Employee (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    last_online TIMESTAMP,
    role VARCHAR(20)
);

CREATE TABLE RolePermission (
    id SERIAL PRIMARY KEY,
    role_slug VARCHAR(64) NOT NULL,
    permission_key VARCHAR(64) NOT NULL,
    allowed BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_role_permission_key UNIQUE (role_slug, permission_key)
);

CREATE INDEX idx_role_permission_slug ON RolePermission(role_slug);

-- Добавление индексов для улучшения производительности
CREATE INDEX idx_show_hall_id ON Show(hall_id);
CREATE INDEX idx_show_scenario_id ON Show(scenario_id);
CREATE INDEX idx_ticket_show_id ON Ticket(show_id);
CREATE INDEX idx_act_scenario_id ON Act(scenario_id);
CREATE INDEX idx_part_act_id ON Part(act_id);
CREATE INDEX idx_vote_common_ticket_id ON Vote_Common(ticket_id);
CREATE INDEX idx_vote_vip_ticket_id ON Vote_VIP(ticket_id);
CREATE INDEX idx_rent_equipment_show_id ON Rent_Equipment(show_id);
CREATE INDEX idx_rent_service_show_id ON Rent_Service(show_id);
