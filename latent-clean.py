import concurrent.futures
import json
import os
import random
import re
import sys
import threading
import time
from datetime import datetime

import requests

TOKEN = "put your self token here"
USER_ID = "your user id"

WHITELIST_CHANNELS = []
WHITELIST_USERS = []

DRY_RUN = False
OLDER_THAN_DAYS = 0
WORKERS = 3

API = "https://discord.com/api/v10"
DELETABLE_TYPES = {0, 19, 20, 23}
DISCORD_EPOCH = 1420070400000
MAX_RETRIES = 8
TIMEOUT = 8
LOG_FILE = "latent_clean_log.txt"
FAILED_FILE = "latent_clean_failed.txt"
CHECKPOINT_FILE = "latent_clean_checkpoint.json"
CHECKPOINT_EVERY = 500

CODES = {"reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "red": "\033[91m",
         "green": "\033[92m", "yellow": "\033[93m", "cyan": "\033[96m"}
ANSI_RE = re.compile(r"\033\[[0-9;]*m")
LINE = "─" * 44

stats = {"channels": 0, "found": 0, "deleted": 0, "failed": 0, "skipped": 0, "rate_limits": 0}
START = time.time()
lock = threading.Lock()
stop = threading.Event()
failed = []
done_channels = set()
rl_until = 0.0
session = requests.Session()
settings = {"dry": DRY_RUN, "days": OLDER_THAN_DAYS, "workers": WORKERS}
account = {"name": "", "id": ""}


def paint(text, *styles):
    return "".join(CODES[s] for s in styles) + str(text) + CODES["reset"]


def log(message, level="info"):
    marks = {"info": paint("•", "cyan"), "ok": paint("✔", "green"),
             "error": paint("✘", "red"), "warn": paint("!", "yellow"),
             "skip": paint("–", "dim")}
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"  {paint(stamp, 'dim')}  {marks[level]}  {message}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] [{level}] {ANSI_RE.sub('', message)}\n")
    except OSError:
        pass


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def title():
    clear()
    print()
    print("  " + paint("LATENT-CLEAN", "bold", "cyan") + paint("  ·  Discord message cleaner", "dim"))
    print("  " + paint(LINE, "dim"))


def header():
    title()
    mode = paint("DRY RUN", "yellow") if settings["dry"] else paint("LIVE", "red")
    age = f"older than {settings['days']} days" if settings["days"] else "none"
    print(f"  {paint('Account', 'dim')}  {account['name']} ({account['id']})")
    print(f"  {paint('Mode   ', 'dim')}  {mode}")
    print(f"  {paint('Filter ', 'dim')}  {age}")
    print(f"  {paint('Threads', 'dim')}  {settings['workers']}")
    print("  " + paint(LINE, "dim"))


def ask(prompt="> "):
    try:
        return input("  " + paint(prompt, "cyan", "bold")).strip()
    except EOFError:
        return ""


def api(method, path, **kwargs):
    global rl_until
    for attempt in range(MAX_RETRIES):
        if stop.is_set():
            return None
        wait = rl_until - time.time()
        if wait > 0:
            time.sleep(wait)
        try:
            response = session.request(method, API + path, timeout=TIMEOUT, **kwargs)
        except requests.RequestException:
            time.sleep(min(2 * (attempt + 1), 10))
            continue
        if response.status_code == 429:
            try:
                data = response.json()
                retry = float(data.get("retry_after", 2))
                is_global = data.get("global", False)
            except ValueError:
                retry, is_global = 2.0, False
            with lock:
                stats["rate_limits"] += 1
                if is_global:
                    rl_until = max(rl_until, time.time() + retry)
            time.sleep(retry + 0.3)
            continue
        if response.status_code == 401:
            log("Token invalid or expired (401)", "error")
            stop.set()
            return None
        return response
    return None


def snowflake_time(snowflake):
    try:
        return ((int(snowflake) >> 22) + DISCORD_EPOCH) / 1000
    except (TypeError, ValueError):
        return 0


