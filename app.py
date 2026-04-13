import streamlit as st
import random
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="班级座位分组可视化", page_icon="🎨", layout="wide")

st.title("🎨 七林2025级(6)班 智能座位分组可视化(预设轮换版)")
st.markdown("""
**图例说明：**
*   **色块**：同一种背景颜色的同学属于同一个小组。
*   **布局**：分为左岛(列1-2)、中岛(列3-5)、右岛(列6-7)。严禁小组跨越走道分割！
*   **轮换**：左侧改变【轮换周期】，小组可以在不同排、不同岛屿平滑移位，同时保持组员聚集。
""")

# ==========================================
# 加载或生成默认分组名单
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
    lines = text.strip().split('\n')
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
                'size': len(members)
            })
    return groups

# ==========================================
# 核心逻辑
# ==========================================
class SeatAllocator:
    def __init__(self):
        # 🌟 核心改进：遵循物理走道的孤岛贪吃蛇路线 🌟
        # 路线总共 58 个座位，确保每一段切出来的连续区间，不会跨越两个岛！
        
        path = []
        
        # 【左岛】 (列0和列1): 9排, 每排放2人，共18人 (2个9人组完美放入)
        for r in range(9):
            if r % 2 == 0: path.extend([(r,0), (r,1)])
            else: path.extend([(r,1), (r,0)])
                
        # 【中岛】 (列2到列4): 8排, 每排放3人，共24人 (3个8人组完美放入)
        # 这里折返时保证3个人横向紧挨，然后在下一排反向折回来
        for r in range(7, -1, -1):
            if r % 2 == 0: path.extend([(r,2), (r,3), (r,4)])
            else: path.extend([(r,4), (r,3), (r,2)])
                
        # 【右岛】 (列5和列6): 8排, 每排放2人，共16人 (2个8人组完美放入)
        for r in range(8):
            if r % 2 == 0: path.extend([(r,5), (r,6)])
            else: path.extend([(r,6), (r,5)])
            
        self.seat_path = path
        
        self.group_colors = [
            '#FFCDD2', '#BBDEFB', '#C8E6C9', '#FFF9C4', 
            '#E1BEE7', '#FFE0B2', '#B2DFDB'
        ]

    def allocate(self, groups, rotation_idx=1, is_current_run=True):
        seat_info = {}
        
        for i, g in enumerate(groups):
            g['bound_color'] = self.group_colors[i % len(self.group_colors)]
            
        # 1. 组间的大轮换
        offset = (rotation_idx - 1) % len(groups)
        rotated_groups = groups[-offset:] + groups[:-offset] if offset != 0 else groups
        
        current_idx = 0
        for group in rotated_groups:
            size = group['size']
            members = group['members'].copy()
            
            # 2. 组内成员规律性轮换
            inner_offset = ((rotation_idx - 1) * 2) % size
            if inner_offset != 0:
                members = members[-inner_offset:] + members[:-inner_offset]
            
            # 3. 点击按钮带来的随机微扰
            if is_current_run:
                for _ in range(max(1, size // 3)):  
                    idx1 = random.randint(0, size - 1)
                    idx2 = random.randint(0, size - 1)
                    members[idx1], members[idx2] = members[idx2], members[idx1]

            my_seats = self.seat_path[current_idx : current_idx + size]
            current_idx += size
            
            for seat, member in zip(my_seats, members):
                seat_info[seat] = {
                    'name': member,
                    'color': group['bound_color'],
                    'group': group['name']
                }
                
        return seat_info

# ==========================================
# 提取表格渲染函数
# ==========================================
def render_seat_chart(result_map):
    display_data = np.full((9, 7), "", dtype=object)
    color_data = np.full((9, 7), "background-color: #ffffff", dtype=object) 

    # 为走道添加深灰色边框进行视觉隔离
    for r in range(9):
        for c in range(7):
            base_style = "color: black; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;"
            # 在走道边上加粗边框
            if c == 1:
                base_style += " border-right: 4px solid #666;"
            elif c == 2:
                base_style += " border-left: 4px solid #666;"
            elif c == 4:
                base_style += " border-right: 4px solid #666;"
            elif c == 5:
                base_style += " border-left: 4px solid #666;"
            color_data[r, c] = base_style

    for (r, c), info in result_map.items():
        display_data[r, c] = info['name']
        existing_style = color_data[r, c]
        color_data[r, c] = existing_style + f" background-color: {info['color']};"

    cols = [f"第{i+1}列" for i in range(7)]
    rows = [f"第{i+1}排" for i in range(9)]
    df = pd.DataFrame(display_data, columns=cols, index=rows)

    def style_apply(x):
        return pd.DataFrame(color_data, index=x.index, columns=x.columns)

    st.dataframe(
        df.style.apply(style_apply, axis=None),
        use_container_width=True,
        height=400
    )

# ==========================================
# 界面与交互
# ==========================================
default_text = load_default_groups_text()

with st.sidebar:
    st.header("⚙️ 设置")
    uploaded_groups_text = st.text_area("预设分组名单", value=default_text, height=300)
    
    st.markdown("---")
    st.header("🔄 轮换与历史控制")
    rotation_week = st.number_input("⏳ 当前座位周期 (例如 第1周)", min_value=1, value=1, step=1)
    
    history_options = ["不显示", "前5周", "前10周", "前15周", "前20周", "全部"]
    history_limit = st.selectbox("📜 显示倒序历史记录", options=history_options, index=1)

if st.button("🎲 生成交替座位图", type="primary"):
    parsed_groups = parse_group_text(uploaded_groups_text)
    allocator = SeatAllocator()
    
    st.write(f"### 🎯 讲台 (FRONT) - 当前第 {rotation_week} 周")
    current_result = allocator.allocate(parsed_groups, rotation_week, is_current_run=True)
    render_seat_chart(current_result)
    
    if history_limit != "不显示" and rotation_week > 1:
        st.markdown("---")
        st.write("### 📜 历史座位表回顾 (倒序)")
        
        if history_limit == "全部":
            limit_num = rotation_week - 1
        else:
            limit_num = int(history_limit.replace("前", "").replace("周", ""))
        
        actual_limit = min(limit_num, rotation_week - 1)
        
        for past_w in range(rotation_week - 1, rotation_week - 1 - actual_limit, -1):
            st.write(f"#### 🔙 第 {past_w} 周的历史座位")
            past_result = allocator.allocate(parsed_groups, past_w, is_current_run=False)
            render_seat_chart(past_result)
