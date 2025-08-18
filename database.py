from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL ve KEY .env dosyasında tanımlı olmalıdır!")

supabase = create_client(url, key)

def save_analysis(
    user_id: str,
    capture_time: str,
    activity: str,
    objects: list,
    environment: str,
    confidence_scores: dict,
    needs_clarification: bool
):
    try:
        supabase.table("analyses").insert({
            "user_id": user_id,
            "capture_time": capture_time,
            "activity": activity,
            "objects": objects,
            "environment": environment,
            "confidence_scores": confidence_scores,
            "needs_clarification": needs_clarification
        }).execute()
    except Exception as e:
        print(f"Veritabanı kayıt hatası: {e}")
        raise


def get_daily_analyses(user_id: str, date_str: str) -> list[dict]:
    date_prefix = date_str.split(" ")[0]

    res = supabase.rpc(
        "get_daily_analyses",
        {"p_user_id": user_id, "p_date": date_prefix}
    ).execute()

    return res.data


def mark_analyses_deleted(user_id: str, date: str):
    date_prefix = date.split(" ")[0]

    supabase.rpc(
        "mark_analyses_deleted",
        {"p_user_id": user_id, "p_date": date_prefix}
    ).execute()

def save_daily_summary(user_id: str, date: str, summary: str):
    supabase.table("daily_summaries").insert({
        "user_id": user_id,
        "date": date,
        "summary": summary
    }).execute()