def save_state():
    with lock:
        data = {
            "stats": dict(stats),
            "failed": list(failed),
            "done_channels": sorted(done_channels),
            "timestamp": datetime.now().isoformat()
        }
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(FAILED_FILE, "w", encoding="utf-8") as f:
            for item in data["failed"]:
                f.write(f"{item['channel_id']},{item['message_id']}\n")
    except OSError:
        pass


def fetch_own_messages(channel_id):
    mine, before, scanned = [], None, 0
    cutoff = time.time() - settings["days"] * 86400 if settings["days"] else None
    while not stop.is_set():
        params = {"limit": 100}
        if before:
            params["before"] = before
        response = api("GET", f"/channels/{channel_id}/messages", params=params)
        if response is None:
            log(f"Channel {channel_id}: api returned None", "error")
            break
        if response.status_code != 200:
            if response.status_code in (403, 404):
                log(f"No access to channel ({response.status_code})", "error")
            else:
                log(f"Channel {channel_id}: HTTP {response.status_code}", "error")
            break
        batch = response.json()
        if not batch:
            break
        scanned += len(batch)
        for message in batch:
            if message.get("author", {}).get("id") != USER_ID:
                continue
            if message.get("type") not in DELETABLE_TYPES:
                continue
            if cutoff and snowflake_time(message["id"]) > cutoff:
                continue
            mine.append(message["id"])
        sys.stdout.write(f"\r  {paint('scanning', 'dim')}  {scanned} messages, {len(mine)} yours   ")
        sys.stdout.flush()
        before = batch[-1]["id"]
        if len(batch) < 100:
            break
        time.sleep(random.uniform(0.1, 0.3))
    sys.stdout.write("\r" + " " * 60 + "\r")
    return mine


def delete_message(channel_id, message_id):
    response = api("DELETE", f"/channels/{channel_id}/messages/{message_id}")
    if response is None:
        return "retries"
    if response.status_code in (200, 204):
        return "deleted"
    if response.status_code == 404:
        return "gone"
    if response.status_code == 403:
        return "forbidden"
    return f"http_{response.status_code}"


def channel_name(channel):
    if not channel:
        return "unknown channel"
    kind = channel.get("type", 0)
    if kind in (1, 3):
        names = [r.get("username", "?") for r in channel.get("recipients", [])]
        return ("DM: " if kind == 1 else "Group DM: ") + ", ".join(names[:4])
    return "#" + str(channel.get("name", "unnamed"))


def progress(done, total, ok, bad, started, skipped=0):
    if total <= 0:
        return
    width = 24
    filled = int(width * done / total)
    rate = done / max(0.1, time.time() - started)
    bar = paint("█" * filled, "green") + paint("░" * (width - filled), "dim")
    skip_txt = f"  {paint(skipped, 'yellow')} skip" if skipped else ""
    sys.stdout.write(f"\r  {bar}  {int(100 * done / total):3d}%  {done}/{total}  "
                     f"{paint(ok, 'green')} ok  {paint(bad, 'red')} failed{skip_txt}  {rate:.1f}/s  ")
    sys.stdout.flush()


