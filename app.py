import streamlit as st
import random
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="班级座位分组可视化", page_icon="🎨", layout="wide")

st.title("🎨 七林2025级(6)班 智能座位分组可视化(预设轮换版)")
st.markdown("""
**图例说明：**
*   **色块**：同一种背景颜色的同学属于同一个小组（绑定组名，方便观察轮换轨迹）。
*   **布局**：左侧两列为9排，其余为8排。
*   **轮换**：使用“区域贪吃蛇连积算法”。左侧改变【轮换周期】，所有小组可以在全教室不同排、不同列平滑移位，同时仍保持组员相邻不失散。随着周期的增加，组内成员也会有规律地在自己小组的领地内首尾轮换位置。
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
        path = []
        for r in range(9):
            if r % 2 == 0: path.extend([(r,0), (r,1)])
            else: path.extend([(r,1), (r,0)])
                
        for r in range(7, -1, -1):
            if r % 2 == 0: path.extend([(r,2), (r,3)])
            else: path.extend([(r,3), (r,2)])
                
        for r in range(8):
            if r % 2 == 0: path.extend([(r,4), (r,5)])
            else: path.extend([(r,5), (r,4)])
                
        for r in range(7, -1, -1):
            path.append((r,6))
            
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
            
            # 使用初始的固定名单顺序复制
            members = group['members'].copy()
            
            # 🌟 2. 组内成员的规律性轮换 
            # 每过一周（无论是否按按钮），按照贪吃蛇序列向前移2位（这样前后/左右交替感更明显）
            inner_offset = ((rotation_idx - 1) * 2) % size
            if inner_offset != 0:
                members = members[-inner_offset:] + members[:-inner_offset]
            
            # 🌟 3. 保留按钮打乱的随机性：仅在绘制“当前周”且用户希望有一点微扰时生效
            # 为了让每次点击“生成交替图”时当前周有一点随机性，但在历史记录里保持绝对一致的轨迹。
            # 给成员做有限打散（比如同排左右换位）：
            if is_current_run:
                # 随机交换几个人的位置增加活性，但不破坏整体顺延逻辑
                for _ in range(size // 3):  
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

    for (r, c), info in result_map.items():
        display_data[r, c] = info['name']
        color_data[r, c] = f"background-color: {info['color']}; color: black; border: 1px solid white;"

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
    
    # 🌟 1. 渲染当前周的座位表 (这里允许有一点生成按钮带来的微小随机打乱)
    st.write(f"### 🎯 讲台 (FRONT) - 当前第 {rotation_week} 周")
    current_result = allocator.allocate(parsed_groups, rotation_week, is_current_run=True)
    render_seat_chart(current_result)
    
    # 🌟 2. 渲染历史记录
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
            # 历史记录渲染时关闭随机微扰，呈现平滑干净的轨迹
            past_result = allocator.allocate(parsed_groups, past_w, is_current_run=False)
            render_seat_chart(past_result)