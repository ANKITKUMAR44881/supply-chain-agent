import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
from datetime import datetime

# Secure API key retrieval
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Function to call Serper.dev for real-time web search
def search_web(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json().get("organic", [])
        return results[:3]
    else:
        return []

# CTB calculation
def calculate_ctb(df):
    ctb_output = df[df['Status'] == 'Active'].copy()
    ctb_output_grouped = ctb_output.groupby('Final_Product')['CTB_Quantity'].min().reset_index()
    ctb_output_grouped.rename(columns={'CTB_Quantity': 'Buildable_Units'}, inplace=True)
    return ctb_output_grouped

# Stock analysis
def analyze_stock(df):
    df['Stock_Status'] = df['On_Hand'].apply(lambda x: 'Out of Stock' if x <= 0 else ('Overstock' if x > 5000 else 'Normal'))
    return df[['Part_Number', 'On_Hand', 'Stock_Status']]

# PO suggestions
def generate_po_suggestions(df, target_doi=14):
    df = df.copy()
    df['Suggested_Order_Qty'] = (target_doi * df['Daily_Demand']) - df['On_Hand']
    df['Suggested_Order_Qty'] = df['Suggested_Order_Qty'].apply(lambda x: max(x, 0))
    po_df = df[df['Suggested_Order_Qty'] > 0][['Part_Number', 'On_Hand', 'Daily_Demand', 'Suggested_Order_Qty']]
    return po_df

# Streamlit UI
st.set_page_config(page_title="Parete - AI Supply Chain Agent", layout="wide")
st.title("🤖 Parete - Your Supply Chain Execution Agent")

# Role collection
with st.chat_message("assistant"):
    st.markdown("👋 Hi! What would you like help with today?")
role = st.selectbox("Choose your role:", ["Buyer", "Sourcing Manager", "Analyst", "Startup Founder", "Other"])
biz_type = st.radio("Your business type:", ["Retail", "Manufacturing", "Repairs"])
category = st.radio("Product category:", ["Consumer Electronics", "AR/VR", "Mobility", "Other"])

# Web Search only
st.subheader("💬 Ask Parete (Web Search)")
user_query = st.text_input("What supply chain task or question do you have?")

if user_query:
    with st.spinner("Searching online..."):
        search_results = search_web(user_query)
    st.markdown("### 🌐 Top Search Results:")
    for res in search_results:
        st.markdown(f"🔹 [{res['title']}]({res['link']}): {res['snippet']}")

# Excel upload
st.header("📁 Upload your CTB Excel file")
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("✅ Clear to Build Report")
    ctb_summary = calculate_ctb(df)
    st.dataframe(ctb_summary)

    st.subheader("📊 Stock Status")
    stock_df = analyze_stock(df)
    st.dataframe(stock_df)

    st.subheader("📑 Purchase Order Suggestions")
    po_df = generate_po_suggestions(df)
    st.dataframe(po_df)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"PO_Suggestions_{timestamp}.xlsx"
    output = BytesIO()
    po_df.to_excel(output, index=False)

    st.download_button("📥 Download PO Suggestion File", data=output.getvalue(), file_name=output_file)
