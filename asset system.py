import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
import xlsxwriter

# ========== 配置和常量 ==========

# 数据文件路径
FINANCIAL_DATA_FILE = "financial_data.json"
PHYSICAL_DATA_FILE = "physical_data.json"
MAPPING_DATA_FILE = "mapping_data.json"

# 页面配置
st.set_page_config(
    page_title="资产映射关系查询系统",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 数据处理函数 ==========

def save_data(data, filename):
    """保存数据到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存数据失败: {str(e)}")
        return False

def load_data(filename):
    """从JSON文件加载数据"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")
        return []

def parse_excel_file(uploaded_file, sheet_name=None):
    """解析Excel文件"""
    try:
        if sheet_name:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 清理数据
        df = df.dropna(how='all')  # 删除完全空白的行
        df = df.fillna('')  # 填充空值
        
        # 转换为字典列表
        return df.to_dict('records')
    except Exception as e:
        st.error(f"解析Excel文件失败: {str(e)}")
        return None

def create_data_index(data, key_field):
    """创建数据索引以提高查询效率"""
    index = {}
    for record in data:
        key = record.get(key_field)
        if key:
            index[str(key)] = record
    return index

def create_mapping_index(mapping_data):
    """创建映射关系索引"""
    f_to_p = {}  # 财务到实物的映射
    p_to_f = {}  # 实物到财务的映射
    
    for record in mapping_data:
        financial_code = str(record.get("财务系统编号", ""))
        physical_code = str(record.get("固定资产编号", ""))
        
        if financial_code and physical_code:
            f_to_p[financial_code] = physical_code
            p_to_f[physical_code] = financial_code
    
    return f_to_p, p_to_f

# ========== 页面函数 ==========

def data_import_page():
    """数据导入页面"""
    st.header("📥 数据导入管理")
    
    # 创建三个标签页
    tab1, tab2, tab3 = st.tabs(["财务系统数据", "实物台账数据", "映射关系数据"])
    
    with tab1:
        st.subheader("💰 财务系统资产数据")
        st.info("请上传包含财务系统资产信息的Excel文件")
        
        # 显示当前数据状态
        current_financial = load_data(FINANCIAL_DATA_FILE)
        if current_financial:
            st.success(f"✅ 当前已有 {len(current_financial)} 条财务资产记录")
            
            # 显示数据预览
            with st.expander("查看当前数据预览"):
                df = pd.DataFrame(current_financial[:5])  # 只显示前5条
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ 暂无财务系统数据")
        
        # 文件上传
        financial_file = st.file_uploader(
            "选择财务系统Excel文件",
            type=['xlsx', 'xls'],
            key="financial_upload"
        )
        
        if financial_file is not None:
            # 获取工作表名称
            try:
                excel_file = pd.ExcelFile(financial_file)
                sheet_names = excel_file.sheet_names
                
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("选择工作表", sheet_names, key="financial_sheet")
                else:
                    selected_sheet = sheet_names[0]
                
                if st.button("导入财务数据", key="import_financial"):
                    with st.spinner("正在处理财务数据..."):
                        data = parse_excel_file(financial_file, selected_sheet)
                        
                        if data:
                            # 验证必要字段
                            required_fields = ["财务系统编号", "资产名称"]
                            sample_record = data[0] if data else {}
                            missing_fields = [field for field in required_fields if field not in sample_record]
                            
                            if missing_fields:
                                st.error(f"❌ 缺少必要字段: {', '.join(missing_fields)}")
                            else:
                                if save_data(data, FINANCIAL_DATA_FILE):
                                    st.success(f"✅ 成功导入 {len(data)} 条财务资产记录")
                                    st.rerun()
                        else:
                            st.error("❌ 数据解析失败")
            except Exception as e:
                st.error(f"❌ 文件处理失败: {str(e)}")
    
    with tab2:
        st.subheader("📋 实物台账资产数据")
        st.info("请上传包含实物台账资产信息的Excel文件")
        
        # 显示当前数据状态
        current_physical = load_data(PHYSICAL_DATA_FILE)
        if current_physical:
            st.success(f"✅ 当前已有 {len(current_physical)} 条实物资产记录")
            
            # 显示数据预览
            with st.expander("查看当前数据预览"):
                df = pd.DataFrame(current_physical[:5])  # 只显示前5条
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ 暂无实物台账数据")
        
        # 文件上传
        physical_file = st.file_uploader(
            "选择实物台账Excel文件",
            type=['xlsx', 'xls'],
            key="physical_upload"
        )
        
        if physical_file is not None:
            # 获取工作表名称
            try:
                excel_file = pd.ExcelFile(physical_file)
                sheet_names = excel_file.sheet_names
                
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("选择工作表", sheet_names, key="physical_sheet")
                else:
                    selected_sheet = sheet_names[0]
                
                if st.button("导入实物数据", key="import_physical"):
                    with st.spinner("正在处理实物数据..."):
                        data = parse_excel_file(physical_file, selected_sheet)
                        
                        if data:
                            # 验证必要字段
                            required_fields = ["固定资产编号", "固定资产名称"]
                            sample_record = data[0] if data else {}
                            missing_fields = [field for field in required_fields if field not in sample_record]
                            
                            if missing_fields:
                                st.error(f"❌ 缺少必要字段: {', '.join(missing_fields)}")
                            else:
                                if save_data(data, PHYSICAL_DATA_FILE):
                                    st.success(f"✅ 成功导入 {len(data)} 条实物资产记录")
                                    st.rerun()
                        else:
                            st.error("❌ 数据解析失败")
            except Exception as e:
                st.error(f"❌ 文件处理失败: {str(e)}")
    
    with tab3:
        st.subheader("🔗 映射关系数据")
        st.info("请上传包含资产映射关系的Excel文件")
        
        # 显示当前数据状态
        current_mapping = load_data(MAPPING_DATA_FILE)
        if current_mapping:
            st.success(f"✅ 当前已有 {len(current_mapping)} 条映射关系记录")
            
            # 显示数据预览
            with st.expander("查看当前数据预览"):
                df = pd.DataFrame(current_mapping[:5])  # 只显示前5条
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ 暂无映射关系数据")
        
        # 文件上传
        mapping_file = st.file_uploader(
            "选择映射关系Excel文件",
            type=['xlsx', 'xls'],
            key="mapping_upload"
        )
        
        if mapping_file is not None:
            # 获取工作表名称
            try:
                excel_file = pd.ExcelFile(mapping_file)
                sheet_names = excel_file.sheet_names
                
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("选择工作表", sheet_names, key="mapping_sheet")
                else:
                    selected_sheet = sheet_names[0]
                
                if st.button("导入映射数据", key="import_mapping"):
                    with st.spinner("正在处理映射数据..."):
                        data = parse_excel_file(mapping_file, selected_sheet)
                        
                        if data:
                            # 验证必要字段
                            required_fields = ["财务系统编号", "固定资产编号"]
                            sample_record = data[0] if data else {}
                            missing_fields = [field for field in required_fields if field not in sample_record]
                            
                            if missing_fields:
                                st.error(f"❌ 缺少必要字段: {', '.join(missing_fields)}")
                            else:
                                if save_data(data, MAPPING_DATA_FILE):
                                    st.success(f"✅ 成功导入 {len(data)} 条映射关系记录")
                                    st.rerun()
                        else:
                            st.error("❌ 数据解析失败")
            except Exception as e:
                st.error(f"❌ 文件处理失败: {str(e)}")
    
    # 数据清理选项
    st.markdown("---")
    st.subheader("🗑️ 数据管理")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("清空财务数据", type="secondary"):
            if save_data([], FINANCIAL_DATA_FILE):
                st.success("✅ 财务数据已清空")
                st.rerun()
    
    with col2:
        if st.button("清空实物数据", type="secondary"):
            if save_data([], PHYSICAL_DATA_FILE):
                st.success("✅ 实物数据已清空")
                st.rerun()
    
    with col3:
        if st.button("清空映射数据", type="secondary"):
            if save_data([], MAPPING_DATA_FILE):
                st.success("✅ 映射数据已清空")
                st.rerun()
    
    with col4:
        if st.button("清空所有数据", type="secondary"):
            if all([
                save_data([], FINANCIAL_DATA_FILE),
                save_data([], PHYSICAL_DATA_FILE),
                save_data([], MAPPING_DATA_FILE)
            ]):
                st.success("✅ 所有数据已清空")
                st.rerun()

def mapping_query_page():
    """映射查询页面"""
    st.header("🔍 资产映射关系查询")
    
    # 加载数据
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)
    
    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 请先导入所有必要的数据（财务系统数据、实物台账数据、映射关系数据）")
        return
    
    # 创建索引以提高查询效率
    financial_index = create_data_index(financial_data, "财务系统编号")
    physical_index = create_data_index(physical_data, "固定资产编号")
    f_to_p_mapping, p_to_f_mapping = create_mapping_index(mapping_data)
    
    # 查询选项
    query_type = st.selectbox(
        "选择查询方式",
        ["按财务系统编号查询", "按实物台账编号查询", "按资产名称搜索", "批量查询"]
    )
    
    if query_type == "按财务系统编号查询":
        st.subheader("🔍 财务系统编号查询")
        
        financial_code = st.text_input("请输入财务系统编号", placeholder="例如: FS001")
        
        if financial_code:
            # 查找财务资产信息
            financial_record = financial_index.get(financial_code)
            
            if financial_record:
                st.success("✅ 找到财务资产信息")
                
                # 显示财务资产信息
                with st.expander("📊 财务资产详情", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**资产编号**: {financial_record.get('财务系统编号', '')}")
                        st.info(f"**资产名称**: {financial_record.get('资产名称', '')}")
                        st.info(f"**资产分类**: {financial_record.get('资产分类', '')}")
                    with col2:
                        st.info(f"**资产价值**: ¥{financial_record.get('资产价值', 0):,.2f}")
                        st.info(f"**所属部门**: {financial_record.get('部门名称', '')}")
                        st.info(f"**保管人**: {financial_record.get('保管人', '')}")
                
                # 查找对应的实物资产
                physical_code = f_to_p_mapping.get(financial_code)
                
                if physical_code:
                    physical_record = physical_index.get(physical_code)
                    if physical_record:
                        st.success("✅ 找到对应的实物资产")
                        
                        # 显示实物资产信息
                        with st.expander("📋 实物资产详情", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**资产编号**: {physical_record.get('固定资产编号', '')}")
                                st.info(f"**资产名称**: {physical_record.get('固定资产名称', '')}")
                                st.info(f"**资产类型**: {physical_record.get('固定资产类型', '')}")
                            with col2:
                                st.info(f"**资产价值**: ¥{physical_record.get('资产价值', 0):,.2f}")
                                st.info(f"**存放部门**: {physical_record.get('存放部门', '')}")
                                st.info(f"**使用状态**: {physical_record.get('使用状态', '')}")
                        
                        # 价值比较
                        financial_value = financial_record.get('资产价值', 0)
                        physical_value = physical_record.get('资产价值', 0)
                        value_diff = financial_value - physical_value
                        
                        if abs(value_diff) > 0.01:
                            st.warning(f"⚠️ 价值差异: ¥{value_diff:,.2f}")
                        else:
                            st.success("✅ 资产价值一致")
                    else:
                        st.error("❌ 映射的实物资产记录不存在")
                else:
                    st.warning("⚠️ 该财务资产未找到对应的实物资产")
            else:
                st.error("❌ 未找到该财务系统编号对应的资产")
    
    elif query_type == "按实物台账编号查询":
        st.subheader("🔍 实物台账编号查询")
        
        physical_code = st.text_input("请输入实物台账编号", placeholder="例如: PA001")
        
        if physical_code:
            # 查找实物资产信息
            physical_record = physical_index.get(physical_code)
            
            if physical_record:
                st.success("✅ 找到实物资产信息")
                
                # 显示实物资产信息
                with st.expander("📋 实物资产详情", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**资产编号**: {physical_record.get('固定资产编号', '')}")
                        st.info(f"**资产名称**: {physical_record.get('固定资产名称', '')}")
                        st.info(f"**资产类型**: {physical_record.get('固定资产类型', '')}")
                    with col2:
                        st.info(f"**资产价值**: ¥{physical_record.get('资产价值', 0):,.2f}")
                        st.info(f"**存放部门**: {physical_record.get('存放部门', '')}")
                        st.info(f"**使用状态**: {physical_record.get('使用状态', '')}")
                
                # 查找对应的财务资产
                financial_code = p_to_f_mapping.get(physical_code)
                
                if financial_code:
                    financial_record = financial_index.get(financial_code)
                    if financial_record:
                        st.success("✅ 找到对应的财务资产")
                        
                        # 显示财务资产信息
                        with st.expander("📊 财务资产详情", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**资产编号**: {financial_record.get('财务系统编号', '')}")
                                st.info(f"**资产名称**: {financial_record.get('资产名称', '')}")
                                st.info(f"**资产分类**: {financial_record.get('资产分类', '')}")
                            with col2:
                                st.info(f"**资产价值**: ¥{financial_record.get('资产价值', 0):,.2f}")
                                st.info(f"**所属部门**: {financial_record.get('部门名称', '')}")
                                st.info(f"**保管人**: {financial_record.get('保管人', '')}")
                        
                        # 价值比较
                        financial_value = financial_record.get('资产价值', 0)
                        physical_value = physical_record.get('资产价值', 0)
                        value_diff = financial_value - physical_value
                        
                        if abs(value_diff) > 0.01:
                            st.warning(f"⚠️ 价值差异: ¥{value_diff:,.2f}")
                        else:
                            st.success("✅ 资产价值一致")
                    else:
                        st.error("❌ 映射的财务资产记录不存在")
                else:
                    st.warning("⚠️ 该实物资产未找到对应的财务资产")
            else:
                st.error("❌ 未找到该实物台账编号对应的资产")
    
    elif query_type == "按资产名称搜索":
        st.subheader("🔍 资产名称搜索")
        
        search_term = st.text_input("请输入资产名称关键词", placeholder="例如: 电脑、桌子、空调")
        
        if search_term:
            # 在财务资产中搜索
            financial_results = [
                record for record in financial_data
                if search_term.lower() in record.get('资产名称', '').lower()
            ]
            
            # 在实物资产中搜索
            physical_results = [
                record for record in physical_data
                if search_term.lower() in record.get('固定资产名称', '').lower()
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 财务系统搜索结果 ({len(financial_results)}条)")
                if financial_results:
                    for record in financial_results[:10]:  # 限制显示前10条
                        with st.expander(f"💰 {record.get('资产名称', '')} - {record.get('财务系统编号', '')}"):
                            st.write(f"**资产分类**: {record.get('资产分类', '')}")
                            st.write(f"**资产价值**: ¥{record.get('资产价值', 0):,.2f}")
                            st.write(f"**所属部门**: {record.get('部门名称', '')}")
                            
                            # 检查是否有对应的实物资产
                            physical_code = f_to_p_mapping.get(record.get('财务系统编号'))
                            if physical_code:
                                st.success(f"✅ 已映射到实物资产: {physical_code}")
                            else:
                                st.warning("⚠️ 未找到对应的实物资产")
                else:
                    st.info("未找到匹配的财务资产")
            
            with col2:
                st.subheader(f"📋 实物台账搜索结果 ({len(physical_results)}条)")
                if physical_results:
                    for record in physical_results[:10]:  # 限制显示前10条
                        with st.expander(f"📦 {record.get('固定资产名称', '')} - {record.get('固定资产编号', '')}"):
                            st.write(f"**资产类型**: {record.get('固定资产类型', '')}")
                            st.write(f"**资产价值**: ¥{record.get('资产价值', 0):,.2f}")
                            st.write(f"**存放部门**: {record.get('存放部门', '')}")
                            st.write(f"**使用状态**: {record.get('使用状态', '')}")
                            
                            # 检查是否有对应的财务资产
                            financial_code = p_to_f_mapping.get(record.get('固定资产编号'))
                            if financial_code:
                                st.success(f"✅ 已映射到财务资产: {financial_code}")
                            else:
                                st.warning("⚠️ 未找到对应的财务资产")
                else:
                    st.info("未找到匹配的实物资产")
    
    else:  # 批量查询
        st.subheader("📋 批量查询")
        
        # 输入多个编号
        batch_input = st.text_area(
            "请输入要查询的编号（每行一个）",
            placeholder="FS001\nFS002\nPA001\nPA002",
            height=150
        )
        
        query_mode = st.radio("查询模式", ["财务系统编号", "实物台账编号"])
        
        if batch_input and st.button("开始批量查询"):
            codes = [code.strip() for code in batch_input.split('\n') if code.strip()]
            
            if codes:
                results = []
                
                for code in codes:
                    if query_mode == "财务系统编号":
                        financial_record = financial_index.get(code)
                        if financial_record:
                            physical_code = f_to_p_mapping.get(code)
                            physical_record = physical_index.get(physical_code) if physical_code else None
                            
                            results.append({
                                "查询编号": code,
                                "财务资产名称": financial_record.get('资产名称', ''),
                                "财务资产价值": financial_record.get('资产价值', 0),
                                "对应实物编号": physical_code or "未映射",
                                "实物资产名称": physical_record.get('固定资产名称', '') if physical_record else "未映射",
                                "实物资产价值": physical_record.get('资产价值', 0) if physical_record else 0,
                                "状态": "已映射" if physical_record else "未映射"
                            })
                        else:
                            results.append({
                                "查询编号": code,
                                "财务资产名称": "未找到",
                                "财务资产价值": 0,
                                "对应实物编号": "未找到",
                                "实物资产名称": "未找到",
                                "实物资产价值": 0,
                                "状态": "不存在"
                            })
                    
                    else:  # 实物台账编号
                        physical_record = physical_index.get(code)
                        if physical_record:
                            financial_code = p_to_f_mapping.get(code)
                            financial_record = financial_index.get(financial_code) if financial_code else None
                            
                            results.append({
                                "查询编号": code,
                                "实物资产名称": physical_record.get('固定资产名称', ''),
                                "实物资产价值": physical_record.get('资产价值', 0),
                                "对应财务编号": financial_code or "未映射",
                                "财务资产名称": financial_record.get('资产名称', '') if financial_record else "未映射",
                                "财务资产价值": financial_record.get('资产价值', 0) if financial_record else 0,
                                "状态": "已映射" if financial_record else "未映射"
                            })
                        else:
                            results.append({
                                "查询编号": code,
                                "实物资产名称": "未找到",
                                "实物资产价值": 0,
                                "对应财务编号": "未找到",
                                "财务资产名称": "未找到",
                                "财务资产价值": 0,
                                "状态": "不存在"
                            })
                
                # 显示结果
                if results:
                    df = pd.DataFrame(results)
                    st.subheader(f"📊 批量查询结果 (共{len(results)}条)")
                    st.dataframe(df, use_container_width=True)
                    
                    # 统计信息
                    mapped_count = len([r for r in results if r["状态"] == "已映射"])
                    unmapped_count = len([r for r in results if r["状态"] == "未映射"])
                    not_found_count = len([r for r in results if r["状态"] == "不存在"])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("已映射", mapped_count)
                    with col2:
                        st.metric("未映射", unmapped_count)
                    with col3:
                        st.metric("不存在", not_found_count)
                    
                    # 导出功能
                    if st.button("📥 导出查询结果"):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name='批量查询结果', index=False)
                        output.seek(0)
                        st.download_button(
                            label="下载Excel文件",
                            data=output,
                            file_name=f"批量查询结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

def data_statistics_page():
    """数据统计页面"""
    st.header("📊 数据统计分析")
    
    # 加载数据
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)
    
    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 请先导入所有必要的数据")
        return
    
    # 基础统计信息
    st.subheader("📈 基础数据统计")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("财务资产总数", len(financial_data))
    
    with col2:
        st.metric("实物资产总数", len(physical_data))
    
    with col3:
        st.metric("映射关系总数", len(mapping_data))
    
    with col4:
        # 计算映射覆盖率
        f_to_p_mapping, p_to_f_mapping = create_mapping_index(mapping_data)
        coverage_rate = len(f_to_p_mapping) / len(financial_data) * 100 if financial_data else 0
        st.metric("映射覆盖率", f"{coverage_rate:.1f}%")
    
    # 映射状态分析
    st.subheader("🔗 映射状态分析")
    
    # 创建索引
    financial_index = create_data_index(financial_data, "财务系统编号")
    physical_index = create_data_index(physical_data, "固定资产编号")
    
    # 统计映射状态
    mapped_financial = len(f_to_p_mapping)
    unmapped_financial = len(financial_data) - mapped_financial
    mapped_physical = len(p_to_f_mapping)
    unmapped_physical = len(physical_data) - mapped_physical
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 财务资产映射状态")
        financial_mapping_data = {
            "状态": ["已映射", "未映射"],
            "数量": [mapped_financial, unmapped_financial],
            "比例": [f"{mapped_financial/len(financial_data)*100:.1f}%" if financial_data else "0%",
                    f"{unmapped_financial/len(financial_data)*100:.1f}%" if financial_data else "0%"]
        }
        st.dataframe(pd.DataFrame(financial_mapping_data), use_container_width=True)
    
    with col2:
        st.subheader("📋 实物资产映射状态")
        physical_mapping_data = {
            "状态": ["已映射", "未映射"],
            "数量": [mapped_physical, unmapped_physical],
            "比例": [f"{mapped_physical/len(physical_data)*100:.1f}%" if physical_data else "0%",
                    f"{unmapped_physical/len(physical_data)*100:.1f}%" if physical_data else "0%"]
        }
        st.dataframe(pd.DataFrame(physical_mapping_data), use_container_width=True)
    
    # 价值统计分析
    st.subheader("💰 资产价值统计")
    
    # 计算总价值
    financial_total_value = sum(record.get("资产价值", 0) for record in financial_data)
    physical_total_value = sum(record.get("资产价值", 0) for record in physical_data)
    
    # 计算已映射资产价值
    mapped_financial_value = sum(
        financial_index.get(code, {}).get("资产价值", 0)
        for code in f_to_p_mapping.keys()
    )
    mapped_physical_value = sum(
        physical_index.get(code, {}).get("资产价值", 0)
        for code in p_to_f_mapping.keys()
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("财务资产总价值", f"¥{financial_total_value:,.2f}")
    
    with col2:
        st.metric("实物资产总价值", f"¥{physical_total_value:,.2f}")
    
    with col3:
        st.metric("已映射财务价值", f"¥{mapped_financial_value:,.2f}")
    
    with col4:
        st.metric("已映射实物价值", f"¥{mapped_physical_value:,.2f}")
    
    # 价值差异统计
    st.subheader("💰 价值差异统计")
    
    # 创建索引
    financial_index = create_data_index(financial_data, "财务系统编号")
    physical_index = create_data_index(physical_data, "固定资产编号")
    f_to_p_mapping, _ = create_mapping_index(mapping_data)
    
    value_differences = []
    for financial_code, physical_code in f_to_p_mapping.items():
        financial_record = financial_index.get(financial_code)
        physical_record = physical_index.get(physical_code)
        
        if financial_record and physical_record:
            diff = financial_record.get("资产价值", 0) - physical_record.get("资产价值", 0)
            if abs(diff) > 0.01:
                value_differences.append({
                    "财务系统编号": financial_code,
                    "实物台账编号": physical_code,
                    "财务资产名称": financial_record.get("资产名称", ""),
                    "实物资产名称": physical_record.get("固定资产名称", ""),
                    "财务价值": financial_record.get("资产价值", 0),
                    "实物价值": physical_record.get("资产价值", 0),
                    "差异金额": diff
                })

    if value_differences:
        total_diff = sum(abs(d["差异金额"]) for d in value_differences)
        avg_diff = total_diff / len(value_differences)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("差异项数", len(value_differences))
        with col2:
            st.metric("差异总额", f"¥{total_diff:,.2f}")
        with col3:
            st.metric("平均差异", f"¥{avg_diff:,.2f}")
        
        # 显示差异明细
        with st.expander("查看价值差异明细"):
            df_diff = pd.DataFrame(value_differences)
            df_diff = df_diff.sort_values(by="差异金额", key=abs, ascending=False)
            st.dataframe(df_diff.head(20), use_container_width=True)
    else:
        st.success("✅ 所有已匹配资产的价值完全一致")

def all_data_view_page():
    """查看全部对应关系页面"""
    st.header("📋 全部资产对应关系")
    
    # 加载数据
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)
    
    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 请先导入所有必要的数据")
        return
    
    # 创建索引
    financial_index = create_data_index(financial_data, "财务系统编号")
    physical_index = create_data_index(physical_data, "固定资产编号")
    f_to_p_mapping, p_to_f_mapping = create_mapping_index(mapping_data)
    
    # 选择查看模式
    view_mode = st.selectbox("选择查看模式", ["对应关系汇总", "财务系统明细", "实物台账明细", "未匹配资产"])
    
    if view_mode == "对应关系汇总":
        st.subheader("🔗 完整对应关系汇总")
        
        # 构建汇总数据
        mapping_summary = []
        for financial_code, physical_code in f_to_p_mapping.items():
            financial_record = financial_index.get(financial_code)
            physical_record = physical_index.get(physical_code)
            
            if financial_record and physical_record:
                mapping_summary.append({
                    "财务系统编号": financial_code,
                    "财务资产名称": financial_record.get("资产名称", ""),
                    "财务资产价值": financial_record.get("资产价值", 0),
                    "财务部门": financial_record.get("部门名称", ""),
                    "实物台账编号": physical_code,
                    "实物资产名称": physical_record.get("固定资产名称", ""),
                    "实物资产价值": physical_record.get("资产价值", 0),
                    "实物部门": physical_record.get("存放部门", ""),
                    "价值差异": financial_record.get("资产价值", 0) - physical_record.get("资产价值", 0)
                })
        
        if mapping_summary:
            df = pd.DataFrame(mapping_summary)
            
            # 添加筛选功能
            col1, col2, col3 = st.columns(3)
            with col1:
                dept_filter = st.selectbox("按部门筛选", ["全部"] + list(set(df["财务部门"].unique()) | set(df["实物部门"].unique())))
            with col2:
                diff_filter = st.selectbox("按差异筛选", ["全部", "有差异", "无差异"])
            with col3:
                search_term = st.text_input("搜索资产名称")
            
            # 应用筛选
            filtered_df = df.copy()
            
            if dept_filter != "全部":
                filtered_df = filtered_df[(filtered_df["财务部门"] == dept_filter) | (filtered_df["实物部门"] == dept_filter)]
            
            if diff_filter == "有差异":
                filtered_df = filtered_df[filtered_df["价值差异"].abs() > 0.01]
            elif diff_filter == "无差异":
                filtered_df = filtered_df[filtered_df["价值差异"].abs() <= 0.01]
            
            if search_term:
                filtered_df = filtered_df[
                    filtered_df["财务资产名称"].str.contains(search_term, case=False, na=False) |
                    filtered_df["实物资产名称"].str.contains(search_term, case=False, na=False)
                ]
            
            st.info(f"共 {len(filtered_df)} 条记录")
            st.dataframe(filtered_df, use_container_width=True)
            
            # 导出功能
            if st.button("📥 导出为Excel"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_df.to_excel(writer, sheet_name='对应关系汇总', index=False)
                output.seek(0)
                st.download_button(
                    label="下载Excel文件",
                    data=output,
                    file_name=f"资产对应关系汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    elif view_mode == "财务系统明细":
        st.subheader("📊 财务系统资产明细")
        
        df = pd.DataFrame(financial_data)
        
        # 添加匹配状态列
        df["匹配状态"] = df["财务系统编号"].apply(lambda x: "已匹配" if x in f_to_p_mapping else "未匹配")
        
        # 筛选功能
        col1, col2 = st.columns(2)
        with col1:
            match_filter = st.selectbox("匹配状态", ["全部", "已匹配", "未匹配"])
        with col2:
            search_term = st.text_input("搜索资产", key="financial_search")
        
        filtered_df = df.copy()
        
        if match_filter != "全部":
            filtered_df = filtered_df[filtered_df["匹配状态"] == match_filter]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df["资产名称"].str.contains(search_term, case=False, na=False) |
                filtered_df["财务系统编号"].str.contains(search_term, case=False, na=False)
            ]
        
        st.info(f"共 {len(filtered_df)} 条记录")
        display_columns = ["财务系统编号", "资产名称", "资产分类", "资产价值", "部门名称", "保管人", "匹配状态"]
        st.dataframe(filtered_df[display_columns], use_container_width=True)
    
    elif view_mode == "实物台账明细":
        st.subheader("📋 实物台账资产明细")
        
        df = pd.DataFrame(physical_data)
        
        # 添加匹配状态列
        df["匹配状态"] = df["固定资产编号"].apply(lambda x: "已匹配" if x in p_to_f_mapping else "未匹配")
        
        # 筛选功能
        col1, col2 = st.columns(2)
        with col1:
            match_filter = st.selectbox("匹配状态", ["全部", "已匹配", "未匹配"], key="physical_match")
        with col2:
            search_term = st.text_input("搜索资产", key="physical_search")
        
        filtered_df = df.copy()
        
        if match_filter != "全部":
            filtered_df = filtered_df[filtered_df["匹配状态"] == match_filter]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df["固定资产名称"].str.contains(search_term, case=False, na=False) |
                filtered_df["固定资产编号"].str.contains(search_term, case=False, na=False)
            ]
        
        st.info(f"共 {len(filtered_df)} 条记录")
        display_columns = ["固定资产编号", "固定资产名称", "固定资产类型", "资产价值", "存放部门", "保管人", "使用状态", "匹配状态"]
        st.dataframe(filtered_df[display_columns], use_container_width=True)
    
    else:  # 未匹配资产
        st.subheader("⚠️ 未匹配资产列表")
        
        tab1, tab2 = st.tabs(["未匹配财务资产", "未匹配实物资产"])
        
        with tab1:
            unmatched_financial = [f for f in financial_data if f.get("财务系统编号") not in f_to_p_mapping]
            if unmatched_financial:
                df = pd.DataFrame(unmatched_financial)
                st.info(f"共 {len(df)} 条未匹配财务资产")
                display_columns = ["财务系统编号", "资产名称", "资产分类", "资产价值", "部门名称", "保管人"]
                st.dataframe(df[display_columns], use_container_width=True)
                
                # 导出未匹配财务资产
                if st.button("📥 导出未匹配财务资产", key="export_unmatched_financial"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df[display_columns].to_excel(writer, sheet_name='未匹配财务资产', index=False)
                    output.seek(0)
                    st.download_button(
                        label="下载Excel文件",
                        data=output,
                        file_name=f"未匹配财务资产_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_unmatched_financial"
                    )
            else:
                st.success("✅ 所有财务资产都已匹配")
        
        with tab2:
            unmatched_physical = [p for p in physical_data if p.get("固定资产编号") not in p_to_f_mapping]
            if unmatched_physical:
                df = pd.DataFrame(unmatched_physical)
                st.info(f"共 {len(df)} 条未匹配实物资产")
                display_columns = ["固定资产编号", "固定资产名称", "固定资产类型", "资产价值", "存放部门", "保管人", "使用状态"]
                st.dataframe(df[display_columns], use_container_width=True)
                
                # 导出未匹配实物资产
                if st.button("📥 导出未匹配实物资产", key="export_unmatched_physical"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df[display_columns].to_excel(writer, sheet_name='未匹配实物资产', index=False)
                    output.seek(0)
                    st.download_button(
                        label="下载Excel文件",
                        data=output,
                        file_name=f"未匹配实物资产_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_unmatched_physical"
                    )
            else:
                st.success("✅ 所有实物资产都已匹配")

# ========== 主函数 ==========

def main():
    """主函数"""
    st.title("🔗 资产映射关系查询系统")
    
    # 侧边栏导航
    with st.sidebar:
        st.header("📋 系统导航")
        page = st.selectbox(
            "选择功能页面",
            ["📥 数据导入", "🔍 映射查询", "📊 数据统计", "📋 全部数据"],
            key="page_selector"
        )
        
        st.markdown("---")
        st.markdown("### 📝 使用说明")
        st.markdown("""
        1. **数据导入**：上传Excel文件导入数据
        2. **映射查询**：查询资产对应关系
        3. **数据统计**：查看统计分析结果
        4. **全部数据**：浏览所有数据记录
        """)
        
        # 显示数据状态
        st.markdown("---")
        st.markdown("### 📊 数据状态")
        financial_count = len(load_data(FINANCIAL_DATA_FILE))
        physical_count = len(load_data(PHYSICAL_DATA_FILE))
        mapping_count = len(load_data(MAPPING_DATA_FILE))
        
        st.info(f"""
        - 财务资产：{financial_count} 条
        - 实物资产：{physical_count} 条
        - 映射关系：{mapping_count} 条
        """)
    
    # 根据选择显示对应页面
    if page == "📥 数据导入":
        data_import_page()
    elif page == "🔍 映射查询":
        mapping_query_page()
    elif page == "📊 数据统计":
        data_statistics_page()
    elif page == "📋 全部数据":
        all_data_view_page()

# ========== 程序入口 ==========

if __name__ == "__main__":
    main()
