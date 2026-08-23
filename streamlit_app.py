import streamlit as st
import pandas as pd
import json
import subprocess
import urllib.request
from datetime import datetime
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session

st.set_page_config(page_title="Nightshift Agent", layout="wide", initial_sidebar_state="collapsed")

try:
    session = get_active_session()
except Exception:
    session = Session.builder.config("connection_name", "CocoHackathon").create()
session.sql("USE DATABASE RESTAURANT_OPS").collect()
session.sql("USE SCHEMA CORE").collect()

# ==========================================================
# Styling
# ==========================================================
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 2rem; max-width: 1200px; }

    .app-header {
        border-bottom: 1px solid #2a2e37;
        padding-bottom: 1.2rem;
        margin-bottom: 1.5rem;
    }
    .app-header h1 {
        font-size: 1.9rem;
        font-weight: 600;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }
    .app-header p {
        color: #8b8f98;
        font-size: 0.95rem;
        margin: 0;
    }

    .metric-card {
        background: #161a23;
        border: 1px solid #262b36;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
    }
    .metric-label {
        color: #8b8f98;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 600;
        color: #f0f1f5;
    }
    .metric-delta-up { color: #e5615a; font-size: 0.9rem; font-weight: 500; }
    .metric-delta-down { color: #4caf7d; font-size: 0.9rem; font-weight: 500; }

    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .status-critical { background: rgba(229, 97, 90, 0.15); color: #e5615a; border: 1px solid rgba(229, 97, 90, 0.3); }
    .status-warning  { background: rgba(224, 168, 68, 0.15); color: #e0a844; border: 1px solid rgba(224, 168, 68, 0.3); }
    .status-info     { background: rgba(96, 148, 224, 0.15); color: #6094e0; border: 1px solid rgba(96, 148, 224, 0.3); }
    .status-ok       { background: rgba(76, 175, 125, 0.15); color: #4caf7d; border: 1px solid rgba(76, 175, 125, 0.3); }
    .status-resolved { background: rgba(139, 143, 152, 0.15); color: #8b8f98; border: 1px solid rgba(139, 143, 152, 0.3); }
    .status-acknowledged { background: rgba(96, 148, 224, 0.15); color: #6094e0; border: 1px solid rgba(96, 148, 224, 0.3); }
    .status-actioned { background: rgba(76, 175, 125, 0.15); color: #4caf7d; border: 1px solid rgba(76, 175, 125, 0.3); }

    .alert-card {
        background: #161a23;
        border: 1px solid #262b36;
        border-left: 3px solid #444;
        border-radius: 8px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
    }
    .alert-card.critical { border-left-color: #e5615a; }
    .alert-card.warning { border-left-color: #e0a844; }
    .alert-card.info { border-left-color: #6094e0; }

    .alert-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f0f1f5;
        margin-bottom: 0.5rem;
    }
    .alert-body {
        color: #b5b9c2;
        font-size: 0.88rem;
        line-height: 1.5;
        margin-bottom: 0.6rem;
    }
    .alert-action {
        background: #0e1117;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        font-size: 0.85rem;
        color: #9fc9ff;
        border-left: 2px solid #3a5f8a;
    }
    .alert-meta {
        color: #62666f;
        font-size: 0.75rem;
        margin-top: 0.6rem;
    }

    .section-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8b8f98;
        font-weight: 600;
        margin-bottom: 0.8rem;
        margin-top: 0.5rem;
    }

    div[data-testid="stButton"] button {
        border-radius: 6px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# Header
# ==========================================================
st.markdown("""
<div class="app-header">
    <h1>Nightshift Agent</h1>
    <p>Multi-agent operational anomaly detection — Momo Junction restaurant group</p>
</div>
""", unsafe_allow_html=True)

restaurants_df = session.sql("SELECT restaurant_id, name, location FROM restaurants ORDER BY name").to_pandas()
restaurant_names = restaurants_df["NAME"].tolist()

col_select, col_spacer = st.columns([2, 3])
with col_select:
    selected_name = st.selectbox("Restaurant", restaurant_names, label_visibility="collapsed")
selected_id = int(restaurants_df[restaurants_df["NAME"] == selected_name]["RESTAURANT_ID"].iloc[0])
selected_location = restaurants_df[restaurants_df["NAME"] == selected_name]["LOCATION"].iloc[0]
st.caption(selected_location)

# ==========================================================
# Sidebar — item 4: adjustable detection thresholds
# ==========================================================
with st.sidebar:
    st.markdown("### Detection sensitivity")
    st.caption("Adjust how sensitive each agent is to drift before it flags a pattern.")
    kitchen_threshold = st.slider("Kitchen: prep-time increase %", min_value=5, max_value=100, value=20, step=5,
                                   help="Grill dinner-rush prep time increase (early vs. late window) that triggers a finding.")
    serving_threshold = st.slider("Serving: turnover increase %", min_value=5, max_value=100, value=15, step=5,
                                   help="Turnover increase for orders with the trigger menu item that triggers a finding.")
    stock_threshold = st.slider("Stock: usage increase %", min_value=5, max_value=100, value=20, step=5,
                                 help="Usage growth (combined with rising supplier delay) that triggers a finding.")
    st.caption("Thresholds apply live to the next check you run in each tab.")

st.write("")

tab_overview, tab_kitchen, tab_serving, tab_stock, tab_compare, tab_alerts = st.tabs(
    ["Overview", "Kitchen Agent", "Serving Agent", "Stock Agent", "Compare", "Alert History"]
)

# ==========================================================
# Helpers
# ==========================================================
def write_alert(restaurant_id, agent_type, severity, pattern, action, supporting_data):
    next_id_df = session.sql("SELECT COALESCE(MAX(alert_id), 0) + 1 AS next_id FROM agent_alerts").to_pandas()
    next_id = int(next_id_df["NEXT_ID"].iloc[0])
    data_json = json.dumps(supporting_data).replace("'", "''")
    pattern_escaped = pattern.replace("'", "''")
    action_escaped = action.replace("'", "''")
    session.sql(f"""
        INSERT INTO agent_alerts (alert_id, restaurant_id, agent_type, severity, pattern_detected, suggested_action, supporting_data, status)
        SELECT {next_id}, {restaurant_id}, '{agent_type}', '{severity}', '{pattern_escaped}', '{action_escaped}', PARSE_JSON('{data_json}'), 'open'
    """).collect()
    return next_id

def get_alert_status(alert_id):
    """Fetches the current status for a single alert (used for inline action controls
    right after logging a new finding, where we only have the alert_id cached)."""
    df = session.sql(f"SELECT COALESCE(status, 'open') AS status FROM agent_alerts WHERE alert_id = {alert_id}").to_pandas()
    return df["STATUS"].iloc[0] if len(df) else "open"

def status_pill(severity):
    label = {"critical": "Critical", "warning": "Warning", "info": "Info", "ok": "Normal",
              "resolved": "Resolved", "acknowledged": "Acknowledged", "actioned": "Actioned"}.get(severity, severity)
    return f'<span class="status-pill status-{severity}">{label}</span>'

def metric_card(label, value, delta=None, delta_up_is_bad=True):
    delta_html = ""
    if delta is not None:
        is_up = delta.strip().startswith("+")
        cls = "metric-delta-up" if (is_up == delta_up_is_bad) else "metric-delta-down"
        delta_html = f'<span class="{cls}">{delta}</span>'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value} {delta_html}</div>
    </div>
    """, unsafe_allow_html=True)

def run_cortex_streaming(prompt, log_placeholder, workdir=r"C:\Users\achar\Desktop\Personal Projects\Coco_CLI_Hackathon", connection="CocoHackathon"):
    """Invoke CoCo CLI in headless exec mode and stream its output live into the UI.

    cortex's own stdout is fully buffered when piped (not a real TTY), so output
    tends to arrive in one big burst near the end rather than incrementally. To
    avoid the UI looking frozen during that wait, a background thread reads the
    pipe while the main loop updates a live elapsed-time indicator every second,
    showing whatever partial output has arrived so far.
    """
    import shutil, threading, queue, time

    cortex_path = shutil.which("cortex")
    if cortex_path is None:
        log_placeholder.error("cortex CLI not found in this environment. Falling back to direct SQL logic.")
        return None

    try:
        process = subprocess.Popen(
            [cortex_path, "exec", prompt, "-c", connection, "--bypass", "--workdir", workdir],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            shell=False
        )
    except (FileNotFoundError, OSError) as e:
        log_placeholder.error(f"Failed to launch cortex CLI: {e}. Falling back to direct SQL logic.")
        return None

    line_queue = queue.Queue()

    def _reader():
        for line in process.stdout:
            line_queue.put(line)
        process.stdout.close()

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    output_lines = []
    start_time = time.time()
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    frame_idx = 0

    while reader_thread.is_alive() or not line_queue.empty():
        got_new_line = False
        while True:
            try:
                output_lines.append(line_queue.get_nowait())
                got_new_line = True
            except queue.Empty:
                break

        elapsed = int(time.time() - start_time)
        frame = spinner_frames[frame_idx % len(spinner_frames)]
        frame_idx += 1
        header = f"{frame} Agent working... ({elapsed}s elapsed)\n\n"

        if output_lines:
            log_placeholder.code(header + "".join(output_lines[-30:]), language=None)
        else:
            log_placeholder.code(header + "(waiting for output -- cortex buffers its output, "
                                  "so the full trace may appear all at once when it finishes)", language=None)
        time.sleep(0.5)

    process.wait()
    total_elapsed = int(time.time() - start_time)
    final_text = "".join(output_lines)
    log_placeholder.code(f"✓ Done in {total_elapsed}s\n\n{final_text}", language=None)
    return final_text

# ---- item 2: executable action buttons ----
# ---- new addition: alert acknowledgment / resolution tracking ----
WEBHOOK_URL = "https://webhook.site/YOUR-UNIQUE-ID-HERE"  # replace with a real webhook.site (or similar) test endpoint

def fire_webhook(payload):
    """Best-effort mock webhook call. Never blocks the UI on failure."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False

def update_alert_status(alert_id, new_status, action_label=None, notify=False):
    """Moves an alert through open -> acknowledged -> actioned -> resolved.
    Only 'actioned' sets action_taken/action_taken_at and fires the webhook;
    acknowledge/resolve are lighter-weight status-only transitions."""
    if action_label is not None:
        action_escaped = action_label.replace("'", "''")
        session.sql(f"""
            UPDATE agent_alerts
            SET status = '{new_status}', action_taken = '{action_escaped}', action_taken_at = CURRENT_TIMESTAMP()
            WHERE alert_id = {alert_id}
        """).collect()
    else:
        session.sql(f"""
            UPDATE agent_alerts SET status = '{new_status}' WHERE alert_id = {alert_id}
        """).collect()
    if notify:
        fire_webhook({
            "alert_id": alert_id,
            "status": new_status,
            "action_taken": action_label,
            "restaurant_id": selected_id,
            "restaurant_name": selected_name,
            "timestamp": datetime.utcnow().isoformat()
        })

def status_controls_for(agent_type, alert_id, current_status, key_suffix):
    """Renders the right next-step control(s) for an alert given its current status.
    open -> acknowledged -> actioned -> resolved. Each step is a deliberate,
    explicit click (human-in-the-loop), not automatic."""
    action_labels = {
        "kitchen": "Log Kitchen Bottleneck Incident",
        "serving": "Log Serving Slowdown Incident",
        "stock": "Trigger Emergency Supplier Order",
    }
    action_label = action_labels.get(agent_type, "Log Incident")

    if current_status == "open":
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Acknowledge", key=f"ack_{key_suffix}"):
                update_alert_status(alert_id, "acknowledged")
                st.rerun()
        with c2:
            if st.button(action_label, key=f"action_{key_suffix}"):
                update_alert_status(alert_id, "actioned", action_label=action_label, notify=True)
                st.success(f"{action_label} — logged and notification sent.")
                st.rerun()
    elif current_status == "acknowledged":
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button(action_label, key=f"action_{key_suffix}"):
                update_alert_status(alert_id, "actioned", action_label=action_label, notify=True)
                st.success(f"{action_label} — logged and notification sent.")
                st.rerun()
        with c2:
            if st.button("Mark resolved", key=f"resolve_{key_suffix}"):
                update_alert_status(alert_id, "resolved")
                st.rerun()
    elif current_status == "actioned":
        if st.button("Mark resolved", key=f"resolve_{key_suffix}"):
            update_alert_status(alert_id, "resolved")
            st.rerun()
    # resolved: no further controls

# ==========================================================
# OVERVIEW TAB
# ==========================================================
with tab_overview:
    alerts_df = session.sql(f"""
        SELECT alert_id, agent_type, severity, pattern_detected, suggested_action, created_at,
               COALESCE(status, 'open') AS status
        FROM agent_alerts WHERE restaurant_id = {selected_id}
        ORDER BY created_at DESC
    """).to_pandas()

    n_critical = len(alerts_df[alerts_df["SEVERITY"] == "critical"]) if len(alerts_df) else 0
    n_warning = len(alerts_df[alerts_df["SEVERITY"] == "warning"]) if len(alerts_df) else 0
    n_info = len(alerts_df[alerts_df["SEVERITY"] == "info"]) if len(alerts_df) else 0

    st.markdown('<div class="section-label">Current Status</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Critical alerts", n_critical)
    with c2:
        metric_card("Warnings", n_warning)
    with c3:
        metric_card("Informational", n_info)

    st.markdown('<div class="section-label">Recent Findings</div>', unsafe_allow_html=True)
    if len(alerts_df):
        for _idx, (_, row) in enumerate(alerts_df.head(5).iterrows()):
            sev = row["SEVERITY"]
            row_status = row["STATUS"]
            display_sev = row_status if row_status in ("acknowledged", "actioned", "resolved") else sev
            st.markdown(f"""
            <div class="alert-card {sev}">
                <div class="alert-title">{status_pill(display_sev)} &nbsp; {row['AGENT_TYPE'].capitalize()} Agent</div>
                <div class="alert-body">{row['PATTERN_DETECTED']}</div>
                <div class="alert-action">{row['SUGGESTED_ACTION']}</div>
            </div>
            """, unsafe_allow_html=True)
            if row_status != "resolved":
                status_controls_for(row["AGENT_TYPE"], row["ALERT_ID"], row_status, f"overview_{row['ALERT_ID']}_{_idx}")
    else:
        st.info("No alerts recorded yet for this restaurant. Run a check from one of the agent tabs.")

# ==========================================================
# KITCHEN AGENT TAB
# ==========================================================
with tab_kitchen:
    st.markdown('<div class="section-label">Kitchen Anomaly Agent</div>', unsafe_allow_html=True)
    st.caption("Detects station-level slowdown patterns that build up over time and are invisible at floor level.")
    st.write("")

    if st.button("Run kitchen check", key="run_kitchen"):
        with st.expander("Live agent reasoning (CoCo CLI)", expanded=True):
            log_area = st.empty()
            kitchen_prompt = (
                f"check kitchen performance for {selected_name}. "
                "As you work, narrate what you are doing in plain language before each step: "
                "say what data you are about to look at, what you find, and what you conclude, "
                "so a restaurant manager watching your output can follow your reasoning live."
            )
            cortex_output = run_cortex_streaming(kitchen_prompt, log_area)

        with st.spinner("Analyzing prep time trends across stations and shifts..."):
            query = f"""
                WITH kitchen_ratios AS (
                    SELECT
                        k.station,
                        DATEDIFF('day', '2026-06-01', k.created_at) AS day_offset,
                        k.actual_prep_time_min / NULLIF(k.expected_prep_time_min, 0) AS prep_ratio
                    FROM kitchen_tickets k
                    WHERE k.restaurant_id = {selected_id}
                      AND k.station = 'grill'
                      AND HOUR(k.created_at) BETWEEN 18 AND 21
                )
                SELECT
                    CASE WHEN day_offset < 20 THEN 'early' ELSE 'late' END AS window,
                    COUNT(*) AS n,
                    AVG(prep_ratio) AS avg_ratio
                FROM kitchen_ratios
                WHERE day_offset < 20 OR day_offset >= 40
                GROUP BY window
            """
            df = session.sql(query).to_pandas()

        # Persist results keyed by restaurant so switching tabs (which triggers a
        # rerun where this button is no longer "just clicked") still shows the
        # last result for whichever restaurant is currently selected.
        st.session_state[f"kitchen_result_{selected_id}"] = {
            "df": df, "cortex_output": cortex_output, "threshold": kitchen_threshold
        }

    cached = st.session_state.get(f"kitchen_result_{selected_id}")
    if cached:
        if cached.get("cortex_output"):
            with st.expander("Live agent reasoning (CoCo CLI) — last run", expanded=False):
                st.code(cached["cortex_output"], language=None)

        df = cached["df"]
        if len(df) == 2:
            early = df[df["WINDOW"] == "early"]["AVG_RATIO"].iloc[0]
            late = df[df["WINDOW"] == "late"]["AVG_RATIO"].iloc[0]
            early_n = int(df[df["WINDOW"] == "early"]["N"].iloc[0])
            late_n = int(df[df["WINDOW"] == "late"]["N"].iloc[0])
            pct_increase = ((late - early) / early) * 100

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("Early window ratio", f"{early:.2f}x")
            with c2:
                metric_card("Late window ratio", f"{late:.2f}x", delta=f"+{pct_increase:.0f}%")
            with c3:
                sev = "critical" if pct_increase > kitchen_threshold * 2.5 else ("warning" if pct_increase > kitchen_threshold else "ok")
                st.markdown(f'<div class="metric-card"><div class="metric-label">Status</div><div style="margin-top:0.3rem">{status_pill(sev)}</div></div>', unsafe_allow_html=True)

            if pct_increase > kitchen_threshold:
                severity = "critical" if pct_increase > kitchen_threshold * 2.5 else "warning"
                pattern = (f"Grill station prep times during dinner rush (6-9pm) increased {pct_increase:.0f}% "
                           f"over the observed period, from {early:.2f}x to {late:.2f}x expected prep time.")
                action = "Investigate grill station bottleneck during dinner rush. Consider adding a second cook during peak hours."

                st.markdown(f"""
                <div class="alert-card {severity}">
                    <div class="alert-title">{status_pill(severity)} &nbsp; Pattern detected</div>
                    <div class="alert-body">{pattern}</div>
                    <div class="alert-action">{action}</div>
                    <div class="alert-meta">Based on {early_n} grill tickets in the early window and {late_n} in the late window (dinner rush, 6-9pm).</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Log this finding to alert history", key="write_kitchen"):
                    aid = write_alert(selected_id, "kitchen", severity, pattern, action,
                                       {"station": "grill", "early_ratio": round(float(early), 2), "late_ratio": round(float(late), 2), "percent_increase": round(float(pct_increase), 1)})
                    st.session_state["last_kitchen_alert_id"] = aid
                    st.success(f"Alert {aid} logged.")

                if st.session_state.get("last_kitchen_alert_id"):
                    aid = st.session_state["last_kitchen_alert_id"]
                    status_controls_for("kitchen", aid, get_alert_status(aid), "kitchen_inline")
            else:
                st.markdown(f'<div class="alert-card"><div class="alert-title">{status_pill("ok")} &nbsp; No anomaly detected</div><div class="alert-body">Prep times are within normal range for the current threshold ({kitchen_threshold}%).</div></div>', unsafe_allow_html=True)
        else:
            st.info("Not enough data in both time windows to compare.")

# ==========================================================
# SERVING AGENT TAB
# ==========================================================
with tab_serving:
    st.markdown('<div class="section-label">Serving Anomaly Agent</div>', unsafe_allow_html=True)
    st.caption("Detects table turnover drift and checks whether it correlates with specific menu changes.")
    st.write("")

    if st.button("Run serving check", key="run_serving"):
        with st.expander("Live agent reasoning (CoCo CLI)", expanded=True):
            log_area = st.empty()
            serving_prompt = (
                f"check serving and table turnover performance for {selected_name}. "
                "As you work, narrate what you are doing in plain language before each step: "
                "say what data you are about to look at, what you find, and what you conclude, "
                "so a restaurant manager watching your output can follow your reasoning live."
            )
            cortex_output = run_cortex_streaming(serving_prompt, log_area)

        with st.spinner("Analyzing table turnover trends..."):
            query = f"""
                WITH order_turnover AS (
                    SELECT
                        o.order_id,
                        DATEDIFF('day', '2026-06-01', o.seated_at) AS day_offset,
                        DATEDIFF('minute', o.seated_at, o.payment_completed_at) AS turnover_minutes,
                        EXISTS (
                            SELECT 1 FROM kitchen_tickets k
                            JOIN menu_items m ON m.menu_item_id = k.menu_item_id
                            WHERE k.order_id = o.order_id AND m.name = 'Sekuwa Platter'
                        ) AS includes_trigger_item
                    FROM orders o
                    WHERE o.restaurant_id = {selected_id}
                )
                SELECT
                    includes_trigger_item,
                    CASE WHEN day_offset < 30 THEN 'before' ELSE 'after' END AS window,
                    COUNT(*) AS n,
                    AVG(turnover_minutes) AS avg_turnover
                FROM order_turnover
                GROUP BY includes_trigger_item, window
            """
            df = session.sql(query).to_pandas()

        st.session_state[f"serving_result_{selected_id}"] = {"df": df, "cortex_output": cortex_output}

    cached = st.session_state.get(f"serving_result_{selected_id}")
    if cached:
        if cached.get("cortex_output"):
            with st.expander("Live agent reasoning (CoCo CLI) — last run", expanded=False):
                st.code(cached["cortex_output"], language=None)

        df = cached["df"]
        if len(df) == 4:
            trig_before = df[(df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "before")]["AVG_TURNOVER"].iloc[0]
            trig_after = df[(df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "after")]["AVG_TURNOVER"].iloc[0]
            other_before = df[(~df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "before")]["AVG_TURNOVER"].iloc[0]
            other_after = df[(~df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "after")]["AVG_TURNOVER"].iloc[0]
            trig_n = int(df[(df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "after")]["N"].iloc[0])
            other_n = int(df[(~df["INCLUDES_TRIGGER_ITEM"]) & (df["WINDOW"] == "after")]["N"].iloc[0])

            trig_pct = ((trig_after - trig_before) / trig_before) * 100
            other_pct = ((other_after - other_before) / other_before) * 100

            c1, c2 = st.columns(2)
            with c1:
                metric_card("Orders with Sekuwa Platter", f"{trig_before:.1f} to {trig_after:.1f} min", delta=f"+{trig_pct:.1f}%")
            with c2:
                metric_card("Orders without it", f"{other_before:.1f} to {other_after:.1f} min", delta=f"+{other_pct:.1f}%")

            is_item_specific = trig_pct > (other_pct + 10)

            if trig_pct > serving_threshold and is_item_specific:
                pattern = (f"Turnover for orders including Sekuwa Platter increased {trig_pct:.1f}%, "
                           f"notably more than the general trend ({other_pct:.1f}%), suggesting an item-specific issue.")
                action = "Review prep and plating workflow for Sekuwa Platter."
                severity = "critical" if trig_pct > serving_threshold * 2 else "warning"
            else:
                pattern = (f"Turnover increased {trig_pct:.1f}% for orders with the trigger item, but a similar "
                           f"{other_pct:.1f}% increase appears across all orders. This looks like a general trend, "
                           f"not specific to one menu item.")
                action = "No urgent item-specific action needed. Monitor overall turnover and review peak-hour staffing if the trend continues."
                severity = "info"

            st.markdown(f"""
            <div class="alert-card {severity}">
                <div class="alert-title">{status_pill(severity)} &nbsp; Finding</div>
                <div class="alert-body">{pattern}</div>
                <div class="alert-action">{action}</div>
                <div class="alert-meta">Based on {trig_n} orders with the trigger item and {other_n} without it, in the recent window.</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Log this finding to alert history", key="write_serving"):
                aid = write_alert(selected_id, "serving", severity, pattern, action,
                                   {"trigger_before": round(float(trig_before), 1), "trigger_after": round(float(trig_after), 1),
                                    "other_before": round(float(other_before), 1), "other_after": round(float(other_after), 1)})
                st.session_state["last_serving_alert_id"] = aid
                st.success(f"Alert {aid} logged.")

            if severity != "info" and st.session_state.get("last_serving_alert_id"):
                aid = st.session_state["last_serving_alert_id"]
                status_controls_for("serving", aid, get_alert_status(aid), "serving_inline")
        else:
            st.info("Not enough data to compare both groups across both windows.")

# ==========================================================
# STOCK AGENT TAB
# ==========================================================
with tab_stock:
    st.markdown('<div class="section-label">Stock Anomaly Agent</div>', unsafe_allow_html=True)
    st.caption("Detects compounding stockout risk from rising usage velocity combined with supplier delivery variance.")
    st.write("")

    if st.button("Run stock check", key="run_stock"):
        with st.expander("Live agent reasoning (CoCo CLI)", expanded=True):
            log_area = st.empty()
            stock_prompt = (
                f"check inventory and supplier risk for {selected_name}. "
                "As you work, narrate what you are doing in plain language before each step: "
                "say what data you are about to look at, what you find, and what you conclude, "
                "so a restaurant manager watching your output can follow your reasoning live."
            )
            cortex_output = run_cortex_streaming(stock_prompt, log_area)

        with st.spinner("Analyzing usage and supplier trends..."):
            usage_query = f"""
                WITH usage_trend AS (
                    SELECT
                        DATEDIFF('day', '2026-06-01', u.date) AS day_offset,
                        u.quantity_used
                    FROM inventory_usage_log u
                    JOIN inventory_items i ON i.inventory_item_id = u.inventory_item_id
                    WHERE i.restaurant_id = {selected_id} AND i.name = 'Chicken (kg)'
                )
                SELECT
                    CASE WHEN day_offset < 40 THEN 'before' ELSE 'after' END AS window,
                    COUNT(*) AS n,
                    AVG(quantity_used) AS avg_usage
                FROM usage_trend GROUP BY window
            """
            delay_query = f"""
                WITH supplier_delay AS (
                    SELECT
                        DATEDIFF('day', '2026-06-01', s.ordered_at) AS day_offset,
                        DATEDIFF('day', s.expected_delivery_date, s.actual_delivery_date) AS delay_days
                    FROM supplier_orders s
                    JOIN inventory_items i ON i.inventory_item_id = s.inventory_item_id
                    WHERE i.restaurant_id = {selected_id} AND i.name = 'Chicken (kg)'
                      AND s.actual_delivery_date IS NOT NULL
                )
                SELECT
                    CASE WHEN day_offset < 40 THEN 'before' ELSE 'after' END AS window,
                    COUNT(*) AS n,
                    AVG(delay_days) AS avg_delay
                FROM supplier_delay GROUP BY window
            """
            usage_df = session.sql(usage_query).to_pandas()
            delay_df = session.sql(delay_query).to_pandas()
            stock_df = session.sql(f"SELECT current_stock FROM inventory_items WHERE restaurant_id = {selected_id} AND name = 'Chicken (kg)'").to_pandas()

        st.session_state[f"stock_result_{selected_id}"] = {
            "usage_df": usage_df, "delay_df": delay_df, "stock_df": stock_df, "cortex_output": cortex_output
        }

    cached = st.session_state.get(f"stock_result_{selected_id}")
    if cached:
        if cached.get("cortex_output"):
            with st.expander("Live agent reasoning (CoCo CLI) — last run", expanded=False):
                st.code(cached["cortex_output"], language=None)

        usage_df, delay_df, stock_df = cached["usage_df"], cached["delay_df"], cached["stock_df"]
        if len(usage_df) == 2 and len(delay_df) == 2:
            usage_before = usage_df[usage_df["WINDOW"] == "before"]["AVG_USAGE"].iloc[0]
            usage_after = usage_df[usage_df["WINDOW"] == "after"]["AVG_USAGE"].iloc[0]
            usage_pct = ((usage_after - usage_before) / usage_before) * 100
            usage_before_n = int(usage_df[usage_df["WINDOW"] == "before"]["N"].iloc[0])
            usage_after_n = int(usage_df[usage_df["WINDOW"] == "after"]["N"].iloc[0])

            delay_before = delay_df[delay_df["WINDOW"] == "before"]["AVG_DELAY"].iloc[0]
            delay_after = delay_df[delay_df["WINDOW"] == "after"]["AVG_DELAY"].iloc[0]

            current_stock = float(stock_df["CURRENT_STOCK"].iloc[0]) if len(stock_df) else 0
            buffer_days = current_stock / usage_after if usage_after else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("Usage per day (kg)", f"{usage_before:.1f} to {usage_after:.1f}", delta=f"+{usage_pct:.0f}%")
            with c2:
                metric_card("Avg supplier delay", f"{delay_before:.1f} to {delay_after:.1f} days")
            with c3:
                metric_card("Stock buffer", f"{buffer_days:.1f} days")

            if usage_pct > stock_threshold and delay_after > delay_before:
                severity = "critical" if buffer_days < delay_after else "warning"
                pattern = (f"Chicken usage rose {usage_pct:.0f}% while supplier delivery delay grew from "
                           f"{delay_before:.1f} to {delay_after:.1f} days, creating compounding stockout risk. "
                           f"Current stock covers approximately {buffer_days:.1f} days at the latest usage rate.")
                action = "Place the next Chicken order earlier than usual. Evaluate a backup supplier given the reliability drop."

                st.markdown(f"""
                <div class="alert-card {severity}">
                    <div class="alert-title">{status_pill(severity)} &nbsp; Pattern detected</div>
                    <div class="alert-body">{pattern}</div>
                    <div class="alert-action">{action}</div>
                    <div class="alert-meta">Based on {usage_before_n} usage-log entries in the early window and {usage_after_n} in the recent window.</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Log this finding to alert history", key="write_stock"):
                    aid = write_alert(selected_id, "stock", severity, pattern, action,
                                       {"usage_before": round(float(usage_before), 2), "usage_after": round(float(usage_after), 2),
                                        "delay_before": round(float(delay_before), 2), "delay_after": round(float(delay_after), 2),
                                        "buffer_days": round(float(buffer_days), 1)})
                    st.session_state["last_stock_alert_id"] = aid
                    st.success(f"Alert {aid} logged.")

                if st.session_state.get("last_stock_alert_id"):
                    aid = st.session_state["last_stock_alert_id"]
                    status_controls_for("stock", aid, get_alert_status(aid), "stock_inline")
            else:
                st.markdown(f'<div class="alert-card"><div class="alert-title">{status_pill("ok")} &nbsp; No compounding risk detected</div><div class="alert-body">Usage and supplier reliability are both stable for the current threshold ({stock_threshold}%).</div></div>', unsafe_allow_html=True)
        else:
            st.info("Not enough data to compare both windows.")

# ==========================================================
# COMPARE TAB — item 4: cross-branch comparison
# ==========================================================
with tab_compare:
    st.markdown('<div class="section-label">Cross-Branch Comparison</div>', unsafe_allow_html=True)
    st.caption("Alert volume across all restaurants, broken down by agent and severity.")
    st.write("")

    compare_df = session.sql("""
        SELECT r.name AS restaurant_name, a.agent_type, a.severity, COUNT(*) AS alert_count
        FROM agent_alerts a
        JOIN restaurants r ON r.restaurant_id = a.restaurant_id
        GROUP BY r.name, a.agent_type, a.severity
        ORDER BY r.name, a.agent_type
    """).to_pandas()

    if len(compare_df):
        chart_rendered = False
        try:
            import plotly.express as px
            fig = px.bar(
                compare_df, x="RESTAURANT_NAME", y="ALERT_COUNT", color="SEVERITY",
                facet_col="AGENT_TYPE", barmode="stack",
                color_discrete_map={"critical": "#e5615a", "warning": "#e0a844", "info": "#6094e0"},
                labels={"RESTAURANT_NAME": "Restaurant", "ALERT_COUNT": "Alerts", "SEVERITY": "Severity", "AGENT_TYPE": "Agent"},
            )
            fig.update_layout(
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#f0f1f5",
                legend_title_text="Severity", margin=dict(t=40, b=20)
            )
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1].capitalize()))
            st.plotly_chart(fig, use_container_width=True)
            chart_rendered = True
        except ImportError:
            pass

        if not chart_rendered:
            # Plotly isn't available in this environment (e.g. not installed on the
            # Snowflake-hosted app) -- fall back to Streamlit's built-in bar_chart,
            # which needs no extra dependency and works everywhere.
            st.caption("Plotly isn't available in this environment — showing a native chart instead.")
            pivot = compare_df.pivot_table(
                index="RESTAURANT_NAME", columns="SEVERITY", values="ALERT_COUNT", aggfunc="sum", fill_value=0
            )
            st.bar_chart(pivot)

        st.write("")
        st.markdown('<div class="section-label">Raw comparison data</div>', unsafe_allow_html=True)
        st.dataframe(compare_df, use_container_width=True, hide_index=True)

        st.write("")
        st.markdown('<div class="section-label">Totals by restaurant</div>', unsafe_allow_html=True)
        totals = compare_df.groupby("RESTAURANT_NAME")["ALERT_COUNT"].sum().reset_index().sort_values("ALERT_COUNT", ascending=False)
        cols = st.columns(len(totals)) if len(totals) else [st]
        for col, (_, row) in zip(cols, totals.iterrows()):
            with col:
                metric_card(row["RESTAURANT_NAME"], int(row["ALERT_COUNT"]))
    else:
        st.info("No alerts logged yet across any restaurant. Run checks and log findings to populate this comparison.")

# ==========================================================
# ALERT HISTORY TAB
# ==========================================================
with tab_alerts:
    st.markdown('<div class="section-label">All Alerts</div>', unsafe_allow_html=True)

    all_alerts_df = session.sql("""
        SELECT a.alert_id, a.restaurant_id, r.name AS restaurant_name, a.agent_type, a.severity,
               a.pattern_detected, a.suggested_action, a.created_at,
               COALESCE(a.status, 'open') AS status, a.action_taken, a.action_taken_at
        FROM agent_alerts a
        JOIN restaurants r ON r.restaurant_id = a.restaurant_id
        ORDER BY a.created_at DESC
    """).to_pandas()

    if len(all_alerts_df):
        fc1, fc2, fc3 = st.columns([1, 1, 1])
        with fc1:
            severity_filter = st.multiselect("Severity", options=sorted(all_alerts_df["SEVERITY"].unique().tolist()),
                                              default=sorted(all_alerts_df["SEVERITY"].unique().tolist()))
        with fc2:
            agent_filter = st.multiselect("Agent", options=sorted(all_alerts_df["AGENT_TYPE"].unique().tolist()),
                                           default=sorted(all_alerts_df["AGENT_TYPE"].unique().tolist()))
        with fc3:
            status_filter = st.multiselect("Status", options=sorted(all_alerts_df["STATUS"].unique().tolist()),
                                            default=sorted(all_alerts_df["STATUS"].unique().tolist()))

        filtered = all_alerts_df[
            all_alerts_df["SEVERITY"].isin(severity_filter)
            & all_alerts_df["AGENT_TYPE"].isin(agent_filter)
            & all_alerts_df["STATUS"].isin(status_filter)
        ]

        st.write("")
        for _idx, (_, row) in enumerate(filtered.iterrows()):
            sev = row["SEVERITY"]
            row_status = row["STATUS"]
            display_sev = row_status if row_status in ("acknowledged", "actioned", "resolved") else sev
            meta = f"Alert #{row['ALERT_ID']} — {row['CREATED_AT']}"
            if row_status == "actioned":
                meta += f" — actioned: {row['ACTION_TAKEN']} at {row['ACTION_TAKEN_AT']}"
            elif row_status == "resolved" and row["ACTION_TAKEN"]:
                meta += f" — resolved (last action: {row['ACTION_TAKEN']})"
            st.markdown(f"""
            <div class="alert-card {sev}">
                <div class="alert-title">{status_pill(display_sev)} &nbsp; {row['AGENT_TYPE'].capitalize()} Agent — {row['RESTAURANT_NAME']}</div>
                <div class="alert-body">{row['PATTERN_DETECTED']}</div>
                <div class="alert-action">{row['SUGGESTED_ACTION']}</div>
                <div class="alert-meta">{meta}</div>
            </div>
            """, unsafe_allow_html=True)
            if row_status != "resolved":
                status_controls_for(row["AGENT_TYPE"], row["ALERT_ID"], row_status, f"history_{row['ALERT_ID']}_{_idx}")
    else:
        st.info("No alerts recorded yet.")