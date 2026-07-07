"""Reset a user's password directly in the deerflow SQLite database.

Usage:
    python backend/scripts/reset_password.py <email> <new_password>
"""

import base64
import hashlib
import sqlite3
import sys
from pathlib import Path

import bcrypt

DB_PATH = Path(__file__).resolve().parent.parent / ".deer-flow" / "data" / "deerflow.db"
_PREFIX_V2 = "$dfv2$"


def hash_password(password: str) -> str:
    pre_hash = base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())
    raw = bcrypt.hashpw(pre_hash, bcrypt.gensalt()).decode("utf-8")
    return f"{_PREFIX_V2}{raw}"


def reset_password(email: str, new_password: str) -> None:
    new_hash = hash_password(new_password)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        print(f"Không tìm thấy user với email: {email}")
        conn.close()
        return

    cur.execute(
        """UPDATE users
           SET password_hash = ?, token_version = token_version + 1
           WHERE email = ?""",
        (new_hash, email),
    )
    conn.commit()
    conn.close()
    print(f"Đã reset password cho {email}. Token cũ cũng bị invalidate luôn.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        sys.exit(1)
    reset_password(sys.argv[1], sys.argv[2])
