"""Shared confirmation and validation for private operator actions."""
import re
import time
import uuid
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .models import LoginAttempt
from .security import digest, passwords


class ConfirmAdmin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    admin_password: str = Field(min_length=1, max_length=512, repr=False)


def email_address(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", value):
        raise ValueError('Enter a valid email address.')
    return value


def confirm_password(db, actor, account, supplied):
    now, key = int(time.time()), digest('admin-confirm:' + actor['id'])
    if db.query(LoginAttempt).filter(LoginAttempt.identity == key, LoginAttempt.timestamp > now - 900).count() >= 10:
        raise HTTPException(429, 'Too many password confirmation attempts. Try again later.')
    try:
        valid = passwords.verify(account.password_hash, supplied)
    except (VerificationError, InvalidHashError):
        valid = False
    if not valid:
        db.add(LoginAttempt(id=str(uuid.uuid4()), identity=key, timestamp=now)); db.commit()
        raise HTTPException(403, 'Your administrator password is incorrect.')
