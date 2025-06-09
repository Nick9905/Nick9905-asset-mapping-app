import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
import subprocess
import sys

# 检查并安装依赖
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        st.info(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(package)

# 确保openpyxl已安装
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

# 页面配置
st.set_page_config(
    page_title="资产映射关系查询系统",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据文件路径
FINANCIAL_DATA_FILE = "financial_assets.json"
PHYSICAL_DATA_FILE = "physical_assets.json"
MAPPING_DATA_FILE = "asset_mapping.json"


@st.cache_data
def load_data(file_path):
    """加载数据 - 带缓存"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_data(data, file_path):
    """保存数据"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def create_demo_data():
    """创建演示数据"""
    if not os.path.exists(FINANCIAL_DATA_FILE):
        demo_financial = [
            {
                "财务系统编号": "FS001",
                "序号": "1",
                "所属公司": "科技有限公司",
                "资产分类": "电子设备",
                "资产编号": "AS001",
                "资产名称": "联想ThinkPad笔记本电脑",
                "资产规格": "ThinkPad X1 Carbon",
                "取得日期": "2023-01-15",
                "资产价值": 8500.0,
                "累积折旧": 2125.0,
                "账面价值": 6375.0,
                "部门名称": "信息技术部",
                "保管人": "张三",
                "备注": "正常使用",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 1
            },
            {
                "财务系统编号": "FS002",
                "序号": "2",
                "所属公司": "科技有限公司",
                "资产分类": "办公家具",
                "资产编号": "AS002",
                "资产名称": "实木办公桌",
                "资产规格": "1.6m*0.8m*0.75m",
                "取得日期": "2023-02-01",
                "资产价值": 1800.0,
                "累积折旧": 450.0,
                "账面价值": 1350.0,
                "部门名称": "行政管理部",
                "保管人": "李四",
                "备注": "良好",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 2
            },
            {
                "财务系统编号": "FS003",
                "序号": "3",
                "所属公司": "科技有限公司",
                "资产分类": "交通工具",
                "资产编号": "AS003",
                "资产名称": "奥迪A4L轿车",
                "资产规格": "2.0T自动挡",
                "取得日期": "2022-06-01",
                "资产价值": 280000.0,
                "累积折旧": 84000.0,
                "账面价值": 196000.0,
                "部门名称": "销售部",
                "保管人": "王五",
                "备注": "公务用车",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 3
            },
            {
                "财务系统编号": "FS004",
                "序号": "4",
                "所属公司": "科技有限公司",
                "资产分类": "电子设备",
                "资产编号": "AS004",
                "资产名称": "激光打印机",
                "资产规格": "HP LaserJet Pro M404n",
                "取得日期": "2023-03-10",
                "资产价值": 2200.0,
                "累积折旧": 440.0,
                "账面价值": 1760.0,
                "部门名称": "行政管理部",
                "保管人": "赵六",
                "备注": "共用设备",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 4
            }
        ]
        save_data(demo_financial, FINANCIAL_DATA_FILE)

    if not os.path.exists(PHYSICAL_DATA_FILE):
        demo_physical = [
            {
                "所属公司": "科技有限公司",
                "一级部门": "技术部门",
                "固定资产编号": "PA001",
                "原固定资产编号": "OLD001",
                "固定资产类型": "电子设备",
                "固定资产名称": "联想ThinkPad笔记本电脑",
                "规格型号": "ThinkPad X1 Carbon",
                "存放部门": "信息技术部",
                "地点": "办公楼3楼IT部",
                "使用人": "张三",
                "保管人": "张三",
                "实盘数量": "1",
                "入账日期": "2023-01-15",
                "资产价值": 8500.0,
                "累计折旧额": 2125.0,
                "使用状态": "正常使用",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 1
            },
            {
                "所属公司": "科技有限公司",
                "一级部门": "行政部门",
                "固定资产编号": "PA002",
                "原固定资产编号": "OLD002",
                "固定资产类型": "办公家具",
                "固定资产名称": "实木办公桌",
                "规格型号": "1.6m*0.8m*0.75m",
                "存放部门": "行政管理部",
                "地点": "办公楼2楼行政部",
                "使用人": "李四",
                "保管人": "李四",
                "实盘数量": "1",
                "入账日期": "2023-02-01",
                "资产价值": 1800.0,
                "累计折旧额": 450.0,
                "使用状态": "正常使用",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 2
            },
            {
                "所属公司": "科技有限公司",
                "一级部门": "销售部门",
                "固定资产编号": "PA003",
                "原固定资产编号": "OLD003",
                "固定资产类型": "交通工具",
                "固定资产名称": "奥迪A4L轿车",
                "规格型号": "2.0T自动挡",
                "存放部门": "销售部",
                "地点": "地下停车场B区",
                "使用人": "王五",
                "保管人": "王五",
                "实盘数量": "1",
                "入账日期": "2022-06-01",
                "资产价值": 280000.0,
                "累计折旧额": 84000.0,
                "使用状态": "正常使用",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 3
            },
            {
                "所属公司": "科技有限公司",
                "一级部门": "行政部门",
                "固定资产编号": "PA004",
                "原固定资产编号": "OLD004",
                "固定资产类型": "电子设备",
                "固定资产名称": "激光打印机",
                "规格型号": "HP LaserJet Pro M404n",
                "存放部门": "行政管理部",
                "地点": "办公楼2楼打印室",
                "使用人": "赵六",
                "保管人": "赵六",
                "实盘数量": "1",
                "入账日期": "2023-03-10",
                "资产价值": 2200.0,
                "累计折旧额": 440.0,
                "使用状态": "正常使用",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 4
            }
        ]
        save_data(demo_physical, PHYSICAL_DATA_FILE)

    if not os.path.exists(MAPPING_DATA_FILE):
        demo_mapping = [
            {
                "实物台账编号": "PA001",
                "财务系统编号": "FS001",
                "资产编号": "AS001",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 1
            },
            {
                "实物台账编号": "PA002",
                "财务系统编号": "FS002",
                "资产编号": "AS002",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 2
            },
            {
                "实物台账编号": "PA003",
                "财务系统编号": "FS003",
                "资产编号": "AS003",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 3
            },
            {
                "实物台账编号": "PA004",
                "财务系统编号": "FS004",
                "资产编号": "AS004",
                "导入时间": "2024-01-01 10:00:00",
                "原始行号": 4
            }
        ]
        save_data(demo_mapping, MAPPING_DATA_FILE)


def safe_str_convert(value):
    """安全地将值转换为字符串"""
    if pd.isna(value) or value is None:
        return ""
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            return value.strftime("%Y-%m-%d")
        except:
            return str(value)
    return str(value).strip()


def safe_float_convert(value):
    """安全地将值转换为浮点数"""
    if pd.isna(value) or value is None:
        return 0.0
    if isinstance(value, str):
        cleaned = value.replace(',', '').replace('¥', '').replace('$', '').replace(' ', '')
        if cleaned == '' or cleaned == '-':
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (datetime, pd.Timestamp)):
        return 0.0
    return 0.0


def get_mapping_info(code, code_type, mapping_data, financial_data, physical_data):
    """获取映射信息"""
    if code_type == "financial":
        # 根据财务系统编号查找对应的实物资产
        mapping = next((m for m in mapping_data if m["财务系统编号"] == code), None)
        if mapping:
            physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), None)
            return physical_record, mapping["实物台账编号"]
    else:
        # 根据实物台账编号查找对应的财务资产
        mapping = next((m for m in mapping_data if m["实物台账编号"] == code), None)
        if mapping:
            financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), None)
            return financial_record, mapping["财务系统编号"]
    return None, None


