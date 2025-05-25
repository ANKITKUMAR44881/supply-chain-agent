import streamlit as st
import pandas as pd
from io import BytesIO

# Define processing functions
def calculate_ctb(df):
    ctb_output = df[df['Status'] == 'Active'].copy()
    ctb_output_grouped = ctb_output.groupby('Final_Product')['CTB_Quantity'].min().reset_index()
    ctb_output_grouped.rename(columns={'CTB_Quantity': 'Buildable_Units'}, inplace=True)
    return ctb_output_grouped

def analyze_stock(df):
    df['Stock_Status'] = df['On_Hand'].apply(lambda x: 'Out of Stock' if x <= 0 else ('Overstock' if x > 5000 else 'Normal'))
    return df[['Part_Number', 'On_Hand', 'Stock_Status']]

def generate_po_suggestions(df, target_doi=14):
    df = df.copy()
    df['Suggested_Order_Qty'] = (target_doi * df['Daily_Demand']) - df['On_Hand']
    df['Suggested_Order_Qty'] = df['Suggested_Order_Qty'].apply(lambda x: max(x, 0))
    po_df = df[df['Suggested_Order_Qty'] > 0][['Part_Number', 'On_Hand', 'Daily_Demand', 'Suggested_Order_Qty']]
    return po_df

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'role' not in st.session_state:
    st.session_state.role = None
if 'business_type' not in st.session_state:
    st.session_state.business_type = None
if 'category' not in st.session_state:
    st.session_state.category = None
if 'target_doi' not in st.session_state:
    st.session_state.target_doi = 14

st.title("🤖 Supply Chain Assistant Chat")

if st.session_state.step == 0:
    with st.chat_message("assistant"):
        st.markdown("👋 Hi! I'm your smart Supply Chain Agent. First, what's your role?")
    role = st.chat_input("Type: Buyer, Sourcing Manager, Analyst")
    if role:
        st.session_state.role = role.strip().title()
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 1:
    with st.chat_message("assistant"):
        st.markdown(f"Great, {st.session_state.role}! Is your work focused on **Retail** or **Manufacturing**?")
    btype = st.chat_input("Type: Retail or Manufacturing")
    if btype:
        st.session_state.business_type = btype.strip().title()
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    with st.chat_message("assistant"):
        st.markdown("And are you working in **Consumer Electronics** or **Repairs**?")
    cat = st.chat_input("Type: Consumer Electronics or Repairs")
    if cat:
        st.session_state.category = cat.strip().title()
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    with st.chat_message("assistant"):
        st.markdown("🎯 What is your target Days of Inventory?")
    doi = st.chat_input("Enter a number like 14")
    if doi and doi.isdigit():
        st.session_state.target_doi = int(doi)
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    with st.chat_message("assistant"):
        st.markdown(f"🔍 Perfect! You’re a **{st.session_state.role}** in **{st.session_state.business_type}** handling **{st.session_state.category}**. Please upload your Excel to get started.")
    uploaded_file = st.file_uploader("Upload your CTB Excel file", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        st.session_state.step = 5
        st.rerun()

elif st.session_state.step == 5:
    df = st.session_state.df
    with st.chat_message("assistant"):
        st.markdown("✅ Here's your Clear to Build Report:")
    ctb_summary = calculate_ctb(df)
    st.dataframe(ctb_summary)

    with st.chat_message("assistant"):
        st.markdown("📊 Here's the Stock Status Analysis:")
    stock_df = analyze_stock(df)
    st.dataframe(stock_df)

    with st.chat_message("assistant"):
        st.markdown("📦 Generating PO Suggestions based on your DOI target...")
    po_df = generate_po_suggestions(df, target_doi=st.session_state.target_doi)
    st.dataframe(po_df)

    output = BytesIO()
    po_df.to_excel(output, index=False)
    st.download_button("📥 Download PO Suggestion File", data=output.getvalue(), file_name="PO_Suggestions.xlsx")

    st.success("All done! Upload a new file or start over anytime.")
