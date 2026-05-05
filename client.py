# client.py

from openai import OpenAI
import os

# `python-dotenv` is optional; only load if available.
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return

# Load .env variables if present
load_dotenv()

# Initialize Groq client
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are Jarvis, a smart AI assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024
        )

        # Try to extract text from several possible response shapes
        try:
            # dict-like response
            return response["choices"][0]["message"]["content"]
        except Exception:
            try:
                # attribute-style (OpenAI v3 client)
                return response.choices[0].message.content
            except Exception:
                # fallback to string representation
                return str(response)

    except Exception as e:
        return f"Error: {str(e)}"
    
    
if __name__ == "__main__":
    reply = ask_ai("What is the capital of France?")
    print("Jarvis:", reply)


# Uncomment for interactive testing
# if __name__ == "__main__":
#     while True:
#         user_input = input("You: ")
#
#         if user_input.lower() in ["exit", "quit"]:
#             break
#
#         reply = ask_ai(user_input)
#         print("Jarvis:", reply)


def get_result(prompt, **kwargs):
    """Compatibility wrapper so other modules can import `get_result`.

    For backward compatibility with previous code that imported
    `get_result` from `client`, this calls `ask_ai` and returns its string.
    """
    return ask_ai(prompt)