from supabase import create_client, Client
import os

# Set environment variables in your .streamlit/secrets.toml or deployment dashboard
SUPABASE_URL = str(os.environ.get("SUPABASE_URL"))
SUPABASE_KEY = str(os.environ.get("SUPABASE_KEY"))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# ----------------- Auth System (Custom) -----------------

def login_user(username, password):
    try:
        print(f"Trying to login with {username} / {password}")
        res = supabase.table("users") \
                      .select("id, username, password") \
                      .eq("username", username) \
                      .eq("password", password) \
                      .execute()
        print(res)

        if not res.data or len(res.data) == 0:
            raise Exception("Invalid credentials.")
        return res.data[0]["id"]

    except Exception as e:
        raise Exception(f"Login failed: {e}")

def register_user(username, password):
    try:
        res = supabase.table("users") \
                      .insert({"username": username, "password": password}) \
                      .execute()

        print("Registration response:", res)

        if not res.data:
            raise Exception("User registration failed.")
        return res.data[0]["id"]

    except Exception as e:
        raise Exception(f"Registration failed: {e}")


# ------------------ Test Management ------------------

def add_test(user_id, name, mode, date, organisation,rank):
    try:
        res = supabase.table("tests") \
                      .insert({
                          "user_id": user_id,
                          "test_name": name,
                          "exam_mode": mode,
                          "date": date,
                          "organisation": organisation,
                          "rank":rank
                      }) \
                      .execute()

        return res.data[0]["id"]

    except Exception as e:
        raise Exception(f"Add test failed: {e}")

def add_subject_data(test_id, subject, total, correct, left, incorrect, marks, total_marks, time_taken):
    try:
        res = supabase.table("test_subjects") \
                      .insert({
                          "test_id": test_id,
                          "subject": subject,
                          "total_qs": total,
                          "correct_qs": correct,
                          "left_qs": left,
                          "incorrect_qs": incorrect,
                          "marks_obtained": marks,
                          "total_marks": total_marks,
                          "time_taken": time_taken
                      }) \
                      .execute()

    except Exception as e:
        raise Exception(f"Add subject data failed: {e}")

# ------------------ Fetch Data for Analytics ------------------

def get_all_tests(user_id):
    try:
        res = supabase.rpc("get_user_tests", {"uid": user_id}).execute()
        return res.data

    except Exception as e:
        raise Exception(f"Data fetch failed: {e}")

def get_test_by_id(test_id):
    response = supabase.rpc("get_test_by_id", {"tid": test_id}).execute()
    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
    return response.data

def update_subject_data(test_id, subject, total, correct, left, incorrect, marks, total_marks, time_taken):
    response = supabase.table("test_subjects").update({
        "total_qs": total,
        "correct_qs": correct,
        "left_qs": left,
        "incorrect_qs": incorrect,
        "marks_obtained": marks,
        "total_marks": total_marks,
        "time_taken": time_taken
    }).eq("test_id", test_id).eq("subject", subject).execute()

    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)

def delete_test(test_id):
    # First delete subject data (foreign key constraint)
    resp1 = supabase.table("test_subjects").delete().eq("test_id", test_id).execute()
    if hasattr(resp1, 'error') and resp1.error:
        raise Exception(resp1.error.message)

    # Then delete the test entry
    resp2 = supabase.table("tests").delete().eq("id", test_id).execute()
    if hasattr(resp2, 'error') and resp2.error:
        raise Exception(resp2.error.message)

def update_rank(test_id, rank):
    response = supabase.table("tests").update({
        "rank": rank
    }).eq("id", test_id).execute()

    if hasattr(response, 'error') and response.error:
        raise Exception(response.error.message)
