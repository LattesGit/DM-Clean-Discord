#!/usr/bin/env python3
import argparse
import concurrent.futures
import getpass
import json
import os
import random
import re
import sys
import threading
import time
from datetime import datetime

import requests


WHITELIST_CHANNELS = []
WHITELIST_USERS = []
DRY_RUN = True
OLDER_THAN_DAYS = 0
WORKERS = 3
KEYWORD = ""
KEEP_PINNED = False


API = "https://discord.com/api/v10"
DELETABLE_TYPES = {0, 19, 20, 23}
DISCORD_EPOCH = 1420070400000
MAX_RETRIES = 8
TIMEOUT = 15
LOG_FILE = "latent_clean_log.txt"
FAILED_FILE = "latent_clean_failed.txt"
CHECKPOINT_FILE = "latent_clean_checkpoint.json"
CHECKPOINT_EVERY = 250

CODES = {"reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "red": "\033[91m",
         "green": "\033[92m", "yellow": "\033[93m", "cyan": "\033[96m"}
ANSI_RE = re.compile(r"\033\[[0-9;]*m")
LINE = "─" * 44


cfg = argparse.Namespace(
    dry=DRY_RUN, days=OLDER_THAN_DAYS, workers=WORKERS, keyword=KEYWORD,
    keep_pinned=KEEP_PINNED, yes=False,
    wl_channels={str(x) for x in WHITELIST_CHANNELS},
    wl_users={str(x) for x in WHITELIST_USERS},
)
stats = {"channels": 0, "found": 0, "deleted": 0, "failed": 0, "skipped": 0, "rate_limits": 0}
START = time.time()
lock = threading.Lock()
io_lock = threading.Lock()
stop = threading.Event()
failed = []
done_channels = set()
bucket_until = {}
global_until = 0.0
session = requests.Session()
account = {"name": "", "id": ""}


def paint(text, *styles):
    return "".join(CODES[s] for s in styles) + str(text) + CODES["reset"]


def log(message, level="info"):
    marks = {"info": paint("•", "cyan"), "ok": paint("✔", "green"),
             "error": paint("✘", "red"), "warn": paint("!", "yellow"),
             "skip": paint("–", "dim")}
    stamp = datetime.now().strftime("%H:%M:%S")
    with io_lock:
        print(f"  {paint(stamp, 'dim')}  {marks[level]}  {message}")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{stamp}] [{level}] {ANSI_RE.sub('', str(message))}\n")
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
    mode = paint("DRY RUN", "yellow") if cfg.dry else paint("LIVE", "red")
    age = f"older than {cfg.days} days" if cfg.days else "none"
    print(f"  {paint('Account', 'dim')}  {account['name']} ({account['id']})")
    print(f"  {paint('Mode   ', 'dim')}  {mode}")
    print(f"  {paint('Age    ', 'dim')}  {age}")
    print(f"  {paint('Keyword', 'dim')}  {cfg.keyword or 'none'}")
    print(f"  {paint('Pinned ', 'dim')}  {'kept' if cfg.keep_pinned else 'deleted too'}")
    print(f"  {paint('Threads', 'dim')}  {cfg.workers}")
    print("  " + paint(LINE, "dim"))


def ask(prompt="> "):
    try:
        return input("  " + paint(prompt, "cyan", "bold")).strip()
    except EOFError:
        return ""


def fail_screen(message):
    title()
    print(f"\n  {paint('✘', 'red')}  {message}\n")


def bucket_key(method, path):
    return method + ":" + re.sub(r"/\d{15,21}$", "/:id", path)


def api(method, path, **kwargs):
    global global_until
    key = bucket_key(method, path)
    for attempt in range(MAX_RETRIES):
        if stop.is_set():
            return None
        with lock:
            wait = max(global_until, bucket_until.get(key, 0.0)) - time.time()
        if wait > 0:
            stop.wait(wait)
            if stop.is_set():
                return None
        try:
            response = session.request(method, API + path, timeout=TIMEOUT, **kwargs)
        except requests.RequestException:
            stop.wait(min(2 * (attempt + 1), 10))
            continue

        if response.status_code == 429:
            try:
                data = response.json()
                retry = float(data.get("retry_after", 2))
                is_global = bool(data.get("global", False))
            except (ValueError, TypeError):
                retry, is_global = 2.0, False
            until = time.time() + retry + 0.2
            with lock:
                stats["rate_limits"] += 1
                if is_global:
                    global_until = max(global_until, until)
                else:
                    bucket_until[key] = max(bucket_until.get(key, 0.0), until)
            continue

        if response.status_code == 401:
            log("Token invalid or expired (401)", "error")
            stop.set()
            return None

        if response.status_code >= 500:
            stop.wait(min(2 * (attempt + 1), 10))
            continue


        if response.headers.get("X-RateLimit-Remaining") == "0":
            try:
                reset = float(response.headers.get("X-RateLimit-Reset-After", 0))
                with lock:
                    bucket_until[key] = max(bucket_until.get(key, 0.0), time.time() + reset + 0.05)
            except ValueError:
                pass
        return response
    return None


