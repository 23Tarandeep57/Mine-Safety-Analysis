import os
import sys
import time
from utility.config import DATA_DIR

USER_QUERY_FILE = DATA_DIR / "user_query.txt"
BOT_RESPONSE_FILE = DATA_DIR / "bot_response.txt"
EOS_TOKEN = "<EOS>"  # A special token to signal the end of the stream

def main():
    """Main function to run the chatbot."""
    print("--- Chatbot is ready. Type 'exit' to quit. ---")

    # Clear files on start-up just in case
    try:
        with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
        with open(BOT_RESPONSE_FILE, "w") as f: f.truncate(0)
    except Exception as e:
        print(f"Warning: Could not clear log files. {e}")

    while True:
        try:
            query = input("You: ")
            if query.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break

            # Write the query to the user_query.txt file to trigger the agent
            with open(USER_QUERY_FILE, "w", encoding="utf-8") as f:
                f.write(query)

            print("Chatbot: ", end='')
            sys.stdout.flush()  # Ensure "Chatbot: " prints immediately

            # --- Tailing Logic ---
            full_response = ""
            while True:
                try:
                    # Wait for the agent to create the file
                    if not os.path.exists(BOT_RESPONSE_FILE):
                        time.sleep(0.05)
                        continue

                    with open(BOT_RESPONSE_FILE, "r", encoding="utf-8") as f:
                        # Move to the end of where we last read
                        f.seek(len(full_response))
                        new_chunk = f.read()

                        if new_chunk:
                            if EOS_TOKEN in new_chunk:
                                # End of stream token found
                                final_part = new_chunk.split(EOS_TOKEN)[0]
                                
                                # --- START CHANGE ---
                                # Print the final part character-by-character
                                for char in final_part:
                                    print(char, end='')
                                    sys.stdout.flush()
                                    time.sleep(0.02)  # <-- Adjust this value to speed up/slow down
                                # --- END CHANGE ---
                                
                                full_response += final_part
                                break  # Exit the tailing loop
                            else:
                                # Normal chunk
                                
                                # --- START CHANGE ---
                                # Print the new chunk character-by-character
                                for char in new_chunk:
                                    print(char, end='')
                                    sys.stdout.flush()
                                    time.sleep(0.02)  # <-- Adjust this value to speed up/slow down
                                # --- END CHANGE ---
                                
                                full_response += new_chunk
                        else:
                            # No new content, wait a moment
                            time.sleep(0.02)
                
                except (FileNotFoundError, PermissionError):
                    time.sleep(0.05) # Wait for file to be created/released
                except Exception as e:
                    print(f"[Tailing Error] {e}")
                    time.sleep(0.1)

            print()  # Final newline after the response is complete

            # Clear both files for the next loop
            with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
            with open(BOT_RESPONSE_FILE, "w") as f: f.truncate(0)

        except (KeyboardInterrupt, EOFError):
            print("\nChatbot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()