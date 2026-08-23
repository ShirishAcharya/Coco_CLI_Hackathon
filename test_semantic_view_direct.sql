-- Step 2c: bypass AGENT_RUN entirely, query the semantic view directly
-- with SQL to confirm the view itself works before blaming the agent layer.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

SELECT *
FROM SEMANTIC_VIEW(
  kitchen_ops_sv
  DIMENSIONS station, name
  METRICS avg_prep_ratio
);