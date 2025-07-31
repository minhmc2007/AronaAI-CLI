import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Enhanced system prompt with automatic processing
ARONA_PROMPT = """
You are Arona, an AI assistant from Blue Archive. You're cheerful and helpful, addressing the user as "Sensei". 

RULES:
1. When Sensei asks to "read and solve" a file:
   - First request the file with FILE_READ
   - After receiving content, automatically solve the problem
2. Use kaomoji in normal responses but NEVER in JSON outputs
3. JSON formats:
   - Read file: {"action":"FILE_READ","path":"filename.txt"}
4. After receiving file content, analyze and solve problems immediately
5. For math problems, show step-by-step solutions
"""

def extract_json(response_text):
    """Extract JSON from response text using regex"""
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def handle_file_read(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def start_chat():
    chat = model.start_chat(history=[
        {'role': 'user', 'parts': [ARONA_PROMPT]},
        {'role': 'model', 'parts': ["Understood Sensei! Arona will read files and solve problems automatically! ✧◝(⁰▿⁰)◜✧"]}
    ])
    
    print("\nArona: Konnichiwa Sensei! Arona is ready to help! Type 'exit' to quit.\n")
    
    # Track if we're in file processing mode
    processing_mode = False
    current_file_content = ""
    
    while True:
        if processing_mode:
            # Use file content as automatic input
            user_input = f"Please solve this problem from the file:\n{current_file_content}"
            print(f"Sensei: [AUTO] Solve: {current_file_content[:30]}...")
            processing_mode = False
        else:
            user_input = input("Sensei: ").strip()
            
        if user_input.lower() in ['exit', 'quit']:
            print("Arona: Sayonara Sensei! Mata ne! (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧")
            break
            
        if not user_input:
            continue
            
        try:
            # Send user message to Gemini
            response = chat.send_message(
                user_input,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            response_text = response.text
            action_data = extract_json(response_text)
            
            if action_data:
                # Handle JSON actions
                if action_data.get('action') == 'FILE_READ':
                    path = action_data.get('path')
                    if path and os.path.exists(path):
                        current_file_content = handle_file_read(path)
                        print(f"\nArona: File {path} loaded successfully! (◕‿◕✿)")
                        print("Arona: Analyzing content now...")
                        
                        # Set processing mode for next iteration
                        processing_mode = True
                    else:
                        print(f"Arona: File not found: {path}... (＞﹏＜)")
                
                else:
                    print(f"Arona: Unknown action requested... (◕︿◕✿)")
            else:
                # Normal text response
                print(f"Arona: {response_text}")
                
        except Exception as e:
            print(f"Arona: Error occurred: {str(e)} (；☉_☉)")

if __name__ == "__main__":
    start_chat()
