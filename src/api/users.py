"""
Study[S]ync Simple User Database
Stores users and their registered courses in a JSON file.
"""
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional

USERS_JSON_PATH = Path(__file__).resolve().parents[2] / "data" / "users.json"


def _load_users() -> list:
    if not USERS_JSON_PATH.exists():
        return []
    with open(USERS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: list):
    os.makedirs(USERS_JSON_PATH.parent, exist_ok=True)
    with open(USERS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str, salt: Optional[str] = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return salt, key.hex()


def _verify_password(password: str, salt: str, hash_hex: str) -> bool:
    _, computed = _hash_password(password, salt)
    return computed == hash_hex


def get_user_by_username(username: str) -> Optional[dict]:
    users = _load_users()
    username_lower = username.strip().lower()
    for u in users:
        if u.get("username", "").lower() == username_lower:
            return u
    return None


def get_user_by_token(token: str) -> Optional[dict]:
    users = _load_users()
    for u in users:
        if u.get("token") == token:
            # Simple token expiry: 7 days
            issued = u.get("token_issued_at", 0)
            if time.time() - issued > 7 * 24 * 3600:
                return None
            return u
    return None


def create_user(username: str, password: str) -> dict:
    users = _load_users()
    if get_user_by_username(username):
        raise ValueError("Username already exists")

    salt, pw_hash = _hash_password(password)
    user = {
        "id": secrets.token_hex(8),
        "username": username.strip(),
        "salt": salt,
        "password_hash": pw_hash,
        "courses": [],
        "created_at": time.time(),
        "token": None,
        "token_issued_at": 0,
    }
    users.append(user)
    _save_users(users)
    return {"id": user["id"], "username": user["username"], "courses": []}


def authenticate_user(username: str, password: str) -> Optional[str]:
    users = _load_users()
    username_lower = username.strip().lower()
    for user in users:
        if user.get("username", "").lower() == username_lower:
            if _verify_password(password, user["salt"], user["password_hash"]):
                token = secrets.token_hex(16)
                user["token"] = token
                user["token_issued_at"] = time.time()
                _save_users(users)
                return token
    return None


def logout_user(token: str):
    users = _load_users()
    for user in users:
        if user.get("token") == token:
            user["token"] = None
            user["token_issued_at"] = 0
            _save_users(users)
            return


def add_user_course(token: str, course_name: str, course_num: str) -> dict:
    users = _load_users()
    for user in users:
        if user.get("token") == token:
            # Simple token expiry check
            issued = user.get("token_issued_at", 0)
            if time.time() - issued > 7 * 24 * 3600:
                raise PermissionError("Invalid or expired token")

            course_num = course_num.strip()
            course_name = course_name.strip()

            # Prevent duplicates by course_num
            for c in user.get("courses", []):
                if c["course_num"] == course_num:
                    raise ValueError("Course already registered")

            user["courses"].append({"course_name": course_name, "course_num": course_num})
            _save_users(users)
            return {"courses": user["courses"]}
    raise PermissionError("Invalid or expired token")


def remove_user_course(token: str, course_num: str) -> dict:
    users = _load_users()
    for user in users:
        if user.get("token") == token:
            issued = user.get("token_issued_at", 0)
            if time.time() - issued > 7 * 24 * 3600:
                raise PermissionError("Invalid or expired token")

            user["courses"] = [c for c in user["courses"] if c["course_num"] != course_num]
            _save_users(users)
            return {"courses": user["courses"]}
    raise PermissionError("Invalid or expired token")


def get_user_courses(token: str) -> list:
    user = get_user_by_token(token)
    if not user:
        raise PermissionError("Invalid or expired token")
    return user.get("courses", [])
