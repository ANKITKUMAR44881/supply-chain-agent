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

# --- ASSISTANT MODE LOGIC ---
def analyze_open_po(po_df):
    overdue = po_df[po_df['Due_Date'] < pd.Timestamp.today()]
    return overdue

def summarize_ctb_risk(ctb_df):
    risk_parts = ctb_df[ctb_df['Buildable_Units'] <= 0]
    return risk_parts

def draft_emails_from_overdue(overdue_df):
    overdue_df['Due_Date'] = pd.to_datetime(overdue_df['Due_Date']).dt.date
    grouped = overdue_df.groupby('Vendor_Name') if 'Vendor_Name' in overdue_df.columns else overdue_df.groupby('PO_Number')
    emails = {}

    for vendor, rows in grouped:
        lines = "\n".join([
            f"- {row['PO_Number']} | {row['Part_Number']} | Qty: {row['Quantity']} | Due: {row['Due_Date']}"
            for _, row in rows.iterrows()
        ])
        email = f"""
**To:** [Vendor Email Here]  
**Subject:** Urgent: Overdue PO Follow-up  

Dear {vendor},

We noticed the following PO lines are overdue as of today:

{lines}

Kindly expedite shipment or provide revised delivery timelines.

Regards,  
Parete Agent
"""
        emails[vendor] = email.strip()
    return emails

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
    "Run My Daily Supply Chain Assistant",
    "Inventory / Demand Planning",
    "Create MRP",
    "Run CTB",
    "PO Suggestions",
    "Local Sourcing (Tariff Mitigation)",
    "Vendor Follow-up (Escalations)",
    "Zomato-style Ordering Sheet",
    "Custom Use Case"
])

# --- STEP 4: TASK ROUTING ---

if task == "Run My Daily Supply Chain Assistant":
    st.subheader("🧠 Assistant Mode - Upload Files")

    po_file = st.file_uploader("Upload Open PO File (.xlsx)", type=["xlsx"], key="po")
    ctb_file = st.file_uploader("Upload CTB File (.xlsx)", type=["xlsx"], key="ctb")

    if po_file and ctb_file:
        po_df = pd.read_excel(po_file)
        ctb_input = pd.read_excel(ctb_file)

        overdue_pos = analyze_open_po(po_df)
        ctb_summary = generate_ctb(ctb_input)
        ctb_risk = summarize_ctb_risk(ctb_summary)

        st.success("✅ Daily Assistant Summary:")
        st.markdown(f"- 🔴 {len(overdue_pos)} overdue PO lines")
        st.markdown(f"- 📦 {len(ctb_risk)} final products with CTB = 0")
        st.markdown(f"- 📈 Total CTB rows: {len(ctb_summary)}")

        st.subheader("📋 CTB Summary")
        st.dataframe(ctb_summary)

        st.subheader("⚠️ Build Risk (CTB = 0)")
        st.dataframe(ctb_risk)

        st.subheader("⏰ Overdue POs")
        st.dataframe(overdue_pos)

        st.subheader("📨 Suggested Vendor Follow-up Emails")
        emails = draft_emails_from_overdue(overdue_pos)
        for vendor, content in emails.items():
            st.markdown(f"**✉️ Vendor: {vendor}**")
            st.code(content, language="markdown")

elif task == "Inventory / Demand Planning" and industry == "Retail":
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
