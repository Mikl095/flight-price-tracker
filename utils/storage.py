# utils/storage.py
import json
import os
import subprocess
import shlex
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

# Optional imports used by JSON sanitizer helpers
try:
    import numpy as np
except Exception:
    np = None

try:
    import pandas as pd
except Exception:
    pd = None

# -------------------------
# Paths / constants
# -------------------------
DATA_DIR = "."
ROUTES_FILE = os.path.join(DATA_DIR, "routes.json")
EMAIL_CFG_FILE = os.path.join(DATA_DIR, "email_config.json")
LOG_FILE = os.path.join(DATA_DIR, "last_updates.log")


# -------------------------
# Low-level helpers
# -------------------------
def _atomic_write(path: str, data_bytes: bytes):
    """Write bytes to a temp file and atomically replace target."""
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data_bytes)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            # os.fsync may not be available in some environments, ignore if it fails
            pass
    os.replace(tmp, path)


def append_log(line: str):
    """Append a single line to the log file (with newline)."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        # avoid raising from logging
        pass


# -------------------------
# Ensure files exist
# -------------------------
def ensure_data_file():
    """Ensure data files exist (create defaults if missing)."""
    if not os.path.exists(ROUTES_FILE):
        _atomic_write(ROUTES_FILE, b"[]")
    if not os.path.exists(EMAIL_CFG_FILE):
        _atomic_write(EMAIL_CFG_FILE, json.dumps({"enabled": False, "email": "", "api_user": "", "api_pass": ""}).encode("utf-8"))
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()


# -------------------------
# Load / Save
# -------------------------
def load_routes() -> List[Dict[str, Any]]:
    """Load list of routes from JSON, return [] on parse error but avoid crash."""
    try:
        with open(ROUTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except Exception:
        # if malformed, rotate the file and return empty list
        try:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            bad = f"{ROUTES_FILE}.broken.{ts}"
            os.replace(ROUTES_FILE, bad)
        except Exception:
            pass
        return []


def load_email_config() -> Dict[str, Any]:
    try:
        with open(EMAIL_CFG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_email_config(cfg: Dict[str, Any]):
    b = json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write(EMAIL_CFG_FILE, b)


# -------------------------
# Git commit & push helper
# -------------------------
def _git_commit_and_push_if_enabled(path: str = ROUTES_FILE, commit_msg: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempt to commit the given file and push using GIT_PUSH_TOKEN / GITHUB_TOKEN if env enabled.
    Returns a dict with keys: ok (bool), msg (str), detail (optional).
    Also appends a human-readable single-line log to LOG_FILE.
    """
    timestamp = datetime.now().isoformat()
    try:
        git_push_flag = os.environ.get("GIT_PUSH", "").lower() in ("1", "true", "yes")
        token = os.environ.get("GIT_PUSH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")  # expected "owner/repo"

        if not git_push_flag or not token:
            msg = "git push not enabled or no token"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # try to determine repo if not provided
        if not repo:
            try:
                p = subprocess.run(shlex.split("git remote get-url origin"), capture_output=True, text=True, check=True)
                url = p.stdout.strip()
                if url:
                    if url.startswith("git@"):
                        # git@github.com:owner/repo.git
                        repo = url.split(":", 1)[1].rstrip(".git")
                    else:
                        # https://github.com/owner/repo.git
                        parts = url.rstrip(".git").split("/")
                        if len(parts) >= 2:
                            repo = parts[-2] + "/" + parts[-1]
            except Exception:
                repo = None

        if not repo:
            msg = "could not determine repository (set GITHUB_REPOSITORY env)"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # ensure git available
        try:
            subprocess.run(shlex.split("git status --porcelain"), capture_output=True, text=True, check=True)
        except Exception as e:
            msg = f"git not available or not a repo: {str(e)}"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg}")
            return {"ok": False, "msg": msg, "detail": None}

        # Stage the file
        try:
            subprocess.run(["git", "add", path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or str(e)).strip()
            msg = "git add failed"
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg={msg} detail={detail}")
            return {"ok": False, "msg": msg, "detail": detail}

        # Commit if changes exist
        if not commit_msg:
            commit_msg = f"Auto update {os.path.basename(path)} via app at {datetime.now().isoformat()}"
        try:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            out = (e.stdout or "") + (e.stderr or "")
            if "nothing to commit" in out.lower():
                append_log(f"{timestamp} - save_routes commit_and_push: ok=True msg=no_changes")
                return {"ok": True, "msg": "no_changes", "detail": out}
            detail = out.strip() or str(e)
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git commit failed detail={detail}")
            return {"ok": False, "msg": "git commit failed", "detail": detail}

        # Add temporary remote with token and push
        owner_repo = repo
        remote_name = f"autopush-{int(time.time())}"
        remote_url = f"https://{token}@github.com/{owner_repo}.git"
        try:
            subprocess.run(["git", "remote", "add", remote_name, remote_url], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or str(e)).strip()
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git remote add failed detail={detail}")
            return {"ok": False, "msg": "git remote add failed", "detail": detail}

        try:
            p = subprocess.run(["git", "push", remote_name, "HEAD"], check=True, capture_output=True, text=True)
            detail = (p.stdout or p.stderr or "").strip()
            append_log(f"{timestamp} - save_routes commit_and_push: ok=True msg=pushed detail={detail}")
            return {"ok": True, "msg": "pushed", "detail": detail}
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or str(e)).strip()
            append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=git push failed detail={detail}")
            return {"ok": False, "msg": "git push failed", "detail": detail}
        finally:
            # remove remote (best-effort)
            try:
                subprocess.run(["git", "remote", "remove", remote_name], capture_output=True, text=True)
            except Exception:
                pass

    except Exception as e:
        detail = str(e)
        append_log(f"{timestamp} - save_routes commit_and_push: ok=False msg=exception detail={detail}")
        return {"ok": False, "msg": "exception", "detail": detail}


# -------------------------
# save_routes (with optional commit+push)
# -------------------------
def save_routes(routes: List[Dict[str, Any]], commit_and_push: bool = False, commit_msg: Optional[str] = None):
    """
    Save routes to JSON atomically.
    If commit_and_push True, attempt to commit & push (logs result).
    Returns None. Logs push outcome in last_updates.log.
    """
    try:
        b = json.dumps(routes, ensure_ascii=False, indent=2).encode("utf-8")
        _atomic_write(ROUTES_FILE, b)
    except Exception as e:
        append_log(f"{datetime.now().isoformat()} - save_routes: write error: {e}")
        # still attempt commit_and_push? usually skip
        if not commit_and_push:
            return

    # If requested, attempt git commit & push (function handles its own logging)
    if commit_and_push:
        _git_commit_and_push_if_enabled(path=ROUTES_FILE, commit_msg=commit_msg)
    else:
        append_log(f"{datetime.now().isoformat()} - save_routes: saved without push")


# -------------------------
# Other utils
# -------------------------
def count_updates_last_24h(route: Dict[str, Any]) -> int:
    """Return number of history entries in the last 24 hours (robust to formats)."""
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


def ensure_route_fields(r: Dict[str, Any]):
    """Ensure a route dict has minimal expected keys (safe defaults)."""
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
    r.setdefault("cabin_class", "Economy")
    r.setdefault("min_bags", 0)
    r.setdefault("direct_only", False)
    r.setdefault("max_stops", "any")
    r.setdefault("avoid_airlines", [])
    r.setdefault("preferred_airlines", [])
    r.setdefault("history", [])
    r.setdefault("last_tracked", None)
    r.setdefault("stats", {})


def increment_route_stat(r: Dict[str, Any], key: str, amount: int = 1):
    """
    Increment a numeric stat inside route['stats'] safely.
    """
    try:
        if r is None:
            return
        stats = r.setdefault("stats", {})
        cur = stats.get(key, 0)
        try:
            cur_val = int(cur)
        except Exception:
            cur_val = 0
        stats[key] = cur_val + int(amount)
    except Exception:
        pass


# -------------------------
# JSON sanitizer helpers
# -------------------------
def json_safe(v):
    """Convert any value into a JSON-serializable type."""
    if v is None:
        return None

    if np is not None and isinstance(v, np.generic):
        return v.item()

    # numpy.nan
    if isinstance(v, float):
        try:
            import math
            if math.isnan(v):
                return None
        except Exception:
            pass

    if pd is not None and (v is pd.NA or v is pd.NaT):
        return None

    if pd is not None and isinstance(v, pd.Timestamp):
        return v.isoformat()

    if isinstance(v, (date, datetime)):
        return v.isoformat()

    return v


def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize any dict for JSON writing."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, list):
            out[k] = [json_safe(x) for x in v]
        elif isinstance(v, dict):
            out[k] = sanitize_dict(v)
        else:
            out[k] = json_safe(v)
    return out
                                                  