def clean_channel(channel_id):
    channel_id = str(channel_id)
    if stop.is_set():
        return

    if channel_id in {str(x) for x in WHITELIST_CHANNELS}:
        log(f"{channel_id} is whitelisted", "skip")
        with lock:
            stats["skipped"] += 1
        return

    with lock:
        if channel_id in done_channels:
            log(f"{channel_id} already done", "skip")
            return

    response = api("GET", f"/channels/{channel_id}")
    info = response.json() if response is not None and response.status_code == 200 else None
    blocked = {str(x) for x in WHITELIST_USERS}
    if info and info.get("type") in (1, 3) and any(str(u.get("id")) in blocked for u in info.get("recipients", [])):
        log(f"{channel_name(info)} is whitelisted", "skip")
        with lock:
            stats["skipped"] += 1
        return

    log(paint(channel_name(info), "bold"))
    ids = fetch_own_messages(channel_id)
    with lock:
        stats["found"] += len(ids)

    if not ids:
        with lock:
            stats["channels"] += 1
            done_channels.add(channel_id)
        log("nothing to delete", "skip")
        save_state()
        return

    if settings["dry"]:
        log(f"{paint(len(ids), 'yellow')} messages would be deleted (dry run)", "ok")
        with lock:
            done_channels.add(channel_id)
        return

    ok = bad = skip = count = 0
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings["workers"]) as pool:
        futures = {pool.submit(delete_message, channel_id, mid): mid for mid in ids}
        for future in concurrent.futures.as_completed(futures):
            mid = futures[future]
            count += 1
            try:
                status = future.result()
            except Exception:
                status = "error"
            if status in ("deleted", "gone"):
                ok += 1
                with lock:
                    stats["deleted"] += 1
            elif status == "forbidden":
                skip += 1
                with lock:
                    stats["skipped"] += 1
            else:
                bad += 1
                with lock:
                    stats["failed"] += 1
                    failed.append({"channel_id": channel_id, "message_id": mid})
            progress(count, len(ids), ok, bad, started, skip)
            if count % CHECKPOINT_EVERY == 0:
                save_state()
            if stop.is_set():
                try:
                    pool.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    pool.shutdown(wait=False)
                break
    print()

    with lock:
        stats["channels"] += 1
        done_channels.add(channel_id)
    log(f"{ok} deleted, {bad} failed, {skip} skipped", "ok")
    save_state()


