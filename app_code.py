import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np

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

# --- ฟังก์ชันคำนวณ Weekly Volatility ---
def get_weekly_volatility():
    try:
        # ดึงข้อมูลราคาของ BTC ในช่วง 7 วันที่ผ่านมา
        history_api = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7"
        history_data = requests.get(history_api).json()
        # ดึงเฉพาะราคาจากข้อมูลที่ได้ (timestamp, price)
        prices = [price[1] for price in history_data['prices']]
        # คำนวณ return ระหว่างวัน
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        # คำนวณความผันผวนเป็น standard deviation ของ returns แล้วแปลงเป็น %
        volatility = np.std(returns) * 100
    except Exception as e:
        # กรณีมีปัญหาให้ใช้ค่า default 5%
        volatility = 5.0
    return volatility

# --- ตั้งชื่อหน้าเว็บ ---
st.title("BTC Average Cost Calculator")

# --- ส่วนกรอกข้อมูล (Input) ---
st.subheader("ใส่ข้อมูลปัจจุบัน")
current_btc = st.number_input("Current BTC Holdings (จำนวนหน่วย BTC ที่ถืออยู่)", min_value=0.0, value=0.0)
current_invested_usd = st.number_input("Total Invested Amount in $USD (เงินที่ลงทุนไปแล้ว)", min_value=0.0, value=0.0)
new_usd_buy = st.number_input("Budget to Buy more (USD) (จำนวนเงินที่ต้องการซื้อเพิ่ม)", min_value=0.0, value=0.0)
avg_usd_thb = st.number_input("Avg. USD/THB from previous buy (ค่าเฉลี่ย USD/THB เดิม)", min_value=0.0, value=0.0)

# --- ดึงค่า Weekly Volatility มาใช้คำนวณ (ไม่ต้องให้ผู้ใช้ป้อนเอง) ---
weekly_volatility = get_weekly_volatility()
st.subheader("ข้อมูล Volatility")
st.write(f"**Weekly Volatility (คำนวณจากข้อมูล 7 วันที่ผ่านมา):** {weekly_volatility:.2f}%")

# --- คำนวณและแสดงผลเมื่อกดปุ่ม "Calculate" ---
if st.button("Calculate"):
    # ดึงราคาจาก CoinGecko (Real-time BTC Price)
    btc_price_api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    btc_price_data = requests.get(btc_price_api).json()
    btc_price = btc_price_data['bitcoin']['usd']

    # 1) Previous Avg. Buy Price (ต้นทุนเฉลี่ยก่อนหน้า)
    if current_btc == 0:
        previous_avg_price_usd = 0
    else:
        previous_avg_price_usd = current_invested_usd / current_btc

    # 2) New BTC Bought (จำนวน BTC ที่ซื้อใหม่)
    new_btc = new_usd_buy / btc_price if btc_price != 0 else 0

    # 3) Total BTC (BTC รวมหลังซื้อเพิ่ม)
    total_btc = current_btc + new_btc

    # 4) New Total Invested (รวมเงินลงทุนใหม่)
    total_invested_usd = current_invested_usd + new_usd_buy

    # 5) New Average Price (ต้นทุนเฉลี่ยใหม่ USD/BTC)
    if total_btc == 0:
        new_avg_price_usd = 0
    else:
        new_avg_price_usd = total_invested_usd / total_btc

    # 6) Portfolio Value (มูลค่าพอร์ตใหม่)
    new_portfolio_value = total_btc * btc_price

    # 7) Rising % จากต้นทุนเฉลี่ยเดิม
    if previous_avg_price_usd != 0:
        rising_percent = ((new_avg_price_usd - previous_avg_price_usd) / previous_avg_price_usd) * 100
    else:
        rising_percent = 0

    # --- แสดงผลลัพธ์ ---
    st.subheader("ผลการคำนวณ")
    st.write(f"**Real-time BTC Price:** ${btc_price:,.2f}")
    st.write(f"**Previous Avg. Buy Price (ต้นทุนเฉลี่ยเดิม):** ${previous_avg_price_usd:,.2f}/BTC")
    st.write(f"**New BTC Bought (BTC ที่ซื้อเพิ่ม):** {new_btc:.6f} BTC")
    st.write(f"**Total BTC Holdings (BTC รวม):** {total_btc:.6f} BTC")
    st.write(f"**New Average Price (ต้นทุนเฉลี่ยใหม่):** ${new_avg_price_usd:,.2f}/BTC")
    st.write(f"**New Portfolio Value (มูลค่าพอร์ต):** ${new_portfolio_value:,.2f}")
    st.write(f"**Rising % (เทียบต้นทุนเดิม):** {rising_percent:.2f}%")
    
    # --- กราฟเปรียบเทียบราคา (Bar Chart) ---
    df_prices = pd.DataFrame({
        "Price Metric": ["Real-time BTC Price", "Previous Avg. Price", "New Avg. Price"],
        "Price (USD)": [btc_price, previous_avg_price_usd, new_avg_price_usd]
    })
    fig_prices = px.bar(
        df_prices, 
        x="Price Metric", 
        y="Price (USD)", 
        title="เปรียบเทียบราคา BTC",
        text_auto=True
    )
    st.plotly_chart(fig_prices)

    # --- กราฟแสดงสัดส่วน BTC Holdings (Pie Chart) ---
    df_btc = pd.DataFrame({
        "Type": ["Existing BTC", "Newly Bought BTC"],
        "Amount": [current_btc, new_btc]
    })
    fig_btc = px.pie(
        df_btc, 
        values="Amount", 
        names="Type", 
        title="สัดส่วน BTC Holdings"
    )
    st.plotly_chart(fig_btc)
    
    # --- แนะนำ Entry Point โดยใช้ Weekly Volatility ---
    st.subheader("แนะนำจุดเข้าซื้อ (Entry Price Range)")
    # คำนวณ Range จุดเข้าซื้อโดยใช้ weekly_volatility ที่คำนวณได้
    low_entry = btc_price * (1 - weekly_volatility/100)
    high_entry = btc_price * (1 + weekly_volatility/100)
    
    st.write(f"จากราคาปัจจุบันที่ ${btc_price:,.2f}")
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

    fig_sim = px.line(
        df_sim, 
        x="Additional Investment (USD)", 
        y=["New Average Price (USD/BTC)", "Portfolio Value (USD)"],
        title="ผลกระทบของการลงทุนเพิ่มเติม",
        labels={"value": "ค่า (USD)", "variable": "ตัวชี้วัด"}
    )
    st.plotly_chart(fig_sim)
