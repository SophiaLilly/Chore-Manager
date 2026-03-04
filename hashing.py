import hashlib


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


if __name__ == "__main__":
    print(hash_pin(""))  # Person 1
    print(hash_pin(""))  # Person 2
    print(hash_pin(""))  # Person 3
    print(hash_pin(""))  # Person 4
    print(hash_pin(""))  # Person 5
    # etc etc whatever, its only meant to be run once
