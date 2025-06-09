import streamlit as st

# 页面配置必须是第一个命令 - 修复从第2行开始
st.set_page_config(
    page_title="资产映射关系查询系统",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 然后导入其他库 - 从第9行开始
import pandas as pd
import json
import os
from datetime import datetime
import io
import subprocess
import sys

# 检查并安装依赖 - 从第17行开始，移动到页面配置之后
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        st.info(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(package)

# 确保openpyxl已安装 - 从第25行开始
try:
    import openpyxl
except ImportError:
    st.warning("正在安装必要的依赖包，请稍候...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
        import openpyxl
        st.success("依赖包安装成功！")
    except:
        st.error("无法自动安装依赖包，请联系管理员")

# 数据文件路径 - 从第36行开始
FINANCIAL_DATA_FILE = "financial_assets.json"
PHYSICAL_DATA_FILE = "physical_assets.json"
MAPPING_DATA_FILE = "asset_mapping.json"

# ========== 添加缺失的函数定义 ==========

@st.cache_data
def load_data(filename):
    """加载JSON数据文件"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        return []

def save_data(filename, data):
    """保存数据到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存数据失败: {e}")
        return False

def create_demo_data():
    """创建演示数据"""
    # 演示财务数据
    demo_financial = [
        {"财务系统编号": "F001", "资产名称": "办公电脑", "资产分类": "电子设备", "资产价值": 5000.00, "部门名称": "行政部", "保管人": "张三"},
        {"财务系统编号": "F002", "资产名称": "打印机", "资产分类": "办公设备", "资产价值": 2000.00, "部门名称": "财务部", "保管人": "李四"},
        {"财务系统编号": "F003", "资产名称": "办公桌", "资产分类": "家具", "资产价值": 800.00, "部门名称": "人事部", "保管人": "王五"},
        {"财务系统编号": "F004", "资产名称": "空调", "资产分类": "电器", "资产价值": 3000.00, "部门名称": "总经理室", "保管人": "赵六"}
    ]
    
    # 演示实物数据
    demo_physical = [
        {"固定资产编号": "P001", "固定资产名称": "办公电脑", "固定资产类型": "电子设备", "资产价值": 5000.00, "存放部门": "行政部", "保管人": "张三"},
        {"固定资产编号": "P002", "固定资产名称": "打印机", "固定资产类型": "办公设备", "资产价值": 2000.00, "存放部门": "财务部", "保管人": "李四"},
        {"固定资产编号": "P003", "固定资产名称": "办公桌", "固定资产类型": "家具", "资产价值": 800.00, "存放部门": "人事部", "保管人": "王五"},
        {"固定资产编号": "P004", "固定资产名称": "空调", "固定资产类型": "电器", "资产价值": 3000.00, "存放部门": "总经理室", "保管人": "赵六"}
    ]
    
    # 演示映射关系
    demo_mapping = [
        {"财务系统编号": "F001", "实物台账编号": "P001"},
        {"财务系统编号": "F002", "实物台账编号": "P002"},
        {"财务系统编号": "F003", "实物台账编号": "P003"},
        {"财务系统编号": "F004", "实物台账编号": "P004"}
    ]
    
    # 如果文件不存在，创建演示数据
    if not os.path.exists(FINANCIAL_DATA_FILE):
        save_data(FINANCIAL_DATA_FILE, demo_financial)
    if not os.path.exists(PHYSICAL_DATA_FILE):
        save_data(PHYSICAL_DATA_FILE, demo_physical)
    if not os.path.exists(MAPPING_DATA_FILE):
        save_data(MAPPING_DATA_FILE, demo_mapping)

def show_financial_summary(financial_data):
    """显示财务系统汇总信息"""
    if not financial_data:
        st.info("暂无财务数据")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("财务资产总数", len(financial_data))
    with col2:
        total_value = sum(item.get("资产价值", 0) for item in financial_data)
        st.metric("资产总价值", f"¥{total_value:,.2f}")
    with col3:
        categories = set(item.get("资产分类", "") for item in financial_data)
        st.metric("资产分类数", len(categories))

def show_physical_summary(physical_data):
    """显示实物台账汇总信息"""
    if not physical_data:
        st.info("暂无实物数据")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("实物资产总数", len(physical_data))
    with col2:
        total_value = sum(item.get("资产价值", 0) for item in physical_data)
        st.metric("资产总价值", f"¥{total_value:,.2f}")
    with col3:
        types = set(item.get("固定资产类型", "") for item in physical_data)
        st.metric("资产类型数", len(types))

def mapping_query_page():
    """资产映射查询页面"""
    st.header("🔍 快速查询")
    
    # 搜索框
    search_term = st.text_input("请输入资产编号或名称", placeholder="例如：F001 或 办公电脑")
    
    if search_term:
        # 加载数据
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)
        
        # 搜索逻辑
        results = []
        for mapping in mapping_data:
            financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), None)
            physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), None)
            
            if financial_record and physical_record:
                # 检查是否匹配搜索条件
                if (search_term.lower() in financial_record.get("财务系统编号", "").lower() or
                    search_term.lower() in financial_record.get("资产名称", "").lower() or
                    search_term.lower() in physical_record.get("固定资产编号", "").lower() or
                    search_term.lower() in physical_record.get("固定资产名称", "").lower()):
                    
                    results.append({
                        "财务系统编号": financial_record["财务系统编号"],
                        "实物台账编号": physical_record["固定资产编号"],
                        "资产名称": financial_record["资产名称"],
                        "资产价值": financial_record["资产价值"],
                        "部门": financial_record.get("部门名称", ""),
                        "保管人": financial_record.get("保管人", "")
                    })
        
        if results:
            st.success(f"找到 {len(results)} 条匹配记录")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("未找到匹配的记录")

