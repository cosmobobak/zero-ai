from typing import Optional
from storage import get_all_quotes, read_raw_text
from markovify import NewlineText
from time import time

def generate_quote(model: NewlineText) -> Optional[str]:
    quote = model.make_short_sentence(200, min_chars=20, tries=100)
    return quote


def generate_model(user: str, ssize: int) -> NewlineText:
    quotes = read_raw_text(user)
    model = NewlineText(quotes, state_size=ssize)
    return model

def regenerate_models(models: "dict[str, NewlineText]", usernames: "list[str]", ssize=1):
    for user in sorted(usernames):
        start_time = time()
        models[user] = generate_model(user, ssize)
        print(f"Generated model for {user} in {(time() - start_time)*1000:.2f} ms")

