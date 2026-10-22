#!/usr/bin/env python3
"""
ElevateX Host V9 — Premium Python Stability Hosting Manager
════════════════════════════════════════════════════════════
⚠️  WARNING: Executes uploaded Python code. Run only inside an
    isolated container/VM — this is NOT a security sandbox.

    Python 3.11+  |  python-telegram-bot[job-queue]>=22,<23
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import shutil
import shlex
import signal
import subprocess
import hashlib
import sqlite3
import platform
import sys
import time
import zipfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, InputFile,
    KeyboardButton, ReplyKeyboardMarkup, Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application, ApplicationBuilder, CallbackQueryHandler,
    ChatMemberHandler, CommandHandler, ContextTypes, MessageHandler, filters,
)

# ═════════════════════════════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

TOKEN = os.getenv("BOT_TOKEN", "8931882023:AAH5mVhRGQbTpLYQ_57vcNIfuXPxWQZ0xXA")
OWNER_ID = int(os.getenv("OWNER_ID", "5659752731"))
ACCESS_PASSWORD = "@Ali.1122"

BRAND_NAME = "ITACHI UCHIHA"
OWNER_NAME = "ALI HAIDER"
OWNER_USERNAME = "@Ali00sona1"

# ── Force-join channel ────────────────────────────────────────────
MAIN_CHANNEL_NAME = "ITACHI-UCHIA"
MAIN_CHANNEL_LINK = "https://t.me/itachialive321"
MAIN_CHANNEL_USERNAME = "@ITACHIALIVE321"

# ── Force-join group (PRIVATE) ────────────────────────────────────
SUPPORT_GROUP_NAME     = os.getenv("SUPPORT_GROUP_NAME",     "TEAM UCHIHA")
SUPPORT_GROUP_LINK     = os.getenv("SUPPORT_GROUP_LINK",     "https://t.me/+WPw5Oypqn7g2ODA0")
SUPPORT_GROUP_USERNAME = os.getenv("SUPPORT_GROUP_USERNAME", "-1004389556928")

SUPPORT_LINK = "https://t.me/Ali00sona1"

MAX_FILE_MB = 20
MAX_ZIP_EXPANDED_MB = 100
DEFAULT_CREDITS = 2
CREDIT_PER_UPLOAD = 1
PREMIUM_BONUS_CREDITS = 100
DAILY_UPLOAD_LIMIT = 1
PREMIUM_DAILY_UPLOAD_LIMIT = 50
MAX_RUNNING_PER_USER = 2
PREMIUM_MAX_RUNNING_PER_USER = 10
LAUNCH_CHECK_SECONDS = 2.0
MAX_LOG_CHARS = 3000
MAX_RESTARTS = 3
INSTALL_TIMEOUT_SECONDS = 180
MAX_INSTALL_OUTPUT_CHARS = 3500
DEPENDENCY_TIMEOUT_SECONDS = int(os.getenv("DEPENDENCY_TIMEOUT_SECONDS", "300"))
DEFAULT_PROJECT_RAM_MB = int(os.getenv("DEFAULT_PROJECT_RAM_MB", "256"))
DEFAULT_PROJECT_CPU_PERCENT = int(os.getenv("DEFAULT_PROJECT_CPU_PERCENT", "50"))
AUTO_INSTALL_DEPENDENCIES = os.getenv("AUTO_INSTALL_DEPENDENCIES", "1") == "1"
SECURITY_SCAN_ENABLED = os.getenv("SECURITY_SCAN_ENABLED", "1") == "1"
DOCKER_MODE = os.getenv("DOCKER_MODE", "0") == "1"
ENFORCE_RESOURCE_LIMITS = os.getenv("ENFORCE_RESOURCE_LIMITS", "1") == "1"
PROJECT_PROCESS_LIMIT = int(os.getenv("PROJECT_PROCESS_LIMIT", "0"))
ENFORCE_ADDRESS_SPACE_LIMIT = os.getenv("ENFORCE_ADDRESS_SPACE_LIMIT", "0") == "1"
PROJECT_OPEN_FILES_LIMIT = int(os.getenv("PROJECT_OPEN_FILES_LIMIT", "512"))
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
WATCHDOG_INTERVAL_DEFAULT = max(20, int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "40")))
LOG_ROTATE_MAX_MB = max(1, int(os.getenv("LOG_ROTATE_MAX_MB", "2")))
LOG_ROTATE_KEEP_MB = max(1, int(os.getenv("LOG_ROTATE_KEEP_MB", "1")))
DEFAULT_STORAGE_QUOTA_MB = max(50, int(os.getenv("DEFAULT_STORAGE_QUOTA_MB", "500")))
PANEL_REMINDER_HOURS = max(24, int(os.getenv("PANEL_REMINDER_HOURS", "72")))
CRASH_WINDOW_SECONDS = max(60, int(os.getenv("CRASH_WINDOW_SECONDS", "600")))
CRASH_LIMIT = max(2, int(os.getenv("CRASH_LIMIT", "5")))
HEALTH_PORT = int(os.getenv("PORT", os.getenv("HEALTH_PORT", "8080")))
KEEPALIVE_INTERVAL_DEFAULT = max(30, min(45, int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "40"))))
KEEPALIVE_URL_ENV = os.getenv("KEEPALIVE_URL", "").strip()


def _auto_public_url() -> str:
    direct = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if direct:
        return direct.rstrip("/") + "/health"
    for key in ("RAILWAY_PUBLIC_DOMAIN", "KOYEB_PUBLIC_DOMAIN"):
        domain = os.getenv(key, "").strip()
        if domain:
            if not domain.startswith(("http://", "https://")):
                domain = "https://" + domain
            return domain.rstrip("/") + "/health"
    fly = os.getenv("FLY_APP_NAME", "").strip()
    if fly:
        return f"https://{fly}.fly.dev/health"
    return ""


KEEPALIVE_URL_DEFAULT = KEEPALIVE_URL_ENV or _auto_public_url()

FORCE_JOIN_ENABLED = True
FORCE_JOIN_CACHE_TTL = max(300, int(os.getenv("FORCE_JOIN_CACHE_TTL", "3600")))
AUTO_RESTART_ENABLED = False
MAINTENANCE_MODE_DEFAULT = False

# ═════════════════════════════════════════════════════════════════════════════
# 📁  PATHS & LOGGING
# ═════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DATA_FILE = BASE_DIR / "bot_data.json"
PROJECTS_FILE = BASE_DIR / "projects.json"
V7_DATA_FILE = BASE_DIR / "v7_data.json"
V9_DB_FILE = BASE_DIR / "elevatex_v9.db"
JOIN_CACHE_FILE = BASE_DIR / "join_cache.json"
PROJECT_BACKUPS_DIR = BASE_DIR / "project_backups"
BACKUPS_DIR = BASE_DIR / "backups"

for d in (DOWNLOADS_DIR, PROJECT_BACKUPS_DIR, BACKUPS_DIR):
    d.mkdir(parents=True, exist_ok=True)

START_TIME = time.time()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("ElevateXHostV9")

# ═════════════════════════════════════════════════════════════════════════════
# 🧩  DATA MODELS & GLOBAL STATE
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class ScriptProcess:
    display_name: str
    entry_file: str
    folder: str
    log_path: str
    proc: subprocess.Popen[Any] | None = None
    started_at: float = field(default_factory=time.time)
    restarts: int = 0
    auto_restart: bool = AUTO_RESTART_ENABLED
    desired_running: bool = False

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    @property
    def pid(self) -> str:
        return str(self.proc.pid) if self.proc else "—"

    @property
    def exit_code(self) -> str:
        if self.proc is None:
            return "Not started"
        return "Running" if self.proc.poll() is None else str(self.proc.returncode)

    def serialize(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name, "entry_file": self.entry_file,
            "folder": self.folder, "log_path": self.log_path,
            "started_at": self.started_at, "restarts": self.restarts,
            "auto_restart": self.auto_restart,
            "was_running": bool(self.running or self.desired_running),
        }


approved_users: set[int] = set()
premium_users: set[int] = set()
banned_users: set[int] = set()
user_stats: dict[str, dict[str, Any]] = {}
user_credits: dict[str, int] = {}
custom_daily_limits: dict[str, int] = {}
custom_running_limits: dict[str, int] = {}
maintenance_mode = MAINTENANCE_MODE_DEFAULT

premium_expiry: dict[str, str] = {}
user_plans: dict[str, str] = {}
redeem_codes: dict[str, dict[str, Any]] = {}
project_envs: dict[str, dict[str, str]] = {}
project_settings: dict[str, dict[str, Any]] = {}
audit_log: list[dict[str, Any]] = []
admin_roles: dict[str, str] = {}
user_storage_limits: dict[str, int] = {}
watchdog_enabled: bool = True
watchdog_interval: int = WATCHDOG_INTERVAL_DEFAULT
watchdog_last_epoch: float = 0.0
watchdog_restarts: int = 0
panel_reminder_enabled: bool = True
panel_last_confirmed_at: float = time.time()
panel_last_reminder_at: float = 0.0
brand_footer: str = "⚡ Powered by ITACHI UCHIHA"

keepalive_enabled: bool = False
keepalive_url: str = KEEPALIVE_URL_DEFAULT
keepalive_interval: int = KEEPALIVE_INTERVAL_DEFAULT
keepalive_last_status: str = "Not run yet"
keepalive_last_at: str = "—"
keepalive_failures: int = 0
keepalive_last_epoch: float = 0.0
health_server_started: bool = False

running_scripts: dict[int, list[ScriptProcess]] = {}
pending_project_names: dict[int, ScriptProcess] = {}
user_locks: dict[int, asyncio.Lock] = {}

chat_membership: dict[str, dict[str, dict[str, Any]]] = {}
forcejoin_bypass_users: set[int] = set()

# ═════════════════════════════════════════════════════════════════════════════
# 💾  STORAGE
# ═════════════════════════════════════════════════════════════════════════════


def lock_for(user_id: int) -> asyncio.Lock:
    return user_locks.setdefault(user_id, asyncio.Lock())


def load_data() -> None:
    global approved_users, premium_users, banned_users
    global user_stats, user_credits, custom_daily_limits, custom_running_limits, maintenance_mode
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text("utf-8"))
            approved_users = {int(x) for x in data.get("approved_users", [])}
            premium_users = {int(x) for x in data.get("premium_users", [])}
            banned_users = {int(x) for x in data.get("banned_users", [])}
            user_stats = dict(data.get("user_stats", {}))
            user_credits = {str(k): int(v) for k, v in data.get("user_credits", {}).items()}
            custom_daily_limits = {str(k): int(v) for k, v in data.get("custom_daily_limits", {}).items()}
            custom_running_limits = {str(k): int(v) for k, v in data.get("custom_running_limits", {}).items()}
            maintenance_mode = bool(data.get("maintenance_mode", MAINTENANCE_MODE_DEFAULT))
        except Exception:
            logger.exception("Could not load bot data")

    if PROJECTS_FILE.exists():
        try:
            data = json.loads(PROJECTS_FILE.read_text("utf-8"))
            for uid, rows in data.items():
                items: list[ScriptProcess] = []
                for row in rows:
                    entry, folder = Path(row["entry_file"]), Path(row["folder"])
                    if entry.exists() and folder.exists():
                        items.append(ScriptProcess(
                            display_name=row.get("display_name", entry.name),
                            entry_file=str(entry), folder=str(folder),
                            log_path=row.get("log_path", str(folder / "runtime.log")),
                            started_at=float(row.get("started_at", time.time())),
                            restarts=int(row.get("restarts", 0)),
                            auto_restart=bool(row.get("auto_restart", AUTO_RESTART_ENABLED)),
                            desired_running=bool(row.get("was_running", False)),
                        ))
                running_scripts[int(uid)] = items
        except Exception:
            logger.exception("Could not load project registry")


def save_data() -> None:
    payload = {
        "approved_users": sorted(approved_users),
        "premium_users": sorted(premium_users),
        "banned_users": sorted(banned_users),
        "user_stats": user_stats, "user_credits": user_credits,
        "custom_daily_limits": custom_daily_limits,
        "custom_running_limits": custom_running_limits,
        "maintenance_mode": maintenance_mode,
    }
    temp = DATA_FILE.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        temp.replace(DATA_FILE)
        if V9_DB_FILE.exists():
            sync_v9_database()
    except Exception:
        logger.exception("Could not save bot data")
        temp.unlink(missing_ok=True)


def save_projects() -> None:
    payload = {str(uid): [i.serialize() for i in items] for uid, items in running_scripts.items()}
    temp = PROJECTS_FILE.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        temp.replace(PROJECTS_FILE)
        if V9_DB_FILE.exists():
            sync_v9_database()
    except Exception:
        logger.exception("Could not save project registry")
        temp.unlink(missing_ok=True)


def load_v7_data() -> None:
    global premium_expiry, user_plans, redeem_codes, project_envs, project_settings
    global audit_log, admin_roles, user_storage_limits, watchdog_enabled, watchdog_interval
    global panel_reminder_enabled, panel_last_confirmed_at, panel_last_reminder_at, brand_footer
    global keepalive_enabled, keepalive_url, keepalive_interval
    if not V7_DATA_FILE.exists():
        return
    try:
        data = json.loads(V7_DATA_FILE.read_text("utf-8"))
        premium_expiry = dict(data.get("premium_expiry", {}))
        user_plans = dict(data.get("user_plans", {}))
        redeem_codes = dict(data.get("redeem_codes", {}))
        project_envs = {str(k): dict(v) for k, v in data.get("project_envs", {}).items()}
        project_settings = {str(k): dict(v) for k, v in data.get("project_settings", {}).items()}
        audit_log = list(data.get("audit_log", []))[-2000:]
        admin_roles = dict(data.get("admin_roles", {}))
        user_storage_limits = {str(k): int(v) for k, v in data.get("user_storage_limits", {}).items()}
        wd = data.get("watchdog", {})
        watchdog_enabled = bool(wd.get("enabled", True))
        watchdog_interval = max(20, int(wd.get("interval", WATCHDOG_INTERVAL_DEFAULT)))
        pr = data.get("panel_reminder", {})
        panel_reminder_enabled = bool(pr.get("enabled", True))
        panel_last_confirmed_at = float(pr.get("last_confirmed_at", time.time()))
        panel_last_reminder_at = float(pr.get("last_reminder_at", 0.0))
        brand_footer = str(data.get("brand_footer", brand_footer))
        ka = data.get("keepalive", {})
        keepalive_enabled = bool(ka.get("enabled", False))
        keepalive_url = str(ka.get("url", KEEPALIVE_URL_DEFAULT) or KEEPALIVE_URL_DEFAULT)
        keepalive_interval = max(30, min(45, int(ka.get("interval", KEEPALIVE_INTERVAL_DEFAULT))))
    except Exception:
        logger.exception("Could not load V7 data")


def save_v7_data() -> None:
    payload = {
        "premium_expiry": premium_expiry, "user_plans": user_plans,
        "redeem_codes": redeem_codes, "project_envs": project_envs,
        "project_settings": project_settings, "audit_log": audit_log[-2000:],
        "admin_roles": admin_roles, "user_storage_limits": user_storage_limits,
        "watchdog": {"enabled": watchdog_enabled, "interval": watchdog_interval},
        "panel_reminder": {
            "enabled": panel_reminder_enabled,
            "last_confirmed_at": panel_last_confirmed_at,
            "last_reminder_at": panel_last_reminder_at,
        },
        "brand_footer": brand_footer,
        "keepalive": {"enabled": keepalive_enabled, "url": keepalive_url, "interval": keepalive_interval},
    }
    temp = V7_DATA_FILE.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        temp.replace(V7_DATA_FILE)
        if V9_DB_FILE.exists():
            sync_v9_database()
    except Exception:
        logger.exception("Could not save V7 data")
        temp.unlink(missing_ok=True)


def load_join_cache() -> None:
    global chat_membership, forcejoin_bypass_users
    if not JOIN_CACHE_FILE.exists():
        return
    try:
        data = json.loads(JOIN_CACHE_FILE.read_text("utf-8"))
        forcejoin_bypass_users = {int(x) for x in data.get("bypass", [])}
        if "chat_membership" in data:
            chat_membership = data["chat_membership"]
        elif "verified" in data:
            for k, ts in data["verified"].items():
                chat_membership[k] = {
                    "channel": {"joined": True, "at": float(ts)},
                    "group": {"joined": True, "at": float(ts)},
                }
            logger.info("Migrated %d join-cache entries", len(chat_membership))
    except Exception:
        logger.exception("Could not load join cache")


def save_join_cache() -> None:
    payload = {"chat_membership": chat_membership, "bypass": sorted(forcejoin_bypass_users)}
    temp = JOIN_CACHE_FILE.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        temp.replace(JOIN_CACHE_FILE)
    except Exception:
        logger.exception("Could not save join cache")
        temp.unlink(missing_ok=True)


def init_v9_database() -> None:
    try:
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS snapshots (name TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, actor INTEGER, action TEXT, target TEXT, detail TEXT)")
            db.commit()
    except Exception:
        logger.exception("Could not initialize V9 SQLite database")


def sync_v9_database() -> None:
    try:
        snapshots = {
            "users": {
                "approved_users": sorted(approved_users),
                "premium_users": sorted(premium_users),
                "banned_users": sorted(banned_users),
                "user_stats": user_stats, "user_credits": user_credits,
                "custom_daily_limits": custom_daily_limits,
                "custom_running_limits": custom_running_limits,
                "maintenance_mode": maintenance_mode,
            },
            "projects": {str(uid): [x.serialize() for x in rows] for uid, rows in running_scripts.items()},
            "premium": {
                "premium_expiry": premium_expiry, "user_plans": user_plans,
                "redeem_codes": redeem_codes, "project_envs": project_envs,
                "project_settings": project_settings, "admin_roles": admin_roles,
                "user_storage_limits": user_storage_limits,
            },
        }
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(V9_DB_FILE) as db:
            for name, payload in snapshots.items():
                db.execute(
                    "INSERT INTO snapshots(name,payload,updated_at) VALUES(?,?,?) "
                    "ON CONFLICT(name) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at",
                    (name, json.dumps(payload, ensure_ascii=False), now),
                )
            db.commit()
    except Exception:
        logger.exception("Could not sync V9 SQLite database")


def db_event(actor: int, action: str, target: str = "", detail: str = "") -> None:
    try:
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute(
                "INSERT INTO events(created_at,actor,action,target,detail) VALUES(?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), actor, action, target, detail[:1000]),
            )
            db.commit()
    except Exception:
        logger.exception("Could not write V9 database event")


def audit(actor: int, action: str, target: str = "", detail: str = "") -> None:
    audit_log.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "actor": actor, "action": action, "target": target, "detail": detail[:500],
    })
    save_v7_data()
    db_event(actor, action, target, detail)


# ═════════════════════════════════════════════════════════════════════════════
# 🛠️  HELPERS
# ═════════════════════════════════════════════════════════════════════════════


def esc(value: Any) -> str:
    return html.escape(str(value))


def progress_bar(current: int, maximum: int, length: int = 10) -> str:
    if maximum <= 0:
        return "▱" * length
    filled = min(length, max(0, int(round(length * current / maximum))))
    return "▰" * filled + "▱" * (length - filled)


def premium_box(title: str, lines: list[str], icon: str = "✦") -> str:
    body = "\n".join(f"  {line}" if line else "" for line in lines)
    footer = globals().get("brand_footer", "")
    footer_line = f"\n  ────────────────\n  <i>{esc(footer)}</i>" if footer else ""
    return (
        f"<b>╭─「 {icon} {esc(title)} 」─╮</b>\n"
        f"{body}{footer_line}\n"
        f"<b>╰──────────────────◈</b>"
    )


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or str(user_id) in admin_roles


def is_approved(user_id: int) -> bool:
    return is_owner(user_id) or user_id in approved_users


def is_premium(user_id: int) -> bool:
    expire_plans()
    return is_owner(user_id) or (user_id in premium_users and expiry_active(user_id))


def plan_name(user_id: int) -> str:
    if is_owner(user_id):
        return "👑 Owner"
    if is_premium(user_id):
        return f"💎 {user_plans.get(str(user_id), 'premium').title()}"
    if is_approved(user_id):
        return "✅ Approved"
    return "🔒 Guest"


def plan_icon(user_id: int) -> str:
    if is_owner(user_id):
        return "👑"
    if is_premium(user_id):
        return "💎"
    if is_approved(user_id):
        return "✅"
    return "🔒"


def get_credits(user_id: int) -> int:
    return int(user_credits.get(str(user_id), DEFAULT_CREDITS))


def set_credits(user_id: int, value: int) -> None:
    user_credits[str(user_id)] = max(0, int(value))
    save_data()


def get_stat(user_id: int) -> dict[str, Any]:
    key = str(user_id)
    if key not in user_stats:
        user_stats[key] = {
            "uploads_total": 0, "uploads_today": 0, "last_upload_date": "",
            "last_active": "", "username": "", "first_name": "",
        }
    return user_stats[key]


def touch_user(user: Any) -> None:
    stat = get_stat(user.id)
    stat["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stat["username"] = user.username or ""
    stat["first_name"] = user.first_name or ""
    save_data()


def reset_daily(user_id: int) -> None:
    stat = get_stat(user_id)
    today = date.today().isoformat()
    if stat.get("last_upload_date") != today:
        stat["last_upload_date"] = today
        stat["uploads_today"] = 0
        save_data()


def daily_limit(user_id: int) -> int:
    if is_owner(user_id):
        return 999_999
    if str(user_id) in custom_daily_limits:
        return custom_daily_limits[str(user_id)]
    return plan_limits(user_id)[0]


def running_limit(user_id: int) -> int:
    if is_owner(user_id):
        return 999_999
    if str(user_id) in custom_running_limits:
        return custom_running_limits[str(user_id)]
    return plan_limits(user_id)[1]


def plan_limits(user_id: int) -> tuple[int, int, int]:
    plan = user_plans.get(str(user_id), "premium" if user_id in premium_users else "free")
    table = {
        "free": (DAILY_UPLOAD_LIMIT, MAX_RUNNING_PER_USER, 128),
        "basic": (5, 3, 256), "premium": (25, 10, 512),
        "business": (100, 30, 1024), "lifetime": (100, 30, 1024),
    }
    return table.get(plan, table["free"])


def expiry_active(user_id: int) -> bool:
    raw = premium_expiry.get(str(user_id), "")
    if not raw or raw == "lifetime":
        return bool(raw == "lifetime" or user_id in premium_users)
    try:
        return datetime.fromisoformat(raw) > datetime.now()
    except ValueError:
        return False


def expire_plans() -> None:
    changed = False
    for uid, raw in list(premium_expiry.items()):
        if raw in ("", "lifetime"):
            continue
        try:
            if datetime.fromisoformat(raw) <= datetime.now():
                premium_users.discard(int(uid))
                user_plans[uid] = "free"
                premium_expiry.pop(uid, None)
                changed = True
        except (ValueError, TypeError):
            premium_expiry.pop(uid, None)
            changed = True
    if changed:
        save_data()
        save_v7_data()


def parse_duration(value: str) -> timedelta | None:
    m = re.fullmatch(r"(\d+)([mhd])", value.strip().lower())
    if not m:
        return None
    amount, unit = int(m.group(1)), m.group(2)
    return {"m": timedelta(minutes=amount), "h": timedelta(hours=amount), "d": timedelta(days=amount)}[unit]


def human_duration(seconds: int) -> str:
    seconds = int(seconds)
    if seconds >= 86400 and seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds >= 3600 and seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds >= 60 and seconds % 60 == 0:
        return f"{seconds // 60}m"
    if seconds >= 86400:
        d, rem = divmod(seconds, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        return " ".join(filter(None, [f"{d}d", f"{h}h" if h else "", f"{m}m" if m else ""]))
    if seconds >= 3600:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m" if m else f"{h}h"
    if seconds >= 60:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s" if s else f"{m}m"
    return f"{seconds}s"


def uptime(started_at: float = START_TIME) -> str:
    seconds = max(0, int(time.time() - started_at))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def user_folder(user_id: int) -> Path:
    folder = DOWNLOADS_DIR / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def clean_filename(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:120] or "upload.bin"


def clean_project_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_. -]+", "_", value).strip()[:80] or "project"


def scripts_for(user_id: int) -> list[ScriptProcess]:
    return running_scripts.setdefault(user_id, [])


def active_count(user_id: int) -> int:
    return sum(item.running for item in scripts_for(user_id))


def find_project(user_id: int, target: str) -> tuple[int, ScriptProcess] | None:
    target_folded = target.casefold()
    for index, item in enumerate(scripts_for(user_id)):
        if item.display_name.casefold() == target_folded or Path(item.entry_file).name.casefold() == target_folded:
            return index, item
    return None


def project_key(item_or_folder: Any) -> str:
    folder = item_or_folder.folder if hasattr(item_or_folder, "folder") else str(item_or_folder)
    return hashlib.sha256(str(Path(folder).resolve()).encode()).hexdigest()[:24]


def project_setting(item: ScriptProcess) -> dict[str, Any]:
    return project_settings.setdefault(project_key(item), {})


def user_storage_mb(user_id: int) -> float:
    total = 0
    for item in scripts_for(user_id):
        folder = Path(item.folder)
        if not folder.exists():
            continue
        try:
            for f in folder.rglob("*"):
                if f.is_file() and ".venv" not in f.parts:
                    total += f.stat().st_size
        except OSError:
            pass
    return total / (1024 * 1024)


def storage_limit_mb(user_id: int) -> int:
    if is_owner(user_id):
        return 999999
    return int(user_storage_limits.get(str(user_id), DEFAULT_STORAGE_QUOTA_MB))


def safe_remove_folder(folder_value: str) -> None:
    folder = Path(folder_value)
    try:
        folder.resolve().relative_to(DOWNLOADS_DIR.resolve())
    except (ValueError, OSError):
        raise ValueError("Unsafe project path")
    shutil.rmtree(folder, ignore_errors=True)


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    max_uncompressed = MAX_ZIP_EXPANDED_MB * 1024 * 1024
    total = 0
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            total += info.file_size
            if total > max_uncompressed:
                raise ValueError(f"ZIP expands beyond {MAX_ZIP_EXPANDED_MB} MB")
            target = (destination / info.filename).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError:
                raise ValueError("Unsafe ZIP path detected")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("ZIP symlinks are not allowed")
        archive.extractall(destination)


def detect_entry(folder: Path) -> Path | None:
    priority = ("main.py", "bot.py", "app.py", "index.py", "server.py", "run.py")
    for name in priority:
        matches = sorted(folder.rglob(name))
        if matches:
            return matches[0]
    files = sorted(folder.rglob("*.py"))
    return files[0] if files else None


def run_command(entry: Path) -> list[str] | None:
    if entry.suffix.lower() != ".py":
        return None
    private_py = None
    for parent in (entry.parent, *entry.parents):
        candidate = parent / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if candidate.exists():
            private_py = candidate
            break
    return [str(private_py) if private_py else sys.executable, "-u", str(entry)]


def spawn_script(item: ScriptProcess | None, entry: Path, folder: Path, log_path: Path) -> ScriptProcess:
    cmd = run_command(entry)
    if not cmd:
        raise ValueError("Unsupported project entry")

    log_handle = open(log_path, "a", encoding="utf-8", errors="replace", buffering=1)
    log_handle.write(f"\n===== Launch {datetime.now().isoformat(timespec='seconds')} =====\n")

    env = os.environ.copy()
    env.update({"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
    env.update(project_envs.get(project_key(folder), {}))

    preexec_fn = None
    if os.name != "nt" and ENFORCE_RESOURCE_LIMITS:
        def apply_limits() -> None:
            try:
                import resource
                settings = project_settings.get(project_key(folder), {})
                ram_mb = int(settings.get("ram_mb", DEFAULT_PROJECT_RAM_MB))
                max_bytes = max(128, ram_mb) * 1024 * 1024
                if entry.suffix.lower() == ".py" and ENFORCE_ADDRESS_SPACE_LIMIT:
                    resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
                if PROJECT_PROCESS_LIMIT > 0:
                    resource.setrlimit(resource.RLIMIT_NPROC, (PROJECT_PROCESS_LIMIT, PROJECT_PROCESS_LIMIT))
                if PROJECT_OPEN_FILES_LIMIT > 0:
                    resource.setrlimit(resource.RLIMIT_NOFILE, (PROJECT_OPEN_FILES_LIMIT, PROJECT_OPEN_FILES_LIMIT))
            except Exception:
                pass
        preexec_fn = apply_limits

    proc = subprocess.Popen(
        cmd, cwd=str(folder), stdout=log_handle, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, env=env,
        start_new_session=(os.name != "nt"), close_fds=(os.name != "nt"),
        preexec_fn=preexec_fn,
    )

    if item is None:
        item = ScriptProcess(
            display_name=entry.name, entry_file=str(entry),
            folder=str(folder), log_path=str(log_path), proc=proc,
        )
    else:
        item.proc = proc
        item.started_at = time.time()
    item.desired_running = True
    save_projects()
    return item


def kill_process(item: ScriptProcess) -> bool:
    if not item.running:
        return True
    assert item.proc is not None
    proc = item.proc
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                proc.kill()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        save_projects()
        return True
    except Exception:
        logger.exception("Failed stopping PID %s", proc.pid)
        return False


async def edit_message(query: Any, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    try:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=markup, disable_web_page_preview=True)
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


def scan_project(folder: Path) -> tuple[str, list[str]]:
    findings: list[str] = []
    patterns = {
        "Shell execution": r"(?:os\.system|subprocess\.(?:Popen|run|call))",
        "Dynamic code": r"(?:\beval\s*\(|\bexec\s*\(|Function\s*\()",
        "Environment access": r"(?:os\.environ|os\.getenv)",
        "Encoded payload": r"(?:base64\.(?:b64decode|decodebytes))",
        "Reverse-shell": r"(?:/bin/sh|/bin/bash|nc\s+-e|socket\.socket)",
        "Destructive FS": r"(?:shutil\.rmtree|rm\s+-rf|os\.remove)",
        "Crypto-mining": r"(?:xmrig|stratum\+tcp|monero)",
    }
    for file in folder.rglob("*.py"):
        if file.stat().st_size > 2_000_000:
            continue
        try:
            text = file.read_text("utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.I):
                findings.append(f"{label}: {file.relative_to(folder)}")
    findings = sorted(set(findings))
    high = any("Reverse" in x or "mining" in x or "Destructive" in x for x in findings)
    risk = "HIGH" if high else ("MEDIUM" if findings else "LOW")
    return risk, findings[:20]


def diagnose_log_text(text: str) -> list[str]:
    checks = [
        ("ModuleNotFoundError", "📦 Missing Python package — repair/reinstall requirements."),
        ("SyntaxError", "📝 Python syntax error — inspect the referenced file/line."),
        ("event loop is already running", "🔁 Async startup conflict — avoid nested run_polling()."),
        ("can't start new thread", "⚠️ Host thread/process resource pressure detected."),
        ("InvalidToken", "🔑 Telegram bot token is invalid or revoked."),
        ("Unauthorized", "🚫 Authentication/token permission error detected."),
        ("Conflict", "⚔️ Another instance may already be polling this token."),
        ("PermissionError", "🔒 Project tried to access a path without permission."),
        ("No space left on device", "💾 Server disk is full or quota exhausted."),
        ("MemoryError", "🧠 Project ran out of available Python memory."),
    ]
    found = [msg for key, msg in checks if key.casefold() in text.casefold()]
    return found or ["✅ No known signature detected. Review the latest runtime log manually."]


def install_project_dependencies(folder: Path, entry: Path, log_path: Path) -> str:
    if entry.suffix.lower() != ".py":
        return "No dependency manifest detected"
    req = next(iter(folder.rglob("requirements.txt")), None)
    if not (req and AUTO_INSTALL_DEPENDENCIES):
        return "No dependency manifest detected"
    venv_dir = folder / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, timeout=60)
    py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    result = subprocess.run(
        [str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(req)],
        cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=DEPENDENCY_TIMEOUT_SECONDS,
    )
    out = result.stdout.decode("utf-8", errors="replace")
    with log_path.open("a", encoding="utf-8", errors="replace") as log_file:
        log_file.write("\n\n===== Dependency Installation =====\n")
        log_file.write(out)
        if out and not out.endswith("\n"):
            log_file.write("\n")
    if result.returncode != 0:
        raise RuntimeError("requirements.txt installation failed; check runtime.log")
    return "Python dependencies installed in private .venv"


def project_resources(item: ScriptProcess) -> dict[str, str]:
    result = {"cpu": "N/A", "ram": "N/A", "disk": "0 MB"}
    try:
        total = sum(f.stat().st_size for f in Path(item.folder).rglob("*") if f.is_file())
        result["disk"] = f"{total / 1024 / 1024:.1f} MB"
    except OSError:
        pass
    if item.running and item.proc:
        try:
            import psutil
            proc = psutil.Process(item.proc.pid)
            result["cpu"] = f"{proc.cpu_percent(interval=0.1):.1f}%"
            result["ram"] = f"{proc.memory_info().rss / 1024 / 1024:.1f} MB"
        except Exception:
            pass
    return result


# ═════════════════════════════════════════════════════════════════════════════
# 🔐  FORCE-JOIN
# ═════════════════════════════════════════════════════════════════════════════


def _matches_chat(chat: Any, target: str) -> bool:
    if not target:
        return False
    if str(chat.id) == str(target):
        return True
    if target.startswith("@") and getattr(chat, "username", None):
        return f"@{chat.username}".lower() == target.lower()
    return False


async def get_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict[str, bool]:
    if not FORCE_JOIN_ENABLED or is_admin(user_id) or user_id in forcejoin_bypass_users:
        return {"channel": True, "group": True}

    cache_key = str(user_id)
    entry = chat_membership.setdefault(cache_key, {})
    now = time.time()
    valid = {"member", "administrator", "creator"}
    out: dict[str, bool] = {}

    for target, chat in (
        ("channel", MAIN_CHANNEL_USERNAME),
        ("group", SUPPORT_GROUP_USERNAME),
    ):
        row = entry.get(target)
        if row and (now - float(row.get("at", 0))) < FORCE_JOIN_CACHE_TTL:
            out[target] = bool(row.get("joined"))
            continue
        try:
            member = await context.bot.get_chat_member(chat, user_id)
            joined = member.status in valid
        except TelegramError as exc:
            logger.warning("Force-join %s check failed for %s: %s", target, user_id, exc)
            joined = False
        entry[target] = {"joined": joined, "at": now}
        out[target] = joined

    save_join_cache()
    return out


async def check_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    m = await get_membership(user_id, context)
    return m["channel"] and m["group"]


async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = update.chat_member
    if not cm:
        return
    if _matches_chat(cm.chat, SUPPORT_GROUP_USERNAME):
        target = "group"
    elif _matches_chat(cm.chat, MAIN_CHANNEL_USERNAME):
        target = "channel"
    else:
        return

    user_id = cm.new_chat_member.user.id
    new_status = cm.new_chat_member.status
    entry = chat_membership.setdefault(str(user_id), {})

    if new_status in {"left", "kicked"}:
        entry[target] = {"joined": False, "at": time.time()}
        logger.info("Force-join: %s LEFT %s", user_id, target)
    elif new_status in {"member", "administrator", "creator"}:
        entry[target] = {"joined": True, "at": time.time()}
        logger.info("Force-join: %s JOINED %s", user_id, target)
    else:
        return
    save_join_cache()


# ═════════════════════════════════════════════════════════════════════════════
# 🎨  COLORFUL UI BUILDERS
# ═════════════════════════════════════════════════════════════════════════════


def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("🚀 ᴅᴇᴘʟᴏʏ ᴘʀᴏᴊᴇᴄᴛ"), KeyboardButton("📁 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs")],
        [KeyboardButton("📋 ʟɪᴠᴇ ʟᴏɢs"), KeyboardButton("🎛 ᴄᴏɴᴛʀᴏʟs")],
        [KeyboardButton("💎 ᴡᴀʟʟᴇᴛ"), KeyboardButton("👤 ᴀᴄᴄᴏᴜɴᴛ")],
        [KeyboardButton("🌟 ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs"), KeyboardButton("🛟 sᴜᴘᴘᴏʀᴛ")],
    ]
    if is_owner(user_id):
        rows.append([KeyboardButton("⚡ ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴄᴇɴᴛᴇʀ ⚡")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def home_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟦 📣 ᴏꜰꜰɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟ", url=MAIN_CHANNEL_LINK),
            InlineKeyboardButton("🟩 👥 ᴄᴏᴍᴍᴜɴɪᴛʏ", url=SUPPORT_GROUP_LINK),
        ],
        [InlineKeyboardButton("🟪 💬 ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ", url=SUPPORT_LINK)],
    ])


def join_buttons(missing: dict[str, bool] | None = None) -> InlineKeyboardMarkup:
    missing = missing or {"channel": True, "group": True}
    rows: list[list[InlineKeyboardButton]] = []
    if missing.get("channel"):
        rows.append([InlineKeyboardButton(f"🟦 📣 ᴊᴏɪɴ {MAIN_CHANNEL_NAME}", url=MAIN_CHANNEL_LINK)])
    if missing.get("group"):
        rows.append([InlineKeyboardButton(f"🟩 👥 ᴊᴏɪɴ {SUPPORT_GROUP_NAME}", url=SUPPORT_GROUP_LINK)])
    rows.append([InlineKeyboardButton("🟢 ✅ ᴠᴇʀɪꜰʏ ᴍᴇᴍʙᴇʀsʜɪᴘ", callback_data="join:check")])
    return InlineKeyboardMarkup(rows)


def project_list_buttons(user_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index, item in enumerate(scripts_for(user_id)):
        color = "🟢" if item.running else "🔴"
        rows.append([InlineKeyboardButton(
            f"{color} {item.display_name[:28]}",
            callback_data=f"project:view:{index}",
        )])
    rows.append([InlineKeyboardButton("🟠 🔃 ʀᴇꜰʀᴇsʜ ʟɪsᴛ", callback_data="project:list")])
    return InlineKeyboardMarkup(rows)


def project_control_buttons(index: int, running: bool) -> InlineKeyboardMarkup:
    primary = (
        InlineKeyboardButton("🔴 ⏹ sᴛᴏᴘ", callback_data=f"project:stop:{index}")
        if running
        else InlineKeyboardButton("🟢 ▶️ sᴛᴀʀᴛ", callback_data=f"project:start:{index}")
    )
    return InlineKeyboardMarkup([
        [
            primary,
            InlineKeyboardButton("🟠 🔄 ʀᴇsᴛᴀʀᴛ", callback_data=f"project:restart:{index}"),
        ],
        [
            InlineKeyboardButton("🔵 📋 ʟᴏɢs", callback_data=f"project:logs:{index}"),
            InlineKeyboardButton("🔵 📥 ᴅᴏᴡɴʟᴏᴀᴅ", callback_data=f"project:logfile:{index}"),
        ],
        [
            InlineKeyboardButton("🟡 ✏️ ʀᴇɴᴀᴍᴇ", callback_data=f"project:rename:{index}"),
            InlineKeyboardButton("🔴 🗑️ ᴅᴇʟᴇᴛᴇ", callback_data=f"project:delete:{index}"),
        ],
        [InlineKeyboardButton("⚫ ◀️ ʙᴀᴄᴋ ᴛᴏ ᴘʀᴏᴊᴇᴄᴛs", callback_data="project:list")],
    ])


def admin_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟣 📊 ᴏᴠᴇʀᴠɪᴇᴡ", callback_data="admin:overview"),
            InlineKeyboardButton("🟦 👥 ᴜsᴇʀs", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton("🟠 🖥 ᴘʀᴏᴄᴇssᴇs", callback_data="admin:processes"),
            InlineKeyboardButton("🟡 💎 ᴘʀᴇᴍɪᴜᴍ", callback_data="admin:premium"),
        ],
        [
            InlineKeyboardButton("🟡 💳 ᴄʀᴇᴅɪᴛs", callback_data="admin:credits"),
            InlineKeyboardButton("🔴 🚫 ʙᴀɴɴᴇᴅ", callback_data="admin:banned"),
        ],
        [
            InlineKeyboardButton("🟢 ▶️ sᴛᴀʀᴛ ᴀʟʟ", callback_data="admin:startall"),
            InlineKeyboardButton("🔴 ⏹ sᴛᴏᴘ ᴀʟʟ", callback_data="admin:stopall"),
        ],
        [
            InlineKeyboardButton("🟦 🔐 ꜰᴏʀᴄᴇ ᴊᴏɪɴ", callback_data="admin:forcejoin"),
            InlineKeyboardButton("🟨 🛠 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", callback_data="admin:maintenance"),
        ],
        [
            InlineKeyboardButton("🟢 💓 ᴋᴇᴇᴘ ᴀʟɪᴠᴇ", callback_data="admin:keepalive"),
            InlineKeyboardButton("🟦 📡 ʜᴏsᴛ sᴛᴀᴛᴜs", callback_data="admin:hoststatus"),
        ],
        [
            InlineKeyboardButton("🟣 🛡 sᴇᴄᴜʀɪᴛʏ", callback_data="admin:security"),
            InlineKeyboardButton("🟡 💾 ʙᴀᴄᴋᴜᴘs", callback_data="admin:backupinfo"),
        ],
        [
            InlineKeyboardButton("🟠 🧹 ᴄʟᴇᴀɴᴜᴘ", callback_data="admin:cleanup"),
            InlineKeyboardButton("🔵 📖 ᴄᴏᴍᴍᴀɴᴅs", callback_data="admin:commands"),
        ],
        [InlineKeyboardButton("⚫ ✖️ ᴄʟᴏsᴇ ᴘᴀɴᴇʟ", callback_data="admin:close")],
    ])


def home_text(user_id: int) -> str:
    reset_daily(user_id)
    stat = get_stat(user_id)
    running_now = active_count(user_id)
    running_max = running_limit(user_id)
    uploads_today = stat["uploads_today"]
    uploads_max = daily_limit(user_id)
    credits_now = get_credits(user_id)
    status_icon = "🟢" if running_now > 0 else "⚫"
    return premium_box(
        BRAND_NAME.upper(),
        [
            "<i>🌐 Premium Telegram Bot Hosting</i>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"{plan_icon(user_id)} <b>ᴘʟᴀɴ</b>     ›  {esc(plan_name(user_id))}",
            f"🆔 <b>ᴜsᴇʀ ɪᴅ</b>  ›  <tg-spoiler><code>{user_id}</code></tg-spoiler>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"{status_icon} <b>ʀᴜɴɴɪɴɢ</b>  ›  <code>{running_now} / {running_max}</code>",
            f"  {progress_bar(running_now, running_max)}",
            f"📤 <b>ᴜᴘʟᴏᴀᴅs</b>  ›  <code>{uploads_today} / {uploads_max}</code>",
            f"  {progress_bar(uploads_today, uploads_max)}",
            f"💎 <b>ᴄʀᴇᴅɪᴛs</b>  ›  <code>{credits_now}</code>",
            f"⏱ <b>ᴜᴘᴛɪᴍᴇ</b>   ›  <code>{uptime()}</code>",
            "━━━━━━━━━━━━━━━━━━━━",
            "📦 <i>Send</i> <code>.py</code> <i>or</i> <code>.zip</code> <i>to deploy.</i>",
        ],
        icon="✦",
    )


def projects_text(user_id: int) -> str:
    items = scripts_for(user_id)
    if not items:
        return premium_box(
            "ᴍʏ ᴘʀᴏᴊᴇᴄᴛs",
            ["", "📭 No hosted projects found.", "", "Send a <code>.py</code> or Python <code>.zip</code> file."],
            icon="📂",
        )
    lines = [f"<i>Total: {len(items)} project(s)</i>", "━━━━━━━━━━━━━━━━━━━━", ""]
    for index, item in enumerate(items, start=1):
        status = "🟢 Online" if item.running else f"🔴 Offline ({esc(item.exit_code)})"
        lines.append(f"<b>{index}. {esc(item.display_name)}</b>")
        lines.append(f"   {status}")
        lines.append(f"   🆔 PID: <tg-spoiler><code>{esc(item.pid)}</code></tg-spoiler>")
        lines.append("")
    return premium_box("ᴍʏ ᴘʀᴏᴊᴇᴄᴛs", lines, icon="📂")


def admin_overview() -> str:
    all_items = [item for items in running_scripts.values() for item in items]
    active = sum(item.running for item in all_items)
    return premium_box(
        f"{BRAND_NAME} ᴀᴅᴍɪɴ",
        [
            "<i>Realtime system snapshot</i>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"👥 <b>Approved</b>     ›  <code>{len(approved_users)}</code>",
            f"💎 <b>Premium</b>      ›  <code>{len(premium_users)}</code>",
            f"🚫 <b>Banned</b>       ›  <code>{len(banned_users)}</code>",
            f"💳 <b>Wallets</b>      ›  <code>{len(user_credits)}</code>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🧩 <b>Registered</b>   ›  <code>{len(all_items)}</code>",
            f"🟢 <b>Active</b>       ›  <code>{active}</code>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🔐 <b>Force Join</b>   ›  <code>{'ON' if FORCE_JOIN_ENABLED else 'OFF'}</code>",
            f"🛠 <b>Maintenance</b>  ›  <code>{'ON' if maintenance_mode else 'OFF'}</code>",
            f"🐍 <b>Python</b>       ›  <code>{platform.python_version()}</code>",
            f"💓 <b>Keep Alive</b>   ›  <code>{'ON' if keepalive_enabled else 'OFF'}</code> / {keepalive_interval}s",
            f"🌐 <b>Health</b>       ›  <code>:{HEALTH_PORT}</code>",
            f"⏱ <b>Uptime</b>        ›  <code>{uptime()}</code>",
        ],
        icon="👑",
    )


def admin_commands_text() -> str:
    return premium_box(
        "ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs",
        [
            "<b>👑 Admin</b>",
            "<code>/admin</code> • <code>/analytics</code> • <code>/admins</code>",
            "<code>/addadmin UID role</code> • <code>/deladmin UID</code>",
            "<code>/finduser Q</code> • <code>/allprojects</code> • <code>/restartall</code>",
            "",
            "<b>🛡 Watchdog</b>",
            "<code>/watchdog on|off</code> • <code>/setwatchdog SEC</code>",
            "<code>/watchdogstatus</code> • <code>/schedulerestart P 6h</code>",
            "<code>/scheduleremove P</code> • <code>/autostart P on|off</code>",
            "<code>/diagnose P</code>",
            "",
            "<b>💾 Storage</b>",
            "<code>/storage</code> • <code>/setstorage UID MB</code>",
            "<code>/logsize P</code> • <code>/clearlogs P</code>",
            "",
            "<b>📦 Dependencies</b>",
            "<code>/requirements P</code> • <code>/piplist P</code>",
            "<code>/checkcompat P</code> • <code>/repairenv P</code>",
            "<code>/install PKG</code> • <code>/installed</code>",
            "",
            "<b>🔐 Force-Join</b>",
            "<code>/verifycache</code> • <code>/bypassjoin UID</code>",
            "<code>/unbypassjoin UID</code> • <code>/clearverify UID</code>",
            "<code>/clearallverify</code> • <code>/forcejoin on|off</code>",
            "",
            "<b>🎟 Redeem</b>",
            "<code>/createcode ...</code> • <code>/codes</code>",
            "<code>/codeinfo C</code> • <code>/disablecode C</code> • <code>/deletecode C</code>",
            "",
            "<b>🎨 Branding</b>",
            "<code>/setbrand NAME</code> • <code>/setfooter TEXT</code>",
            "<code>/panelreminder on|off</code> • <code>/panelvisited</code>",
            "",
            "<b>⚙️ System</b>",
            "<code>/backup</code> • <code>/backups</code> • <code>/restorebackup F CONFIRM</code>",
            "<code>/hoststats</code> • <code>/security</code> • <code>/keepalive</code>",
            "<code>/setkeepalive URL [30-45]</code>",
        ],
        icon="📖",
    )


def keepalive_text() -> str:
    return premium_box("ᴋᴇᴇᴘ ᴀʟɪᴠᴇ", [
        f"Status: <code>{'ON' if keepalive_enabled else 'OFF'}</code>",
        f"Interval: <code>{keepalive_interval}s</code>",
        f"URL: <code>{esc(keepalive_url or 'Not configured')}</code>",
        f"Last Ping: <code>{esc(keepalive_last_at)}</code>",
        f"Last Result: <code>{esc(keepalive_last_status)}</code>",
        f"Failures: <code>{keepalive_failures}</code>",
        f"Health: <code>{'ONLINE' if health_server_started else 'UNAVAILABLE'}</code> : <code>{HEALTH_PORT}</code>",
        "Use <code>/setkeepalive https://domain/health 40</code>",
    ], icon="💓")


def host_stats_text() -> str:
    all_items = [i for items in running_scripts.values() for i in items]
    active = sum(i.running for i in all_items)
    disk = "N/A"
    ram = "N/A"
    cpu = "N/A"
    try:
        total, used, free = shutil.disk_usage(BASE_DIR)
        disk = f"{used/1024**3:.2f}/{total/1024**3:.2f} GB"
    except OSError:
        pass
    try:
        import psutil
        ram = f"{psutil.virtual_memory().percent:.1f}%"
        cpu = f"{psutil.cpu_percent(interval=0.1):.1f}%"
    except Exception:
        pass
    return premium_box("ʜᴏsᴛ sᴛᴀᴛᴜs", [
        f"Python: <code>{platform.python_version()}</code>",
        f"OS: <code>{esc(platform.system())} {esc(platform.release())}</code>",
        f"CPU: <code>{cpu}</code>",
        f"RAM: <code>{ram}</code>",
        f"Disk: <code>{disk}</code>",
        f"Projects: <code>{len(all_items)}</code>",
        f"Running: <code>{active}</code>",
        f"Users: <code>{len(user_stats)}</code>",
        f"Keep Alive: <code>{'ON' if keepalive_enabled else 'OFF'} / {keepalive_interval}s</code>",
        f"Uptime: <code>{uptime()}</code>",
    ], icon="🖥")


def security_text() -> str:
    return premium_box("sᴇᴄᴜʀɪᴛʏ & ʀᴜɴᴛɪᴍᴇ", [
        "Runtime: <code>PYTHON ONLY</code>",
        f"Security Scan: <code>{'ON' if SECURITY_SCAN_ENABLED else 'OFF'}</code>",
        f"Auto Dependencies: <code>{'ON' if AUTO_INSTALL_DEPENDENCIES else 'OFF'}</code>",
        f"Docker Mode: <code>{'ON' if DOCKER_MODE else 'OFF'}</code>",
        f"Resource Limits: <code>{'ON' if ENFORCE_RESOURCE_LIMITS else 'OFF'}</code>",
        f"Process Limit: <code>{PROJECT_PROCESS_LIMIT or 'disabled'}</code>",
        f"Open Files: <code>{PROJECT_OPEN_FILES_LIMIT}</code>",
        f"Max Upload: <code>{MAX_FILE_MB} MB</code>",
        f"Max ZIP: <code>{MAX_ZIP_EXPANDED_MB} MB</code>",
    ], icon="🛡")


# ═════════════════════════════════════════════════════════════════════════════
# 🛡️  ACCESS CONTROL
# ═════════════════════════════════════════════════════════════════════════════


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return False
    touch_user(user)

    if user.id in banned_users:
        await message.reply_text(
            "🚫 <b>Access Suspended</b>\n\nYour account has been restricted.",
            parse_mode=ParseMode.HTML,
        )
        return False

    if maintenance_mode and not is_admin(user.id):
        await message.reply_text(
            premium_box("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", [
                "🛠 <b>Service under maintenance</b>",
                "",
                "<i>Please try again later.</i>",
            ], icon="🛠"),
            parse_mode=ParseMode.HTML,
        )
        return False

    if not is_approved(user.id):
        await message.reply_text(
            premium_box("ᴀᴄᴄᴇss ʀᴇǫᴜɪʀᴇᴅ", [
                "🔐 <b>Premium access needed</b>",
                "",
                "Send the access password or use",
                "<code>/request reason</code> to apply.",
            ], icon="🔐"),
            parse_mode=ParseMode.HTML,
            reply_markup=home_buttons(),
        )
        return False

    missing = await get_membership(user.id, context)
    if not (missing["channel"] and missing["group"]):
        lines = ["🔒 <b>Membership required</b>", ""]
        if not missing["channel"]:
            lines.append("📣 Channel: <b>not joined</b>")
        if not missing["group"]:
            lines.append("👥 Group: <b>not joined</b>")
        lines += ["", "<i>Tap below, then verify.</i>"]
        await message.reply_text(
            premium_box("ᴠᴇʀɪꜰʏ ᴍᴇᴍʙᴇʀsʜɪᴘ", lines, icon="🔒"),
            parse_mode=ParseMode.HTML,
            reply_markup=join_buttons(missing),
        )
        return False
    return True


def owner_only(update: Update) -> bool:
    return bool(update.effective_user and is_owner(update.effective_user.id))


def admin_or_owner(update: Update) -> bool:
    return bool(update.effective_user and is_admin(update.effective_user.id))


def admin_role(user_id: int) -> str:
    return "owner" if is_owner(user_id) else admin_roles.get(str(user_id), "none")


async def require_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return await guard(update, context)


# ═════════════════════════════════════════════════════════════════════════════
# 🚀  BASIC COMMANDS
# ═════════════════════════════════════════════════════════════════════════════


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    touch_user(user)

    if user.id in banned_users:
        await update.effective_message.reply_text(
            "🚫 <b>Access Suspended</b>", parse_mode=ParseMode.HTML
        )
        return

    if not is_approved(user.id):
        await update.effective_message.reply_text(
            premium_box(f"ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {BRAND_NAME}", [
                "<i>Premium Telegram Bot Hosting</i>",
                "",
                "🔐 <b>Premium access required</b>",
                "",
                "Send the access password or use",
                "<code>/request reason</code>.",
            ], icon="✨"),
            parse_mode=ParseMode.HTML,
            reply_markup=home_buttons(),
        )
        return

    missing = await get_membership(user.id, context)
    if not (missing["channel"] and missing["group"]):
        lines = ["🔒 <b>Complete membership verification</b>", ""]
        if not missing["channel"]:
            lines.append("📣 Channel: <b>not joined</b>")
        if not missing["group"]:
            lines.append("👥 Group: <b>not joined</b>")
        await update.effective_message.reply_text(
            premium_box("ᴠᴇʀɪꜰʏ ᴍᴇᴍʙᴇʀsʜɪᴘ", lines, icon="🔒"),
            parse_mode=ParseMode.HTML,
            reply_markup=join_buttons(missing),
        )
        return

    await update.effective_message.reply_text(
        home_text(user.id),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu(user.id),
        disable_web_page_preview=True,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    text = premium_box("ʜᴇʟᴘ", [
        "<b>📂 Projects</b>",
        "<code>/projects</code> — Open project list",
        "<code>/logs [name]</code> — Latest logs",
        "<code>/restart NAME</code> — Restart project",
        "<code>/stop NAME</code> — Stop project",
        "<code>/delete NAME</code> — Delete stopped project",
        "<code>/rename OLD NEW</code> — Rename project",
        "",
        "<b>💎 Account</b>",
        "<code>/credits</code> — Wallet",
        "<code>/skip</code> — Skip project name prompt",
    ], icon="ℹ️")
    if is_owner(update.effective_user.id):
        text += "\n\n" + admin_commands_text()
    await update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def request_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id in banned_users:
        return
    reason = " ".join(context.args).strip() or "No reason provided"
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 ✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"request:approve:{user.id}"),
        InlineKeyboardButton("🔴 ❌ ʀᴇᴊᴇᴄᴛ", callback_data=f"request:reject:{user.id}"),
    ]])
    await context.bot.send_message(
        OWNER_ID,
        premium_box("ɴᴇᴡ ᴀᴄᴄᴇss ʀᴇǫᴜᴇsᴛ", [
            f"👤 <b>{esc(user.full_name)}</b>",
            f"🔗 @{esc(user.username or 'not_set')}",
            f"🆔 <tg-spoiler><code>{user.id}</code></tg-spoiler>",
            f"📝 <i>{esc(reason)}</i>",
        ], icon="📩"),
        parse_mode=ParseMode.HTML,
        reply_markup=buttons,
    )
    await update.effective_message.reply_text(
        "✅ <b>Request sent to the owner.</b>", parse_mode=ParseMode.HTML
    )


async def projects_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    uid = update.effective_user.id
    await update.effective_message.reply_text(
        projects_text(uid), parse_mode=ParseMode.HTML, reply_markup=project_list_buttons(uid)
    )


async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    uid = update.effective_user.id
    items = scripts_for(uid)
    if not items:
        await update.effective_message.reply_text(
            "🧾 <i>No logs available.</i>", parse_mode=ParseMode.HTML
        )
        return
    item = items[-1]
    if context.args:
        found = find_project(uid, " ".join(context.args))
        if not found:
            await update.effective_message.reply_text("❌ Project not found.")
            return
        _, item = found
    path = Path(item.log_path)
    content = path.read_text("utf-8", errors="replace")[-MAX_LOG_CHARS:] if path.exists() else "No output yet."
    await update.effective_message.reply_text(
        premium_box(f"ʟᴏɢs › {item.display_name}", [f"<pre>{esc(content)}</pre>"], icon="🧾"),
        parse_mode=ParseMode.HTML,
    )


async def credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    uid = caller
    if context.args:
        if not is_owner(caller):
            await update.effective_message.reply_text("❌ Owner only.")
            return
        try:
            uid = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text("❌ Invalid user ID.")
            return
    await update.effective_message.reply_text(
        premium_box("ᴄʀᴇᴅɪᴛ ᴡᴀʟʟᴇᴛ", [
            f"🆔 User: <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"{plan_icon(uid)} Plan: {esc(plan_name(uid))}",
            f"💎 Credits: <code>{get_credits(uid)}</code>",
            f"📤 Upload cost: <code>{CREDIT_PER_UPLOAD}</code> credit",
        ], icon="💳"),
        parse_mode=ParseMode.HTML,
    )


async def skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid not in pending_project_names:
        await update.effective_message.reply_text("ℹ️ No project name is pending.")
        return
    pending_project_names.pop(uid, None)
    await update.effective_message.reply_text(
        "✅ <b>Original project name kept.</b>", parse_mode=ParseMode.HTML
    )


async def rename_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: /rename OLD_NAME NEW_NAME")
        return
    uid = update.effective_user.id
    found = find_project(uid, context.args[0])
    if not found:
        await update.effective_message.reply_text("❌ Project not found.")
        return
    _, item = found
    item.display_name = clean_project_name(" ".join(context.args[1:]))
    save_projects()
    await update.effective_message.reply_text(
        premium_box("ʀᴇɴᴀᴍᴇᴅ", [f"✅ → <code>{esc(item.display_name)}</code>"], icon="✏️"),
        parse_mode=ParseMode.HTML,
    )


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    if not context.args:
        await projects_cmd(update, context)
        return
    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))
    if not found:
        await update.effective_message.reply_text("❌ Project not found.")
        return
    _, item = found
    item.desired_running = False
    project_setting(item)["autostart"] = False
    ok = kill_process(item)
    save_projects()
    save_v7_data()
    await update.effective_message.reply_text(
        premium_box("sᴛᴏᴘᴘᴇᴅ" if ok else "ꜰᴀɪʟᴇᴅ", [
            f"🔴 <b>{esc(item.display_name)}</b>" if ok else "❌ Could not stop project."
        ], icon="⏹" if ok else "⚠️"),
        parse_mode=ParseMode.HTML,
    )


async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /restart PROJECT_NAME")
        return
    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))
    if not found:
        await update.effective_message.reply_text("❌ Project not found.")
        return
    _, item = found
    async with lock_for(uid):
        if item.running:
            kill_process(item)
        item.restarts += 1
        try:
            spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
            await asyncio.sleep(0.5)
            await update.effective_message.reply_text(
                premium_box("ʀᴇsᴛᴀʀᴛᴇᴅ" if item.running else "ꜰᴀɪʟᴇᴅ", [
                    f"🟠 <b>{esc(item.display_name)}</b>" if item.running else "❌ Project exited.",
                    f"🆔 PID: <tg-spoiler><code>{item.pid}</code></tg-spoiler>",
                ], icon="🔄" if item.running else "❌"),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            await update.effective_message.reply_text(
                f"❌ Restart failed: <code>{esc(exc)}</code>", parse_mode=ParseMode.HTML
            )


async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /delete PROJECT_NAME")
        return
    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))
    if not found:
        await update.effective_message.reply_text("❌ Project not found.")
        return
    index, item = found
    if item.running:
        await update.effective_message.reply_text("⚠️ Stop the project before deleting it.")
        return
    key = project_key(item)
    safe_remove_folder(item.folder)
    scripts_for(uid).pop(index)
    project_settings.pop(key, None)
    project_envs.pop(key, None)
    save_projects()
    save_v7_data()
    await update.effective_message.reply_text(
        premium_box("ᴅᴇʟᴇᴛᴇᴅ", [f"🗑 <b>{esc(item.display_name)}</b>"], icon="✅"),
        parse_mode=ParseMode.HTML,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 👑  OWNER COMMANDS
# ═════════════════════════════════════════════════════════════════════════════


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update):
        await update.effective_message.reply_text("❌ Admin only.")
        return
    await update.effective_message.reply_text(
        admin_overview(), parse_mode=ParseMode.HTML, reply_markup=admin_buttons()
    )


async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    approved_users.add(uid)
    banned_users.discard(uid)
    user_credits.setdefault(str(uid), DEFAULT_CREDITS)
    save_data()
    await update.effective_message.reply_text(
        premium_box("ᴀᴘᴘʀᴏᴠᴇᴅ", [f"✅ <tg-spoiler><code>{uid}</code></tg-spoiler>"], icon="✅"),
        parse_mode=ParseMode.HTML,
    )
    try:
        await context.bot.send_message(uid, f"✅ Access approved for {BRAND_NAME}. Send /start.")
    except TelegramError:
        pass


async def revoke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    approved_users.discard(uid)
    premium_users.discard(uid)
    save_data()
    await update.effective_message.reply_text(f"✅ Revoked from <code>{uid}</code>.", parse_mode=ParseMode.HTML)


async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    approved_users.add(uid)
    premium_users.add(uid)
    banned_users.discard(uid)
    set_credits(uid, get_credits(uid) + PREMIUM_BONUS_CREDITS)
    save_data()
    await update.effective_message.reply_text(
        premium_box("ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ", [
            f"💎 <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"🎁 +{PREMIUM_BONUS_CREDITS} credits",
            f"📤 Daily: <code>{daily_limit(uid)}</code>",
            f"🖥 Running: <code>{running_limit(uid)}</code>",
        ], icon="💎"),
        parse_mode=ParseMode.HTML,
    )
    try:
        await context.bot.send_message(uid, f"💎 Premium activated on {BRAND_NAME}.\nCredits: {get_credits(uid)}")
    except TelegramError:
        pass


async def unpremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    premium_users.discard(uid)
    save_data()
    await update.effective_message.reply_text(f"✅ Premium removed from <code>{uid}</code>.", parse_mode=ParseMode.HTML)


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    banned_users.add(uid)
    approved_users.discard(uid)
    premium_users.discard(uid)
    admin_roles.pop(str(uid), None)
    forcejoin_bypass_users.discard(uid)
    stopped = 0
    for item in scripts_for(uid):
        if item.running and kill_process(item):
            stopped += 1
    save_data()
    save_v7_data()
    save_join_cache()
    await update.effective_message.reply_text(
        premium_box("ʙᴀɴɴᴇᴅ", [
            f"🚫 <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"🛑 Stopped: <code>{stopped}</code> project(s)",
        ], icon="🚫"),
        parse_mode=ParseMode.HTML,
    )


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    banned_users.discard(uid)
    save_data()
    await update.effective_message.reply_text(f"✅ Unbanned <code>{uid}</code>.", parse_mode=ParseMode.HTML)


async def addcredits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    try:
        uid, amount = int(context.args[0]), int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return
    set_credits(uid, get_credits(uid) + amount)
    await update.effective_message.reply_text(
        premium_box("ᴄʀᴇᴅɪᴛs ᴀᴅᴅᴇᴅ", [
            f"💎 <code>+{amount}</code> → <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"💰 Total: <code>{get_credits(uid)}</code>",
        ], icon="💳"),
        parse_mode=ParseMode.HTML,
    )


async def setcredits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    try:
        uid, amount = int(context.args[0]), int(context.args[1])
        if amount < 0:
            raise ValueError
    except ValueError:
        return
    set_credits(uid, amount)
    await update.effective_message.reply_text(f"✅ Set <code>{uid}</code> → <code>{amount}</code>.", parse_mode=ParseMode.HTML)


async def takecredits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    try:
        uid, amount = int(context.args[0]), int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return
    set_credits(uid, get_credits(uid) - amount)
    await update.effective_message.reply_text(
        f"✅ Removed <code>{amount}</code> from <code>{uid}</code>.\nRemaining: <code>{get_credits(uid)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def setdaily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    try:
        uid, limit = int(context.args[0]), int(context.args[1])
        if limit < 0:
            raise ValueError
    except ValueError:
        return
    custom_daily_limits[str(uid)] = limit
    save_data()
    await update.effective_message.reply_text(f"✅ Daily limit for <code>{uid}</code> → <code>{limit}</code>.", parse_mode=ParseMode.HTML)


async def setrunning_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    try:
        uid, limit = int(context.args[0]), int(context.args[1])
        if limit < 1:
            raise ValueError
    except ValueError:
        return
    custom_running_limits[str(uid)] = limit
    save_data()
    await update.effective_message.reply_text(f"✅ Running limit for <code>{uid}</code> → <code>{limit}</code>.", parse_mode=ParseMode.HTML)


async def userinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    stat = get_stat(uid)
    await update.effective_message.reply_text(
        premium_box(f"ᴜsᴇʀ ɪɴꜰᴏ › {uid}", [
            f"🆔 <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"🔗 @{esc(stat.get('username') or 'not_set')}",
            f"👤 {esc(stat.get('first_name') or 'Unknown')}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"{plan_icon(uid)} Plan: {esc(plan_name(uid))}",
            f"✅ Approved: <code>{'YES' if is_approved(uid) else 'NO'}</code>",
            f"💎 Premium: <code>{'YES' if is_premium(uid) else 'NO'}</code>",
            f"🚫 Banned: <code>{'YES' if uid in banned_users else 'NO'}</code>",
            f"🎖 Role: <code>{esc(admin_role(uid))}</code>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"💎 Credits: <code>{get_credits(uid)}</code>",
            f"🖥 Running: <code>{active_count(uid)}/{running_limit(uid)}</code>",
            f"📤 Today: <code>{stat.get('uploads_today', 0)}/{daily_limit(uid)}</code>",
            f"📦 Total: <code>{stat.get('uploads_total', 0)}</code>",
            f"⏱ Last: <code>{esc(stat.get('last_active') or 'Unknown')}</code>",
        ], icon="👤"),
        parse_mode=ParseMode.HTML,
    )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    body = " ".join(context.args).strip()
    if not body:
        await update.effective_message.reply_text("Usage: /broadcast MESSAGE")
        return
    targets = approved_users | premium_users | {OWNER_ID}
    sent = failed = 0
    status = await update.effective_message.reply_text(
        premium_box("ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ", ["📣 <i>Sending to all users…</i>"], icon="📣"),
        parse_mode=ParseMode.HTML,
    )
    for uid in targets:
        try:
            await context.bot.send_message(uid, premium_box(BRAND_NAME, [f"📣 {esc(body)}"], icon="📢"), parse_mode=ParseMode.HTML)
            sent += 1
            await asyncio.sleep(0.05)
        except (Forbidden, TelegramError):
            failed += 1
    await status.edit_text(
        premium_box("ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ", [
            f"✅ Sent: <code>{sent}</code>",
            f"❌ Failed: <code>{failed}</code>",
        ], icon="📣"),
        parse_mode=ParseMode.HTML,
    )


async def maintenance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global maintenance_mode
    if not owner_only(update):
        return
    if not context.args or context.args[0].lower() not in {"on", "off"}:
        await update.effective_message.reply_text("Usage: /maintenance on|off")
        return
    maintenance_mode = context.args[0].lower() == "on"
    save_data()
    await update.effective_message.reply_text(
        f"🛠 Maintenance <b>{'ON' if maintenance_mode else 'OFF'}</b>", parse_mode=ParseMode.HTML
    )


async def startall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    started = failed = 0
    for uid, items in running_scripts.items():
        async with lock_for(uid):
            for item in items:
                if item.running:
                    continue
                try:
                    spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                    await asyncio.sleep(0.15)
                    if item.running:
                        started += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
    await update.effective_message.reply_text(
        premium_box("sᴛᴀʀᴛ ᴀʟʟ", [
            f"✅ Started: <code>{started}</code>",
            f"❌ Failed: <code>{failed}</code>",
        ], icon="▶️"),
        parse_mode=ParseMode.HTML,
    )


async def stopalladmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    stopped = 0
    for items in running_scripts.values():
        for item in items:
            if item.running and kill_process(item):
                stopped += 1
    await update.effective_message.reply_text(f"🧨 Stopped <code>{stopped}</code> projects.", parse_mode=ParseMode.HTML)


async def cleanup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    removed = 0
    for uid, items in list(running_scripts.items()):
        kept: list[ScriptProcess] = []
        for item in items:
            if Path(item.folder).exists() and Path(item.entry_file).exists():
                kept.append(item)
            else:
                removed += 1
        running_scripts[uid] = kept
    save_projects()
    await update.effective_message.reply_text(
        premium_box("ᴄʟᴇᴀɴᴜᴘ", [f"🧹 Removed <code>{removed}</code> record(s)"], icon="🧹"),
        parse_mode=ParseMode.HTML,
    )


async def install_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    raw = " ".join(context.args).strip()
    if not raw:
        await update.effective_message.reply_text(
            premium_box("ᴘᴀᴄᴋᴀɢᴇ ɪɴsᴛᴀʟʟᴇʀ", [
                "<b>Python:</b> <code>/install beautifulsoup4</code>",
                "<b>Python:</b> <code>/install pip3 install requests</code>",
                "",
                "🔐 Owner-only • no shell execution",
            ], icon="📦"),
            parse_mode=ParseMode.HTML,
        )
        return
    try:
        args = shlex.split(raw)
    except ValueError as exc:
        await update.effective_message.reply_text(f"❌ {exc}")
        return
    if args[:2] in (["pip", "install"], ["pip3", "install"]):
        packages = args[2:]
    elif args and args[0].lower() in {"npm", "node", "yarn"}:
        await update.effective_message.reply_text("❌ Python-only. Node packages disabled.")
        return
    else:
        packages = args
    pattern = re.compile(r"^[A-Za-z0-9@._/+:-]+(?:[<>=!~]{1,2}[A-Za-z0-9.*+_-]+)?$")
    if not packages or len(packages) > 15 or any(not pattern.fullmatch(x) for x in packages):
        await update.effective_message.reply_text("❌ Invalid package names.")
        return
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *packages]
    status = await update.effective_message.reply_text(
        premium_box("ɪɴsᴛᴀʟʟɪɴɢ", [f"📦 <code>{esc(' '.join(packages))}</code>"], icon="⏳"),
        parse_mode=ParseMode.HTML,
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(BASE_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=INSTALL_TIMEOUT_SECONDS)
        output = stdout.decode("utf-8", errors="replace")[-MAX_INSTALL_OUTPUT_CHARS:]
        ok = proc.returncode == 0
        await status.edit_text(
            premium_box("ɪɴsᴛᴀʟʟᴇᴅ" if ok else "ꜰᴀɪʟᴇᴅ", [
                f"📦 <code>{esc(' '.join(packages))}</code>",
                "",
                f"<pre>{esc(output or 'No output')}</pre>",
            ], icon="✅" if ok else "❌"),
            parse_mode=ParseMode.HTML,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        await status.edit_text(premium_box("ᴛɪᴍᴇᴏᴜᴛ", [f"⚠️ Exceeded {INSTALL_TIMEOUT_SECONDS}s"], icon="⏱"), parse_mode=ParseMode.HTML)
    except Exception as exc:
        await status.edit_text(f"❌ <code>{esc(exc)}</code>", parse_mode=ParseMode.HTML)


async def installed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pip", "list", "--format=columns",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace")[-MAX_INSTALL_OUTPUT_CHARS:]
    await update.effective_message.reply_text(
        premium_box("ɪɴsᴛᴀʟʟᴇᴅ", [f"<pre>{esc(output)}</pre>"], icon="📚"),
        parse_mode=ParseMode.HTML,
    )


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    save_data()
    save_projects()
    files_sent = 0
    for path in (DATA_FILE, PROJECTS_FILE):
        if path.exists():
            await update.effective_message.reply_document(
                document=InputFile(str(path)),
                caption=f"📦 {BRAND_NAME} backup: {path.name}",
            )
            files_sent += 1
    if not files_sent:
        await update.effective_message.reply_text("❌ No backup files.")


# ═════════════════════════════════════════════════════════════════════════════
# 🔐  FORCE-JOIN MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════


async def verifycache_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    now = time.time()
    ttl = FORCE_JOIN_CACHE_TTL
    ch = sum(1 for e in chat_membership.values() if e.get("channel", {}).get("joined") and now - e["channel"]["at"] < ttl)
    gr = sum(1 for e in chat_membership.values() if e.get("group", {}).get("joined") and now - e["group"]["at"] < ttl)
    both = sum(
        1 for e in chat_membership.values()
        if e.get("channel", {}).get("joined") and e.get("group", {}).get("joined")
        and now - e["channel"]["at"] < ttl and now - e["group"]["at"] < ttl
    )
    await update.effective_message.reply_text(
        premium_box("ᴊᴏɪɴ ᴄᴀᴄʜᴇ", [
            f"👥 Cached: <code>{len(chat_membership)}</code>",
            f"📣 Channel fresh: <code>{ch}</code>",
            f"👥 Group fresh: <code>{gr}</code>",
            f"✅ Both fresh: <code>{both}</code>",
            f"🔑 Bypassed: <code>{len(forcejoin_bypass_users)}</code>",
            f"⏱ TTL: <code>{human_duration(ttl)}</code>",
        ], icon="🔐"),
        parse_mode=ParseMode.HTML,
    )


async def bypassjoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args or not context.args[0].isdigit():
        return
    uid = int(context.args[0])
    forcejoin_bypass_users.add(uid)
    save_join_cache()
    audit(update.effective_user.id, "bypass_join", str(uid))
    await update.effective_message.reply_text(
        premium_box("ʙʏᴘᴀss ᴀᴅᴅᴇᴅ", [
            f"🔓 <tg-spoiler><code>{uid}</code></tg-spoiler> bypasses force-join.",
            f"Revoke: <code>/unbypassjoin {uid}</code>",
        ], icon="🔓"),
        parse_mode=ParseMode.HTML,
    )


async def unbypassjoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args or not context.args[0].isdigit():
        return
    uid = int(context.args[0])
    forcejoin_bypass_users.discard(uid)
    chat_membership.pop(str(uid), None)
    save_join_cache()
    await update.effective_message.reply_text(f"✅ Bypass + cache cleared for <code>{uid}</code>.", parse_mode=ParseMode.HTML)


async def clearverify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args or not context.args[0].isdigit():
        return
    uid = int(context.args[0])
    had = chat_membership.pop(str(uid), None) is not None
    save_join_cache()
    await update.effective_message.reply_text(
        f"✅ Cache {'cleared' if had else 'already empty'} for <code>{uid}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def clearallverify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    count = len(chat_membership)
    chat_membership.clear()
    save_join_cache()
    audit(update.effective_user.id, "clear_all_verify", detail=str(count))
    await update.effective_message.reply_text(
        premium_box("ᴄᴀᴄʜᴇ ᴄʟᴇᴀʀᴇᴅ", [
            f"🗑 Cleared <code>{count}</code> entries",
            f"🔑 Bypass list: <code>{len(forcejoin_bypass_users)}</code>",
        ], icon="🧹"),
        parse_mode=ParseMode.HTML,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 📥  FILE HOSTING
# ═════════════════════════════════════════════════════════════════════════════


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return
    user_id = update.effective_user.id
    document = update.effective_message.document
    if not document:
        return
    async with lock_for(user_id):
        reset_daily(user_id)
        stat = get_stat(user_id)
        if stat["uploads_today"] >= daily_limit(user_id):
            await update.effective_message.reply_text("⚠️ Daily upload limit reached.")
            return
        if not is_premium(user_id) and get_credits(user_id) < CREDIT_PER_UPLOAD:
            await update.effective_message.reply_text("💳 Not enough credits.")
            return
        if active_count(user_id) >= running_limit(user_id):
            await update.effective_message.reply_text(f"⚠️ Running limit: {running_limit(user_id)}.")
            return
        used_mb = user_storage_mb(user_id)
        quota_mb = storage_limit_mb(user_id)
        incoming_mb = (document.file_size or 0) / (1024 * 1024)
        if not is_owner(user_id) and used_mb + incoming_mb > quota_mb:
            await update.effective_message.reply_text(f"💾 Quota: {used_mb:.1f}/{quota_mb} MB.")
            return
        filename = clean_filename(document.file_name or "project")
        suffix = Path(filename).suffix.lower()
        if suffix not in {".py", ".zip"}:
            await update.effective_message.reply_text("❌ Python-only: send .py or .zip.")
            return
        size = document.file_size or 0
        if size > MAX_FILE_MB * 1024 * 1024:
            await update.effective_message.reply_text(f"❌ Max {MAX_FILE_MB} MB.")
            return
        progress = await update.effective_message.reply_text(
            premium_box("ᴜᴘʟᴏᴀᴅ ʀᴇᴄᴇɪᴠᴇᴅ", [
                f"📄 <code>{esc(filename)}</code>",
                f"📦 Size: <code>{size / (1024 * 1024):.2f} MB</code>",
                "",
                "⚙️ Preparing hosting environment…",
            ], icon="📥"),
            parse_mode=ParseMode.HTML,
        )
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        folder = user_folder(user_id) / f"{stamp}_{Path(filename).stem}"
        folder.mkdir(parents=True)
        uploaded = folder / filename
        try:
            tg_file = await context.bot.get_file(document.file_id)
            await tg_file.download_to_drive(str(uploaded))
            await progress.edit_text(
                premium_box("ɪɴsᴘᴇᴄᴛɪɴɢ", ["🔍 Analyzing project…"], icon="🔎"),
                parse_mode=ParseMode.HTML,
            )
            if suffix == ".zip":
                safe_extract_zip(uploaded, folder)
                uploaded.unlink(missing_ok=True)
                entry = detect_entry(folder)
            else:
                entry = uploaded
            if not entry:
                raise ValueError("No runnable Python entry found.")
            log_path = folder / "runtime.log"
            risk, findings = scan_project(folder) if SECURITY_SCAN_ENABLED else ("DISABLED", [])
            if risk == "HIGH" and not is_owner(user_id):
                raise ValueError("High-risk code: " + "; ".join(findings[:3]))
            dependency_note = await asyncio.to_thread(install_project_dependencies, folder, entry, log_path)
            item = spawn_script(None, entry, folder, log_path)
            scripts_for(user_id).append(item)
            save_projects()
            await asyncio.sleep(LAUNCH_CHECK_SECONDS)
            if not item.running:
                error = (
                    log_path.read_text("utf-8", errors="replace")[-MAX_LOG_CHARS:]
                    if log_path.exists() else "No error output."
                )
                scripts_for(user_id).remove(item)
                save_projects()
                safe_remove_folder(item.folder)
                await progress.edit_text(
                    premium_box("ʟᴀᴜɴᴄʜ ꜰᴀɪʟᴇᴅ", [f"<pre>{esc(error)}</pre>"], icon="❌"),
                    parse_mode=ParseMode.HTML,
                )
                return
            if not is_premium(user_id):
                set_credits(user_id, get_credits(user_id) - CREDIT_PER_UPLOAD)
            stat["uploads_today"] += 1
            stat["uploads_total"] += 1
            stat["last_upload_date"] = date.today().isoformat()
            save_data()
            pending_project_names[user_id] = item
            risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "DISABLED": "⚪"}.get(risk, "⚪")
            await progress.edit_text(
                premium_box("ʜᴏsᴛɪɴɢ sᴛᴀʀᴛᴇᴅ", [
                    f"🧩 Entry: <code>{esc(entry.name)}</code>",
                    f"🆔 PID: <tg-spoiler><code>{item.pid}</code></tg-spoiler>",
                    f"🟢 Status: <b>Online</b>",
                    f"{risk_icon} Scan: <code>{esc(risk)}</code>",
                    f"📦 Deps: {esc(dependency_note)}",
                    f"💎 Credits: <code>{get_credits(user_id)}</code>",
                    "",
                    "📝 <b>Now send a custom name.</b>",
                    "Example: <code>My Bot</code>",
                    "Or <code>/skip</code> to keep filename.",
                ], icon="✅"),
                parse_mode=ParseMode.HTML,
                reply_markup=project_control_buttons(len(scripts_for(user_id)) - 1, True),
            )
        except Exception as exc:
            logger.exception("Upload failed")
            shutil.rmtree(folder, ignore_errors=True)
            await progress.edit_text(
                premium_box("ᴜᴘʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ", [f"<code>{esc(exc)}</code>"], icon="❌"),
                parse_mode=ParseMode.HTML,
            )


# ═════════════════════════════════════════════════════════════════════════════
# 💬  TEXT HANDLER
# ═════════════════════════════════════════════════════════════════════════════


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    user = update.effective_user
    if not user:
        return
    touch_user(user)

    if user.id in pending_project_names:
        item = pending_project_names.pop(user.id)
        project_name = clean_project_name(text)
        if not project_name:
            pending_project_names[user.id] = item
            await update.effective_message.reply_text("❌ Invalid name.")
            return
        item.display_name = project_name
        save_projects()
        await update.effective_message.reply_text(
            premium_box("ɴᴀᴍᴇ sᴀᴠᴇᴅ", [
                f"✅ <b>{esc(project_name)}</b>",
                f"Status: {'🟢 Online' if item.running else '🔴 Offline'}",
            ], icon="💾"),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(user.id),
        )
        return

    if not is_approved(user.id):
        if ACCESS_PASSWORD and text == ACCESS_PASSWORD:
            approved_users.add(user.id)
            banned_users.discard(user.id)
            user_credits.setdefault(str(user.id), DEFAULT_CREDITS)
            save_data()
            await update.effective_message.reply_text(
                premium_box("ᴀᴄᴄᴇss ᴀᴄᴛɪᴠᴀᴛᴇᴅ", ["✅ Send /start to begin."], icon="✨"),
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.effective_message.reply_text(
                premium_box("ɪɴᴠᴀʟɪᴅ", ["🔐 Wrong password.", "Use <code>/request</code>."], icon="⚠️"),
                parse_mode=ParseMode.HTML,
            )
        return

    if text == "🚀 ᴅᴇᴘʟᴏʏ ᴘʀᴏᴊᴇᴄᴛ":
        await update.effective_message.reply_text(
            premium_box("ᴅᴇᴘʟᴏʏ ɴᴇᴡ ᴘʀᴏᴊᴇᴄᴛ", [
                "📦 <b>Supported:</b>",
                "  • <code>.py</code> — single file",
                "  • <code>.zip</code> — project archive",
                "━━━━━━━━━━━━━━━━━━━━",
                "🔍 <b>Auto-entry:</b>",
                "  <code>main.py</code> <code>bot.py</code> <code>app.py</code>",
                "  <code>server.py</code> <code>run.py</code>",
                "",
                "⚡ <i>Send your file now.</i>",
            ], icon="🚀"),
            parse_mode=ParseMode.HTML,
        )
    elif text in {"📁 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs", "🎛 ᴄᴏɴᴛʀᴏʟs"}:
        await projects_cmd(update, context)
    elif text == "📋 ʟɪᴠᴇ ʟᴏɢs":
        await logs_cmd(update, context)
    elif text == "💎 ᴡᴀʟʟᴇᴛ":
        await credits_cmd(update, context)
    elif text == "👤 ᴀᴄᴄᴏᴜɴᴛ":
        await update.effective_message.reply_text(
            home_text(user.id), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
    elif text == "🌟 ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs":
        await update.effective_message.reply_text(
            premium_box(f"{BRAND_NAME} ᴘʟᴀɴs", [
                "✅ <b>Free</b>",
                f"  📤 Daily: <code>{DAILY_UPLOAD_LIMIT}</code>",
                f"  🖥 Slots: <code>{MAX_RUNNING_PER_USER}</code>",
                f"  💳 Cost: <code>{CREDIT_PER_UPLOAD}</code> credit",
                "━━━━━━━━━━━━━━━━━━━━",
                "💎 <b>Premium</b>",
                f"  📤 Daily: <code>{PREMIUM_DAILY_UPLOAD_LIMIT}</code>",
                f"  🖥 Slots: <code>{PREMIUM_MAX_RUNNING_PER_USER}</code>",
                "  ✨ Unlimited uploads",
                f"  🎁 Bonus: <code>+{PREMIUM_BONUS_CREDITS}</code> credits",
                "",
                "💬 <i>Contact owner to upgrade.</i>",
            ], icon="🌟"),
            parse_mode=ParseMode.HTML,
        )
    elif text == "🛟 sᴜᴘᴘᴏʀᴛ":
        await update.effective_message.reply_text(
            premium_box("sᴜᴘᴘᴏʀᴛ", [
                f"👤 Owner: {esc(OWNER_USERNAME)}",
                f"📣 Channel: {esc(MAIN_CHANNEL_LINK)}",
                f"👥 Group: {esc(SUPPORT_GROUP_LINK)}",
                f"💬 Direct: {esc(SUPPORT_LINK)}",
            ], icon="🛟"),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    elif text == "⚡ ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴄᴇɴᴛᴇʀ ⚡":
        await admin_cmd(update, context)
    else:
        await update.effective_message.reply_text(
            premium_box("ᴛɪᴘ", ["💡 Send <code>.py</code> or <code>.zip</code> to deploy."], icon="🤖"),
            parse_mode=ParseMode.HTML,
        )


# ═════════════════════════════════════════════════════════════════════════════
# 🎭  CALLBACK HANDLER
# ═════════════════════════════════════════════════════════════════════════════


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data or ""

    if data == "join:check":
        chat_membership.pop(str(uid), None)
        missing = await get_membership(uid, context)
        if missing["channel"] and missing["group"]:
            await edit_message(query, premium_box("ᴠᴇʀɪꜰɪᴇᴅ", [
                "✅ <b>Membership confirmed!</b>",
                "Send /start to open the menu.",
            ], icon="🎉"))
        else:
            lines = ["🔒 <b>Still missing:</b>", ""]
            if not missing["channel"]:
                lines.append("📣 Channel")
            if not missing["group"]:
                lines.append("👥 Group")
            await edit_message(query, premium_box("ᴠᴇʀɪꜰʏ", lines, icon="🔒"), join_buttons(missing))
        return

    if data.startswith("request:"):
        if not is_owner(uid):
            await query.answer("Owner only", show_alert=True)
            return
        _, action, raw_id = data.split(":")
        target = int(raw_id)
        if action == "approve":
            approved_users.add(target)
            banned_users.discard(target)
            user_credits.setdefault(str(target), DEFAULT_CREDITS)
            save_data()
            try:
                await context.bot.send_message(target, f"✅ Access approved for {BRAND_NAME}. Send /start.")
            except TelegramError:
                pass
            await edit_message(query, f"✅ Approved <code>{target}</code>.")
        else:
            try:
                await context.bot.send_message(target, "❌ Access request rejected.")
            except TelegramError:
                pass
            await edit_message(query, f"❌ Rejected <code>{target}</code>.")
        return

    if data.startswith("admin:"):
        if not is_admin(uid):
            await query.answer("Admin only", show_alert=True)
            return
        action = data.split(":", 1)[1]
        read_only = {
            "close", "overview", "users", "premium", "credits", "banned",
            "processes", "analytics", "watchdog", "panelreminder", "codes",
            "hoststatus", "security", "backupinfo",
        }
        if not is_owner(uid) and action not in read_only:
            await query.answer("Owner required", show_alert=True)
            return

        if action == "close":
            await edit_message(query, "✅ Admin Center closed.")
        elif action == "overview":
            await edit_message(query, admin_overview(), admin_buttons())
        elif action == "users":
            rows = [
                f"• <tg-spoiler><code>{u}</code></tg-spoiler> @{esc(get_stat(u).get('username') or 'not_set')}"
                for u in sorted(approved_users)
            ]
            await edit_message(query, premium_box("ᴀᴘᴘʀᴏᴠᴇᴅ ᴜsᴇʀs", rows[:80] or ["None"], icon="👥"), admin_buttons())
        elif action == "premium":
            rows = [f"• <tg-spoiler><code>{x}</code></tg-spoiler>" for x in sorted(premium_users)]
            await edit_message(query, premium_box("ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs", rows or ["None"], icon="💎"), admin_buttons())
        elif action == "credits":
            rows = [f"• <code>{k}</code>: <b>{v}</b>" for k, v in sorted(user_credits.items())]
            await edit_message(query, premium_box("ᴄʀᴇᴅɪᴛ ᴡᴀʟʟᴇᴛs", rows[:100] or ["None"], icon="💳"), admin_buttons())
        elif action == "banned":
            rows = [f"• <tg-spoiler><code>{x}</code></tg-spoiler>" for x in sorted(banned_users)]
            await edit_message(query, premium_box("ʙᴀɴɴᴇᴅ", rows or ["None"], icon="🚫"), admin_buttons())
        elif action == "processes":
            rows = [
                f"• <code>{u}</code> {esc(i.display_name)} {'🟢' if i.running else '🔴'}"
                for u, items in running_scripts.items() for i in items
            ]
            await edit_message(query, premium_box("ʜᴏsᴛᴇᴅ", rows[:100] or ["None"], icon="🚀"), admin_buttons())
        elif action == "startall":
            started = failed = 0
            for user_id, items in running_scripts.items():
                async with lock_for(user_id):
                    for item in items:
                        if item.running:
                            continue
                        try:
                            spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                            await asyncio.sleep(0.1)
                            if item.running:
                                started += 1
                            else:
                                failed += 1
                        except Exception:
                            failed += 1
            await edit_message(query, premium_box("sᴛᴀʀᴛ ᴀʟʟ", [
                f"✅ Started: <code>{started}</code>",
                f"❌ Failed: <code>{failed}</code>",
            ], icon="▶️"), admin_buttons())
        elif action == "stopall":
            stopped = 0
            for items in running_scripts.values():
                for item in items:
                    if item.running and kill_process(item):
                        stopped += 1
            await edit_message(query, f"🧨 Stopped <code>{stopped}</code> projects.", admin_buttons())
        elif action == "forcejoin":
            admins_line = ", ".join(f"<code>{u}</code>" for u in admin_roles) or "—"
            await edit_message(query, premium_box("ꜰᴏʀᴄᴇ ᴊᴏɪɴ", [
                f"Status: <code>{'ON' if FORCE_JOIN_ENABLED else 'OFF'}</code>",
                f"📣 Channel: <code>{esc(MAIN_CHANNEL_USERNAME)}</code>",
                f"👥 Group: <code>{esc(SUPPORT_GROUP_USERNAME)}</code>",
                "",
                "<b>Bypass exempts:</b>",
                f"👑 Owner: <code>{OWNER_ID}</code>",
                f"🎖 Admins: {admins_line}",
                "",
                "Toggle: <code>/forcejoin on|off</code>",
            ], icon="🔐"), admin_buttons())
        elif action == "maintenance":
            global maintenance_mode
            maintenance_mode = not maintenance_mode
            save_data()
            await edit_message(query, admin_overview(), admin_buttons())
        elif action == "keepalive":
            await edit_message(query, keepalive_text(), admin_buttons())
        elif action == "hoststatus":
            await edit_message(query, host_stats_text(), admin_buttons())
        elif action == "security":
            await edit_message(query, security_text(), admin_buttons())
        elif action == "backupinfo":
            backups = sorted(BACKUPS_DIR.glob("elevatex_backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
            lines = [
                f"⏱ Interval: <code>{BACKUP_INTERVAL_HOURS}h</code>",
                f"📦 Stored: <code>{len(backups)}</code>",
                "Use <code>/backup</code> to download.",
            ]
            if backups:
                lines.append(f"🔖 Latest: <code>{esc(backups[0].name)}</code>")
            await edit_message(query, premium_box("ʙᴀᴄᴋᴜᴘs", lines, icon="💾"), admin_buttons())
        elif action == "analytics":
            total_projects = sum(len(x) for x in running_scripts.values())
            running = sum(i.running for x in running_scripts.values() for i in x)
            await edit_message(query, premium_box("ᴀɴᴀʟʏᴛɪᴄs", [
                f"👥 Users: <code>{len(user_stats)}</code>",
                f"🧩 Projects: <code>{total_projects}</code>",
                f"🟢 Running: <code>{running}</code>",
                f"🎟 Codes: <code>{len(redeem_codes)}</code>",
            ], icon="📈"), admin_buttons())
        elif action == "watchdog":
            await edit_message(query, premium_box("ᴡᴀᴛᴄʜᴅᴏɢ", [
                f"Status: <code>{'ON' if watchdog_enabled else 'OFF'}</code>",
                f"Interval: <code>{watchdog_interval}s</code>",
                f"Restarts: <code>{watchdog_restarts}</code>",
            ], icon="🛡"), admin_buttons())
        elif action == "panelreminder":
            await edit_message(query, premium_box("ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ", [
                f"Status: <code>{'ON' if panel_reminder_enabled else 'OFF'}</code>",
                f"Cycle: <code>{PANEL_REMINDER_HOURS}h</code>",
                "Use <code>/panelvisited</code> after visiting.",
            ], icon="⏰"), admin_buttons())
        elif action == "panelvisited":
            if not is_owner(uid):
                await query.answer("Owner only", show_alert=True)
                return
            global panel_last_confirmed_at, panel_last_reminder_at
            panel_last_confirmed_at = time.time()
            panel_last_reminder_at = 0.0
            save_v7_data()
            await edit_message(query, premium_box("ᴘᴀɴᴇʟ ᴠɪsɪᴛ", [
                "✅ Visit confirmed.",
                "Next reminder: <code>3 days</code>",
            ], icon="✅"), admin_buttons())
        elif action == "codes":
            rows = [
                f"• <code>{esc(c)}</code> — {'OFF' if r.get('disabled') else 'ON'}"
                for c, r in list(redeem_codes.items())[:25]
            ]
            await edit_message(query, premium_box("ᴄᴏᴅᴇs", rows or ["No codes."], icon="🎟"), admin_buttons())
        elif action == "cleanup":
            removed = 0
            for user_id, items in list(running_scripts.items()):
                kept = [i for i in items if Path(i.folder).exists() and Path(i.entry_file).exists()]
                removed += len(items) - len(kept)
                running_scripts[user_id] = kept
            save_projects()
            await edit_message(query, f"🧹 Removed <code>{removed}</code> records.", admin_buttons())
        elif action == "commands":
            await edit_message(query, admin_commands_text(), admin_buttons())
        return

    if not is_approved(uid) or uid in banned_users:
        await query.answer("Access restricted", show_alert=True)
        return

    if data == "project:list":
        await edit_message(query, projects_text(uid), project_list_buttons(uid))
        return

    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "project":
        return
    action = parts[1]
    try:
        index = int(parts[2])
        item = scripts_for(uid)[index]
    except (ValueError, IndexError):
        await query.answer("Project not found", show_alert=True)
        return

    async with lock_for(uid):
        if action == "view":
            status = "🟢 Online" if item.running else f"🔴 Offline ({esc(item.exit_code)})"
            text = premium_box(f"ᴘʀᴏᴊᴇᴄᴛ › {item.display_name}", [
                f"Status: {status}",
                f"Entry: <code>{esc(Path(item.entry_file).name)}</code>",
                f"PID: <tg-spoiler><code>{esc(item.pid)}</code></tg-spoiler>",
                f"Uptime: <code>{uptime(item.started_at) if item.running else '—'}</code>",
                f"Restarts: <code>{item.restarts}</code>",
            ], icon="🧩")
            await edit_message(query, text, project_control_buttons(index, item.running))
        elif action == "stop":
            ok = kill_process(item)
            await edit_message(
                query,
                premium_box("sᴛᴏᴘᴘᴇᴅ" if ok else "ꜰᴀɪʟᴇᴅ", [
                    f"🔴 <b>{esc(item.display_name)}</b>" if ok else "❌ Could not stop."
                ], icon="⏹" if ok else "⚠️"),
                project_control_buttons(index, False),
            )
        elif action in {"start", "restart"}:
            if item.running:
                kill_process(item)
            item.restarts += 1
            try:
                spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                await asyncio.sleep(0.5)
                await edit_message(
                    query,
                    premium_box("sᴛᴀʀᴛᴇᴅ" if item.running else "ꜰᴀɪʟᴇᴅ", [
                        f"🟢 <b>{esc(item.display_name)}</b>"
                        if item.running else "❌ Exited after launch.",
                        f"🆔 PID: <tg-spoiler><code>{item.pid}</code></tg-spoiler>",
                    ], icon="▶️" if item.running else "❌"),
                    project_control_buttons(index, item.running),
                )
            except Exception as exc:
                await edit_message(
                    query, f"❌ Start failed: <code>{esc(exc)}</code>",
                    project_control_buttons(index, False),
                )
        elif action == "logs":
            path = Path(item.log_path)
            content = path.read_text("utf-8", errors="replace")[-MAX_LOG_CHARS:] if path.exists() else "No output."
            await edit_message(
                query,
                premium_box(f"ʟᴏɢs › {item.display_name}", [f"<pre>{esc(content)}</pre>"], icon="🧾"),
                project_control_buttons(index, item.running),
            )
        elif action == "logfile":
            path = Path(item.log_path)
            if path.exists():
                await context.bot.send_document(uid, InputFile(str(path)), caption=f"Logs: {item.display_name}")
                await query.answer("Log file sent")
            else:
                await query.answer("Log file not found", show_alert=True)
        elif action == "rename":
            pending_project_names[uid] = item
            await query.message.reply_text("✏️ Send the new project name.")
        elif action == "delete":
            if item.running:
                await query.answer("Stop the project first", show_alert=True)
                return
            safe_remove_folder(item.folder)
            scripts_for(uid).pop(index)
            save_projects()
            await edit_message(query, projects_text(uid), project_list_buttons(uid))


# ═════════════════════════════════════════════════════════════════════════════
# 🎁  V7/V9 EXTRA COMMANDS
# ═════════════════════════════════════════════════════════════════════════════


async def setplan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) < 3:
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    plan, duration = context.args[1].lower(), context.args[2].lower()
    if plan not in {"free", "basic", "premium", "business", "lifetime"}:
        return
    if plan == "free":
        premium_users.discard(uid)
        premium_expiry.pop(str(uid), None)
    else:
        premium_users.add(uid)
        if duration == "lifetime" or plan == "lifetime":
            premium_expiry[str(uid)] = "lifetime"
        else:
            delta = parse_duration(duration)
            if not delta:
                return
            premium_expiry[str(uid)] = (datetime.now() + delta).isoformat(timespec="seconds")
    user_plans[str(uid)] = plan
    save_data()
    save_v7_data()
    audit(update.effective_user.id, "setplan", str(uid), f"{plan} {duration}")
    await update.effective_message.reply_text(
        premium_box("ᴘʟᴀɴ ᴜᴘᴅᴀᴛᴇᴅ", [
            f"👤 <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"💎 Plan: <b>{esc(plan.title())}</b>",
            f"⏱ Duration: <code>{esc(duration)}</code>",
        ], icon="✅"),
        parse_mode=ParseMode.HTML,
    )


async def plans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    exp = premium_expiry.get(str(uid), "—")
    await update.effective_message.reply_text(
        premium_box("ᴘʟᴀɴs", [
            f"Current: <b>{esc(plan_name(uid))}</b>",
            f"Expiry: <code>{esc(exp)}</code>",
            "",
            "✅ <b>Free</b> — 1 daily / 2 running / 128 MB",
            "💎 <b>Basic</b> — 5 daily / 3 running / 256 MB",
            "🌟 <b>Premium</b> — 25 daily / 10 running / 512 MB",
            "👑 <b>Business</b> — 100 daily / 30 running / 1024 MB",
        ], icon="🌟"),
        parse_mode=ParseMode.HTML,
    )


async def createcode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) < 4:
        return
    code = context.args[0].upper()
    kind = context.args[1].lower()
    value = context.args[2]
    try:
        max_uses = int(context.args[3])
    except ValueError:
        return
    expiry = ""
    if len(context.args) > 4:
        d = parse_duration(context.args[4])
        expiry = (datetime.now() + d).isoformat(timespec="seconds") if d else ""
    redeem_codes[code] = {
        "kind": kind, "value": value, "max_uses": max_uses,
        "used_by": [], "expiry": expiry, "created_by": update.effective_user.id,
    }
    save_v7_data()
    await update.effective_message.reply_text(
        premium_box("ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ", [f"🎟 <code>{esc(code)}</code>"], icon="✅"),
        parse_mode=ParseMode.HTML,
    )


async def redeem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        return
    uid = update.effective_user.id
    code = context.args[0].upper()
    row = redeem_codes.get(code)
    if not row or row.get("disabled"):
        await update.effective_message.reply_text("❌ Invalid/disabled code.")
        return
    if uid in row.get("used_by", []):
        await update.effective_message.reply_text("❌ Already used.")
        return
    if len(row.get("used_by", [])) >= int(row.get("max_uses", 0)):
        await update.effective_message.reply_text("❌ Limit reached.")
        return
    if row.get("expiry") and datetime.fromisoformat(row["expiry"]) <= datetime.now():
        await update.effective_message.reply_text("❌ Expired.")
        return
    if row.get("kind") == "credits":
        set_credits(uid, get_credits(uid) + int(row["value"]))
    elif row.get("kind") == "plan":
        premium_users.add(uid)
        user_plans[str(uid)] = row["value"].lower()
        premium_expiry[str(uid)] = (datetime.now() + timedelta(days=30)).isoformat(timespec="seconds")
        save_data()
    else:
        await update.effective_message.reply_text("❌ Invalid config.")
        return
    row.setdefault("used_by", []).append(uid)
    save_v7_data()
    await update.effective_message.reply_text("✅ Code redeemed!")


async def setenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context) or len(context.args) < 3:
        return
    found = find_project(update.effective_user.id, context.args[0])
    if not found:
        await update.effective_message.reply_text("Project not found.")
        return
    _, item = found
    key = context.args[1]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", key):
        await update.effective_message.reply_text("Invalid variable name.")
        return
    project_envs.setdefault(project_key(item), {})[key] = " ".join(context.args[2:])
    save_v7_data()
    await update.effective_message.reply_text(f"✅ <code>{esc(key)}</code> saved. Restart to apply.", parse_mode=ParseMode.HTML)


async def env_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, context.args[0])
    if not found:
        return
    _, item = found
    envs = project_envs.get(project_key(item), {})
    lines = [f"<code>{esc(k)}</code> = ••••••••" for k in envs] or ["No variables."]
    await update.effective_message.reply_text(premium_box("ᴇɴᴠ", lines, icon="🔐"), parse_mode=ParseMode.HTML)


async def delenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context) or len(context.args) < 2:
        return
    found = find_project(update.effective_user.id, context.args[0])
    if not found:
        return
    _, item = found
    project_envs.get(project_key(item), {}).pop(context.args[1], None)
    save_v7_data()
    await update.effective_message.reply_text("✅ Removed.")


async def autorestart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context) or len(context.args) < 2:
        return
    found = find_project(update.effective_user.id, context.args[0])
    if not found:
        return
    _, item = found
    item.auto_restart = context.args[1].lower() in {"on", "yes", "1"}
    item.restarts = 0
    save_projects()
    await update.effective_message.reply_text(f"♻️ Auto restart: {'ON' if item.auto_restart else 'OFF'}")


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, context.args[0])
    if not found:
        return
    _, item = found
    r = project_resources(item)
    await update.effective_message.reply_text(
        premium_box(f"ʜᴇᴀʟᴛʜ › {item.display_name}", [
            f"Status: {'🟢 Online' if item.running else '🔴 Offline'}",
            f"PID: <tg-spoiler><code>{item.pid}</code></tg-spoiler>",
            f"CPU: <code>{r['cpu']}</code>",
            f"RAM: <code>{r['ram']}</code>",
            f"Disk: <code>{r['disk']}</code>",
            f"Uptime: <code>{uptime(item.started_at) if item.running else '—'}</code>",
            f"Restarts: <code>{item.restarts}</code>",
        ], icon="📊"),
        parse_mode=ParseMode.HTML,
    )


async def auditlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    rows = audit_log[-30:]
    text = "\n".join(f"{x['time']} | {x['actor']} | {x['action']} | {x['target']}" for x in rows) or "No entries"
    await update.effective_message.reply_text(f"<pre>{esc(text[-3800:])}</pre>", parse_mode=ParseMode.HTML)


async def finduser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    q = " ".join(context.args).lstrip("@").casefold()
    rows = []
    for uid, st in user_stats.items():
        hay = f"{uid} {st.get('username', '')} {st.get('first_name', '')}".casefold()
        if q in hay:
            rows.append(f"• <tg-spoiler><code>{uid}</code></tg-spoiler> @{esc(st.get('username') or 'not_set')}")
    await update.effective_message.reply_text(
        premium_box("ꜰᴏᴜɴᴅ", rows[:30] or ["No match."], icon="🔎"),
        parse_mode=ParseMode.HTML,
    )


async def allprojects_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    rows = []
    for uid, items in sorted(running_scripts.items()):
        for i in items:
            rows.append(f"• <code>{uid}</code> | <b>{esc(i.display_name)}</b> | {'🟢' if i.running else '🔴'}")
    await update.effective_message.reply_text(
        premium_box("ᴀʟʟ ᴘʀᴏᴊᴇᴄᴛs", rows[:70] or ["None."], icon="📂"),
        parse_mode=ParseMode.HTML,
    )


async def restartall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    restarted = failed = 0
    for items in running_scripts.values():
        for item in items:
            try:
                if item.running:
                    kill_process(item)
                spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                restarted += 1
            except Exception:
                failed += 1
    save_projects()
    await update.effective_message.reply_text(
        premium_box("ʀᴇsᴛᴀʀᴛ ᴀʟʟ", [
            f"♻️ Restarted: <code>{restarted}</code>",
            f"❌ Failed: <code>{failed}</code>",
        ], icon="♻️"),
        parse_mode=ParseMode.HTML,
    )


async def watchdog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_enabled
    if not owner_only(update):
        return
    if context.args and context.args[0].lower() in ("on", "off"):
        watchdog_enabled = context.args[0].lower() == "on"
        save_v7_data()
    await update.effective_message.reply_text(
        premium_box("ᴡᴀᴛᴄʜᴅᴏɢ", [
            f"Status: <code>{'ON' if watchdog_enabled else 'OFF'}</code>",
            f"Interval: <code>{watchdog_interval}s</code>",
            f"Restarts: <code>{watchdog_restarts}</code>",
        ], icon="🛡"),
        parse_mode=ParseMode.HTML,
    )


async def setwatchdog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_interval
    if not owner_only(update) or not context.args or not context.args[0].isdigit():
        return
    watchdog_interval = max(20, int(context.args[0]))
    save_v7_data()
    await update.effective_message.reply_text(f"✅ Watchdog → {watchdog_interval}s")


async def watchdogstatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await watchdog_cmd(update, context)


async def schedulerestart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or len(context.args) < 2:
        return
    found = find_project(update.effective_user.id, " ".join(context.args[:-1]))
    dur = parse_duration(context.args[-1])
    if not found or not dur:
        await update.effective_message.reply_text("Usage: /schedulerestart PROJECT 6h")
        return
    _, item = found
    sec = max(300, int(dur.total_seconds()))
    st = project_setting(item)
    st["restart_schedule_seconds"] = sec
    st["next_restart_at"] = time.time() + sec
    save_v7_data()
    await update.effective_message.reply_text(f"✅ Scheduled every {human_duration(sec)}.")


async def scheduleremove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    st = project_setting(item)
    st.pop("restart_schedule_seconds", None)
    st.pop("next_restart_at", None)
    save_v7_data()
    await update.effective_message.reply_text("✅ Schedule removed.")


async def autostart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or len(context.args) < 2:
        return
    if context.args[-1].lower() not in ("on", "off"):
        return
    found = find_project(update.effective_user.id, " ".join(context.args[:-1]))
    if not found:
        return
    _, item = found
    project_setting(item)["autostart"] = context.args[-1].lower() == "on"
    save_v7_data()
    await update.effective_message.reply_text(f"✅ Auto-start: {'ON' if project_setting(item)['autostart'] else 'OFF'}")


async def projectbackup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    folder = Path(item.folder)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = PROJECT_BACKUPS_DIR / f"{update.effective_user.id}_{clean_project_name(item.display_name)}_{stamp}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob("*"):
            if not f.is_file() or ".venv" in f.parts or f.name == "runtime.log":
                continue
            z.write(f, f.relative_to(folder))
    await update.effective_message.reply_document(InputFile(str(out)), caption=f"💾 {item.display_name}")
    
    
async def backups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    rows = sorted(BACKUPS_DIR.glob("elevatex_backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
    await update.effective_message.reply_text(
        premium_box("ʙᴀᴄᴋᴜᴘs", [f"• <code>{esc(x.name)}</code>" for x in rows] or ["None."], icon="💾"),
        parse_mode=ParseMode.HTML,
    )


async def restorebackup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2 or context.args[1] != "CONFIRM":
        return
    name = Path(context.args[0]).name
    src = BACKUPS_DIR / name
    if not src.exists() or not name.startswith("elevatex_backup_"):
        return
    allowed = {DATA_FILE.name, PROJECTS_FILE.name, V7_DATA_FILE.name, V9_DB_FILE.name}
    with zipfile.ZipFile(src) as z:
        for member in z.infolist():
            if Path(member.filename).name in allowed and "/" not in member.filename.strip("/"):
                z.extract(member, BASE_DIR)
    await update.effective_message.reply_text("✅ Restored. Restart bot to reload.")


async def logsize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    p = Path(item.log_path)
    size = (p.stat().st_size / (1024 * 1024)) if p.exists() else 0
    await update.effective_message.reply_text(f"🧾 {item.display_name} log: {size:.2f} MB")


async def clearlogs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    Path(item.log_path).write_text("", encoding="utf-8")
    await update.effective_message.reply_text("✅ Log cleared.")


async def diagnose_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    p = Path(item.log_path)
    text = p.read_text("utf-8", errors="replace")[-12000:] if p.exists() else ""
    await update.effective_message.reply_text(
        premium_box("ᴅɪᴀɢɴᴏsᴛɪᴄs", [
            f"Project: <b>{esc(item.display_name)}</b>"
        ] + [f"• {esc(x)}" for x in diagnose_log_text(text)], icon="🩺"),
        parse_mode=ParseMode.HTML,
    )


async def storage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    used = user_storage_mb(uid)
    limit = storage_limit_mb(uid)
    await update.effective_message.reply_text(
        premium_box("sᴛᴏʀᴀɢᴇ", [
            f"Used: <code>{used:.1f} MB</code>",
            f"Quota: <code>{limit} MB</code>",
            f"Available: <code>{max(0, limit - used):.1f} MB</code>",
        ], icon="💾"),
        parse_mode=ParseMode.HTML,
    )


async def setstorage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2 or not context.args[1].isdigit():
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        return
    user_storage_limits[str(uid)] = max(50, int(context.args[1]))
    save_v7_data()
    await update.effective_message.reply_text("✅ Storage updated.")


async def analytics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update):
        return
    total_projects = sum(len(x) for x in running_scripts.values())
    running = sum(i.running for x in running_scripts.values() for i in x)
    total_storage = sum(user_storage_mb(uid) for uid in running_scripts)
    await update.effective_message.reply_text(
        premium_box("ᴀɴᴀʟʏᴛɪᴄs", [
            f"Known users: <code>{len(user_stats)}</code>",
            f"Approved: <code>{len(approved_users)}</code>",
            f"Premium: <code>{len(premium_users)}</code>",
            f"Projects: <code>{total_projects}</code>",
            f"Running: <code>{running}</code>",
            f"Storage: <code>{total_storage:.1f} MB</code>",
            f"Codes: <code>{len(redeem_codes)}</code>",
            f"Events: <code>{len(audit_log)}</code>",
        ], icon="📈"),
        parse_mode=ParseMode.HTML,
    )


async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or len(context.args) != 2:
        return
    if not context.args[0].isdigit() or context.args[1].lower() not in ("support", "moderator", "superadmin"):
        return
    uid = int(context.args[0])
    admin_roles[str(uid)] = context.args[1].lower()
    approved_users.add(uid)
    banned_users.discard(uid)
    user_credits.setdefault(str(uid), DEFAULT_CREDITS)
    save_data()
    save_v7_data()
    await update.effective_message.reply_text(
        premium_box("ᴀᴅᴍɪɴ ɢʀᴀɴᴛᴇᴅ", [
            f"👤 <tg-spoiler><code>{uid}</code></tg-spoiler>",
            f"🎖 Role: <b>{esc(context.args[1])}</b>",
            "🔐 Force-join: <b>BYPASSED</b>",
            "✅ Approved: <b>YES</b>",
        ], icon="✅"),
        parse_mode=ParseMode.HTML,
    )


async def deladmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args or not context.args[0].isdigit():
        return
    admin_roles.pop(str(int(context.args[0])), None)
    save_v7_data()
    await update.effective_message.reply_text("✅ Admin removed.")


async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update):
        return
    rows = [f"• <code>{u}</code> — <b>{esc(r)}</b>" for u, r in admin_roles.items()]
    await update.effective_message.reply_text(
        premium_box("ᴀᴅᴍɪɴs", rows or ["None."], icon="👑"),
        parse_mode=ParseMode.HTML,
    )


async def codes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    rows = []
    for code, row in list(redeem_codes.items())[:50]:
        rows.append(f"• <code>{esc(code)}</code> — {row.get('kind')}:{row.get('value')} — {'OFF' if row.get('disabled') else 'ON'}")
    await update.effective_message.reply_text(
        premium_box("ᴄᴏᴅᴇs", rows or ["None."], icon="🎟"),
        parse_mode=ParseMode.HTML,
    )


async def disablecode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    code = context.args[0].upper()
    row = redeem_codes.get(code)
    if not row:
        return
    row["disabled"] = not bool(row.get("disabled"))
    save_v7_data()
    await update.effective_message.reply_text(f"✅ {code}: {'disabled' if row['disabled'] else 'enabled'}")


async def deletecode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    existed = redeem_codes.pop(context.args[0].upper(), None)
    save_v7_data()
    await update.effective_message.reply_text("✅ Deleted." if existed else "❌ Not found.")


async def codeinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update) or not context.args:
        return
    code = context.args[0].upper()
    row = redeem_codes.get(code)
    if not row:
        return
    await update.effective_message.reply_text(
        premium_box("ᴄᴏᴅᴇ ɪɴꜰᴏ", [
            f"Code: <code>{esc(code)}</code>",
            f"Kind: <code>{esc(str(row.get('kind')))}</code>",
            f"Value: <code>{esc(str(row.get('value')))}</code>",
            f"Used: <code>{len(row.get('used_by', []))}/{row.get('max_uses', '∞')}</code>",
            f"Status: <code>{'Disabled' if row.get('disabled') else 'Active'}</code>",
        ], icon="🎟"),
        parse_mode=ParseMode.HTML,
    )


async def forcejoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global FORCE_JOIN_ENABLED
    if not owner_only(update):
        return
    if context.args and context.args[0].lower() in ("on", "off"):
        FORCE_JOIN_ENABLED = context.args[0].lower() == "on"
        project_settings.setdefault("__global__", {})["force_join_enabled"] = FORCE_JOIN_ENABLED
        save_v7_data()
    await update.effective_message.reply_text(
        f"🔐 Force Join: {'ON' if FORCE_JOIN_ENABLED else 'OFF'}",
        parse_mode=ParseMode.HTML,
    )


async def setbrand_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BRAND_NAME
    if not owner_only(update) or not context.args:
        return
    BRAND_NAME = " ".join(context.args)[:50]
    project_settings.setdefault("__global__", {})["brand_name"] = BRAND_NAME
    save_v7_data()
    await update.effective_message.reply_text("✅ Brand updated.")


async def setfooter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global brand_footer
    if not owner_only(update) or not context.args:
        return
    brand_footer = " ".join(context.args)[:120]
    save_v7_data()
    await update.effective_message.reply_text("✅ Footer updated.")


async def panelreminder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_reminder_enabled
    if not owner_only(update):
        return
    if context.args and context.args[0].lower() in ("on", "off"):
        panel_reminder_enabled = context.args[0].lower() == "on"
        save_v7_data()
    next_due = panel_last_confirmed_at + PANEL_REMINDER_HOURS * 3600
    await update.effective_message.reply_text(
        premium_box("ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ", [
            f"Status: <code>{'ON' if panel_reminder_enabled else 'OFF'}</code>",
            f"Cycle: <code>{PANEL_REMINDER_HOURS}h</code>",
            f"Last: <code>{datetime.fromtimestamp(panel_last_confirmed_at).strftime('%Y-%m-%d %H:%M')}</code>",
            f"Next: <code>{datetime.fromtimestamp(next_due).strftime('%Y-%m-%d %H:%M')}</code>",
        ], icon="⏰"),
        parse_mode=ParseMode.HTML,
    )


async def panelvisited_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_last_confirmed_at, panel_last_reminder_at
    if not owner_only(update):
        return
    panel_last_confirmed_at = time.time()
    panel_last_reminder_at = 0.0
    save_v7_data()
    await update.effective_message.reply_text("✅ Marked.")


async def piplist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    py = Path(item.folder) / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        await update.effective_message.reply_text("❌ No venv.")
        return
    r = await asyncio.to_thread(subprocess.run, [str(py), "-m", "pip", "list", "--format=freeze"], capture_output=True, text=True, timeout=60)
    text = (r.stdout or r.stderr)[-3500:]
    await update.effective_message.reply_text(f"<pre>{esc(text)}</pre>", parse_mode=ParseMode.HTML)


async def requirements_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    req = Path(item.folder) / "requirements.txt"
    if not req.exists():
        await update.effective_message.reply_text("No requirements.txt.")
        return
    await update.effective_message.reply_text(f"<pre>{esc(req.read_text('utf-8', errors='replace')[:3500])}</pre>", parse_mode=ParseMode.HTML)


async def checkcompat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    req = Path(item.folder) / "requirements.txt"
    notes = [f"Host Python: <code>{sys.version.split()[0]}</code>"]
    if req.exists():
        txt = req.read_text("utf-8", errors="replace")
        notes.append("requirements.txt: <code>Detected</code>")
        if sys.version_info >= (3, 13) and re.search(r"python-telegram-bot\s*==\s*20\.", txt, re.I):
            notes.append("⚠️ PTB 20.x not recommended on Python 3.13")
    else:
        notes.append("requirements.txt: <code>Not found</code>")
    await update.effective_message.reply_text(
        premium_box("ᴄᴏᴍᴘᴀᴛɪʙɪʟɪᴛʏ", notes, icon="🧪"),
        parse_mode=ParseMode.HTML,
    )


async def repairenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context) or not context.args:
        return
    found = find_project(update.effective_user.id, " ".join(context.args))
    if not found:
        return
    _, item = found
    folder = Path(item.folder)
    req = next(iter(folder.rglob("requirements.txt")), None)
    if not req:
        await update.effective_message.reply_text("❌ No requirements.txt.")
        return
    msg = await update.effective_message.reply_text("🔧 Rebuilding venv…")
    venv = folder / ".venv"
    try:
        if venv.exists():
            shutil.rmtree(venv, ignore_errors=True)
        note = await asyncio.to_thread(install_project_dependencies, folder, Path(item.entry_file), Path(item.log_path))
        await msg.edit_text(f"✅ Repaired. {note}")
    except Exception as exc:
        await msg.edit_text(f"❌ {exc}")


async def hoststats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    await update.effective_message.reply_text(host_stats_text(), parse_mode=ParseMode.HTML)


async def security_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update):
        return
    await update.effective_message.reply_text(security_text(), parse_mode=ParseMode.HTML)


async def keepalive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_enabled
    if not owner_only(update):
        return
    if context.args and context.args[0].lower() in ("on", "off"):
        keepalive_enabled = context.args[0].lower() == "on"
        save_v7_data()
    await update.effective_message.reply_text(keepalive_text(), parse_mode=ParseMode.HTML)


async def setkeepalive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_url, keepalive_interval, keepalive_enabled
    if not owner_only(update) or not context.args:
        return
    if context.args[0].lower() == "off":
        keepalive_enabled = False
        save_v7_data()
        await update.effective_message.reply_text("💤 Disabled.")
        return
    url = context.args[0].strip()
    if not url.startswith(("http://", "https://")):
        await update.effective_message.reply_text("❌ URL must be http(s).")
        return
    interval = keepalive_interval
    if len(context.args) > 1:
        try:
            interval = max(30, min(45, int(context.args[1])))
        except ValueError:
            return
    keepalive_url = url
    keepalive_interval = interval
    keepalive_enabled = True
    save_v7_data()
    await update.effective_message.reply_text(keepalive_text(), parse_mode=ParseMode.HTML)


# ═════════════════════════════════════════════════════════════════════════════
# 🌐  HEALTH SERVER & KEEPALIVE
# ═════════════════════════════════════════════════════════════════════════════


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] not in {"/", "/health"}:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({
            "service": BRAND_NAME, "status": "online", "runtime": "python-only",
            "uptime": uptime(),
            "projects": sum(len(v) for v in running_scripts.values()),
            "active": sum(i.running for v in running_scripts.values() for i in v),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def start_health_server() -> None:
    global health_server_started
    try:
        server = ThreadingHTTPServer(("0.0.0.0", HEALTH_PORT), _HealthHandler)
        health_server_started = True
        threading.Thread(target=server.serve_forever, daemon=True, name="elevatex-health").start()
        logger.info("Health server on 0.0.0.0:%s", HEALTH_PORT)
    except OSError as exc:
        health_server_started = False
        logger.warning("Health server failed on %s: %s", HEALTH_PORT, exc)


def _ping_keepalive(url: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ElevateX/9.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def keepalive_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_last_status, keepalive_last_at, keepalive_failures, keepalive_last_epoch
    if not keepalive_enabled or not keepalive_url:
        return
    now = time.time()
    if keepalive_last_epoch and now - keepalive_last_epoch < keepalive_interval:
        return
    keepalive_last_epoch = now
    ok, detail = await asyncio.to_thread(_ping_keepalive, keepalive_url)
    keepalive_last_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keepalive_last_status = detail
    if ok:
        keepalive_failures = 0
    else:
        keepalive_failures += 1
        logger.warning("Keep-alive failed (%s): %s", keepalive_failures, detail)


# ═════════════════════════════════════════════════════════════════════════════
# ⏰  JOBS
# ═════════════════════════════════════════════════════════════════════════════


async def auto_restart_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    for uid, items in list(running_scripts.items()):
        async with lock_for(uid):
            for item in items:
                if not item.running and item.auto_restart and item.restarts < MAX_RESTARTS:
                    try:
                        item.restarts += 1
                        spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                        await context.bot.send_message(uid, f"♻️ Auto-restarted {item.display_name}.")
                    except Exception:
                        logger.exception("Auto restart failed")


async def watchdog_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_last_epoch, watchdog_restarts
    if not watchdog_enabled or time.time() - watchdog_last_epoch < watchdog_interval:
        return
    watchdog_last_epoch = time.time()
    now = time.time()
    for uid, items in list(running_scripts.items()):
        async with lock_for(uid):
            for item in items:
                st = project_setting(item)
                sec = int(st.get("restart_schedule_seconds", 0) or 0)
                nxt = float(st.get("next_restart_at", 0) or 0)
                if sec and nxt and now >= nxt:
                    try:
                        if item.running:
                            kill_process(item)
                        spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                        st["next_restart_at"] = now + sec
                        watchdog_restarts += 1
                    except Exception:
                        logger.exception("Scheduled restart failed")
                if item.running:
                    continue
                if not (item.auto_restart or st.get("autostart") or item.desired_running):
                    continue
                crashes = [float(x) for x in st.get("crash_times", []) if now - float(x) <= CRASH_WINDOW_SECONDS]
                crashes.append(now)
                st["crash_times"] = crashes[-20:]
                if len(crashes) > CRASH_LIMIT:
                    if not st.get("crash_alerted"):
                        st["crash_alerted"] = True
                        try:
                            await context.bot.send_message(
                                uid, f"🛑 {item.display_name} crash-loop stopped ({len(crashes)} crashes)."
                            )
                        except TelegramError:
                            pass
                    continue
                try:
                    spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                    watchdog_restarts += 1
                except Exception:
                    logger.exception("Watchdog restart failed")
    save_v7_data()
    save_projects()


async def startup_recovery_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    recovered = 0
    for uid, items in running_scripts.items():
        async with lock_for(uid):
            for item in items:
                if item.running:
                    continue
                if not (item.desired_running or project_setting(item).get("autostart")):
                    continue
                try:
                    spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path))
                    recovered += 1
                except Exception:
                    logger.exception("Startup recovery failed")
    if recovered:
        try:
            await context.bot.send_message(OWNER_ID, f"♻️ Recovered {recovered} project(s).")
        except TelegramError:
            pass


async def log_rotation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    maxb = LOG_ROTATE_MAX_MB * 1024 * 1024
    keep = LOG_ROTATE_KEEP_MB * 1024 * 1024
    for items in running_scripts.values():
        for item in items:
            p = Path(item.log_path)
            try:
                if p.exists() and p.stat().st_size > maxb:
                    with p.open("rb") as f:
                        f.seek(-min(keep, p.stat().st_size), 2)
                        tail = f.read()
                    p.write_bytes(b"===== Rotated =====\n" + tail)
            except OSError:
                pass


async def panel_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_last_reminder_at
    if not panel_reminder_enabled:
        return
    now = time.time()
    due = panel_last_confirmed_at + PANEL_REMINDER_HOURS * 3600
    if now < due or (panel_last_reminder_at and now - panel_last_reminder_at < 12 * 3600):
        return
    panel_last_reminder_at = now
    save_v7_data()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🟢 ✅ ɪ ᴠɪsɪᴛᴇᴅ", callback_data="admin:panelvisited")]])
    try:
        await context.bot.send_message(
            OWNER_ID,
            premium_box("ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ", [
                "Your 3-day panel visit reminder is due.",
                "Open your panel manually, then tap below.",
            ], icon="⏰"),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except TelegramError:
        logger.exception("Panel reminder failed")


async def scheduled_backup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    save_data()
    save_projects()
    save_v7_data()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = BACKUPS_DIR / f"elevatex_backup_{stamp}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for f in (DATA_FILE, PROJECTS_FILE, V7_DATA_FILE, V9_DB_FILE):
            if f.exists():
                z.write(f, f.name)
    old = sorted(BACKUPS_DIR.glob("elevatex_backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)[7:]
    for f in old:
        f.unlink(missing_ok=True)
    try:
        await context.bot.send_document(OWNER_ID, document=InputFile(str(archive)), caption="📦 Auto backup")
    except TelegramError:
        logger.exception("Backup delivery failed")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled update error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An internal error occurred.")
        except TelegramError:
            pass


# ═════════════════════════════════════════════════════════════════════════════
# 🎬  MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main() -> None:
    if not TOKEN or TOKEN == "PASTE_NEW_BOT_TOKEN_HERE":
        raise SystemExit("BOT token missing.")
    if OWNER_ID <= 0:
        raise SystemExit("Invalid OWNER_ID.")

    load_data()
    load_v7_data()
    load_join_cache()
    init_v9_database()
    sync_v9_database()

    global FORCE_JOIN_ENABLED, BRAND_NAME
    g = project_settings.get("__global__", {})
    FORCE_JOIN_ENABLED = bool(g.get("force_join_enabled", FORCE_JOIN_ENABLED))
    BRAND_NAME = str(g.get("brand_name", BRAND_NAME))
    expire_plans()
    start_health_server()

    app: Application = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .concurrent_updates(32)
        .build()
    )

    # Basic
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("request", request_cmd))
    app.add_handler(CommandHandler("projects", projects_cmd))
    app.add_handler(CommandHandler("status", projects_cmd))
    app.add_handler(CommandHandler("logs", logs_cmd))
    app.add_handler(CommandHandler("credits", credits_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    app.add_handler(CommandHandler("rename", rename_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("delete", delete_cmd))

    # Owner
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("revoke", revoke_cmd))
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("unpremium", unpremium_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("userinfo", userinfo_cmd))
    app.add_handler(CommandHandler("addcredits", addcredits_cmd))
    app.add_handler(CommandHandler("setcredits", setcredits_cmd))
    app.add_handler(CommandHandler("takecredits", takecredits_cmd))
    app.add_handler(CommandHandler("setdaily", setdaily_cmd))
    app.add_handler(CommandHandler("setrunning", setrunning_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("maintenance", maintenance_cmd))
    app.add_handler(CommandHandler("startall", startall_cmd))
    app.add_handler(CommandHandler("stopalladmin", stopalladmin_cmd))
    app.add_handler(CommandHandler("cleanup", cleanup_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("install", install_cmd))
    app.add_handler(CommandHandler("installed", installed_cmd))

    # Force-join management
    app.add_handler(CommandHandler("verifycache", verifycache_cmd))
    app.add_handler(CommandHandler("bypassjoin", bypassjoin_cmd))
    app.add_handler(CommandHandler("unbypassjoin", unbypassjoin_cmd))
    app.add_handler(CommandHandler("clearverify", clearverify_cmd))
    app.add_handler(CommandHandler("clearallverify", clearallverify_cmd))
    app.add_handler(CommandHandler("forcejoin", forcejoin_cmd))

    # V7/V9 extras
    app.add_handler(CommandHandler("setplan", setplan_cmd))
    app.add_handler(CommandHandler("plans", plans_cmd))
    app.add_handler(CommandHandler("createcode", createcode_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("setenv", setenv_cmd))
    app.add_handler(CommandHandler("env", env_cmd))
    app.add_handler(CommandHandler("delenv", delenv_cmd))
    app.add_handler(CommandHandler("autorestart", autorestart_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("auditlog", auditlog_cmd))
    app.add_handler(CommandHandler("finduser", finduser_cmd))
    app.add_handler(CommandHandler("allprojects", allprojects_cmd))
    app.add_handler(CommandHandler("restartall", restartall_cmd))
    app.add_handler(CommandHandler("watchdog", watchdog_cmd))
    app.add_handler(CommandHandler("setwatchdog", setwatchdog_cmd))
    app.add_handler(CommandHandler("watchdogstatus", watchdogstatus_cmd))
    app.add_handler(CommandHandler("schedulerestart", schedulerestart_cmd))
    app.add_handler(CommandHandler("scheduleremove", scheduleremove_cmd))
    app.add_handler(CommandHandler("autostart", autostart_cmd))
    app.add_handler(CommandHandler("projectbackup", projectbackup_cmd))
    app.add_handler(CommandHandler("backups", backups_cmd))
    app.add_handler(CommandHandler("restorebackup", restorebackup_cmd))
    app.add_handler(CommandHandler("logsize", logsize_cmd))
    app.add_handler(CommandHandler("clearlogs", clearlogs_cmd))
    app.add_handler(CommandHandler("diagnose", diagnose_cmd))
    app.add_handler(CommandHandler("storage", storage_cmd))
    app.add_handler(CommandHandler("setstorage", setstorage_cmd))
    app.add_handler(CommandHandler("analytics", analytics_cmd))
    app.add_handler(CommandHandler("addadmin", addadmin_cmd))
    app.add_handler(CommandHandler("deladmin", deladmin_cmd))
    app.add_handler(CommandHandler("admins", admins_cmd))
    app.add_handler(CommandHandler("codes", codes_cmd))
    app.add_handler(CommandHandler("disablecode", disablecode_cmd))
    app.add_handler(CommandHandler("deletecode", deletecode_cmd))
    app.add_handler(CommandHandler("codeinfo", codeinfo_cmd))
    app.add_handler(CommandHandler("setbrand", setbrand_cmd))
    app.add_handler(CommandHandler("setfooter", setfooter_cmd))
    app.add_handler(CommandHandler("panelreminder", panelreminder_cmd))
    app.add_handler(CommandHandler("panelvisited", panelvisited_cmd))
    app.add_handler(CommandHandler("piplist", piplist_cmd))
    app.add_handler(CommandHandler("requirements", requirements_cmd))
    app.add_handler(CommandHandler("checkcompat", checkcompat_cmd))
    app.add_handler(CommandHandler("repairenv", repairenv_cmd))
    app.add_handler(CommandHandler("hoststats", hoststats_cmd))
    app.add_handler(CommandHandler("security", security_cmd))
    app.add_handler(CommandHandler("keepalive", keepalive_cmd))
    app.add_handler(CommandHandler("setkeepalive", setkeepalive_cmd))

    # ChatMemberHandler for join/leave events
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.add_error_handler(error_handler)

    if app.job_queue:
        app.job_queue.run_once(startup_recovery_job, when=8)
        app.job_queue.run_repeating(watchdog_job, interval=10, first=20)
        app.job_queue.run_repeating(log_rotation_job, interval=300, first=180)
        app.job_queue.run_repeating(panel_reminder_job, interval=3600, first=60)
        app.job_queue.run_repeating(keepalive_job, interval=5, first=10, name="elevatex_keepalive")
        app.job_queue.run_repeating(
            scheduled_backup_job,
            interval=max(3600, BACKUP_INTERVAL_HOURS * 3600),
            first=120,
        )

    logger.info("%s V9 started | Owner: %s", BRAND_NAME, OWNER_ID)

    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()