# ========== 你的原有函数保持不变 ==========

def all_data_view_page():
    """查看全部对应关系页面"""
    st.header("📋 全部资产对应关系")

    # 加载数据
    financial_data = load_data(FINANCIAL_DATA_FILE)
    physical_data = load_data(PHYSICAL_DATA_FILE)
    mapping_data = load_data(MAPPING_DATA_FILE)

    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 数据正在加载中...")
        return

    # 选择查看模式
    view_mode = st.selectbox("选择查看模式", ["对应关系汇总", "财务系统明细", "实物台账明细"])

    if view_mode == "对应关系汇总":
        st.subheader("🔗 完整对应关系汇总")

        # 构建完整的对应关系表
        mapping_summary = []
        for mapping in mapping_data:
            financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), {})
            physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), {})

            if financial_record and physical_record:
                summary_record = {
                    "财务系统编号": mapping["财务系统编号"],
                    "实物台账编号": mapping["实物台账编号"],
                    "财务-资产名称": financial_record.get("资产名称", ""),
                    "实物-资产名称": physical_record.get("固定资产名称", ""),
                    "财务-价值": financial_record.get("资产价值", 0),
                    "实物-价值": physical_record.get("资产价值", 0),
                    "价值差异": financial_record.get("资产价值", 0) - physical_record.get("资产价值", 0),
                    "财务-部门": financial_record.get("部门名称", ""),
                    "实物-部门": physical_record.get("存放部门", ""),
                    "财务-保管人": financial_record.get("保管人", ""),
                    "实物-保管人": physical_record.get("保管人", "")
                }
                mapping_summary.append(summary_record)

        if mapping_summary:
            summary_df = pd.DataFrame(mapping_summary)

            # 显示汇总统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("映射关系数", len(summary_df))
            with col2:
                total_financial = summary_df["财务-价值"].sum()
                st.metric("财务系统总值", f"¥{total_financial:,.2f}")
            with col3:
                total_physical = summary_df["实物-价值"].sum()
                st.metric("实物台账总值", f"¥{total_physical:,.2f}")
            with col4:
                total_diff = summary_df["价值差异"].sum()
                st.metric("总差异", f"¥{total_diff:,.2f}")

            # 显示详细表格
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无完整的对应关系数据")

    elif view_mode == "财务系统明细":
        # 显示财务系统汇总
        show_financial_summary(financial_data)

        st.markdown("---")
        st.subheader("📊 财务系统-资产明细账")

        # 创建DataFrame
        df = pd.DataFrame(financial_data)

        # 搜索功能
        search_term = st.text_input("🔍 搜索财务资产", placeholder="输入资产名称或编号")
        if search_term:
            mask = (
                    df['资产名称'].str.contains(search_term, case=False, na=False) |
                    df['财务系统编号'].str.contains(search_term, case=False, na=False)
            )
            df = df[mask]

        # 显示数据表格
        if len(df) > 0:
            st.dataframe(df, use_container_width=True, hide_index=True)

    else:  # 实物台账明细
        # 显示实物台账汇总
        show_physical_summary(physical_data)

        st.markdown("---")
        st.subheader("📋 实物台账明细")

        # 创建DataFrame
        df = pd.DataFrame(physical_data)

        # 搜索功能
        search_term = st.text_input("🔍 搜索实物资产", placeholder="输入资产名称或编号")
        if search_term:
            mask = (
                    df['固定资产名称'].str.contains(search_term, case=False, na=False) |
                    df['固定资产编号'].str.contains(search_term, case=False, na=False)
            )
            df = df[mask]

        # 显示数据表格
        if len(df) > 0:
            st.dataframe(df, use_container_width=True, hide_index=True)


