import streamlit as st
import pandas as pd
import os
import shutil
from io import StringIO

def find_file(root_folder, base_name):
    base_lower = base_name.lower()
    for root, _, files in os.walk(root_folder):
        for f in files:
            if f.lower().endswith('.mp4') and os.path.splitext(f)[0].lower() == base_lower:
                return os.path.join(root, f)
    return None

def login_ui(password_hint=""):
    st.title("🔐 File Renamer - Login")
    if password_hint:
        st.caption(f"Hint: {password_hint}")

    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == st.secrets["app_password"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password. Try again.")


def main():
    # Protect access with password
    if not st.session_state.get("authenticated", False):
        login_ui(password_hint="Ask your supervisor.")  # Optional hint
        return
    
    st.set_page_config(page_title="Playblast Renamer", layout="centered")

    st.title("📦 Playblast Renamer")
    st.caption("Upload your CSV, select folders, and export renamed MP4 files effortlessly.")

    with st.expander("📘 Instructions", expanded=False):
        st.markdown("""
        1. **Upload CSV** that contains `RM##` and `File Name` columns.
        2. **Enter Source Folder** where original `.mp4` files are located.
        3. **Enter Destination Folder** where renamed files will be saved.
        4. **Click Process** to copy and rename files like `RM101_ShotA.mp4`.
        """)

    # --- CSV Upload ---
    uploaded_file = st.file_uploader("📄 Upload CSV File", type=["csv"])
    rows = []

    if uploaded_file:
        try:
            raw_lines = uploaded_file.read().decode("utf-8").splitlines()
            header_idx = next(i for i, line in enumerate(raw_lines) if "RM##" in line and "File Name" in line)
            df = pd.read_csv(StringIO("\n".join(raw_lines[header_idx:])))
            
            if "RM##" not in df.columns or "File Name" not in df.columns:
                st.error("CSV must contain 'RM##' and 'File Name' columns.")
                return

            rows = [(row["RM##"].strip(), row["File Name"].strip()) for _, row in df.iterrows()]
            st.success(f"✅ Loaded {len(rows)} entries from CSV.")

        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return

    # --- Folder Inputs ---
    st.markdown("### 📂 Folder Selection")
    col1, col2 = st.columns(2)
    with col1:
        source_folder = st.text_input("🔍 Source Folder Path", placeholder="e.g. C:/Projects/Exports")
    with col2:
        dest_folder = st.text_input("💾 Destination Folder Path", placeholder="e.g. D:/Playblasts")

    # --- Process Files ---
    if st.button("🚀 Process Files") and rows and source_folder and dest_folder:
        with st.spinner("Processing files..."):
            copied = 0
            missing = []
            errors = []
            logs = []

            for rm_code, base_filename in rows:
                found_path = find_file(source_folder, base_filename)
                if found_path:
                    new_name = f"{rm_code}_{base_filename}.mp4"
                    dest_path = os.path.join(dest_folder, new_name)
                    try:
                        shutil.copy(found_path, dest_path)
                        logs.append(f"✅ Copied: {base_filename}.mp4 → {new_name}")
                        copied += 1
                    except Exception as e:
                        msg = f"❌ Error copying {base_filename}: {e}"
                        logs.append(msg)
                        errors.append(msg)
                else:
                    logs.append(f"❌ Not found: {base_filename}.mp4")
                    missing.append(base_filename)

        # --- Results ---
        st.success(f"✅ Done: {copied} files copied.")
        if missing:
            st.warning(f"⚠️ Missing files ({len(missing)}):")
            st.text("\n".join(f"• {m}.mp4" for m in missing))
        if errors:
            st.error(f"🚫 Errors occurred while copying:")
            st.text("\n".join(errors))

        # --- Log Output ---
        with st.expander("🧾 Full Log"):
            st.text("\n".join(logs))

if __name__ == "__main__":
    main()
