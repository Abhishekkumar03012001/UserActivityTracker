# Required: pip install google-genai

import os
from google import genai
from google.genai import types

def generate():
    # ✅ Load API key from environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")

    # ❌ Stop execution if key not found
    if not api_key:
        raise ValueError("API key not found. Set the 'GOOGLE_API_KEY' environment variable.")

    # ✅ Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # ✅ Use Gemini 1.5 Pro
    model = "gemini-1.5-pro-latest"

    # ✅ Read prompt from a file
    file_path = "prompt_input.txt"  # Change this path if needed

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The prompt file '{file_path}' was not found.")

    with open(file_path, "r", encoding="utf-8") as file:
        file_prompt = file.read().strip()

    if not file_prompt:
        raise ValueError("The prompt file is empty. Please provide valid input.")

    # ✅ Define content with file input
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=file_prompt),
            ],
        ),
    ]

    # ✅ Response config
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain"
    )

    # ✅ Print streamed output
    print("\n🔍 Gemini Response:\n")
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    generate()
