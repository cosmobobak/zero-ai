def read_users() -> "dict[str, str]":
    with open("users.txt", 'r') as f:
        no_empty = filter(lambda x: len(x) > 0, f)
        tokens = map(lambda x: x.split(" "), no_empty)
        return {uid: name for uid, name in tokens}

def save_user(uid: str, name: str):
    with open("users.txt", 'a') as f:
        f.write(f"{uid} {name}\n")
