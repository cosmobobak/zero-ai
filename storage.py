from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    username: str
    code: str
    isnull: bool = False

    def __eq__(self, o: object) -> bool:
        if isinstance(o, UserData):
            return self.name == o.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{self.name}, {self.username}#{self.code}\n"

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
            if uid == "null":
                users.add(UserData(name, "null", "null", True))
            else:
                username, code = uid.split("#")
                users.add(UserData(name, username, code))
        return users

def write_users(users: "set[UserData]") -> None:
    # Writes the users.txt file
    with open("users.txt", 'w') as f:
        for user in sorted(users, key=lambda u: u.name):
            if user.isnull:
                f.write(f"{user.name}:null\n")
            else:
                f.write(f"{user.name}:{user.username}#{user.code}\n")

def compute_quote_distribution() -> "dict[str, int]":
    # Reads the users file, and then for each user, counts how many quotes they have
    # and returns a dictionary of quote: count
    users = read_users()
    quote_distribution = {}
    for user in users:
        if user.isnull:
            continue
        with open(f"quotes/{user.name}quotes.txt", 'r') as f:
            quote_distribution[user.name] = len(f.readlines())
    return quote_distribution
