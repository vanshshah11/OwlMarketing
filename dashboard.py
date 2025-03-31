#!/usr/bin/env python3
import streamlit as st
import subprocess
import os
import time

# Set the page configuration
st.set_page_config(page_title="OWLmarketing Dashboard", layout="wide")

st.title("OWLmarketing: Automated Marketing Dashboard")

# Sidebar for controls and configuration
st.sidebar.header("Control Panel")

# ---- Run Master Pipeline ----
st.sidebar.subheader("Run Pipeline")
if st.sidebar.button("Run Master Pipeline"):
    st.sidebar.write("Starting master pipeline...")
    # Launch the master pipeline as a subprocess
    process = subprocess.Popen(
        ["python", "scripts/master_pipeline.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    log_area = st.empty()
    output_lines = []
    # Read output in real time and display it
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            output_lines.append(output)
            log_area.text("".join(output_lines))
            time.sleep(0.1)
    st.sidebar.success("Master pipeline finished.")

# ---- Reload Configuration ----
st.sidebar.subheader("Configuration")
if st.sidebar.button("Reload Configuration"):
    config_path = "config/config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_data = f.read()
        st.sidebar.text_area("Current Config", config_data, height=300)
    else:
        st.sidebar.error("Config file not found.")

# ---- Avatar Models Overview ----
st.header("Avatar Models")
avatar_dir = "video_generation/avatars"
if os.path.exists(avatar_dir):
    avatars = sorted(os.listdir(avatar_dir))
    if avatars:
        st.write("The following avatar models have been created:")
        for avatar in avatars:
            st.markdown(f"- **{avatar}**")
    else:
        st.write("No avatar models found.")
else:
    st.error("Avatar directory not found.")

# ---- Scheduled Posts ----
st.header("Scheduled Posts")
scheduled_file = "config/scheduled_posts.json"
if os.path.exists(scheduled_file):
    with open(scheduled_file, "r") as f:
        scheduled_data = f.read()
    st.text_area("Scheduled Posts", scheduled_data, height=300)
else:
    st.write("No scheduled posts found.")

# ---- Live Log Viewer ----
st.header("Live Log Viewer")
log_file = "pipeline.log"  # If you configure your pipeline to output logs to this file
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        logs = f.read()
    st.text_area("Pipeline Logs", logs, height=300)
else:
    st.write("Log file not found. Ensure your pipeline writes logs to 'pipeline.log'.")
