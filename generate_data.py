import random
import csv
import os
from datetime import datetime, timedelta, date
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

OUT_DIR = "output_csv"
os.makedirs(OUT_DIR, exist_ok=True)

NUM_DAYS = 60
START_DATE = date(2026, 6, 1)  # 60 days ending ~July 30

# ==========================================================
# 1. Restaurants (1 brand, 3 branches)
# ==========================================================
restaurants = [
    {"restaurant_id": 1, "name": "Momo Junction - Thamel", "brand_group": "Momo Junction", "location": "Thamel, Kathmandu"},
    {"restaurant_id": 2, "name": "Momo Junction - Patan", "brand_group": "Momo Junction", "location": "Patan, Lalitpur"},
    {"restaurant_id": 3, "name": "Momo Junction - Baneshwor", "brand_group": "Momo Junction", "location": "Baneshwor, Kathmandu"},
]

# ==========================================================
# 2. Menu items (shared menu structure across branches)
# ==========================================================
MENU_TEMPLATE = [
    # name, category, station, base_prep_time_min, price
    ("Steam Momo (Chicken)", "main", "steamer", 12, 220),
    ("Fried Momo (Buff)", "main", "grill", 15, 240),
    ("Chicken Chowmein", "main", "grill", 14, 260),
    ("Thukpa", "main", "curry", 16, 250),
    ("Sekuwa Platter", "main", "grill", 22, 450),
    ("Paneer Curry", "main", "curry", 18, 300),
    ("Veg Spring Roll", "appetizer", "grill", 10, 180),
    ("Chicken Lollipop", "appetizer", "grill", 13, 320),
    ("Cold Drink", "beverage", "cold", 2, 90),
    ("Lassi", "beverage", "cold", 4, 120),
    ("Gulab Jamun", "dessert", "dessert", 5, 140),
    ("Kheer", "dessert", "dessert", 6, 150),
]

menu_items = []
menu_item_id = 1
# menu item that will get a "recipe change" on day 30 to correlate with turnover slowdown
TURNOVER_TRIGGER_ITEM_NAME = "Sekuwa Platter"
turnover_trigger_ids = {}

for r in restaurants:
    for name, category, station, base_prep, price in MENU_TEMPLATE:
        active_since = START_DATE - timedelta(days=random.randint(200, 600))
        if name == TURNOVER_TRIGGER_ITEM_NAME:
            # simulate a recipe change 30 days into our window
            active_since = START_DATE + timedelta(days=30)
            turnover_trigger_ids[r["restaurant_id"]] = menu_item_id
        menu_items.append({
            "menu_item_id": menu_item_id,
            "restaurant_id": r["restaurant_id"],
            "name": name,
            "category": category,
            "station": station,
            "base_prep_time_min": base_prep,
            "price": price,
            "active_since": active_since.isoformat(),
        })
        menu_item_id += 1

# grill station items per restaurant (for kitchen slowdown anomaly)
grill_items_by_restaurant = {}
for r in restaurants:
    grill_items_by_restaurant[r["restaurant_id"]] = [
        m["menu_item_id"] for m in menu_items
        if m["restaurant_id"] == r["restaurant_id"] and m["station"] == "grill"
    ]

# ==========================================================
# 3. Staff shifts (cooks + servers, daily, per restaurant)
# ==========================================================
staff_shifts = []
shift_id = 1
COOK_NAMES = ["Sujan", "Bikash", "Anita", "Rohit", "Sabina", "Kiran"]
SERVER_NAMES = ["Prakash", "Gita", "Manish", "Puja", "Deepak", "Naresh"]
STATIONS = ["grill", "curry", "steamer", "cold", "dessert"]

# map (restaurant_id, date) -> list of shift_ids for cooks per station, and servers
shifts_by_day = {}  # key: (restaurant_id, date) -> {"cooks": {station: shift_id}, "servers": [shift_id,...]}