def snowflake_time(snowflake):
    try:
        return ((int(snowflake) >> 22) + DISCORD_EPOCH) / 1000
    except (TypeError, ValueError):
        return 0


def bump(key, amount=1):
    with lock:
        stats[key] += amount


def save_state():
    with lock:
        data = {
            "stats": dict(stats),
            "failed": list(failed),
            "done_channels": sorted(done_channels),
            "timestamp": datetime.now().isoformat(),
        }
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(FAILED_FILE, "w", encoding="utf-8") as f:
            for item in data["failed"]:
                f.write(f"{item['channel_id']},{item['message_id']}\n")
    except OSError:
        pass


def load_checkpoint(auto=False):
    if not os.path.exists(CHECKPOINT_FILE):
        return
    try:
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not auto:
            answer = ask(f"Resume from checkpoint ({data['timestamp'][:16]})? [y/n] ")
            if answer.lower() != "y":
                return
        done_channels.update(str(x) for x in data.get("done_channels", []))
        failed.extend(data.get("failed", []))
        for key in ("deleted", "found", "channels", "skipped", "rate_limits"):
            stats[key] = data["stats"].get(key, 0)
        stats["failed"] = len(failed)
        log(f"checkpoint loaded ({len(done_channels)} channels already done)", "info")
    except (OSError, ValueError, KeyError):
        pass


def is_wanted(message, cutoff, keyword):
    if message.get("author", {}).get("id") != account["id"]:
        return False
    if message.get("type") not in DELETABLE_TYPES:
        return False
    if cfg.keep_pinned and message.get("pinned"):
        return False
    if cutoff and snowflake_time(message["id"]) > cutoff:
        return False
    if keyword and keyword not in (message.get("content") or "").lower():
        return False
    return True


def fetch_own_messages(channel_id):
    mine, before, scanned = [], None, 0
    cutoff = time.time() - cfg.days * 86400 if cfg.days else None
    keyword = cfg.keyword.lower()
    while not stop.is_set():
        params = {"limit": 100}
        if before:
            params["before"] = before
        response = api("GET", f"/channels/{channel_id}/messages", params=params)
        if response is None:
            if not stop.is_set():
                log(f"Channel {channel_id}: no response from API", "error")
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
        mine.extend(m["id"] for m in batch if is_wanted(m, cutoff, keyword))
        with io_lock:
            sys.stdout.write(f"\r  {paint('scanning', 'dim')}  {scanned} messages, {len(mine)} match   ")
            sys.stdout.flush()
        before = batch[-1]["id"]
        if len(batch) < 100:
            break
        stop.wait(random.uniform(0.05, 0.2))
    with io_lock:
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()
    return mine


def delete_message(channel_id, message_id):
    response = api("DELETE", f"/channels/{channel_id}/messages/{message_id}")
    if response is None:
        return "stopped" if stop.is_set() else "retries"
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
    eta = int((total - done) / rate) if rate > 0 else 0
    bar = paint("█" * filled, "green") + paint("░" * (width - filled), "dim")
    skip_txt = f"  {paint(skipped, 'yellow')} skip" if skipped else ""
    with io_lock:
        sys.stdout.write(f"\r  {bar}  {int(100 * done / total):3d}%  {done}/{total}  "
                         f"{paint(ok, 'green')} ok  {paint(bad, 'red')} failed{skip_txt}  "
                         f"{rate:.1f}/s  ~{eta}s   ")
        sys.stdout.flush()


def run_deletes(items):
    ok = bad = skip = 0
    total = len(items)
    started = time.time()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=cfg.workers)
    futures = {pool.submit(delete_message, c, m): (c, m) for c, m in items}
    try:
        for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
            channel_id, message_id = futures[future]
            try:
                status = future.result()
            except Exception:
                status = "error"
            if status in ("deleted", "gone"):
                ok += 1
                bump("deleted")
            elif status == "forbidden":
                skip += 1
                bump("skipped")
            elif status == "stopped":
                pass
            else:
                bad += 1
                with lock:
                    stats["failed"] += 1
                    failed.append({"channel_id": channel_id, "message_id": message_id})
            progress(count, total, ok, bad, started, skip)
            if count % CHECKPOINT_EVERY == 0:
                save_state()
    except KeyboardInterrupt:
        stop.set()
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    print()
    return ok, bad, skip