def data_statistics_page():
    """数据统计分析页面"""
    st.header("📊 数据统计分析")

    # 加载数据
    financial_data = load_data(FINANCIAL_DATA_FILE)
    physical_data = load_data(PHYSICAL_DATA_FILE)
    mapping_data = load_data(MAPPING_DATA_FILE)

    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 数据正在加载中...")
        return

    # 基础统计信息
    st.subheader("📈 基础统计")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("财务系统资产数", len(financial_data))
    with col2:
        st.metric("实物台账资产数", len(physical_data))
    with col3:
        st.metric("已建立映射关系数", len(mapping_data))

    # 匹配率分析
    st.subheader("🔗 匹配率分析")

    # 计算财务系统的匹配率
    financial_mapped = set(m["财务系统编号"] for m in mapping_data)
    financial_match_rate = len(financial_mapped) / len(financial_data) * 100 if financial_data else 0

    # 计算实物台账的匹配率
    physical_mapped = set(m["实物台账编号"] for m in mapping_data)
    physical_match_rate = len(physical_mapped) / len(physical_data) * 100 if physical_data else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("财务系统匹配率", f"{financial_match_rate:.1f}%")
        st.progress(financial_match_rate / 100)
    with col2:
        st.metric("实物台账匹配率", f"{physical_match_rate:.1f}%")
        st.progress(physical_match_rate / 100)

    # 价值分析
    st.subheader("💰 价值分析")

    # 计算总价值
    total_financial_value = sum(item["资产价值"] for item in financial_data)
    total_physical_value = sum(item["资产价值"] for item in physical_data)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("财务系统总价值", f"¥{total_financial_value:,.2f}")
    with col2:
        st.metric("实物台账总价值", f"¥{total_physical_value:,.2f}")
    with col3:
        value_diff = total_financial_value - total_physical_value
        st.metric("价值差异", f"¥{value_diff:,.2f}")

    # 差异分析
    st.subheader("⚠️ 差异分析")

    # 计算已匹配资产的价值差异
    value_differences = []
    for mapping in mapping_data:
        financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), None)
        physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), None)

        if financial_record and physical_record:
            diff = financial_record["资产价值"] - physical_record["资产价值"]
            if abs(diff) > 0.01:
                value_differences.append({
                    "财务系统编号": financial_record["财务系统编号"],
                    "实物台账编号": physical_record["固定资产编号"],
                    "财务资产名称": financial_record["资产名称"],
                    "实物资产名称": physical_record["固定资产名称"],
                    "财务价值": financial_record["资产价值"],
                    "实物价值": physical_record["资产价值"],
                    "差异金额": diff,
                    "差异率": (diff / financial_record["资产价值"] * 100) if financial_record["资产价值"] > 0 else 0
                })

    if value_differences:
        st.warning(f"发现 {len(value_differences)} 项资产存在价值差异")

        # 显示差异统计
        df_diff = pd.DataFrame(value_differences)
        total_diff = df_diff["差异金额"].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("差异项数", len(value_differences))
        with col2:
            st.metric("差异总额", f"¥{total_diff:,.2f}")
        with col3:
            avg_diff_rate = df_diff["差异率"].mean()
            st.metric("平均差异率", f"{avg_diff_rate:.2f}%")

        # 显示差异明细
        with st.expander("查看差异明细"):
            st.dataframe(df_diff, use_container_width=True, hide_index=True)
    else:
        st.success("✅ 所有已匹配资产的价值完全一致")

    # 未匹配资产统计
    st.subheader("📋 未匹配资产")

    # 未匹配的财务资产
    unmatched_financial = [f for f in financial_data if f["财务系统编号"] not in financial_mapped]
    # 未匹配的实物资产
    unmatched_physical = [p for p in physical_data if p["固定资产编号"] not in physical_mapped]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("未匹配财务资产", len(unmatched_financial))
        if unmatched_financial:
            with st.expander("查看未匹配财务资产"):
                df_unmatched_f = pd.DataFrame(unmatched_financial)
                display_cols = ["财务系统编号", "资产名称", "资产分类", "资产价值"]
                st.dataframe(df_unmatched_f[display_cols], use_container_width=True, hide_index=True)

    with col2:
        st.metric("未匹配实物资产", len(unmatched_physical))
        if unmatched_physical:
            with st.expander("查看未匹配实物资产"):
                df_unmatched_p = pd.DataFrame(unmatched_physical)
                display_cols = ["固定资产编号", "固定资产名称", "固定资产类型", "资产价值"]
                st.dataframe(df_unmatched_p[display_cols], use_container_width=True, hide_index=True)


