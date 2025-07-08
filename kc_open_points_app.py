import streamlit as st
import pandas as pd
import os
from datetime import date

EXCEL_FILE = "KC Open Points.xlsx"
CSV_FILE = "kc_open_points.csv"

REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        df.rename(columns={"Resolution Date": "Target Resolution Date"}, inplace=True)
        df["Closing Comment"] = ""
        df["Closed By"] = ""
        df["Actual Resolution Date"] = ""
        df.to_csv(CSV_FILE, index=False)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def safe_to_date(val):
    if pd.isna(val) or val == "":
        return date.today()
    if isinstance(val, date):
        return val
    try:
        dt = pd.to_datetime(val)
        return dt.date()
    except Exception:
        return date.today()

# Page functions

def home():
    st.title("📘 K-C Issue Tracker")
    st.write("Welcome! Use the sidebar to navigate.")

def submit_request():
    st.header("📝 Submit Your Request")

    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_resolution_date = st.date_input("Target Resolution Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            new_entry = pd.DataFrame([{
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Target Resolution Date": target_resolution_date,
                "Closing Comment": "",
                "Closed By": "",
                "Actual Resolution Date": ""
            }])
            new_entry.to_csv(CSV_FILE, mode='a', header=False, index=False)
            st.success("✅ Entry submitted successfully!")

def open_topics():
    st.header("📌 Open Topics")
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if open_df.empty:
        st.info("No open topics available.")
        return

    st.markdown("### 🗂️ Topics Table")

    clicked_close = None
    clicked_edit = None

    for i, row in open_df.iterrows():
        with st.container():
            style = "background-color: #e6f2ff; border: 1px solid #cce6ff; padding: 10px; margin-bottom: 5px;"
            st.markdown(f"<div style='{style}'>", unsafe_allow_html=True)

            cols = st.columns([3, 2, 2, 3, 1, 1])
            cols[0].markdown(row["Topic"])
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(row["Target Resolution Date"])

            if cols[4].button("Close", key=f"close_btn_{i}"):
                clicked_close = i
            if cols[5].button("Edit", key=f"edit_btn_{i}"):
                clicked_edit = i

            if "close_row" in st.session_state and st.session_state.close_row == i:
                with st.form(f"close_form_{i}"):
                    st.markdown("**🔒 Provide Closing Details**")
                    comment = st.text_area("Closing Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                    action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_action_{i}")
                    submitted = st.form_submit_button("Submit")
                    if submitted:
                        if action == "Confirm Close":
                            df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                            df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                            df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                            df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                            save_data(df)
                            st.success(f"✅ '{row['Topic']}' marked as Closed.")
                        st.session_state.close_row = None

            if "edit_row" in st.session_state and st.session_state.edit_row == i:
                with st.form(f"edit_form_{i}"):
                    st.markdown("**✏️ Edit Topic Details**")
                    new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
                    new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
                    new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
                    new_date = st.date_input(
                        "Target Resolution Date",
                        value=safe_to_date(row["Target Resolution Date"]),
                        key=f"edit_date_{i}"
                    )
                    action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_action_{i}")
                    submitted = st.form_submit_button("Submit")
                    if submitted:
                        if action == "Save Changes":
                            df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                            df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                            df.loc[df["Topic"] == new_topic, "Status"] = new_status
                            df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                            save_data(df)
                            st.success(f"✅ '{new_topic}' updated successfully.")
                        st.session_state.edit_row = None

            st.markdown("</div>", unsafe_allow_html=True)

    if clicked_close is not None:
        st.session_state.close_row = clicked_close
        st.session_state.edit_row = None

    if clicked_edit is not None:
        st.session_state.edit_row = clicked_edit
        st.session_state.close_row = None

    csv = open_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Open Topics as CSV",
        data=csv,
        file_name='open_topics.csv',
        mime='text/csv'
    )

def closed_topics():
    st.header("✅ Closed Topics")
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]

    if closed_df.empty:
        st.info("No closed topics available.")
        return

    st.dataframe(
        closed_df[[
            "Topic", "Owner", "Target Resolution Date",
            "Actual Resolution Date", "Closed By", "Closing Comment"
        ]],
        use_container_width=True,
    )

    csv = closed_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Closed Topics as CSV",
        data=csv,
        file_name='closed_topics.csv',
        mime='text/csv'
    )


# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation",
    ("Home", "Submit Request", "Open Topics", "Closed Topics")
)

st.set_page_config(page_title="K-C Tracker", layout="wide")

if page == "Home":
    home()
elif page == "Submit Request":
    submit_request()
elif page == "Open Topics":
    open_topics()
elif page == "Closed Topics":
    closed_topics()
