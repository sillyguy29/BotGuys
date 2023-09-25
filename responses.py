
count = 0
def handle_responses(message) -> str:
    processed = message.lower().strip()
    if message == "test":
        return "Response"
    
    if message == "count":
        count += 1
        return str(count)