import pandas as pd
import streamlit as st
import plotly.express as px
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Set layout
st.set_page_config(layout="wide")
st.title("📊 Brazilian E-Commerce Dashboard")
st.markdown("Analisis persebaran geografis, preferensi pembayaran, ulasan pelanggan, dan segmentasi berdasarkan data Olist.")

# Sidebar Navigation
page = st.sidebar.radio("📂 Navigasi Halaman", [
    "Pelanggan & Penjual",
    "Inklusi Keuangan",
    "Produk & Review",
    "Segmentasi RFM",
    "Cicilan Kredit"
])

# Load Data
data_path = os.path.join("dashboard", "data-dashboard")
customer_location = pd.read_csv(os.path.join(data_path, "customer_counts.csv"))
seller_location = pd.read_csv(os.path.join(data_path, "seller_counts.csv"))
payments_location = pd.read_csv(os.path.join(data_path, "payment_pivot.csv"))
top_categories_location = pd.read_csv(os.path.join(data_path, "top_per_state.csv"))
rfm = pd.read_csv(os.path.join(data_path, "rfm_analysis.csv"))
reviews = pd.read_csv(os.path.join(data_path, "merged_reviews.csv"))
payments = pd.read_csv(os.path.join(data_path, "merged_payments.csv"))
brazil_map = gpd.read_file(os.path.join(data_path, "brazil-states.geojson"))

# Convert date columns
payments["order_purchase_timestamp"] = pd.to_datetime(payments["order_purchase_timestamp"])
reviews["order_purchase_timestamp"] = pd.to_datetime(reviews["order_purchase_timestamp"])

# Sidebar filter for time
st.sidebar.header("🗓️ Filter Waktu")
min_date = payments["order_purchase_timestamp"].min().date()
max_date = payments["order_purchase_timestamp"].max().date()
selected_date = st.sidebar.date_input("Rentang Waktu Pembelian", [min_date, max_date], min_value=min_date, max_value=max_date)
start_date, end_date = pd.to_datetime(selected_date[0]), pd.to_datetime(selected_date[1])
payments = payments[(payments["order_purchase_timestamp"] >= start_date) & (payments["order_purchase_timestamp"] <= end_date)]
reviews = reviews[(reviews["order_purchase_timestamp"] >= start_date) & (reviews["order_purchase_timestamp"] <= end_date)]

# Pages
if page == "Pelanggan & Penjual":
    st.subheader("📍 Persebaran Pelanggan dan Penjual")
    col1, col2 = st.columns(2)
    with col1:
        fig_cust = px.choropleth(customer_location, geojson=brazil_map, locations="state", featureidkey="properties.sigla", color="customer_count", color_continuous_scale="YlGnBu", title="Jumlah Pelanggan")
        fig_cust.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_cust, use_container_width=True)
    with col2:
        fig_seller = px.choropleth(seller_location, geojson=brazil_map, locations="state", featureidkey="properties.sigla", color="seller_count", color_continuous_scale="OrRd", title="Jumlah Penjual")
        fig_seller.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_seller, use_container_width=True)

elif page == "Inklusi Keuangan":
    st.subheader("💳 Inklusi Keuangan")
    fig_inc = px.choropleth(payments_location, geojson=brazil_map, locations="state", featureidkey="properties.sigla", color="financial_inclusion_ratio", color_continuous_scale="Plasma", title="Rasio Inklusi Keuangan")
    fig_inc.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig_inc, use_container_width=True)
    
    st.subheader("💰 Distribusi Jenis Pembayaran")
    payment_melted = payments_location.melt(id_vars=["state"], value_vars=["boleto", "credit_card", "debit_card", "voucher"], var_name="payment_type", value_name="count")
    fig_pay = px.bar(payment_melted, x="state", y="count", color="payment_type", title="Jenis Pembayaran per State")
    st.plotly_chart(fig_pay, use_container_width=True)

elif page == "Produk & Review":
    st.subheader("📦 Kategori Produk Terpopuler")
    fig_cat = px.bar(top_categories_location, x="state", y="count", color="product_category_name", title="Kategori Produk Terpopuler")
    st.plotly_chart(fig_cat, use_container_width=True)

    st.subheader("⭐ Rata-rata Review per Kategori Produk")
    avg_review = reviews.groupby("product_category_name")["review_score"].mean().reset_index()
    fig_avg = px.bar(avg_review.sort_values(by="review_score", ascending=False), x="product_category_name", y="review_score", color="review_score", color_continuous_scale="Blues", title="Rata-rata Skor Ulasan per Kategori Produk")
    fig_avg.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_avg, use_container_width=True)

elif page == "Segmentasi RFM":
    st.subheader("📊 Distribusi RFM")
    fig_rfm, ax = plt.subplots(1, 3, figsize=(18, 5))
    sns.histplot(rfm['Recency'], bins=20, ax=ax[0], color='skyblue')
    sns.histplot(rfm['Frequency'], bins=20, ax=ax[1], color='lightgreen')
    sns.histplot(rfm['Monetary'], bins=20, ax=ax[2], color='salmon')
    ax[0].set_title('Recency')
    ax[1].set_title('Frequency')
    ax[2].set_title('Monetary')
    st.pyplot(fig_rfm)

    fig_seg, ax = plt.subplots(figsize=(10, 5))
    sns.countplot(data=rfm, x='Segment', order=rfm['Segment'].value_counts().index, palette='pastel')
    plt.title("Segmentasi Pelanggan RFM")
    plt.xticks(rotation=45)
    st.pyplot(fig_seg)

elif page == "Cicilan Kredit":
    st.subheader("🏷️ Distribusi Cicilan Kredit per Kategori Produk")
    payment_counts = payments.groupby(["product_category_name", "payment_type"]).size().unstack(fill_value=0)
    dominant_credit_card = payment_counts[(payment_counts["credit_card"] > payment_counts["boleto"]) & (payment_counts["credit_card"] > payment_counts["debit_card"]) & (payment_counts["credit_card"] > payment_counts["voucher"])]
    
    credit_card_transactions = payments[payments["payment_type"] == "credit_card"]
    installments_avg = credit_card_transactions.groupby("product_category_name")["payment_installments"].mean().reset_index()
    installments_avg = installments_avg[installments_avg["product_category_name"].isin(dominant_credit_card.index)]
    installments_avg = installments_avg.sort_values(by="payment_installments", ascending=False)
    
    fig_install, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=installments_avg, x="product_category_name", y="payment_installments", palette="viridis", ax=ax)
    plt.xticks(rotation=90)
    ax.set_title("Rata-rata Cicilan per Kategori Produk")
    st.pyplot(fig_install)