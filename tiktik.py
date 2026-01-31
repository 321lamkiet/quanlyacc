import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH & AUTH
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASS = "mmo888"  # <--- Đổi pass ở đây
DATA_FILE = 'tiktok_farm_v2.json'

st.set_page_config(page_title="TikTok Farm Pro", page_icon="🚀", layout="wide")

# ==========================================
# BACKEND: XỬ LÝ DỮ LIỆU
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        # Dữ liệu mẫu phong phú hơn cho bản Pro
        data = [
            {
                "id": "iPhone 7-A",
                "status": "Live",
                "username": "user_us_01",
                "niche": "Health", # Chủ đề
                "country": "US",
                "proxy_ip": "192.168.1.10",
                "proxy_exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                "views": 1500,
                "gmv": 12.5,
                "last_active": "2023-10-25"
            },
            {
                "id": "iPhone 8-B",
                "status": "Shadowban",
                "username": "user_fr_09",
                "niche": "Gadget",
                "country": "FR",
                "proxy_ip": "10.0.0.5",
                "proxy_exp": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                "views": 200,
                "gmv": 0.0,
                "last_active": "2023-10-24"
            }
        ]
        save_data(data)
        return data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# AUTHENTICATION
# ==========================================
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.title("🔒 Farm Manager Pro")
            with st.form("login"):
                u = st.text_input("User")
                p = st.text_input("Pass", type="password")
                if st.form_submit_button("Login"):
                    if u == ADMIN_USER and p == ADMIN_PASS:
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Sai thông tin!")
        return False
    return True

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
def main_app():
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Menu")
        menu = st.radio("Chọn chức năng:", ["Dashboard Tổng quan", "Quản lý Account (Table)", "Thêm Account Mới"])
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()

    data_list = load_data()
    df = pd.DataFrame(data_list)

    # --- TAB 1: DASHBOARD ---
    if menu == "Dashboard Tổng quan":
        st.title("🚀 Tổng quan hiệu suất Farm")
        
        # Metrics hàng trên
        total_acc = len(df)
        live_acc = len(df[df['status'] == 'Live'])
        total_gmv = df['gmv'].sum() if 'gmv' in df.columns else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Acc", total_acc)
        c2.metric("Acc Live", live_acc, delta=f"{live_acc/total_acc*100:.0f}%")
        c3.metric("Acc Die/Shadow", total_acc - live_acc, delta_color="inverse")
        c4.metric("Tổng GMV (Doanh thu)", f"${total_gmv}", delta="Hôm nay")

        st.divider()
        
        # Cảnh báo Proxy
        st.subheader("⚠️ Cảnh báo cần xử lý ngay")
        today = datetime.now().date()
        warnings = []
        for acc in data_list:
            try:
                exp_date = datetime.strptime(acc['proxy_exp'], '%Y-%m-%d').date()
                days_left = (exp_date - today).days
                if days_left <= 3:
                    warnings.append(f"🔴 **{acc['id']}** ({acc['username']}): Proxy còn {days_left} ngày!")
            except:
                warnings.append(f"⚪ **{acc['id']}**: Lỗi định dạng ngày Proxy")
        
        if warnings:
            for w in warnings: st.write(w)
        else:
            st.success("Hệ thống ổn định, không có cảnh báo.")

    # --- TAB 2: QUẢN LÝ ACCOUNT (EDITOR) ---
    elif menu == "Quản lý Account (Table)":
        st.title("📱 Danh sách & Trạng thái")
        
        # Bộ lọc nhanh
        col_f1, col_f2 = st.columns(2)
        filter_status = col_f1.multiselect("Lọc theo trạng thái:", ["Live", "Shadowban", "Die", "Nuôi"], default=[])
        search_txt = col_f2.text_input("Tìm kiếm (ID hoặc User):")
        
        # Filter Dataframe
        df_show = df.copy()
        if filter_status:
            df_show = df_show[df_show['status'].isin(filter_status)]
        if search_txt:
            df_show = df_show[df_show['id'].str.contains(search_txt, case=False) | df_show['username'].str.contains(search_txt, case=False)]

        # EDITABLE DATAFRAME (Tính năng đáng tiền nhất)
        st.info("💡 Mẹo: Bạn có thể sửa trực tiếp Status, GMV, Views ngay trong bảng dưới đây rồi nhấn Save.")
        
        edited_df = st.data_editor(
            df_show,
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Trạng thái",
                    options=["Live", "Shadowban", "Die", "Nuôi", "Kháng"],
                    required=True,
                ),
                "gmv": st.column_config.NumberColumn(
                    "Doanh thu ($)",
                    format="$%.2f",
                ),
                "views": st.column_config.NumberColumn(
                    "Views",
                    format="%d",
                ),
                "proxy_exp": st.column_config.DateColumn("Hết hạn Proxy"),
                "id": "Tên máy",
                "username": "User TikTok"
            },
            hide_index=True,
            num_rows="dynamic", # Cho phép thêm/xóa hàng
            use_container_width=True
        )

        # Nút Save Data
        if st.button("Lưu thay đổi (Save Changes)", type="primary"):
            # Chuyển đổi format date về string để lưu JSON
            saved_data = edited_df.to_dict(orient='records')
            # Format lại date thành string vì data_editor trả về object date
            for item in saved_data:
                if isinstance(item['proxy_exp'], (datetime, pd.Timestamp)):
                     item['proxy_exp'] = item['proxy_exp'].strftime('%Y-%m-%d')
                if hasattr(item['proxy_exp'], 'strftime'): # Check kỹ hơn
                     item['proxy_exp'] = item['proxy_exp'].strftime('%Y-%m-%d')
                else:
                    item['proxy_exp'] = str(item['proxy_exp'])

            # Logic merge dữ liệu (để giữ lại những dòng bị ẩn do filter)
            # Ở đây làm đơn giản: Load lại data gốc, update những dòng có ID trùng, giữ nguyên dòng ẩn
            full_data = load_data()
            full_map = {item['id']: item for item in full_data}
            
            for new_item in saved_data:
                full_map[new_item['id']] = new_item
            
            # Xử lý xóa: Nếu user xóa dòng trong bảng edited, ta cần detect
            # (Phần này hơi phức tạp với data_editor, tạm thời dùng cơ chế update)
            
            save_data(list(full_map.values()))
            st.success("Đã cập nhật dữ liệu thành công!")
            st.rerun()

    # --- TAB 3: THÊM ACCOUNT MỚI ---
    elif menu == "Thêm Account Mới":
        st.title("➕ Thêm thiết bị vào Farm")
        with st.form("add_acc_form"):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Tên máy (Ví dụ: iPhone X-01)", placeholder="iPhone...")
            new_user = c2.text_input("Username TikTok")
            
            c3, c4 = st.columns(2)
            new_niche = c3.selectbox("Chủ đề (Niche)", ["Gia dụng", "Mỹ phẩm", "Thời trang", "Sức khỏe", "Giải trí", "Khác"])
            new_country = c4.selectbox("Quốc gia", ["US", "UK", "FR", "DE", "VN"])
            
            c5, c6 = st.columns(2)
            new_ip = c5.text_input("Proxy IP:Port")
            new_exp = c6.date_input("Ngày hết hạn Proxy")
            
            if st.form_submit_button("Thêm Account"):
                if new_id and new_user:
                    new_record = {
                        "id": new_id,
                        "status": "Nuôi", # Mặc định mới thêm là đang nuôi
                        "username": new_user,
                        "niche": new_niche,
                        "country": new_country,
                        "proxy_ip": new_ip,
                        "proxy_exp": new_exp.strftime('%Y-%m-%d'),
                        "views": 0,
                        "gmv": 0.0,
                        "last_active": datetime.now().strftime('%Y-%m-%d')
                    }
                    current_data = load_data()
                    current_data.append(new_record)
                    save_data(current_data)
                    st.success(f"Đã thêm {new_id} thành công!")
                else:
                    st.warning("Vui lòng nhập Tên máy và Username")

if __name__ == "__main__":
    if check_login():
        main_app()
