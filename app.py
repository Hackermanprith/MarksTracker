import streamlit as st
from db import *
from utils import *
from datetime import date,datetime
from streamlit_option_menu import option_menu
from supabase import  *
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout='wide', page_title='📘 JEE/NEET Prep Tracker')

if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'token' not in st.session_state: st.session_state.token = None
if 'email' not in st.session_state: st.session_state.email = ""
with st.sidebar:
    st.markdown("## 📘 Tracker Panel")
    st_autorefresh(interval=60000,limit=5)
    if st.session_state.user_id:
        hour = datetime.now().hour
        greeting = (
            "Good morning" if hour < 12 else
            "Good afternoon" if hour < 17 else
            "Good evening"
        )
        st.markdown(f"**{greeting}, {st.session_state.username}!**", help="Welcome back!")
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = ""
            st.success("✅ Logged out successfully.")
            st.rerun()  # Refresh to update UI
    else:
        st.markdown("*Please log in to access full features.*")

    # Spacing
    st.markdown("---")

    # Navigation Menu (Minimalist)
    section = option_menu(
        menu_title=None,
        options=["Login/Register", "Enter Marks", "All Entries", "Analytics"],
        icons=["box-arrow-in-right", "pencil-square", "table", "bar-chart-line"],
        default_index=1,
        orientation="vertical",
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "#111",
            },
            "icon": {"color": "#c4c4c4", "font-size": "16px"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "0px",
                "padding": "10px 12px",
                "color": "#ffffff",
                "border-radius": "6px"
            },
            "nav-link-selected": {
                "background-color": "#4a4a4a",
                "color": "#ffffff"
            },
        }
    )

# Coaching options
coaching_classes = [
    "FIITJEE", "Allen", "Aakash", "Resonance", "Narayana", "PACE", "Vibrant",
    "Motion", "Sri Chaitanya", "Local Tuition", "Others"
]

# ------------------------- AUTH SECTION -------------------------
if section == "Login/Register":
    st.title("🔐 Login / Register")

    tab1, tab2 = st.tabs(["🔓 Login", "🆕 Register"])

    with tab1:
        st.markdown("#### Welcome Back!")
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type='password', key="login_pass")
        if st.button("Login", type="primary"):
            try:
                user_id = login_user(u, p)
                st.session_state.user_id = user_id
                st.session_state.username = u
                st.success(f"✅ Logged in as {u}")
            except Exception as e:
                st.error(f"❌ Login Failed: {e}")

    with tab2:
        email = st.text_input("username", key="reg_email")
        password = st.text_input("password", type="password", key="reg_pass")

        if st.button("Register"):
            try:
                uid = register_user(email, password)
                st.success("✅ Registration successful! Please login.")
            except Exception as e:
                st.error(f"❌ Registration Failed")

# --------------------- ENTER MARKS SECTION ---------------------
elif section == "Enter Marks":
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to enter data.")
    else:
        st.title("📝 Enter New Test Data")

        with st.form("entry_form"):
            st.markdown("### 🧪 Test Information")
            st.info("**⚠️ Please check the following before submitting:** - All fields must be filled correctly - Use **consistent test names** for better analytics. - Use **consistent organisation names** for trend tracking. - ❌ **Incorrect questions** are auto-calculated from Total - Correct - Left.")

            mode = st.selectbox("Exam Mode", ["JEE"])
            tname = st.text_input("Test Name")
            dt = st.date_input("Date", value=date.today())
            org = st.selectbox("Organisation", coaching_classes)
            rank = st.number_input("🏆 Your Rank (if known)", min_value=1, step=1)

            st.markdown("---")
            st.markdown("### 📚 Subject-wise Input")

            subjects = ['Physics', 'Chemistry', 'Maths'] 
            subject_data = {}

            for subj in subjects:
                st.markdown(f"#### 📘 {subj}")
                cols = st.columns(4)
                total = cols[0].number_input(f"{subj} - Total Questions", min_value=0, key=f"{subj}_total")
                correct = cols[1].number_input(f"{subj} - Correct", min_value=0, key=f"{subj}_correct")
                left = cols[2].number_input(f"{subj} - Left", min_value=0, max_value=max(0, total - correct), key=f"{subj}_left")

                 # ✅ Instant incorrect calculation
                incorrect = max(0, total - correct - left)

                marks_cols = st.columns(2)
                mo = marks_cols[0].number_input(f"{subj} - Marks Obtained", min_value=0, key=f"{subj}_mo")
                tm = marks_cols[1].number_input(f"{subj} - Total Marks", min_value=0, key=f"{subj}_tm")

                time_taken = st.number_input(f"{subj} - Time Taken (mins)", min_value=0, key=f"{subj}_tt")
                subject_data[subj] = (total, correct, left, incorrect, mo, tm, time_taken)
                st.markdown("---")


            if st.form_submit_button("✅ Submit Test"):
                try:
                    tid = add_test(st.session_state.user_id, tname, mode, str(dt), org,rank)
                    for subj, (total, correct, left, incorrect, mo, tm, tt) in subject_data.items():
                        add_subject_data(tid, subj, total, correct, left, incorrect, mo, tm, tt)
                    st.success("🎉 Test submitted successfully!")
                except Exception as e:
                    st.error(f"❌ Failed: {e}")

# ----------------------- ALL ENTRIES --------------------------
elif section == "All Entries":
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to view entries.")
    else:
        st.title("📋 All Recorded Test Entries")
        try:
            rows = get_all_tests(st.session_state.user_id)
            if rows:
                df = make_df(rows)  # Your existing function
                all_entries_page(df)
            else:
                st.info("ℹ️ No entries found. Please add some tests first.")
        except Exception as e:
            st.error(f"Failed to load data: {e}")

# ------------------------- ANALYTICS --------------------------
elif section == "Analytics":
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to view analytics.")
    else:
        rows = get_all_tests(st.session_state.user_id)
        if rows:
            df = make_df(rows)  # Your existing function
            analytics_page(df)  # 👈 Plug in the function here
        else:
            st.info("ℹ️ No data available yet.")
            
with st.sidebar:
     st.markdown("""
        <hr style='margin-top:2em;margin-bottom:0;'>
        <div style='text-align: center; font-size: 0.9em;'>
            Made with ❤️ by <strong>Prithwish Mukherjee</strong><br>
            <a href='https://github.com/Hackermanprith' target='_blank'>GitHub</a> |
            <a href='https://www.instagram.com/human.d3f4ult' target='_blank'>Instagram</a>
        </div>
        """, unsafe_allow_html=True)