for r in restaurants:
    for d in range(NUM_DAYS):
        cur_date = START_DATE + timedelta(days=d)
        day_shifts = {"cooks": {}, "servers": []}
        # one cook per station per day
        for station in STATIONS:
            cook_name = random.choice(COOK_NAMES)
            shift_start = datetime.combine(cur_date, datetime.min.time()) + timedelta(hours=11)
            shift_end = shift_start + timedelta(hours=10)
            staff_shifts.append({
                "shift_id": shift_id,
                "restaurant_id": r["restaurant_id"],
                "staff_name": cook_name,
                "role": "cook",
                "station": station,
                "shift_start": shift_start.isoformat(),
                "shift_end": shift_end.isoformat(),
            })
            day_shifts["cooks"][station] = shift_id
            shift_id += 1
        # 2-3 servers per day
        for _ in range(random.randint(2, 3)):
            server_name = random.choice(SERVER_NAMES)
            shift_start = datetime.combine(cur_date, datetime.min.time()) + timedelta(hours=11)
            shift_end = shift_start + timedelta(hours=10)
            staff_shifts.append({
                "shift_id": shift_id,
                "restaurant_id": r["restaurant_id"],
                "staff_name": server_name,
                "role": "server",
                "station": None,
                "shift_start": shift_start.isoformat(),
                "shift_end": shift_end.isoformat(),
            })
            day_shifts["servers"].append(shift_id)
            shift_id += 1
        shifts_by_day[(r["restaurant_id"], cur_date)] = day_shifts

# ==========================================================
# 4. Tables
# ==========================================================
tables = []
table_id = 1
tables_by_restaurant = {}
for r in restaurants:
    ids = []
    for _ in range(12):  # 12 tables per branch
        tables.append({
            "table_id": table_id,
            "restaurant_id": r["restaurant_id"],
            "capacity": random.choice([2, 2, 4, 4, 4, 6, 8]),
        })
        ids.append(table_id)
        table_id += 1
    tables_by_restaurant[r["restaurant_id"]] = ids

# ==========================================================
# 5. Orders + Kitchen tickets (generated together, per day)
# ==========================================================
orders = []
kitchen_tickets = []
order_id = 1
ticket_id = 1

# dinner rush hours where kitchen slowdown anomaly will manifest
DINNER_RUSH_HOURS = [18, 19, 20, 21]
SLOWDOWN_START_DAY = 25  # slowdown pattern starts showing from day 25 onward, worsens toward day 60