def show_financial_summary(financial_data):
    """显示财务系统汇总信息"""
    if not financial_data:
        return

    df = pd.DataFrame(financial_data)

    # 计算汇总统计
    total_count = len(df)
    total_asset_value = df["资产价值"].sum()
    total_accumulated_depreciation = df["累积折旧"].sum()
    total_book_value = df["账面价值"].sum()

    # 显示汇总信息
    st.subheader("💰 财务系统汇总统计")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("资产数量", f"{total_count:,}项")
    with col2:
        st.metric("资产原值", f"¥{total_asset_value:,.2f}")
    with col3:
        st.metric("累积折旧", f"¥{total_accumulated_depreciation:,.2f}")
    with col4:
        st.metric("账面价值", f"¥{total_book_value:,.2f}")

    # 按分类统计
    if "资产分类" in df.columns and len(df) > 0:
        category_stats = df.groupby("资产分类").agg({
            "资产价值": "sum",
            "累积折旧": "sum",
            "账面价值": "sum"
        }).reset_index()

        with st.expander("📊 按分类统计"):
            st.dataframe(category_stats, use_container_width=True)


def show_physical_summary(physical_data):
    """显示实物台账汇总信息"""
    if not physical_data:
        return

    df = pd.DataFrame(physical_data)

    # 计算汇总统计
    total_count = len(df)
    total_asset_value = df["资产价值"].sum()
    total_accumulated_depreciation = df["累计折旧额"].sum()
    total_book_value = total_asset_value - total_accumulated_depreciation

    # 显示汇总信息
    st.subheader("📋 实物台账汇总统计")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("资产数量", f"{total_count:,}项")
    with col2:
        st.metric("资产原值", f"¥{total_asset_value:,.2f}")
    with col3:
        st.metric("累计折旧", f"¥{total_accumulated_depreciation:,.2f}")
    with col4:
        st.metric("净值合计", f"¥{total_book_value:,.2f}")

    # 按类型统计
    if "固定资产类型" in df.columns and len(df) > 0:
        type_stats = df.groupby("固定资产类型").agg({
            "资产价值": "sum",
            "累计折旧额": "sum"
        }).reset_index()
        type_stats["净值"] = type_stats["资产价值"] - type_stats["累计折旧额"]

        with st.expander("📊 按类型统计"):
            st.dataframe(type_stats, use_container_width=True)


