import streamlit as st
import requests

# ตั้งชื่อ/หัวข้อให้หน้าเว็บ
st.title("BTC Average Cost Calculator")

# ส่วนกรอกข้อมูล (Input)
st.subheader("ใส่ข้อมูลปัจจุบัน")
current_btc = st.number_input("Current BTC Holdings (จำนวนหน่วย BTC ที่ถืออยู่)", min_value=0.0, value=0.0)
current_invested_usd = st.number_input("Total Invested Amount in $USD (เงินที่ลงทุนไปแล้ว)", min_value=0.0, value=0.0)
new_usd_buy = st.number_input("Budget to Buy more (USD) (จำนวนเงินที่ต้องการซื้อเพิ่ม)", min_value=0.0, value=0.0)
avg_usd_thb = st.number_input("Avg. USD/THB from previous buy (ค่าเฉลี่ย USD/THB เดิม)", min_value=0.0, value=0.0)

# เมื่อกดปุ่ม "Calculate" ให้ทำงานคำนวณทั้งหมด
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

    # แสดงผลลัพธ์
    st.subheader("ผลการคำนวณ")
    st.write(f"**Real-time BTC Price:** ${btc_price:,.2f}")
    st.write(f"**Previous Avg. Buy Price (ต้นทุนเฉลี่ยเดิม):** ${previous_avg_price_usd:,.2f}/BTC")
    st.write(f"**New BTC Bought (BTC ที่ซื้อเพิ่ม):** {new_btc:.6f} BTC")
    st.write(f"**Total BTC Holdings (BTC รวม):** {total_btc:.6f} BTC")
    st.write(f"**New Average Price (ต้นทุนเฉลี่ยใหม่):** ${new_avg_price_usd:,.2f}/BTC")
    st.write(f"**New Portfolio Value (มูลค่าพอร์ต):** ${new_portfolio_value:,.2f}")
    st.write(f"**Rising % (เทียบต้นทุนเดิม):** {rising_percent:.2f}%")
