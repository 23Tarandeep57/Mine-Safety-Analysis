import os
import sys
import time

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
            with open("user_query.txt", "w") as f:
                f.write(query)

            # Wait for the response from the bot
            while not os.path.exists("bot_response.txt") or os.path.getsize("bot_response.txt") == 0:
                time.sleep(1)

            with open("bot_response.txt", "r") as f:
                answer = f.read().strip()
            
            print(f"Chatbot: {answer}")

            # Clear the response file
            with open("bot_response.txt", "w") as f:
                f.truncate(0)

        except (KeyboardInterrupt, EOFError):
            print("\nChatbot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()