from attr import dataclass
from discord import User

@dataclass
class UserData:
    name: str
    code: str
    username: str
    isnull: bool = False

    def __eq__(self, o: object) -> bool:
        if isinstance(o, UserData):
            return self.name == o.name and self.code == o.code and self.username == o.username and self.isnull == o.isnull
        return False

    def __hash__(self) -> int:
        return hash(self.name + self.code + self.username)

def read_users() -> "set[UserData]":
    # Reads the users.txt file and returns a dictionary of uid: name
    # uid is in the format "username#1234"
    with open("users.txt", 'r') as f:
        users = set()
        for line in f:
            line = line.strip()
            if line == "":
                continue
            name, uid = line.split(":")
            username, code = uid.split("#")
            users.add(UserData(name, code, username))
        return users

def write_users(users: "set[UserData]") -> None:
    # Writes the users.txt file
    with open("users.txt", 'w') as f:
        for user in users:
            if user.isnull:
                f.write(f"{user.name}:null\n")
            else:
                f.write(f"{user.name}:{user.username}#{user.code}\n")

def save_user(uid: str, name: str):
    with open("users.txt", 'a') as f:
        f.write(f"{uid} {name}\n")
