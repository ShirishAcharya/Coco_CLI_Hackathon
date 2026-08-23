-- Step 1: bare-minimum test that SNOWFLAKE.CORTEX.AGENT_RUN is callable
-- on your account/role before we build anything on top of it.
-- No tools, no semantic model yet -- just confirms the function works.

USE ROLE ACCOUNTADMIN;
USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

SELECT TRY_PARSE_JSON(
  SNOWFLAKE.CORTEX.AGENT_RUN(
    $${
      "messages": [
        { "role": "user", "content": [ { "type": "text", "text": "Say hello and confirm you are running." } ] }
      ],
      "models": { "orchestration": "claude-sonnet-4-6" }
    }$$,
    TRUE
  )
) AS resp;