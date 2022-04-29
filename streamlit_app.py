"""This is a very simple wrapper around the Streamlit UI code"""
import argparse

import streamlit as st

from arc.app.ui import run_ui

st.set_page_config(layout="wide")

parser = argparse.ArgumentParser(description="Select Streamlit mode")
parser.add_argument("mode", help="Streamlit app mode: Demo, Dev, Stats")
parser.add_argument("-n", default=400, type=int, help="Total tasks to run")
args = parser.parse_args()

run_ui(args.mode, args.n)
