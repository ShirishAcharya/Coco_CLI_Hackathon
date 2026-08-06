-- ==========================================================
-- Restaurant Ops Multi-Agent Schema (CoCo CLI Hackathon)
-- ==========================================================

CREATE DATABASE IF NOT EXISTS RESTAURANT_OPS;
USE DATABASE RESTAURANT_OPS;
CREATE SCHEMA IF NOT EXISTS CORE;
USE SCHEMA CORE;

-- ==========================================================
-- Core reference table
-- ==========================================================

CREATE OR REPLACE TABLE restaurants (
    restaurant_id   INT PRIMARY KEY,
    name            VARCHAR,
    brand_group     VARCHAR,
    location        VARCHAR
);

-- ==========================================================
-- Menu
-- ==========================================================

CREATE OR REPLACE TABLE menu_items (
    menu_item_id        INT PRIMARY KEY,
    restaurant_id       INT REFERENCES restaurants(restaurant_id),
    name                VARCHAR,
    category            VARCHAR,       -- main, appetizer, beverage, dessert
    station              VARCHAR,       -- grill, curry, tandoor, cold, dessert
    base_prep_time_min  FLOAT,
    price               FLOAT,
    active_since        DATE
);

-- ==========================================================
-- Staff shifts (shared by kitchen + serving agents)
-- ==========================================================

CREATE OR REPLACE TABLE staff_shifts (
    shift_id        INT PRIMARY KEY,
    restaurant_id   INT REFERENCES restaurants(restaurant_id),
    staff_name      VARCHAR,
    role            VARCHAR,       -- cook, server, manager
    station          VARCHAR,       -- nullable, only relevant for cooks
    shift_start     TIMESTAMP_NTZ,
    shift_end       TIMESTAMP_NTZ
);

-- ==========================================================
-- Kitchen agent tables
-- ==========================================================

CREATE OR REPLACE TABLE kitchen_tickets (
    ticket_id               INT PRIMARY KEY,
    restaurant_id           INT REFERENCES restaurants(restaurant_id),
    order_id                INT,        -- FK to orders, added below after orders table exists
    menu_item_id            INT REFERENCES menu_items(menu_item_id),
    station                  VARCHAR,
    special_instruction     BOOLEAN,
    created_at              TIMESTAMP_NTZ,
    started_at              TIMESTAMP_NTZ,
    completed_at             TIMESTAMP_NTZ,
    expected_prep_time_min  FLOAT,
    actual_prep_time_min    FLOAT,
    shift_id                INT REFERENCES staff_shifts(shift_id)
);

-- ==========================================================
-- Serving agent tables
-- ==========================================================

CREATE OR REPLACE TABLE tables (
    table_id        INT PRIMARY KEY,
    restaurant_id   INT REFERENCES restaurants(restaurant_id),
    capacity        INT
);

CREATE OR REPLACE TABLE orders (
    order_id                INT PRIMARY KEY,
    restaurant_id           INT REFERENCES restaurants(restaurant_id),
    table_id                INT REFERENCES tables(table_id),
    server_id                INT REFERENCES staff_shifts(shift_id),
    seated_at                TIMESTAMP_NTZ,
    order_placed_at         TIMESTAMP_NTZ,
    payment_completed_at    TIMESTAMP_NTZ,
    party_size              INT
);

-- Add the FK from kitchen_tickets to orders now that orders exists
ALTER TABLE kitchen_tickets ADD CONSTRAINT fk_kitchen_order
    FOREIGN KEY (order_id) REFERENCES orders(order_id);

-- ==========================================================
-- Stock agent tables
-- ==========================================================

CREATE OR REPLACE TABLE inventory_items (
    inventory_item_id   INT PRIMARY KEY,
    restaurant_id       INT REFERENCES restaurants(restaurant_id),
    name                VARCHAR,
    unit                VARCHAR,
    current_stock       FLOAT,
    reorder_threshold   FLOAT
);

CREATE OR REPLACE TABLE inventory_usage_log (
    log_id               INT PRIMARY KEY,
    inventory_item_id    INT REFERENCES inventory_items(inventory_item_id),
    date                 DATE,
    quantity_used        FLOAT
);

CREATE OR REPLACE TABLE supplier_orders (
    supplier_order_id       INT PRIMARY KEY,
    inventory_item_id       INT REFERENCES inventory_items(inventory_item_id),
    ordered_at               DATE,
    expected_delivery_date  DATE,
    actual_delivery_date    DATE   -- nullable until delivered
);

-- ==========================================================
-- Shared agent output table
-- ==========================================================

CREATE OR REPLACE TABLE agent_alerts (
    alert_id             INT PRIMARY KEY,
    restaurant_id        INT REFERENCES restaurants(restaurant_id),
    agent_type           VARCHAR,     -- kitchen / serving / stock
    severity             VARCHAR,     -- info / warning / critical
    pattern_detected     VARCHAR,
    suggested_action     VARCHAR,
    supporting_data      VARIANT,
    created_at           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
