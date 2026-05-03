import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 0. แทรก CSS ตกแต่งหน้าตา (UI Customization)
# ==========================================
st.set_page_config(page_title="DTP BESS Set Point Calculator_By PHU", layout="wide")

st.markdown("""
<style>
/* บังคับช่อง Number Input ให้พื้นเหลือง ตัวหนังสือดำชัดเจน */
div[data-testid="stNumberInputContainer"] {
    background-color: #FFD700 !important;
    border-radius: 6px;
}
input[type="number"] {
    background-color: #FFD700 !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 22px !important;
    -webkit-text-fill-color: #000000 !important; 
}
/* เปลี่ยนสีปุ่ม +/- ในช่องให้เป็นสีดำ */
button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. การตั้งค่าตัวแปรพื้นฐาน
# ==========================================
TOTAL_BESS_CAPACITY = 93.568    # Capacity รวมทั้งหมดของแพลนต์ (9*10.03 + 3.298)
EFFICIENCY = 0.98             # Efficiency factor 
T2_HOURS = 2.0                

st.title("🔋 DTP Partial Firm PPA (T2) : MW Set Point Calculation By Phu")
st.markdown("Web App สำหรับคำนวณการตั้งค่าจ่ายแบตเตอรี่ (MW Set point) ในช่วง Partial Firm PPA (T2)")

# ==========================================
# 2. ส่วนเลือก Station ที่พร้อมใช้งาน
# ==========================================
st.markdown("**เลือก Station ที่พร้อมใช้งาน (Availability)**")
col_st1, col_st2, col_st3, col_st4, col_st5 = st.columns(5)
col_st6, col_st7, col_st8, col_st9, col_st10 = st.columns(5)

with col_st1: st_1 = st.checkbox("Station 1 (10.03 MWh)", value=True)
with col_st2: st_2 = st.checkbox("Station 2 (10.03 MWh)", value=True)
with col_st3: st_3 = st.checkbox("Station 3 (10.03 MWh)", value=True)
with col_st4: st_4 = st.checkbox("Station 4 (10.03 MWh)", value=True)
with col_st5: st_5 = st.checkbox("Station 5 (10.03 MWh)", value=True)

with col_st6: st_6 = st.checkbox("Station 6 (10.03 MWh)", value=True)
with col_st7: st_7 = st.checkbox("Station 7 (10.03 MWh)", value=True)
with col_st8: st_8 = st.checkbox("Station 8 (10.03 MWh)", value=True)
with col_st9: st_9 = st.checkbox("Station 9 (10.03 MWh)", value=True)
with col_st10: st_10 = st.checkbox("Station 10 (3.298 MWh)", value=True)

# คำนวณ Capacity เฉพาะ Station ที่ใช้งานได้ (Active)
stations_status = [st_1, st_2, st_3, st_4, st_5, st_6, st_7, st_8, st_9, st_10]
active_capacity_mwh = sum([10.03 if status else 0.0 for status in stations_status[:9]])
active_capacity_mwh += 3.298 if st_10 else 0.0

st.info(f"⚡ **Total ACTIVE BESS Capacity: {active_capacity_mwh:.1f} MWh** (จากทั้งหมด {TOTAL_BESS_CAPACITY} MWh)")
st.divider()

# ==========================================
# 3. ส่วนรับข้อมูล (Input)
# ==========================================
st.subheader("📝 Input Data (อ่านค่าจากระบบรวม)")
col1, col2, col3 = st.columns(3)
with col1:
    total_bess_dischargeable = st.number_input(
        "Total BESS Dischargeable (MWh) - ค่าจาก SUNGROW", 
        min_value=0.0, max_value=float(TOTAL_BESS_CAPACITY), 
        value=min(87.00, float(TOTAL_BESS_CAPACITY)), step=0.1
    )
with col2:
    target_soc_percent = st.number_input(
        "Target Remaining SOC (%)", 
        min_value=0.0, max_value=100.0, value=8.0, step=1.0
    )
with col3:
    is_holiday = st.checkbox("Supply House Load Via SST02?", value=True)
    house_load_mwh = 1.0 if is_holiday else 0.0
    st.caption(f"*Current House Load = {house_load_mwh} MWh")

# ==========================================
# 4. ลอจิกการคำนวณ (Corrected Physics Logic)
# ==========================================
current_soc_percent = (total_bess_dischargeable / TOTAL_BESS_CAPACITY) * 100.0
active_initial_mwh = active_capacity_mwh * (current_soc_percent / 100.0)
active_reserved_mwh = active_capacity_mwh * (target_soc_percent / 100.0)

dc_dischargeable_mwh = active_initial_mwh - active_reserved_mwh

if dc_dischargeable_mwh > 0:
    ac_dischargeable_mwh = dc_dischargeable_mwh * EFFICIENCY
    usable_mwh = ac_dischargeable_mwh - house_load_mwh
    t2_set_point_mw = usable_mwh / T2_HOURS if usable_mwh > 0 else 0.0
else:
    dc_dischargeable_mwh = 0.0
    ac_dischargeable_mwh = 0.0
    usable_mwh = 0.0
    t2_set_point_mw = 0.0

# ==========================================
# 5. ส่วนแสดงผลลัพธ์
# ==========================================
st.divider()
st.subheader("🎯 Result: คำแนะนำการตั้งค่า")

result_col1, result_col2 = st.columns(2)

with result_col1:
    # พื้นหลังสีฟ้า (#0066cc) ตัวหนังสือสีขาว
    st.markdown(f"""
    <div style="background-color: #0066cc; padding: 30px; border-radius: 12px; text-align: center; border: 2px solid #3399ff; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <h3 style="color: #FFFFFF; margin-top: 0; font-weight: normal;">🧊 ปรับค่า T2 MW Set point ไปที่ 🧊</h3>
        <h1 style="color: #FFFFFF; font-size: 70px; margin: 5px 0; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{t2_set_point_mw:.2f} <span style="font-size: 30px; font-weight: normal;">MW</span></h1>
    </div>
    """, unsafe_allow_html=True)
    
    # === ส่วนที่เพิ่มกลับมา แบ่งเป็น 2 คอลัมน์ย่อย ===
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric(label="Current Plant SOC (%)", value=f"{current_soc_percent:.2f} %")
    with m_col2:
        st.metric(label="SOC ที่จะเหลือหลังจบ T2", value=f"{target_soc_percent:.2f} %", delta=f"{active_reserved_mwh:.2f} MWh", delta_color="off")
    # ==========================================

    st.caption(f"**สมการ (Physical):**\n1. ดึงพลังงาน Active ({active_initial_mwh:.2f}) หักกั๊ก ({active_reserved_mwh:.2f}) = ยอดดิบ DC {dc_dischargeable_mwh:.2f} MWh\n2. แปลงเป็น AC หัก Loss ({dc_dischargeable_mwh:.2f} * {EFFICIENCY}) - Load ({house_load_mwh}) / {T2_HOURS} ชม.")

with result_col2:
    fig = go.Figure(go.Waterfall(
        name="Energy Balance",
        orientation="v",
        measure=["absolute", "relative", "total", "relative", "relative", "total"],
        x=["Active Initial", f"Reserve ({target_soc_percent}%)", "DC Discharge", "Efficiency Loss", "House Load", "Available for T2"],
        textposition="outside",
        text=[
            f"{active_initial_mwh:.2f}", 
            f"-{active_reserved_mwh:.2f}", 
            f"{dc_dischargeable_mwh:.2f}",
            f"-{dc_dischargeable_mwh * (1-EFFICIENCY):.2f}", 
            f"-{house_load_mwh}", 
            f"{usable_mwh:.2f}"
        ],
        y=[
            active_initial_mwh, 
            -active_reserved_mwh, 
            dc_dischargeable_mwh,
            -(dc_dischargeable_mwh * (1-EFFICIENCY)), 
            -house_load_mwh, 
            usable_mwh
        ],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#EF553B"}},
        increasing={"marker": {"color": "#00CC96"}},
        totals={"marker": {"color": "#0066cc"}}
    ))
    
    fig.update_layout(
        title="BESS Energy Balance (MWh) - Active Stations Only",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="Energy (MWh)",
        margin=dict(t=40, b=40, l=40, r=40) 
    )
    st.plotly_chart(fig, use_container_width=True)