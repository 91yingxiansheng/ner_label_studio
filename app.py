# filepath: ner_label/app.py
import streamlit as st
import pandas as pd
import json
import os
from utils.annotation import AnnotationManager
from utils.mapping import VocabularyMapper
import streamlit.components.v1 as components

st.set_page_config(page_title="NER数据标注工具", page_icon="📝", layout="wide")

PROJECT_DIR = "data/projects"
os.makedirs(PROJECT_DIR, exist_ok=True)

def init_session_state():
    if 'annotation_manager' not in st.session_state:
        st.session_state.annotation_manager = AnnotationManager()
    if 'vocab_mapper' not in st.session_state:
        st.session_state.vocab_mapper = VocabularyMapper()
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'entity_labels' not in st.session_state:
        st.session_state.entity_labels = ["品类", "品牌", "型号", "年份", "价格", "cpu", "gpu", "内存", "存储", "重量", "颜色", "屏幕尺寸", "屏幕分辨率", "其他", "ai"]
    if 'label_category_map' not in st.session_state:
        st.session_state.label_category_map = {
            "品类": ["category"],
            "品牌": ["brand"],
            "型号": ["model"],
            "年份": ["release_year"],
            "价格": ["price"],
            "cpu": ['cpu_brand', 'cpu_series', 'cpu_family', 'cpu_model', 'cpu_gen'],
            "gpu": ['gpu_type', 'gpu_brand', 'gpu_series', 'gpu_model'],
            "内存": ['memory_capacity_gb'],
            "存储": ['storage_capacity_gb'],
            "屏幕尺寸": ['screen_size_inch'],
            "屏幕分辨率": ['screen_resolution'],
            "其他": ['other'],
            "颜色": ['color'],
            "ai": ['ai']
        }

def main():
    st.title("📝 NER数据标注工具")
    init_session_state()
    sidebar()
    main_content()

def sidebar():
    with st.sidebar:
        st.header("项目管理")
        os.makedirs(PROJECT_DIR, exist_ok=True)
        project_list = [
            f.replace(".csv", "").replace(".json", "")
            for f in os.listdir(PROJECT_DIR)
            if (
                (f.endswith(".csv") or f.endswith(".json"))
                and not f.endswith("_annotations.json")
                and not f.endswith("_vocab.json")
                and not f.endswith("_label_map.json")
            )
        ]
        selected_project = st.selectbox("选择项目", ["新建项目"] + project_list, key="project_select")
        if selected_project == "新建项目":
            st.markdown("#### 新建项目")
            new_project_name = st.text_input("项目名称", key="new_project_name")
            uploaded_file = st.file_uploader("上传数据集文件", type=['csv', 'xlsx', 'json'], key="project_file")
            uploaded_vocab = st.file_uploader("（可选）上传项目词表", type=['json'], key="project_vocab")
            uploaded_label_map = st.file_uploader("（可选）上传标签-类别映射", type=['json'], key="project_label_map")
            if st.button("创建项目", key="create_project_btn") and new_project_name and uploaded_file:
                try:
                    # 只读取一次文件内容
                    if uploaded_file.name.endswith('.json'):
                        file_bytes = uploaded_file.read()
                        data = json.loads(file_bytes.decode('utf-8'))
                        df = pd.DataFrame(data)
                        df.to_json(f"{PROJECT_DIR}/{new_project_name}.json", orient="records", force_ascii=False)
                    elif uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                        df.to_csv(f"{PROJECT_DIR}/{new_project_name}.csv", index=False, encoding="utf-8-sig")
                    elif uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                        df.to_csv(f"{PROJECT_DIR}/{new_project_name}.csv", index=False, encoding="utf-8-sig")
                    else:
                        st.error("不支持的文件类型")
                        print("[ERROR] 不支持的文件类型")
                        return
                except Exception as e:
                    print(f"[ERROR] 数据文件解析失败: {e}")
                    st.error(f"数据文件解析失败: {e}")
                    return

                # 初始化标注
                try:
                    if 'annotations' in df.columns:
                        annotations = {}
                        for idx, row in df.iterrows():
                            anns = row['annotations']
                            if isinstance(anns, str):
                                try:
                                    anns = json.loads(anns)
                                except Exception as e:
                                    print(f"[WARN] 第{idx}行annotations字段解析失败: {e}")
                                    anns = []
                            elif isinstance(anns, (list, dict)):
                                pass
                            elif pd.isna(anns):
                                anns = []
                            else:
                                anns = []
                            annotations[str(idx)] = anns
                        with open(f"{PROJECT_DIR}/{new_project_name}_annotations.json", "w", encoding="utf-8") as f:
                            json.dump(annotations, f, ensure_ascii=False)
                    else:
                        with open(f"{PROJECT_DIR}/{new_project_name}_annotations.json", "w", encoding="utf-8") as f:
                            json.dump({str(i): [] for i in range(len(df))}, f, ensure_ascii=False)
                except Exception as e:
                    print(f"[ERROR] 标注文件保存失败: {e}")
                    st.error(f"标注文件保存失败: {e}")
                    return

                # 保存词表
                if uploaded_vocab:
                    try:
                        vocab_data = json.load(uploaded_vocab)
                        with open(f"{PROJECT_DIR}/{new_project_name}_vocab.json", "w", encoding="utf-8") as f:
                            json.dump(vocab_data, f, ensure_ascii=False)
                    except Exception as e:
                        print(f"[ERROR] 词表保存失败: {e}")
                        st.error(f"词表保存失败: {e}")
                # 保存标签-类别映射
                if uploaded_label_map:
                    try:
                        label_map = json.load(uploaded_label_map)
                        with open(f"{PROJECT_DIR}/{new_project_name}_label_map.json", "w", encoding="utf-8") as f:
                            json.dump(label_map, f, ensure_ascii=False)
                    except Exception as e:
                        print(f"[ERROR] 标签-类别映射保存失败: {e}")
                        st.error(f"标签-类别映射保存失败: {e}")

                st.success(f"项目 {new_project_name} 创建成功！")
                st.rerun()
        else:
            st.markdown(f"#### 当前项目：**{selected_project}**")
            # 加载项目数据和标注
            try:
                if os.path.exists(f"{PROJECT_DIR}/{selected_project}.csv"):
                    df = pd.read_csv(f"{PROJECT_DIR}/{selected_project}.csv")
                elif os.path.exists(f"{PROJECT_DIR}/{selected_project}.json"):
                    with open(f"{PROJECT_DIR}/{selected_project}.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    df = pd.DataFrame(data)
                else:
                    st.error("未找到项目数据文件")
                    return
                st.session_state.df = df
                # 加载标注
                ann_path = f"{PROJECT_DIR}/{selected_project}_annotations.json"
                if os.path.exists(ann_path):
                    with open(ann_path, "r", encoding="utf-8") as f:
                        annotations = json.load(f)
                    st.session_state.annotation_manager.annotations = {int(k): v for k, v in annotations.items()}
                else:
                    st.session_state.annotation_manager.initialize_annotations(len(df))
                st.session_state.selected_project = selected_project
                # 加载项目词表
                vocab_path = f"{PROJECT_DIR}/{selected_project}_vocab.json"
                if os.path.exists(vocab_path):
                    with open(vocab_path, "r", encoding="utf-8") as f:
                        vocab_data = json.load(f)
                    st.session_state.vocab_mapper.load_vocabulary(vocab_data)
                # 加载项目标签-类别映射
                label_map_path = f"{PROJECT_DIR}/{selected_project}_label_map.json"
                if os.path.exists(label_map_path):
                    with open(label_map_path, "r", encoding="utf-8") as f:
                        label_map = json.load(f)
                    st.session_state.label_category_map = label_map
                st.success(f"已加载项目 {selected_project}")
            except Exception as e:
                print(f"[ERROR] 项目加载失败: {e}")
                st.error(f"项目加载失败: {e}")

            st.markdown("#### 词表管理")
            uploaded_vocab = st.file_uploader("上传/覆盖项目词表", type=['json'], key="vocab_upload")
            if uploaded_vocab:
                try:
                    vocab_data = json.load(uploaded_vocab)
                    st.session_state.vocab_mapper.load_vocabulary(vocab_data)
                    with open(f"{PROJECT_DIR}/{selected_project}_vocab.json", "w", encoding="utf-8") as f:
                        json.dump(vocab_data, f, ensure_ascii=False)
                    st.success("词表已覆盖并保存到项目")
                    st.rerun()
                except Exception as e:
                    st.error(f"词表加载失败: {e}")

            st.markdown("#### 标签-类别映射管理")
            uploaded_label_map = st.file_uploader("上传/覆盖标签-类别映射", type=['json'], key="label_map_upload")
            if uploaded_label_map:
                try:
                    label_map = json.load(uploaded_label_map)
                    st.session_state.label_category_map = label_map
                    with open(f"{PROJECT_DIR}/{selected_project}_label_map.json", "w", encoding="utf-8") as f:
                        json.dump(label_map, f, ensure_ascii=False)
                    st.success("标签-类别映射已覆盖并保存到项目")
                    st.rerun()
                except Exception as e:
                    st.error(f"标签-类别映射加载失败: {e}")

        show_statistics()

def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        if 'query' not in df.columns:
            st.error("数据文件必须包含 'query' 列")
            return
        st.session_state.df = df
        # 初始化标注
        st.session_state.annotation_manager.initialize_annotations(len(df))
        if 'annotations' in df.columns:
            for idx, row in df.iterrows():
                try:
                    anns = row['annotations']
                    if isinstance(anns, str):
                        anns = json.loads(anns)
                    elif pd.isna(anns):
                        anns = []
                    st.session_state.annotation_manager.annotations[idx] = anns
                except Exception as e:
                    st.warning(f"第{idx}行实体解析失败: {e}")
        st.success(f"成功加载 {len(df)} 条数据")
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")

def manage_entity_labels():
    col1, col2 = st.columns(2)
    with col1:
        new_label = st.text_input("新增标签", placeholder="输入新标签", key="new_label_input")
        if st.button("添加标签", key="add_label_btn"):
            if new_label and new_label.strip():
                if new_label not in st.session_state.entity_labels:
                    st.session_state.entity_labels.append(new_label)
                    st.success(f"标签 '{new_label}' 添加成功")
                    st.rerun()
                else:
                    st.warning("标签已存在")
    with col2:
        if st.session_state.entity_labels:
            label_to_remove = st.selectbox("选择要删除的标签", [""] + st.session_state.entity_labels, key="remove_label_select")
            if st.button("删除标签", key="remove_label_btn") and label_to_remove:
                st.session_state.entity_labels.remove(label_to_remove)
                st.success(f"标签 '{label_to_remove}' 删除成功")
                st.rerun()

def load_vocabulary(uploaded_file):
    try:
        vocab_data = json.load(uploaded_file)
        st.session_state.vocab_mapper.load_vocabulary(vocab_data)
        st.success("词表加载成功")
        vocab_stats = st.session_state.vocab_mapper.get_vocabulary_stats()
        for category, count in vocab_stats.items():
            st.info(f"{category}: {count} 个词条")
    except Exception as e:
        st.error(f"加载词表失败: {str(e)}")

def show_statistics():
    if hasattr(st.session_state, 'df'):
        total = 0
        mapped = 0
        # 遍历所有数据条目
        for idx in range(len(st.session_state.df)):
            annotations = st.session_state.annotation_manager.get_annotations(idx)
            total += len(annotations)
            for ann in annotations:
                # mapped_value 字典有内容即认为已完成映射
                if isinstance(ann.get("mapped_value", None), dict) and any(ann["mapped_value"].values()):
                    mapped += 1
        progress = mapped / total if total > 0 else 0
        st.subheader("映射完成进度")
        st.progress(progress)
        st.write(f"已完成映射: {mapped}/{total} ({progress:.1%})")

def main_content():
    if not hasattr(st.session_state, 'df'):
        st.info("请先上传数据文件开始标注")
        return
    navigation_controls()
    annotation_interface()
    export_controls()

def navigation_controls():
    # 重新设计的导航控件
    total = len(st.session_state.df)
    current_idx = st.session_state.current_index
    
    # 计算进度百分比
    progress_percent = (current_idx + 1) / total if total > 0 else 0
    
    # 创建两行布局
    # 第一行：进度条和当前进度
    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 14px; color: #666;">进度</span>
                <span style="font-size: 14px; color: #666;">{current_idx + 1}/{total}</span>
            </div>
            <div style="width: 100%; background-color: #f0f2f6; border-radius: 10px; overflow: hidden;">
                <div style="width: {progress_percent * 100}%; height: 8px; background: linear-gradient(90deg, #4ECDC4, #44A08D); transition: width 0.3s;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 第二行：导航按钮和状态
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # 留空或可以添加其他功能
        pass
    
    with col2:
        # 居中的导航按钮组
        col_prev, col_counter, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("◀", key="prev_btn", use_container_width=True, 
                        disabled=current_idx <= 0,
                        help="上一页") and current_idx > 0:
                st.session_state.current_index -= 1
                st.rerun()
        
        with col_counter:
            # 美观计数器
            st.markdown(
                f"""
                <div style="text-align: center; padding: 8px; background: #f0f2f6; border-radius: 8px;">
                    <div style="font-size: 16px; font-weight: bold; color: #4ECDC4;">{current_idx + 1}</div>
                    <div style="font-size: 12px; color: #666;">/ {total}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # 添加滑动条
            slider_idx = st.slider(
                "快速跳转", min_value=1, max_value=total, value=current_idx + 1, key="data_slider"
            )
            if slider_idx - 1 != current_idx:
                st.session_state.current_index = slider_idx - 1
                st.rerun()
        
        with col_next:
            if st.button("▶", key="next_btn", use_container_width=True,
                        disabled=current_idx >= total-1,
                        help="下一页") and current_idx < total-1:
                st.session_state.current_index += 1
                st.rerun()
    
    with col3:
        # 显示标注完成状态
        current_annotations = st.session_state.annotation_manager.get_annotations(current_idx)
        
        # 判断是否完成标注：有实体且有映射关系
        is_completed = False
        if current_annotations:
            # 检查每个标注的mapped_value是否都有值
            has_valid_mappings = True
            for ann in current_annotations:
                mapped_value = ann.get("mapped_value", {})
                # 如果mapped_value是空字典，或者所有值都是空列表，则认为没有有效映射
                if not mapped_value or not any(mapped_value.values()):
                    has_valid_mappings = False
                    break
            is_completed = has_valid_mappings
        
        # 根据完成状态设置颜色和文本
        if is_completed:
            status_color = "#4ECDC4"  # 绿色 - 已完成
            status_text = "标注完成"
        elif current_annotations:
            status_color = "#FFA500"  # 橙色 - 有实体但映射未完成
            status_text = "映射未完成"
        else:
            status_color = "#FF6B6B"  # 红色 - 未开始
            status_text = "未开始标注"
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 8px; background: {status_color}20; border-radius: 8px; border: 1px solid {status_color}40;">
                <div style="font-size: 14px; font-weight: bold; color: {status_color};">{status_text}</div>
                <div style="font-size: 12px; color: #666;">{len(current_annotations)} 个实体</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # 添加一个小的分隔线
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

def annotation_interface():
    current_idx = st.session_state.current_index
    current_data = st.session_state.df.iloc[current_idx]
    query = current_data['query']
    
    # 紧凑的标题布局
    col_title, col_nav = st.columns([3, 1])
    with col_title:
        st.subheader("待标注文本")
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Query: {query}</span>", 
                   unsafe_allow_html=True)
    with col_nav:
        st.write("")  # 空行用于垂直对齐
        # if st.button("导出当前样本", key=f"export_single_{current_idx}"):
        #     # 这里可以添加导出当前样本的功能
        #     st.success("当前样本已导出")
    
    st.caption("选中上方文本后，Ctrl+C复制并粘贴到下方实体文本框，系统自动定位实体位置。")
    
    # 实体标注部分 - 上下布局
    st.markdown("---")
    st.write("#### 实体标注")
    
    entity_text = st.text_input("实体文本（粘贴或输入）", key=f"entity_text_{current_idx}")
    
    # 自动定位
    start_pos, end_pos = 0, 0
    if entity_text and entity_text in query:
        start_pos = query.find(entity_text)
        end_pos = start_pos + len(entity_text)
    else:
        col_start, col_end = st.columns(2)
        with col_start:
            start_pos = st.number_input("起始位置", min_value=0, max_value=len(query), 
                                      value=0, key=f"start_pos_{current_idx}")
        with col_end:
            end_pos = st.number_input("结束位置", min_value=0, max_value=len(query), 
                                    value=0, key=f"end_pos_{current_idx}")

    # 校验输入
    valid = True
    if not entity_text:
        st.warning("请粘贴或输入实体文本")
        valid = False
    elif start_pos >= end_pos:
        st.warning("起始位置必须小于结束位置")
        valid = False
    elif end_pos > len(query):
        st.warning("结束位置超出文本长度")
        valid = False

    if start_pos < end_pos and end_pos <= len(query):
        st.info(f"选中的文本: **{query[start_pos:end_pos]}**")
    
    col_label, col_btn = st.columns([3, 1])
    with col_label:
        selected_label = st.selectbox("选择实体标签", options=st.session_state.entity_labels, 
                                    key=f"label_select_{current_idx}")
    with col_btn:
        st.write("")  # 垂直间距
        if st.button("添加标注", key=f"add_annotation_{current_idx}", use_container_width=True) and valid:
            annotation = {
                'text': entity_text,
                'label': selected_label,
                'start': start_pos,
                'end': end_pos,
                'mapped_value': {}
            }
            result = st.session_state.annotation_manager.add_annotation(current_idx, annotation)
            if result:
                save_annotations()
                st.success("标注添加成功！")
                st.rerun()
            else:
                st.error("标注重叠或无效")
    
    # 映射标注部分 - 直接调用显示当前标注
    st.markdown("---")
    display_current_annotations(query, current_idx)

def display_current_annotations(query, current_idx):
    st.write("#### 映射标注")
    current_annotations = st.session_state.annotation_manager.get_annotations(current_idx)
    
    if not current_annotations:
        st.info("暂无标注，请先添加实体标注")
        return
    
    # 简化预览 - 只显示标注文本
    st.write("**当前标注预览:**")
    colors = {
        "品牌": "#ff6b6b", "品类": "#4ecdc4", "型号": "#45b7d1", 
        "CPU": "#96ceb4", "GPU": "#ffd966", "内存": "#d4a5a5",
        "存储": "#9bdeac", "屏幕尺寸": "#a2d2ff", "价格": "#ffafcc"
    }
    
    annotated_text = []
    for ann in current_annotations:
        color = colors.get(ann['label'], "#ffe66d")
        annotated_text.append(
            f"<span style='background-color: {color}; padding: 4px 8px; margin: 2px; "
            f"border-radius: 4px; display: inline-block; font-size: 14px;'>"
            f"{ann['text']} ({ann['label']})</span>"
        )
    
    if annotated_text:
        st.markdown("".join(annotated_text), unsafe_allow_html=True)
    else:
        st.info("暂无标注")
    
    # 映射部分 - 使用展开器让界面更整洁
    for i, ann in enumerate(current_annotations):
        with st.expander(f"标注 {i+1}: {ann['text']} - {ann['label']}", expanded=False):
            col_del, col_info = st.columns([1, 4])
            with col_del:
                if st.button("🗑️ 删除", key=f"delete_{current_idx}_{i}", use_container_width=True):
                    st.session_state.annotation_manager.remove_annotation(current_idx, i)
                    save_annotations()
                    st.success("标注已删除")
                    st.rerun()
            
            with col_info:
                st.write(f"位置: {ann['start']}-{ann['end']}")
            
            # 多类别映射
            if st.session_state.vocab_mapper.has_vocabulary():
                label_category_map = st.session_state.get("label_category_map", {})
                categories = label_category_map.get(ann['label'], [])
                
                if "mapped_value" not in ann or not isinstance(ann["mapped_value"], dict):
                    ann["mapped_value"] = {}
                    st.session_state.annotation_manager.update_annotation(current_idx, i, ann)
                
                for cat in categories:
                    candidates = st.session_state.vocab_mapper.vocab.get(cat, [])
                    current_mapping = ann["mapped_value"].get(cat, [])
                    if not isinstance(current_mapping, list):
                        current_mapping = [current_mapping] if current_mapping else []
                    
                    col_map, col_add = st.columns([3, 2])
                    with col_map:
                        selected_mappings = st.multiselect(
                            f"**{cat}** 映射", 
                            options=candidates,
                            default=current_mapping,
                            key=f"mapping_multiselect_{current_idx}_{i}_{cat}"
                        )
                    
                    with col_add:
                        new_candidate = st.text_input(
                            f"添加{cat}候选词", 
                            value="", 
                            key=f"add_candidate_{current_idx}_{i}_{cat}",
                            placeholder="输入新词条"
                        )
                        if st.button("添加", key=f"add_candidate_btn_{current_idx}_{i}_{cat}") and new_candidate:
                            if new_candidate not in st.session_state.vocab_mapper.vocab.get(cat, []):
                                st.session_state.vocab_mapper.vocab.setdefault(cat, []).append(new_candidate)
                                if 'selected_project' in st.session_state:
                                    vocab_path = f"{PROJECT_DIR}/{st.session_state.selected_project}_vocab.json"
                                    with open(vocab_path, "w", encoding="utf-8") as f:
                                        json.dump(st.session_state.vocab_mapper.vocab, f, ensure_ascii=False)
                                st.success(f"已添加: {new_candidate}")
                                st.rerun()
                            else:
                                st.warning("词条已存在")
                    
                    if selected_mappings != current_mapping:
                        ann["mapped_value"][cat] = selected_mappings
                        st.session_state.annotation_manager.update_annotation(current_idx, i, ann)
                        save_annotations()
                        st.success(f"映射已更新: {cat} → {selected_mappings}")

def display_annotated_text(query, annotations):
    st.write("**标注预览:**")
    colors = {
        "品牌": "#ff6b6b",
        "品类": "#4ecdc4",
        "型号": "#45b7d1",
    }
    sorted_annotations = sorted(annotations, key=lambda x: x['start'])
    colored_parts = []
    last_end = 0
    for ann in sorted_annotations:
        if ann['start'] > last_end:
            colored_parts.append(query[last_end:ann['start']])
        color = colors.get(ann['label'], "#ffe66d")
        colored_part = f"<mark style='background-color: {color}; padding: 2px; border-radius: 3px;' title='{ann['label']}'>{ann['text']}</mark>"
        colored_parts.append(colored_part)
        last_end = ann['end']
    if last_end < len(query):
        colored_parts.append(query[last_end:])
    annotated_html = "".join(colored_parts)
    st.markdown(annotated_html, unsafe_allow_html=True)

def export_controls():
    # 简化导出控件
    st.markdown("---")
    
    # 在页面中间展示当前样本的annotations
    if hasattr(st.session_state, 'df') and st.session_state.current_index < len(st.session_state.df):
        current_idx = st.session_state.current_index
        current_annotations = st.session_state.annotation_manager.get_annotations(current_idx)
        
        # 创建居中的布局
        col_left, col_center, col_right = st.columns([2, 2, 1])
        
        with col_left:
            st.write("#### 当前样本标注")
            
            if current_annotations:
                # 格式化显示annotations
                annotations_json = json.dumps(current_annotations, ensure_ascii=False, indent=2)
                st.text_area(
                    "Annotations",
                    value=annotations_json,
                    height=200,
                    key="current_annotations_display",
                    disabled=True
                )
                
                # 添加复制按钮
                if st.button("📋 复制Annotations", use_container_width=True):
                    st.session_state.clipboard = annotations_json
                    st.success("已复制到剪贴板！")
            else:
                st.info("当前样本暂无标注")
        with col_center:
            # 你可以在这里添加其他居中内容
            pass

        with col_right:
            st.write("")  # 占位
            # 下一条按钮
            total = len(st.session_state.df)
            current_idx = st.session_state.current_index
            # if st.button("⬅️ 上一条", key="export_prev_btn", use_container_width=True) and current_idx > 0:
            #     st.session_state.current_index -= 1
            #     st.rerun()
            if st.button("➡️ 下一条", key="export_next_btn", use_container_width=True) and current_idx < total - 1:
                st.session_state.current_index += 1
                st.rerun()
    
    # 导出按钮
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write("#### 数据导出")
        if hasattr(st.session_state, 'df'):
            export_data = st.session_state.annotation_manager.export_annotations(st.session_state.df)
            csv = export_data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载全部标注数据",
                data=csv,
                file_name="ner_annotations.csv",
                mime="text/csv",
                use_container_width=True
            )

def save_annotations():
    # 保存标注到本地
    if 'selected_project' in st.session_state:
        ann_path = f"{PROJECT_DIR}/{st.session_state.selected_project}_annotations.json"
        with open(ann_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state.annotation_manager.annotations, f, ensure_ascii=False)

if __name__ == "__main__":
    main()