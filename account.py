from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import TypedDict

from loguru import logger


class AccountInfo(TypedDict):
    password: str
    go_games_played: int
    go_wins: int
    gomoku_games_played: int
    gomoku_wins: int
    othello_games_played: int
    othello_wins: int


class AccountManager:
    def __init__(self, filename="accounts.json"):
        self.filename = filename
        self.accounts = self.load_accounts()
        self.login_state = {key: False for key, _ in self.accounts.items()}

    def load_accounts(self):
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename, "r") as file:
            return json.load(file)

    def save_accounts(self):
        with open(self.filename, "w") as file:
            json.dump(self.accounts, file, indent=4)

    def _hash_password(self, password: str) -> str:
        # Use a secure hashing algorithm with a salt
        salt = os.urandom(32)  # A new salt for this user
        hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return (salt + hashed_password).hex()

    def verify_password(self, username, password: str):
        salt_from_storage = bytes.fromhex(self.accounts[username]["password"])[:32]  # The salt from the stored password
        stored_password = bytes.fromhex(self.accounts[username]["password"])[32:]
        hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_from_storage, 100000)
        return hashed_password == stored_password

    def register(self, username: str, password: str):
        if username in self.accounts:
            logger.warning("Username already exists")
            return False  # Username already exists
        self.accounts[username] = AccountInfo(
            password=self._hash_password(password),
            go_games_played=0,
            go_wins=0,
            gomoku_games_played=0,
            gomoku_wins=0,
            othello_games_played=0,
            othello_wins=0,
        )
        self.save_accounts()
        return True

    def login(self, username: str, password: str) -> bool:
        if username not in self.accounts:
            logger.warning("Username does not exist, please register")
            return False  # Username does not exist
        if not self.verify_password(username, password):
            logger.warning("Incorrect password")
            return False
        self.login_state[username] = True
        logger.info("Login successful")
        return True

    def update_record(self, username: str, game: str, win: bool):
        if username not in self.login_state:
            return False
        else:
            if not self.login_state[username]:
                return False
        game_list = ["go", "gomoku", "othello"]
        if game not in game_list:
            return False
        self.accounts[username][f"{game}_games_played"] += 1
        if win:
            self.accounts[username][f"{game}_wins"] += 1
        self.save_accounts()
        return True

    def get_record(self, username: str) -> dict:
        if username not in self.login_state:
            return {}
        else:
            if not self.login_state[username]:
                return {}
        record = copy.deepcopy(self.accounts[username])
        del record["password"]
        return record


if __name__ == "__main__":
    account_manager = AccountManager()
    account_manager.register("test", "test")
    account_manager.login("test", "test")
    account_manager.update_record("test", "go", True)
    print(account_manager.get_record("test"))
