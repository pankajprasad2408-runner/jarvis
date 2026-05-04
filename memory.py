import json

MEMORY_FILE = "memory.json"

# Load memory
def get_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# Save memory
def add_to_memory(key, value):
    memory = get_memory()
    memory[key] = value

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)