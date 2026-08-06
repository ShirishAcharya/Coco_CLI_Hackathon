---
name: stock-anomaly-agent
description: Detects stockout risk from the combination of rising usage velocity and growing supplier delivery variance — a compounding risk calculation a manager wouldn't naturally compute by watching stock levels alone. Use when asked to check inventory, stock levels, stockout risk, or supplier reliability. Do NOT use for kitchen prep-time issues (see kitchen-anomaly-agent). Do NOT use for table turnover/serving issues (see serving-anomaly-agent).
---

# Stock Anomaly Agent

## Context
Database: RESTAURANT_OPS.CORE
Relevant tables:
- inventory_items (inventory_item_id, restaurant_id, name, unit,
  current_stock, reorder_threshold)
- inventory_usage_log (log_id, inventory_item_id, date, quantity_used)
- supplier_orders (supplier_order_id, inventory_item_id, ordered_at,
  expected_delivery_date, actual_delivery_date)
- restaurants (restaurant_id, name, brand_group, location)
- agent_alerts (write destination for findings)

A single low-stock reading is easy for a manager to notice by looking at
the shelf. The value here is projecting FORWARD risk: if usage velocity is
climbing AND supplier delivery is becoming less reliable at the same time,
the two combine into a risk that isn't obvious from either signal alone.

## Workflow
1. For each inventory item at the target restaurant(s), compute daily
   usage velocity over time, bucketed into windows (e.g. rolling 10-20 day
   buckets) across the available date range.
2. Compute average delivery delay (actual_delivery_date -
   expected_delivery_date) for that item's supplier_orders, same bucketing.
3. Flag an item as elevated risk if BOTH:
   - usage velocity has increased by at least 20% between early and late
     windows, AND
   - average delivery delay has also increased (even modestly) in the same
     window
4. For flagged items, estimate days-until-stockout: current_stock /
   recent average daily usage. Combine with the delivery delay trend to
   describe realistic risk (e.g. "at current usage, stock covers ~5 days,
   but recent deliveries have been arriving 2-3 days late — real risk of
   stockout before next delivery lands").
5. Severity: "warning" if estimated buffer (days-until-stockout minus
   typical delay) is positive but slim (<3 days), "critical" if the
   buffer is negative (i.e. projected stockout before a delayed delivery
   would likely arrive).
6. Write finding to agent_alerts:
   - agent_type = 'stock'
   - pattern_detected = plain language (item, restaurant, usage trend,
     delivery trend, estimated buffer)
   - suggested_action = concrete recommendation (e.g. "place next order
     for [item] earlier than usual given recent supplier delays" or
     "consider a backup supplier for [item] given delivery reliability
     has degraded")
   - supporting_data = JSON with the actual numbers (usage before/after,
     delay before/after, current_stock, estimated buffer days)

## Common Mistakes
- Do not flag purely on low current_stock alone if usage/delivery trends
  are both stable — that's a normal reorder situation, not an anomaly.
- Do not flag purely on rising usage if delivery is still reliable — that
  might just mean the item is more popular, worth a note but not a
  critical alert.
- Only combine both signals (usage AND delivery) for the higher-severity
  tiers, per the workflow above.