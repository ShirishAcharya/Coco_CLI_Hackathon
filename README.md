# Nightshift Agent

Multi-agent operational anomaly detection for restaurants, built with Snowflake CoCo CLI.

Built for the Snowflake CoCo CLI Hackathon 2026 — Problem Statement 1: Intelligent Workflow Automation Agent.

## The Problem

Restaurant managers catch visible, single-event problems easily — a slow table, a late order. The costly problems are the invisible ones: patterns that only show up when you look across weeks of data, which no one has time to manually trend-watch.

This project builds three specialized AI agents that watch different parts of restaurant operations, detect patterns that would be invisible to a manager on the floor, and surface them with evidence and a suggested fix. The agents recommend, they do not act autonomously — this is a deliberate design choice, since restaurant staff are unlikely to accept AI making unilateral operational decisions, but will accept AI that flags evidence-backed patterns for a human to act on.

## System Overview

Three agents, one per operational area, modeled on real restaurant ERP domain experience:

- **Kitchen agent** — detects station-level prep-time slowdowns that build up over days or weeks (for example, a grill station degrading during dinner rush)
- **Serving agent** — detects table turnover trends, and checks whether they correlate with specific menu or recipe changes rather than assuming a cause
- **Stock agent** — detects compounding stockout risk from the combination of rising usage velocity and growing supplier delivery variance

All three agents write their findings to a shared `agent_alerts` table, so they function as one coherent system rather than three disconnected scripts. In testing, the three agents independently converged on a connected root cause at one branch: a kitchen bottleneck was driving both slower table turnover and faster inventory depletion.

## Architecture

- **Snowflake** — data warehouse. Database `RESTAURANT_OPS`, schema `CORE`, 10 tables covering restaurants, menu items, staff shifts, kitchen tickets, orders, tables, inventory, supplier orders, and agent alerts.
- **CoCo CLI** — each agent is defined as a CoCo Agent Skill (`.cortex/skills/*/SKILL.md`), specifying what data to examine, what counts as an anomaly, severity thresholds, and what action to suggest. Agents are invoked with natural language and autonomously generate and run their own SQL against Snowflake.
- **Streamlit in Snowflake** — a deployed dashboard that lets a user select a restaurant, run any of the three checks, and review alert history, using the same underlying tables as the CLI agents.
- **Python (Faker)** — synthetic data generator producing 60 days of data across 3 branches of a fictional restaurant chain ("Momo Junction"), with three anomaly patterns deliberately modeled in for demonstration and testing.

## Repository Structure

```
schema.sql                          Database DDL for all 10 tables
generate_data.py                    Synthetic data generator
load_data.sql                       PUT + COPY INTO data loading script
populate_alerts.sql                 Fallback alert population (SQL-verified findings)
streamlit_app.py                    Streamlit-in-Snowflake dashboard
.cortex/skills/kitchen-anomaly-agent/SKILL.md
.cortex/skills/serving-anomaly-agent/SKILL.md
.cortex/skills/stock-anomaly-agent/SKILL.md
output_csv/                         Generated synthetic CSV data (Not included in the repo due to large data)
```

## Running This Project

1. Run `schema.sql` against a Snowflake account to create the database and tables
2. Run `generate_data.py` to produce synthetic CSVs in `output_csv/`
3. Run `load_data.sql` via the Snowflake CLI to load the data
4. Install CoCo CLI and connect it to the same Snowflake account
5. From the project root, run `cortex` and invoke any agent, for example:
   ```
   $kitchen-anomaly-agent check kitchen performance for Momo Junction - Thamel
   ```
6. Deploy `streamlit_app.py` as a Streamlit-in-Snowflake app for the dashboard view

## Design Notes

- No customer-modification/modifier system was modeled, as heavy dish customization is less common in the Nepali restaurant context this project draws on; kitchen variance is instead captured through station, time-of-day, and day-of-week patterns.
- Anomalies require recurrence across multiple days, not a single event, matching the core premise: these agents exist to catch what a floor manager cannot, not to duplicate what they already see.
- The serving agent explicitly tests and rules out plausible-but-wrong correlations (for example, checking whether a new menu item caused a turnover slowdown, then correctly identifying the trend as restaurant-wide instead) rather than assuming causation.
- The stock agent intentionally avoids flagging routine reorder situations, only escalating when usage growth and supplier reliability decline occur together.

## Team

Nightshift Agent — Shirish Acharya (solo)

## License
 
This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.