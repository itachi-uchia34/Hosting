# ElevateX Host V9 — Python Stability Pro

Python-only Telegram hosting manager with premium admin controls, recovery tooling, backups and diagnostics.

## V9 highlights

- Python `.py` and Python `.zip` hosting only.
- SQLite snapshot/migration database (`elevatex_v9.db`) alongside backward-compatible JSON state.
- Internal watchdog with configurable interval and crash-loop protection.
- Scheduled project restarts and startup recovery.
- Per-user storage quotas with upload enforcement.
- Project backup, admin backup listing and confirmation-gated restore.
- Automatic log rotation, log size and log clear tools.
- Common-error diagnostics for project logs.
- Project dependency/compatibility tools: `/requirements`, `/piplist`, `/checkcompat`, `/repairenv`.
- Delegated read-only admin roles while destructive actions stay owner-only.
- Redeem-code manager: list, info, disable/enable and delete.
- Analytics dashboard.
- Runtime force-join toggle and brand/footer controls.
- Admin panel visit reminder every 72 hours by default. Use `/panelvisited` after manually visiting the hosting panel.
- External URL keep-alive remains available for optional health checks but is OFF by default.

## New V9 commands

### Stability / projects
`/watchdog [on|off]`
`/setwatchdog SECONDS`
`/watchdogstatus`
`/schedulerestart PROJECT 6h|30m|1d`
`/scheduleremove PROJECT`
`/autostart PROJECT on|off`
`/diagnose PROJECT`
`/logsize PROJECT`
`/clearlogs PROJECT`
`/requirements PROJECT`
`/piplist PROJECT`
`/checkcompat PROJECT`
`/repairenv PROJECT`

### Storage / backup
`/storage`
`/setstorage USER_ID MB`
`/projectbackup PROJECT`
`/backups`
`/restorebackup FILENAME.zip CONFIRM`

### Admin / analytics
`/analytics`
`/addadmin USER_ID support|moderator|superadmin`
`/deladmin USER_ID`
`/admins`
`/codes`
`/codeinfo CODE`
`/disablecode CODE`
`/deletecode CODE`
`/forcejoin on|off`
`/setbrand NAME`
`/setfooter TEXT`

### Panel reminder
`/panelreminder [on|off]`
`/panelvisited`

The reminder defaults to 72 hours. It only reminds the owner to manually visit the hosting panel; it does not automate third-party login.

## Deployment

Set at least:

```bash
BOT_TOKEN=your_new_bot_token
OWNER_ID=your_telegram_user_id
```

Install:

```bash
pip install -r requirements.txt
python main.py
```

For arbitrary user-uploaded code, run ElevateX Host inside an isolated container/VM. Static scanning and process monitoring are not a complete sandbox.
