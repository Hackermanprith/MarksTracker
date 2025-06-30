import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from db import get_all_tests, update_subject_data, get_test_by_id,update_rank, delete_test
from export_utils import df_to_pdf
import base64

def transform_for_subjectwise_export(df):
    grouped = df.groupby(['Test ID', 'Test Name', 'Organisation', 'Date', 'Rank', 'Exam Mode'])
    rows = []
    for (tid, tname, org, date, rank, exam), group in grouped:
        entry = {
            "Test ID": tid,
            "Test Name": tname,
            "Test Org": org,
            "Date": date,
            "Rank": rank,
            "Exam Mode": exam
        }
        total_time = 0
        total_qs = 0
        total_correct = 0
        for _, row in group.iterrows():
            prefix = row['Subject'][:4]  # Phy, Chem, Math...
            entry[f"{prefix} Total"] = row['Total Qs']
            entry[f"{prefix} Correct"] = row['Correct Qs']
            entry[f"{prefix} Incorrect"] = row['Incorrect Qs']
            entry[f"{prefix} Left"] = row['Left Qs']
            entry[f"{prefix} Marks"] = row['Marks']
            entry[f"{prefix} Time Taken"] = row['Time Taken (min)']
            total_time += row['Time Taken (min)']
            total_qs += row['Total Qs']
            total_correct += row['Correct Qs']

        entry["Total Time"] = total_time
        entry["Total Questions"] = total_qs
        entry["Avg Time per Question"] = round(total_time / total_qs, 2) if total_qs else None
        entry["Overall Accuracy %"] = round((total_correct / total_qs) * 100, 2) if total_qs else None
        rows.append(entry)
    return pd.DataFrame(rows).drop_duplicates()
def all_entries_page(df):
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to view entries.")
        return
    try:
        rows = get_all_tests(st.session_state.user_id)
        if not rows:
            st.info("ℹ️ No data recorded yet.")
            return
               # --- Export Buttons ---
        st.markdown("### 📂 Export Data")
        col_csv, col_pdf = st.columns(2)
        with col_csv:
            transformed = transform_for_subjectwise_export(df)
            csv = transformed.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name='export.csv',
                mime='text/csv'
            )
        grouped = df.groupby("Test ID")
        for test_id, group in grouped:
            with st.expander(f"📘 {group['Test Name'].iloc[0]} - {group['Date'].iloc[0].strftime('%d %b %Y')} ({group['Exam Mode'].iloc[0]}) - {group['Organisation'].iloc[0]}"):
                st.dataframe(group.drop(columns=["Test ID", "Test Name", "Exam Mode", "Organisation", "Date"]).set_index("Subject"))

                # Rank Editor
                with st.form(f"rank_form_{test_id}"):
                    rank_val = group['Rank'].iloc[0] if 'Rank' in group.columns else 0
                    new_rank = st.number_input("🏅 Rank for this test", min_value=0, value=int(rank_val), key=f"rank_{test_id}")
                    if st.form_submit_button("Update Rank"):
                        try:
                            update_rank(test_id, new_rank)
                            st.success("✅ Rank updated.")
                        except Exception as e:
                           st.error(f"❌ Failed to update rank: {e}")

                # Editing
                st.markdown("#### ✏️ Edit Subject Entries")
                for idx, row in group.iterrows():
                    with st.form(f"edit_form_{row['Test ID']}_{row['Subject']}"):
                        st.markdown(f"##### {row['Subject']}")
                        total = st.number_input("Total Questions", min_value=0, value=int(row['Total Qs']), key=f"total_{idx}")
                        correct = st.number_input("Correct Questions", min_value=0, max_value=total, value=int(row['Correct Qs']), key=f"correct_{idx}")
                        left = st.number_input("Left Questions", min_value=0, max_value=total - correct, value=int(row['Left Qs']), key=f"left_{idx}")
                        incorrect = total - correct - left
                        st.write(f"**Incorrect: {incorrect}**")
                        marks = st.number_input("Marks Obtained", min_value=0.0, value=float(row['Marks']), key=f"marks_{idx}")
                        total_marks = st.number_input("Total Marks", min_value=1.0, value=float(row['Total Marks']), key=f"tm_{idx}")
                        time = st.number_input("Time Taken (min)", min_value=0.0, value=float(row['Time Taken (min)']), key=f"time_{idx}")

                        if st.form_submit_button("Save Changes"):
                            try:
                                update_subject_data(row['Test ID'], row['Subject'], total, correct, left, incorrect, marks, total_marks, time)
                                st.success("✅ Updated successfully. Please refresh to view changes.")
                            except Exception as e:
                                st.error(f"❌ Update failed: {e}")

                # Deletion Option
                if st.button("🗑 Delete Entire Test", key=f"delete_{test_id}"):
                    try:
                        delete_test(test_id)
                        st.success("🗑 Test deleted. Refresh to update view.")
                    except Exception as e:
                        st.error(f"❌ Failed to delete test: {e}")

    except Exception as e:
        st.error(f"Failed to load data: {e}")


