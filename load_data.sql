-- ==========================================================
-- Load synthetic data into RESTAURANT_OPS via internal stage
-- ==========================================================

USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

-- Internal stage to hold uploaded CSVs
CREATE OR REPLACE STAGE data_stage
    FILE_FORMAT = (
        TYPE = 'CSV'
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        NULL_IF = ('', 'NULL')
        EMPTY_FIELD_AS_NULL = TRUE
    );

PUT file://output_csv/restaurants.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/menu_items.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/staff_shifts.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/tables.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/orders.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/kitchen_tickets.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/inventory_items.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/inventory_usage_log.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
PUT file://output_csv/supplier_orders.csv @data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE;


COPY INTO restaurants
FROM @data_stage/restaurants.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO menu_items
FROM @data_stage/menu_items.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO staff_shifts
FROM @data_stage/staff_shifts.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO tables
FROM @data_stage/tables.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO orders
FROM @data_stage/orders.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO kitchen_tickets
FROM @data_stage/kitchen_tickets.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO inventory_items
FROM @data_stage/inventory_items.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO inventory_usage_log
FROM @data_stage/inventory_usage_log.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO supplier_orders
FROM @data_stage/supplier_orders.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

-- ==========================================================
-- Sanity check row counts
-- ==========================================================

SELECT 'restaurants' AS table_name, COUNT(*) AS row_count FROM restaurants
UNION ALL SELECT 'menu_items', COUNT(*) FROM menu_items
UNION ALL SELECT 'staff_shifts', COUNT(*) FROM staff_shifts
UNION ALL SELECT 'tables', COUNT(*) FROM tables
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'kitchen_tickets', COUNT(*) FROM kitchen_tickets
UNION ALL SELECT 'inventory_items', COUNT(*) FROM inventory_items
UNION ALL SELECT 'inventory_usage_log', COUNT(*) FROM inventory_usage_log
UNION ALL SELECT 'supplier_orders', COUNT(*) FROM supplier_orders;