def retry_failed():
    with lock:
        items = list(failed)
        failed.clear()
        stats["failed"] = 0
    if not items:
        log("no failed messages", "warn")
        save_state()
        return
    log(f"retrying {len(items)} messages")
    ok = bad = skip = count = 0
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings["workers"]) as pool:
        futures = {pool.submit(delete_message, item["channel_id"], item["message_id"]): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            count += 1
            try:
                status = future.result()
            except Exception:
                status = "error"
            if status in ("deleted", "gone"):
                ok += 1
                with lock:
                    stats["deleted"] += 1
            elif status == "forbidden":
                skip += 1
                with lock:
                    stats["skipped"] += 1
            else:
                bad += 1
                with lock:
                    stats["failed"] += 1
                    failed.append(item)
            progress(count, len(items), ok, bad, started, skip)
            if count % CHECKPOINT_EVERY == 0:
                save_state()
            if stop.is_set():
                try:
                    pool.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    pool.shutdown(wait=False)
                break
    print()
    log(f"{ok}/{len(items)} deleted, {bad} failed, {skip} skipped", "ok")
    save_state()


def guild_text_channels(guild_id):
    response = api("GET", f"/guilds/{guild_id}/channels")
    if response is None or response.status_code != 200:
        return []
    return [c for c in response.json() if c.get("type") in (0, 5)]


def show_stats():
    elapsed = max(1, int(time.time() - START))
    speed = stats["deleted"] / elapsed
    rows = [("Time", f"{elapsed}s"), ("Channels", stats["channels"]),
            ("Whitelisted", stats["skipped"]), ("Found", stats["found"]),
            ("Deleted", paint(stats["deleted"], "green")),
            ("Failed", paint(stats["failed"], "red")),
            ("Rate limits", stats["rate_limits"]), ("Speed", f"{speed:.1f} msg/s")]
    print()
    for label, value in rows:
        print(f"  {paint(label.ljust(12), 'dim')}{value}")


def confirm(what):
    if settings["dry"]:
        return True
    print()
    answer = ask(f"This will permanently delete messages in {what}. Type YES to continue: ")
    return answer == "YES"


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return
    try:
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        answer = ask(f"Resume from checkpoint ({data['timestamp'][:16]})? [y/n] ")
        if answer.lower() == "y":
            done_channels.update(data.get("done_channels", []))
            failed.extend(data.get("failed", []))
            for key in ("deleted", "found", "channels", "skipped", "rate_limits"):
                stats[key] = data["stats"].get(key, 0)
            stats["failed"] = len(failed)
    except (OSError, ValueError, KeyError):
        pass


def settings_menu():
    while True:
        header()
        print(f"  {paint('1', 'cyan')}  Dry run      {'on' if settings['dry'] else 'off'}")
        print(f"  {paint('2', 'cyan')}  Age filter   {settings['days']} days (0 = off)")
        print(f"  {paint('3', 'cyan')}  Threads      {settings['workers']}")
        print(f"  {paint('0', 'cyan')}  Back")
        print()
        choice = ask()
        if choice == "1":
            settings["dry"] = not settings["dry"]
        elif choice == "2":
            value = ask("Delete only messages older than how many days? ")
            settings["days"] = int(value) if value.isdigit() else 0
        elif choice == "3":
            value = ask("Threads (1-10): ")
            if value.isdigit():
                settings["workers"] = max(1, min(10, int(value)))
        elif choice == "0":
            return


def menu():
    print(f"  {paint('1', 'cyan')}  Clean channels by ID")
    print(f"  {paint('2', 'cyan')}  Clean all DMs")
    print(f"  {paint('3', 'cyan')}  Clean all servers")
    print(f"  {paint('4', 'cyan')}  Clean one server")
    print(f"  {paint('5', 'cyan')}  Retry failed")
    print(f"  {paint('6', 'cyan')}  Statistics")
    print(f"  {paint('7', 'cyan')}  Settings")
    print(f"  {paint('0', 'cyan')}  Exit")
    print()
    return ask()


def fail_screen(message):
    title()
    print(f"\n  {paint('✘', 'red')}  {message}\n")


def main():
    global USER_ID
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if not TOKEN or TOKEN == "YOUR_TOKEN_HERE":
        fail_screen("Set your token in the TOKEN variable at the top of this file.")
        return

    session.headers.update({
        "Authorization": TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })

    response = api("GET", "/users/@me")
    if response is None or response.status_code != 200:
        fail_screen("Login failed. Your token may be invalid.")
        return
    me = response.json()
    USER_ID = str(me["id"])
    account["name"] = me.get("username", "?")
    account["id"] = USER_ID

    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except OSError:
            pass
    header()
    print()
    load_checkpoint()

    while not stop.is_set():
        header()
        choice = menu()
        print()

        if choice == "1":
            ids = [x.strip() for x in ask("Channel IDs (comma separated): ").split(",") if x.strip()]
            if ids and confirm(f"{len(ids)} channel(s)"):
                for channel_id in ids:
                    clean_channel(channel_id)
        elif choice == "2":
            response = api("GET", "/users/@me/channels")
            data = response.json() if response is not None and response.status_code == 200 else []
            channels = [c for c in data if c.get("type") in (1, 3)]
            log(f"found {len(channels)} DM channels")
            if channels and confirm("all DMs"):
                for channel in channels:
                    clean_channel(channel["id"])
        elif choice == "3":
            response = api("GET", "/users/@me/guilds")
            guilds = response.json() if response is not None and response.status_code == 200 else []
            log(f"found {len(guilds)} servers")
            if guilds and confirm("all servers"):
                for guild in guilds:
                    log(paint(f"Server: {guild.get('name', '?')}", "bold", "cyan"))
                    for channel in guild_text_channels(guild["id"]):
                        clean_channel(channel["id"])
        elif choice == "4":
            guild_id = ask("Server ID: ")
            channels = guild_text_channels(guild_id) if guild_id else []
            log(f"found {len(channels)} text channels")
            if channels and confirm("this server"):
                for channel in channels:
                    clean_channel(channel["id"])
        elif choice == "5":
            retry_failed()
        elif choice == "6":
            show_stats()
        elif choice == "7":
            settings_menu()
            continue
        elif choice == "0":
            break
        else:
            log("invalid choice", "warn")

        print()
        ask("Press Enter to continue ")

    stop.set()
    save_state()
    show_stats()
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop.set()
        save_state()
        print(f"\n\n  {paint('!', 'yellow')}  Cancelled")
        show_stats()
        print()
