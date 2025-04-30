from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLIC_KEY")  # Make sure this is the public key, not service role
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test connection and role
try:
    res = supabase.rpc("whoami").execute()
    print("🔍 Current role:", res)
except Exception as e:
    print("❌ Error connecting to Supabase:", str(e))
    exit(1)

def store_assignment(title, instructions, answer, feedback):
    try:
        data = {
            "title": title,
            "instructions": instructions,
            "answer": answer,
            "feedback": feedback
        }
        print(f'trying to store assignment {data}')
        response = supabase.table("assignments").insert(data).execute()
        print("✅ Data stored:", response)
    except Exception as e:
        print("❌ Error storing assignment:", str(e))
        raise

# Test the function
