-- Step 2b: AGENT_RUN referencing the semantic view created in
-- create_semantic_view.sql, instead of an inline semantic model string.

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
            { "type": "text", "text": "Check grill station kitchen performance for the restaurant named Momo Junction - Thamel. Compare average prep time ratio for the first 20 days of data versus the most recent 20 days, for tickets created between 6pm and 9pm. Report the percent change and whether it looks like a real slowdown." }
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
          "semantic_view": "RESTAURANT_OPS.CORE.KITCHEN_OPS_SV"
        }
      }
    }$$,
    TRUE
  )
) AS resp;