def admin_page():
    """管理员页面 - 数据导入功能"""
    st.header("🔧 系统管理")

    # 简单的管理员验证
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("⚠️ 此功能仅限管理员使用")
        admin_password = st.text_input("管理员密码", type="password")

        if st.button("登录"):
            if admin_password == "admin123":  # 你可以修改这个密码
                st.session_state.admin_authenticated = True
                st.success("✅ 管理员登录成功")
                st.rerun()
            else:
                st.error("❌ 密码错误")

        st.info("💡 提示：管理员可以导入和更新系统数据")
        return

    # 管理员功能
    st.success("🔓 管理员模式")
    if st.button("🚪 退出管理员模式"):
        st.session_state.admin_authenticated = False
        st.rerun()

    st.markdown("---")

    # 数据导入功能
    st.subheader("📥 数据导入")
    tab1, tab2, tab3 = st.tabs(["财务系统数据", "实物台账数据", "关系对照表"])
    with tab1:
        st.markdown("### 📊 财务系统数据导入")
        financial_file = st.file_uploader("上传财务系统Excel文件", type=['xlsx', 'xls'], key="admin_financial")

        if financial_file:
            try:
                df = pd.read_excel(financial_file)
                st.success(f"✅ 文件读取成功：{len(df)}行数据")

                with st.expander("数据预览"):
                    st.dataframe(df.head())

                if st.button("导入财务数据", key="admin_import_financial"):
    try:
        # 转换DataFrame为所需格式
        financial_records = []
        for _, row in df.iterrows():
            record = {
                "财务系统编号": str(row.get("财务系统编号", "")),
                "资产名称": str(row.get("资产名称", "")),
                "资产分类": str(row.get("资产分类", "")),
                "资产价值": float(row.get("资产价值", 0)),
                "部门名称": str(row.get("部门名称", "")),
                "保管人": str(row.get("保管人", ""))
            }
            financial_records.append(record)
        
        # 保存数据
        if save_data(FINANCIAL_DATA_FILE, financial_records):
            st.success(f"✅ 成功导入 {len(financial_records)} 条财务数据")
            st.cache_data.clear()  # 清除缓存
        else:
            st.error("❌ 数据保存失败")
    except Exception as e:
        st.error(f"❌ 数据导入失败：{str(e)}")

            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")

    with tab2:
        st.markdown("### 📋 实物台账数据导入")
        physical_file = st.file_uploader("上传实物台账Excel文件", type=['xlsx', 'xls'], key="admin_physical")

        if physical_file:
            try:
                df = pd.read_excel(physical_file)
                st.success(f"✅ 文件读取成功：{len(df)}行数据")

                with st.expander("数据预览"):
                    st.dataframe(df.head())

                if st.button("导入实物数据", key="admin_import_physical"):
    try:
        # 转换DataFrame为所需格式
        physical_records = []
        for _, row in df.iterrows():
            record = {
                "固定资产编号": str(row.get("固定资产编号", "")),
                "固定资产名称": str(row.get("固定资产名称", "")),
                "固定资产类型": str(row.get("固定资产类型", "")),
                "资产价值": float(row.get("资产价值", 0)),
                "存放部门": str(row.get("存放部门", "")),
                "保管人": str(row.get("保管人", ""))
            }
            physical_records.append(record)
        
        # 保存数据
        if save_data(PHYSICAL_DATA_FILE, physical_records):
            st.success(f"✅ 成功导入 {len(physical_records)} 条实物数据")
            st.cache_data.clear()  # 清除缓存
        else:
            st.error("❌ 数据保存失败")
    except Exception as e:
        st.error(f"❌ 数据导入失败：{str(e)}")

            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")

    with tab3:
        st.markdown("### 🔗 关系对照表导入")
        mapping_file = st.file_uploader("上传关系对照表Excel文件", type=['xlsx', 'xls'], key="admin_mapping")

        if mapping_file:
            try:
                df = pd.read_excel(mapping_file)
                st.success(f"✅ 文件读取成功：{len(df)}行数据")

                with st.expander("数据预览"):
                    st.dataframe(df.head())

                if st.button("导入对照关系", key="admin_import_mapping"):
    try:
        # 转换DataFrame为所需格式
        mapping_records = []
        for _, row in df.iterrows():
            record = {
                "财务系统编号": str(row.get("财务系统编号", "")),
                "实物台账编号": str(row.get("实物台账编号", ""))
            }
            mapping_records.append(record)
        
        # 保存数据
        if save_data(MAPPING_DATA_FILE, mapping_records):
            st.success(f"✅ 成功导入 {len(mapping_records)} 条映射关系")
            st.cache_data.clear()  # 清除缓存
        else:
            st.error("❌ 数据保存失败")
    except Exception as e:
        st.error(f"❌ 数据导入失败：{str(e)}")


            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")