def analytics_page (df):
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to view entries.")
        return

    st.title("📊 Analytics Dashboard")

    try:
        rows = get_all_tests(st.session_state.user_id)
        if not rows:
            st.info("ℹ️ No data recorded yet.")
            return

        filt_col1, filt_col2, filt_col3 = st.columns([5, 1, 2])
        with filt_col1:
            st.markdown("### 📌 Summary Stats")
        with filt_col2:
            if st.button("🔍 Filters"):
                st.session_state.show_filters = not st.session_state.show_filters

        if st.session_state.show_filters:
            with st.expander("Filter Options", expanded=True):
                test_names = df['Test Name'].unique().tolist()
                selected_test = st.selectbox("Select Test for Analytics (or leave empty for all)", ["All Tests"] + test_names)

                organisations = df['Organisation'].dropna().unique().tolist()
                selected_org = st.selectbox("Select Organisation (optional)", ["All Organisations"] + organisations)

                date_range = st.date_input("Filter by Date Range", [], help="Optional - pick a range to filter tests")

                if selected_test != "All Tests":
                    df = df[df['Test Name'] == selected_test]

                if selected_org != "All Organisations":
                    df = df[df['Organisation'] == selected_org]

                if len(date_range) == 2:
                    df = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]

        if df.empty:
            st.warning("No data matching your filters.")
            return

        col1, col2, radar_col = st.columns([1, 1, 1])
        with col1:
            st.metric("Total Questions", int(df['Total Qs'].sum()))
            st.metric("Total Correct", int(df['Correct Qs'].sum()))
            st.metric("Average Accuracy %", f"{round((df['Correct Qs'].sum()/df['Total Qs'].sum())*100, 2)}%")
        with col2:
            st.metric("Average Marks %", f"{round((df['Marks'].sum()/df['Total Marks'].sum())*100, 2)}%")
            st.metric("Average Time per Question", f"{round(df['Time per Question'].mean(), 2)} min")
            if 'Rank' in df.columns and df['Rank'].notna().any():
                st.metric("Average Rank", round(df['Rank'].mean(), 2))
        with radar_col:
            st.plotly_chart(plot_radar_chart(df), use_container_width=True)
       
        st.markdown("---")
        st.subheader("📊 Performance Charts")
        chart_cols = st.columns(2)
        with chart_cols[0]: unique_chart(plot_overall_trend(df))
        with chart_cols[1]: unique_chart(plot_accuracy(df))
        with chart_cols[0]: unique_chart(plot_time_trend(df))
        with chart_cols[1]: unique_chart(plot_speed_chart(df))
        with chart_cols[0]: unique_chart(plot_time_per_question(df))
        with chart_cols[1]: unique_chart(plot_rank_trend(df))
        with st.expander("📡 Subject Radar Chart"):
            unique_chart(plot_radar_chart(df))


        st.markdown("""
        <hr style='margin-top:2em;margin-bottom:0;'>
        <div style='text-align: center; font-size: 0.9em;'>
            Made with ❤️ by <strong>Prithwish Mukherjee</strong><br>
            <a href='https://github.com/yourgithub' target='_blank'>GitHub</a> |
            <a href='https://instagram.com/yourinsta' target='_blank'>Instagram</a>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Failed to load data: {e}")


def make_df_Stats(rows):
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])

    # ✅ Clean, snake_case column names (for internal use)
    df = df.rename(columns={
        'test_id': 'test_id',
        'test_name': 'test_name',
        'exam_mode': 'exam_mode',
        'organisation': 'organisation',
        'subject': 'subject',
        'total_qs': 'total_qs',
        'correct_qs': 'correct_qs',
        'left_qs': 'left_qs',
        'incorrect_qs': 'incorrect_qs',
        'marks_obtained': 'marks_obtained',
        'total_marks': 'total_marks',
        'time_taken': 'time_taken',
        'date': 'date'
    })

    # ➕ Derived metrics for plotting
    df["accuracy_pct"] = (df["correct_qs"] / df["total_qs"].replace(0, 1)) * 100
    df["score_pct"] = (df["marks_obtained"] / df["total_marks"].replace(0, 1)) * 100
    df["marks_per_min"] = df["marks_obtained"] / df["time_taken"].replace(0, 1)
    df["time_per_question"] = df["time_taken"] / df["total_qs"].replace(0, 1)
    df["test_label"] = df["test_name"] + " - " + df["date"].dt.strftime("%d-%b-%Y")

    return df.sort_values(by="date", ascending=False)

def make_df(rows):
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={
        'test_id': 'Test ID',
        'test_name': 'Test Name',
        'exam_mode': 'Exam Mode',
        'organisation': 'Organisation',
        'subject': 'Subject',
        'total_qs': 'Total Qs',
        'correct_qs': 'Correct Qs',
        'left_qs': 'Left Qs',
        'incorrect_qs': 'Incorrect Qs',
        'marks_obtained': 'Marks',
        'total_marks': 'Total Marks',
        'time_taken': 'Time Taken (min)',
        'date': 'Date',
        'rank': 'Rank'
    })
    df["Accuracy %"] = (df["Correct Qs"] / df["Total Qs"]) * 100
    df["Score %"] = (df["Marks"] / df["Total Marks"]) * 100
    df["Marks per Min"] = df["Marks"] / df["Time Taken (min)"].replace(0, 1)
    df["Time per Question"] = df["Time Taken (min)"] / df["Total Qs"].replace(0, 1)
    df["Test Label"] = df["Test Name"] + " - " + df["Date"].dt.strftime("%d-%b-%Y")
    return df.sort_values(by="Date", ascending=False)


chart_counter = 0  # Unique counter for plotly charts

def unique_chart(fig):
    global chart_counter
    chart_counter += 1
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_counter}")

def plot_overall_trend(df):
    df_grouped = df.groupby("Date").agg({"Marks": "sum", "Total Marks": "sum"}).reset_index()
    df_grouped["Score %"] = (df_grouped["Marks"] / df_grouped["Total Marks"]) * 100
    return px.line(df_grouped, x="Date", y="Score %", markers=True, title="📈 Score % Trend Over Time")

def plot_accuracy(df):
    avg = df.groupby("Subject").agg({"Accuracy %": "mean"}).reset_index()
    return px.bar(avg, x="Subject", y="Accuracy %", color="Subject", title="📊 Average Accuracy per Subject")

def plot_time_trend(df):
    df_time = df.groupby("Date").agg({"Time Taken (min)": "sum"}).reset_index()
    return px.line(df_time, x="Date", y="Time Taken (min)", markers=True, title="⏱️ Total Time Taken per Test Day")

def plot_speed_chart(df):
    df_speed = df.groupby("Date").agg({"Marks": "sum", "Time Taken (min)": "sum"}).reset_index()
    df_speed["Marks per Min"] = df_speed["Marks"] / df_speed["Time Taken (min)"].replace(0, 1)
    return px.line(df_speed, x="Date", y="Marks per Min", markers=True, title="⚡ Speed (Marks per Minute)")

def plot_time_per_question(df):
    df_qtime = df.groupby("Date").agg({"Time Taken (min)": "sum", "Total Qs": "sum"}).reset_index()
    df_qtime["Time per Question"] = df_qtime["Time Taken (min)"] / df_qtime["Total Qs"].replace(0, 1)
    return px.line(df_qtime, x="Date", y="Time per Question", markers=True, title="🧪 Time per Question Over Time")

def plot_radar_chart(df):
    radar_df = df.groupby("Subject").agg({"Marks": "sum", "Total Marks": "sum"}).reset_index()
    radar_df["Score %"] = (radar_df["Marks"] / radar_df["Total Marks"]) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=radar_df["Score %"], theta=radar_df["Subject"], fill="toself", name="Performance"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def plot_rank_trend(df):
    rank_df = df.dropna(subset=["Rank"]).groupby("Date")["Rank"].mean().reset_index()
    return px.line(rank_df, x="Date", y="Rank", markers=True, title="🏆 Average Rank Trend")