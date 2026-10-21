# import json
# import os
# from google import genai

# FILE = "tickets.json"
# MODEL = "gemini-2.5-flash"

# api_key = os.environ.get("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key) if api_key else None


# def fallback_note(ticket):
#     """Simple rule-based note used if the AI is unavailable."""
#     text = (ticket["title"] + " " + ticket["description"]).lower()
#     urgent = ["down", "crash", "error", "cannot", "can't", "urgent", "broken", "not working"]
#     priority = "high" if any(w in text for w in urgent) else "medium"
#     return f"Summary: {ticket['title']}. Suggested priority: {priority}."


# def ai_message(ticket):
#     """Ask Gemini to review the ticket. Never crashes the app."""
#     if client is None:
#         return fallback_note(ticket)
#     try:
#         prompt = (
#             "You are a helpdesk assistant. In at most 2 sentences, summarize "
#             "this ticket and suggest a priority (low, medium or high).\n\n"
#             f"Title: {ticket['title']}\n"
#             f"Description: {ticket['description']}"
#         )
#         response = client.models.generate_content(model=MODEL, contents=prompt)
#         return response.text.strip()
#     except Exception as e:
#         print("DEBUG:", e)
#         return fallback_note(ticket)


# def load_tickets():
#     if not os.path.exists(FILE):
#         return []
#     try:
#         with open(FILE, encoding="utf-8") as f:
#             return json.load(f)
#     except json.JSONDecodeError:
#         print("Warning: tickets.json is corrupted; starting empty.")
#         return []


# def save_tickets(tickets):
#     with open(FILE, "w", encoding="utf-8") as f:
#         json.dump(tickets, f, indent=4)


# def create_ticket():
#     tickets = load_tickets()
#     ticket = {
#         "id": max((t["id"] for t in tickets), default=0) + 1,
#         "name": input("Your name: "),
#         "title": input("Title: "),
#         "description": input("Description: "),
#         "status": "open",
#     }

#     print("\nAI is reviewing your ticket...")
#     note = ai_message(ticket)
#     print(f"AI message: {note}\n")
#     ticket["ai_note"] = note

#     tickets.append(ticket)
#     save_tickets(tickets)
#     print(f"Ticket {ticket['id']} created.")


# def list_tickets():
#     tickets = load_tickets()
#     if not tickets:
#         print("No tickets yet.")
#         return
#     for t in tickets:
#         print(f"{t['id']} [{t['status']}] {t['title']} - {t['name']}")
#         if t.get("ai_note"):
#             print(f"    AI: {t['ai_note']}")


# def close_ticket():
#     tickets = load_tickets()
#     try:
#         ticket_id = int(input("Ticket ID to close: "))
#     except ValueError:
#         print("Please enter a number.")
#         return
#     for t in tickets:
#         if t["id"] == ticket_id:
#             t["status"] = "closed"
#             save_tickets(tickets)
#             print("Ticket closed.")
#             return
#     print("No ticket with that ID.")


# def main():
#     while True:
#         print("\n1) New ticket  2) List  3) Close  4) Quit")
#         choice = input("Choose: ")
#         if choice == "1":
#             create_ticket()
#         elif choice == "2":
#             list_tickets()
#         elif choice == "3":
#             close_ticket()
#         elif choice == "4":
#             break
#         else:
#             print("Invalid choice")


# if __name__ == "__main__":
#     main()

## REPLACED
import json
import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "tickets.json")
KEY_FILE = os.path.join(BASE_DIR, "api_key.txt")
MODEL = "gemini-2.5-flash"
DEBUG = False  # set to True to see why the AI call fails


def get_api_key():
    """Use GEMINI_API_KEY if set, otherwise read api_key.txt next to this file."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            return f.read().strip()
    return None


def fallback_note(ticket):
    """Simple rule-based note used if the AI is unavailable."""
    text = (ticket["title"] + " " + ticket["description"]).lower()
    urgent = ["down", "crash", "error", "cannot", "can't", "urgent", "broken", "not working"]
    priority = "high" if any(w in text for w in urgent) else "medium"

    if any(w in text for w in ["network", "wifi", "internet", "slow", "connection", "configuration"]):
        solution = "Restart your device and router, reconnect to the network, then test another site or device. If it continues, report the location and time to IT."
    elif any(w in text for w in ["software", "app", "install", "program"]):
        solution = "Restart the application, check for updates, and reinstall it if the problem continues."
    elif any(w in text for w in ["password", "login", "account"]):
        solution = "Reset your password and make sure Caps Lock is off. Contact IT if you are still locked out."
    elif any(w in text for w in ["printer", "print"]):
        solution = "Check the printer is on and connected, clear any paper jam, and try printing again."
    else:
        solution = "Restart the device and note any error message to share with IT support."

    return (
        f"Summary: {ticket['title']}\n"
        f"Priority: {priority}\n"
        f"Suggested solution: {solution}"
    )


def ai_message(ticket):
    """Ask Gemini to review the ticket. Never crashes the app."""
    api_key = get_api_key()
    if not api_key:
        return fallback_note(ticket)
    try:
        prompt = (
            "You are an IT helpdesk assistant for a campus. Read the ticket and reply "
            "in this exact format, using plain text and no markdown:\n"
            "Summary: <one sentence>\n"
            "Priority: <low, medium or high>\n"
            "Suggested solution: <2 to 4 short, practical steps the user can try first>\n\n"
            f"Title: {ticket['title']}\n"
            f"Description: {ticket['description']}"
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        if DEBUG:
            print("DEBUG:", e)
        return fallback_note(ticket)


def load_tickets():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Warning: tickets.json is corrupted; starting empty.")
        return []


def save_tickets(tickets):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=4)


def create_ticket():
    tickets = load_tickets()
    ticket = {
        "id": max((t["id"] for t in tickets), default=0) + 1,
        "name": input("Your name: "),
        "title": input("Title: "),
        "description": input("Description: "),
        "status": "open",
    }

    print("\nAI is reviewing your ticket...")
    note = ai_message(ticket)
    print(f"AI message: {note}\n")
    ticket["ai_note"] = note

    tickets.append(ticket)
    save_tickets(tickets)
    print(f"Ticket {ticket['id']} created.")


def list_tickets():
    tickets = load_tickets()
    if not tickets:
        print("No tickets yet.")
        return
    for t in tickets:
        print(f"{t['id']} [{t['status']}] {t['title']} - {t['name']}")
        if t.get("ai_note"):
                        print("    AI: " + t["ai_note"].replace("\n", "\n        "))


def close_ticket():
    tickets = load_tickets()
    try:
        ticket_id = int(input("Ticket ID to close: "))
    except ValueError:
        print("Please enter a number.")
        return
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = "closed"
            save_tickets(tickets)
            print("Ticket closed.")
            return
    print("No ticket with that ID.")


def main():
    while True:
        print("\n1) New ticket  2) List  3) Close  4) Quit")
        choice = input("Choose: ")
        if choice == "1":
            create_ticket()
        elif choice == "2":
            list_tickets()
        elif choice == "3":
            close_ticket()
        elif choice == "4":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
print("    AI: " + t["ai_note"].replace("\n", "\n        "))