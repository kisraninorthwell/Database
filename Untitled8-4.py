#!/usr/bin/env python
# coding: utf-8

# In[3]:


import streamlit as st
import pandas as pd

# Load the cleaned dataset
df = pd.read_csv("Neurogram_Chat_With_GCS_Folder.csv")
df["Date Recorded"] = pd.to_datetime(df["Date Recorded"], errors="coerce")

# Fields to hide from results
hide_cols = ["Id", "Start time", "Completion time", "Email", "Name"]
gcs_col = [col for col in df.columns if "GCS Folder" in col][0]

# UI Header
st.set_page_config(page_title="Neurogram Explorer", layout="centered")
st.title("🧠 Neurogram Explorer")
st.markdown("Let’s guide you to the recordings you’re interested in based on just a few simple questions.")

# Question 1: Mediator
with st.container():
    st.subheader("1️⃣ Select a Mediator")
    mediator = st.selectbox("Which mediator are you exploring?", sorted(df["Mediator"].dropna().unique()))
    filtered = df[df["Mediator"] == mediator]

# Question 2: Responder status
with st.container():
    st.subheader("2️⃣ Do you want only Responder recordings?")
    responder = st.radio("Responder status", ["All", "Yes", "No"])
    if responder != "All":
        filtered = filtered[filtered["Responder"].str.lower() == responder.lower()]

# Question 3: Administration Method
with st.container():
    st.subheader("3️⃣ Choose an Administration Method")
    options = sorted(filtered["Administration Method"].dropna().unique())
    admin_method = st.selectbox("Select method", ["All"] + options)
    if admin_method != "All":
        filtered = filtered[filtered["Administration Method"] == admin_method]

# Question 4: GCS Folder link availability
with st.container():
    st.subheader("4️⃣ Should it have a GCS Folder link?")
    gcs_option = st.radio("GCS Folder Link:", ["All", "Yes", "No"])
    has_link = filtered[gcs_col].notna()
    if gcs_option == "Yes":
        filtered = filtered[has_link]
    elif gcs_option == "No":
        filtered = filtered[~has_link]

# Question 5: Date Range
with st.container():
    st.subheader("5️⃣ Narrow by Date")
    if not filtered["Date Recorded"].dropna().empty:
        start_date, end_date = st.date_input(
            "Pick a date range:",
            [filtered["Date Recorded"].min(), filtered["Date Recorded"].max()]
        )
        filtered = filtered[
            (filtered["Date Recorded"] >= pd.to_datetime(start_date)) &
            (filtered["Date Recorded"] <= pd.to_datetime(end_date))
        ]

# Display Results
st.markdown("---")
st.markdown("### 🔎 Matching Results")
if filtered.empty:
    st.warning("No recordings found. Try changing the filters above.")
else:
    for _, row in filtered.iterrows():
        st.markdown("----")
        for col in filtered.columns:
            if col in hide_cols:
                continue
            val = row[col]
            if pd.notna(val):
                if col == gcs_col:
                    st.markdown(f"**📂 {col.strip()}:** [Open Folder]({val})")
                else:
                    st.markdown(f"**{col.strip()}:** {val}")


# In[ ]:




