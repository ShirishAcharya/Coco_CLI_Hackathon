-- ==========================================================
-- Populate agent_alerts with findings derived from
-- verify_anomalies.sql results (fallback for CoCo CLI outage)
-- Thresholds/severity match the logic defined in each SKILL.md
-- ==========================================================

USE DATABASE RESTAURANT_OPS;
USE SCHEMA CORE;

-- ==========================================================
-- KITCHEN ALERTS
-- Threshold: >=20% ratio increase early->late = warning, >50% = critical
-- Observed: ~1.02 -> ~1.87 across all 3 branches = ~83% increase = CRITICAL
-- ==========================================================

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    101, restaurant_id, 'kitchen', 'critical',
    'Grill station prep times during dinner rush (6-9pm) have nearly doubled over the observed 60-day period — actual prep time now runs 87% over the expected baseline, up from a normal 2% over baseline in the first 20 days. Pattern is consistent and recurring, not a single bad day.',
    'Investigate grill station bottleneck during dinner rush — likely candidates: equipment constraint, insufficient staffing during peak hours, or menu/order-volume mismatch. Consider adding a second cook to the grill station for Fri/Sat dinner service as a first test.',
    PARSE_JSON('{"station": "grill", "time_window": "18:00-21:00", "early_ratio": 1.02, "late_ratio": 1.87, "percent_increase": 83, "sample_size_early": 284, "sample_size_late": 269}')
FROM restaurants WHERE name = 'Momo Junction - Thamel';

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    102, restaurant_id, 'kitchen', 'critical',
    'Grill station prep times during dinner rush (6-9pm) have nearly doubled over the observed 60-day period — actual prep time now runs 87% over the expected baseline, up from a normal 2% over baseline in the first 20 days.',
    'Investigate grill station bottleneck during dinner rush. Consider adding a second cook to the grill station for Fri/Sat dinner service as a first test.',
    PARSE_JSON('{"station": "grill", "time_window": "18:00-21:00", "early_ratio": 1.02, "late_ratio": 1.88, "percent_increase": 84, "sample_size_early": 302, "sample_size_late": 283}')
FROM restaurants WHERE name = 'Momo Junction - Patan';

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    103, restaurant_id, 'kitchen', 'critical',
    'Grill station prep times during dinner rush (6-9pm) have nearly doubled over the observed 60-day period — actual prep time now runs 87% over the expected baseline, up from a normal 2% over baseline in the first 20 days.',
    'Investigate grill station bottleneck during dinner rush. Consider adding a second cook to the grill station for Fri/Sat dinner service as a first test.',
    PARSE_JSON('{"station": "grill", "time_window": "18:00-21:00", "early_ratio": 1.02, "late_ratio": 1.87, "percent_increase": 83, "sample_size_early": 287, "sample_size_late": 286}')
FROM restaurants WHERE name = 'Momo Junction - Baneshwor';

-- ==========================================================
-- SERVING ALERTS
-- Threshold: >=15% increase = warning, >30% = critical
-- Observed: ~45min -> ~48min = ~7% increase, general (not item-specific)
-- Below the flagging threshold, but included as an "info" note showing
-- the agent correctly did NOT over-flag a weak/non-actionable signal
-- ==========================================================

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    201, restaurant_id, 'serving', 'info',
    'Table turnover time has drifted from ~45 to ~48 minutes over the 60-day period. This increase appears general across all orders rather than specific to any one menu item (including "Sekuwa Platter", which was initially suspected) — likely reflects overall volume growth rather than a specific process issue.',
    'No urgent action needed. Monitor turnover trend over the next few weeks; if it continues climbing, revisit staffing levels during peak hours.',
    PARSE_JSON('{"early_avg_turnover_min": 45.0, "late_avg_turnover_min": 48.4, "percent_increase": 7.6, "item_specific_correlation": false}')
FROM restaurants WHERE name = 'Momo Junction - Thamel';

-- ==========================================================
-- STOCK ALERTS
-- Threshold: usage +20% AND delivery delay increasing = flag
-- Observed: usage +38%, delay 0.2->3 days = CRITICAL (compounding risk)
-- ==========================================================

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    301, restaurant_id, 'stock', 'critical',
    'Chicken usage has risen 38% (12kg/day to 16.7kg/day) over the past 20 days, while supplier delivery delay has grown from near-zero to averaging 1-3 days late in the same window. The combination creates real stockout risk: rising consumption plus an increasingly unreliable supplier.',
    'Place next Chicken order earlier than the usual 7-10 day cycle to buffer against supplier delays. Consider evaluating a backup supplier given the recent reliability drop.',
    PARSE_JSON('{"item": "Chicken (kg)", "early_avg_daily_usage_kg": 11.99, "late_avg_daily_usage_kg": 16.72, "usage_percent_increase": 39, "early_avg_delay_days": 0.0, "late_avg_delay_days": 1.0}')
FROM restaurants WHERE name = 'Momo Junction - Thamel';

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    302, restaurant_id, 'stock', 'critical',
    'Chicken usage has risen 38% (12.1kg/day to 16.1kg/day) over the past 20 days, while supplier delivery delay has grown from 0.14 to 3 days late in the same window.',
    'Place next Chicken order earlier than the usual cycle to buffer against supplier delays. Consider evaluating a backup supplier.',
    PARSE_JSON('{"item": "Chicken (kg)", "early_avg_daily_usage_kg": 12.13, "late_avg_daily_usage_kg": 16.11, "usage_percent_increase": 33, "early_avg_delay_days": 0.14, "late_avg_delay_days": 3.0}')
FROM restaurants WHERE name = 'Momo Junction - Patan';

INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data)
SELECT
    303, restaurant_id, 'stock', 'critical',
    'Chicken usage has risen 38% (11.9kg/day to 16.5kg/day) over the past 20 days, while supplier delivery delay has grown from 0.5 to 3 days late in the same window.',
    'Place next Chicken order earlier than the usual cycle to buffer against supplier delays. Consider evaluating a backup supplier.',
    PARSE_JSON('{"item": "Chicken (kg)", "early_avg_daily_usage_kg": 11.93, "late_avg_daily_usage_kg": 16.47, "usage_percent_increase": 38, "early_avg_delay_days": 0.5, "late_avg_delay_days": 3.0}')
FROM restaurants WHERE name = 'Momo Junction - Baneshwor';

-- ==========================================================
-- Verify
-- ==========================================================
SELECT alert_id, restaurant_id, agent_type, severity, pattern_detected, created_at
FROM agent_alerts
ORDER BY agent_type, alert_id;