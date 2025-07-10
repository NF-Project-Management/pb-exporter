import streamlit as st
import pandas as pd
import os
import zipfile
import tempfile
import shutil
from io import BytesIO, StringIO

# ----------------------
# Find matching .mp4 file in extracted ZIP folder
# ----------------------
def find_file(root_folder, base_name):
    base_lower = base_name.lower()
    for root, _, files in os.walk(root_folder):
        for f in files:
            if f.lower().endswith('.mp4') and os.path.splitext(f)[0].lower() == base_lower:
                return os.path.join(root, f)
    return None

# ----------------------
# Login screen
# ----------------------
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

# ----------------------
# Main UI
# ----------------------
def main():
    # Password gate
    if not st.session_state.get("authenticated", False):
        login_ui(password_hint="Ask your supervisor.")
        return

    st.set_page_config(page_title="Playblast Renamer", layout="centered")
    st.title("📦 Playblast Renamer (ZIP Version)")
    st.caption("Upload a CSV and a ZIP of .mp4s. Get renamed files back in a ZIP.")

    with st.expander("📘 Instructions", expanded=False):
        st.markdown("""
        1. Upload a **CSV** file that includes `RM##` and `File Name` columns.
        2. Upload a **ZIP file** of `.mp4` files to be renamed.
        3. Click **Process**, and download the ZIP of renamed files.
        """)

    # Upload CSV
    uploaded_csv = st.file_uploader("📄 Upload CSV File", type=["csv"])
    uploaded_zip = st.file_uploader("📦 Upload ZIP of .mp4 Files", type=["zip"])
    rows = []

    if uploaded_csv:
        try:
            raw_lines = uploaded_csv.read().decode("utf-8").splitlines()
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

    if st.button("🚀 Process Files") and uploaded_zip and rows:
        with st.spinner("Processing..."):
            copied = 0
            missing = []
            errors = []
            logs = []

            # Temp folders
            with tempfile.TemporaryDirectory() as extract_dir, tempfile.TemporaryDirectory() as output_dir:
                # Extract uploaded zip
                with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Rename and copy files
                for rm_code, base_filename in rows:
                    found_path = find_file(extract_dir, base_filename)
                    if found_path:
                        new_name = f"{rm_code}_{base_filename}.mp4"
                        dest_path = os.path.join(output_dir, new_name)
                        try:
                            shutil.copy(found_path, dest_path)
                            logs.append(f"✅ Copied: {base_filename}.mp4 → {new_name}")
                            copied += 1
                        except Exception as e:
                            error_msg = f"❌ Error copying {base_filename}: {e}"
                            logs.append(error_msg)
                            errors.append(error_msg)
                    else:
                        logs.append(f"❌ Not found: {base_filename}.mp4")
                        missing.append(base_filename)

                # Create ZIP to download
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for f in os.listdir(output_dir):
                        full_path = os.path.join(output_dir, f)
                        zipf.write(full_path, arcname=f)

                zip_buffer.seek(0)
                st.success(f"✅ Done! {copied} files copied and renamed.")

                st.download_button(
                    label="📥 Download Renamed ZIP",
                    data=zip_buffer,
                    file_name="renamed_files.zip",
                    mime="application/zip"
                )

            # Logs
            if missing:
                st.warning(f"⚠️ Missing files ({len(missing)}):")
                st.text("\n".join(f"• {m}.mp4" for m in missing))
            if errors:
                st.error("🚫 Errors:")
                st.text("\n".join(errors))
            with st.expander("🧾 Full Log"):
                st.text("\n".join(logs))

if __name__ == "__main__":
    main()
