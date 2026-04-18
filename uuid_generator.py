import uuid

def generate_uuid():
    """
    Generate a unique identifier (UUID) using the uuid4 method.

    Returns:
        str: A string representation of the generated UUID.
    """
    return str(uuid.uuid4())


if __name__ == "__main__":
    # Example usage: Generate and print a UUID
    new_uuid = generate_uuid()
    print(f"Generated UUID: {new_uuid}")