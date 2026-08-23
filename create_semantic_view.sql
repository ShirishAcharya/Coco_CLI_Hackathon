-- Step 2a: create a Semantic View object over kitchen_tickets + restaurants,
-- so we can reference it (not an inline YAML) in the AGENT_RUN tool_resources.
-- Verify column names against your real schema.sql before running.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

CREATE OR REPLACE SEMANTIC VIEW kitchen_ops_sv
  TABLES (
    kitchen_tickets AS kitchen_tickets
      PRIMARY KEY (ticket_id)
      WITH SYNONYMS ('tickets', 'kitchen orders')
      COMMENT = 'Kitchen ticket-level prep time records',
    restaurants AS restaurants
      PRIMARY KEY (restaurant_id)
      WITH SYNONYMS ('branches', 'locations')
      COMMENT = 'Restaurant branch info'
  )
  RELATIONSHIPS (
    kitchen_tickets_to_restaurants AS
      kitchen_tickets (restaurant_id) REFERENCES restaurants (restaurant_id)
  )
  FACTS (
    kitchen_tickets.actual_prep_time_min AS actual_prep_time_min
      COMMENT = 'Actual time in minutes to prepare the ticket',
    kitchen_tickets.expected_prep_time_min AS expected_prep_time_min
      COMMENT = 'Expected/target prep time in minutes'
  )
  DIMENSIONS (
    kitchen_tickets.station AS station
      WITH SYNONYMS ('kitchen station')
      COMMENT = 'Kitchen station name, e.g. grill',
    kitchen_tickets.created_at AS created_at
      COMMENT = 'Timestamp the ticket was created',
    restaurants.name AS name
      WITH SYNONYMS ('restaurant name', 'branch name')
      COMMENT = 'Restaurant display name'
  )
  METRICS (
    kitchen_tickets.avg_prep_ratio AS AVG(actual_prep_time_min / NULLIF(expected_prep_time_min, 0))
      COMMENT = 'Average ratio of actual to expected prep time'
  )
  COMMENT = 'Semantic view for kitchen anomaly analysis (Nightshift Agent)';

-- Sanity check it was created
SHOW SEMANTIC VIEWS LIKE 'kitchen_ops_sv' IN SCHEMA RESTAURANT_OPS.CORE;