for r in restaurants:
    rid = r["restaurant_id"]
    for d in range(NUM_DAYS):
        cur_date = START_DATE + timedelta(days=d)
        is_weekend = cur_date.weekday() in (4, 5)  # Fri, Sat
        day_shifts = shifts_by_day[(rid, cur_date)]
        num_orders_today = random.randint(35, 55) if is_weekend else random.randint(20, 35)

        for _ in range(num_orders_today):
            hour = random.choices(
                population=list(range(11, 22)),
                weights=[3,3,4,5,6,4,3,6,8,9,7],  # lunch + dinner peaks
                k=1
            )[0]
            minute = random.randint(0, 59)
            seated_at = datetime.combine(cur_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
            order_placed_at = seated_at + timedelta(minutes=random.randint(2, 6))

            table_id_choice = random.choice(tables_by_restaurant[rid])
            server_id_choice = random.choice(day_shifts["servers"])
            party_size = random.choice([1,2,2,2,3,4,4,5,6])

            # base turnover time
            base_turnover_min = random.randint(35, 55)

            # TURNOVER ANOMALY: if this order includes the trigger menu item
            # and it's after the "recipe change" date, turnover degrades
            trigger_item_id = turnover_trigger_ids.get(rid)
            includes_trigger_item = trigger_item_id is not None and random.random() < 0.25
            turnover_penalty = 0
            if includes_trigger_item and d >= 30:
                days_since_change = d - 30
                turnover_penalty = min(25, days_since_change * 0.9)  # grows over time, caps at 25 min

            payment_completed_at = seated_at + timedelta(minutes=base_turnover_min + turnover_penalty)

            orders.append({
                "order_id": order_id,
                "restaurant_id": rid,
                "table_id": table_id_choice,
                "server_id": server_id_choice,
                "seated_at": seated_at.isoformat(),
                "order_placed_at": order_placed_at.isoformat(),
                "payment_completed_at": payment_completed_at.isoformat(),
                "party_size": party_size,
            })

            # 1-3 kitchen tickets per order
            num_items = random.randint(1, 3)
            chosen_items = random.sample(
                [m for m in menu_items if m["restaurant_id"] == rid],
                k=min(num_items, len([m for m in menu_items if m["restaurant_id"] == rid]))
            )
            for item in chosen_items:
                created_at = order_placed_at + timedelta(minutes=random.randint(0, 2))
                cook_shift_id = day_shifts["cooks"].get(item["station"], random.choice(list(day_shifts["cooks"].values())))
                started_at = created_at + timedelta(minutes=random.randint(1, 5))

                expected_prep = item["base_prep_time_min"]
                actual_prep = expected_prep * random.uniform(0.9, 1.15)  # normal variance

                # KITCHEN ANOMALY: grill station, dinner rush, from day 25 onward, worsening
                special_instruction = random.random() < 0.15
                if (item["station"] == "grill" and hour in DINNER_RUSH_HOURS
                        and d >= SLOWDOWN_START_DAY):
                    severity_factor = min(1.0, (d - SLOWDOWN_START_DAY) / 30)  # ramps 0->1 over 30 days
                    actual_prep = expected_prep * (1.15 + 0.9 * severity_factor)  # up to ~2x by day 55+
                    if special_instruction:
                        actual_prep *= 1.1  # slight extra hit for special instructions

                completed_at = started_at + timedelta(minutes=actual_prep)

                kitchen_tickets.append({
                    "ticket_id": ticket_id,
                    "restaurant_id": rid,
                    "order_id": order_id,
                    "menu_item_id": item["menu_item_id"],
                    "station": item["station"],
                    "special_instruction": special_instruction,
                    "created_at": created_at.isoformat(),
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "expected_prep_time_min": round(expected_prep, 1),
                    "actual_prep_time_min": round(actual_prep, 1),
                    "shift_id": cook_shift_id,
                })
                ticket_id += 1

            order_id += 1

# ==========================================================
# 6. Inventory items, usage log, supplier orders
# ==========================================================
INVENTORY_TEMPLATE = [
    # name, unit, starting_stock, reorder_threshold, base_daily_usage
    ("Chicken (kg)", "kg", 80, 20, 12),
    ("Buff meat (kg)", "kg", 60, 15, 8),
    ("Flour (kg)", "kg", 100, 25, 10),
    ("Cooking Oil (L)", "L", 50, 12, 5),
    ("Paneer (kg)", "kg", 30, 8, 4),
    ("Tomato (kg)", "kg", 40, 10, 6),
    ("Cold Drink Bottles", "unit", 200, 50, 25),
]

STOCKOUT_ITEM_NAME = "Chicken (kg)"  # this item will show the stockout risk pattern

inventory_items = []
inv_item_id = 1
inventory_by_restaurant = {}
for r in restaurants:
    ids = {}
    for name, unit, stock, threshold, _ in INVENTORY_TEMPLATE:
        inventory_items.append({
            "inventory_item_id": inv_item_id,
            "restaurant_id": r["restaurant_id"],
            "name": name,
            "unit": unit,
            "current_stock": stock,
            "reorder_threshold": threshold,
        })
        ids[name] = inv_item_id
        inv_item_id += 1
    inventory_by_restaurant[r["restaurant_id"]] = ids

inventory_usage_log = []
log_id = 1
supplier_orders = []
supplier_order_id = 1

for r in restaurants:
    rid = r["restaurant_id"]
    for name, unit, stock, threshold, base_usage in INVENTORY_TEMPLATE:
        item_id = inventory_by_restaurant[rid][name]
        running_stock = stock
        for d in range(NUM_DAYS):
            cur_date = START_DATE + timedelta(days=d)

            # STOCKOUT ANOMALY: for the trigger item, usage velocity climbs
            # over the last 20 days (e.g. growing popularity / promo)
            usage = base_usage * random.uniform(0.85, 1.15)
            if name == STOCKOUT_ITEM_NAME and d >= 40:
                growth_factor = 1 + ((d - 40) / 20) * 0.8  # up to +80% usage by day 60
                usage *= growth_factor

            usage = round(usage, 1)
            running_stock -= usage
            inventory_usage_log.append({
                "log_id": log_id,
                "inventory_item_id": item_id,
                "date": cur_date.isoformat(),
                "quantity_used": usage,
            })
            log_id += 1

            # supplier reorders roughly every 7-10 days, or when stock is low
            if d % random.randint(7, 10) == 0:
                ordered_at = cur_date
                expected_delivery = ordered_at + timedelta(days=2)

                # STOCKOUT ANOMALY: for trigger item, supplier delivery variance
                # grows in the same late window, compounding the risk
                delay_days = 0
                if name == STOCKOUT_ITEM_NAME and d >= 40:
                    delay_days = random.choice([0, 1, 1, 2, 3])
                else:
                    delay_days = random.choice([0, 0, 0, 1])

                actual_delivery = expected_delivery + timedelta(days=delay_days)
                # only mark as delivered if the date has passed within our window
                actual_delivery_str = actual_delivery.isoformat() if (d + 2 + delay_days) < NUM_DAYS else ""

                restock_amount = base_usage * random.randint(8, 12)
                running_stock += restock_amount  # approximate restock effect

                supplier_orders.append({
                    "supplier_order_id": supplier_order_id,
                    "inventory_item_id": item_id,
                    "ordered_at": ordered_at.isoformat(),
                    "expected_delivery_date": expected_delivery.isoformat(),
                    "actual_delivery_date": actual_delivery_str,
                })
                supplier_order_id += 1

        # update final current_stock to reflect the running total (bounded, not below 0)
        for inv in inventory_items:
            if inv["inventory_item_id"] == item_id:
                inv["current_stock"] = round(max(running_stock, 0), 1)

# ==========================================================
# Write all CSVs
# ==========================================================
def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {path}")

write_csv("restaurants.csv", restaurants, ["restaurant_id", "name", "brand_group", "location"])
write_csv("menu_items.csv", menu_items, ["menu_item_id", "restaurant_id", "name", "category", "station", "base_prep_time_min", "price", "active_since"])
write_csv("staff_shifts.csv", staff_shifts, ["shift_id", "restaurant_id", "staff_name", "role", "station", "shift_start", "shift_end"])
write_csv("tables.csv", tables, ["table_id", "restaurant_id", "capacity"])
write_csv("orders.csv", orders, ["order_id", "restaurant_id", "table_id", "server_id", "seated_at", "order_placed_at", "payment_completed_at", "party_size"])
write_csv("kitchen_tickets.csv", kitchen_tickets, ["ticket_id", "restaurant_id", "order_id", "menu_item_id", "station", "special_instruction", "created_at", "started_at", "completed_at", "expected_prep_time_min", "actual_prep_time_min", "shift_id"])
write_csv("inventory_items.csv", inventory_items, ["inventory_item_id", "restaurant_id", "name", "unit", "current_stock", "reorder_threshold"])
write_csv("inventory_usage_log.csv", inventory_usage_log, ["log_id", "inventory_item_id", "date", "quantity_used"])
write_csv("supplier_orders.csv", supplier_orders, ["supplier_order_id", "inventory_item_id", "ordered_at", "expected_delivery_date", "actual_delivery_date"])

print("\nDone. Anomaly patterns baked in:")
print(f" - Kitchen: grill station slowdown during dinner rush ({DINNER_RUSH_HOURS}h), ramping from day {SLOWDOWN_START_DAY}")
print(f" - Serving: turnover degrades on orders including '{TURNOVER_TRIGGER_ITEM_NAME}' after its active_since change (day 30)")
print(f" - Stock: '{STOCKOUT_ITEM_NAME}' usage velocity + supplier delay both climb from day 40")