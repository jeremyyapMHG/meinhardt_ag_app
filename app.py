import streamlit as st
from auth import load_auth
from db import init_db

init_db()

st.set_page_config(page_title="Meinhardt AG App", layout="wide")

# Inject custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load auth and login
authenticator = load_auth()
name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome, {name}")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Upload AG",
        "DevCo Input",
        "Add/Delete Points",
        "Merged AG + Export",
        "Submission History",
        "Analyze AG (OLD)",
        "Analyze AG (NEW)",
        "Main AG Processor", 
        "Load Versions",
        "Audit Log"
    ])

    # Route pages
    if page == "Upload AG":
        import ag_upload; ag_upload.render()
    elif page == "DevCo Input":
        import devco_entry; devco_entry.render(username)
    elif page == "Add/Delete Points":
        import ag_admin_tools; ag_admin_tools.render()
    elif page == "Merged AG + Export":
        import ag_merge_export; ag_merge_export.render()
    elif page == "Submission History":
        import history_view; history_view.render()
    elif page == "Load Versions":
        import load_versions
        load_versions.render()
    elif page == "Audit Log":
        import audit_log
        audit_log.render()
    elif page == "Main AG Processor":
        import process_ag
        process_ag.render(username)
    elif page == "Analyze AG (OLD)":
        import analyze_ag
        analyze_ag.render(username)
    elif page == "Analyze AG (NEW)":
        import analyze_ag_rebuilt
        analyze_ag_rebuilt.render(username)

else:
    st.warning("Please log in to continue.")