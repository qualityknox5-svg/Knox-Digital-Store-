import logging
import random
import string
import html
import requests
import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= CONFIG =================
BOT_TOKEN = "8867196258:AAGnNRaN-WH3r0MtOmIQ7DAJ-_hqrSYindo"
ADMIN_ID = 8263739354
GROQ_API_KEY = "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"

# ================= IMAGE URLs =================
WELCOME_IMAGE    = "https://iili.io/CnwXYb9.md.png"
ORDER_CONFIRM_IMAGE = "https://iili.io/Cn6QeBj.md.png"
ORDER_PENDING_IMAGE = "https://iili.io/Cn68MG9.md.png"

# ================= NEW FEATURE SETTINGS =================
# Loyalty Points: customers earn points on every completed order, redeemable
# back into wallet balance at POINT_VALUE_KS each.
POINTS_PER_1000KS = 1
POINT_VALUE_KS = 10
MIN_POINTS_TO_REDEEM = 50

# Referral Program: bonus paid to the referrer once their invitee's FIRST
# order is confirmed (kept separate from ordinary wallet cashback).
REFERRAL_BONUS = 1000

# Auto-Delivery: when stock (added via /addstock) drops to this level or
# below after a delivery, the admin gets a low-stock warning.
LOW_STOCK_THRESHOLD = 3

PAYMENT_INFO = (
    "╔══════════════════╗\n"
    "      <b>💰 ငွေလွှဲရန် အကောင့်အချက်အလက် 💰</b>\n"
    "╚══════════════════╝\n"
    "<b>🖼️ KPay / WavePay</b>\n\n"
    "👤 Name: <b>Daw Aye Nwet</b>\n\n"
    "☎️ Number: <code>09756068378</code> (Tap to copy)\n"
    "─────────────────────\n"
    "⚠️ <i>ငွေလွှဲပြီးပါက ပြေစာ(Screenshot) ပို့ပေးပါ။</i>"
)

# ================= PRODUCT CATALOG =================
CATALOG = {
    "TT": {
        "title": "📱 TikTok Boost Services",
        "type": "tiktok",
        "note": "🌟 Viewကြာချိန်: 15min to 24hours\n❤️ Like ကြာချိန်: 24hours to 3days\n👤 Follower ကြာချိန်: 24hours to 5days",
        "items": {
            "LK":  {"name": "Likes (ပြန်မကျ)",       "emoji": "❤️", "tiers": {300: 2000, 500: 2500, 1000: 5000, 5000: 23000, 10000: 47000}},
            "VWN": {"name": "Views (ပြန်မကျ)",        "emoji": "🎵", "tiers": {1000: 1000, 3000: 2500, 5000: 4500, 10000: 9000, 100000: 90000}},
            "MV":  {"name": "Monetization Views",      "emoji": "👑", "tiers": {5000: 3500, 10000: 7000}},
            "FL":  {"name": "Followers (အကျနည်း)",    "emoji": "👥", "tiers": {100: 5000, 300: 14000, 500: 24000, 1000: 48000}},
            "FV":  {"name": "Favourites (ပြန်မကျ)",   "emoji": "💗", "tiers": {500: 500, 1000: 1000, 10000: 10000}},
            "SH":  {"name": "Shares (ပြန်မကျ)",       "emoji": "📤", "tiers": {500: 1000, 1000: 2000, 10000: 15000}},
            "JP":  {"name": "Japan Region ACC",        "emoji": "🇯🇵", "tiers": {1: 8000}},
            "PM":  {"name": "Tiktok Promote",           "emoji": "📹", "tiers": {1: 8000}, "custom": True},
        }
    },
    "PUBG": {
        "title": "🎮 PUBG UC & PASS",
        "type": "fixed",
        "note": "🔣 <b>ID & IN GAME NAME</b> ပေးရန် လိုအပ်ပါသည်\n⏳ <b>ကြာချိန် - 30 Min</b>",
        "ask_label": "🆔 PUBG <b>ID</b> နှင့် <b>IN GAME NAME</b> ကို ပို့ပေးပါခင်ဗျာ",
        "groups": {
            "UC": {
                "title": "🔥 UC ပက်ကေ့ဂျ်များ",
                "items": {
                    "UC60":   {"name": "🔥 60 UC",   "price": 5000},
                    "UC325":  {"name": "🔥 325 UC",  "price": 24000},
                    "UC660":  {"name": "🔥 660 UC",  "price": 42000},
                    "UC1800": {"name": "🔥 1800 UC", "price": 120000},
                    "UC3850": {"name": "🔥 3850 UC", "price": 220000},
                    "UC8100": {"name": "🔥 8100 UC", "price": 400000},
                }
            },
            "PK": {
                "title": "💰 Special Packs",
                "items": {
                    "MYTHIC":  {"name": "🌟 Mythic Emblem Pack",   "price": 23000},
                    "MATRL":   {"name": "🌟 Material Pack",        "price": 14000},
                    "FIRSTBY": {"name": "💵 First Purchase Pack",  "price": 5500},
                }
            },
            "PP": {
                "title": "🎮 Prime Pass",
                "items": {
                    "PP1":  {"name": "Prime Pass - 1 Month",  "price": 6000},
                    "PP3":  {"name": "Prime Pass - 3 Months", "price": 15000},
                    "PP6":  {"name": "Prime Pass - 6 Months", "price": 27000},
                    "PP12": {"name": "Prime Pass - 1 Year",   "price": 53000},
                }
            },
            "PPP": {
                "title": "🎮 Prime Plus Pass",
                "items": {
                    "PPP1":  {"name": "Prime Plus Pass - 1 Month",  "price": 50000},
                    "PPP3":  {"name": "Prime Plus Pass - 3 Months", "price": 165000},
                    "PPP6":  {"name": "Prime Plus Pass - 6 Months", "price": 312000},
                    "PPP12": {"name": "Prime Plus Pass - 1 Year",   "price": 624000},
                }
            },
        }
    },
    "MLBB": {
        "title": "💎 Mlbb Diamond",
        "type": "fixed",
        "note": "🔣 Game <b>ID</b> နှင့် <b>Server ID</b> ပေးရန် လိုအပ်ပါသည်",
        "ask_label": "🆔 MLBB <b>Game ID (Server ID)</b> ကို ပို့ပေးပါခင်ဗျာ\nဥပမာ - <code>123456789 (1234)</code>",
        "groups": {
            "DM": {
                "title": "💎 Diamond ဈေးများ",
                "items": {
                    "WP":    {"name": "💎 Weekly Pass",  "price": 6800},
                    "D86":   {"name": "💎 86",           "price": 5600},
                    "D172":  {"name": "💎 172",          "price": 12000},
                    "D257":  {"name": "💎 257",          "price": 16500},
                    "D343":  {"name": "💎 343",          "price": 22000},
                    "D429":  {"name": "💎 429",          "price": 28500},
                    "D600":  {"name": "💎 600",          "price": 37500},
                    "D706":  {"name": "💎 706",          "price": 39900},
                    "D878":  {"name": "💎 878",          "price": 48500},
                    "D1050": {"name": "💎 1050",         "price": 59100},
                    "D1135": {"name": "💎 1135",         "price": 65900},
                    "D2195": {"name": "💎 2195",         "price": 128000},
                    "D3688": {"name": "💎 3688",         "price": 189000},
                    "D5532": {"name": "💎 5532",         "price": 296000},
                    "D9288": {"name": "💎 9288",         "price": 479000},
                }
            },
            "DD": {
                "title": "💎💎 Double Diamond ဈေးများ",
                "items": {
                    "DD50":  {"name": "💎 (50+50)",   "price": 4000},
                    "DD150": {"name": "💎 (150+150)", "price": 11500},
                    "DD250": {"name": "💎 (250+250)", "price": 17500},
                    "DD500": {"name": "💎 (500+500)", "price": 34000},
                }
            },
        }
    },
    "APPS": {
        "title": "📱 Apps (CapCut / Canva)",
        "type": "fixed",
        "note": "",
        "ask_label": "📧 လိုအပ်သော <b>Email / Account Info</b> ကို ပို့ပေးပါခင်ဗျာ",
        "items": {
            "CAPCUT1M": {"name": "Capcut Pro - 1 Month (Private)",                "price": 20000},
            "CANVA1Y":  {"name": "Canva Pro (Edu) - 1 Year (Myanmar Font✅ Fast⚡️)", "price": 8000},
            "ALM9DEV":  {"name": "Alight Motion Private - 1Year (9Dev)",           "price": 10000},
            "ALM1DEV":  {"name": "Alight Motion Private - 1Year (1Dev)",           "price": 5000},
            "WINKSHARE":   {"name": "Wink Premium - 1Month (Share)",               "price": 10000},
            "WINKPRIVATE": {"name": "Wink Premium - 1Month (Private)",             "price": 20000},
        }
    },
    "VPN": {
        "title": "🛡️ VPN Services",
        "type": "fixed",
        "note": (
            "⏳ ငွေလွှဲပြီးပါက Admin မှ Login Info ပို့ပေးပါမည်။\n"
            "📌 Device အရေအတွက်ကို သတိပြုပြီး ရွေးချယ်ပါ။"
        ),
        "ask_label": "📧 လိုအပ်သော <b>Email</b> ရှိပါက ပို့ပေးပါ (မရှိပါက <code>None</code> ဟု ရိုက်ပါ)",
        "items": {
            "EVPN1DEV":  {"name": "Express Vpn (25-30Days) - 1Dev",           "price": 4000},
            "EVPN2DEV":  {"name": "Express Vpn (25-30Days) - 2Dev (PC)",      "price": 4500},
            "EVPN8DEV":  {"name": "Express Vpn (25-30Days) - 8Dev (Private)", "price": 12000},
            "OVPN1DEV":  {"name": "Outline Vpn - 1Dev",                          "price": 6000},
            "OVPNUNLIM": {"name": "Outline Vpn - Unlimited Dev",                 "price": 20000},
            "OVPNEU":    {"name": "Outline Vpn - Poland/Germany/France (Unlimited)", "price": 20000},
            "NORDVPN1Y": {"name": "Nord Vpn 1Year (Private)",                    "price": 25000},
        }
    },
    "SUB": {
        "title": "🎬 Streaming & Subscription",
        "type": "fixed",
        "note": (
            "⏳ ငွေလွှဲပြီးပါက Admin မှ Login Info ချက်ချင်း ပို့ပေးပါမည်။\n"
            "📌 Warranty ကာလအတွင်း ပြဿနာရှိပါက Admin ကို ဆက်သွယ်ပါ။"
        ),
        "ask_label": "📧 လိုအပ်သော <b>Email</b> ရှိပါက ပို့ပေးပါ (မရှိပါက <code>None</code> ဟု ရိုက်ပါ)",
        "items": {
            "DISCORD1M":  {"name": "Discord Nitro - 1Month",                      "price": 15800},
            "YT1M":       {"name": "Youtube Private - 1Month (25Days Warranty📌)", "price": 15000},
            "NFSHARE":    {"name": "Netflix Ultra 4K - Share (1Dev)",              "price": 1300},
            "NFPROFILE":  {"name": "Netflix Ultra 4K - 1Profile (2Dev)",           "price": 20000},
            "NF5PROFILE": {"name": "Netflix Ultra 4K - 5Profile (Head)",           "price": 63000},
            "SPOTIFY3M":  {"name": "Spotify (Private/Family/US) - 3Month",         "price": 18000},
            "SPOTIFY6M":  {"name": "Spotify (Private/Family/US) - 6Month",         "price": 30000},
            "SPOTIFY1Y":  {"name": "Spotify (Private/Family/US) - 1Year",          "price": 55000},
        }
    },
    "TG": {
        "title": "⭐ Telegram Premium & Accounts",
        "type": "fixed",
        "note": (
            "🔣 <b>Login</b> ဝယ်ယူပါက Phone Number + Login Code လိုအပ်ပါသည်။\n"
            "🔣 <b>Gift Plan</b> အတွက် Telegram <b>Username</b> သာ လိုအပ်ပါသည်။\n"
            "🔣 <b>Gift Link</b> ကို Link နှိပ်ပြီး အသုံးပြုလို့ရပါသည်။"
        ),
        "ask_label": "👤 လိုအပ်သော <b>Username / Phone Number / Link</b> ကို ပို့ပေးပါခင်ဗျာ",
        "items": {
            "TGP1M":    {"name": "⭐ Telegram Premium 1 Month (Login)", "price": 23000},
            "TGSMS":    {"name": "📩 SMS Fee",                          "price": 10000},
            "TGGIFT3":  {"name": "🎁 Gift Plan - 3 Months (Username)",  "price": 56000},
            "TGGIFT6":  {"name": "🎁 Gift Plan - 6 Months (Username)",  "price": 74500},
            "TGGIFT12": {"name": "🎁 Gift Plan - 12 Months (Username)", "price": 128000},
            "TGLINK3":  {"name": "🎁 Gift Link - 3 Months",             "price": 53000},
            "TGLINK6":  {"name": "🎁 Gift Link - 6 Months",             "price": 70000},
            "TGLINK12": {"name": "🎁 Gift Link - 12 Months",            "price": 130000},
            "TGACC":    {"name": "✨ Telegram Account (+95)",           "price": 2000},
        }
    },
}

# Derived helper tables
PRICE_TABLE = {item["name"]: item["tiers"] for item in CATALOG["TT"]["items"].values()}
SVC_SHORT = {item["name"]: code for code, item in CATALOG["TT"]["items"].items()}
SVC_LONG  = {code: item["name"] for code, item in CATALOG["TT"]["items"].items()}

STATUS_EMOJI = {
    "pending": "⏳ Pending (စစ်ဆေးဆဲ)",
    "processing": "⚙️ Processing (လုပ်ဆောင်နေဆဲ)",
    "order uploaded": "✅ Order uploaded (အောင်မြင်သည်)",
    "rejected": "❌ Rejected (ငြင်းပယ်ခံရသည်)"
}

# ================= SQLITE DATABASE FOR STABILITY =================
DB_FILE = "knox_store.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Wallets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    # Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            user_name TEXT,
            description TEXT,
            total INTEGER,
            status TEXT,
            created_at TEXT,
            note TEXT DEFAULT ''
        )
    """)
    # Migration: add 'note' column if the table already existed without it
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN note TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Users Table (Persistent storage for broadcast so data never lost on restart)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT,
            joined_at TEXT,
            banned INTEGER DEFAULT 0
        )
    """)
    # Migration: add 'banned' column if the table already existed without it
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: add 'username' column (Telegram @handle, separate from full_name)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: loyalty points balance
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: this user's own referral code
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN ref_code TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Migration: who referred this user (user_id of the referrer, if any)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Stock (for auto-delivery of digital codes/accounts, e.g. VPN / Apps)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_key TEXT,
            content TEXT,
            delivered INTEGER DEFAULT 0,
            delivered_to INTEGER,
            delivered_at TEXT,
            added_at TEXT
        )
    """)
    # Promo codes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            kind TEXT,
            value INTEGER,
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0,
            expiry TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    # Referral earnings log (for the "🎁 Referral" stats page)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            bonus INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize Database on boot
init_db()

# Database Helper Functions
def add_user(user_id: int, user_name: str, username: str = None):
    """Registers a user, or refreshes their name/@handle if they already exist
    (so /users and /find always show the current name, not just the first-ever one)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (user_id, user_name, username, joined_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET user_name = excluded.user_name, username = excluded.username",
        (user_id, user_name, username, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def get_all_users() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_user_display_name(user_id: int) -> str:
    """Returns '@handle' if the user has a Telegram username, otherwise their full name, otherwise the ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return str(user_id)
    user_name, username = row
    if username:
        return f"@{username}"
    return user_name or str(user_id)

def _user_registered(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_total_users_count() -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(user_id) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ================= BAN SYSTEM =================
def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_banned_users() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, user_name FROM users WHERE banned = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_users_with_balance() -> list:
    """Returns (user_id, user_name, username, balance, banned) for every registered
    user — not just ones that happen to have a wallet row. Fixes /users only showing
    people who had touched their wallet before."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.user_name, u.username, COALESCE(w.balance, 0), u.banned
        FROM users u
        LEFT JOIN wallets w ON u.user_id = w.user_id
        ORDER BY COALESCE(w.balance, 0) DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ================= WALLET CASHBACK ON PURCHASE =================
# Tiered cashback: the more a single order costs, the more bonus goes back
# into the buyer's wallet. Edit these tiers any time — sorted high to low,
# first matching threshold wins.
CASHBACK_TIERS = [
    (100000, 10000),
    (50000, 2500),
    (20000, 1000),
    (10000, 500),
]

def calculate_cashback(total: int) -> int:
    for threshold, bonus in CASHBACK_TIERS:
        if total >= threshold:
            return bonus
    return 0

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE wallets SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id: int, amount: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    bal = cursor.fetchone()[0]
    if bal >= amount:
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_order_by_id(order_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, user_name, description, total, status, created_at, note FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "user_name": row[1],
            "description": row[2],
            "total": row[3],
            "status": row[4],
            "created_at": row[5],
            "note": row[6] if len(row) > 6 and row[6] else ""
        }
    return None

def create_order(user_id: int, user_name: str, description: str, total: int, note: str = "") -> str:
    order_id = generate_order_id()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (order_id, user_id, user_name, description, total, status, created_at, note) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
        (order_id, user_id, user_name, description, total, datetime.now().strftime("%Y-%m-%d %H:%M"), note)
    )
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id: str, status: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

def get_user_orders(user_id: int) -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, description, total, status, created_at, note FROM orders WHERE user_id = ? ORDER BY rowid DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        (row[0], {
            "description": row[1],
            "total": row[2],
            "status": row[3],
            "created_at": row[4],
            "note": row[5] if len(row) > 5 and row[5] else ""
        }) for row in rows
    ]

def get_pending_orders(limit: int = 15) -> list:
    """Returns most recent pending orders for the admin quick-view."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, user_id, user_name, description, total, created_at, note "
        "FROM orders WHERE status = 'pending' ORDER BY rowid DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "order_id": r[0], "user_id": r[1], "user_name": r[2],
            "description": r[3], "total": r[4], "created_at": r[5],
            "note": r[6] if len(r) > 6 and r[6] else ""
        } for r in rows
    ]

def get_vip_status(user_id: int):
    """Returns (badge_text, total_spent) based on lifetime completed-order spend."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total) FROM orders WHERE user_id = ? AND status = 'completed'", (user_id,))
    row = cursor.fetchone()
    conn.close()
    spent = row[0] if row and row[0] else 0
    if spent >= 400000:
        badge = "💎 VIP Diamond Member"
    elif spent >= 150000:
        badge = "🥇 Gold Member"
    elif spent >= 50000:
        badge = "🥈 Silver Member"
    elif spent > 0:
        badge = "🥉 Bronze Member"
    else:
        badge = "🆕 New Member"
    return badge, spent

def count_confirmed_orders(user_id: int) -> int:
    """Orders that had payment accepted (completed by admin, or instant wallet pay)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ? AND status IN ('completed', 'processing')",
        (user_id,)
    )
    n = cursor.fetchone()[0]
    conn.close()
    return n

# ================= LOYALTY POINTS =================
def get_points(user_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0

def add_points(user_id: int, pts: int):
    if pts <= 0:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = COALESCE(points, 0) + ? WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()

def award_points_for_order(user_id: int, total: int) -> int:
    """Awards loyalty points for a confirmed order total. Returns points earned."""
    pts = (total // 1000) * POINTS_PER_1000KS
    if pts > 0:
        add_points(user_id, pts)
    return pts

def redeem_points_to_wallet(user_id: int, pts: int) -> bool:
    """Converts `pts` loyalty points into wallet balance at POINT_VALUE_KS each."""
    if pts <= 0:
        return False
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    have = row[0] if row and row[0] else 0
    if have < pts:
        conn.close()
        return False
    cursor.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()
    add_balance(user_id, pts * POINT_VALUE_KS)
    return True

# ================= REFERRAL PROGRAM =================
def _generate_ref_code() -> str:
    return "KX" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def get_or_create_ref_code(user_id: int) -> str:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT ref_code FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0]:
        conn.close()
        return row[0]
    while True:
        code = _generate_ref_code()
        cursor.execute("SELECT 1 FROM users WHERE ref_code = ?", (code,))
        if not cursor.fetchone():
            break
    cursor.execute("UPDATE users SET ref_code = ? WHERE user_id = ?", (code, user_id))
    conn.commit()
    conn.close()
    return code

def get_user_id_by_ref_code(code: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE ref_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_referred_by(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def set_referred_by(user_id: int, referrer_id: int):
    """Only sets it the first time — never overwrites, and never allows self-referral."""
    if user_id == referrer_id:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] is None:
        cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referrer_id, user_id))
        conn.commit()
    conn.close()

def count_referrals(referrer_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (referrer_id,))
    n = cursor.fetchone()[0]
    conn.close()
    return n

def get_referral_earnings(referrer_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(bonus), 0) FROM referral_log WHERE referrer_id = ?", (referrer_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0

def log_referral_bonus(referrer_id: int, referred_id: int, bonus: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO referral_log (referrer_id, referred_id, bonus, created_at) VALUES (?, ?, ?, ?)",
        (referrer_id, referred_id, bonus, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

async def maybe_award_referral_bonus(context, user_id: int):
    """Call right after a user's order becomes confirmed. If this was their
    FIRST confirmed order and they were referred, pays the referrer and
    notifies them."""
    if count_confirmed_orders(user_id) != 1:
        return
    referrer_id = get_referred_by(user_id)
    if not referrer_id:
        return
    add_balance(referrer_id, REFERRAL_BONUS)
    log_referral_bonus(referrer_id, user_id, REFERRAL_BONUS)
    try:
        buyer_name = get_user_display_name(user_id)
        await context.bot.send_message(
            chat_id=referrer_id,
            text=(
                f"🎁 <b>Referral Bonus ရရှိပါပြီ!</b>\n\n"
                f"👤 သင် ဖိတ်ခေါ်ထားသော <b>{html.escape(str(buyer_name))}</b> က ပထမဆုံး Order အောင်မြင်သွားပါပြီ။\n"
                f"💰 Bonus: <b>+{REFERRAL_BONUS:,} ks</b> — Wallet ထဲသို့ ထည့်ပေးလိုက်ပါပြီ။\n\n"
                f"🛍️ ကျေးဇူးတင်ပါတယ်! ပိုမိုဖိတ်ခေါ်ရန် /start → 🎁 Referral ကိုနှိပ်ပါ"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

# ================= STOCK & AUTO-DELIVERY =================
def stock_item_key(cat_code: str, grp_code: str, item_code: str) -> str:
    return f"{cat_code}:{grp_code}:{item_code}"

def add_stock(item_key: str, lines: list) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.executemany(
        "INSERT INTO stock (item_key, content, delivered, added_at) VALUES (?, ?, 0, ?)",
        [(item_key, line, now) for line in lines if line.strip()]
    )
    conn.commit()
    added = cursor.rowcount if cursor.rowcount and cursor.rowcount > 0 else len(lines)
    conn.close()
    return added

def get_stock_count(item_key: str) -> int:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock WHERE item_key = ? AND delivered = 0", (item_key,))
    n = cursor.fetchone()[0]
    conn.close()
    return n

def take_stock(item_key: str):
    """Atomically claims one undelivered stock line for this item, or None if empty."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM stock WHERE item_key = ? AND delivered = 0 ORDER BY id LIMIT 1", (item_key,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    stock_id, content = row
    cursor.execute("UPDATE stock SET delivered = 1, delivered_at = ? WHERE id = ?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), stock_id))
    conn.commit()
    conn.close()
    return content

def list_stock_summary() -> list:
    """Returns [(item_key, remaining_count)] for every item_key that has ever had stock added."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_key, SUM(CASE WHEN delivered = 0 THEN 1 ELSE 0 END) as remaining
        FROM stock GROUP BY item_key ORDER BY item_key
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

async def try_auto_deliver(context, target_user_id: int, cat_code: str, grp_code: str, item_code: str) -> bool:
    """If stock exists for this exact item, sends it straight to the buyer and
    warns the admin if stock is now running low. Returns True if delivered."""
    item_key = stock_item_key(cat_code, grp_code, item_code)
    content = take_stock(item_key)
    if not content:
        return False
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "🎁 <b>Auto-Delivery — အကောင့်အချက်အလက်</b>\n\n"
                f"<code>{html.escape(content)}</code>\n\n"
                "⚠️ <i>ဒီအချက်အလက်ကို မျှဝေခြင်း မပြုလုပ်ပါနှင့်။</i>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass
    remaining = get_stock_count(item_key)
    if remaining <= LOW_STOCK_THRESHOLD:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ <b>Stock Low:</b> <code>{item_key}</code> — {remaining} ခု ကျန်ပါတော့သည်။ /addstock ဖြင့် ဖြည့်ပေးပါ။",
                parse_mode="HTML"
            )
        except Exception:
            pass
    return True

# ================= PROMO CODES =================
def create_promo(code: str, kind: str, value: int, max_uses: int, expiry: str) -> bool:
    code = code.strip().upper()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO promo_codes (code, kind, value, max_uses, used_count, expiry, active, created_at) "
            "VALUES (?, ?, ?, ?, 0, ?, 1, ?)",
            (code, kind, value, max_uses, expiry, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok

def get_promo(code: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT code, kind, value, max_uses, used_count, expiry, active FROM promo_codes WHERE code = ?", (code.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"code": row[0], "kind": row[1], "value": row[2], "max_uses": row[3],
            "used_count": row[4], "expiry": row[5], "active": row[6]}

def validate_promo(code: str):
    """Returns (promo_dict, None) if usable, or (None, error_message) if not."""
    promo = get_promo(code)
    if not promo:
        return None, "❌ ဒီ Promo Code မတွေ့ပါ။"
    if not promo["active"]:
        return None, "❌ ဒီ Promo Code ကို ပိတ်ထားပါသည်။"
    if promo["expiry"] and promo["expiry"].lower() != "none":
        try:
            if datetime.now() > datetime.strptime(promo["expiry"], "%Y-%m-%d"):
                return None, "❌ ဒီ Promo Code သက်တမ်းကုန်သွားပါပြီ။"
        except ValueError:
            pass
    if promo["max_uses"] and promo["used_count"] >= promo["max_uses"]:
        return None, "❌ ဒီ Promo Code ကို အသုံးပြုနိုင်သည့် အရေအတွက် ပြည့်သွားပါပြီ။"
    return promo, None

def compute_discount(promo: dict, total: int) -> int:
    if promo["kind"] == "percent":
        discount = (total * promo["value"]) // 100
    else:
        discount = promo["value"]
    return max(0, min(discount, total - 1))  # never discount to 0 or below

def consume_promo(code: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?", (code.strip().upper(),))
    conn.commit()
    conn.close()

def delete_promo(code: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM promo_codes WHERE code = ?", (code.strip().upper(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def list_promos() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT code, kind, value, max_uses, used_count, expiry, active FROM promo_codes ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ================= ORDER ID GENERATOR =================
def generate_order_id() -> str:
    while True:
        suffix = ''.join(random.choices(string.digits, k=4))
        order_id = f"KNOX-{suffix}"
        if not get_order_by_id(order_id):
            return order_id

# ================= AI ASSISTANT (Human-like Natural Persona) =================
def build_catalog_ai_context() -> str:
    """Builds a compact, accurate price list from the live CATALOG so the AI
    never has to guess/hallucinate prices — this is the #1 cause of wrong AI answers."""
    lines = []
    for cat_code, cat in CATALOG.items():
        lines.append(f"[{cat['title']}]")
        if cat_code == "TT":
            for item in cat["items"].values():
                tier_txt = ", ".join(f"{qty}={price:,}ks" for qty, price in item["tiers"].items())
                lines.append(f"  {item['name']}: {tier_txt}")
        elif "groups" in cat:
            for grp in cat["groups"].values():
                for item in grp["items"].values():
                    lines.append(f"  {item['name']} = {item['price']:,}ks")
        else:
            for item in cat["items"].values():
                lines.append(f"  {item['name']} = {item['price']:,}ks")
        if cat.get("note"):
            note_plain = cat["note"].replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
            lines.append(f"  မှတ်ချက်: {note_plain}")
    return "\n".join(lines)

def ask_ai(user_text, conversation_history=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    catalog_context = build_catalog_ai_context()
    system_prompt = (
        "သင်သည် Knox Digital Store ၏ Customer Support 'Knox' ဖြစ်ပါတယ်။ "
        "မြန်မာလူငယ်တစ်ယောက်လို သဘာဝကျကျ၊ ရင်းနှီးစွာ ဖြေပါ (ဥပမာ - 'ဟုတ်ကဲ့ ကိုကြီး/ညီမလေး', 'အေးဆေးပဲနော်')။\n\n"
        "🚫 အရေးကြီးဆုံး စည်းကမ်းများ:\n"
        "1) အမြဲတမ်း **အတိုချုပ်** ဖြေပါ — 1 to 3 sentences ထက် မပိုစေရ။ စာရင်း/ရှင်းလင်းချက်ရှည်ရှည် မရေးရ။\n"
        "2) ဈေးနှုန်း မေးရင် အောက်ပါ 'တကယ့် ဈေးနှုန်းစာရင်း' ထဲကသာ တိကျစွာ ဖြေပါ။ စာရင်းထဲမရှိတဲ့ ပစ္စည်း/ဈေးကို လုံးဝ လက်ဖြင့် တွက်ဖန်တီး/မှန်းဆ မဖြေရ။ "
        "စာရင်းထဲ မတွေ့ရင် 'ဒီဟာလေးတော့ Admin ကို တိုက်ရိုက်မေးပေးဖို့ လိုမယ်နော် (@just_knox)' ဟု ရိုးရိုးရှင်းရှင်း ဖြေပါ။\n"
        "3) ဆိုင်နဲ့ မသက်ဆိုင်တဲ့ မေးခွန်း (ဥပမာ - နိုင်ငံရေး၊ ဆေးပညာ၊ ကုဒ်ရေးခိုင်းခြင်း စသည်) ဆိုရင် 'ဒါကတော့ ကျွန်တော့် အလုပ်နဲ့ မဆိုင်ဘူးနော်၊ ဆိုင်နဲ့ပတ်သက်တာပဲ ကူညီပေးနိုင်ပါတယ်' ဟု ယဉ်ကျေးစွာ ငြင်းပါ။\n"
        "4) မသေချာတာ/ရှုပ်ထွေးတာဆိုရင် ခန့်မှန်း/စိတ်ကူးဖန်တီးမနေဘဲ Admin ဆီ လွှဲပေးပါ (@just_knox)။\n"
        "5) /start ကိုနှိပ်ပြီး Menu ကနေ ဝယ်ယူနိုင်ကြောင်း လိုအပ်မှသာ တိုတိုပြောပါ။\n\n"
        f"📋 တကယ့် ဈေးနှုန်းစာရင်း (ဒီထဲကသာ ကိုးကားပါ):\n{catalog_context}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_text})

    # llama-3.3-70b-versatile / llama-3.1-8b-instant are deprecated on Groq
    # (shutting down 08/16/26) — gpt-oss-120b is the recommended replacement and
    # follows the strict Burmese-only / catalog-only instructions more reliably.
    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 250,
            "temperature": 0.3
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            else:
                logging.warning(f"Groq API Error ({model_name}): {response.status_code} - {response.text}")
        except Exception as e:
            logging.warning(f"Failed using model {model_name}: {e}")
            continue

    return fallback_reply()

def fallback_reply():
    return (
        "👋 ဟယ်လို ကိုကြီး/ညီမလေးရေ! 𝗞𝗻𝗼𝘅 𝗗𝗶𝗴𝗶𝘁𝗮𝗹 𝗦𝘁𝗼𝗿𝗲 Botမှ ကြိုဆိုပါတယ်။ "
        "ဝန်ဆောင်မှုတွေ ဝယ်ချင်ရင် /start လေးကို နှိပ်ပြီး Menu ထဲကနေ အေးဆေး ရွေးချယ်နိုင်ပါတယ်ခင်ဗျာ။"
    )

# ================= MENU BUILDERS =================
def build_main_buy_menu():
    kb = []
    for code, cat in CATALOG.items():
        kb.append([InlineKeyboardButton(cat["title"], callback_data=f"cat_{code}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="start")])
    return InlineKeyboardMarkup(kb)

def build_tt_multiselect_menu(selected_items: dict):
    kb = []
    total = 0
    for code, item in CATALOG["TT"]["items"].items():
        emoji = item["emoji"]
        name = item["name"]
        if code in selected_items:
            qty = selected_items[code]
            if code == "PM":
                price = qty * 8000
                label = f"✅ {emoji} {name} ({qty}$) ({price:,}ks)"
            elif code == "JP":
                price = item["tiers"].get(1, 0)
                label = f"✅ {emoji} {name} ({price:,}ks)"
            else:
                price = item["tiers"].get(qty, 0)
                label = f"✅ {emoji} {name} x{qty} ({price:,}ks)"
            total += price
        else:
            label = f"➕ {emoji} {name}"
        kb.append([InlineKeyboardButton(label, callback_data=f"ttsel_{code}")])
    if selected_items:
        kb.append([InlineKeyboardButton(
            f"🛒 ရွေးထားသည်: {len(selected_items)} မျိုး | စုစုပေါင်း: {total:,} ks",
            callback_data="tt_summary"
        )])
        kb.append([InlineKeyboardButton("✅ အတည်ပြုပြီး ဆက်သွားမည်", callback_data="tt_confirm_multi")])
        kb.append([InlineKeyboardButton("🗑️ အားလုံးဖြုတ်မည်", callback_data="tt_clear")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="buy")])
    return InlineKeyboardMarkup(kb), total

def build_tt_qty_menu(svc_code: str, selected_items: dict):
    item = CATALOG["TT"]["items"][svc_code]
    kb = []
    row = []
    if svc_code == "PM":
        for dollars in [1, 2, 3, 5, 10, 20]:
            price = dollars * 8000
            tick = "✅ " if selected_items.get(svc_code) == dollars else ""
            label = f"{tick}{dollars}$ = {price:,}ks"
            row.append(InlineKeyboardButton(label, callback_data=f"ttqty_{svc_code}_{dollars}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([InlineKeyboardButton("🔢 Custom ပမာဏ ထည့်မည်", callback_data="pm_custom_amount")])
    else:
        for qty, price in item["tiers"].items():
            if svc_code == "JP":
                qty_str = "Buy"
            else:
                qty_str = f"{qty//1000}k" if qty >= 1000 else str(qty)
            tick = "✅ " if selected_items.get(svc_code) == qty else ""
            label = f"{tick}{qty_str} = {price:,}ks"
            row.append(InlineKeyboardButton(label, callback_data=f"ttqty_{svc_code}_{qty}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
    if svc_code in selected_items:
        kb.append([InlineKeyboardButton("❌ ဤ Service ဖယ်ရှားမည်", callback_data=f"ttremove_{svc_code}")])
    kb.append([InlineKeyboardButton("🔙 Service list သို့ပြန်", callback_data="tt_back_multi")])
    return InlineKeyboardMarkup(kb)

def build_group_menu(cat_code):
    cat = CATALOG[cat_code]
    kb = []
    for grp_code, grp in cat["groups"].items():
        kb.append([InlineKeyboardButton(grp["title"], callback_data=f"grp_{cat_code}_{grp_code}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="buy")])
    return InlineKeyboardMarkup(kb)

def build_item_buttons_rows(cat_code, grp_code, items):
    kb, row = [], []
    for code, item in items.items():
        label = f"{item['name']} - {item['price']:,}ks"
        row.append(InlineKeyboardButton(label, callback_data=f"item_{cat_code}_{grp_code}_{code}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return kb

def get_item(cat_code, grp_code, item_code):
    cat = CATALOG[cat_code]
    if grp_code != "-" and "groups" in cat:
        return cat["groups"][grp_code]["items"][item_code]
    return cat["items"][item_code]

# ================= SAFE MESSAGE EDIT HELPER =================
async def safe_edit_message(q, text: str, reply_markup=None, parse_mode="HTML"):
    """Reliably updates the message behind a callback button, whether that
    message currently has a photo+caption or is a plain text message.
    This is what makes every '🔙 Back' button actually work: mixing
    edit_message_caption() and edit_message_text() on the wrong message type
    silently fails and leaves the button unresponsive."""
    try:
        if q.message and q.message.photo:
            await q.edit_message_caption(caption=text, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            await q.edit_message_text(text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception:
        try:
            await q.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as e:
            logging.warning(f"safe_edit_message fully failed: {e}")

# ================= MLBB WEEKLY PASS CUSTOM QTY MENU (+ / -) =================
async def show_mlbb_wp_menu(q, context):
    qty = context.user_data.get("mlbb_wp_qty", 1)
    unit_price = 7000
    total_price = qty * unit_price
    
    kb = [
        [
            InlineKeyboardButton("➖ လျှော့မည် (-)", callback_data="mlbbwp_dec"),
            InlineKeyboardButton(f"📦 {qty} ခု", callback_data="mlbbwp_noop"),
            InlineKeyboardButton("➕ တိုးမည် (+)", callback_data="mlbbwp_inc"),
        ],
        [InlineKeyboardButton(f"✅ ဒီပမာဏဖြင့် ဝယ်မည် ({total_price:,} ks)", callback_data="mlbbwp_confirm")],
        [InlineKeyboardButton("🔙 Back", callback_data="cat_MLBB")]
    ]
    text = (
        "💎 <b>MLBB Weekly Pass - Custom Quantity</b>\n\n"
        f"📌 ရွေးချယ်ထားသော ပမာဏ: <b>{qty} ခု</b>\n"
        f"💵 ကျသင့်ငွေ စုစုပေါင်း: <b>{total_price:,} ks</b> (1 ခု = 7,000 ks)\n\n"
        "👇 + နှင့် - ခလုတ်များနှိပ်၍ လိုအပ်သလောက် ရွေးချယ်နိုင်ပါသည်ခင်ဗျာ။"
    )
    await safe_edit_message(q, text, reply_markup=InlineKeyboardMarkup(kb))

async def update_mlbb_wp_message(q, context):
    qty = context.user_data.get("mlbb_wp_qty", 1)
    unit_price = 7000
    total_price = qty * unit_price
    
    kb = [
        [
            InlineKeyboardButton("➖ လျှော့မည် (-)", callback_data="mlbbwp_dec"),
            InlineKeyboardButton(f"📦 {qty} ခု", callback_data="mlbbwp_noop"),
            InlineKeyboardButton("➕ တိုးမည် (+)", callback_data="mlbbwp_inc"),
        ],
        [InlineKeyboardButton(f"✅ ဒီပမာဏဖြင့် ဝယ်မည် ({total_price:,} ks)", callback_data="mlbbwp_confirm")],
        [InlineKeyboardButton("🔙 Back", callback_data="cat_MLBB")]
    ]
    text = (
        "💎 <b>MLBB Weekly Pass - Custom Quantity</b>\n\n"
        f"📌 ရွေးချယ်ထားသော ပမာဏ: <b>{qty} ခု</b>\n"
        f"💵 ကျသင့်ငွေ စုစုပေါင်း: <b>{total_price:,} ks</b> (1 ခု = 7,000 ks)\n\n"
        "👇 + နှင့် - ခလုတ်များနှိပ်၍ လိုအပ်သလောက် ရွေးချယ်နိုင်ပါသည်ခင်ဗျာ။"
    )
    await safe_edit_message(q, text, reply_markup=InlineKeyboardMarkup(kb))

def build_price_text(cat_code):
    cat = CATALOG[cat_code]
    text = f"╔═════════════════════════╗\n"
    text += f"   📋 <b>{cat['title']} ဈေးနှုန်းများ</b>\n"
    text += f"╚═════════════════════════╝\n\n"
    if cat_code == "TT":
        for code, item in cat["items"].items():
            text += f"💠 <b>{item['emoji']} {item['name']}</b>:\n"
            for qty, price in item["tiers"].items():
                if code in ["JP", "PM"]:
                    text += f"   🔹 ဈေးနှုန်း = <code>{price:,}</code> ks\n"
                else:
                    qty_str = f"{qty//1000}k" if qty >= 10000 else str(qty)
                    text += f"   🔹 {qty_str} = <code>{price:,}</code> ks\n"
            text += "\n"
    elif "groups" in cat:
        for grp in cat["groups"].values():
            text += f"📦 <b>{grp['title']}</b>\n"
            for item in grp["items"].values():
                text += f"  🔸 {item['name']} ➡️ <code>{item['price']:,}</code> ks\n"
            text += "\n"
    else:
        for item in cat["items"].values():
            text += f"🔸 {item['name']} ➡️ <code>{item['price']:,}</code> ks\n"
    if cat.get("note"):
        text += f"─────────────────────────\n💡 <b>မှတ်ချက်:</b>\n{cat['note']}\n"
    return text.strip()

def build_multiselect_summary(selected_items: dict) -> str:
    lines = ["🛒 <b>ရွေးချယ်ထားသော ဝန်ဆောင်မှုများ</b>\n"]
    total = 0
    for svc_code, qty in selected_items.items():
        item = CATALOG["TT"]["items"][svc_code]
        if svc_code == "PM":
            price = qty * 8000
            lines.append(f"  {item['emoji']} {item['name']} ({qty}$) = <b>{price:,} ks</b>")
        elif svc_code == "JP":
            price = item["tiers"].get(1, 0)
            lines.append(f"  {item['emoji']} {item['name']} = <b>{price:,} ks</b>")
        else:
            price = item["tiers"].get(qty, 0)
            qty_str = f"{qty//1000}k" if qty >= 1000 else str(qty)
            lines.append(f"  {item['emoji']} {item['name']} x{qty_str} = <b>{price:,} ks</b>")
        total += price
    lines.append(f"\n💰 <b>စုစုပေါင်း ကျသင့်ငွေ: {total:,} ks</b>")
    return "\n".join(lines)

# ================= MY ORDERS (PAGINATED HISTORY) =================
MY_ORDERS_PAGE_SIZE = 5

def build_my_orders_page(user_id: int, page: int):
    orders = get_user_orders(user_id)
    total = len(orders)
    pages = max(1, (total + MY_ORDERS_PAGE_SIZE - 1) // MY_ORDERS_PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    chunk = orders[page * MY_ORDERS_PAGE_SIZE: (page + 1) * MY_ORDERS_PAGE_SIZE]

    if not orders:
        text = (
            "╔═══════════════════╗\n"
            "   📦 <b>My Orders / Order History</b>\n"
            "╚═══════════════════╝\n\n"
            "⚠️ သင်၏ ဝယ်ယူထားမှုမှတ်တမ်း မရှိသေးပါ။\n\n"
            "💡 /start နှိပ်ပြီး အော်ဒါ စတင်ဝယ်ယူနိုင်ပါသည်ခင်ဗျာ။"
        )
        return text, pages, page

    text = "╔═══════════════════╗\n"
    text += f"   📦 <b>My Orders</b> (စုစုပေါင်း {total} ခု) | Page {page+1}/{pages}\n"
    text += "╚═══════════════════╝\n\n"
    for oid, data in chunk:
        status_label = STATUS_EMOJI.get(data["status"], data["status"])
        desc = data["description"]
        desc_short = desc[:40] + "..." if len(desc) > 40 else desc
        text += (
            f"🔹 <b>#{oid}</b>\n"
            f"   📋 {desc_short}\n"
            f"   💰 {data['total']:,} ks\n"
            f"   {status_label}\n"
            f"   🕐 {data['created_at']}\n\n"
        )
    text += "🔍 Order ID ဖြင့် အသေးစိတ် စစ်ဆေးရန် ID ကို ရိုက်ထည့်ပါ\nဥပမာ: <code>KNOX-1234</code>"
    return text, pages, page

def build_my_orders_kb(page: int, pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"myorderspage_{page-1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"myorderspage_{page+1}"))
    kb = []
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="start")])
    return InlineKeyboardMarkup(kb)

# ================= START MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user

    # ── Referral deep-link: /start ref_KX7QP2A ──
    is_new_user = not _user_registered(user.id)
    add_user(user.id, user.full_name, user.username)
    if is_new_user and context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            referrer_id = get_user_id_by_ref_code(arg[4:])
            if referrer_id:
                set_referred_by(user.id, referrer_id)

    if user.id != ADMIN_ID and is_banned(user.id):
        await (update.effective_message).reply_text(
            "🚫 သင့်အား Admin မှ ဤ Bot ကို အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။"
        )
        return

    balance = get_balance(user.id)
    vip_badge, vip_spent = get_vip_status(user.id)

    keyboard = [
        [
            InlineKeyboardButton("🛍️ ဝယ်ယူရန်",             callback_data="buy"),
            InlineKeyboardButton("📊 ဈေးနှုန်းကြည့်ရန်",      callback_data="price"),
        ],
        [
            InlineKeyboardButton("📦 My Orders",              callback_data="order_status"),
            InlineKeyboardButton(f"💳 My Wallet ({balance:,}ks)", callback_data="wallet_menu"),
        ],
        [
            InlineKeyboardButton("🎁 Referral (ဖိတ်ခေါ်ရန်)",  callback_data="referral_info"),
            InlineKeyboardButton(f"🏆 Points ({get_points(user.id):,})", callback_data="points_info"),
        ],
        [
            InlineKeyboardButton("❓ FAQ (အမေး/အဖြေ)",        callback_data="faq"),
            InlineKeyboardButton("🤖 သိချင်တာမေးရန်", callback_data="ai_chat"),
        ],
        [InlineKeyboardButton("👨‍💻 Admin ကို ဆက်သွယ်ရန်",     url="https://t.me/just_knox")],
    ]

    welcome_text = (
        "╔══════════════════╗\n"
        "   ✨ <b>𝗞𝗻𝗼𝘅 𝗗𝗶𝗴𝗶𝘁𝗮𝗹 𝗦𝘁𝗼𝗿𝗲 မှ ကြိုဆိုပါတယ်!</b> ✨\n"
        "╚══════════════════╝\n"
        "🔒 <i>အတန်ဆုံးဈေး၊အကောင်းဆုံး Quality🔥</i>\n\n"
        "👑 <b>ဝယ်ယူနိုင်သော Products များ</b>\n"
        "┌────────────────────\n"
        "│ 📱 TikTok Boost Services (ပြန်မကျ)\n"
        "│ 🎮 PUBG UC & PASS\n"
        "│ 💎 Mlbb Diamond\n"
        "│ 🫟 Capcut / Canva / Alight Motion\n"
        "│ ⭐ Telegram Premium & Account\n"
        "│ 🛡️ VPN Services (Express/Outline/Nord)\n"
        "│ 🎬 Premium(Netflix/Spotify/YouTube)\n"
        "└────────────────────\n"
        "🔰 <b>Join Channel:</b> https://t.me/knox_zone\n"
        "🔍 <b>အသုံးပြုနည်းလမ်းညွှန်ကြည့်ရန်:</b> /help\n"
        "─────────────────────"
    )

    if update.callback_query:
        try:
            await update.callback_query.message.reply_photo(
                photo=WELCOME_IMAGE, caption=welcome_text,
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text=welcome_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await update.message.reply_photo(
            photo=WELCOME_IMAGE, caption=welcome_text,
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= /help COMMAND (TUTORIAL) =============
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.full_name, user.username)
    tutorial_text = (
        "╔═══════════════════╗\n"
        "   📖 <b>အသုံးပြုနည်းလမ်းညွှန် Tutorial</b>\n"
        "╚═══════════════════╝\n\n"

        "🤖 <b>Bot Commands များ</b>\n"
        "─────────────────────\n"
        "• /start — Bot အသစ်ပြန်စရန် / Home Menu သို့\n"
        "• /help — ဤ Tutorial ကို ပြန်ကြည့်ရန်\n"
        "• /status — မိမိနောက်ဆုံးဝယ်ထားသော Order စစ်ရန်\n"
        "• /review [စာသား] — bot အပေါ် ကျေနပ်မှု Review ပေးရန်\n"
        "   ဥပမာ: <code>/review Bot လေး အရမ်းကောင်းတယ်!</code>\n\n"

        "💳 <b>Wallet (အီလက်ထရောနစ်ပိုက်ဆံအိတ်) အသုံးပြုနည်း</b>\n"
        "─────────────────────\n"
        "<b>အဆင့် ①</b> - /start ပြန်သွားပြီး <b>💳 My Wallet</b> ကို နှိပ်ပါ။\n"
        "<b>အဆင့် ②</b> - <b>➕ ‌ငွေဖြည့်မည် (Top-up)</b> ကိုနှိပ်ပြီး ဖြည့်မည့် ပမာဏ ရွေးချယ်ပါ။\n"
        "<b>အဆင့် ③</b> - ပြသလာသော KPay နံပါတ်သို့ ငွေလွှဲပြီး <b>ပြေစာ Screenshot</b> ကို Bot ထံ ပို့ပေးပါ။\n"
        "<b>အဆင့် ④</b> - Admin မှ အတည်ပြုပေးလိုက်ပါက Wallet Balance ရောက်လာပါမည်။\n\n"

        "📱 <b>TikTok Services ဝယ်နည်း (Multi-Select)</b>\n"
        "─────────────────────\n"
        "① /start → <b>ဝယ်ယူရန်</b> → TikTok Boost Services\n"
        "② လိုချင်သော Service ကို နှိပ်ပါ (ဥပမာ: Likes)\n"
        "③ အရေအတွက် ရွေးချယ်ပါ\n"
        "④ အခြား Service များပါ ထပ်မံ ပေါင်းထည့်နိုင်သည်\n"
        "⑤ ပြီးပါက ✅ အတည်ပြုပြီး Link ပို့ပါ\n"
        "⑥ Note ရေးလိုပါက ရေးပါ (မလိုပါက Skip နှိပ်ပါ)\n"
        "⑦ ငွေချေစနစ်ရွေးချယ်ပါ (KPay သို့မဟုတ် Wallet)\n\n"

        "🎮 <b>PUBG / MLBB / Apps / VPN / Subscription ဝယ်နည်း</b>\n"
        "─────────────────────\n"
        "① /start → <b>ဝယ်ယူရန်</b> → Category ရွေးပါ (ဥပမာ: PUBG UC & PASS)\n"
        "② Package/Pack ကို ရွေးချယ်ပါ\n"
        "③ တောင်းဆိုသော Game ID / Email / Info ကို ပို့ပေးပါ\n"
        "④ Note ရေးလိုပါက ရေးပါ (မလိုပါက Skip နှိပ်ပါ)\n"
        "⑤ ငွေချေစနစ်ရွေးချယ်ပါ (KPay သို့မဟုတ် Wallet)\n"
        "💡 မှားရွေးမိရင် <b>❌ ဤဝယ်ယူမှု ပယ်ဖျက်မည်</b> ကို နှိပ်ပြီး ပြန်စနိုင်ပါသည်\n\n"

        "📝 <b>Order Note Feature</b>\n"
        "─────────────────────\n"
        "ဝယ်ယူတိုင်းတွင် မှတ်ချက် (Discount code, အထူးတောင်းဆိုချက် စသည်) "
        "ရေးထည့်နိုင်ပါသည်။ မလိုအပ်ပါက Skip ခလုတ်ကို နှိပ်ရုံနှင့် ကျော်နိုင်ပါသည်။\n\n"

        "📊 <b>ဈေးနှုန်းကြိုကြည့်လိုပါက</b>\n"
        "─────────────────────\n"
        "/start → <b>📊 ဈေးနှုန်းများ</b> ကိုနှိပ်ပြီး Category ရွေးကြည့်နိုင်ပါသည်\n\n"

        "🤖 <b>AI Assistant</b>\n"
        "─────────────────────\n"
        "Menu ထဲက <b>🤖 သိချင်တာမေးရန်</b> ကိုနှိပ်ပြီး မည်သည့်မေးခွန်းမဆို "
        "တိုက်ရိုက်ရိုက်မေးနိုင်ပါသည် (ဈေးနှုန်း၊ ဝယ်နည်း စသည်)\n\n"

        "🎁 <b>Referral Program</b>\n"
        "─────────────────────\n"
        "Menu ထဲက <b>🎁 Referral</b> ကိုနှိပ်ပြီး သင်၏ Link ကို မိတ်ဆွေများထံ ပို့ပါ။ "
        "သူတို့ ပထမဆုံးအကြိမ် Order အောင်မြင်တိုင်း သင့် Wallet ထဲသို့ Bonus ရရှိပါမည်။\n\n"

        "🏆 <b>Loyalty Points</b>\n"
        "─────────────────────\n"
        "ဝယ်ယူတိုင်း Points အလိုအလျောက် ရရှိပြီး Menu ထဲက <b>🏆 Points</b> တွင် "
        "Wallet အဖြစ် ပြောင်းလဲနိုင်ပါသည်။\n\n"

        "🎟️ <b>Promo Code</b>\n"
        "─────────────────────\n"
        "ငွေချေမည့်အဆင့်တွင် <b>🎟️ Promo Code ထည့်မည်</b> ခလုတ်ဖြင့် လျှော့ကြေး Code ထည့်နိုင်ပါသည်။\n\n"

        "👨‍💻 <b>Admin ဆက်သွယ်ရန်</b>: @just_knox\n"
        "📢 <b>KNOX ZONE</b>: @knox_zone"
    )
    if user.id == ADMIN_ID:
        tutorial_text += (
            "\n\n━━━━━━━━━━━━━━━━━━━━━\n"
            "🛠 <b>Admin-only Commands</b>\n"
            "─────────────────────\n"
            "• /pending — Pending Orders အားလုံးကို လျှင်မြန်စွာ ကြည့်ရန်\n"
            "• /report — ရောင်းအား Report (ယနေ့/အပတ်/လ)\n"
            "• /dashboard — Revenue/Top-seller Analytics Dashboard\n"
            "• /export — Order အားလုံးကို CSV ဖြင့် Export ထုတ်ရန်\n"
            "• /users — Bot Users + Wallet Balance စာရင်း\n"
            "• /find [id] — User တစ်ဦးချင်းစီ အသေးစိတ်ကြည့်ရန်\n"
            "• /top — အသုံးအများဆုံး Customer 10 ဦး\n"
            "• /msg [id] [message] — User တစ်ဦးထံ တိုက်ရိုက်စာပို့ရန်\n"
            "• /addbalance [id] [amount] — Wallet ငွေပမာဏ ပြင်ရန် (- ဖြင့် နှုတ်နိုင်)\n"
            "• /addstock [key]\\n[lines...] — Auto-Delivery အတွက် Stock ထည့်ရန်\n"
            "• /stock — Stock ကျန်ရှိမှု စစ်ရန်\n"
            "• /addpromo [code] [percent|fixed] [value] [maxuses] [expiry] — Promo Code ဖန်တီးရန်\n"
            "• /promos — Promo Code စာရင်း\n"
            "• /delpromo [code] — Promo Code ဖျက်ရန်\n"
            "• /bc [message] — User အားလုံးထံ Broadcast ပို့ရန်\n"
            "• /ban [id] / /unban [id] / /banned — User ပိတ်ပင်ခြင်း စီမံရန်"
        )
    kb = [[InlineKeyboardButton("🏠 Home သို့ပြန်", callback_data="start")]]
    await update.message.reply_text(tutorial_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


# ================= /status COMMAND (CUSTOMER ORDERS) =============
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.full_name, user.username)
    orders = get_user_orders(user.id)
    if orders:
        text = "  ╔═══════════════════╗\n"
        text += "   📦 <b>သင်၏ နောက်ဆုံး Orders အခြေအနေများ</b>\n"
        text += "╚═══════════════════╝\n\n"
        for oid, data in orders[:5]:
            status_label = STATUS_EMOJI.get(data["status"], data["status"])
            text += (
                f"🔖 <b>Order ID:</b> <code>#{oid}</code>\n"
                f"📋 <b>အမျိုးအစား:</b> <code>{data['description'][:35]}</code>...\n"
                f"💰 <b>တန်ဖိုး:</b> <code>{data['total']:,}</code> ks\n"
                f"📊 <b>အခြေအနေ:</b> {status_label}\n"
                f"🕐 <b>အချိန်:</b> {data['created_at']}\n"
                f"─────────────────────────\n"
            )
    else:
        text = (
            "╔═══════════════════╗\n"
            "   📦 <b>Orderအခြေအနေ စစ်ဆေးခြင်း</b>\n"
            "╚═══════════════════╝\n\n"
            "⚠️ သင်၏ ဝယ်ယူထားမှုမှတ်တမ်း မရှိသေးပါ။\n\n"
            "💡 /start နှိပ်ပြီး အော်ဒါ စတင်ဝယ်ယူနိုင်ပါသည်ခင်ဗျာ။"
        )
    kb = [[InlineKeyboardButton("🏠 Home သို့ပြန်", callback_data="start")]]
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

# ================= ADMIN PENDING ORDERS COMMAND =================
async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = get_pending_orders(15)
    if not orders:
        await update.message.reply_text("✅ Pending Order မရှိတော့ပါ — အားလုံး ပြီးစီးပြီးပါပြီ!")
        return

    text = f"⏳ <b>Pending Orders</b> (နောက်ဆုံး {len(orders)} ခု)\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    for o in orders:
        note_line = f"   📝 Note: {html.escape(o['note'])}\n" if o["note"] else ""
        text += (
            f"🔖 <code>#{o['order_id']}</code>\n"
            f"   👤 {html.escape(o['user_name'])} (<code>{o['user_id']}</code>)\n"
            f"   📦 {o['description'][:45]}\n"
            f"   💰 {o['total']:,} ks | 🕐 {o['created_at']}\n"
            f"{note_line}\n"
        )
    text += "━━━━━━━━━━━━━━━━━━━━━\n💡 <i>Order ID ကို tap ကူးပြီး admin ချန်နယ်ထဲက photo caption ကနေ Confirm/Reject လုပ်နိုင်ပါသည်</i>"
    await update.message.reply_text(text, parse_mode="HTML")


async def admin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    now = datetime.now()
    today_str  = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    month_str  = now.strftime("%Y-%m")

    def fetch_stats(date_filter):
        cursor.execute(
            "SELECT SUM(total), COUNT(order_id) FROM orders WHERE created_at LIKE ? AND status = 'completed'",
            (f"{date_filter}%",)
        )
        row = cursor.fetchone()
        return (row[0] or 0, row[1] or 0)

    today_sales,  today_count  = fetch_stats(today_str)

    cursor.execute(
        "SELECT SUM(total), COUNT(order_id) FROM orders WHERE created_at >= ? AND status = 'completed'",
        (week_start + " 00:00",)
    )
    row = cursor.fetchone()
    week_sales, week_count = (row[0] or 0, row[1] or 0)

    month_sales, month_count = fetch_stats(month_str)

    cursor.execute("SELECT COUNT(order_id) FROM orders WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(order_id) FROM orders WHERE status = 'processing'")
    processing_count = cursor.fetchone()[0]

    # Total users from SQLite users table (Persistent across bot restarts)
    total_users = get_total_users_count()

    cursor.execute("SELECT SUM(balance) FROM wallets")
    total_wallet = cursor.fetchone()[0] or 0

    conn.close()

    report_text = (
        "📊 <b>KNOX ADMIN REPORT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>ယနေ့:</b> <code>{today_str}</code>\n\n"
        "📆 <b>ယနေ့ (Today)</b>\n"
        f"  💰 ရောင်းရငွေ: <code>{today_sales:,}</code> ks\n"
        f"  📦 Order အောင်မြင်: <code>{today_count}</code> ခု\n\n"
        "🗓 <b>ဤအပတ် (This Week)</b>\n"
        f"  💰 ရောင်းရငွေ: <code>{week_sales:,}</code> ks\n"
        f"  📦 Order အောင်မြင်: <code>{week_count}</code> ခု\n\n"
        "📅 <b>ဤလ (This Month)</b>\n"
        f"  💰 ရောင်းရငွေ: <code>{month_sales:,}</code> ks\n"
        f"  📦 Order အောင်မြင်: <code>{month_count}</code> ခု\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>Pending Orders:</b> <code>{pending_count}</code> ခု\n"
        f"⚙️ <b>Processing Orders:</b> <code>{processing_count}</code> ခု\n"
        f"👥 <b>စုစုပေါင်း Users (DB):</b> <code>{total_users}</code> ယောက်\n"
        f"🏦 <b>Wallet ငွေစုစုပေါင်း:</b> <code>{total_wallet:,}</code> ks\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>/users — User စာရင်းအသေးစိတ်ကြည့်ရန်</i>"
    )
    await update.message.reply_text(report_text, parse_mode="HTML")

# ================= ADMIN VIEW BOT USERS SYSTEM =================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    rows = get_users_with_balance()

    if not rows:
        await update.message.reply_text("👥 Bot တွင် အသုံးပြုသူစာရင်း မရှိသေးပါ။")
        return

    PAGE_SIZE = 30
    total = len(rows)
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    def build_page(page: int) -> str:
        start = page * PAGE_SIZE
        chunk = rows[start:start + PAGE_SIZE]
        text = f"?? <b>Bot Users စာရင်း</b> (စုစုပေါင်း {total} ဦး) | Page {page+1}/{pages}\n"
        text += "─────────────────────\n"
        for uid, uname, uhandle, bal, banned in chunk:
            ban_mark = " 🚫" if banned else ""
            display = f"@{uhandle}" if uhandle else (uname or str(uid))
            text += f"👤 {html.escape(display)} (<code>{uid}</code>) | 💰 <code>{bal:,}</code> ks{ban_mark}\n"
        return text

    context.bot_data.setdefault("users_rows", rows)

    page = 0
    text = build_page(page)
    kb = []
    if pages > 1:
        kb.append([InlineKeyboardButton("▶️ Next Page", callback_data=f"userspage_1")])
    await update.message.reply_text(text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb) if kb else None)

# ================= SPECIAL COMMANDS =================
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.full_name, user.username)
    if not context.args:
        await update.message.reply_text(
            "❌ စာသားထည့်ရန် လိုအပ်ပါသည်။ ပုံစံ: <code>/review Bot လေး အရမ်းမိုက်တယ်ဗျာ</code>",
            parse_mode="HTML"
        )
        return
    review_text = " ".join(context.args)
    admin_msg = (
        f"⭐️ <b>Review အသစ် ရောက်ရှိလာပါပြီ</b> ⭐️\n\n"
        f"👤 <b>ပေးသူ:</b> {html.escape(user.full_name)} (ID: <code>{user.id}</code>)\n"
        f"✍️ <b>Review:</b> {html.escape(review_text)}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
    await update.message.reply_text("💖 Review ပေးပေးတဲ့အတွက် ကျေးဇူးအများကြီးတင်ပါတယ်ခင်ဗျာ! Admin ထံ ပေးပို့လိုက်ပါပြီ။")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ သင်သည် Admin မဟုတ်သဖြင့် ဤ Command ကို သုံးခွင့်မရှိပါ။")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ စာသားထည့်ရန် လိုအပ်ပါသည်။ ပုံစံ: <code>/bc စာသားရိုက်ရန်</code>",
            parse_mode="HTML"
        )
        return
    bc_msg = " ".join(context.args)
    all_users = get_all_users()
    count = 0
    await update.message.reply_text(f"📢 User {len(all_users)} ယောက်ဆီ စာလှမ်းပို့နေပါပြီ...")
    for uid in all_users:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 <b>[Knox Zone Announcement]</b>\n\n{bc_msg}",
                parse_mode="HTML"
            )
            count += 1
        except Exception:
            continue
    await update.message.reply_text(f"✅ User {count} ယောက်ဆီ စာသား အောင်မြင်စွာ ပို့ပြီးပါပြီ။")

# ================= ADMIN BAN SYSTEM COMMANDS =================
async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ သင်သည် Admin မဟုတ်သဖြင့် ဤ Command ကို သုံးခွင့်မရှိပါ။")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ User ID ထည့်ရန် လိုအပ်ပါသည်။ ပုံစံ: <code>/ban 123456789</code>",
            parse_mode="HTML"
        )
        return
    try:
        target_uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID သည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    ban_user(target_uid)
    await update.message.reply_text(f"🚫 User <code>{target_uid}</code> ကို ban လုပ်လိုက်ပါပြီ။", parse_mode="HTML")
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text="🚫 သင့်အား Admin မှ ဤ Bot ကို အသုံးပြုခွင့် ပိတ်ပင်လိုက်ပါသည်။"
        )
    except Exception:
        pass

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ သင်သည် Admin မဟုတ်သဖြင့် ဤ Command ကို သုံးခွင့်မရှိပါ။")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ User ID ထည့်ရန် လိုအပ်ပါသည်။ ပုံစံ: <code>/unban 123456789</code>",
            parse_mode="HTML"
        )
        return
    try:
        target_uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID သည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    unban_user(target_uid)
    await update.message.reply_text(f"✅ User <code>{target_uid}</code> ကို ban ပြန်ဖြေလိုက်ပါပြီ။", parse_mode="HTML")
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text="✅ သင့်အား ဤ Bot ကို ပြန်လည်အသုံးပြုခွင့် ပေးလိုက်ပါပြီ။"
        )
    except Exception:
        pass

async def admin_banned_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    rows = get_banned_users()
    if not rows:
        await update.message.reply_text("🚫 Ban ခံထားရသော User မရှိသေးပါ။")
        return
    text = f"🚫 <b>Ban ခံထားရသော Users</b> (စုစုပေါင်း {len(rows)} ဦး)\n─────────────────────\n"
    for uid, uname in rows:
        text += f"👤 <code>{uid}</code> | {html.escape(uname or '-')}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ================= ADMIN: LOOK UP A SINGLE USER =================
async def admin_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "❌ User ID ထည့်ရန် လိုအပ်ပါသည်။ ပုံစံ: <code>/find 123456789</code>",
            parse_mode="HTML"
        )
        return
    try:
        target_uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID သည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    balance = get_balance(target_uid)
    banned = is_banned(target_uid)
    vip_badge, vip_spent = get_vip_status(target_uid)
    orders = get_user_orders(target_uid)
    display_name = get_user_display_name(target_uid)
    text = (
        f"🔎 <b>User Info</b>\n─────────────────────\n"
        f"👤 Name: {html.escape(display_name)}\n"
        f"🆔 ID: <code>{target_uid}</code>\n"
        f"💰 Wallet: <code>{balance:,}</code> ks\n"
        f"🏅 {vip_badge} (Lifetime: {vip_spent:,} ks)\n"
        f"📦 Orders: {len(orders)}\n"
        f"🚫 Ban Status: {'Banned' if banned else 'Active'}\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# ================= ADMIN: DIRECT MESSAGE TO A SINGLE USER =================
async def admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message straight to one user's chat, from the bot — not a broadcast."""
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ ပုံစံ: <code>/msg 123456789 စာသားရိုက်ရန်</code>\n"
            "(User ID ကို ဦးစွာသိရန် /users သို့မဟုတ် /find ကို သုံးပါ)",
            parse_mode="HTML"
        )
        return
    try:
        target_uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID သည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    msg_text = " ".join(context.args[1:])
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=f"💬 <b>[Knox Digital Store မှ Admin]</b>\n\n{html.escape(msg_text)}",
            parse_mode="HTML"
        )
        display_name = get_user_display_name(target_uid)
        await update.message.reply_text(
            f"✅ {html.escape(display_name)} (<code>{target_uid}</code>) ဆီ စာပို့ပြီးပါပြီ။",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ စာပို့မရပါ — User က Bot ကို Block လုပ်ထားနိုင်ပါသည်။\n<code>{html.escape(str(e))}</code>", parse_mode="HTML")

# ================= ADMIN: MANUAL WALLET ADJUSTMENT =================
async def admin_addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ ပုံစံ: <code>/addbalance 123456789 5000</code>\n(အနုတ်ကိန်း ရိုက်ထည့်ပြီး နှုတ်လည်းရပါသည်၊ ဥပမာ - -2000)",
            parse_mode="HTML"
        )
        return
    try:
        target_uid = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ User ID နှင့် ပမာဏသည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    add_balance(target_uid, amount)
    new_balance = get_balance(target_uid)
    display_name = get_user_display_name(target_uid)
    await update.message.reply_text(
        f"✅ {html.escape(display_name)} (<code>{target_uid}</code>) ၏ Wallet ကို {amount:+,}ks ပြင်ဆင်ပြီးပါပြီ။\n"
        f"💰 လက်ရှိ Balance: <code>{new_balance:,}</code> ks",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=f"💰 Admin မှ သင့် Wallet ကို {amount:+,}ks ပြင်ဆင်ပေးလိုက်ပါသည်။\nလက်ရှိ Balance: {new_balance:,}ks",
        )
    except Exception:
        pass

# ================= ADMIN: TOP SPENDERS =================
async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.user_id, u.user_name, u.username, SUM(o.total) as spent
        FROM orders o
        LEFT JOIN users u ON u.user_id = o.user_id
        WHERE o.status = 'completed'
        GROUP BY o.user_id
        ORDER BY spent DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("📊 ပြီးစီးထားသော Order မရှိသေးပါ။")
        return
    text = "🏆 <b>Top 10 Spenders (Lifetime)</b>\n─────────────────────\n"
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    for i, (uid, uname, uhandle, spent) in enumerate(rows):
        display = f"@{uhandle}" if uhandle else (uname or str(uid))
        text += f"{medals[i]} {html.escape(display)} (<code>{uid}</code>) — {spent:,}ks\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ================= ADMIN: STOCK / AUTO-DELIVERY =================
async def admin_addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage (first line = command + item key, following lines = one stock unit each):
    /addstock VPN_-_EVPN1DEV
    user1@mail.com:pass1
    user2@mail.com:pass2
    Item key format is CATCODE_GRPCODE_ITEMCODE (use - for no group, e.g. VPN/APPS items)."""
    if update.effective_user.id != ADMIN_ID:
        return
    lines = update.message.text.split("\n")
    first_line = lines[0].strip()
    parts = first_line.split(maxsplit=1)
    if len(parts) < 2 or len(lines) < 2:
        await update.message.reply_text(
            "❌ ပုံစံ:\n<code>/addstock VPN_-_EVPN1DEV\nline1\nline2</code>\n\n"
            "🔑 Key ပုံစံ: <code>CATCODE_GRPCODE_ITEMCODE</code> (Group မရှိလျှင် <code>-</code> ထည့်ပါ)\n"
            "ဥပမာ - <code>VPN_-_EVPN1DEV</code>, <code>PUBG_UC_UC60</code>",
            parse_mode="HTML"
        )
        return
    item_key = parts[1].strip().replace(" ", "_")
    stock_lines = [l for l in lines[1:] if l.strip()]
    if not stock_lines:
        await update.message.reply_text("❌ Stock content မပါပါ (2nd line မှစပြီး ထည့်ပေးပါ)။")
        return
    added = add_stock(item_key, stock_lines)
    await update.message.reply_text(
        f"✅ <code>{html.escape(item_key)}</code> အတွက် stock <b>{added}</b> ခု ထည့်ပြီးပါပြီ။\n"
        f"📦 လက်ရှိ ကျန်ရှိမှု: <b>{get_stock_count(item_key)}</b> ခု",
        parse_mode="HTML"
    )

async def admin_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    rows = list_stock_summary()
    if not rows:
        await update.message.reply_text("📦 Stock item မထည့်ရသေးပါ။ /addstock ဖြင့် ထည့်ပါ။")
        return
    text = "📦 <b>Stock Levels</b>\n─────────────────────\n"
    for item_key, remaining in rows:
        warn = " ⚠️" if remaining <= LOW_STOCK_THRESHOLD else ""
        text += f"<code>{html.escape(item_key)}</code> — <b>{remaining}</b> ခု{warn}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ================= ADMIN: PROMO CODES =================
async def admin_addpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 4:
        await update.message.reply_text(
            "❌ ပုံစံ: <code>/addpromo CODE percent|fixed VALUE MAXUSES [EXPIRY:YYYY-MM-DD|none]</code>\n\n"
            "ဥပမာ - <code>/addpromo KNOX10 percent 10 100 none</code>\n"
            "ဥပမာ - <code>/addpromo SAVE2K fixed 2000 50 2026-12-31</code>",
            parse_mode="HTML"
        )
        return
    code, kind, value_s, max_uses_s = context.args[0], context.args[1].lower(), context.args[2], context.args[3]
    expiry = context.args[4] if len(context.args) > 4 else "none"
    if kind not in ("percent", "fixed"):
        await update.message.reply_text("❌ Type သည် <code>percent</code> သို့မဟုတ် <code>fixed</code> ဖြစ်ရပါမည်။", parse_mode="HTML")
        return
    try:
        value = int(value_s)
        max_uses = int(max_uses_s)
    except ValueError:
        await update.message.reply_text("❌ VALUE နှင့် MAXUSES သည် ဂဏန်းဖြစ်ရပါမည်။")
        return
    if create_promo(code, kind, value, max_uses, expiry):
        await update.message.reply_text(
            f"✅ Promo Code <code>{code.upper()}</code> ဖန်တီးပြီးပါပြီ။\n"
            f"🎟️ {kind} — {value}{'%' if kind == 'percent' else 'ks'} — {max_uses} ကြိမ် — Expiry: {expiry}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"❌ Promo Code <code>{code.upper()}</code> ရှိပြီးသားဖြစ်ပါသည်။", parse_mode="HTML")

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    rows = list_promos()
    if not rows:
        await update.message.reply_text("🎟️ Promo Code မရှိသေးပါ။ /addpromo ဖြင့် ဖန်တီးပါ။")
        return
    text = "🎟️ <b>Promo Codes</b>\n─────────────────────\n"
    for code, kind, value, max_uses, used_count, expiry, active in rows:
        status = "✅" if active else "🚫"
        val_str = f"{value}%" if kind == "percent" else f"{value:,}ks"
        text += f"{status} <code>{code}</code> — {val_str} — {used_count}/{max_uses} — Exp: {expiry}\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def admin_delpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ ပုံစံ: <code>/delpromo CODE</code>", parse_mode="HTML")
        return
    if delete_promo(context.args[0]):
        await update.message.reply_text(f"✅ Promo Code <code>{context.args[0].upper()}</code> ဖျက်ပြီးပါပြီ။", parse_mode="HTML")
    else:
        await update.message.reply_text("❌ ဒီ Promo Code မတွေ့ပါ။")

# ================= ADMIN: DASHBOARD / ANALYTICS =================
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    def revenue_since(days):
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
        cursor.execute("SELECT COALESCE(SUM(total),0), COUNT(*) FROM orders WHERE status='completed' AND created_at >= ?", (since,))
        return cursor.fetchone()

    today_rev, today_n = revenue_since(1)
    week_rev, week_n = revenue_since(7)
    month_rev, month_n = revenue_since(30)

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
    pending_n = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('completed','processing')")
    total_orders = cursor.fetchone()[0]
    cursor.execute("SELECT description, COUNT(*) c FROM orders WHERE status IN ('completed','processing') GROUP BY description ORDER BY c DESC LIMIT 5")
    top_items = cursor.fetchall()
    conn.close()

    total_users = get_total_users_count()

    text = (
        "╔══════════════════╗\n"
        "   📊 <b>Knox Store Dashboard</b>\n"
        "╚══════════════════╝\n\n"
        f"👥 Total Users: <b>{total_users:,}</b>\n"
        f"🧾 Total Confirmed Orders: <b>{total_orders:,}</b>\n"
        f"⏳ Pending Orders: <b>{pending_n:,}</b>\n\n"
        f"💰 <b>Revenue</b>\n"
        f"  • Today: <b>{today_rev:,} ks</b> ({today_n} orders)\n"
        f"  • Last 7 days: <b>{week_rev:,} ks</b> ({week_n} orders)\n"
        f"  • Last 30 days: <b>{month_rev:,} ks</b> ({month_n} orders)\n\n"
        f"🔥 <b>Top Sellers (all-time)</b>\n"
    )
    if top_items:
        max_c = max(c for _, c in top_items)
        for desc, c in top_items:
            bar_len = max(1, int((c / max_c) * 10))
            bar = "█" * bar_len
            label = (desc[:28] + "…") if len(desc) > 28 else desc
            text += f"  {bar} {c}  {html.escape(label)}\n"
    else:
        text += "  (Order မရှိသေးပါ)\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ================= ADMIN: EXPORT ORDERS TO CSV =================
async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    import csv, io
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, user_id, user_name, description, total, status, created_at, note FROM orders ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("📄 Export လုပ်ရန် Order မရှိသေးပါ။")
        return
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["order_id", "user_id", "user_name", "description", "total", "status", "created_at", "note"])
    writer.writerows(rows)
    data = buf.getvalue().encode("utf-8-sig")
    filename = f"knox_orders_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await update.message.reply_document(
        document=(filename, data),
        caption=f"📄 Order {len(rows)} ခု Export ပြီးပါပြီ။"
    )

# ================= BUTTON HANDLER =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    add_user(user.id, user.full_name, user.username)
    user_id = user.id

    if user_id != ADMIN_ID and is_banned(user_id):
        await q.message.reply_text("🚫 သင့်အား Admin မှ ဤ Bot ကို အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
        return

    # ─────────── HOME ───────────
    if q.data == "start":
        await start(update, context)

    # ─────────── CANCEL AN IN-PROGRESS ORDER ───────────
    elif q.data == "cancel_order":
        context.user_data.clear()
        await q.message.reply_text("❌ ဝယ်ယူမှုကို ပယ်ဖျက်လိုက်ပါပြီ။")
        await start(update, context)

    # ─────────── AI CHAT INFO ───────────
    elif q.data == "ai_chat":
        await q.message.reply_text(
            "🤖 <b>AI Assistant</b>\n\n"
            "ဤ Chat ထဲတွင် မည်သည့်အရာမဆို တိုက်ရိုက် ရိုက်မေးနိုင်ပါသည်!\n\n"
            "ဥပမာ:\n"
            "• <code>Likes 500 ဈေး ဘယ်လောက်လဲ?</code>\n"
            "• <code>TikTok Views ဘာကြောင့် ဝယ်သုံးသင့်လဲ?</code>\n"
            "• <code>MLBB Diamond ဘယ်လို ဝယ်ရမလဲ?</code>\n\n"
            "💬 ဘာပဲ မေးမေး - AI ဖြေပါမည်!",
            parse_mode="HTML"
        )

    # ─────────── BUY CATEGORY LIST ───────────
    elif q.data == "buy":
        await safe_edit_message(q, "🛍️ <b>ဝယ်ယူလိုသော Category ကို ရွေးချယ်ပါ</b>", reply_markup=build_main_buy_menu())

    # ─────────── CATEGORY SELECTED ───────────
    elif q.data.startswith("cat_"):
        cat_code = q.data.replace("cat_", "")
        cat = CATALOG[cat_code]

        if cat_code == "TT":
            if "tt_selected" not in context.user_data:
                context.user_data["tt_selected"] = {}
            selected = context.user_data.get("tt_selected", {})
            markup, total = build_tt_multiselect_menu(selected)
            caption = (
                "📱 <b>TikTok Boost Services</b>\n\n"
                "✨ <b>Multi-Select Feature!</b> - Service များကို တစ်ချိန်တည်းမှာ အများကြီး ရွေးနိုင်ပါတယ်!\n\n"
                "📌 Service တစ်ခု နှိပ်ပြီး အရေအတွက် ရွေးပါ\n"
                "📌 ဈေးကို Auto တွက်ပေးပါမည်\n\n"
                f"{cat.get('note', '')}"
            )
            await safe_edit_message(q, caption, reply_markup=markup)

        elif "groups" in cat:
            caption = f"📦 <b>{cat['title']}</b>\n\n"
            if cat.get("note"):
                caption += f"{cat['note']}\n\n"
            caption += "👇 အမျိုးအစား ရွေးချယ်ပါ"
            await safe_edit_message(q, caption, reply_markup=build_group_menu(cat_code))
        else:
            kb = build_item_buttons_rows(cat_code, "-", cat["items"])
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="buy")])
            caption = f"📦 <b>{cat['title']}</b>\n\n"
            if cat.get("note"):
                caption += f"{cat['note']}\n\n"
            caption += "👇 ပစ္စည်း ရွေးချယ်ပါ"
            await safe_edit_message(q, caption, reply_markup=InlineKeyboardMarkup(kb))

    # ─────────── GROUP (SUB-CATEGORY) ───────────
    elif q.data.startswith("grp_"):
        _, cat_code, grp_code = q.data.split("_")
        cat = CATALOG[cat_code]
        grp = cat["groups"][grp_code]
        kb = build_item_buttons_rows(cat_code, grp_code, grp["items"])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data=f"cat_{cat_code}")])
        caption = f"📦 <b>{grp['title']}</b>\n\n"
        if cat.get("note"):
            caption += f"{cat['note']}\n\n"
        caption += "👇 ပစ္စည်း ရွေးချယ်ပါ"
        await safe_edit_message(q, caption, reply_markup=InlineKeyboardMarkup(kb))

    # ─────────── TIKTOK MULTI-SELECT: Service ─────────────
    elif q.data.startswith("ttsel_"):
        svc_code = q.data.replace("ttsel_", "")
        if "tt_selected" not in context.user_data:
            context.user_data["tt_selected"] = {}
        selected = context.user_data["tt_selected"]
        item = CATALOG["TT"]["items"][svc_code]
        markup = build_tt_qty_menu(svc_code, selected)
        caption = f"🔢 <b>{item['emoji']} {item['name']}</b>\n\n"
        if selected:
            caption += build_multiselect_summary(selected) + "\n\n"
        for qty, price in item["tiers"].items():
            if svc_code in ["JP", "PM"]:
                caption += f"🔸 ဈေးနှုန်း = {price:,} ks\n"
            else:
                qty_str = f"{qty//1000}k" if qty >= 1000 else str(qty)
                caption += f"🔸 {qty_str} = {price:,} ks\n"
        await safe_edit_message(q, caption, reply_markup=markup)

    elif q.data.startswith("ttqty_"):
        parts = q.data.split("_")
        svc_code, qty = parts[1], int(parts[2])
        if "tt_selected" not in context.user_data:
            context.user_data["tt_selected"] = {}
        context.user_data["tt_selected"][svc_code] = qty
        selected = context.user_data["tt_selected"]
        markup, total = build_tt_multiselect_menu(selected)
        caption = "📱 <b>TikTok Boost Services</b>\n\n✅ ရွေးချယ်မှု သိမ်းဆည်းပြီးပါပြီ!\n\n"
        caption += build_multiselect_summary(selected)
        caption += "\n\n➕ ထပ်ဆောင်း Service ရွေးနိုင်သည် သို့မဟုတ် ✅ နှိပ်ပြီး ဆက်သွားပါ"
        await safe_edit_message(q, caption, reply_markup=markup)

    elif q.data.startswith("ttremove_"):
        svc_code = q.data.replace("ttremove_", "")
        if "tt_selected" in context.user_data and svc_code in context.user_data["tt_selected"]:
            del context.user_data["tt_selected"][svc_code]
        selected = context.user_data.get("tt_selected", {})
        markup, _ = build_tt_multiselect_menu(selected)
        caption = "📱 <b>TikTok Boost Services</b>\n\n❌ Service ဖယ်ရှားပြီးပါပြီ\n\n"
        caption += build_multiselect_summary(selected) if selected else "📌 Service တစ်ခု နှိပ်ပြီး အရေအတွက် ရွေးပါ"
        await safe_edit_message(q, caption, reply_markup=markup)

    elif q.data == "tt_clear":
        context.user_data["tt_selected"] = {}
        markup, _ = build_tt_multiselect_menu({})
        await safe_edit_message(
            q, "📱 <b>TikTok Boost Services</b>\n\n🗑️ အားလုံး ရှင်းလင်းပြီးပါပြီ\n\n📌 Service တစ်ခု နှိပ်ပြီး ထပ်ရွေးပါ",
            reply_markup=markup
        )

    elif q.data == "tt_back_multi":
        selected = context.user_data.get("tt_selected", {})
        markup, _ = build_tt_multiselect_menu(selected)
        caption = "📱 <b>TikTok Boost Services</b>\n\n"
        caption += build_multiselect_summary(selected) + "\n\n" if selected else ""
        caption += "📌 ထပ်ဆောင်း Service ရွေးနိုင်သည် သို့မဟုတ် ✅ နှိပ်ပြီး ဆက်သွားပါ"
        await safe_edit_message(q, caption, reply_markup=markup)

    elif q.data == "tt_summary":
        selected = context.user_data.get("tt_selected", {})
        if selected:
            total = 0
            for sc, qty in selected.items():
                if sc == "PM":
                    total += qty * 8000
                elif sc == "JP":
                    total += CATALOG["TT"]["items"][sc]["tiers"].get(1, 0)
                else:
                    total += CATALOG["TT"]["items"][sc]["tiers"].get(qty, 0)
            await q.answer(f"စုစုပေါင်း: {total:,} ks", show_alert=True)
        else:
            await q.answer("မရွေးရသေးပါ", show_alert=True)

    elif q.data == "pm_custom_amount":
        context.user_data["step"] = "pm_custom_dollar"
        await q.message.reply_text(
            "📹 <b>TikTok Promote - Custom Amount</b>\n\n"
            "Promote လုပ်ချင်သော ပမာဏကို <b>Dollar ($)</b> ဖြင့် ရိုက်ထည့်ပါ\n"
            "ဥပမာ: <code>5</code> (5$ = 40,000 ks)\n\n"
            "💡 အနည်းဆုံး 1$, ဂဏန်းသာ ရိုက်ပါ",
            parse_mode="HTML"
        )

    elif q.data == "tt_confirm_multi":
        selected = context.user_data.get("tt_selected", {})
        if not selected:
            await q.answer("⚠️ Service တစ်ခုမျှ မရွေးရသေးပါ!", show_alert=True)
            return
        total = 0
        for sc, qty in selected.items():
            if sc == "PM":
                total += qty * 8000
            elif sc == "JP":
                total += CATALOG["TT"]["items"][sc]["tiers"].get(1, 0)
            else:
                total += CATALOG["TT"]["items"][sc]["tiers"].get(qty, 0)
        context.user_data["flow"] = "tiktok_multi"
        context.user_data["tt_total"] = total
        context.user_data["step"] = "tt_multi_link"
        summary = build_multiselect_summary(selected)
        await q.message.reply_text(
            f"✅ <b>Order အတည်ပြုပြီးပါပြီ!</b>\n\n{summary}\n\n"
            f"🔗 <b>TikTok Video Link</b> ပို့ပေးပါခင်ဗျ\n"
            f"(Video သည် Public ဖြစ်ရပါမည်)",
            parse_mode="HTML"
        )

    # ─────────── PRICE LIST ───────────
    elif q.data == "price":
        kb = [[InlineKeyboardButton(cat["title"], callback_data=f"pricecat_{code}")] for code, cat in CATALOG.items()]
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="start")])
        await q.message.reply_text(
            "📊 <b>ဈေးနှုန်းကြည့်လိုသော Category ကို ရွေးချယ်ပါ</b>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data.startswith("pricecat_"):
        cat_code = q.data.replace("pricecat_", "")
        text = build_price_text(cat_code)
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="price")]]
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ─────────── FAQ ───────────
    elif q.data == "faq":
        keyboard = [
            [InlineKeyboardButton("⏱️ တက်ချိန် ဘယ်လောက်ကြာလဲ။",    callback_data="faq_time")],
            [InlineKeyboardButton("🔒 အကောင့် Password ပေးရမလား။",   callback_data="faq_safe")],
            [InlineKeyboardButton("🛒 Multi-Select ဘယ်လိုသုံးရမလဲ",   callback_data="faq_multi")],
            [InlineKeyboardButton("🔙 Back",                           callback_data="start")],
        ]
        await q.message.reply_text(
            "❓ <b>သိလိုသော မေးခွန်းကို နှိပ်ပါခင်ဗျာ</b>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif q.data == "faq_time":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="faq")]]
        await q.message.reply_text(
            "⏳ ဝန်ဆောင်မှု ကြာချိန်ကတော့ ပုံမှန်အားဖြင့် 15 မိနစ် ကနေ ၂၄ နာရီအတွင်း ရပါတယ်ခင်ဗျာ။\n"
            "Monetization View ကတော့ ၂၄ နာရီကနေ ၇၂ နာရီအထိ ကြာနိုင်ပါတယ်ခင်ဗျ။\n"
            "PUBG / MLBB Order များကို ၃၀ မိနစ်အတွင်း ပြီးစီးအောင် လုပ်ပေးပါသည်။",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data == "faq_safe":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="faq")]]
        await q.message.reply_text(
            "🔒 လုံးဝ ပေးစရာမလိုပါဘူးခင်ဗျာ။ Password ပေးစရာမလိုဘဲ "
            "TikTok Video Link / Game ID တစ်ခုတည်းနဲ့တင် ၁၀၀% Safe ဖြစ်လို့ စိတ်ချနိုင်ပါတယ်။",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data == "faq_multi":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="faq")]]
        await q.message.reply_text(
            "🛒 <b>TikTok Multi-Select အသုံးပြုနည်း</b>\n\n"
            "① ဝယ်ယူရန် → TikTok Boost Services\n"
            "② လုပ်ချင်သော Service ကို နှိပ်ပါ\n"
            "③ အရေအတွက် ရွေးပါ → ဈေး auto တွက်သည်\n"
            "④ Service list သို့ပြန်ပြီး နောက်တစ်ခု ထပ်ရွေးပါ\n"
            "⑤ ပြီးရင် ✅ နှိပ်ပြီး Link ပို့ပါ\n\n"
            "ဥပမာ: Like 500 (2,000ks) + View 1,000 (1000ks)\n= <b>စုစုပေါင်း 2,500ks</b> သာ ပေးရမည်",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # ─────────── FIXED-PRICE ITEM SELECTED & MLBB WEEKLY PASS CUSTOM ───────────
    elif q.data.startswith("item_"):
        _, cat_code, grp_code, item_code = q.data.split("_")
        
        # Check if MLBB Weekly Pass (WP) -> Custom Quantity (+ / -) Handler
        if cat_code == "MLBB" and item_code == "WP":
            context.user_data.clear()
            context.user_data["mlbb_wp_qty"] = 1
            await show_mlbb_wp_menu(q, context)
            return

        cat = CATALOG[cat_code]
        item = get_item(cat_code, grp_code, item_code)
        context.user_data.clear()
        context.user_data["flow"] = "fixed"
        context.user_data["cat_code"] = cat_code
        context.user_data["grp_code"] = grp_code
        context.user_data["item_code"] = item_code
        context.user_data["item_name"] = item["name"]
        context.user_data["price"] = item["price"]
        context.user_data["step"] = "info_fixed"
        ask_label = cat.get("ask_label", "🆔 လိုအပ်သော အချက်အလက်များကို ပို့ပေးပါခင်ဗျာ")
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ ဤဝယ်ယူမှု ပယ်ဖျက်မည်", callback_data="cancel_order")]])
        await q.message.reply_text(
            f"🛒 <b>{item['name']}</b>\n💰 ဈေးနှုန်း: <b>{item['price']:,} ks</b>\n\n{ask_label}",
            parse_mode="HTML",
            reply_markup=back_kb
        )

    # ── MLBB Weekly Pass Quantity Actions (+ / -) ──
    elif q.data == "mlbbwp_inc":
        qty = context.user_data.get("mlbb_wp_qty", 1)
        if qty < 50:
            context.user_data["mlbb_wp_qty"] = qty + 1
        await update_mlbb_wp_message(q, context)

    elif q.data == "mlbbwp_dec":
        qty = context.user_data.get("mlbb_wp_qty", 1)
        if qty > 1:
            context.user_data["mlbb_wp_qty"] = qty - 1
        await update_mlbb_wp_message(q, context)

    elif q.data == "mlbbwp_noop":
        await q.answer("📦 လက်ရှိ ရွေးချယ်ထားသော ပမာဏဖြစ်ပါသည်။", show_alert=False)

    elif q.data == "mlbbwp_confirm":
        qty = context.user_data.get("mlbb_wp_qty", 1)
        total_price = qty * 7000
        
        context.user_data.clear()
        context.user_data["flow"] = "fixed"
        context.user_data["cat_code"] = "MLBB"
        context.user_data["grp_code"] = "DM"
        context.user_data["item_code"] = "WP"
        context.user_data["item_name"] = f"💎 Weekly Pass (x{qty})"
        context.user_data["price"] = total_price
        context.user_data["step"] = "info_fixed"
        
        ask_label = CATALOG["MLBB"].get("ask_label", "🆔 MLBB <b>Game ID (Server ID)</b> ကို ပို့ပေးပါခင်ဗျာ")
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ ဤဝယ်ယူမှု ပယ်ဖျက်မည်", callback_data="cancel_order")]])
        await q.message.reply_text(
            f"🛒 <b>💎 Weekly Pass (x{qty})</b>\n💰 စုစုပေါင်း ကျသင့်ငွေ: <b>{total_price:,} ks</b>\n\n{ask_label}",
            parse_mode="HTML",
            reply_markup=back_kb
        )

    # ─────────── SKIP THE OPTIONAL ORDER NOTE ───────────
    elif q.data == "note_skip":
        await show_payment_method_prompt(q.message, context, user_id)

    # ─────────── MY ORDERS / ORDER STATUS TRACKING ───────────
    elif q.data == "order_status":
        text, pages, page = build_my_orders_page(user_id, 0)
        context.user_data["step"] = "check_order_status"
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=build_my_orders_kb(page, pages))

    # ─────────── REFERRAL PROGRAM ───────────
    elif q.data == "referral_info":
        ref_code = get_or_create_ref_code(user_id)
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{ref_code}"
        referrals = count_referrals(user_id)
        earned = get_referral_earnings(user_id)
        text = (
            "╔══════════════════╗\n"
            "   🎁 <b>Referral Program</b>\n"
            "╚══════════════════╝\n\n"
            f"👥 သင် ဖိတ်ခေါ်ထားသူ: <b>{referrals} ဦး</b>\n"
            f"💰 စုစုပေါင်း ရရှိငွေ: <b>{earned:,} ks</b>\n\n"
            f"🔗 <b>သင်၏ Referral Link:</b>\n<code>{link}</code>\n\n"
            f"🎟️ <b>သင်၏ Referral Code:</b> <code>{ref_code}</code>\n\n"
            f"✨ သင့် Link ဖြင့် ဝင်လာသူတစ်ဦးဦး ပထမဆုံးအကြိမ် Order အောင်မြင်တိုင်း "
            f"သင့် Wallet ထဲသို့ <b>{REFERRAL_BONUS:,} ks</b> အလိုအလျောက် ရရှိပါမည်!"
        )
        kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ─────────── LOYALTY POINTS ───────────
    elif q.data == "points_info":
        pts = get_points(user_id)
        worth = pts * POINT_VALUE_KS
        text = (
            "╔══════════════════╗\n"
            "   🏆 <b>Loyalty Points</b>\n"
            "╚══════════════════╝\n\n"
            f"⭐ လက်ရှိ Points: <b>{pts:,}</b>\n"
            f"💰 Wallet အဖြစ် လဲလှယ်ပါက: <b>{worth:,} ks</b>\n\n"
            f"📌 <i>Order 1,000ks တိုင်းအတွက် {POINTS_PER_1000KS} Point ရရှိပြီး, "
            f"1 Point = {POINT_VALUE_KS} ks အဖြစ် Wallet ထဲ ပြန်လဲလှယ်နိုင်ပါသည်</i>\n"
            f"(အနည်းဆုံး {MIN_POINTS_TO_REDEEM} Points လိုအပ်ပါသည်)"
        )
        kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
        if pts >= MIN_POINTS_TO_REDEEM:
            kb.insert(0, [InlineKeyboardButton(f"💳 Points {pts:,} ခုလုံး Wallet သို့ ပြောင်းမည်", callback_data="redeem_points_all")])
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "redeem_points_all":
        pts = get_points(user_id)
        if pts < MIN_POINTS_TO_REDEEM:
            await q.answer(f"❌ အနည်းဆုံး {MIN_POINTS_TO_REDEEM} Points လိုအပ်ပါသည်", show_alert=True)
            return
        redeem_points_to_wallet(user_id, pts)
        await q.message.reply_text(
            f"✅ <b>Points {pts:,} ခုကို {pts * POINT_VALUE_KS:,} ks အဖြစ် Wallet ထဲသို့ ပြောင်းပြီးပါပြီ!</b>\n\n"
            f"💳 လက်ရှိ Wallet လက်ကျန်ငွေ: <b>{get_balance(user_id):,} ks</b>",
            parse_mode="HTML"
        )

    elif q.data.startswith("myorderspage_"):
        page = int(q.data.replace("myorderspage_", ""))
        text, pages, page = build_my_orders_page(user_id, page)
        context.user_data["step"] = "check_order_status"
        try:
            await q.edit_message_text(text, parse_mode="HTML", reply_markup=build_my_orders_kb(page, pages))
        except Exception:
            await q.message.reply_text(text, parse_mode="HTML", reply_markup=build_my_orders_kb(page, pages))

    # ─────────── WALLET MENU ───────────
    elif q.data == "wallet_menu":
        balance = get_balance(user_id)
        text = (
            "╔═══════════════╗\n"
            "   💳 <b>KNOX E-WALLET SYSTEM</b>\n"
            "╚═══════════════╝\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"💰 လက်ကျန်ငွေ: <b>{balance:,} ks</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Wallet ငွေဖြင့် ဝယ်ယူပါက ပြေစာမလိုပဲ အရမ်းမြန်!\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = [
            [InlineKeyboardButton("➕ ငွေဖြည့်မည် (Top-up)", callback_data="wallet_topup")],
            [InlineKeyboardButton("📊 Transaction History",  callback_data="wallet_history")],
            [InlineKeyboardButton("🔙 Back",                 callback_data="start")],
        ]
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "wallet_topup":
        text = (
            "➕ <b>Wallet ငွေဖြည့်ရန်</b>\n\n"
            "ဖြည့်လိုသော ငွေပမာဏ ရွေးချယ်ပါ သို့မဟုတ် တိုက်ရိုက် ရိုက်ထည့်ပါ။\n"
            "Min: <b>5,000 ks</b>\n\n"
            "<i>ငွေလွှဲပြီးနောက် ပြေစာ ပို့ပေးပါ - Admin မှ စစ်ပြီး ထည့်ပေးပါမည်</i>"
        )
        kb = [
            [
                InlineKeyboardButton("5,000 ks",  callback_data="topup_5000"),
                InlineKeyboardButton("10,000 ks", callback_data="topup_10000"),
            ],
            [
                InlineKeyboardButton("20,000 ks", callback_data="topup_20000"),
                InlineKeyboardButton("50,000 ks", callback_data="topup_50000"),
            ],
            [InlineKeyboardButton("🔢 ကိုယ်တိုင် ပမာဏ ရိုက်ထည့်မည်", callback_data="topup_custom")],
            [InlineKeyboardButton("🔙 Back", callback_data="wallet_menu")],
        ]
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("topup_"):
        amount_str = q.data.replace("topup_", "")
        if amount_str == "custom":
            context.user_data["step"] = "topup_custom_amount"
            await q.message.reply_text(
                "💰 ဖြည့်လိုသော ပမာဏ ရိုက်ထည့်ပါ (ks ဖြင့်)\nဥပမာ: <code>15000</code>",
                parse_mode="HTML"
            )
            return
        amount = int(amount_str)
        context.user_data["topup_amount"] = amount
        context.user_data["step"] = "topup_payment"
        payment_text = (
            f"💳 <b>Wallet Top-up</b>\n\n"
            f"💰 ဖြည့်မည့် ပမာဏ: <b>{amount:,} ks</b>\n\n"
            f"{PAYMENT_INFO}\n\n"
            f"📸 ပြေစာ ဓာတ်ပုံ ပို့ပြီးပါက Admin မှ စစ်ပြီး ငွေထည့်ပေးပါမည်"
        )
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="wallet_topup")]]
        await q.message.reply_text(payment_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "wallet_history":
        orders = get_user_orders(user_id)
        balance = get_balance(user_id)
        if orders:
            text = f"📊 <b>Transaction History</b>\n💰 လက်ကျန်ငွေ: <b>{balance:,} ks</b>\n\n"
            for oid, data in orders[-10:]:
                status_label = STATUS_EMOJI.get(data["status"], data["status"])
                text += f"🔹 #{oid} | {data['total']:,}ks | {status_label}\n"
        else:
            text = "📊 <b>Transaction History</b>\n\nOrder မရှိသေးပါ။"
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="wallet_menu")]]
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("userspage_"):
        if user_id != ADMIN_ID:
            return
        page = int(q.data.replace("userspage_", ""))
        rows = get_users_with_balance()
        total = len(rows)
        PAGE_SIZE = 30
        pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        start = page * PAGE_SIZE
        chunk = rows[start:start + PAGE_SIZE]
        text = f"👥 <b>Bot Users စာရင်း</b> (စုစုပေါင်း {total} ဦး) | Page {page+1}/{pages}\n"
        text += "─────────────────────\n"
        for uid, uname, uhandle, bal, banned in chunk:
            ban_mark = " 🚫" if banned else ""
            display = f"@{uhandle}" if uhandle else (uname or str(uid))
            text += f"👤 {html.escape(display)} (<code>{uid}</code>) | 💰 <code>{bal:,}</code> ks{ban_mark}\n"
        kb = []
        row_btns = []
        if page > 0:
            row_btns.append(InlineKeyboardButton("◀️ Prev", callback_data=f"userspage_{page-1}"))
        if page < pages - 1:
            row_btns.append(InlineKeyboardButton("▶️ Next", callback_data=f"userspage_{page+1}"))
        if row_btns:
            kb.append(row_btns)
        await q.message.reply_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb) if kb else None)

    elif q.data == "kpay_send":
        await q.edit_message_text(
            text=f"{PAYMENT_INFO}\n\n⚠️ ငွေလွှဲပြေစာဓာတ်ပုံကို 10မိနစ်အတွင်း ပို့ပေးပါခင်ဗျာ။",
            parse_mode="HTML"
        )

    # ─────────── PROMO CODE ENTRY ───────────
    elif q.data == "enter_promo":
        context.user_data["step"] = "enter_promo_code"
        kb = [[InlineKeyboardButton("⏭ မထည့်တော့ပါ (Skip)", callback_data="skip_promo")]]
        await q.message.reply_text(
            "🎟️ <b>Promo Code ရိုက်ထည့်ပါ</b>\n\n"
            "ဥပမာ - <code>KNOX10</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data == "skip_promo":
        await show_payment_method_prompt(q.message, context, user_id)

    elif q.data.startswith("walletpay_"):
        price = int(q.data.replace("walletpay_", ""))
        balance = get_balance(user_id)
        
        if balance < price:
            kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
            await q.message.reply_text(
                f"❌ <b>လက်ကျန်ငွေ မလုံလောက်ပါ!</b>\n\n"
                f"💰 သင်၏ လက်ရှိလက်ကျန်ငွေ: <b>{balance:,} ks</b>\n"
                f"💵 ကျသင့်ငွေ: <b>{price:,} ks</b>\n\n"
                f"💡 ဝယ်ယူရန်အတွက် ကျေးဇူးပြု၍ Wallet ထဲသို့‌ ငွေဖြည့်ပေးပါခင်ဗျာ။",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(kb)
            )
            return
            
        context.user_data["pay_via_wallet"] = True
        context.user_data["price"] = price
        
        await q.message.reply_text(
            f"╔═════════════════╗\n"
            f"   💳 <b>Wallet ဖြင့် ဝယ်ယူမှုအတည်ပြုခြင်း</b>\n"
            f"╚═════════════════╝\n\n"
            f"💵 ကျသင့်ငွေ: <b>{price:,} ks</b>\n"
            f"👤 သင်၏ လက်ရှိလက်ကျန်ငွေ: <b>{balance:,} ks</b>\n\n"
            f"⚠️ <i>ဤအဆင့်ပြီးပါက Wallet ထဲမှ ပိုက်ဆံအား တိုက်ရိုက်နှုတ်ယူသွားမည်ဖြစ်ပါသည်။</i>\n\n"
            f"✍️ ဝယ်ယူမှုကို အတည်ပြုရန် <b>YES</b> ဟု စာရိုက်ပြီး ပို့ပေးပါခင်ဗျာ။\n"
            f"❌ မဝယ်ယူလိုတော့ပါက /start နှိပ်ပြီး ဖျက်သိမ်းနိုင်ပါသည်။",
            parse_mode="HTML"
        )
        context.user_data["step"] = "wallet_confirm_pay"

    # ─── TikTok Single Confirm / Reject ───
    elif q.data.startswith("cf_") or q.data.startswith("rj_"):
        parts = q.data.split("_")
        action = parts[0]
        svc_code = parts[1]
        qty = parts[2]
        target_user_id = int(parts[3])
        order_id = parts[4] if len(parts) > 4 else None
        service_full = SVC_LONG.get(svc_code, svc_code)
        qty_display = "" if svc_code in ["JP", "PM"] else f" ({qty})"
        orig_caption = q.message.caption if q.message.caption else ""

        if action == "cf":
            cashback = 0
            if order_id:
                update_order_status(order_id, "completed")
                order_info = get_order_by_id(order_id)
                if order_info:
                    cashback = calculate_cashback(order_info["total"])
                    if cashback > 0:
                        add_balance(target_user_id, cashback)
                    award_points_for_order(target_user_id, order_info["total"])
                    await maybe_award_referral_bonus(context, target_user_id)
            cashback_line = f"🎁 Wallet Cashback: <b>+{cashback:,} ks</b>\n\n" if cashback > 0 else ""
            confirm_caption = (
                f"❣️ <b>Order အောင်မြင်ပါသည်!🎉</b>\n\n"
                f"{'🔖 Order ID: <b>#' + order_id + '</b>' + chr(10) if order_id else ''}\n\n"
                f"📦 {service_full}{qty_display}\n\n"
                f"{cashback_line}"
                "⏰ သင်၏ Order ကို စတင်ဆောင်ရွက်နေပြီဖြစ်၍ ခေတ္တစောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်\n\n"
                "🙏 Thank You So Much!\n\n"
                "🧑‍💻 Owner - @just_knox\n\n"
                "🛍️ နောက်ထပ်အသစ်ဝယ်ရန် /start ကိုနှိပ်ပါ"
            )
            try:
                await context.bot.send_photo(chat_id=target_user_id, photo=ORDER_CONFIRM_IMAGE, caption=confirm_caption, parse_mode="HTML")
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n✅ <b>APPROVED!</b> (Admin စနစ်မှ အော်ဒါ အတည်ပြုပြီးပါပြီ)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")
        else:
            if order_id:
                update_order_status(order_id, "rejected")
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"❌ စိတ်မကောင်းပါဘူး၊ Order <b>#{order_id}</b> ငွေလွှဲအမှားရှိ၍ ငြင်းပယ်ခံရပါသည်။\nAdmin @just_knox ထံ ဆက်သွယ်နိုင်ပါသည်။",
                    parse_mode="HTML"
                )
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n❌ <b>REJECTED!</b> (Admin စနစ်မှ အော်ဒါ ငြင်းပယ်လိုက်ပါသည်)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")

    # ─── TikTok Multi Confirm / Reject ───
    elif q.data.startswith("cfm_") or q.data.startswith("rjm_"):
        parts = q.data.split("_")
        action = parts[0]
        target_user_id = int(parts[1])
        order_id = parts[2] if len(parts) > 2 else None
        orig_caption = q.message.caption if q.message.caption else ""

        if action == "cfm":
            cashback = 0
            if order_id:
                update_order_status(order_id, "completed")
                order_info = get_order_by_id(order_id)
                if order_info:
                    cashback = calculate_cashback(order_info["total"])
                    if cashback > 0:
                        add_balance(target_user_id, cashback)
                    award_points_for_order(target_user_id, order_info["total"])
                    await maybe_award_referral_bonus(context, target_user_id)
            cashback_line = f"🎁 Wallet Cashback: <b>+{cashback:,} ks</b>\n\n" if cashback > 0 else ""
            confirm_caption = (
                f"❣️ <b>TikTok Order အောင်မြင်ပါသည်!🎉</b>\n\n"
                f"{'🔖 Order ID: <b>#' + order_id + '</b>' + chr(10) if order_id else ''}"
                f"{cashback_line}"
                "⏰သင်၏ Order ကို စတင်ဆောင်ရွက်နေပြီဖြစ်၍ သတ်မှတ်ချိန်ပြည့်တာနဲ့ ရရှိပါမည်။\n\n"
                "🙏 Thank You So Much!❣️\n\n"
                "👨‍💻 Owner - @just_knox\n\n"
                "🛍️ နောက်ထပ်အသစ်ဝယ်ရန် /start ကိုနှိပ်ပါ"
            )
            try:
                await context.bot.send_photo(chat_id=target_user_id, photo=ORDER_CONFIRM_IMAGE, caption=confirm_caption, parse_mode="HTML")
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n✅ <b>APPROVED!</b> (Admin စနစ်မှ အော်ဒါ အတည်ပြုပြီးပါပြီ)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")
        else:
            if order_id:
                update_order_status(order_id, "rejected")
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"❌ Order <b>#{order_id}</b> ငွေလွှဲအမှားရှိ၍ ငြင်းပယ်ခံရပါသည်။",
                    parse_mode="HTML"
                )
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n❌ <b>REJECTED!</b> (Admin စနစ်မှ အော်ဒါ ငြင်းပယ်လိုက်ပါသည်)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")

    # ─── Fixed-Price Confirm / Reject ───
    elif q.data.startswith("cfx_") or q.data.startswith("rjx_"):
        parts = q.data.split("_")
        action = parts[0]
        cat_code, grp_code, item_code = parts[1], parts[2], parts[3]
        target_user_id = int(parts[4])
        order_id = parts[5] if len(parts) > 5 else None
        item = get_item(cat_code, grp_code, item_code)
        item_name = item["name"]
        orig_caption = q.message.caption if q.message.caption else ""

        if action == "cfx":
            cashback = 0
            if order_id:
                update_order_status(order_id, "completed")
                order_info = get_order_by_id(order_id)
                if order_info:
                    cashback = calculate_cashback(order_info["total"])
                    if cashback > 0:
                        add_balance(target_user_id, cashback)
                    award_points_for_order(target_user_id, order_info["total"])
                    await maybe_award_referral_bonus(context, target_user_id)
            await try_auto_deliver(context, target_user_id, cat_code, grp_code, item_code)
            cashback_line = f"🎁 Wallet Cashback: <b>+{cashback:,} ks</b>\n\n" if cashback > 0 else ""
            confirm_caption = (
                f"🎉 <b>Order အောင်မြင်ပါသည်!</b>\n\n"
                f"{'🔖 Order ID: <b>#' + order_id + '</b>' + chr(10) if order_id else ''}"
                f"📦 {item_name}\n\n"
                f"{cashback_line}"
                "🥳 လူကြီးမင်းရဲ့ order အား လုပ်ဆောင်‌ပြီးပါပြီ💐 \n\n"
                "🙏 Thank You So Much!\n\n"
                "👨‍💻 Owner - @just_knox\n\n"
                "🛍️ နောက်အသစ်တစ်ခုဝယ်ရန် /start ကိုနှိပ်ပါ"
            )
            try:
                await context.bot.send_photo(chat_id=target_user_id, photo=ORDER_CONFIRM_IMAGE, caption=confirm_caption, parse_mode="HTML")
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n✅ <b>APPROVED!</b> (Admin စနစ်မှ အော်ဒါ အတည်ပြုပြီးပါပြီ)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")
        else:
            if order_id:
                update_order_status(order_id, "rejected")
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"❌ Order <b>#{order_id}</b> ({item_name}) ငွေလွှဲအမှားရှိ၍ ငြင်းပယ်ခံရပါသည်။",
                    parse_mode="HTML"
                )
                await q.edit_message_caption(
                    caption=f"{orig_caption}\n\n───────────────────\n❌ <b>REJECTED!</b> (Admin စနစ်မှ အော်ဒါ ငြင်းပယ်လိုက်ပါသည်)", 
                    reply_markup=None,
                    parse_mode="HTML"
                )
            except Exception as e:
                await q.message.reply_text(f"❌ User ဆီ စာပို့မရပါ: {e}")

    # ─── Admin: Approve Top-up ───
    elif q.data.startswith("w_ap_"):
        if user_id != ADMIN_ID:
            await q.answer("❌ Admin သာ ဤလုပ်ဆောင်ချက် ပြုလုပ်နိုင်သည်", show_alert=True)
            return
        parts = q.data.split("_")
        target_uid = int(parts[2])
        amount = int(parts[3])
        add_balance(target_uid, amount)
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"✅ <b>Wallet ငွေဖြည့်မှု အောင်မြင်ပါသည်!</b>\n\n"
                    f"💰 ဖြည့်ထားသောငွေ: <b>{amount:,} ks</b>\n"
                    f"💳 လက်ကျန်ငွေ: <b>{get_balance(target_uid):,} ks</b>\n\n"
                    "🛍️ ယခု ဝယ်ယူနိုင်ပြီ! /start နှိပ်ပါ"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await q.edit_message_caption(
            caption=f"✅ User {target_uid} ၏ Wallet တွင် {amount:,} ks ဖြည့်ပြီးပါပြီ!\nလက်ကျန်: {get_balance(target_uid):,} ks",
            reply_markup=None
        )

    # ─── Admin: Reject Top-up ───
    elif q.data.startswith("w_rj_"):
        if user_id != ADMIN_ID:
            await q.answer("❌ Admin သာ ဤလုပ်ဆောင်ချက် ပြုလုပ်နိုင်သည်", show_alert=True)
            return
        parts = q.data.split("_")
        target_uid = int(parts[2])
        amount = int(parts[3])
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=f"❌ Wallet Top-up <b>{amount:,} ks</b> ငြင်းပယ်ခံရပါသည်။\nAdmin @just_knox ထံ ဆက်သွယ်ပါ။",
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await q.edit_message_caption(
            caption=f"❌ User {target_uid} ၏ Top-up {amount:,} ks ငြင်းပယ်ပြီးပါပြီ။", 
            reply_markup=None
        )


async def show_payment_method_prompt(message_obj, context, user_id):
    """Shows the wallet/KPay payment-method choice. Shared by the fixed-item
    flow and the TikTok multi-select flow, called after the optional order note."""
    flow = context.user_data.get("flow")
    balance = get_balance(user_id)
    note = context.user_data.get("note", "")
    note_line = f"📝 <b>မှတ်ချက်:</b> {html.escape(note)}\n\n" if note else ""

    promo_code = context.user_data.get("promo_code")
    promo_line = f"🎟️ Promo <code>{promo_code}</code> အသုံးပြုပြီး: <b>-{context.user_data.get('promo_discount', 0):,} ks</b>\n" if promo_code else ""
    promo_btn_label = "🎟️ Promo Code ပြောင်းမည်" if promo_code else "🎟️ Promo Code ထည့်မည်"

    if flow == "tiktok_multi":
        total = context.user_data.get("tt_total", 0)
        context.user_data["step"] = "tt_multi_payment"
        selected = context.user_data.get("tt_selected", {})
        desc = "TikTok: " + ", ".join(
            f"{CATALOG['TT']['items'][sc]['name']}" + ("" if sc in ["JP", "PM"] else f" x{qty}")
            for sc, qty in selected.items()
        )
        context.user_data["wallet_desc"] = desc
        kb = [
            [InlineKeyboardButton(f"💳 Wallet ဖြင့်ပေးမည် (လက်ကျန်: {balance:,}ks)", callback_data=f"walletpay_{total}")],
            [InlineKeyboardButton("🖼️ KPay / Wave ဖြင့်ပေးမည်", callback_data="kpay_send")],
            [InlineKeyboardButton(promo_btn_label, callback_data="enter_promo")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]
        ]
        await message_obj.reply_text(
            f"💰 <b>ငွေပေးချေနည်း ရွေးချယ်ပါ</b>\n\n"
            f"📦 ကျသင့်ငွေ စုစုပေါင်း: <b>{total:,} ks</b>\n{promo_line}\n{note_line}"
            f"👇 အောက်ပါ Button များမှ တစ်ခုရွေးပါ",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        price = context.user_data.get("price", 0)
        item_name = context.user_data.get("item_name", "")
        context.user_data["step"] = "payment_fixed"
        context.user_data["wallet_desc"] = item_name
        kb = [
            [InlineKeyboardButton(f"💳 Wallet ဖြင့်ပေးမည် (လက်ကျန်: {balance:,}ks)", callback_data=f"walletpay_{price}")],
            [InlineKeyboardButton("🖼️ KPay / Wave ဖြင့်ပေးမည်", callback_data="kpay_send")],
            [InlineKeyboardButton(promo_btn_label, callback_data="enter_promo")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]
        ]
        await message_obj.reply_text(
            f"💰 <b>ငွေပေးချေနည်း ရွေးချယ်ပါ</b>\n\n"
            f"📦 <b>{item_name}</b>\n"
            f"💰 ကျသင့်ငွေ စုစုပေါင်း: <b>{price:,} ks</b>\n{promo_line}\n{note_line}"
            f"👇 အောက်ပါ Button များမှ တစ်ခုရွေးပါ",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= MESSAGE HANDLER ==================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    user_text = update.message.text.strip()
    user = update.effective_user
    add_user(user.id, user.full_name, user.username)
    user_id = user.id

    if user_id != ADMIN_ID and is_banned(user_id):
        await update.message.reply_text("🚫 သင့်အား Admin မှ ဤ Bot ကို အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
        return

    LINK_STEPS = {"tt_multi_link"}
    INFO_STEPS = {"info_fixed"}
    RECEIPT_STEPS = {"tt_multi_payment", "payment_fixed", "topup_payment"}

    if step in LINK_STEPS:
        if not (user_text.startswith("http") or user_text.startswith("www") or "tiktok" in user_text.lower()):
            await update.message.reply_text(
                "⚠️ <b>TikTok Video Link ပေးရန် လိုအပ်ပါသည်!</b>\n\n"
                "🔗 TikTok video link ကိုသာ ပို့ပေးပါ\n\n"
                "ဥပမာ: <code>https://www.tiktok.com/@username/video/...</code>\n\n",
                parse_mode="HTML"
            )
            return

    if step in INFO_STEPS:
        cat_code = context.user_data.get("cat_code", "")
        if cat_code == "TT" and (user_text.startswith("http") or len(user_text) < 2):
            await update.message.reply_text(
                "⚠️ <b>Game ID / Email / Account Info ပေးရပါမည်!</b>\n\n"
                "Link မဟုတ်ပဲ လိုအပ်သော ID / Email ကို ပို့ပေးပါ\n\n"
                "📸 ပြေစာ Screenshot ဤနေရာတွင် မလိုပါ",
                parse_mode="HTML"
            )
            return

    if step in RECEIPT_STEPS:
        await update.message.reply_text(
            "⚠️ <b>ပြေစာ (Screenshot) ဓာတ်ပုံ ပို့ရပါမည်!</b>\n\n"
            "📸 KPay / WavePay ငွေလွှဲပြေစာ ဓာတ်ပုံကို Gallery မှ ရွေးပြီး ပေးပို့ပါ\n"
            "✉️ စာသား (text) မဟုတ်ပဲ ဓာတ်ပုံ (photo) ပို့ရမည် ",
            parse_mode="HTML"
        )
        return

    if step == "enter_promo_code":
        promo, err = validate_promo(user_text)
        if err:
            kb = [[InlineKeyboardButton("⏭ မထည့်တော့ပါ (Skip)", callback_data="skip_promo")]]
            await update.message.reply_text(err + "\n\nထပ်ရိုက်ကြည့်ပါ (သို့) Skip နှိပ်ပါ", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
            return
        flow = context.user_data.get("flow")
        base_total = context.user_data.get("tt_total", 0) if flow == "tiktok_multi" else context.user_data.get("price", 0)
        discount = compute_discount(promo, base_total)
        context.user_data["promo_code"] = promo["code"]
        context.user_data["promo_discount"] = discount
        if flow == "tiktok_multi":
            context.user_data["tt_total"] = base_total - discount
        else:
            context.user_data["price"] = base_total - discount
        await update.message.reply_text(
            f"✅ <b>Promo Code <code>{promo['code']}</code> အောင်မြင်စွာ အသုံးပြုပြီးပါပြီ!</b>\n\n"
            f"💸 လျှော့ကြေး: <b>-{discount:,} ks</b>",
            parse_mode="HTML"
        )
        await show_payment_method_prompt(update.message, context, user_id)
        return

    if step == "pm_custom_dollar":
        if not user_text.isdigit() or int(user_text) < 1:
            await update.message.reply_text(
                "❌ ဂဏန်းတစ်ခုသာ ရိုက်ပါ (အနည်းဆုံး 1)\nဥပမာ: <code>5</code>",
                parse_mode="HTML"
            )
            return
        dollars = int(user_text)
        price = dollars * 8000
        if "tt_selected" not in context.user_data:
            context.user_data["tt_selected"] = {}
        context.user_data["tt_selected"]["PM"] = dollars
        context.user_data.pop("step", None)
        selected = context.user_data["tt_selected"]
        markup, total = build_tt_multiselect_menu(selected)
        await update.message.reply_text(
            f"✅ TikTok Promote <b>{dollars}$</b> ({price:,} ks) ထည့်သွင်းပြီးပါပြီ!\n\n"
            + build_multiselect_summary(selected)
            + "\n\n➕ ထပ်ဆောင်း Service ရွေးနိုင်သည် သို့မဟုတ် ✅ နှိပ်ပြီး ဆက်သွားပါ",
            parse_mode="HTML",
            reply_markup=markup
        )
        return

    if step == "check_order_status":
        oid = user_text.upper().replace("#", "").strip()
        data = get_order_by_id(oid)
        if data:
            if data["user_id"] != user_id:
                await update.message.reply_text("❌ ဤ Order ID သည် သင်၏ Order မဟုတ်ပါ။")
                return
            status_label = STATUS_EMOJI.get(data["status"], data["status"])
            text = (
                f"📦 <b>Order Details</b>\n\n"
                f"🔖 Order ID: <b>#{oid}</b>\n"
                f"📋 ဝန်ဆောင်မှု: {data['description']}\n"
                f"💰 ပေးချေမှု: {data['total']:,} ks\n"
                f"📊 Status: {status_label}\n"
                f"⌛ အချိန်: {data['created_at']}"
            )
            kb = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="order_status")],
                [InlineKeyboardButton("🔙 Home",    callback_data="start")],
            ]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(
                f"❌ Order ID <b>#{oid}</b> မတွေ့ပါ။\nမှန်ကန်သော ID ကို ရိုက်ထည့်ပါ။\nဥပမာ: <code>KNOX-1234</code>",
                parse_mode="HTML"
            )
        context.user_data["step"] = "check_order_status"
        return

    if step == "topup_custom_amount":
        if not user_text.isdigit() or int(user_text) < 5000:
            await update.message.reply_text("❌ အနည်းဆုံး 5,000 ks ဖြည့်ရပါသည်။ ဂဏန်းသာ ရိုက်ပါ။")
            return
        amount = int(user_text)
        context.user_data["topup_amount"] = amount
        context.user_data["step"] = "topup_payment"
        payment_text = (
            f"💳 <b>Wallet Top-up</b>\n\n"
            f"💰 ဖြည့်မည့် ပမာဏ: <b>{amount:,} ks</b>\n\n"
            f"{PAYMENT_INFO}\n\n"
            "⚠️ ပြေစာ ဓာတ်ပုံ ပို့ပြီးပါက Admin မှ စစ်ပြီး Balance တင်ပေးပါမည်"
        )
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="wallet_topup")]]
        await update.message.reply_text(payment_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        return

    if step == "wallet_confirm_pay":
        if user_text.upper() == "YES":
            price = context.user_data.get("price", 0)

            if deduct_balance(user_id, price):
                desc = context.user_data.get("wallet_desc", "ဝယ်ယူမှု")
                note = context.user_data.get("note", "")
                order_id = create_order(user_id, user.full_name, desc, price, note)
                update_order_status(order_id, "processing")

                promo_code = context.user_data.get("promo_code")
                if promo_code:
                    consume_promo(promo_code)
                pts_earned = award_points_for_order(user_id, price)
                await maybe_award_referral_bonus(context, user_id)
                if context.user_data.get("flow") == "fixed":
                    await try_auto_deliver(
                        context, user_id,
                        context.user_data.get("cat_code", ""),
                        context.user_data.get("grp_code", "-"),
                        context.user_data.get("item_code", "")
                    )

                await update.message.reply_photo(
                    photo=ORDER_CONFIRM_IMAGE,
                    caption=(
                        "╔═══════════════════╗\n"
                        "  🎉 <b>Wallet ဖြင့် ဝယ်ယူမှု အောင်မြင်ပါသည်!</b> 🎉\n"
                        "╚═══════════════════╝\n\n"
                        f"🔖 <b>Order ID:</b> <code>#{order_id}</code>\n"
                        f"📦 <b>အမျိုးအစား:</b> <code>{desc}</code>\n"
                        f"💵 <b>ကျသင့်ငွေ:</b> <code>{price:,} ks</code>\n"
                        f"💳 <b>ကျန်ရှိသော လက်ကျန်ငွေ:</b> <code>{get_balance(user_id):,} ks</code>\n"
                        + (f"🏆 <b>Points ရရှိ:</b> <code>+{pts_earned}</code>\n" if pts_earned > 0 else "") +
                        "─────────────────────\n"
                        "⚙️ <i>သင်၏ Order ကို စတင်ဆောင်ရွက်နေပြီဖြစ်၍ ခေတ္တစောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။</i>\n\n"
                        "🙏 <b>နောက်အသစ်တစ်ခု ဝယ်ရန် /start ကိုနှိပ်ပါ!</b>\n"
                        "─────────────────────"
                    ),
                    parse_mode="HTML"
                )
                
                detail_text = ""
                link = context.user_data.get("link", "")
                info_text = context.user_data.get("info_text", "")
                if link:
                    detail_text += f"🔗 <b>Link (Tap to Copy):</b>\n<code>{html.escape(link)}</code>\n\n"
                if info_text:
                    detail_text += f"🧾 <b>Player Info (Tap to Copy):</b>\n<code>{html.escape(info_text)}</code>\n\n"
                if note:
                    detail_text += f"📝 <b>Customer Note:</b>\n<code>{html.escape(note)}</code>\n\n"

                admin_text = (
                    f"💳 <b>WALLET ORDER (ငွေချေပြီး)</b>\n"
                    f"────────────────────\n"
                    f"🔖 <b>Order ID:</b> <code>#{order_id}</code>\n"
                    f"👤 <b>Customer:</b> {html.escape(user.full_name)} (ID: <code>{user.id}</code>)\n"
                    f"📦 <b>Details:</b> <code>{desc}</code>\n"
                    f"💰 <b>Total Price:</b> <code>{price:,}</code> ks\n"
                    f"────────────────────\n"
                    f"{detail_text}"
                )
                kb = [[InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user.id}")]]
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
            else:
                kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
                await update.message.reply_text(
                    f"❌ Wallet ငွေ မလုံလောက်ပါ!\n💰 လက်ကျန်: {get_balance(user_id):,} ks\n💸 လိုအပ်သည်: {price:,} ks\n\n"
                    "💳 /start → My Wallet → ငွေ ဖြည့်မည် ကို နှိပ်ပါ",
                    reply_markup=InlineKeyboardMarkup(kb)
                )
            context.user_data.clear()
        else:
            await update.message.reply_text("❌ ဖျက်သိမ်းလိုက်ပါသည်။ /start နှိပ်ပါ")
            context.user_data.clear()
        return

    if step == "tt_multi_link":
        context.user_data["link"] = user_text
        context.user_data["step"] = "order_note"
        note_kb = [[InlineKeyboardButton("⏭ Note မထည့်တော့ပါ (Skip)", callback_data="note_skip")]]
        await update.message.reply_text(
            "📝 <b>Order အတွက် မှတ်ချက် (Note) ရေးလိုပါသလား?</b>\n\n"
            "ဥပမာ - မြန်မြန်လေးရအောင်လုပ်ပေးပါ,ဘာညာ...\n\n"
            "မလိုအပ်ပါက အောက်က Skip ခလုတ်ကို နှိပ်ပါ",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(note_kb)
        )
        return

    elif step == "info_fixed":
        context.user_data["info_text"] = user_text
        context.user_data["step"] = "order_note"
        note_kb = [[InlineKeyboardButton("⏭ Note မထည့်တော့ပါ (Skip)", callback_data="note_skip")]]
        await update.message.reply_text(
            "📝 <b>Order အတွက် မှတ်ချက် (Note) ရေးလိုပါသလား?</b>\n\n"
            "ဥပမာ - မြန်မြန်လေးရအောင်လုပ်ပေးပါ,ဘာညာ...\n\n"
            "မလိုအပ်ပါက အောက်က Skip ခလုတ်ကို နှိပ်ပါ",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(note_kb)
        )
        return

    elif step == "order_note":
        note_text = user_text.strip()
        if note_text.lower() not in ("skip", "no", "none", "-", "မလို"):
            context.user_data["note"] = note_text
        await show_payment_method_prompt(update.message, context, user_id)
        return

    elif step is None:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        if "ai_history" not in context.user_data:
            context.user_data["ai_history"] = []
        history = context.user_data["ai_history"]
        ai_reply = ask_ai(user_text, history)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": ai_reply})
        if len(history) > 6:
            context.user_data["ai_history"] = history[-6:]
        await update.message.reply_text(ai_reply)


# ================= PHOTO HANDLER ====================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.full_name, user.username)
    user_id = user.id

    if user_id != ADMIN_ID and is_banned(user_id):
        await update.message.reply_text("🚫 သင့်အား Admin မှ ဤ Bot ကို အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
        return

    step = context.user_data.get("step")

    VALID_PHOTO_STEPS = {"topup_payment", "tt_multi_payment", "payment_fixed"}

    if step not in VALID_PHOTO_STEPS:
        if step == "tt_multi_link":
            await update.message.reply_text(
                "⚠️ <b>ဤနေရာတွင် ငွေလွှဲပြေစာ မပို့ရပါ!</b>\n\n"
                "🔗 TikTok video <b>Link</b> ကိုသာ text ဖြင့် ပို့ပေးပါ\n"
                "ဥပမာ: <code>https://www.tiktok.com/video/...</code>",
                parse_mode="HTML"
            )
        elif step == "info_fixed":
            await update.message.reply_text(
                "⚠️ <b>ဤနေရာတွင် ငွေလွှဲပြေစာ မပို့ရပါ!</b>\n\n"
                "📝 Game ID / Email / Account Info ကို <b>text</b> ဖြင့်သာ ရိုက်ပေးပါ",
                parse_mode="HTML"
            )
        elif step == "wallet_confirm_pay":
            await update.message.reply_text(
            "⚠️ <b>ဤနေရာတွင် ငွေလွှဲပြေစာ မလိုပါ!</b>\n\n"
                "✅ Wallet ဖြင့် ပေးချေရန် <b>YES</b> ဟု စာရိုက်ပြီး ပို့ပေးပါ",
                parse_mode="HTML"
            )
        elif step == "order_note":
            kb = [[InlineKeyboardButton("⏭ Note မထည့်တော့ပါ (Skip)", callback_data="note_skip")]]
            await update.message.reply_text(
                "⚠️ <b>Note အတွက် ဓာတ်ပုံ မလိုပါ!</b>\n\n"
                "📝 မှတ်ချက်ကို <b>text</b> ဖြင့်သာ ရိုက်ထည့်ပါ (သို့) Skip ကိုနှိပ်ပါ",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        return

    if step == "topup_payment":
        amount = context.user_data.get("topup_amount", 0)
        
        pending_caption = (
            f"⏳ <b>Admin မှ စစ်ဆေးနေပါပြီ</b>\n\n"
            f"💰 <b>ဖြည့်မည့်ငွေ: {amount:,} ks</b>\n\n"
            "🌟 ငွေလွှဲပြေစာ မှန်ကန်ပါက Wallet ထဲသို့ ငွေရောက်ရှိလာပါမည်\n\n"
            "❣️ Thank You So Much ❤️"
        )
        try:
            await update.message.reply_photo(photo=ORDER_PENDING_IMAGE, caption=pending_caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(text=pending_caption, parse_mode="HTML")

        admin_text = (
            f"🔔 <b>Wallet Top-up Request</b>\n"
            f"────────────────────\n"
            f"👤 <b>Customer:</b> {html.escape(user.full_name)}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"💰 <b>Amount:</b> {amount:,} ks\n"
            f"────────────────────"
        )
        kb = [
            [InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user.id}")],
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"w_ap_{user.id}_{amount}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"w_rj_{user.id}_{amount}"),
            ]
        ]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data.clear()

    elif step == "tt_multi_payment":
        selected = context.user_data.get("tt_selected", {})
        total = context.user_data.get("tt_total", 0)
        link  = context.user_data.get("link", "")

        service_lines = []
        for svc_code, qty in selected.items():
            item = CATALOG["TT"]["items"][svc_code]
            price = item["tiers"].get(qty, 0)
            qty_str = "" if svc_code in ["JP", "PM"] else f" x{qty//1000}k" if qty >= 1000 else f" x{qty}"
            service_lines.append(f"  {item['emoji']} {item['name']}{qty_str} = {price:,}ks")
        services_text = "\n".join(service_lines)
        
        desc = "TikTok: " + ", ".join(
            f"{CATALOG['TT']['items'][sc]['name']}" + ("" if sc in ["JP", "PM"] else f" x{qty}")
            for sc, qty in selected.items()
        )

        note = context.user_data.get("note", "")
        order_id = create_order(user_id, user.full_name, desc, total, note)
        promo_code = context.user_data.get("promo_code")
        if promo_code:
            consume_promo(promo_code)

        pending_caption = (
            f"⏳ <b>Admin မှ စစ်ဆေးနေပါပြီ</b>\n\n"
            f"🔖 <b>သင်၏ Order ID: #{order_id}</b>\n\n"
            "🌟 စစ်ပြီး Order တင်ပြီးပါက စာပြန်ပို့ပေးပါမည်\n\n"
            "📦 Order Status စစ်ရန် /start → 📦 My ordersကိုနှိပ်ပါ\n\n"
            "🥳 Thank You So Much ❤️"
        )
        try:
            await update.message.reply_photo(photo=ORDER_PENDING_IMAGE, caption=pending_caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(text=pending_caption, parse_mode="HTML")

        note_line = f"📝 <b>Customer Note:</b>\n<code>{html.escape(note)}</code>\n" if note else ""
        admin_text = (
            f"🔔 <b>TikTok Multi-Service Order အသစ်</b>\n"
            f"────────────────────\n"
            f"🔖 <b>Order ID:</b> <code>#{order_id}</code>\n"
            f"👤 <b>Customer:</b> {html.escape(user.full_name)}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"📦 <b>Services:</b>\n{services_text}\n"
            f"💰 <b>Total:</b> {total:,} ks\n"
            f"────────────────────\n"
            f"🔗 <b>Link (Tap to copy ):</b>\n<code>{html.escape(link)}</code>\n"
            f"{note_line}"
        )
        kb = [
            [InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user.id}")],
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"cfm_{user.id}_{order_id}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"rjm_{user.id}_{order_id}"),
            ]
        ]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data.clear()

    elif step == "payment_fixed":
        cat_code  = context.user_data["cat_code"]
        grp_code  = context.user_data["grp_code"]
        item_code = context.user_data["item_code"]
        item_name = context.user_data["item_name"]
        price     = context.user_data["price"]
        info_text = context.user_data["info_text"]
        cat = CATALOG[cat_code]

        note = context.user_data.get("note", "")
        desc = f"{cat['title']} - {item_name}"
        order_id = create_order(user_id, user.full_name, desc, price, note)
        promo_code = context.user_data.get("promo_code")
        if promo_code:
            consume_promo(promo_code)

        pending_caption = (
            f"⏳ <b>Admin မှ စစ်ဆေးနေပါပြီ</b>\n\n"
            f"🔖 <b>သင်၏ Order ID: #{order_id}</b>\n\n"
            "🌟 စစ်ပြီးပါက စာပြန်ပို့ပေးပါမည်\n\n"
            "📦 Order Status: /start → 📦 Order Status စစ်ရန်\n\n"
            "👾 Thank You So Much ❤️"
        )
        try:
            await update.message.reply_photo(photo=ORDER_PENDING_IMAGE, caption=pending_caption, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(text=pending_caption, parse_mode="HTML")

        note_line = f"\n📝 <b>Customer Note:</b>\n<code>{html.escape(note)}</code>" if note else ""
        admin_text = (
            f"🔔 <b>Order အသစ်</b>\n"
            f"─────────────────────\n"
            f"🔖 <b>Order ID:</b> <code>#{order_id}</code>\n"
            f"👤 <b>Customer:</b> {html.escape(user.full_name)}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"🗂 <b>Category:</b> {cat['title']}\n"
            f"📦 <b>Item:</b> {item_name}\n"
            f"💰 <b>Total:</b> {price:,} ks\n"
            f"─────────────────────\n"
            f"🧾 <b>Info (Tap to copy ):</b>\n<code>{html.escape(info_text)}</code>"
            f"{note_line}"
        )
        kb = [
            [InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user.id}")],
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"cfx_{cat_code}_{grp_code}_{item_code}_{user.id}_{order_id}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"rjx_{cat_code}_{grp_code}_{item_code}_{user.id}_{order_id}"),
            ]
        ]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        context.user_data.clear()
        
# ================= MAIN =================
if __name__ == "__main__":
    import time

    while True:
        try:
            app = ApplicationBuilder().token(BOT_TOKEN).build()

            app.add_handler(CommandHandler("start",  start))
            app.add_handler(CommandHandler("help",   help_command))
            app.add_handler(CommandHandler("review", review))
            app.add_handler(CommandHandler("status", status_command))
            app.add_handler(CommandHandler("bc",     broadcast))
            app.add_handler(CommandHandler("report", admin_report))
            app.add_handler(CommandHandler("users",  admin_users))
            app.add_handler(CommandHandler("pending", admin_pending))
            app.add_handler(CommandHandler("ban",     admin_ban))
            app.add_handler(CommandHandler("unban",   admin_unban))
            app.add_handler(CommandHandler("banned",  admin_banned_list))
            app.add_handler(CommandHandler("find",    admin_find))
            app.add_handler(CommandHandler("msg",     admin_msg))
            app.add_handler(CommandHandler("addbalance", admin_addbalance))
            app.add_handler(CommandHandler("top",     admin_top))
            app.add_handler(CommandHandler("addstock", admin_addstock))
            app.add_handler(CommandHandler("stock",    admin_stock))
            app.add_handler(CommandHandler("addpromo", admin_addpromo))
            app.add_handler(CommandHandler("promos",   admin_promos))
            app.add_handler(CommandHandler("delpromo", admin_delpromo))
            app.add_handler(CommandHandler("dashboard", admin_dashboard))
            app.add_handler(CommandHandler("export",   admin_export))
            app.add_handler(CallbackQueryHandler(buttons))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
            app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

            print("🚀 Knox All-in-One Shop Bot v2.4 is running!")
            print("✅ SQLite Persistent Database: Active (knox_store.db + users table)")
            print("✅ MLBB Weekly Pass Custom Qty (+ / -): Active")
            print("✅ Human-Like AI Persona (gpt-oss-120b): Active")
            print("✅ Admin: /msg, /addbalance, /top: Active")
            print("✅ Referral Program (/start ref_CODE, auto bonus): Active")
            print("✅ Loyalty Points (earn + redeem to wallet): Active")
            print("✅ Promo Codes (/addpromo, /promos, /delpromo): Active")
            print("✅ Auto-Delivery & Stock Alerts (/addstock, /stock): Active")
            print("✅ Admin Dashboard & CSV Export (/dashboard, /export): Active")
            print("✅ Auto-Restart on Crash: Active")

            app.run_polling(drop_pending_updates=True)

        except Exception as e:
            logging.error(f"❌ Bot crashed: {e}. Restarting in 5 seconds...")
            time.sleep(5)
            continue