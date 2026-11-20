from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import ui
from planner_ui import run_planner

st.set_page_config("DBB · Plano de 10 dias", "✦", layout="wide")
ui.inject()
run_planner()
