import streamlit as st
import random
import pandas as pd
import numpy as np
import os
import json

st.set_page_config(page_title="班级座位分组可视化", page_icon="🎨", layout="wide")

st.title("🎨 七林2025级(6)班 智能座位分组可视化(完整保存+回溯版)")
st.markdown("""
**图例说明：**
* **色块**：同属一个小组（绑定组名，方便观察轮换轨迹）。
* **布局**：分为左岛(列1-2)、中岛(列3-5)、右岛(列6-7)。严禁小组跨越走道分割！
* **断点续传与历史**：你在这周生成的座位（含随机微调）会被永久记录。调整左侧【当前周期】不仅可以翻看过去的记录，还能以此为基础生成新周的图。
""")

HISTORY_FILE = "seat_history.json"

# ==========================================
# 数据加载与历史存取模块 
# ==========================================
def load_default_groups_text():
    file_path = "groups.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """第1组(9人): 陈嘉扬, 陈可凡, 陈昕睿, 陈亚熙, 付亦深, 何旻峰, 何知热, 黄理懿, 黄钰焮
第2组(9人): 康小伍, 李荣耀, 李彦霖, 梁徐琪山, 林子杰, 栾一淳, 罗传海, 明朗, 欧计嘉
第3组(8人): 宋靖轩, 万谦, 王渤然, 吴浩宇, 肖万雄, 肖语轩, 徐靖轩, 许铭祎
第4组(8人): 杨峻熙, 杨林果, 袁睿, 张乐涵, 张拾唯, 章翊轩, 赵雨翔, 郑云升
第5组(8人): 钟达川, 周家阳, 周于翔, 周子杰, 陈锦萱, 杜蔓霖, 何紫瑞, 李姿逸
第6组(8人): 刘柏影, 刘思岑, 罗晨溪, 王可昕, 王星妙, 韦妙, 魏峨娇, 温雅歆
第7组(8人): 吴家萱, 吴昕睿, 习芷晗, 向茹悕, 杨轶之, 张思纳, 张桐颖, 赵思琪"""

def parse_group_text(text):
    groups = []
    # 提前定义好颜色库
    group_colors = ['#FFCDD2', '#BBDEFB', '#C8E6C9', '#FFF9C4', '#E1BEE7', '#FFE0B2', '#B2DFDB']
    
    lines = text.strip().split('\n')
    idx = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ':' in line or '：' in line:
            line = line.replace('：', ':')
            group_name, members_str = line.split(':', 1)
            members_str = members_str.replace('，', ',')
            members = [m.strip() for m in members_str.split(',') if m.strip()]
            
            groups.append({
                'name': group_name.strip(),
                'members': members,
                'size': len(members),
                # 🌟 修版重点：在初始解析时就把颜色烙印在字典属性中
                'bound_color': group_colors[idx % len(group_colors)]
            })
            idx += 1
    return groups

def load_all_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_all_history(history_dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_dict, f, ensure_ascii=False, indent=2)

# ==========================================
# 核心分配逻辑
# ==========================================
class SeatAllocator:
    def __init__(self):
        path = []
        for r in range(9):
            if r % 2 == 0: path.extend([(r,0), (r,1)])
            else: path.extend([(r,1), (r,0)])
                
        for r in range(7, -1, -1):
            if r % 2 == 0: path.extend([(r,2), (r,3), (r,4)])
            else: path.extend([(r,4), (r,3), (r,2)])
                
        for r in range(8):
            if r % 2 == 0: path.extend([(r,5), (r,6)])
            else: path.extend([(r,6), (r,5)])
            
        self.seat_path = path

    def direct_render_from_data(self, specific_groups_data):
        seat_info = {}
        current_idx = 0
        
        for group in specific_groups_data:
            # 🌟 修复重点：不再通过索引算颜色，直接读取固定的 bound_color
            color = group.get('bound_color', '#FFFFFF') 
            size = group['size']
            members = group['members']
            
            my_seats = self.seat_path[current_idx : current_idx + size]
            current_idx += size
            
            for seat, member in zip(my_seats, members):
                seat_info[seat] = {
                    'name': member,
                    'color': color,
                    'group': group['name']
                }
        return seat_info

    def generate_next_week(self, previous_groups_data):
        new_groups_data = []
        
        offset = 1 % len(previous_groups_data)
        rotated_groups = previous_groups_data[-offset:] + previous_groups_data[:-offset] if offset != 0 else previous_groups_data
        
        for group in rotated_groups:
            size = group['size']
            members = group['members'].copy()
            # 🌟 修复重点：颜色属性必须要往下传承
            bound_color = group.get('bound_color', '#FFFFFF')
            
            inner_offset = 3 % size
            if inner_offset != 0:
                members = members[-inner_offset:] + members[:-inner_offset]
            
            for _ in range(max(1, size // 3)):  
                idx1 = random.randint(0, size - 1)
                idx2 = random.randint(0, size - 1)
                members[idx1], members[idx2] = members[idx2], members[idx1]
                
            new_groups_data.append({
                'name': group['name'],
                'size': size,
                'members': members,
                'bound_color': bound_color # 传给新的一期
            })
            
        return new_groups_data

# ==========================================
# 提取渲染功能
# ==========================================
def render_seat_chart(result_map):
    display_data = np.full((9, 7), "", dtype=object)
    color_data = np.full((9, 7), "background-color: #ffffff", dtype=object) 

    for r in range(9):
        for c in range(7):
            base_style = "color: black; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;"
            if c == 1: base_style += " border-right: 4px solid #666;"
            elif c == 2: base_style += " border-left: 4px solid #666;"
            elif c == 4: base_style += " border-right: 4px solid #666;"
            elif c == 5: base_style += " border-left: 4px solid #666;"
            color_data[r, c] = base_style

    for (r, c), info in result_map.items():
        display_data[r, c] = info['name']
        color_data[r, c] += f" background-color: {info['color']};"

    cols = [f"第{i+1}列" for i in range(7)]
    rows = [f"第{i+1}排" for i in range(9)]
    df = pd.DataFrame(display_data, columns=cols, index=rows)

    def style_apply(x):
        return pd.DataFrame(color_data, index=x.index, columns=x.columns)

    st.dataframe(df.style.apply(style_apply, axis=None), use_container_width=True, height=400)


# ==========================================
# UI 控制与运行
# ==========================================
default_text = load_default_groups_text()
history_db = load_all_history()  

with st.sidebar:
    st.header("⚙️ 班级数据")
    
    if len(history_db) > 0:
        st.success(f"✅ 系统检测到截止目前最高排至 **第 {len(history_db)} 周**。")
        use_history = st.checkbox("从最新存档提取历史接力运算？", value=True)
    else:
        st.info("尚无本地存档，以纯净的初始状态排座。")
        use_history = False

    uploaded_groups_text = st.text_area("预设分组名单 (仅清除存档并重算第1周时有效)", value=default_text, height=350)
    
    st.markdown("---")
    st.header("🔄 轮换与历史记录提取")  
    max_week = len(history_db) if len(history_db) > 0 else 1
    target_week = st.number_input("⏳ 目标要查看/生成的周次", min_value=1, value=max_week, step=1)
    
    history_options = ["全部", "前5周", "前10周", "不显示"]
    history_limit = st.selectbox("📜 显示生成结果的过往周次缩影", options=history_options, index=0)
    
    if st.button("🧹 抹除并重置全部历史记录(危险)"):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            st.rerun()

if st.button("🎲 生成交替座位图 / 读取该周存档", type="primary"):
    parsed_groups = parse_group_text(uploaded_groups_text)
    allocator = SeatAllocator()
    
    week_str = str(target_week)
    final_data_to_render = None
    
    if week_str in history_db and use_history:
        st.success("这是提取出存盘的老记录，非新生成。")
        final_data_to_render = history_db[week_str]
        
    else:
        prev_week_str = str(target_week - 1)
        
        if prev_week_str in history_db and use_history:
            st.info(f"提取上周进度（第 {prev_week_str} 周）...在此基础上轮转换座并加入洗牌。")
            final_data_to_render = allocator.generate_next_week(history_db[prev_week_str])
        else:
            st.warning("基于左侧全新名单生成（不具时间接力）。")
            parsed_groups_with_size = parsed_groups
            for g in parsed_groups_with_size:
                size = g['size']
                for _ in range(max(1, size // 3)):  
                    idx1 = random.randint(0, size - 1)
                    idx2 = random.randint(0, size - 1)
                    g['members'][idx1], g['members'][idx2] = g['members'][idx2], g['members'][idx1]
            final_data_to_render = parsed_groups_with_size
            
        history_db[week_str] = final_data_to_render
        save_all_history(history_db)

    # =============== 画图部分 ===============
    st.write(f"### 🎯 讲台 (FRONT) - 第 {target_week} 周")
    result_map = allocator.direct_render_from_data(final_data_to_render)
    render_seat_chart(result_map)
    
    if history_limit != "不显示" and target_week > 1:
        st.markdown("---")
        st.write("### 📜 历史座位表回顾 (倒序)")
        
        if history_limit == "全部":
            limit_num = target_week - 1
        else:
            limit_num = int(history_limit.replace("前", "").replace("周", ""))
        
        actual_limit = min(limit_num, target_week - 1)
        
        for past_w in range(target_week - 1, target_week - 1 - actual_limit, -1):
            pw_str = str(past_w)
            if pw_str in history_db:
                st.write(f"#### 🔙 第 {past_w} 周的历史座位")
                past_result = allocator.direct_render_from_data(history_db[pw_str])
                render_seat_chart(past_result)