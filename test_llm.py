from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()
try:
    client = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.environ["GEMINI_API_KEY"])
    print(client.invoke("Hello").content)
except Exception as e:
    print("Error 1.5-flash:", e)
