-- Step 2: AGENT_RUN with an inline Cortex Analyst semantic model, scoped to
-- just kitchen_tickets + restaurants, so the agent can actually query data
-- instead of just chatting. Verify column names below against your real
-- schema.sql before running -- these are inferred from the Streamlit app's
-- existing SQL queries.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

SELECT TRY_PARSE_JSON(
  SNOWFLAKE.CORTEX.AGENT_RUN(
    $${
      "messages": [
        {
          "role": "user",
          "content": [
            { "type": "text", "text": "Check grill station kitchen performance for the restaurant named Momo Junction - Thamel. Compare average prep time ratio (actual_prep_time_min divided by expected_prep_time_min) for the first 20 days of data versus the most recent 20 days, for tickets created between 6pm and 9pm. Report the percent change and whether it looks like a real slowdown." }
          ]
        }
      ],
      "models": { "orchestration": "claude-sonnet-4-6" },
      "tools": [
        {
          "tool_spec": {
            "type": "cortex_analyst_text_to_sql",
            "name": "kitchen_analyst"
          }
        }
      ],
      "tool_resources": {
        "kitchen_analyst": {
          "semantic_model": "name: kitchen_ops\ntables:\n  - name: kitchen_tickets\n    base_table:\n      database: RESTAURANT_OPS\n      schema: CORE\n      table: KITCHEN_TICKETS\n    dimensions:\n      - name: station\n        expr: station\n        data_type: varchar\n      - name: restaurant_id\n        expr: restaurant_id\n        data_type: number\n    time_dimensions:\n      - name: created_at\n        expr: created_at\n        data_type: timestamp\n    facts:\n      - name: actual_prep_time_min\n        expr: actual_prep_time_min\n        data_type: number\n      - name: expected_prep_time_min\n        expr: expected_prep_time_min\n        data_type: number\n  - name: restaurants\n    base_table:\n      database: RESTAURANT_OPS\n      schema: CORE\n      table: RESTAURANTS\n    dimensions:\n      - name: restaurant_id\n        expr: restaurant_id\n        data_type: number\n      - name: name\n        expr: name\n        data_type: varchar\n"
        }
      }
    }$$,
    TRUE
  )
) AS resp;