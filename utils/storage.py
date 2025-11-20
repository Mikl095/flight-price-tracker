# utils/storage.py
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any

DATA_DIR = "."  # ou "./data" si tu utilises un dossier data/
ROUTES_FILE = os.path.join(DATA_DIR, "routes.json")
EMAIL_CFG_FILE = os.path.join(DATA_DIR, "email_config.json")
LOG_FILE = os.path.join(DATA_DIR, "last_updates.log")


def _atomic_write(path: str, data_bytes: bytes):
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data_bytes)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def ensure_data_file():
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except Exception:
            pass
    if not os.path.exists(ROUTES_FILE):
        _atomic_write(ROUTES_FILE, b"[]")
    if not os.path.exists(EMAIL_CFG_FILE):
        _atomic_write(EMAIL_CFG_FILE, json.dumps({"enabled": False, "email": "", "api_user": "", "api_pass": ""}).encode("utf-8"))
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()


def load_routes() -> List[Dict[str, Any]]:
    try:
        with open(ROUTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except Exception:
        try:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            bad = f"{ROUTES_FILE}.broken.{ts}"
            os.replace(ROUTES_FILE, bad)
        except Exception:
            pass
        return []


def _git_commit_and_push_if_enabled(path: str, commit_msg: str = None):
    """
    Optionally commit & push changes to the repo if environment variables are set.
    Variables:
      - GIT_PUSH = "1" or "true" to enable
      - GIT_PUSH_TOKEN = personal access token or GitHub Actions token
      - GITHUB_REPOSITORY = "owner/repo" (optional; read from env in GH actions)
    This function is tolerant: on any error it logs to stderr but does NOT raise.
    """
    try:
        enabled = os.environ.get("GIT_PUSH", "").lower() in ("1", "true", "yes")
        token = os.environ.get("GIT_PUSH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")  # owner/repo

        if not enabled or not token:
            return False, "git push not enabled or no token"

        # Determine repo remote URL
        # If running inside a git repo, get origin URL to detect owner/repo fallback
        if not repo:
            try:
                res = subprocess.run(["git", "config", "--get", "remote.origin.url"],
                                     capture_output=True, text=True, check=False)
                origin = (res.stdout or "").strip()
                # try to parse origin for owner/repo
                if origin:
                    # support https and git@ forms
                    if origin.startswith("git@"):
                        # git@github.com:owner/repo.git
                        origin = origin.split(":", 1)[1]
                    if origin.endswith(".git"):
                        origin = origin[:-4]
                    repo = origin
            except Exception:
                repo = None

        if not repo:
            # If still unknown, cannot push securely
            return False, "repo unknown"

        # Build https remote using token (note: token appears in process args -> keep minimal)
        remote_with_token = f"https://{token}@github.com/{repo}.git"

        # git add path, commit, push using subprocess
        # Use a temporary remote name to avoid altering origin
        remote_name = "autopush-temp-remote"

        # Add remote
        subprocess.run(["git", "remote", "remove", remote_name], check=False, capture_output=True)
        subprocess.run(["git", "remote", "add", remote_name, remote_with_token], check=True, capture_output=True)

        # Stage file
        subprocess.run(["git", "add", path], check=True, capture_output=True)

        msg = commit_msg or f"Auto-save routes {os.path.basename(path)} @ {datetime.now().isoformat()}"
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)

        # Push to the default branch (use HEAD)
        subprocess.run(["git", "push", remote_name, "HEAD"], check=True, capture_output=True)

        # Remove remote
        subprocess.run(["git", "remote", "remove", remote_name], check=False, capture_output=True)

        return True, "pushed"
    except subprocess.CalledProcessError as cpe:
        # capture stderr for debugging
        err = cpe.stderr.decode() if hasattr(cpe, "stderr") and isinstance(cpe.stderr, (bytes, bytearray)) else str(cpe)
        return False, f"git error: {err}"
    except Exception as e:
        return False, f"git exception: {e}"


def save_routes(routes: List[Dict[str, Any]], commit_and_push: bool = False):
    """
    Save routes to JSON atomically.
    If commit_and_push=True, tentera de commit & push en utilisant GIT_PUSH_TOKEN (ou GITHUB_TOKEN).
    """
    try:
        b = json.dumps(routes, ensure_ascii=False, indent=2).encode("utf-8")
        _atomic_write(ROUTES_FILE, b)
    except Exception as e:
        # if save fails, raise to surface error
        raise

    # Optionally commit & push (gracieux)
    if commit_and_push:
        ok, msg = _git_commit_and_push_if_enabled(ROUTES_FILE, commit_msg=None)
        # we don't raise on push failure to avoid breaking the app; but write a small local log
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - save_routes commit_and_push: ok={ok} msg={msg}\n")
        except Exception:
            pass

import subprocess
import shlex
import json
import time

