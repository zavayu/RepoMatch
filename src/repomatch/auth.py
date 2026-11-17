
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator
from pwdlib import PasswordHash

load_dotenv()

router = APIRouter()
hasher = PasswordHash.recommended()
db_path = Path(__file__).resolve().parents[1] / "users.db"

secret = os.environ.get("REPOMATCH_AUTH_SECRET")
if not secret:
    raise RuntimeError("Set REPOMATCH_AUTH_SECRET in your .env file")


class User(BaseModel):
    email: EmailStr
    password: str


class SkillsUpdate(BaseModel):
    skills: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]] = Field(max_length=50)

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, skills):
        seen = set()
        result = []
        for skill in skills:
            if skill.casefold() not in seen:
                seen.add(skill.casefold())
                result.append(skill)
        return result


def init_db():
    with sqlite3.connect(db_path) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        columns = [
            row[1]
            for row in db.execute("PRAGMA table_info(users)")
        ]

        if "id" not in columns:
            db.execute("ALTER TABLE users RENAME TO old_users")

            db.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

            db.execute("""
                INSERT INTO users (email, password)
                SELECT email, password FROM old_users
            """)

            db.execute("DROP TABLE old_users")

        # Add skills without changing existing account IDs or password hashes
        columns = [row[1] for row in db.execute("PRAGMA table_info(users)")]
        if "skills" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN skills TEXT NOT NULL DEFAULT '[]'")


def create_token(user_id: int):
    expires = datetime.now(timezone.utc) + timedelta(days=7)

    return jwt.encode(
        {"sub": str(user_id), "exp": expires},
        secret,
        algorithm="HS256",
    )


def set_session(response: Response, user_id: int):
    response.set_cookie(
        key="repomatch_session",
        value=create_token(user_id),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
    )

# this untion checks whether a user is logged in and returns their user ID
def require_user(request: Request):
    token = request.cookies.get("repomatch_session")

    if not token:
        raise HTTPException(401, "Please log in")

    try:
        data = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = int(data["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired session")

    with sqlite3.connect(db_path) as db:
        user = db.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if not user:
        raise HTTPException(401, "Account no longer exists")

    return user_id


@router.post("/api/signup")
def signup(user: User, response: Response):
    if len(user.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    email = user.email.strip().lower()

    with sqlite3.connect(db_path) as db:
        try:
            cursor = db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hasher.hash(user.password)),
            )
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(400, "Account already exists")

    set_session(response, user_id)
    return {"message": "Account created"}


@router.post("/api/login")
def login(user: User, response: Response):
    email = user.email.strip().lower()

    with sqlite3.connect(db_path) as db:
        result = db.execute(
            "SELECT id, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not result or not hasher.verify(user.password, result[1]):
        raise HTTPException(401, "Invalid login")

    set_session(response, result[0])
    return {"message": "Login successful"}





@router.get("/api/me")
def me(user_id: int = Depends(require_user)):
    with sqlite3.connect(db_path) as db:
        result = db.execute(
            "SELECT email, skills FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return {"id": user_id, "email": result[0], "skills": json.loads(result[1])}


@router.put("/api/me/skills")
def update_skills(update: SkillsUpdate, user_id: int = Depends(require_user)):
    with sqlite3.connect(db_path) as db:
        db.execute(
            "UPDATE users SET skills = ? WHERE id = ?",
            (json.dumps(update.skills), user_id),
        )
    return {"skills": update.skills}



@router.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("repomatch_session")
    return {"message": "Logged out"}