def clean_channel(channel_id):
    channel_id = str(channel_id)
    if stop.is_set():
        return

    if channel_id in cfg.wl_channels:
        log(f"{channel_id} is whitelisted", "skip")
        bump("skipped")
        return

    with lock:
        if channel_id in done_channels:
            log(f"{channel_id} already done", "skip")
            return

    response = api("GET", f"/channels/{channel_id}")
    info = response.json() if response is not None and response.status_code == 200 else None
    if info and info.get("type") in (1, 3) and any(
            str(u.get("id")) in cfg.wl_users for u in info.get("recipients", [])):
        log(f"{channel_name(info)} is whitelisted", "skip")
        bump("skipped")
        return

    log(paint(channel_name(info), "bold"))
    ids = fetch_own_messages(channel_id)
    if stop.is_set():
        return
    bump("found", len(ids))

    if not ids:
        with lock:
            stats["channels"] += 1
            if not cfg.dry:
                done_channels.add(channel_id)
        log("nothing to delete", "skip")
        save_state()
        return

    if cfg.dry:
        log(f"{paint(len(ids), 'yellow')} messages would be deleted (dry run)", "ok")
        return

    ok, bad, skip = run_deletes([(channel_id, mid) for mid in ids])
    if not stop.is_set():
        with lock:
            stats["channels"] += 1
            done_channels.add(channel_id)
    log(f"{ok} deleted, {bad} failed, {skip} skipped", "ok")
    save_state()


def retry_failed():
    with lock:
        items = [(i["channel_id"], i["message_id"]) for i in failed]
        failed.clear()
        stats["failed"] = 0
    if not items:
        log("no failed messages", "warn")
        save_state()
        return
    log(f"retrying {len(items)} messages")
    ok, bad, skip = run_deletes(items)
    log(f"{ok}/{len(items)} deleted, {bad} failed, {skip} skipped", "ok")
    save_state()


def guild_text_channels(guild_id):
    response = api("GET", f"/guilds/{guild_id}/channels")
    if response is None or response.status_code != 200:
        log(f"Could not read channels of server {guild_id}", "error")
        return []
    return [c for c in response.json() if c.get("type") in (0, 5)]


def do_channels(ids):
    for channel_id in ids:
        clean_channel(channel_id)


def do_dms():
    response = api("GET", "/users/@me/channels")
    data = response.json() if response is not None and response.status_code == 200 else []
    channels = [c for c in data if c.get("type") in (1, 3)]
    log(f"found {len(channels)} DM channels")
    for channel in channels:
        clean_channel(channel["id"])


def do_guild(guild_id):
    channels = guild_text_channels(guild_id)
    log(f"found {len(channels)} text channels")
    for channel in channels:
        clean_channel(channel["id"])


def do_all_guilds():
    response = api("GET", "/users/@me/guilds")
    guilds = response.json() if response is not None and response.status_code == 200 else []
    log(f"found {len(guilds)} servers")
    for guild in guilds:
        log(paint(f"Server: {guild.get('name', '?')}", "bold", "cyan"))
        do_guild(guild["id"])


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
    if cfg.dry or cfg.yes:
        return True
    print()
    return ask(f"This will permanently delete messages in {what}. Type YES to continue: ") == "YES"


def load_token():
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token and os.path.exists(".env"):
        try:
            with open(".env", encoding="utf-8") as f:
                for line in f:
                    name, _, value = line.strip().partition("=")
                    if name.strip() == "DISCORD_TOKEN":
                        token = value.strip().strip("\"'")
        except OSError:
            pass
    if not token and sys.stdin.isatty():
        token = getpass.getpass("  Token (input hidden): ").strip()
    return token.strip().strip("\"'")


