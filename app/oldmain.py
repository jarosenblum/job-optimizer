import streamlit as st

st.set_page_config(page_title="Job Optimizer MVP", layout="wide")

st.title("Job Optimizer — MVP Part 1")

st.markdown("### Step 1: Upload Materials")

resume = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
job_desc = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"])

if st.button("Generate Blueprint"):
    st.success("Blueprint generation placeholder executed.")