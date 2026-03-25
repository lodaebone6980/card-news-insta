"""Supabase 데이터베이스 연동"""

import hashlib
import os
import secrets
from datetime import datetime, timezone

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://wtgjiuwivdhyidxyigza.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

_client = None


def get_sb():
    global _client
    if _client is None:
        if not SUPABASE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY 환경변수를 설정하세요.")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ─── 비밀번호 해싱 ───

def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{h}:{salt}"


def verify_password(pw: str, pw_hash: str) -> bool:
    parts = pw_hash.split(":")
    if len(parts) != 2:
        return False
    stored_hash, salt = parts
    check = hashlib.sha256((salt + pw).encode()).hexdigest()
    return check == stored_hash


# ─── 사용자 ───

def login(username: str, password: str, ip: str = "", ua: str = "") -> dict | None:
    sb = get_sb()
    r = sb.table("cn_users").select("*").eq("username", username).execute()
    if not r.data:
        return None
    user = r.data[0]
    if not verify_password(password, user["password_hash"]):
        return None

    # last_login 업데이트
    sb.table("cn_users").update({
        "last_login_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", user["id"]).execute()

    # 접속 로그
    sb.table("cn_access_logs").insert({
        "user_id": user["id"],
        "action": "login",
        "ip_address": ip,
        "user_agent": ua,
    }).execute()

    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def get_all_users() -> list:
    sb = get_sb()
    r = sb.table("cn_users").select("id,username,role,created_at,last_login_at").order("created_at", desc=True).execute()
    return r.data


def get_access_logs(limit: int = 50) -> list:
    sb = get_sb()
    r = sb.table("cn_access_logs").select("*,cn_users(username)").order("created_at", desc=True).limit(limit).execute()
    return r.data


def create_user(username: str, password: str, role: str = "user") -> dict:
    sb = get_sb()
    r = sb.table("cn_users").insert({
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
    }).execute()
    return r.data[0] if r.data else {}


def delete_user(user_id: str):
    sb = get_sb()
    sb.table("cn_users").delete().eq("id", user_id).execute()


# ─── 카드뉴스 히스토리 ───

def save_card_history(user_id: str | None, session_name: str, category: str,
                      topic: str, slides_count: int, slides_data: dict,
                      png_urls: list[str]) -> dict:
    sb = get_sb()
    r = sb.table("cn_card_history").insert({
        "user_id": user_id,
        "session_name": session_name,
        "category": category,
        "topic": topic,
        "slides_count": slides_count,
        "slides_data": slides_data,
        "png_urls": png_urls,
    }).execute()
    return r.data[0] if r.data else {}


def get_card_history(user_id: str | None = None, limit: int = 20) -> list:
    sb = get_sb()
    q = sb.table("cn_card_history").select("*").order("created_at", desc=True).limit(limit)
    if user_id:
        q = q.eq("user_id", user_id)
    r = q.execute()
    return r.data


def get_card_history_item(history_id: int) -> dict | None:
    sb = get_sb()
    r = sb.table("cn_card_history").select("*").eq("id", history_id).execute()
    return r.data[0] if r.data else None