def mapping_query_page():
    """映射关系查询页面"""
    st.header("🔍 资产映射关系查询")

    # 加载数据
    financial_data = load_data(FINANCIAL_DATA_FILE)
    physical_data = load_data(PHYSICAL_DATA_FILE)
    mapping_data = load_data(MAPPING_DATA_FILE)

    if not all([financial_data, physical_data, mapping_data]):
        st.warning("⚠️ 数据正在加载中...")
        return

    # 创建查询界面
    col1, col2 = st.columns(2)

    with col1:
        query_type = st.selectbox("查询方式", ["按财务系统编号查询", "按实物台账编号查询", "按资产名称查询"])

    with col2:
        if query_type == "按财务系统编号查询":
            financial_codes = [item["财务系统编号"] for item in financial_data if item["财务系统编号"]]
            query_value = st.selectbox("选择财务系统编号", [""] + financial_codes)
        elif query_type == "按实物台账编号查询":
            physical_codes = [item["固定资产编号"] for item in physical_data if item["固定资产编号"]]
            query_value = st.selectbox("选择实物台账编号", [""] + physical_codes)
        else:
            query_value = st.text_input("输入资产名称关键词")

    if query_value and st.button("🔍 查询", type="primary"):
        results = []

        if query_type == "按财务系统编号查询":
            # 查找对应的映射关系
            mapping_records = [m for m in mapping_data if m["财务系统编号"] == query_value]

            if mapping_records:
                for mapping in mapping_records:
                    # 获取财务记录
                    financial_record = next((f for f in financial_data if f["财务系统编号"] == query_value), None)
                    # 获取对应的实物记录
                    physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]),
                                           None)

                    if financial_record and physical_record:
                        results.append({
                            "financial": financial_record,
                            "physical": physical_record,
                            "mapping": mapping
                        })

        elif query_type == "按实物台账编号查询":
            # 查找对应的映射关系
            mapping_records = [m for m in mapping_data if m["实物台账编号"] == query_value]

            if mapping_records:
                for mapping in mapping_records:
                    # 获取实物记录
                    physical_record = next((p for p in physical_data if p["固定资产编号"] == query_value), None)
                    # 获取对应的财务记录
                    financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]),
                                            None)

                    if financial_record and physical_record:
                        results.append({
                            "financial": financial_record,
                            "physical": physical_record,
                            "mapping": mapping
                        })

        else:  # 按资产名称查询
            # 在财务系统中查找
            financial_matches = [f for f in financial_data if query_value.lower() in f["资产名称"].lower()]

            for financial_record in financial_matches:
                # 查找对应的映射
                mapping = next((m for m in mapping_data if m["财务系统编号"] == financial_record["财务系统编号"]), None)
                if mapping:
                    # 查找对应的实物资产
                    physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]),
                                           None)
                    if physical_record:
                        results.append({
                            "financial": financial_record,
                            "physical": physical_record,
                            "mapping": mapping
                        })

            # 在实物台账中查找
            physical_matches = [p for p in physical_data if query_value.lower() in p["固定资产名称"].lower()]

            for physical_record in physical_matches:
                # 查找对应的映射
                mapping = next((m for m in mapping_data if m["实物台账编号"] == physical_record["固定资产编号"]), None)
                if mapping:
                    # 查找对应的财务资产
                    financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]),
                                            None)
                    if financial_record:
                        # 避免重复添加
                        if not any(r["financial"]["财务系统编号"] == financial_record["财务系统编号"] for r in results):
                            results.append({
                                "financial": financial_record,
                                "physical": physical_record,
                                "mapping": mapping
                            })

        # 显示查询结果
        if results:
            st.success(f"✅ 找到 {len(results)} 条匹配记录")

            for idx, result in enumerate(results):
                with st.expander(f"📌 记录 {idx + 1}: {result['financial']['资产名称']}", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### 📊 财务系统信息")
                        financial = result["financial"]
                        st.write(f"**编号**：{financial['财务系统编号']}")
                        st.write(f"**名称**：{financial['资产名称']}")
                        st.write(f"**分类**：{financial['资产分类']}")
                        st.write(f"**规格**：{financial['资产规格']}")
                        st.write(f"**价值**：¥{financial['资产价值']:,.2f}")
                        st.write(f"**累积折旧**：¥{financial['累积折旧']:,.2f}")
                        st.write(f"**账面价值**：¥{financial['账面价值']:,.2f}")
                        st.write(f"**部门**：{financial['部门名称']}")
                        st.write(f"**保管人**：{financial['保管人']}")

                    with col2:
                        st.markdown("### 📋 实物台账信息")
                        physical = result["physical"]
                        st.write(f"**编号**：{physical['固定资产编号']}")
                        st.write(f"**名称**：{physical['固定资产名称']}")
                        st.write(f"**类型**：{physical['固定资产类型']}")
                        st.write(f"**规格**：{physical['规格型号']}")
                        st.write(f"**价值**：¥{physical['资产价值']:,.2f}")
                        st.write(f"**累计折旧**：¥{physical['累计折旧额']:,.2f}")
                        st.write(f"**净值**：¥{physical['资产价值'] - physical['累计折旧额']:,.2f}")
                        st.write(f"**部门**：{physical['存放部门']}")
                        st.write(f"**保管人**：{physical['保管人']}")

                    # 差异分析
                    st.markdown("### 📊 差异分析")
                    value_diff = financial['资产价值'] - physical['资产价值']
                    depreciation_diff = financial['累积折旧'] - physical['累计折旧额']

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if abs(value_diff) > 0.01:
                            st.error(f"价值差异：¥{value_diff:,.2f}")
                        else:
                            st.success("价值一致 ✓")

                    with col2:
                        if abs(depreciation_diff) > 0.01:
                            st.error(f"折旧差异：¥{depreciation_diff:,.2f}")
                        else:
                            st.success("折旧一致 ✓")

                    with col3:
                        if financial['部门名称'] != physical['存放部门']:
                            st.warning("部门不一致")
                        else:
                            st.success("部门一致 ✓")
        else:
            st.warning("❌ 未找到匹配的记录")


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
                    # 这里可以添加你原有的导入逻辑

                    st.success("✅ 数据导入功能需要完整的导入逻辑")


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
                    st.success("✅ 数据导入功能需要完整的导入逻辑")


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
                    st.success("✅ 数据导入功能需要完整的导入逻辑")


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
