-- Find any duplicate alert_id values in agent_alerts (root cause of the
-- StreamlitDuplicateElementKey crash). alert_id is a plain PK, not an
-- IDENTITY column, so concurrent inserts can collide.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

SELECT alert_id, COUNT(*) AS n
FROM agent_alerts
GROUP BY alert_id
HAVING COUNT(*) > 1
ORDER BY alert_id;