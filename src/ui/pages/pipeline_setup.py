import streamlit as st
import os
import threading
from ruamel.yaml import YAML

from src.utils.file_helpers import create_folder, delete_path, save_uploaded_files
from src.utils.logger import *

def get_raw_dir():
    if "project_root" in st.session_state:
        return os.path.join(st.session_state["project_root"], "data", "raw")
    return os.path.join(os.getcwd(), "data", "raw")

def start_pipeline(selected):
    st.session_state["processing"] = True
    try:
        from src.preprocess.pipeline import preprocess_file
        from src.llm.pipeline import create_quest_from_file
        from src.postprocess.pipeline import postprocess_file
        log_info("========== START PIPELINE==========")
        try:
            for file_path in selected:
                log_info(f"--- Processing file: {file_path} ---")
                log_info("--- Preprocessing ---")
                preprocess_path = preprocess_file(file_path)
                log_info("--- Preprocessing Complete ---\n")
                log_info("--- Generatate Data ---")
                generate_path, _ = create_quest_from_file(preprocess_path)
                log_info("--- Data Generation Complete ---\n")
                log_info("--- Postprocessing ---")
                postprocess_file(generate_path)
                log_info("--- Postprocessing Complete ---\n")
        except Exception as e:
            log_error("Pipeline error:", e)
        finally:
            log_info("========== PIPELINE ENDED SUCCESSFULLY ==========")
    finally:
        st.session_state["processing"] = False


def render_tree(dir_path):
    if not os.path.exists(dir_path):
        return

    try:
        items = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x))
    except PermissionError:
        st.error("Permission denied")
        return

    for name in items:
        full_path = os.path.join(dir_path, name)
        key = full_path
        is_dir = os.path.isdir(full_path)

        c_main, c_menu = st.columns([0.9, 0.1])

        with c_main:
            if is_dir:
                with st.expander(f"📂 {name}", expanded=False):
                    render_tree(full_path)
            else:
                fsize = os.stat(full_path).st_size / 1024
                icon = "📜" if name.endswith(".json") else "📄"
                st.checkbox(f"{icon} {name} ({fsize:.1f} KB)", key=f"sel_{key}")

        with c_menu:
            with st.popover("⋮"):
                st.markdown(f"**Target:** `{name}`")
                
                if is_dir:
                    tab1, tab2 = st.tabs(["Add", "Upload"])
                    with tab1:
                        new_f = st.text_input("Name", key=f"nf_{key}")
                        if st.button("Create", key=f"btn_nf_{key}", use_container_width=True):
                            if new_f:
                                ok, msg = create_folder(os.path.join(full_path, new_f))
                                if ok: st.rerun()
                                else: st.error(msg)
                    with tab2:
                        up_files = st.file_uploader("Files", key=f"up_{key}", accept_multiple_files=True)
                        if up_files and st.button("Save", key=f"btn_up_{key}", use_container_width=True):
                            cnt = save_uploaded_files(up_files, full_path)
                            if cnt: st.rerun()
                    st.divider()

                if st.button("Delete", key=f"del_{key}", type="primary", use_container_width=True):
                    ok, msg = delete_path(full_path)
                    if ok: st.rerun()
                    else: st.error(msg)


def app(router_func=None):
    c, _ = st.columns([0.1, 0.9])
    with c:
        if st.button("Back to Home", type="primary", use_container_width=True):
            if router_func: router_func("home")
            return

    st.title(" Pipeline Manager")

    RAW_DIR = get_raw_dir()
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    c_tree, c_run = st.columns([0.75, 0.25], gap="medium")

    with c_tree:
        c_head, c_act = st.columns([0.89, 0.11])
        with c_head:
            st.subheader("📂 Raw Data")
        with c_act:
            with st.popover("Create Folder"):
                root_name = st.text_input("Folder Name")
                if st.button("Create", use_container_width=True):
                    create_folder(os.path.join(RAW_DIR, root_name))
                    st.rerun()


        st.markdown("---")
        with st.container(height=600, border=True):
            if not os.listdir(RAW_DIR):
                st.info("Directory empty.")
            else:
                render_tree(RAW_DIR)

    with c_run:
        st.subheader("Trigger")
        
        selected = []
        for k, v in st.session_state.items():
            if isinstance(k, str) and k.startswith("sel_") and v is True:
                path = k.replace("sel_", "")
                if os.path.exists(path): selected.append(path)

        with st.container(height=300, border=True):
            st.markdown(f"**Selected: {len(selected)}**")
            if selected:
                for f in selected:
                    st.caption(f"• {os.path.basename(f)}")
            else:
                st.caption("No files selected.")

        st.write("")
        type_dict = {
            "Multi-choices question": "mcq",
            "Question and Answer": "qna",
        }
        data_type = st.selectbox("Data Type", ["Multi-choices question", "Question and Answer"], index=0)
        
        if st.button("START PIPELINE", type="primary", use_container_width=True, disabled=not selected):
            st.session_state["pipeline_running"] = True
            st.session_state["selected_files"] = selected
            cfg = os.path.join(st.session_state.get("project_root", ""), "config", "parameters.yaml")
            yaml = YAML()
            yaml.preserve_quotes = True

            with open(cfg, "r", encoding="utf-8") as f:
                params = yaml.load(f)

            params["data_type"] = type_dict[data_type]

            with open(cfg, "w", encoding="utf-8") as f:
                yaml.dump(params, f)
            
            t = threading.Thread(target=start_pipeline, args=(selected,))
            t.start()

            if router_func:
                router_func("home")