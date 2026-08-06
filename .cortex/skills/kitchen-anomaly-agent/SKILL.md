---
name: kitchen-anomaly-agent
description: Detects station-level kitchen slowdown patterns that are invisible at floor level but become clear when prep-time data is aggregated across days and shifts. Use when asked to check kitchen performance, station slowdowns, prep time anomalies, or "how is the kitchen doing." Do NOT use for table turnover or serving-side issues (see serving-anomaly-agent). Do NOT use for inventory/stock questions (see stock-anomaly-agent).
---

# Kitchen Anomaly Agent

## Context
Database: RESTAURANT_OPS.CORE
Relevant tables:
- kitchen_tickets (ticket_id, restaurant_id, menu_item_id, station,
  special_instruction, created_at, started_at, completed_at,
  expected_prep_time_min, actual_prep_time_min, shift_id)
- menu_items (menu_item_id, restaurant_id, name, station, base_prep_time_min)
- staff_shifts (shift_id, restaurant_id, staff_name, role, station,
  shift_start, shift_end)
- restaurants (restaurant_id, name, brand_group, location)
- agent_alerts (write destination for findings)

A single slow ticket is normal variance and NOT worth flagging — a manager
on the floor would already notice one late order. The value of this agent
is catching *patterns across time* a human wouldn't naturally cross-reference:
recurring slowdowns tied to a specific station, time-of-day, or day-of-week,
that trend over multiple days/weeks.

## Workflow
1. For the target restaurant(s), compute the ratio of actual_prep_time_min
   to expected_prep_time_min for kitchen_tickets, grouped by:
   - station
   - hour-of-day bucket (e.g. lunch 11-14, dinner 18-21, other)
   - day-of-week type (weekday vs weekend)
2. Bucket results into time windows (e.g. 10-day rolling buckets) across the
   available date range and compare early-window average ratio vs
   late-window average ratio.
3. Flag a pattern only if:
   - the ratio has increased by at least 20% between early and late windows, AND
   - the pattern recurs across at least 3 distinct days (not a single spike)
4. For each flagged pattern, determine severity:
   - "warning" if ratio increase is 20-50%
   - "critical" if ratio increase is >50%
5. Write a row to agent_alerts with:
   - agent_type = 'kitchen'
   - pattern_detected = plain-language description (station, time window,
     magnitude, trend)
   - suggested_action = a concrete, actionable recommendation (e.g. "add a
     second cook to the grill station during Fri/Sat dinner rush" or
     "review grill station prep workflow — bottleneck may be equipment or
     staffing, not order volume")
   - supporting_data = JSON with the actual numbers (station, date range,
     early ratio, late ratio, sample size) so the finding is auditable, not
     a black-box claim
6. Summarize findings back to the user in plain language before/instead of
   raw SQL output — the person using this is a restaurant manager, not a
   data analyst.

## Common Mistakes
- Do not flag normal lunch/dinner busyness alone — only flag when the
  actual/expected ratio itself is trending worse over time, not just when
  volume is high.
- Do not treat a single bad day as a pattern — require recurrence.
- Do not recommend firing or blaming a specific staff member by name in
  suggested_action — focus on station/process-level recommendations.