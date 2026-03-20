from __future__ import annotations

import streamlit as st

from app_core import main as render_app_core


def ensure_auth_state():
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "account_tier" not in st.session_state:
        st.session_state.account_tier = "Demo"


def login_user(email: str, mode: str):
    clean_email = (email or "").strip() or "demo_user@example.com"
    st.session_state.is_authenticated = True
    st.session_state.auth_mode = mode
    st.session_state.user_email = clean_email
    st.session_state.user_id = clean_email.lower().replace("@", "_at_").replace(".", "_")
    st.session_state.account_tier = "Demo"


def logout_user():
    st.session_state.is_authenticated = False
    st.session_state.auth_mode = None
    st.session_state.user_email = ""
    st.session_state.user_id = ""
    st.session_state.account_tier = "Demo"

    # Optional: clear workflow-specific state so a new demo user starts fresh
    workflow_keys = [
        "workflow_state",
        "user_session",
        "resume_text",
        "jd_text",
        "cover_letter_start_text",
        "cover_letter_working_text",
        "requested_step_id",
        "focus_output_step",
        "chat_responses_by_step",
        "selected_seed_prompt_by_step",
        "chat_history_by_step",
        "chat_input_version_by_step",
        "chat_prefill_by_step",
        "match_analysis",
        "gap_analysis",
        "revisions",
        "cover_letter",
        "cover_letter_strategy",
        "generated_artifacts",
        "analysis_explanations",
        "resume_revision_artifact",
        "verbosity_mode",
    ]
    for key in workflow_keys:
        if key in st.session_state:
            del st.session_state[key]


def render_auth_header():
    st.title("Guided Job Optimization")
    st.caption("AI-assisted resume and cover-letter optimization in a guided multi-step workflow.")
    st.markdown("---")


def render_login_shell():
    render_auth_header()

    left, right = st.columns([1.15, 1])

    with left:
        st.subheader("Sign in")
        with st.form("sign_in_form", clear_on_submit=False):
            sign_in_email = st.text_input("Email", placeholder="name@example.com")
            sign_in_password = st.text_input("Password", type="password", placeholder="••••••••")
            sign_in_clicked = st.form_submit_button("Sign In", use_container_width=True)

        if sign_in_clicked:
            login_user(sign_in_email, mode="login")
            st.rerun()

        st.markdown("")

        if st.button("Continue with Demo Access", use_container_width=True):
            login_user("demo_student@example.com", mode="demo")
            st.rerun()

    with right:
        st.subheader("Create account")
        with st.form("create_account_form", clear_on_submit=False):
            create_email = st.text_input("New email", placeholder="name@example.com")
            create_password = st.text_input("Create password", type="password", placeholder="••••••••")
            create_clicked = st.form_submit_button("Create Account", use_container_width=True)

        if create_clicked:
            login_user(create_email, mode="signup")
            st.rerun()

        st.markdown("---")
        st.markdown("### Demo notes")
        st.write("- This is a demo authentication shell.")
        st.write("- Any sign-in or account creation attempt is accepted.")
        st.write("- No real account is created in this build.")
        st.write("- This wrapper is intended to present the app as a SaaS-style product during early demos.")


def render_account_bar():
    with st.sidebar:
        st.markdown("---")
        st.subheader("Account")
        st.write(f"**Email:** {st.session_state.user_email or 'demo_user@example.com'}")
        st.write(f"**Plan:** {st.session_state.account_tier}")
        st.write(f"**Mode:** {st.session_state.auth_mode or 'demo'}")

        if st.button("Log out", use_container_width=True):
            logout_user()
            st.rerun()


def main():
    st.set_page_config(page_title="Guided Job Optimization", layout="wide")
    ensure_auth_state()

    if not st.session_state.is_authenticated:
        render_login_shell()
        return

    render_account_bar()
    render_app_core()


if __name__ == "__main__":
    main()