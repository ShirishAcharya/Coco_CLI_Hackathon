-- Run these against your CocoHackathon account (role: ACCOUNTADMIN) to allow
-- the Nightshift Agent Streamlit app to make outbound calls to webhook.site
-- for the action-button notifications (item 2).

USE ROLE ACCOUNTADMIN;

-- 1. Network rule: allow egress to webhook.site
CREATE OR REPLACE NETWORK RULE webhook_site_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('webhook.site')
  COMMENT = 'Allow outbound calls to webhook.site for Nightshift Agent action buttons';

-- 2. External access integration wrapping the network rule
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION webhook_site_eai
  ALLOWED_NETWORK_RULES = (webhook_site_rule)
  ENABLED = TRUE
  COMMENT = 'EAI for Nightshift Agent webhook notifications';

-- 3. Grant usage on the integration to the role that runs the app
GRANT USAGE ON INTEGRATION webhook_site_eai TO ROLE ACCOUNTADMIN;

-- 4. Attach the EAI to the deployed Streamlit app
--    Replace the object name below if yours differs from the handoff doc.
ALTER STREAMLIT RESTAURANT_OPS.CORE.ZKSPDD__B0LR1V3T
  SET EXTERNAL_ACCESS_INTEGRATIONS = (webhook_site_eai);

-- 5. Verify the EAI is attached
DESCRIBE STREAMLIT RESTAURANT_OPS.CORE.ZKSPDD__B0LR1V3T;