def main():
    """主函数"""
    # 初始化演示数据
    create_demo_data()

    st.title("🔗 资产映射关系查询系统")

    # 添加系统说明
    with st.expander("📖 系统说明", expanded=False):
        st.markdown("""
        ### 🎯 系统功能
        - **🔍 资产查询**：通过编号或名称查找资产对应关系
        - **📊 数据浏览**：查看完整的资产清单和对应关系
        - **📈 统计分析**：查看匹配率和差异分析
        - **🔧 系统管理**：管理员可以导入和更新数据

        ### 👥 使用说明
        1. **快速查询**：在查询页面输入资产编号或名称进行查找
        2. **数据浏览**：查看所有财务系统和实物台账数据
        3. **统计分析**：了解系统整体匹配情况和差异
        4. **系统管理**：管理员可以导入新的Excel数据

        ### 📊 演示数据
        系统已预装演示数据，包含4项资产的完整对应关系，您可以直接体验查询功能。

        ### 📞 技术支持
        如需导入实际数据或遇到问题，请联系系统管理员。
        """)

    # 侧边栏导航
    st.sidebar.title("🧭 导航菜单")

    # 显示当前数据状态
    financial_count = len(load_data(FINANCIAL_DATA_FILE))
    physical_count = len(load_data(PHYSICAL_DATA_FILE))
    mapping_count = len(load_data(MAPPING_DATA_FILE))

    st.sidebar.success(f"""
    ✅ 系统数据状态：
    - 财务系统：{financial_count} 条
    - 实物台账：{physical_count} 条  
    - 映射关系：{mapping_count} 条

    📅 最后更新：{datetime.now().strftime('%Y-%m-%d')}
    """)

    # 主导航菜单
    page = st.sidebar.radio(
        "选择功能模块",
        ["🔍 快速查询", "📋 数据浏览", "📊 统计分析", "🔧 系统管理"],
        help="选择要使用的功能模块"
    )

    # 添加快速操作
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ 快速操作")
    if st.sidebar.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.success("✅ 数据已刷新")
        st.rerun()

    # 根据选择显示不同页面
    if page == "🔍 快速查询":
        mapping_query_page()
    elif page == "📋 数据浏览":
        all_data_view_page()
    elif page == "📊 统计分析":
        data_statistics_page()
    elif page == "🔧 系统管理":
        admin_page()

    # 页脚信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
    🔗 资产映射关系查询系统<br>
    版本 1.0.0<br>
    © 2024 技术支持
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
