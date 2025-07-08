import streamlit as st
import pandas as pd

CSV_FILE = "kc_open_points.csv"

@st.cache_data
def load_data():
    return pd.read_csv(CSV_FILE)

def save_entry(entry):
    df = pd.DataFrame([entry])
    df.to_csv(CSV_FILE, mode='a', header=False, index=False)

st.set_page_config(page_title="KC Open Points Tracker", layout="wide")
page = st.sidebar.selectbox("Select Page", ["Data Entry Form", "View Data"])

if page == "Data Entry Form":
    st.title("📋 KC Open Points - Data Entry")

    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        resolution_date = st.date_input("Resolution Date", format="YYYY-MM-DD")

        submitted = st.form_submit_button("Submit")

        if submitted:
            new_entry = {
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Resolution Date": resolution_date
            }
            save_entry(new_entry)
            st.success("✅ Entry submitted successfully!")

elif page == "View Data":
    st.title("📊 KC Open Points - View Data")
    df = load_data()
    st.dataframe(df, use_container_width=True)
