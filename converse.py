import os
import sys
import time
from utility.config import DATA_DIR

USER_QUERY_FILE = DATA_DIR / "user_query.txt"
BOT_RESPONSE_FILE = DATA_DIR / "bot_response.txt"
EOS_TOKEN = "<EOS>"  # A special token to signal the end of the stream
WAIT_TIMEOUT = 60  # seconds

def main():
    """Main function to run the chatbot."""
    print("--- Chatbot is ready. Type 'exit' to quit. ---")

    # Clear files on start-up just in case
    try:
        if USER_QUERY_FILE.exists():
            with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
        if BOT_RESPONSE_FILE.exists():
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
            sys.stdout.flush()

            # --- Tailing Logic with Timeout and Animation ---
            start_time = time.time()
            full_response = ""
            animation = ' |/-\ '
            anim_idx = 0
            
            waiting_message_printed = False
            while time.time() - start_time < WAIT_TIMEOUT:
                try:
                    if not BOT_RESPONSE_FILE.exists() or BOT_RESPONSE_FILE.stat().st_size == 0:
                        # File doesn't exist or is empty, show waiting animation
                        if not waiting_message_printed:
                            print("Thinking...", end='', flush=True)
                            waiting_message_printed = True
                        else:
                            print(f"\b{animation[anim_idx]}", end="", flush=True)
                            anim_idx = (anim_idx + 1) % len(animation)
                        time.sleep(0.1)
                        continue

                    # Clear the "Thinking..." message
                    if waiting_message_printed:
                        print("\b" * 12 + " " * 12 + "\b" * 12, end="", flush=True)
                        waiting_message_printed = False # so it doesn't clear again


                    with open(BOT_RESPONSE_FILE, "r", encoding="utf-8") as f:
                        current_content = f.read()
                    
                    # print(f"\ncurrent_content: {len(current_content)}, full_response: {len(full_response)}")

                    if len(current_content) > len(full_response):
                        new_text = current_content[len(full_response):]
                        
                        if EOS_TOKEN in new_text:
                            final_part = new_text.split(EOS_TOKEN)[0]
                            for char in final_part:
                                print(char, end='')
                                sys.stdout.flush()
                                time.sleep(0.02)  # Adjust this value for desired speed
                            full_response += final_part
                            break # Exit loop
                        else:
                            for char in new_text:
                                print(char, end='')
                                sys.stdout.flush()
                                time.sleep(0.02)  # Adjust this value for desired speed
                            full_response += new_text
                    
                    if EOS_TOKEN in current_content:
                        break # EOS token might have been in the part we already processed

                    time.sleep(0.05)
                
                except (FileNotFoundError, PermissionError):
                    time.sleep(0.05)
                except Exception as e:
                    print(f"\n[Tailing Error] {e}")
                    break
            
            if time.time() - start_time >= WAIT_TIMEOUT and not full_response:
                if waiting_message_printed:
                    print("\b" * 12 + " " * 12 + "\b" * 12, end="", flush=True)
                print("Sorry, the request timed out. Please try again.")

            print()  # Final newline

            # Clear files for the next loop
            if USER_QUERY_FILE.exists():
                with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
            if BOT_RESPONSE_FILE.exists():
                with open(BOT_RESPONSE_FILE, "w") as f: f.truncate(0)

        except (KeyboardInterrupt, EOFError):
            print("\nChatbot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()