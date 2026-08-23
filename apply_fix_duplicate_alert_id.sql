-- Renumber the weekend-pattern row (created_at ...434000, the second of the
-- two 304 rows) to the next free id, 318. The weekday row keeps 304.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

UPDATE agent_alerts
SET alert_id = 318
WHERE alert_id = 304
  AND created_at = '2026-08-05 03:08:10.434000';

-- Confirm no duplicates remain
SELECT alert_id, COUNT(*) AS n
FROM agent_alerts
GROUP BY alert_id
HAVING COUNT(*) > 1;