def settings_menu():
    while True:
        header()
        print(f"  {paint('1', 'cyan')}  Dry run      {'on' if cfg.dry else 'off'}")
        print(f"  {paint('2', 'cyan')}  Age filter   {cfg.days} days (0 = off)")
        print(f"  {paint('3', 'cyan')}  Threads      {cfg.workers}")
        print(f"  {paint('4', 'cyan')}  Keyword      {cfg.keyword or 'off'}")
        print(f"  {paint('5', 'cyan')}  Keep pinned  {'on' if cfg.keep_pinned else 'off'}")
        print(f"  {paint('0', 'cyan')}  Back")
        print()
        choice = ask()
        if choice == "1":
            cfg.dry = not cfg.dry
        elif choice == "2":
            value = ask("Delete only messages older than how many days? ")
            cfg.days = int(value) if value.isdigit() else 0
        elif choice == "3":
            value = ask("Threads (1-10): ")
            if value.isdigit():
                cfg.workers = max(1, min(10, int(value)))
        elif choice == "4":
            cfg.keyword = ask("Keyword (empty = off): ")
        elif choice == "5":
            cfg.keep_pinned = not cfg.keep_pinned
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


def interactive():
    load_checkpoint()
    while not stop.is_set():
        header()
        choice = menu()
        print()
        if choice == "1":
            ids = [x.strip() for x in ask("Channel IDs (comma separated): ").split(",") if x.strip()]
            if ids and confirm(f"{len(ids)} channel(s)"):
                do_channels(ids)
        elif choice == "2":
            if confirm("all DMs"):
                do_dms()
        elif choice == "3":
            if confirm("all servers"):
                do_all_guilds()
        elif choice == "4":
            guild_id = ask("Server ID: ")
            if guild_id and confirm("this server"):
                do_guild(guild_id)
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


def parse_args():
    p = argparse.ArgumentParser(
        prog="main.py",
        description="LATENT CLEAN - delete your own Discord messages. "
                    "Without target flags an interactive menu is shown. Dry run is ON unless --live is given.")
    p.add_argument("-c", "--channel", nargs="+", metavar="ID", help="clean these channel IDs")
    p.add_argument("--dm", action="store_true", help="clean all DMs and group DMs")
    p.add_argument("-g", "--guild", nargs="+", metavar="ID", help="clean these server IDs")
    p.add_argument("--all-guilds", action="store_true", help="clean every server you are in")
    p.add_argument("--live", action="store_true", help="actually delete (default is dry run)")
    p.add_argument("--older-than", type=int, metavar="DAYS", help="only messages older than N days")
    p.add_argument("--keyword", metavar="TEXT", help="only messages containing TEXT")
    p.add_argument("--keep-pinned", action="store_true", help="never delete pinned messages")
    p.add_argument("-w", "--workers", type=int, metavar="N", help="delete workers (1-10)")
    p.add_argument("--skip-channel", nargs="+", default=[], metavar="ID", help="channel IDs to skip")
    p.add_argument("--skip-user", nargs="+", default=[], metavar="ID", help="skip DMs with these user IDs")
    p.add_argument("--resume", action="store_true", help="resume from the last checkpoint")
    p.add_argument("-y", "--yes", action="store_true", help="skip the YES confirmation")
    return p.parse_args()


def apply_args(args):
    if args.live:
        cfg.dry = False
    if args.older_than is not None:
        cfg.days = max(0, args.older_than)
    if args.keyword:
        cfg.keyword = args.keyword
    if args.keep_pinned:
        cfg.keep_pinned = True
    if args.workers:
        cfg.workers = max(1, min(10, args.workers))
    cfg.wl_channels.update(str(x) for x in args.skip_channel)
    cfg.wl_users.update(str(x) for x in args.skip_user)
    cfg.yes = args.yes


def main():
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = parse_args()
    apply_args(args)

    token = load_token()
    if not token:
        fail_screen("No token found. Set DISCORD_TOKEN (env var or .env file), see README.")
        return

    session.headers.update({
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })

    response = api("GET", "/users/@me")
    if response is None or response.status_code != 200:
        fail_screen("Login failed. Your token may be invalid.")
        return
    me = response.json()
    account["name"] = me.get("username", "?")
    account["id"] = str(me["id"])

    try:
        os.remove(LOG_FILE)
    except OSError:
        pass

    cli_mode = bool(args.channel or args.dm or args.guild or args.all_guilds)
    try:
        if cli_mode:
            if args.resume:
                load_checkpoint(auto=True)
            log(f"{account['name']}  ·  {'DRY RUN' if cfg.dry else 'LIVE'}")
            if confirm("the selected targets"):
                if args.channel:
                    do_channels(args.channel)
                if args.dm:
                    do_dms()
                for guild_id in args.guild or []:
                    do_guild(guild_id)
                if args.all_guilds:
                    do_all_guilds()
                if not cfg.dry and not stop.is_set() and not failed:
                    try:
                        os.remove(CHECKPOINT_FILE)
                    except OSError:
                        pass
        else:
            interactive()
    finally:
        stop.set()
        if not cli_mode or failed or not cfg.dry:
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
