# LOUD WIN ZONE — Telegram Auto Delete Bot

A Telegram group bot that schedules deletion of ordinary group messages after 30 seconds by default. Admin-only commands control the feature and delay.

## Features

- Auto-delete ordinary group messages after a configurable delay (default 30 seconds).
- `/autodelete on` and `/autodelete off` (group admins only).
- `/settime 30` (group admins only; allowed range 5–86400 seconds).
- `/status` and `/help`.
- Handles text, media, stickers, and other ordinary messages.
- Does not schedule slash-command messages or Telegram service messages.

## Important limitations

- **Render Free:** Render's free instances are not a reliable always-on home for a bot worker. Background Workers generally require a paid instance; check Render's current pricing before deploying. If the worker stops, messages arriving while it is offline will not be scheduled for deletion.
- **In-memory timers/settings:** pending deletion jobs and per-chat setting changes are lost on restart/redeploy. The defaults come from Render environment variables. For production-grade behavior, add persistent storage and a durable job queue.
- Telegram may reject deletion if the bot lacks permission, if the message is too old, or due to Telegram API limits. This bot logs failures.
- Group admin commands are checked against Telegram's live chat membership.
- The bot cannot delete messages sent before it was added or before it received updates.
- Avoid using this in groups where messages must be retained; ordinary messages can disappear quickly.

## 1. Create the Telegram bot

1. Open `@BotFather` in Telegram and run `/newbot`.
2. Follow the prompts and copy the token.
3. Keep the token secret. Do not put it in source code or commit it to GitHub.
4. Add the bot to your Telegram group.
5. Promote it to administrator and enable **Delete messages**.
6. If you want to make sure the bot receives all group messages, use `@BotFather` → `/setprivacy` → select your bot → **Disable**. Admin bots generally receive group messages, but this setting can help if it is not an admin.

## 2. Upload to GitHub

1. Create a new repository, e.g. `loud-win-zone-auto-delete-bot`.
2. Upload `bot.py`, `requirements.txt`, `render.yaml`, `.gitignore`, and `README.md`.
3. Do not upload your real `.env` file or token.

## 3. Deploy on Render

1. Sign in to Render and choose **New → Blueprint** (if using `render.yaml`) or create a **Background Worker** manually.
2. Connect the GitHub repository.
3. Confirm the build command: `pip install -r requirements.txt`.
4. Confirm the start command: `python bot.py`.
5. Add environment variables:
   - `BOT_TOKEN` = token from BotFather
   - `DELETE_AFTER_SECONDS` = `30`
   - `AUTO_DELETE_ENABLED` = `true`
6. Deploy and inspect the logs. A successful start should show `Starting LOUD WIN ZONE Auto Delete Bot`.

## 4. Use in the group

- `/help` — command list
- `/status` — current settings
- `/autodelete off` — pause deletion (admin only)
- `/autodelete on` — resume deletion (admin only)
- `/settime 30` — delete ordinary messages after 30 seconds (admin only)

The `/autodelete` and `/settime` command messages themselves are not scheduled for deletion.

## Troubleshooting

- **Bot does not respond:** check Render logs and confirm `BOT_TOKEN` is correct.
- **Messages are not deleted:** make sure the bot is an admin with Delete Messages permission.
- **Bot sees only commands:** check BotFather privacy settings and bot admin status.
- **Token leaked:** immediately revoke/regenerate it with BotFather and update Render's `BOT_TOKEN`.
