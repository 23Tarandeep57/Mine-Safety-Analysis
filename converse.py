import os
import sys
import time
from utility.config import DATA_DIR

USER_QUERY_FILE = DATA_DIR / "user_query.txt"
BOT_RESPONSE_FILE = DATA_DIR / "bot_response.txt"

def main():
    """Main function to run the chatbot."""
    print("--- Chatbot is ready. Type 'exit' to quit. ---")

    while True:
        try:
            query = input("You: ")
            if query.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break

            # Write the query to the user_query.txt file
            with open(USER_QUERY_FILE, "w") as f:
                f.write(query)

            # Wait for the response from the bot
            while not os.path.exists(BOT_RESPONSE_FILE) or os.path.getsize(BOT_RESPONSE_FILE) == 0:
                time.sleep(1)

            with open(BOT_RESPONSE_FILE, "r") as f:
                answer = f.read().strip()
            
            print(f"Chatbot: {answer}")

            # Clear the response file
            with open(BOT_RESPONSE_FILE, "w") as f:
                f.truncate(0)

        except (KeyboardInterrupt, EOFError):
            print("\nChatbot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()