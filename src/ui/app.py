import os
import sys
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

import streamlit as st
from src.ui.pages import home, pipeline_setup

with open(os.path.join(PROJECT_ROOT, "config/path.yaml"), "r", encoding="utf-8") as f:
    path_config = yaml.safe_load(f)

with open(os.path.join(PROJECT_ROOT, "config/parameters.yaml"), "r", encoding="utf-8") as f:
    parameter_config = yaml.safe_load(f)

st.set_page_config(
    page_title="Vietnamese Telecom Data",
    layout="wide",
)

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"

if "path_config" not in st.session_state:
    st.session_state["path_config"] = path_config

if "parameter_config" not in st.session_state:
    st.session_state["parameter_config"] = parameter_config

if "project_root" not in st.session_state:
    st.session_state["project_root"] = PROJECT_ROOT

def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.rerun()


if __name__ == "__main__":
    try:
        page = st.session_state["current_page"]

        if page == "home":
            home.app(navigate_to)
        if page == "pipeline_setup":
            pipeline_setup.app(navigate_to)
    except Exception as e:
        print("Streamlit app error:", e)
        st.write("Đang chuyển hướng...")
