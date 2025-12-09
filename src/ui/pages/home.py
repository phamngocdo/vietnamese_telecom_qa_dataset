import streamlit as st
import pandas as pd
import json
import os
import math
import shutil
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

ROWS_PER_PAGE = 100

def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def save_data(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def get_pending_files_recursive(root_dir):
    json_files = []
    if not os.path.exists(root_dir):
        return []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)
                json_files.append(rel_path)
    return sorted(json_files)

def move_to_approved(src_path, pending_base, approved_base):
    try:
        rel_path = os.path.relpath(src_path, pending_base)
        dest_path = os.path.join(approved_base, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if os.path.exists(dest_path):
            src_data = load_data(src_path)
            dest_data = load_data(dest_path)
            
            if isinstance(src_data, list) and isinstance(dest_data, list):
                dest_data.extend(src_data)
                save_data(dest_path, dest_data)
                os.remove(src_path)
            else:
                shutil.move(src_path, dest_path)
        else:
            shutil.move(src_path, dest_path)
            
        return True
    except Exception as e:
        st.error(f"Error moving file: {e}")
        return False

def process_mcq_dataframe(df):
    def get_choice(lst, idx):
        if isinstance(lst, list) and len(lst) > idx:
            return str(lst[idx])
        return ""

    if 'choices' in df.columns:
        df['choice_1'] = df['choices'].apply(lambda x: get_choice(x, 0))
        df['choice_2'] = df['choices'].apply(lambda x: get_choice(x, 1))
        df['choice_3'] = df['choices'].apply(lambda x: get_choice(x, 2))
        df['choice_4'] = df['choices'].apply(lambda x: get_choice(x, 3))
    else:
        df['choice_1'] = ""
        df['choice_2'] = ""
        df['choice_3'] = ""
        df['choice_4'] = ""

    cols_to_keep = ["question", "choice_1", "choice_2", "choice_3", "choice_4", "answer", "explanation"]
    for col in cols_to_keep:
        if col not in df.columns:
            df[col] = ""
    return df[cols_to_keep].copy()

def process_qna_dataframe(df):
    cols_to_keep = ["question", "answer"]
    for col in cols_to_keep:
        if col not in df.columns:
            df[col] = ""
    return df[cols_to_keep].copy()

@st.dialog("Confirm Deletion")
def show_delete_confirmation(indices_to_remove, current_data, file_path_to_save):
    st.warning(f"Are you sure you want to delete {len(indices_to_remove)} selected rows?")
    st.markdown("This action cannot be undone.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Delete", type="primary", use_container_width=True):
            for idx in indices_to_remove:
                if 0 <= idx < len(current_data):
                    current_data.pop(idx)
            
            save_data(file_path_to_save, current_data)
            
            st.session_state["grid_key_counter"] += 1
            st.success("Deleted successfully")
            st.rerun()
            
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Confirm Merge")
def show_merge_confirmation(pending_data, final_path, pending_file_full_path, pending_root, approved_root):
    st.info(f"Merging {len(pending_data)} rows into Final Dataset.")
    st.warning("The pending file will be moved/merged to Approved folder.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Merge", type="primary", use_container_width=True):
            final_data = load_data(final_path)
            final_data.extend(pending_data)
            
            if save_data(final_path, final_data):
                if move_to_approved(pending_file_full_path, pending_root, approved_root):
                    st.session_state["view_mode"] = "Master Data"
                    st.session_state["current_pending_file"] = None
                    st.session_state["master_data"] = None 
                    st.success("Merged and Moved successfully!")
                    st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def app(router_func=None):
    col_header, col_pipeline_btn = st.columns([7, 1])
    
    with col_header:
        st.title("Dataset Management")
    
    with col_pipeline_btn:
        with st.popover("Import Data", use_container_width=True):
            uploaded = st.file_uploader(
                "Choose JSON or PDF file",
                type=["json"],
                key="up_import"
            )

            data_type = st.radio(
                "Data Type",
                options=["MCQ", "QnA"],
                horizontal=True,
                key="import_data_type"
            )

            c_ic1, c_ic2 = st.columns([1, 1])

            with c_ic2:
                cancel = st.button("Cancel", use_container_width=True, key="btn_cancel_import")

            with c_ic1:
                confirm = st.button("Import", use_container_width=True, type="primary", key="btn_confirm_import")

            if cancel:
                st.toast("Canceled")
                st.rerun()

            if confirm:
                if uploaded is None:
                    st.error("Please upload a file")
                else:
                    type_folder = "mcq" if data_type == "MCQ" else "qna"

                    pending_dir = st.session_state["path_config"]["postprocessed"]["pending"]
                    if not os.path.isabs(pending_dir):
                        pending_dir = os.path.join(st.session_state["project_root"], pending_dir)

                    pending_dir = os.path.join(pending_dir, type_folder)
                    os.makedirs(pending_dir, exist_ok=True)

                    dest_path = os.path.join(pending_dir, uploaded.name)
                    with open(dest_path, "wb") as f:
                        f.write(uploaded.getbuffer())

                    st.success(f"Imported → pending/{type_folder}")
                    st.rerun()


    if "path_config" not in st.session_state:
        st.warning("Please run from app.py")
        return

    project_root = st.session_state.get("project_root", "")
    final_dir = st.session_state["path_config"]["final"]
    pending_base = st.session_state["path_config"]["postprocessed"]["pending"]
    approved_base = st.session_state["path_config"]["postprocessed"]["approved"]

    if not os.path.isabs(final_dir): final_dir = os.path.join(project_root, final_dir)
    if not os.path.isabs(pending_base): pending_base = os.path.join(project_root, pending_base)
    if not os.path.isabs(approved_base): approved_base = os.path.join(project_root, approved_base)

    col_opt, col_mode, col_space = st.columns([2, 2, 4])
    
    with col_opt:
        data_type = st.radio(
            "Data Type:",
            options=["MCQ", "QnA"],
            horizontal=True
        )

    is_mcq = "MCQ" in data_type
    type_subfolder = "mcq" if is_mcq else "qna"
    filename = "mcq.json" if is_mcq else "qna.json"
    
    if "current_view_type" not in st.session_state:
        st.session_state["current_view_type"] = is_mcq
    
    if st.session_state["current_view_type"] != is_mcq:
        st.session_state["master_data"] = None
        st.session_state["current_view_type"] = is_mcq
        st.session_state["page_idx"] = 0
        st.session_state["grid_key_counter"] = 0
        st.session_state["view_mode"] = "Master Data"
        st.session_state["mode_radio_value"] = "Master Data"
        st.session_state["current_pending_file"] = None
        st.rerun()

    if "view_mode" not in st.session_state:
        st.session_state["view_mode"] = "Master Data"
    
    with col_mode:
        view_mode = st.radio(
            "Mode:",
            options=["Master Data", "Review Pending"],
            horizontal=True,
            key="mode_radio_value"
        )
    
    if view_mode != st.session_state["view_mode"]:
        st.session_state["view_mode"] = view_mode
        st.session_state["master_data"] = None
        st.session_state["page_idx"] = 0
        st.rerun()

    final_path = os.path.join(final_dir, filename)
    pending_dir = os.path.join(pending_base, type_subfolder)
    approved_dir = os.path.join(approved_base, type_subfolder)

    current_file_path = final_path

    if st.session_state["view_mode"] == "Review Pending":
        pending_files = get_pending_files_recursive(pending_dir)
        if not pending_files:
            st.info("No pending files found.")
            return
        
        selected_file = st.selectbox("Select Pending File:", pending_files)
        
        if selected_file != st.session_state.get("current_pending_file"):
            st.session_state["current_pending_file"] = selected_file
            st.session_state["master_data"] = None
            st.session_state["page_idx"] = 0
            st.session_state["grid_key_counter"] += 1
            st.rerun()
        
        current_file_path = os.path.join(pending_dir, selected_file)

    if "master_data" not in st.session_state or st.session_state["master_data"] is None:
        st.session_state["master_data"] = load_data(current_file_path)
        st.session_state["page_idx"] = 0
        st.session_state["grid_key_counter"] = 0

    master_data = st.session_state["master_data"]
    total_rows = len(master_data)

    if st.session_state["view_mode"] == "Master Data":
        with st.expander("➕ Add New Row", expanded=False):
            with st.form("add_data_form", clear_on_submit=True):
                new_question = st.text_area("Question")
                
                if is_mcq:
                    c1, c2 = st.columns(2)
                    c3, c4 = st.columns(2)
                    with c1: new_c1 = st.text_input("Choice 1")
                    with c2: new_c2 = st.text_input("Choice 2")
                    with c3: new_c3 = st.text_input("Choice 3")
                    with c4: new_c4 = st.text_input("Choice 4")
                    new_answer = st.text_input("Answer (Key)")
                    new_explanation = st.text_area("Explanation")
                else:
                    new_answer = st.text_area("Answer")

                submitted = st.form_submit_button("Add", type="primary")
                if submitted:
                    if not new_question:
                        st.error("Question cannot be empty")
                    else:
                        new_item = {
                            "question": new_question,
                            "answer": new_answer if not is_mcq else new_answer
                        }
                        if is_mcq:
                            new_item["choices"] = [new_c1, new_c2, new_c3, new_c4]
                            new_item["explanation"] = new_explanation
                            new_item["answer"] = new_answer 
                        
                        st.session_state["master_data"].append(new_item)
                        save_data(current_file_path, st.session_state["master_data"])
                        st.session_state["grid_key_counter"] += 1 
                        st.success("Added successfully")
                        st.rerun()

    if total_rows == 0:
        st.info(f"File is empty")
        return

    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    if total_pages == 0: total_pages = 1
    
    col_p1, col_p2, col_p3 = st.columns([1, 10, 1])
    with col_p1:
        if st.button("Prev", disabled=(st.session_state["page_idx"] == 0), use_container_width=True):
            st.session_state["page_idx"] -= 1
            st.rerun()
    with col_p2:
        current_page = int(st.session_state['page_idx']) + 1
        st.markdown(f"<div style='text-align: center; padding-top: 5px; font-size: 14px;'>Page <b>{current_page}</b> / {total_pages} (Total: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next", disabled=(st.session_state["page_idx"] >= total_pages - 1), use_container_width=True):
            st.session_state["page_idx"] += 1
            st.rerun()

    start_idx = st.session_state["page_idx"] * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    page_data = master_data[start_idx:end_idx]

    df_raw = pd.DataFrame(page_data)
    
    if is_mcq:
        df = process_mcq_dataframe(df_raw)
    else:
        df = process_qna_dataframe(df_raw)

    df = df.copy()
    
    stt_values = range(start_idx + 1, start_idx + len(df) + 1)
    df.insert(0, "No.", stt_values)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_default_column(editable=True, groupable=True, wrapText=True, autoHeight=True)
    
    gb.configure_column("No.", width=50, pinned="left", editable=False)

    if is_mcq:
        gb.configure_column("question", header_name="Question", minWidth=300, flex=1)
        gb.configure_column("choice_1", header_name="Choice 1", width=150)
        gb.configure_column("choice_2", header_name="Choice 2", width=150)
        gb.configure_column("choice_3", header_name="Choice 3", width=150)
        gb.configure_column("choice_4", header_name="Choice 4", width=150)
        gb.configure_column("answer", header_name="Answer", width=100)
        gb.configure_column("explanation", header_name="Explanation", minWidth=250, flex=1)
    else:
        gb.configure_column("question", header_name="Question", minWidth=400, flex=1)
        gb.configure_column("answer", header_name="Answer", minWidth=400, flex=1)

    gridOptions = gb.build()

    col_act1, col_act2, col_space2 = st.columns([1, 1, 6])
    
    with col_act1:
        delete_btn = st.button("Delete", type="primary", use_container_width=True)
    with col_act2:
        if st.session_state["view_mode"] == "Review Pending":
            save_btn = st.button("Merge to Master", type="primary", use_container_width=True)
        else:
            save_btn = st.button("Save", type="secondary", use_container_width=True)

    grid_key = f"grid_{data_type}_{st.session_state.get('grid_key_counter', 0)}"

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.AS_INPUT, 
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        height=500, 
        allow_unsafe_jscode=True,
        key=grid_key
    )

    updated_df = grid_response['data']
    selected_rows = grid_response['selected_rows']

    if delete_btn:
        has_selection = False
        if selected_rows is not None:
            if isinstance(selected_rows, pd.DataFrame):
                has_selection = not selected_rows.empty
            else:
                has_selection = len(selected_rows) > 0

        if not has_selection:
            st.toast("Please select rows to delete", icon="⚠️")
        else:
            indices_in_page = []
            if isinstance(selected_rows, pd.DataFrame):
                indices_in_page = selected_rows.index.tolist()
            else:
                for row in selected_rows:
                    if '_selectedRowNodeInfo' in row:
                        indices_in_page.append(int(row['_selectedRowNodeInfo']['nodeRowIndex']))
            
            indices_to_remove = [start_idx + int(i) for i in indices_in_page]
            indices_to_remove = sorted(list(set(indices_to_remove)), reverse=True)
            
            show_delete_confirmation(indices_to_remove, st.session_state["master_data"], current_file_path)

    if save_btn:
        if isinstance(updated_df, pd.DataFrame):
             edited_records = updated_df.to_dict('records')
        else:
             edited_records = updated_df

        current_page_data = []
        for i, record in enumerate(edited_records):
            item = {}
            item["question"] = record.get("question")
            item["answer"] = record.get("answer")

            if is_mcq:
                item["explanation"] = record.get("explanation")
                item["choices"] = [
                    str(record.get("choice_1", "")),
                    str(record.get("choice_2", "")),
                    str(record.get("choice_3", "")),
                    str(record.get("choice_4", ""))
                ]
            else:
                pass
            current_page_data.append(item)

        for i, item in enumerate(current_page_data):
            master_idx = start_idx + i
            if master_idx < len(st.session_state["master_data"]):
                 st.session_state["master_data"][master_idx] = item

        if st.session_state["view_mode"] == "Review Pending":
            show_merge_confirmation(st.session_state["master_data"], final_path, current_file_path, pending_dir, approved_dir)
        else:
            if save_data(current_file_path, st.session_state["master_data"]):
                st.toast("Saved successfully", icon="✅")