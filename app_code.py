import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np
import yfinance as yf
from sklearn.cluster import KMeans

# --- Google Analytics Integration ---
GA_SCRIPT = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MBDK43KS67"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-MBDK43KS67');
</script>
"""
st.components.v1.html(GA_SCRIPT, height=0, scrolling=False)

# --- ฟังก์ชันคำนวณ Volatility จาก Yahoo Finance ---
def get_volatility(period, ticker="BTC-USD", interval="1d"):
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data.empty:
        return None
    prices = data['Close'].values.flatten()
    if len(prices) < 2:
        return None
    # คำนวณ daily returns
    returns = np.diff(prices) / prices[:-1]
    # คำนวณ volatility โดยใช้ standard deviation ของ returns แล้วแปลงเป็น %
    volatility = np.std(returns) * 100
    return volatility

# --- ตั้งชื่อหน้าเว็บ ---
st.title("BTC Average Cost Calculator")

# --- ส่วนกรอกข้อมูล (Input) ---
st.subheader("ใส่ข้อมูลปัจจุบัน")
current_btc = st.number_input("Current BTC Holdings (จำนวนหน่วย BTC ที่ถืออยู่)", min_value=0.0, value=0.0)
current_invested_usd = st.number_input("Total Invested Amount in $USD (เงินที่ลงทุนไปแล้ว)", min_value=0.0, value=0.0)
new_usd_buy = st.number_input("Budget to Buy more (USD) (จำนวนเงินที่ต้องการซื้อเพิ่ม)", min_value=0.0, value=0.0)
avg_usd_thb = st.number_input("Avg. USD/THB from previous buy (ค่าเฉลี่ย USD/THB เดิม)", min_value=0.0, value=0.0)

# --- ดึงข้อมูล Volatility จาก Yahoo Finance ---
st.subheader("ข้อมูล Volatility จาก Yahoo Finance")
weekly_volatility = get_volatility("7d")
monthly_volatility = get_volatility("30d")

if weekly_volatility is None:
    st.write("ไม่สามารถดึงข้อมูล Weekly Volatility ได้")
else:
    st.write(f"**Weekly Volatility (7 days):** {weekly_volatility:.2f}%")
    
if monthly_volatility is None:
    st.write("ไม่สามารถดึงข้อมูล Monthly Volatility ได้")
else:
    st.write(f"**Monthly Volatility (30 days):** {monthly_volatility:.2f}%")

# --- คำนวณและแสดงผลเมื่อกดปุ่ม "Calculate" ---
if st.button("Calculate"):
    # ดึงราคาจาก CoinGecko พร้อมตรวจสอบข้อมูล
    btc_price_api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    btc_price_data = requests.get(btc_price_api).json()
    if 'bitcoin' in btc_price_data and 'usd' in btc_price_data['bitcoin']:
        btc_price = btc_price_data['bitcoin']['usd']
    else:
        st.error("Error: Could not retrieve BTC price from API. Please try again later.")
        st.stop()
    
    # --- คำนวณ BTC Portfolio ---
    previous_avg_price_usd = current_invested_usd / current_btc if current_btc != 0 else 0
    new_btc = new_usd_buy / btc_price if btc_price != 0 else 0
    total_btc = current_btc + new_btc
    total_invested_usd = current_invested_usd + new_usd_buy
    new_avg_price_usd = total_invested_usd / total_btc if total_btc != 0 else 0
    new_portfolio_value = total_btc * btc_price
    rising_percent = ((new_avg_price_usd - previous_avg_price_usd) / previous_avg_price_usd * 100
                      if previous_avg_price_usd != 0 else 0)
    
    # --- แสดงผลการคำนวณ ---
    st.subheader("ผลการคำนวณ")
    st.write(f"**Real-time BTC Price:** ${btc_price:,.2f}")
    st.write(f"**Previous Avg. Buy Price:** ${previous_avg_price_usd:,.2f}/BTC")
    st.write(f"**New BTC Bought:** {new_btc:.6f} BTC")
    st.write(f"**Total BTC Holdings:** {total_btc:.6f} BTC")
    st.write(f"**New Average Price:** ${new_avg_price_usd:,.2f}/BTC")
    st.write(f"**New Portfolio Value:** ${new_portfolio_value:,.2f}")
    st.write(f"**Rising %:** {rising_percent:.2f}%")
    
    # --- กราฟเปรียบเทียบราคา (Bar Chart) ---
    df_prices = pd.DataFrame({
        "Price Metric": ["Real-time BTC Price", "Previous Avg. Price", "New Avg. Price"],
        "Price (USD)": [btc_price, previous_avg_price_usd, new_avg_price_usd]
    })
    fig_prices = px.bar(df_prices, x="Price Metric", y="Price (USD)", 
                        title="เปรียบเทียบราคา BTC", text_auto=True)
    st.plotly_chart(fig_prices)
    
    # --- กราฟแสดงสัดส่วน BTC Holdings (Pie Chart) ---
    df_btc = pd.DataFrame({
        "Type": ["Existing BTC", "Newly Bought BTC"],
        "Amount": [current_btc, new_btc]
    })
    fig_btc = px.pie(df_btc, values="Amount", names="Type", title="สัดส่วน BTC Holdings")
    st.plotly_chart(fig_btc)
    
    # --- แนะนำ Entry Point โดยใช้ข้อมูล Volatility ---
    st.subheader("แนะนำจุดเข้าซื้อ (Entry Price Range)")
    # ใช้ Weekly Volatility สำหรับการคำนวณ Entry Range หากมีข้อมูล ถ้าไม่มีก็ใช้ค่า default 5%
    used_volatility = weekly_volatility if weekly_volatility is not None else 5.0
    low_entry = btc_price * (1 - used_volatility/100)
    high_entry = btc_price * (1 + used_volatility/100)
    st.write(f"จากราคาปัจจุบันที่ ${btc_price:,.2f} โดยใช้ **Weekly Volatility** {used_volatility:.2f}%")
    st.write(f"แนะนำให้พิจารณาจุดเข้าซื้อในช่วง: **${low_entry:,.2f} - ${high_entry:,.2f}**")
    
    # --- แสดงกราฟ Entry Range ด้วย Plotly ---
    df_zone = pd.DataFrame({
        "Price": [low_entry, btc_price, high_entry],
        "Zone": ["Lower Bound", "Current Price", "Upper Bound"]
    })
    fig_zone = px.scatter(df_zone, x="Price", y=["Zone"],
                          title="Recommended Entry Price Range",
                          labels={"Price": "Price (USD)", "value": "Zone"})
    fig_zone.add_shape(
        type="rect",
        x0=low_entry, y0=-0.5, x1=high_entry, y1=0.5,
        fillcolor="LightSalmon", opacity=0.3, line_width=0
    )
    st.plotly_chart(fig_zone)
    
    # --- กราฟ Sensitivity Analysis ---
    investment_range = np.linspace(0, new_usd_buy * 2, 50)
    new_avg_prices = []
    portfolio_values = []

    for additional_investment in investment_range:
        total_invested_sim = current_invested_usd + additional_investment
        new_btc_sim = additional_investment / btc_price if btc_price != 0 else 0
        total_btc_sim = current_btc + new_btc_sim
        new_avg_price_sim = total_invested_sim / total_btc_sim if total_btc_sim != 0 else 0
        portfolio_value_sim = total_btc_sim * btc_price
        new_avg_prices.append(new_avg_price_sim)
        portfolio_values.append(portfolio_value_sim)
    
    df_sim = pd.DataFrame({
        "Additional Investment (USD)": investment_range,
        "New Average Price (USD/BTC)": new_avg_prices,
        "Portfolio Value (USD)": portfolio_values
    })

    fig_sim = px.line(df_sim, x="Additional Investment (USD)", 
                      y=["New Average Price (USD/BTC)", "Portfolio Value (USD)"],
                      title="ผลกระทบของการลงทุนเพิ่มเติม",
                      labels={"value": "ค่า (USD)", "variable": "ตัวชี้วัด"})
    st.plotly_chart(fig_sim)
    
    # --- Price Cluster Analysis ---
    st.subheader("Price Cluster Analysis (30-day)")
    # ดึงข้อมูลราคาประวัติศาสตร์ 30 วันสำหรับการ clustering
    data_cluster = yf.download("BTC-USD", period="30d", interval="1d", progress=False)
    if not data_cluster.empty:
        prices_cluster = data_cluster['Close'].values.reshape(-1, 1)
        # ใช้ KMeans แบ่งข้อมูลออกเป็น 3 กลุ่ม (สามารถปรับจำนวนกลุ่มได้)
        n_clusters = 3
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(prices_cluster)
        cluster_centers = kmeans.cluster_centers_.flatten()
        labels = kmeans.labels_
        
        # สร้าง DataFrame สำหรับ Plot
        df_cluster = pd.DataFrame({
            "Date": data_cluster.index,
            "Close": data_cluster['Close'],
            "Cluster": labels
        })
        
        fig_cluster = px.scatter(df_cluster, x="Date", y="Close", color="Cluster", 
                                 title="Historical Price Clusters (30 days)")
        # แสดง cluster centers เป็นเส้นแนวนอน
        for center in cluster_centers:
            fig_cluster.add_hline(y=center, line_dash="dash", line_color="red",
                                    annotation_text=f"Cluster Center: {center:.2f}", annotation_position="top left")
        st.plotly_chart(fig_cluster)
    else:
        st.write("ไม่สามารถดึงข้อมูลสำหรับ Price Clustering ได้")
