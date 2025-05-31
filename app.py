import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import os

# --- CONFIG ---
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# --- SEARCH FUNCTION ---
def search_web(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json().get("organic", [])
        return results[:3]
    else:
        return []

# --- CTB REPORT ---
def generate_ctb(df):
    active = df[df['Status'] == 'Active'].copy()
    ctb_summary = active.groupby('Final_Product')['CTB_Quantity'].min().reset_index()
    ctb_summary.rename(columns={'CTB_Quantity': 'Buildable_Units'}, inplace=True)
    return ctb_summary

# --- PO SUGGESTIONS ---
def generate_po(df, target_doi=14):
    df = df.copy()
    df['Suggested_Order_Qty'] = (target_doi * df['Daily_Demand']) - df['On_Hand']
    df['Suggested_Order_Qty'] = df['Suggested_Order_Qty'].apply(lambda x: max(x, 0))
    return df[df['Suggested_Order_Qty'] > 0][['Part_Number', 'On_Hand', 'Daily_Demand', 'Suggested_Order_Qty']]

# --- STREAMLIT PAGE ---
st.set_page_config(page_title="Parete - AI Supply Chain Agent", layout="wide")
st.title("🤖 Parete - Interactive Supply Chain Assistant")

# --- STEP 1: INDUSTRY ---
industry = st.selectbox("🌐 What industry do you work in?", [
    "Retail",
    "Consumer Electronics (Manufacturing)",
    "Repairs (RMA)",
    "Other"
])

# --- STEP 2: ROLE ---
role = st.selectbox("👤 What is your role?", [
    "Buyer", "Demand Planner", "Supply Chain Analyst",
    "Sourcing Manager", "Operations/Program Manager", "Startup Founder", "Other"
])

# --- STEP 3: TASK TYPE ---
task = st.radio("⚙️ What do you want to do today?", [
    "Inventory / Demand Planning",
    "Create MRP",
    "Run CTB",
    "PO Suggestions",
    "Local Sourcing (Tariff Mitigation)",
    "Vendor Follow-up (Escalations)",
    "Zomato-style Ordering Sheet",
    "Custom Use Case"
])

# --- STEP 4: DYNAMIC TASK LOGIC ---
if task == "Inventory / Demand Planning" and industry == "Retail":
    st.info("Upload your forecast and stock file. Parete will generate an ARS-style planning sheet (like Zomato or Blinkit).")

elif task == "Create MRP" and "Consumer Electronics" in industry:
    st.info("Upload your BOM, Open POs, and forecast. Parete will calculate weekly MRP and generate order plans.")

elif task == "Run CTB":
    st.header("📁 Upload CTB Excel File")
    file = st.file_uploader("Upload .xlsx file with Status, Final_Product, CTB_Quantity", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        ctb = generate_ctb(df)
        st.dataframe(ctb)

elif task == "PO Suggestions":
    st.header("📁 Upload PO Suggestion Input")
    file = st.file_uploader("Upload .xlsx file with On_Hand and Daily_Demand columns", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        po = generate_po(df)
        st.dataframe(po)

elif task == "Local Sourcing (Tariff Mitigation)":
    st.info("Let’s run a sourcing project to shift from China to local vendors. You’ll upload a parts list, and Parete will guide your next steps.")

elif task == "Vendor Follow-up (Escalations)":
    st.info("Upload your Open PO report. Parete will highlight delayed lines and help you generate follow-up emails.")

elif task == "Zomato-style Ordering Sheet":
    st.info("This feature is under construction. It will generate a reorder planning sheet based on daily/weekly sales and clusters.")

# --- STEP 5: Web Search Add-on ---
st.subheader("🔎 Ask a quick supply chain question")
query = st.text_input("Type a real-world supply chain query (e.g., 'Best practices for MRP in electronics')")
if query:
    with st.spinner("Searching..."):
        results = search_web(query)
    st.markdown("### 🌐 Search Results")
    for res in results:
        st.markdown(f"🔹 [{res['title']}]({res['link']}): {res['snippet']}")
