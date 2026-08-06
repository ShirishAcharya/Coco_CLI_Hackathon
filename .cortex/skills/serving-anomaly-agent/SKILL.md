---
name: serving-anomaly-agent
description: Detects table turnover trends that drift over time, especially patterns correlated with menu changes, that aren't visible to a manager watching the floor in real time. Use when asked to check serving performance, table turnover, floor efficiency, or "how is service today/this week." Do NOT use for kitchen prep-time issues (see kitchen-anomaly-agent). Do NOT use for inventory/stock questions (see stock-anomaly-agent).
---

# Serving Anomaly Agent

## Context
Database: RESTAURANT_OPS.CORE
Relevant tables:
- orders (order_id, restaurant_id, table_id, server_id, seated_at,
  order_placed_at, payment_completed_at, party_size)
- tables (table_id, restaurant_id, capacity)
- menu_items (menu_item_id, restaurant_id, name, active_since)
- kitchen_tickets (join to orders via order_id to see which menu items
  were part of an order)
- restaurants (restaurant_id, name, brand_group, location)
- agent_alerts (write destination for findings)

A single slow table turn is normal — a manager on the floor sees that
immediately. The value here is catching turnover DRIFT over time (weeks,
not one shift), especially where it correlates with something structural
like a menu/recipe change, rather than just being busier that day.

## Workflow
1. Compute table turnover time (payment_completed_at - seated_at) for the
   target restaurant(s), bucketed into time windows across the available
   date range (e.g. rolling 10-20 day buckets).
2. Compare average turnover in early buckets vs. late buckets.
3. Cross-reference: check whether orders containing specific menu items
   (via kitchen_tickets -> menu_items) show a turnover increase that is
   notably larger than orders WITHOUT those items, in the same time window.
   This distinguishes "this specific item's prep/serving flow is a
   problem" from "the whole restaurant is just busier lately."
4. Also check each menu_item's active_since date — if a turnover increase
   begins shortly after a menu item's active_since, flag this as a
   possible correlation (not proven causation — say so explicitly in the
   alert).
5. Flag a pattern only if:
   - turnover has increased by at least 15% between early and late windows, AND
   - the increase is consistent across multiple days (not one busy weekend)
6. Severity: "warning" if 15-30% increase, "critical" if >30%.
7. Write finding to agent_alerts:
   - agent_type = 'serving'
   - pattern_detected = plain language (which restaurant, magnitude, any
     correlated menu item, whether it looks isolated to that item or
     general)
   - suggested_action = concrete recommendation (e.g. "review prep/plating
     workflow for [item] introduced on [date]" or, if the increase looks
     restaurant-wide rather than item-specific, "turnover slowdown appears
     general rather than tied to one item — review staffing levels or
     table availability during peak hours")
   - supporting_data = JSON with the actual numbers
8. Be honest in the summary if the data shows a general trend rather than
   a specific menu-item correlation — do not force a causal story that
   the numbers don't support.

## Common Mistakes
- Do not claim menu-item causation if non-trigger orders show a similar
  increase in the same window — that indicates a restaurant-wide trend,
  not an item-specific issue. Say so explicitly.
- Do not flag a single busy day/weekend as an anomaly.
- Do not recommend blaming a specific server by name — focus on
  process/menu/staffing level recommendations.