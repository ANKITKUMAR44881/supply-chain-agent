# Step 1: Setup - Install required packages
# pip install streamlit pandas openpyxl

import streamlit as st
import pandas as pd
from io import BytesIO

# Step 2: CTB Logic - Calculate how many final products can be built
def calculate_ctb(df):
    ctb_output = df[df['Status'] == 'Active'].copy()
    ctb_output_grouped = ctb_output.groupby('Final_Product')['CTB_Quantity'].min().reset_index()
    ctb_output_grouped.rename(columns={'CTB_Quantity': 'Buildable_Units'}, inplace=True)
    return ctb_output_grouped

# Step 3: Stock analysis
def analyze_stock(df):
    df['Stock_Status'] = df['On_Hand'].apply(lambda x: 'Out of Stock' if x <= 0 else ('Overstock' if x > 5000 else 'Normal'))
    return df[['Part_Number', 'On_Hand', 'Stock_Status']]

# Step 4: Generate Purchase Order Suggestions
def generate_po_suggestions(df, target_doi=14):
    df = df.copy()
    df['Suggested_Order_Qty'] = (target_doi * df['Daily_Demand']) - df['On_Hand']
    df['Suggested_Order_Qty'] = df['Suggested_Order_Qty'].apply(lambda x: max(x, 0))
    po_df = df[df['Suggested_Order_Qty'] > 0][['Part_Number', 'On_Hand', 'Daily_Demand', 'Suggested_Order_Qty']]
    return po_df

# Step 5: Streamlit UI
st.title("📦 Supply Chain Agent - CTB, Stock & PO Suggestion")

uploaded_file = st.file_uploader("Upload your CTB Excel file", type=["xlsx"])

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

    output = BytesIO()
    po_df.to_excel(output, index=False)
    st.download_button("📥 Download PO Suggestion File", data=output.getvalue(), file_name="PO_Suggestions.xlsx")
