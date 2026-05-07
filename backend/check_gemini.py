import os
import google.generativeai as genai
from dotenv import load_dotenv

def check_gemini():
    # Load .env file
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        print("Testing connection to Gemini...")
        response = model.generate_content("Say 'Gemini is working!' if you can hear me.")
        
        print(f"✅ Success! Response: {response.text.strip()}")
        
    except Exception as e:
        print(f"❌ Failed to connect to Gemini API.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    check_gemini()
