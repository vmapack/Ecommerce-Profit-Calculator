import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Multi-Marketplace Profit Dashboard", layout="wide"
)

st.title("📊 Multi-Marketplace E-Commerce Profit Dashboard")
st.markdown("All-in-One Profit & Loss Calculator for Amazon, Flipkart & More")


# Load Master SKU Costing
@st.cache_data
def load_costing():
    try:
        cost_df = pd.read_excel("AMAZON COSTING.xlsx", sheet_name=0)
        cost_df["SKU_clean"] = (
            cost_df["SKU"].astype(str).str.strip().str.upper()
        )
        return dict(zip(cost_df["SKU_clean"], cost_df["COSTING"]))
    except Exception as e:
        st.error(f"AMAZON COSTING.xlsx फ़ाइल लोड करने में एरर: {e}")
        return {}


costing_map = load_costing()

# Sidebar Settings
st.sidebar.header("⚙️ General Settings")
channel = st.sidebar.selectbox(
    "Select Marketplace",
    ["Amazon (Unified Report)", "Flipkart (Coming Soon)", "Meesho (Coming Soon)"],
)

damage_loss = st.sidebar.number_input(
    "Est. Return Freight/Loss per Refund (₹)", value=40
)

# Amazon Module
if channel == "Amazon (Unified Report)":
    st.subheader("🟠 Amazon Payment & Profit Calculator")
    uploaded_file = st.file_uploader(
        "Upload Amazon Unified CSV Report", type=["csv"]
    )

    if uploaded_file is not None:
        try:
            first_line = uploaded_file.readline().decode(
                "latin1", errors="ignore"
            )
            uploaded_file.seek(0)
            skip_rows = (
                13 if "Includes Amazon Marketplace" in first_line else 0
            )

            df = pd.read_csv(
                uploaded_file, skiprows=skip_rows, encoding="latin1"
            )

            df["total_clean"] = pd.to_numeric(
                df["total"].astype(str).str.replace(",", ""), errors="coerce"
            ).fillna(0)
            df["Sku_clean"] = df["Sku"].astype(str).str.strip()

            orders_df = df[df["type"].str.strip() == "Order"].copy()
            refunds_df = df[df["type"].str.strip() == "Refund"].copy()

            orders_df["unit_cost"] = (
                orders_df["Sku_clean"].str.upper().map(costing_map).fillna(0)
            )
            orders_df["quantity_clean"] = pd.to_numeric(
                orders_df["quantity"], errors="coerce"
            ).fillna(1)
            orders_df["total_cogs"] = (
                orders_df["quantity_clean"] * orders_df["unit_cost"]
            )

            total_orders = len(orders_df)
            total_refunds = len(refunds_df)
            net_payout = df[df["type"].str.strip() != "Transfer"][
                "total_clean"
            ].sum()
            total_cogs = orders_df["total_cogs"].sum()
            total_return_loss = total_refunds * damage_loss
            net_profit = net_payout - total_cogs - total_return_loss

            # Summary Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Orders", total_orders)
            c2.metric(
                "Refunds / Returns",
                total_refunds,
                delta=(
                    f"{(total_refunds/total_orders*100):.1f}% Return Rate"
                    if total_orders
                    else "0%"
                ),
                delta_color="inverse",
            )
            c3.metric("Amazon Net Payout", f"₹{net_payout:,.2f}")
            c4.metric("Net Profit", f"₹{net_profit:,.2f}")

            st.markdown("---")
            st.subheader("📋 Top Profitable SKUs Breakdown")

            sku_summary = (
                orders_df.groupby("Sku_clean")
                .agg(
                    Orders=("order id", "count"),
                    Total_Qty=("quantity_clean", "sum"),
                    Unit_Cost=("unit_cost", "first"),
                    Amazon_Payout=("total_clean", "sum"),
                    Total_COGS=("total_cogs", "sum"),
                )
                .reset_index()
            )

            sku_summary["Net_Margin"] = (
                sku_summary["Amazon_Payout"] - sku_summary["Total_COGS"]
            )
            sku_summary = sku_summary.sort_values(
                by="Net_Margin", ascending=False
            )

            st.dataframe(sku_summary, use_container_width=True)

        except Exception as e:
            st.error(f"फ़ाइल प्रोसेस करने में समस्या आई: {e}")