def _git_commit_and_push_if_enabled(path: str = ROUTES_FILE, commit_msg: str = None):
    """
    Attempt to commit the given file and push using GIT_PUSH_TOKEN if env enabled.
    Writes a single-line log to LOG_FILE describing result.
    Returns dict {"ok": bool, "msg": str, "detail": str}
    """
    try:
        git_push_flag = os.environ.get("GIT_PUSH", "").lower() in ("1", "true", "yes")
        token = os.environ.get("GIT_PUSH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
        timestamp = datetime.now().isoformat()

        if not git_push_flag or not token:
            msg = "git push not enabled or no token"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # try to discover remote repo if not provided
        if not repo:
            try:
                # try git remote get-url origin
                p = subprocess.run(shlex.split("git remote get-url origin"), capture_output=True, text=True, check=True)
                url = p.stdout.strip()
                # derive owner/repo from url
                if url.startswith("git@"):
                    # git@github.com:owner/repo.git
                    repo = url.split(":", 1)[1].rstrip(".git")
                else:
                    # https://github.com/owner/repo.git
                    repo = url.rstrip(".git").split("/")[-2] + "/" + url.rstrip(".git").split("/")[-1]
            except Exception:
                repo = None

        if not repo:
            msg = "could not determine repository (set GITHUB_REPOSITORY env)"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # Make sure we are in a git repo
        try:
            subprocess.run(shlex.split("git status --porcelain"), capture_output=True, text=True, check=True)
        except Exception as e:
            # not a git repo or git not available
            msg = f"git not available or not a repo: {e}"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # Stage the file
        try:
            subprocess.run(["git", "add", path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            detail = e.stderr or e.stdout or str(e)
            msg = "git add failed"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg} detail={detail}")
            return {"ok": False, "msg": msg, "detail": detail}

        # Commit if there are staged changes
        if not commit_msg:
            commit_msg = f"Auto update {os.path.basename(path)} via app at {datetime.now().isoformat()}"
        try:
            # commit may fail if no changes to commit
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # if no changes to commit, treat as ok (nothing to push)
            out = (e.stdout or "") + (e.stderr or "")
            if "nothing to commit" in out.lower():
                append_log(f"{timestamp} - save_routes commit_and_push: ok=True msg=no_changes")
                return {"ok": True, "msg": "no_changes", "detail": out}
            # otherwise return error
            detail = out or str(e)
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git commit failed detail={detail}")
            return {"ok": False, "msg": "git commit failed", "detail": detail}

        # Create a temporary remote with token embedded
        owner_repo = repo  # expected owner/repo
        remote_name = f"autopush-{int(time.time())}"
        # compose remote url: https://<token>@github.com/owner/repo.git
        remote_url = f"https://{token}@github.com/{owner_repo}.git"
        try:
            subprocess.run(["git", "remote", "add", remote_name, remote_url], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            detail = e.stderr or e.stdout or str(e)
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git remote add failed detail={detail}")
            return {"ok": False, "msg": "git remote add failed", "detail": detail}

        # Push
        try:
            p = subprocess.run(["git", "push", remote_name, "HEAD"], check=True, capture_output=True, text=True)
            detail = p.stdout or p.stderr or ""
            append_log(f"{timestamp} - save_routes commit_and_push: ok=True msg=pushed detail={detail}")
            return {"ok": True, "msg": "pushed", "detail": detail}
        except subprocess.CalledProcessError as e:
            detail = e.stderr or e.stdout or str(e)
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git push failed detail={detail}")
            return {"ok": False, "msg": "git push failed", "detail": detail}
        finally:
            # clean up remote (best-effort)
            try:
                subprocess.run(["git", "remote", "remove", remote_name], capture_output=True, text=True)
            except Exception:
                pass

    except Exception as e:
        timestamp = datetime.now().isoformat()
        append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=exception detail={str(e)}")
        return {"ok": False, "msg": "exception", "detail": str(e)}
        

def load_email_config() -> dict:
    try:
        with open(EMAIL_CFG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_email_config(cfg: dict):
    b = json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write(EMAIL_CFG_FILE, b)


def append_log(line: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        pass


def count_updates_last_24h(route: dict) -> int:
    from datetime import datetime, timedelta
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    cnt = 0
    for h in route.get("history", []) or []:
        d = h.get("date")
        if not d:
            continue
        try:
            if isinstance(d, (int, float)):
                dt = datetime.fromtimestamp(d)
            else:
                dt = datetime.fromisoformat(str(d))
            if dt >= cutoff:
                cnt += 1
        except Exception:
            continue
    return cnt


def ensure_route_fields(r: dict):
    r.setdefault("id", "")
    r.setdefault("origin", "")
    r.setdefault("destination", "")
    r.setdefault("departure", None)
    r.setdefault("departure_flex_days", 0)
    r.setdefault("return", None)
    r.setdefault("return_flex_days", 0)
    r.setdefault("return_airport", None)
    r.setdefault("stay_min", 1)
    r.setdefault("stay_max", 1)
    r.setdefault("target_price", 100.0)
    r.setdefault("tracking_per_day", 1)
    r.setdefault("notifications", False)
    r.setdefault("email", "")
    r.setdefault("min_bags", 0)
    r.setdefault("cabin_class", "Economy")
    r.setdefault("direct_only", False)
    r.setdefault("max_stops", "any")
    r.setdefault("avoid_airlines", [])
    r.setdefault("preferred_airlines", [])
    r.setdefault("history", [])
    r.setdefault("last_tracked", None)
    r.setdefault("stats", {})

def increment_route_stat(r: dict, key: str, amount: int = 1):
    """
    Increment a numeric stat inside route['stats'] safely.
    - r: the route dict (will ensure 'stats' exists)
    - key: stat name, ex: "updates_total", "updates_today", "notifications_sent"
    - amount: integer increment (can be negative to decrement)
    """
    try:
        if r is None:
            return
        stats = r.setdefault("stats", {})
        # If the value is missing or non-int, try to coerce to int safely
        cur = stats.get(key, 0)
        try:
            cur_val = int(cur)
        except Exception:
            cur_val = 0
        stats[key] = cur_val + int(amount)
    except Exception:
        # Never raise: stats increment is best-effort
        pass
    

# optional helpers for sanitization if needed
import numpy as np
import pandas as pd
from datetime import date, datetime

def json_safe(v):
    if v is None:
        return None
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, float) and np.isnan(v):
        return None
    if v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v

def sanitize_dict(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, list):
            out[k] = [json_safe(x) for x in v]
        elif isinstance(v, dict):
            out[k] = sanitize_dict(v)
        else:
            out[k] = json_safe(v)
    return out
        
