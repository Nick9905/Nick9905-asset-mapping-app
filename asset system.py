import warnings  
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
import numpy as np
import re
import plotly
# 添加GitHub存储支持 - 修复GITHUB_AVAILABLE变量定义
GITHUB_AVAILABLE = False
try:
    from github import Github
    import base64
    import requests
    GITHUB_AVAILABLE = True
    print("✅ GitHub库导入成功")
except ImportError as e:
    print(f"⚠️ GitHub库导入失败: {e}")
    GITHUB_AVAILABLE = False
except Exception as e:
    print(f"⚠️ GitHub库导入异常: {e}")
    GITHUB_AVAILABLE = False

# 显示GitHub可用状态（调试用）
if not GITHUB_AVAILABLE:
    st.sidebar.warning("⚠️ GitHub功能不可用，使用本地存储")

# GitHub数据存储函数
def get_github_config():
    """获取GitHub配置"""
    try:
        # 检查Streamlit secrets
        if hasattr(st, 'secrets') and "github" in st.secrets:
            config = {
                "token": st.secrets["github"]["token"],
                "repo": st.secrets["github"]["repo"]
            }
            # 验证配置完整性
            if config["token"] and config["repo"]:
                return config
        return None
    except Exception as e:
        print(f"GitHub配置读取失败: {str(e)}")
        return None

def save_data_to_github(data, filename):
    """保存数据到GitHub"""
    if not GITHUB_AVAILABLE:
        return False
        
    try:
        config = get_github_config()
        if not config:
            st.warning("⚠️ GitHub配置未找到")
            return False
            
        g = Github(config["token"])
        repo = g.get_repo(config["repo"])
        
        # 清理数据
        cleaned_data = clean_data_for_json(data)
        content = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        
        # 文件路径
        file_path = f"data/{filename}"
        
        try:
            # 尝试获取现有文件
            file = repo.get_contents(file_path)
            # 更新文件
            repo.update_file(
                file_path,
                f"Update {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                content,
                file.sha
            )
            st.success(f"✅ 数据已保存到GitHub: {filename}")
        except:
            # 文件不存在，创建新文件
            repo.create_file(
                file_path,
                f"Create {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                content
            )
            st.success(f"✅ 数据已创建到GitHub: {filename}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ GitHub保存失败: {str(e)}")
        return False

def load_data_from_github(filename):
    """增强版GitHub数据加载"""
    if not GITHUB_AVAILABLE:
        return []
        
    try:
        config = get_github_config()
        if not config:
            return []
            
        g = Github(config["token"])
        repo = g.get_repo(config["repo"])
        
        file_path = f"data/{filename}"
        
        try:
            file = repo.get_contents(file_path)
            raw_content = base64.b64decode(file.content)
            
            # 检查文件是否为空
            if len(raw_content) == 0:
                st.sidebar.warning(f"⚠️ {filename} 文件为空")
                return []
            
            # 尝试不同编码解码
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']:
                try:
                    content = raw_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                st.sidebar.error(f"❌ {filename} 编码解析失败")
                return []
            
            # 清理内容（移除BOM和空白字符）
            content = content.strip()
            if content.startswith('\ufeff'):  # 移除BOM
                content = content[1:]
            
            # 检查是否为空内容
            if not content:
                st.sidebar.warning(f"⚠️ {filename} 内容为空")
                return []
            
            # 尝试解析JSON
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    st.sidebar.success(f"✅ {filename} 加载成功: {len(data)} 条记录")
                    return data
                else:
                    st.sidebar.error(f"❌ {filename} 不是数组格式")
                    return []
            except json.JSONDecodeError as json_error:
                st.sidebar.error(f"❌ {filename} JSON解析失败: {str(json_error)}")
                st.sidebar.write(f"内容预览: {repr(content[:200])}")
                return []
                
        except Exception as file_error:
            st.sidebar.error(f"❌ {filename} 文件访问失败: {str(file_error)}")
            return []
            
    except Exception as e:
        st.sidebar.error(f"❌ GitHub连接失败: {str(e)}")
        return []
def debug_github_file_content(filename):
    """调试GitHub文件内容"""
    try:
        config = get_github_config()
        if not config:
            return None
            
        g = Github(config["token"])
        repo = g.get_repo(config["repo"])
        
        file_path = f"data/{filename}"
        file = repo.get_contents(file_path)
        
        # 获取原始内容
        raw_content = base64.b64decode(file.content)
        
        st.sidebar.write(f"📄 {filename} 文件信息:")
        st.sidebar.write(f"- 文件大小: {len(raw_content)} 字节")
        st.sidebar.write(f"- 编码检测: {raw_content[:100]}")
        
        # 尝试不同编码
        try:
            content_utf8 = raw_content.decode('utf-8')
            st.sidebar.write(f"- UTF-8解码长度: {len(content_utf8)}")
            st.sidebar.write(f"- 前100字符: {repr(content_utf8[:100])}")
            return content_utf8
        except UnicodeDecodeError:
            st.sidebar.error("❌ UTF-8解码失败")
            try:
                content_gbk = raw_content.decode('gbk')
                st.sidebar.write(f"- GBK解码成功，长度: {len(content_gbk)}")
                return content_gbk
            except:
                st.sidebar.error("❌ 多种编码尝试失败")
                return None
                
    except Exception as e:
        st.sidebar.error(f"❌ 文件内容检查失败: {str(e)}")
        return None

def create_sample_data_files():
    """创建示例数据文件"""
    st.sidebar.markdown("### 🔧 数据文件修复")
    
    if st.sidebar.button("🔍 检查文件内容", key="debug_files"):
        st.sidebar.write("**财务数据文件检查:**")
        debug_github_file_content("financial_data.json")
        
        st.sidebar.write("**实物数据文件检查:**")
        debug_github_file_content("physical_data.json")
    
    if st.sidebar.button("📝 创建示例数据", key="create_sample"):
        # 示例财务数据
        sample_financial = [
            {
                "资产编号": "FA001",
                "资产名称": "办公桌",
                "资产类别": "办公设备",
                "购置日期": "2023-01-15",
                "原值": 1200.00,
                "累计折旧": 100.00,
                "净值": 1100.00,
                "使用部门": "行政部",
                "资产状态": "在用"
            },
            {
                "资产编号": "FA002", 
                "资产名称": "笔记本电脑",
                "资产类别": "电子设备",
                "购置日期": "2023-02-20",
                "原值": 5500.00,
                "累计折旧": 458.33,
                "净值": 5041.67,
                "使用部门": "技术部",
                "资产状态": "在用"
            }
        ]
        
        # 示例实物数据
        sample_physical = [
            {
                "实物编号": "PA001",
                "实物名称": "办公桌",
                "规格型号": "1.2m*0.6m",
                "存放位置": "办公室101",
                "责任人": "张三",
                "盘点日期": "2023-12-01",
                "实物状态": "正常",
                "备注": "状态良好"
            },
            {
                "实物编号": "PA002",
                "实物名称": "笔记本电脑", 
                "规格型号": "ThinkPad E14",
                "存放位置": "技术部",
                "责任人": "李四",
                "盘点日期": "2023-12-01", 
                "实物状态": "正常",
                "备注": "运行正常"
            }
        ]
        
        # 提供下载链接
        financial_json = json.dumps(sample_financial, ensure_ascii=False, indent=2)
        physical_json = json.dumps(sample_physical, ensure_ascii=False, indent=2)
        
        st.sidebar.download_button(
            "📥 下载财务数据模板",
            financial_json,
            "financial_data.json",
            "application/json",
            key="download_financial"
        )
        
        st.sidebar.download_button(
            "📥 下载实物数据模板", 
            physical_json,
            "physical_data.json",
            "application/json",
            key="download_physical"
        )
        
        st.sidebar.success("✅ 示例数据已生成，请下载并上传到GitHub")
# ========== 配置和常量 ==========

# 数据文件路径
FINANCIAL_DATA_FILE = "financial_data.json"
PHYSICAL_DATA_FILE = "physical_data.json"
MAPPING_DATA_FILE = "mapping_data.json"

# 页面配置
st.set_page_config(
    page_title="资产映射关系查询",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== 数据处理函数 ==========
def clean_data_for_json(data):
    """清理数据以便JSON序列化"""
    import numpy as np

    def clean_value(value):
        """清理单个值"""
        # 处理NaN值
        if pd.isna(value):
            return None
        # 处理numpy类型
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            if np.isnan(value):
                return None
            return float(value)
        elif isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        # 处理字符串
        elif isinstance(value, str):
            return value.strip() if value.strip() else ""
        # 其他类型转换为字符串
        elif value is None:
            return None
        else:
            try:
                return str(value)
            except:
                return ""

    def clean_record(record):
        """清理单条记录"""
        if isinstance(record, dict):
            cleaned = {}
            for key, value in record.items():
                cleaned_key = str(key) if key is not None else ""
                cleaned_value = clean_value(value)
                if cleaned_key:  # 只保留非空键
                    cleaned[cleaned_key] = cleaned_value
            return cleaned
        else:
            return clean_value(record)

    # 清理整个数据列表
    if isinstance(data, list):
        return [clean_record(record) for record in data]
    else:
        return clean_record(data)

    """保存数据到JSON文件"""
    try:
        # ✅ 添加：数据验证
        if not isinstance(data, list):
            st.error(f"❌ 数据格式错误：期望列表格式，实际为 {type(data)}")
            return False

        # ✅ 添加：清理数据中的NaN值
        cleaned_data = clean_data_for_json(data)

        # ✅ 添加：创建备份
        if os.path.exists(filename):
            backup_name = f"{filename}.backup"
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(backup_name, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
            except:
                pass  # 备份失败不影响主流程

        # 保存清理后的数据
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ 保存数据失败 ({filename}): {str(e)}")
        return False
def save_data(data, filename):
    """保存数据 - 优先GitHub存储"""
    # 先尝试GitHub存储
    if save_data_to_github(data, filename):
        # GitHub保存成功，同时保存本地备份
        try:
            cleaned_data = clean_data_for_json(data)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        except:
            pass  # 本地备份失败不影响主流程
        return True
    
    # GitHub失败，尝试本地存储
    try:
        cleaned_data = clean_data_for_json(data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        st.warning("⚠️ 数据已保存到本地（GitHub不可用）")
        return True
    except Exception as e:
        st.error(f"❌ 保存失败: {str(e)}")
        return False

def load_data(filename):
    """加载数据 - 优先GitHub存储"""
    # 先尝试从GitHub加载
    github_data = load_data_from_github(filename)
    if github_data:
        return github_data
    
    # GitHub失败，尝试本地加载
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.info(f"📁 从本地加载数据: {filename} ({len(data)} 条记录)")
                return data
        return []
    except Exception as e:
        st.error(f"❌ 加载数据失败: {str(e)}")
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
    """
    创建映射索引
    返回两个字典：
    - financial_to_physical_mapping: '资产编号+序号' -> ['固定资产编码'列表]
    - physical_to_financial_mapping: '固定资产编码' -> ['资产编号+序号'列表]
    """
    financial_to_physical_mapping = {}  # 财务系统主键到实物台账主键的映射
    physical_to_financial_mapping = {}  # 实物台账主键到财务系统主键的映射

    for mapping in mapping_data:
        financial_key = str(mapping.get("资产编号+序号", "")).strip()  # 财务系统主键
        physical_key = str(mapping.get("固定资产编码", "")).strip()    # 实物台账主键

        if (pd.notna(financial_key) and pd.notna(physical_key) and
                str(financial_key).strip() and str(physical_key).strip()):
            # 财务系统到实物台账的映射
            if financial_key not in financial_to_physical_mapping:
                financial_to_physical_mapping[financial_key] = []
            if physical_key not in financial_to_physical_mapping[financial_key]:
                financial_to_physical_mapping[financial_key].append(physical_key)

            # 实物台账到财务系统的映射
            if physical_key not in physical_to_financial_mapping:
                physical_to_financial_mapping[physical_key] = []
            if financial_key not in physical_to_financial_mapping[physical_key]:
                physical_to_financial_mapping[physical_key].append(financial_key)

    return financial_to_physical_mapping, physical_to_financial_mapping


def safe_get_value(record, key, default=0):
    """安全获取数值，处理可能的类型转换问题 - 通用增强版"""
    try:
        # 根据实际Excel字段，尝试多个可能的字段名
        value = None

        # 🔧 新增：资产名称字段处理
        if key == "资产名称":
            # 财务系统资产名称字段
            for field in ["资产名称", "固定资产名称", "资产名", "名称", "设备名称"]:
                if field in record and record[field] is not None:
                    return str(record[field]).strip()
            return str(default)

        elif key == "固定资产名称":
            # 实物系统资产名称字段
            for field in ["固定资产名称", "资产名称", "设备名称", "名称", "资产名"]:
                if field in record and record[field] is not None:
                    return str(record[field]).strip()
            return str(default)

        # 特定字段的映射处理
        elif key == "资产价值":
            # 财务系统可能的字段名
            for field in ["资产价值", "账面价值", "资产净额", "固定资产原值", "原价", "原值"]:
                if field in record and record[field] is not None:
                    value = record[field]
                    break
        elif key == "固定资产原值":
            # 实物台账可能的字段名
            for field in ["固定资产原值", "资产价值", "原值", "资产原值", "原价", "购置价值"]:
                if field in record and record[field] is not None:
                    value = record[field]
                    break
        elif key == "累计折旧":
            # 累计折旧字段的可能名称（财务和实物通用）
            for field in ["累计折旧", "累计摊销", "折旧累计", "已计提折旧", "折旧金额", "累计折旧额", "折旧合计"]:
                if field in record and record[field] is not None:
                    value = record[field]
                    break
            # 如果还没找到，尝试模糊匹配
            if value is None:
                for field_name, field_value in record.items():
                    if field_value is not None and ("折旧" in str(field_name) or "摊销" in str(field_name)):
                        # 排除明显不是累计折旧的字段
                        if not any(
                                exclude in str(field_name) for exclude in ["率", "年限", "方法", "政策", "说明"]):
                            value = field_value
                            break
        elif key == "净额" or key == "净值":
            # 净值字段的可能名称（主要用于财务系统）
            for field in ["净额", "净值", "账面净值", "资产净值", "固定资产净值", "账面价值", "净资产"]:
                if field in record and record[field] is not None:
                    value = record[field]
                    break
        else:
            # 直接获取字段值
            value = record.get(key, default)

        # 调用通用数值转换函数
        return convert_to_number(value, default)

    except Exception:
        # 如果出现任何异常，返回默认值
        return default


def convert_to_number(value, default=0):
    """通用数值转换函数，处理各种可能的数值格式"""
    try:
        # 如果没有找到值，返回默认值
        if value is None or value == "":
            return default

        # 处理pandas的NaN值
        if pd.isna(value):
            return default

        # 如果已经是数字类型
        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else default

        # 如果是字符串，进行清理和转换
        if isinstance(value, str):
            # 移除常见的非数字字符
            cleaned_value = value.strip()

            # 处理常见的文本情况
            if cleaned_value.lower() in ['', '-', 'nan', 'null', 'none', '无', '空', 'n/a', '#n/a', '#value!',
                                         '#div/0!']:
                return default

            # 移除货币符号和格式字符
            cleaned_value = cleaned_value.replace(',', '').replace('¥', '').replace('￥', '').replace('$', '').replace(
                '€', '')
            cleaned_value = cleaned_value.replace('，', '').replace(' ', '').replace('\t', '').replace('\n', '')
            cleaned_value = cleaned_value.replace('元', '').replace('万元', '0000').replace('千元', '000')

            # 处理括号表示负数的情况 (1,000.00) -> -1000.00
            if cleaned_value.startswith('(') and cleaned_value.endswith(')'):
                cleaned_value = '-' + cleaned_value[1:-1]

            # 处理百分号
            if cleaned_value.endswith('%'):
                try:
                    return float(cleaned_value[:-1]) / 100
                except ValueError:
                    pass

            # 尝试转换为浮点数
            try:
                return float(cleaned_value)
            except ValueError:
                # 如果包含其他文字，尝试提取数字部分
                import re
                # 匹配数字（包括小数点和负号）
                number_match = re.search(r'-?\d+(?:\.\d+)?', cleaned_value)
                if number_match:
                    return float(number_match.group())
                else:
                    return default

        # 其他类型尝试直接转换
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    except Exception:
        # 如果出现任何异常，返回默认值
        return default


def is_numeric_field(field_name, sample_values):
    """判断字段是否为数值类型字段"""
    # 明确的数值字段关键词
    numeric_keywords = [
        '价值', '金额', '原值', '净值', '净额', '折旧', '摊销',
        '成本', '费用', '收入', '利润', '资产', '负债', '权益',
        '数量', '单价', '总价', '合计', '小计', '余额', '结余',
        '面积', '长度', '重量', '容量', '功率', '电压', '电流',
        '年限', '月数', '天数', '比率', '率', '百分比', '%'
    ]

    # 检查字段名是否包含数值关键词
    field_name_lower = field_name.lower()
    for keyword in numeric_keywords:
        if keyword in field_name_lower:
            return True

    # 检查样本值是否主要为数值类型
    if not sample_values:
        return False

    numeric_count = 0
    total_count = len(sample_values)

    for value in sample_values[:min(10, total_count)]:  # 检查前10个样本
        if value is None or value == "":
            continue

        # 尝试转换为数值
        converted = convert_to_number(value, None)
        if converted is not None:
            numeric_count += 1

    # 如果超过60%的样本可以转换为数值，则认为是数值字段
    return numeric_count / max(1, total_count) > 0.6


def auto_detect_and_convert_numeric_fields(data):
    """自动检测并转换数值字段"""
    if not data:
        return data

    # 获取所有字段名
    all_fields = set()
    for record in data[:100]:  # 检查前100条记录以确定字段
        all_fields.update(record.keys())

    # 检测数值字段
    numeric_fields = {}
    for field in all_fields:
        # 收集该字段的样本值
        sample_values = []
        for record in data[:20]:  # 取前20条记录作为样本
            if field in record:
                sample_values.append(record[field])

        if is_numeric_field(field, sample_values):
            numeric_fields[field] = True

    # 转换数值字段
    converted_data = []
    for record in data:
        new_record = {}
        for key, value in record.items():
            if key in numeric_fields:
                # 转换为数值
                new_record[key] = convert_to_number(value, 0)
            else:
                # 保持原值
                new_record[key] = value
        converted_data.append(new_record)

    return converted_data, numeric_fields


# ========== 页面函数 ==========

def data_import_page():
    """数据导入页面 - 增加删除数据功能"""
    st.header("📥 数据导入管理")

    st.info("💡 **映射规则说明**：财务系统的'资产编号+序号' ↔ 实物台账的'固定资产编码'（多对多关系）")

    # 创建四个标签页
    tab1, tab2, tab3, tab4 = st.tabs(["财务系统数据", "实物台账数据", "映射关系数据", "🗑️ 数据删除"])

    with tab1:
        st.subheader("💰 财务系统明细账数据")
        st.markdown("**必需字段**：`资产编号+序号`、`资产名称`、`资产价值`等")

        # 显示当前数据状态
        current_financial = load_data(FINANCIAL_DATA_FILE)

        # ✅ 添加：数据验证和修复
        if current_financial is None:
            current_financial = []
            st.warning("⚠️ 财务数据文件可能损坏，已重置为空")
        elif not isinstance(current_financial, list):
            st.error("❌ 财务数据格式错误，应为列表格式")
            current_financial = []

        if current_financial:
            st.success(f"✅ 当前已有 {len(current_financial)} 条财务资产记录")

            # 显示完整当前数据
            with st.expander("📊 查看当前所有财务数据", expanded=False):
                df_current = pd.DataFrame(current_financial)

                # 添加搜索功能
                search_term = st.text_input("🔍 搜索财务数据（按资产编号或名称）", key="search_financial_current")
                if search_term:
                    mask = df_current.astype(str).apply(
                        lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                    df_filtered = df_current[mask]
                    st.write(f"搜索结果：{len(df_filtered)} 条记录")
                    st.dataframe(df_filtered, use_container_width=True, height=400)
                else:
                    st.dataframe(df_current, use_container_width=True, height=400)

                # 数据统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总记录数", len(df_current))
                with col2:
                    # ✅ 修复：只从"资产价值"字段计算总价值
                    if "资产价值" in df_current.columns:
                        try:
                            total_value = 0.0
                            valid_count = 0
                            error_count = 0

                            # 逐行处理"资产价值"字段
                            for _, row in df_current.iterrows():
                                asset_value = row["资产价值"]
                                try:
                                    # 使用安全转换函数
                                    converted_value = safe_convert_to_float(asset_value)
                                    if converted_value >= 0:  # 接受0和正数
                                        total_value += converted_value
                                        valid_count += 1
                                    else:
                                        error_count += 1
                                except:
                                    error_count += 1

                            # 显示计算结果
                            st.metric("总资产价值", f"¥{total_value:,.2f}")

                            # 显示处理统计
                            if valid_count > 0:
                                success_rate = (valid_count / len(df_current)) * 100
                                st.success(f"✅ 成功处理 {valid_count}/{len(df_current)} 条记录 ({success_rate:.1f}%)")

                                if error_count > 0:
                                    st.warning(f"⚠️ {error_count} 条记录的资产价值字段无法转换为数字")
                            else:
                                st.error("❌ 所有资产价值字段都无法转换为有效数字")

                                # 显示调试信息
                                with st.expander("🔧 资产价值字段问题分析"):
                                    st.write("**前5条记录的资产价值字段内容：**")
                                    sample_data = df_current["资产价值"].head(5).tolist()
                                    for i, value in enumerate(sample_data, 1):
                                        converted = safe_convert_to_float(value)
                                        st.write(f"{i}. 原值: `{value}` ({type(value).__name__}) → 转换后: {converted}")

                                    st.markdown("**可能的问题：**")
                                    st.markdown("- 字段包含文本而非数字")
                                    st.markdown("- 数字格式不标准（如包含特殊字符）")
                                    st.markdown("- 字段为空值或NaN")
                                    st.markdown("- 数字使用了特殊的千位分隔符")

                        except Exception as e:
                            st.metric("总资产价值", "计算错误")
                            st.error(f"❌ 计算资产价值时出错: {str(e)}")

                            with st.expander("🚨 错误详情"):
                                st.code(f"错误类型: {type(e).__name__}\n错误信息: {str(e)}")
                                if len(df_current) > 0:
                                    st.write("数据样本：", df_current["资产价值"].head(3).tolist())
                    else:
                        st.metric("总资产价值", "字段缺失")
                        st.error("❌ 数据中没有资产价值字段")

                        with st.expander("📋 当前数据字段列表"):
                            st.write("**现有字段：**")
                            for i, col in enumerate(df_current.columns, 1):
                                st.write(f"{i}. `{col}`")

                            st.info("💡 请确保Excel文件中有名为资产价值的列")

                with col3:
                    if "部门名称" in df_current.columns:
                        dept_count = df_current["部门名称"].nunique()
                        st.metric("涉及部门数", dept_count)

            # 🗑️ 快速删除功能
            st.markdown("---")
            with st.expander("🗑️ 财务数据快速删除", expanded=False):
                st.warning("⚠️ **注意**：删除操作不可恢复，请谨慎操作！")

                col1, col2, col3 = st.columns(3)
                with col1:
                    # 按条件删除
                    st.markdown("**🎯 条件删除**")
                    delete_condition = st.selectbox(
                        "选择删除条件",
                        ["选择条件...", "资产价值为0", "资产名称为空", "部门名称为空", "自定义条件"],
                        key="financial_delete_condition"
                    )

                    if delete_condition == "自定义条件":
                        custom_field = st.selectbox("选择字段", df_current.columns.tolist(),
                                                    key="financial_custom_field")
                        custom_value = st.text_input("输入要删除的值", key="financial_custom_value")

                        if st.button("🗑️ 执行条件删除", key="financial_condition_delete"):
                            if custom_value:
                                original_count = len(current_financial)
                                filtered_data = [
                                    record for record in current_financial
                                    if str(record.get(custom_field, "")) != custom_value
                                ]
                                save_data(filtered_data, FINANCIAL_DATA_FILE)
                                deleted_count = original_count - len(filtered_data)
                                st.success(f"✅ 已删除 {deleted_count} 条记录")
                                st.rerun()

                    elif delete_condition != "选择条件..." and st.button("🗑️ 执行条件删除",
                                                                         key="financial_preset_delete"):
                        original_count = len(current_financial)
                        if delete_condition == "资产价值为0":
                            filtered_data = [
                                record for record in current_financial
                                if safe_convert_to_float(record.get("资产价值", 0)) != 0
                            ]
                        elif delete_condition == "资产名称为空":
                            filtered_data = [
                                record for record in current_financial
                                if str(record.get("资产名称", "")).strip() != ""
                            ]
                        elif delete_condition == "部门名称为空":
                            filtered_data = [
                                record for record in current_financial
                                if str(record.get("部门名称", "")).strip() != ""
                            ]

                        save_data(filtered_data, FINANCIAL_DATA_FILE)
                        deleted_count = original_count - len(filtered_data)
                        st.success(f"✅ 已删除 {deleted_count} 条记录")
                        st.rerun()

                with col2:
                    # 按编号删除
                    st.markdown("**🔢 按编号删除**")
                    delete_codes = st.text_area(
                        "输入要删除的资产编号（每行一个）",
                        height=100,
                        key="financial_delete_codes",
                        help="每行输入一个资产编号+序号"
                    )

                    if st.button("🗑️ 删除指定编号", key="financial_code_delete"):
                        if delete_codes.strip():
                            codes_to_delete = [code.strip() for code in delete_codes.split('\n') if code.strip()]
                            original_count = len(current_financial)
                            filtered_data = [
                                record for record in current_financial
                                if record.get("资产编号+序号", "") not in codes_to_delete
                            ]
                            save_data(filtered_data, FINANCIAL_DATA_FILE)
                            deleted_count = original_count - len(filtered_data)
                            st.success(f"✅ 已删除 {deleted_count} 条记录")
                            st.rerun()

                with col3:
                    # 清空所有数据
                    st.markdown("**🚨 危险操作**")
                    st.error("⚠️ 以下操作将清空所有财务数据")

                    # 双重确认机制
                    confirm_clear = st.checkbox("我确认要清空所有财务数据", key="financial_confirm_clear")

                    if confirm_clear:
                        final_confirm = st.text_input(
                            "请输入 'DELETE ALL' 确认清空",
                            key="financial_final_confirm"
                        )

                        if final_confirm == "DELETE ALL" and st.button("🚨 清空所有数据", key="financial_clear_all"):
                            save_data([], FINANCIAL_DATA_FILE)
                            st.success("✅ 已清空所有财务数据")
                            st.rerun()

        else:
            st.warning("⚠️ 暂无财务系统数据")

        # 文件上传部分保持不变
        financial_file = st.file_uploader(
            "上传财务系统明细账Excel文件",
            type=['xlsx', 'xls'],
            key="financial_upload",
            help="Excel文件应包含'资产编号+序号'列作为主键"
        )

        if financial_file is not None:
            try:
                financial_df = pd.read_excel(financial_file)
                st.success(f"✅ 成功读取财务数据: {len(financial_df)} 行 x {len(financial_df.columns)} 列")

                # 检查必需字段
                required_columns = ["资产编号+序号"]
                missing_columns = []

                for col in required_columns:
                    if col not in financial_df.columns:
                        similar_cols = [c for c in financial_df.columns if "资产编号" in str(c) and "序号" in str(c)]
                        if not similar_cols:
                            similar_cols = [c for c in financial_df.columns if "编号" in str(c)]

                        if similar_cols:
                            st.warning(f"⚠️ 未找到标准列名'{col}'，发现相似列名：{similar_cols}")
                            st.info("请确保Excel文件中有'资产编号+序号'列，或手动重命名相应列")
                        else:
                            missing_columns.append(col)

                if missing_columns:
                    st.error(f"❌ 缺少必需字段：{missing_columns}")
                    st.stop()

                # 显示完整上传数据预览
                st.subheader("📊 上传数据完整预览")

                search_upload = st.text_input("🔍 搜索上传数据", key="search_financial_upload")
                if search_upload:
                    mask = financial_df.astype(str).apply(
                        lambda x: x.str.contains(search_upload, case=False, na=False)).any(axis=1)
                    df_filtered = financial_df[mask]
                    st.write(f"搜索结果：{len(df_filtered)} 条记录")
                    st.dataframe(df_filtered, use_container_width=True, height=500)
                else:
                    st.dataframe(financial_df, use_container_width=True, height=500)

                # 数据质量检查
                st.subheader("🔍 数据质量检查")

                col1, col2, col3 = st.columns(3)
                with col1:
                    asset_codes = financial_df["资产编号+序号"].dropna()
                    duplicate_codes = asset_codes[asset_codes.duplicated()].unique()

                    if len(duplicate_codes) > 0:
                        st.error(f"❌ 重复编号: {len(duplicate_codes)} 个")
                        with st.expander("查看重复记录"):
                            duplicate_records = financial_df[financial_df["资产编号+序号"].isin(duplicate_codes)]
                            st.dataframe(duplicate_records, use_container_width=True)
                    else:
                        st.success("✅ 编号唯一性通过")

                with col2:
                    null_counts = financial_df.isnull().sum()
                    total_nulls = null_counts.sum()
                    if total_nulls > 0:
                        st.warning(f"⚠️ 空值: {total_nulls} 个")
                        with st.expander("查看空值统计"):
                            st.dataframe(null_counts[null_counts > 0].to_frame("空值数量"), use_container_width=True)
                    else:
                        st.success("✅ 无空值")

                with col3:
                    if "资产价值" in financial_df.columns:
                        total_value = financial_df["资产价值"].sum()
                        st.metric("总价值", f"{total_value:,.2f}")

                # 导入选项
                st.markdown("---")
                st.subheader("📥 导入选项")

                import_mode = st.radio(
                    "选择导入模式",
                    ["覆盖导入（清空原数据）", "追加导入（保留原数据）", "更新导入（按编号更新）"],
                    key="financial_import_mode"
                )

                # 导入确认
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 确认导入财务数据", type="primary", use_container_width=True):
                        # 数据标准化处理
                        processed_data = []
                        for _, row in financial_df.iterrows():
                            record = {}
                            # 确保主键字段正确
                            record["资产编号+序号"] = str(row.get("资产编号+序号", "")).strip()
                            record["序号"] = str(row.get("序号", "")).strip()
                            record["资产编号"] = str(row.get("资产编号", "")).strip()
                            record["资产名称"] = str(row.get("资产名称", "")).strip()

                            # ✅ 修复：使用安全的数值转换
                            record["资产价值"] = safe_convert_to_float(row.get("资产价值", 0))
                            record["账面价值"] = safe_convert_to_float(row.get("账面价值", 0))
                            record["资产净额"] = safe_convert_to_float(row.get("资产净额", 0))

                            record["部门名称"] = str(row.get("部门名称", "")).strip()
                            record["保管人名称"] = str(row.get("保管人名称", "")).strip()
                            record["资产分类"] = str(row.get("资产分类", "")).strip()

                            # ✅ 修复：安全处理所有其他字段
                            for col in financial_df.columns:
                                if col not in record:
                                    value = row.get(col)
                                    # 清理NaN值和特殊类型
                                    if pd.isna(value):
                                        record[col] = ""
                                    elif isinstance(value, (int, float)):
                                        if pd.isna(value):
                                            record[col] = 0
                                        else:
                                            record[col] = float(value) if not pd.isna(value) else 0
                                    else:
                                        record[col] = str(value).strip() if value is not None else ""

                            if record["资产编号+序号"]:
                                processed_data.append(record)

                        # 根据导入模式处理数据
                        if import_mode == "覆盖导入（清空原数据）":
                            save_data(processed_data, FINANCIAL_DATA_FILE)
                            st.success(f"✅ 覆盖导入 {len(processed_data)} 条财务资产记录")

                        elif import_mode == "追加导入（保留原数据）":
                            existing_data = load_data(FINANCIAL_DATA_FILE)
                            combined_data = existing_data + processed_data
                            save_data(combined_data, FINANCIAL_DATA_FILE)
                            st.success(f"✅ 追加导入 {len(processed_data)} 条记录，总计 {len(combined_data)} 条")

                        elif import_mode == "更新导入（按编号更新）":
                            existing_data = load_data(FINANCIAL_DATA_FILE)
                            existing_dict = {record.get("资产编号+序号"): record for record in existing_data}

                            # 更新或添加新记录
                            for record in processed_data:
                                existing_dict[record[("资产编号+序号")]] = record

                            updated_data = list(existing_dict.values())
                            save_data(updated_data, FINANCIAL_DATA_FILE)
                            st.success(f"✅ 更新导入完成，总计 {len(updated_data)} 条记录")

                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("📥 导出当前数据", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            financial_df.to_excel(writer, index=False, sheet_name='财务数据')

                        st.download_button(
                            label="⬇️ 下载Excel文件",
                            data=output.getvalue(),
                            file_name=f"财务数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                with col3:
                    if st.button("🔄 重新上传", use_container_width=True):
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件读取失败：{str(e)}")

    with tab2:
        st.subheader("📦 实物台账数据")
        st.markdown("**必需字段**：`固定资产编码`、`固定资产名称`、`固定资产原值`等")

        # 显示当前数据状态
        current_physical = load_data(PHYSICAL_DATA_FILE)
        if current_physical:
            st.success(f"✅ 当前已有 {len(current_physical)} 条实物资产记录")

            # 显示完整当前数据
            with st.expander("📊 查看当前所有实物数据", expanded=False):
                df_current = pd.DataFrame(current_physical)

                search_term = st.text_input("🔍 搜索实物数据（按编码或名称）", key="search_physical_current")
                if search_term:
                    mask = df_current.astype(str).apply(
                        lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                    df_filtered = df_current[mask]
                    st.write(f"搜索结果：{len(df_filtered)} 条记录")
                    st.dataframe(df_filtered, use_container_width=True, height=400)
                else:
                    st.dataframe(df_current, use_container_width=True, height=400)

                # 数据统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总记录数", len(df_current))

                with col2:
                    # ✅ 修复：使用固定资产原值字段计算总价值，支持核算筛选
                    if "固定资产原值" in df_current.columns:
                        try:
                            # 🆕 新增：检查是否有核算字段
                            has_accounting_field = "是否核算" in df_current.columns

                            # 原始计算（支持核算筛选）
                            total_value_raw = 0.0
                            valid_count_raw = 0
                            error_count = 0
                            non_accounting_count = 0  # 非核算资产数量

                            for _, row in df_current.iterrows():
                                try:
                                    # 🆕 检查是否核算
                                    if has_accounting_field:
                                        accounting_status = str(row.get("是否核算", "")).strip()
                                        if accounting_status not in ["是", "Y", "y", "Yes", "YES", "1", "True", "true"]:
                                            non_accounting_count += 1
                                            continue  # 跳过非核算资产

                                    value = safe_convert_to_float(row.get("固定资产原值", 0))
                                    if value > 0:
                                        total_value_raw += value
                                        valid_count_raw += 1
                                    elif value == 0:
                                        pass  # 价值为0的记录
                                    else:
                                        error_count += 1
                                except:
                                    error_count += 1

                            # 去重计算（支持核算筛选）
                            df_deduped = df_current.drop_duplicates(subset=['固定资产编码'], keep='first')
                            total_value_dedup = 0.0
                            valid_count_dedup = 0
                            non_accounting_dedup_count = 0

                            for _, row in df_deduped.iterrows():
                                try:
                                    # 🆕 检查是否核算
                                    if has_accounting_field:
                                        accounting_status = str(row.get("是否核算", "")).strip()
                                        if accounting_status not in ["是", "Y", "y", "Yes", "YES", "1", "True", "true"]:
                                            non_accounting_dedup_count += 1
                                            continue  # 跳过非核算资产

                                    value = safe_convert_to_float(row.get("固定资产原值", 0))
                                    if value > 0:
                                        total_value_dedup += value
                                        valid_count_dedup += 1
                                except:
                                    pass

                            # 显示结果
                            duplicate_count = len(df_current) - len(df_deduped)

                            if duplicate_count > 0:
                                st.metric("固定资产原值总计", f"¥{total_value_dedup:,.2f}")
                                caption_text = f"去重后金额（删除{duplicate_count}条重复）"
                                if has_accounting_field and non_accounting_dedup_count > 0:
                                    caption_text += f" | 已排除{non_accounting_dedup_count}条非核算"
                                st.caption(caption_text)
                            else:
                                st.metric("固定资产原值总计", f"¥{total_value_raw:,.2f}")
                                caption_text = "无重复记录"
                                if has_accounting_field and non_accounting_count > 0:
                                    caption_text += f" | 已排除{non_accounting_count}条非核算"
                                st.caption(caption_text)

                            # 显示处理统计
                            effective_valid_count = valid_count_dedup if duplicate_count > 0 else valid_count_raw
                            effective_total_count = len(df_deduped) if duplicate_count > 0 else len(df_current)
                            effective_non_accounting = non_accounting_dedup_count if duplicate_count > 0 else non_accounting_count

                            if effective_valid_count > 0:
                                success_rate = (effective_valid_count / (
                                            effective_valid_count + effective_non_accounting + error_count)) * 100
                                st.success(
                                    f"✅ 成功处理 {effective_valid_count}/{effective_total_count} 条记录 ({success_rate:.1f}%)")

                                if error_count > 0:
                                    st.warning(f"⚠️ {error_count} 条记录的固定资产原值字段无法转换为数字")

                                # 🆕 显示核算筛选统计
                                if has_accounting_field and effective_non_accounting > 0:
                                    st.info(f"📊 已排除 {effective_non_accounting} 条非核算资产")
                            else:
                                st.error("❌ 所有固定资产原值字段都无法转换为有效数字")

                            # 去重计算
                            df_deduped = df_current.drop_duplicates(subset=['固定资产编码'], keep='first')
                            total_value_dedup = 0.0
                            valid_count_dedup = 0

                            for _, row in df_deduped.iterrows():
                                try:
                                    value = safe_convert_to_float(row.get("固定资产原值", 0))
                                    if value > 0:
                                        total_value_dedup += value
                                        valid_count_dedup += 1
                                except:
                                    pass

                            # 显示结果
                            duplicate_count = len(df_current) - len(df_deduped)

                            if duplicate_count > 0:
                                st.metric("固定资产原值总计", f"¥{total_value_dedup:,.2f}")
                                st.caption(f"去重后金额（删除{duplicate_count}条重复）")
                            else:
                                st.metric("固定资产原值总计", f"¥{total_value_raw:,.2f}")
                                st.caption("无重复记录")

                            # 显示处理统计
                            if valid_count_raw > 0:
                                success_rate = (valid_count_raw / len(df_current)) * 100
                                st.success(
                                    f"✅ 成功处理 {valid_count_raw}/{len(df_current)} 条记录 ({success_rate:.1f}%)")

                                if error_count > 0:
                                    st.warning(f"⚠️ {error_count} 条记录的固定资产原值字段无法转换为数字")
                            else:
                                st.error("❌ 所有固定资产原值字段都无法转换为有效数字")

                                # 显示调试信息
                                with st.expander("🔧 固定资产原值字段问题分析"):
                                    st.write("**前5条记录的固定资产原值字段内容：**")
                                    sample_data = df_current["固定资产原值"].head(5).tolist()
                                    for i, value in enumerate(sample_data, 1):
                                        converted = safe_convert_to_float(value)
                                        st.write(f"{i}. 原值: `{value}` ({type(value).__name__}) → 转换后: {converted}")

                                    st.markdown("**可能的问题：**")
                                    st.markdown("- 字段包含文本而非数字")
                                    st.markdown("- 数字格式不标准（如包含特殊字符）")
                                    st.markdown("- 字段为空值或NaN")
                                    st.markdown("- 数字使用了特殊的千位分隔符")

                        except Exception as e:
                            st.metric("固定资产原值总计", "计算错误")
                            st.error(f"❌ 计算固定资产原值时出错: {str(e)}")

                            with st.expander("🚨 错误详情"):
                                st.code(f"错误类型: {type(e).__name__}\n错误信息: {str(e)}")
                                if len(df_current) > 0:
                                    st.write("数据样本：", df_current["固定资产原值"].head(3).tolist())

                    elif "资产价值" in df_current.columns:
                        # 备用：如果没有固定资产原值字段，使用资产价值字段
                        st.warning("⚠️ 未找到'固定资产原值'字段，使用'资产价值'字段")
                        try:
                            total_value = sum(
                                safe_convert_to_float(row.get("资产价值", 0)) for _, row in df_current.iterrows())
                            st.metric("资产价值总计", f"¥{total_value:,.2f}")
                            st.caption("使用资产价值字段")
                        except Exception as e:
                            st.metric("资产价值总计", "计算错误")
                            st.error(f"❌ 计算资产价值时出错: {str(e)}")

                    else:
                        st.metric("资产价值总计", "字段缺失")
                        st.error("❌ 数据中没有'固定资产原值'或'资产价值'字段")

                        with st.expander("📋 当前数据字段列表"):
                            st.write("**现有字段：**")
                            for i, col in enumerate(df_current.columns, 1):
                                st.write(f"{i}. `{col}`")

                            st.info("💡 请确保Excel文件中有名为'固定资产原值'的列")

                with col3:
                    if "存放部门" in df_current.columns:
                        dept_count = df_current["存放部门"].nunique()
                        st.metric("涉及部门数", dept_count)

            # 🗑️ 实物数据删除功能（保持不变）
            st.markdown("---")
            with st.expander("🗑️ 实物数据快速删除", expanded=False):
                st.warning("⚠️ **注意**：删除操作不可恢复，请谨慎操作！")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**🎯 条件删除**")
                    delete_condition = st.selectbox(
                        "选择删除条件",
                        ["选择条件...", "固定资产原值为0", "固定资产名称为空", "存放部门为空", "自定义条件"],
                        key="physical_delete_condition"
                    )

                    if delete_condition == "自定义条件":
                        custom_field = st.selectbox("选择字段", df_current.columns.tolist(),
                                                    key="physical_custom_field")
                        custom_value = st.text_input("输入要删除的值", key="physical_custom_value")

                        if st.button("🗑️ 执行条件删除", key="physical_condition_delete"):
                            if custom_value:
                                original_count = len(current_physical)
                                filtered_data = [
                                    record for record in current_physical
                                    if str(record.get(custom_field, "")) != custom_value
                                ]
                                save_data(filtered_data, PHYSICAL_DATA_FILE)
                                deleted_count = original_count - len(filtered_data)
                                st.success(f"✅ 已删除 {deleted_count} 条记录")
                                st.rerun()

                    elif delete_condition != "选择条件..." and st.button("🗑️ 执行条件删除",
                                                                         key="physical_preset_delete"):
                        original_count = len(current_physical)
                        if delete_condition == "固定资产原值为0":
                            filtered_data = [
                                record for record in current_physical
                                if safe_convert_to_float(record.get("固定资产原值", 0)) != 0
                            ]
                        elif delete_condition == "固定资产名称为空":
                            filtered_data = [
                                record for record in current_physical
                                if str(record.get("固定资产名称", "")).strip() != ""
                            ]
                        elif delete_condition == "存放部门为空":
                            filtered_data = [
                                record for record in current_physical
                                if str(record.get("存放部门", "")).strip() != ""
                            ]

                        save_data(filtered_data, PHYSICAL_DATA_FILE)
                        deleted_count = original_count - len(filtered_data)
                        st.success(f"✅ 已删除 {deleted_count} 条记录")
                        st.rerun()

                with col2:
                    st.markdown("**🔢 按编码删除**")
                    delete_codes = st.text_area(
                        "输入要删除的固定资产编码（每行一个）",
                        height=100,
                        key="physical_delete_codes"
                    )

                    if st.button("🗑️ 删除指定编码", key="physical_code_delete"):
                        if delete_codes.strip():
                            codes_to_delete = [code.strip() for code in delete_codes.split('\n') if code.strip()]
                            original_count = len(current_physical)
                            filtered_data = [
                                record for record in current_physical
                                if record.get("固定资产编码", "") not in codes_to_delete
                            ]
                            save_data(filtered_data, PHYSICAL_DATA_FILE)
                            deleted_count = original_count - len(filtered_data)
                            st.success(f"✅ 已删除 {deleted_count} 条记录")
                            st.rerun()

                with col3:
                    st.markdown("**🚨 危险操作**")
                    st.error("⚠️ 以下操作将清空所有实物数据")

                    confirm_clear = st.checkbox("我确认要清空所有实物数据", key="physical_confirm_clear")

                    if confirm_clear:
                        final_confirm = st.text_input(
                            "请输入 'DELETE ALL' 确认清空",
                            key="physical_final_confirm"
                        )

                        if final_confirm == "DELETE ALL" and st.button("🚨 清空所有数据", key="physical_clear_all"):
                            save_data([], PHYSICAL_DATA_FILE)
                            st.success("✅ 已清空所有实物数据")
                            st.rerun()

        else:
            st.warning("⚠️ 暂无实物台账数据")

        # 实物数据上传部分
        physical_file = st.file_uploader(
            "上传实物台账Excel文件",
            type=['xlsx', 'xls'],
            key="physical_upload",
            help="Excel文件应包含'固定资产编码'列作为主键，'固定资产原值'列作为价值字段"
        )

        if physical_file is not None:
            try:
                physical_df = pd.read_excel(physical_file)
                st.success(f"✅ 成功读取实物数据: {len(physical_df)} 行 x {len(physical_df.columns)} 列")

                required_columns = ["固定资产编码"]
                missing_columns = [col for col in required_columns if col not in physical_df.columns]

                if missing_columns:
                    st.error(f"❌ 缺少必需字段：{missing_columns}")
                    st.stop()

                st.subheader("📊 上传数据完整预览")

                search_upload = st.text_input("🔍 搜索上传数据", key="search_physical_upload")
                if search_upload:
                    mask = physical_df.astype(str).apply(
                        lambda x: x.str.contains(search_upload, case=False, na=False)).any(axis=1)
                    df_filtered = physical_df[mask]
                    st.write(f"搜索结果：{len(df_filtered)} 条记录")
                    st.dataframe(df_filtered, use_container_width=True, height=500)
                else:
                    st.dataframe(physical_df, use_container_width=True, height=500)

                # 数据质量检查
                st.subheader("🔍 数据质量检查")

                col1, col2, col3 = st.columns(3)
                with col1:
                    asset_codes = physical_df["固定资产编码"].dropna()
                    duplicate_codes = asset_codes[asset_codes.duplicated()].unique()

                    if len(duplicate_codes) > 0:
                        st.error(f"❌ 重复编码: {len(duplicate_codes)} 个")
                        with st.expander("查看重复记录"):
                            duplicate_records = physical_df[physical_df["固定资产编码"].isin(duplicate_codes)]
                            st.dataframe(duplicate_records, use_container_width=True)
                    else:
                        st.success("✅ 编码唯一性通过")

                with col2:
                    null_counts = physical_df.isnull().sum()
                    total_nulls = null_counts.sum()
                    if total_nulls > 0:
                        st.warning(f"⚠️ 空值: {total_nulls} 个")
                        with st.expander("查看空值统计"):
                            st.dataframe(null_counts[null_counts > 0].to_frame("空值数量"), use_container_width=True)
                    else:
                        st.success("✅ 无空值")

                with col3:
                    # ✅ 修复：优先使用固定资产原值字段
                    if "固定资产原值" in physical_df.columns:
                        total_value = sum(safe_convert_to_float(val) for val in physical_df["固定资产原值"])
                        st.metric("固定资产原值总计", f"¥{total_value:,.2f}")
                    elif "资产价值" in physical_df.columns:
                        total_value = sum(safe_convert_to_float(val) for val in physical_df["资产价值"])
                        st.metric("资产价值总计", f"¥{total_value:,.2f}")
                        st.caption("使用资产价值字段")
                    else:
                        st.warning("⚠️ 未找到价值字段")

                # 导入选项
                st.markdown("---")
                st.subheader("📥 导入选项")

                import_mode = st.radio(
                    "选择导入模式",
                    ["覆盖导入（清空原数据）", "追加导入（保留原数据）", "更新导入（按编码更新）"],
                    key="physical_import_mode"
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 确认导入实物数据", type="primary", use_container_width=True):
                        # 数据标准化处理
                        processed_data = []
                        for _, row in physical_df.iterrows():
                            record = {}
                            # 确保主键字段正确
                            record["固定资产编码"] = str(row.get("固定资产编码", "")).strip()
                            record["固定资产名称"] = str(row.get("固定资产名称", "")).strip()

                            # ✅ 修复：优先处理固定资产原值字段
                            record["固定资产原值"] = safe_convert_to_float(row.get("固定资产原值", 0))

                            # 如果没有固定资产原值，尝试其他价值字段
                            if record["固定资产原值"] == 0:
                                for alt_field in ["资产价值", "原值", "账面价值"]:
                                    if alt_field in row and safe_convert_to_float(row.get(alt_field, 0)) > 0:
                                        record["固定资产原值"] = safe_convert_to_float(row.get(alt_field, 0))
                                        break

                            # 其他标准字段
                            record["资产价值"] = record["固定资产原值"]  # 保持兼容性
                            record["存放部门"] = str(row.get("存放部门", "")).strip()
                            record["保管人"] = str(row.get("保管人", "")).strip()
                            record["资产状态"] = str(row.get("资产状态", "")).strip()
                            record["使用人"] = str(row.get("使用人", "")).strip()
                            record["固定资产类型"] = str(row.get("固定资产类型", "")).strip()

                            # 保留所有其他字段
                            for col in physical_df.columns:
                                if col not in record:
                                    value = row.get(col)
                                    if pd.isna(value):
                                        record[col] = ""
                                    elif isinstance(value, (int, float)):
                                        record[col] = float(value) if not pd.isna(value) else 0
                                    else:
                                        record[col] = str(value).strip() if value is not None else ""

                            if record["固定资产编码"]:
                                processed_data.append(record)

                        # 根据导入模式处理数据
                        if import_mode == "覆盖导入（清空原数据）":
                            save_data(processed_data, PHYSICAL_DATA_FILE)
                            st.success(f"✅ 覆盖导入 {len(processed_data)} 条实物资产记录")

                        elif import_mode == "追加导入（保留原数据）":
                            existing_data = load_data(PHYSICAL_DATA_FILE)
                            combined_data = existing_data + processed_data
                            save_data(combined_data, PHYSICAL_DATA_FILE)
                            st.success(f"✅ 追加导入 {len(processed_data)} 条记录，总计 {len(combined_data)} 条")

                        elif import_mode == "更新导入（按编码更新）":
                            existing_data = load_data(PHYSICAL_DATA_FILE)
                            existing_dict = {record.get("固定资产编码"): record for record in existing_data}

                            # 更新或添加新记录
                            for record in processed_data:
                                existing_dict[record["固定资产编码"]] = record

                            updated_data = list(existing_dict.values())
                            save_data(updated_data, PHYSICAL_DATA_FILE)
                            st.success(f"✅ 更新导入完成，总计 {len(updated_data)} 条记录")

                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("📥 导出当前数据", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            physical_df.to_excel(writer, index=False, sheet_name='实物数据')

                        st.download_button(
                            label="⬇️ 下载Excel文件",
                            data=output.getvalue(),
                            file_name=f"实物数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                with col3:
                    if st.button("🔄 重新上传", use_container_width=True):
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件读取失败：{str(e)}")

    with tab3:
        st.subheader("🔗 映射关系数据")
        st.markdown("**映射规则**：建立财务系统'资产编号+序号' ↔ 实物台账'固定资产编码'的对应关系")

        # 显示当前映射数据
        current_mapping = load_data(MAPPING_DATA_FILE)
        if current_mapping:
            st.success(f"✅ 当前已有 {len(current_mapping)} 条映射关系")

            with st.expander("📊 查看当前所有映射关系", expanded=False):
                df_mapping = pd.DataFrame(current_mapping)

                search_mapping = st.text_input("🔍 搜索映射关系", key="search_mapping_current")
                if search_mapping:
                    mask = df_mapping.astype(str).apply(
                        lambda x: x.str.contains(search_mapping, case=False, na=False)).any(axis=1)
                    df_filtered = df_mapping[mask]
                    st.write(f"搜索结果：{len(df_filtered)} 条记录")
                    st.dataframe(df_filtered, use_container_width=True, height=400)
                else:
                    st.dataframe(df_mapping, use_container_width=True, height=400)

            # 🗑️ 映射关系删除功能
            st.markdown("---")
            with st.expander("🗑️ 映射关系快速删除", expanded=False):
                st.warning("⚠️ **注意**：删除操作不可恢复，请谨慎操作！")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**🎯 条件删除**")
                    delete_condition = st.selectbox(
                        "选择删除条件",
                        ["选择条件...", "财务编号为空", "实物编码为空", "自定义条件"],
                        key="mapping_delete_condition"
                    )

                    if delete_condition == "自定义条件":
                        custom_field = st.selectbox("选择字段", df_mapping.columns.tolist(), key="mapping_custom_field")
                        custom_value = st.text_input("输入要删除的值", key="mapping_custom_value")

                        if st.button("🗑️ 执行条件删除", key="mapping_condition_delete"):
                            if custom_value:
                                original_count = len(current_mapping)
                                filtered_data = [
                                    record for record in current_mapping
                                    if str(record.get(custom_field, "")) != custom_value
                                ]
                                save_data(filtered_data, MAPPING_DATA_FILE)
                                deleted_count = original_count - len(filtered_data)
                                st.success(f"✅ 已删除 {deleted_count} 条映射关系")
                                st.rerun()

                    elif delete_condition != "选择条件..." and st.button("🗑️ 执行条件删除",
                                                                         key="mapping_preset_delete"):
                        original_count = len(current_mapping)
                        if delete_condition == "财务编号为空":
                            filtered_data = [
                                record for record in current_mapping
                                if str(record.get("资产编号+序号", "")).strip() != ""
                            ]
                        elif delete_condition == "实物编码为空":
                            filtered_data = [
                                record for record in current_mapping
                                if str(record.get("固定资产编码", "")).strip() != ""
                            ]

                        save_data(filtered_data, MAPPING_DATA_FILE)
                        deleted_count = original_count - len(filtered_data)
                        st.success(f"✅ 已删除 {deleted_count} 条映射关系")
                        st.rerun()

                with col2:
                    st.markdown("**🔢 按编号删除**")
                    delete_type = st.radio(
                        "删除类型",
                        ["按财务编号", "按实物编码"],
                        key="mapping_delete_type"
                    )

                    delete_codes = st.text_area(
                        f"输入要删除的{'财务编号' if delete_type == '按财务编号' else '实物编码'}（每行一个）",
                        height=100,
                        key="mapping_delete_codes"
                    )

                    if st.button("🗑️ 删除相关映射", key="mapping_code_delete"):
                        if delete_codes.strip():
                            codes_to_delete = [code.strip() for code in delete_codes.split('\n') if code.strip()]
                            original_count = len(current_mapping)

                            if delete_type == "按财务编号":
                                filtered_data = [
                                    record for record in current_mapping
                                    if record.get("资产编号+序号", "") not in codes_to_delete
                                ]
                            else:
                                filtered_data = [
                                    record for record in current_mapping
                                    if record.get("固定资产编码", "") not in codes_to_delete
                                ]

                            save_data(filtered_data, MAPPING_DATA_FILE)
                            deleted_count = original_count - len(filtered_data)
                            st.success(f"✅ 已删除 {deleted_count} 条映射关系")
                            st.rerun()

                with col3:
                    st.markdown("**🚨 危险操作**")
                    st.error("⚠️ 以下操作将清空所有映射关系")

                    confirm_clear = st.checkbox("我确认要清空所有映射关系", key="mapping_confirm_clear")

                    if confirm_clear:
                        final_confirm = st.text_input(
                            "请输入 'DELETE ALL' 确认清空",
                            key="mapping_final_confirm"
                        )

                        if final_confirm == "DELETE ALL" and st.button("🚨 清空所有映射", key="mapping_clear_all"):
                            save_data([], MAPPING_DATA_FILE)
                            st.success("✅ 已清空所有映射关系")
                            st.rerun()

        else:
            st.warning("⚠️ 暂无映射关系数据")

        # 映射关系上传部分
        mapping_file = st.file_uploader(
            "上传映射关系Excel文件",
            type=['xlsx', 'xls'],
            key="mapping_upload",
            help="Excel文件应包含'资产编号+序号'和'固定资产编码'列"
        )

        if mapping_file is not None:
            try:
                mapping_df = pd.read_excel(mapping_file)
                st.success(f"✅ 成功读取映射数据: {len(mapping_df)} 行 x {len(mapping_df.columns)} 列")

                required_columns = ["资产编号+序号", "固定资产编码"]
                missing_columns = [col for col in required_columns if col not in mapping_df.columns]

                if missing_columns:
                    st.error(f"❌ 缺少必需字段：{missing_columns}")
                    st.stop()

                st.subheader("📊 映射数据预览")
                st.dataframe(mapping_df, use_container_width=True, height=400)

                # 导入选项
                st.markdown("---")
                st.subheader("📥 导入选项")

                import_mode = st.radio(
                    "选择导入模式",
                    ["覆盖导入（清空原数据）", "追加导入（保留原数据）"],
                    key="mapping_import_mode"
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 确认导入映射数据", type="primary", use_container_width=True):
                        processed_data = []
                        for _, row in mapping_df.iterrows():
                            record = {
                                "资产编号+序号": str(row.get("资产编号+序号", "")).strip(),
                                "固定资产编码": str(row.get("固定资产编码", "")).strip()
                            }

                            # 添加其他列
                            for col in mapping_df.columns:
                                if col not in ["资产编号+序号", "固定资产编码"]:
                                    record[col] = str(row.get(col, "")).strip()

                            if record["资产编号+序号"] and record["固定资产编码"]:
                                processed_data.append(record)

                        # 根据导入模式处理数据
                        if import_mode == "覆盖导入（清空原数据）":
                            save_data(processed_data, MAPPING_DATA_FILE)
                            st.success(f"✅ 覆盖导入 {len(processed_data)} 条映射关系")

                        elif import_mode == "追加导入（保留原数据）":
                            existing_data = load_data(MAPPING_DATA_FILE)
                            combined_data = existing_data + processed_data
                            save_data(combined_data, MAPPING_DATA_FILE)
                            st.success(f"✅ 追加导入 {len(processed_data)} 条记录，总计 {len(combined_data)} 条")

                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("📥 导出当前数据", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            mapping_df.to_excel(writer, index=False, sheet_name='映射数据')

                        st.download_button(
                            label="⬇️ 下载Excel文件",
                            data=output.getvalue(),
                            file_name=f"映射数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                with col3:
                    if st.button("🔄 重新上传", use_container_width=True):
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件读取失败：{str(e)}")

    with tab4:
        st.subheader("🗑️ 数据删除管理中心")
        st.markdown("**统一管理所有数据的删除操作，支持批量操作和数据备份**")

        # 数据概览
        st.markdown("---")
        st.subheader("📊 当前数据概览")

        col1, col2, col3 = st.columns(3)

        with col1:
            financial_data = load_data(FINANCIAL_DATA_FILE)
            st.metric(
                label="💰 财务系统数据",
                value=f"{len(financial_data)} 条",
                delta=f"总价值: {sum(safe_convert_to_float(record.get('资产价值', 0)) for record in financial_data):,.2f}" if financial_data else "无数据"
            )

        with col2:
            physical_data = load_data(PHYSICAL_DATA_FILE)
            st.metric(
                label="📦 实物台账数据",
                value=f"{len(physical_data)} 条",
                delta=f"总价值: {sum(safe_convert_to_float(record.get('资产价值', 0)) for record in physical_data):,.2f}" if physical_data else "无数据"
            )

        with col3:
            mapping_data = load_data(MAPPING_DATA_FILE)
            st.metric(
                label="🔗 映射关系数据",
                value=f"{len(mapping_data)} 条",
                delta="映射关系" if mapping_data else "无数据"
            )

        # 🔄 数据备份功能
        st.markdown("---")
        st.subheader("💾 数据备份")
        st.info("💡 **建议**：在执行删除操作前，先备份当前数据以防意外")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 创建完整数据备份", use_container_width=True):
                try:
                    backup_data = {
                        "financial_data": financial_data,
                        "physical_data": physical_data,
                        "mapping_data": mapping_data,
                        "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # 创建Excel备份文件
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        if financial_data:
                            pd.DataFrame(financial_data).to_excel(writer, index=False, sheet_name='财务数据')
                        if physical_data:
                            pd.DataFrame(physical_data).to_excel(writer, index=False, sheet_name='实物数据')
                        if mapping_data:
                            pd.DataFrame(mapping_data).to_excel(writer, index=False, sheet_name='映射数据')

                    st.download_button(
                        label="⬇️ 下载完整备份文件",
                        data=output.getvalue(),
                        file_name=f"完整数据备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("✅ 备份文件已生成，请点击下载")

                except Exception as e:
                    st.error(f"❌ 备份失败：{str(e)}")

        with col2:
            st.markdown("**📋 备份内容包括：**")
            st.markdown("- 💰 所有财务系统数据")
            st.markdown("- 📦 所有实物台账数据")
            st.markdown("- 🔗 所有映射关系数据")
            st.markdown("- 🕐 备份时间戳")

        # 🗑️ 批量删除功能
        st.markdown("---")
        st.subheader("🗑️ 批量删除操作")
        st.error("⚠️ **危险区域**：以下操作将永久删除数据，请确保已备份重要数据！")

        # 选择性删除
        st.markdown("**🎯 选择性删除**")
        delete_options = st.multiselect(
            "选择要删除的数据类型",
            ["财务系统数据", "实物台账数据", "映射关系数据"],
            key="batch_delete_options"
        )

        if delete_options:
            st.warning(f"⚠️ 将删除：{', '.join(delete_options)}")

            # 双重确认
            col1, col2 = st.columns(2)

            with col1:
                confirm_delete = st.checkbox(
                    f"我确认要删除选中的 {len(delete_options)} 类数据",
                    key="batch_confirm_delete"
                )

            with col2:
                if confirm_delete:
                    final_confirm = st.text_input(
                        "请输入 'DELETE SELECTED' 最终确认",
                        key="batch_final_confirm"
                    )

                    if final_confirm == "DELETE SELECTED" and st.button("🗑️ 执行批量删除", key="batch_execute_delete"):
                        deleted_count = 0

                        if "财务系统数据" in delete_options:
                            save_data([], FINANCIAL_DATA_FILE)
                            deleted_count += len(financial_data)
                            st.success("✅ 已清空财务系统数据")

                        if "实物台账数据" in delete_options:
                            save_data([], PHYSICAL_DATA_FILE)
                            deleted_count += len(physical_data)
                            st.success("✅ 已清空实物台账数据")

                        if "映射关系数据" in delete_options:
                            save_data([], MAPPING_DATA_FILE)
                            deleted_count += len(mapping_data)
                            st.success("✅ 已清空映射关系数据")

                        st.success(f"🎉 批量删除完成，共删除 {deleted_count} 条记录")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()

        # 🚨 完全重置
        st.markdown("---")
        st.markdown("**🚨 完全重置系统**")
        st.error("💀 **极度危险**：此操作将清空所有数据，包括财务、实物和映射关系！")

        reset_confirm1 = st.checkbox("我理解此操作的后果", key="reset_confirm1")

        if reset_confirm1:
            reset_confirm2 = st.checkbox("我已备份所有重要数据", key="reset_confirm2")

            if reset_confirm2:
                reset_confirm3 = st.text_input(
                    "请输入 'RESET ALL DATA' 确认完全重置",
                    key="reset_final_confirm"
                )

                if reset_confirm3 == "RESET ALL DATA" and st.button("💀 完全重置系统", key="system_reset"):
                    # 清空所有数据文件
                    save_data([], FINANCIAL_DATA_FILE)
                    save_data([], PHYSICAL_DATA_FILE)
                    save_data([], MAPPING_DATA_FILE)

                    st.success("✅ 系统已完全重置")
                    st.info("🔄 页面将在3秒后刷新...")
                    time.sleep(3)
                    st.rerun()

        # 📊 删除操作统计
        st.markdown("---")
        st.subheader("📊 删除操作记录")
        st.info("💡 **提示**：系统会记录删除操作的基本统计信息")

        # 这里可以添加删除操作的日志记录功能
        if st.button("🔍 查看操作日志", key="view_delete_log"):
            st.info("📝 操作日志功能开发中...")
            # 未来可以添加操作日志的显示

# 需要添加的辅助函数
import time
from datetime import datetime
from io import BytesIO


def safe_convert_to_float(value):
    """安全转换为浮点数 - 增强版"""
    try:
        # 处理pandas NaN
        if pd.isna(value):
            return 0.0

        if value is None or value == "":
            return 0.0

        # 处理字符串类型的数值
        if isinstance(value, str):
            # 移除货币符号和逗号
            cleaned_value = value.replace("¥", "").replace("$", "").replace("€", "").replace(",", "").replace("，", "").strip()
            if cleaned_value == "" or cleaned_value == "-" or cleaned_value.lower() in ['nan', 'null', 'none']:
                return 0.0
            return float(cleaned_value)

        # 处理numpy类型
        if hasattr(value, 'dtype'):  # numpy类型
            if pd.isna(value):
                return 0.0
            return float(value)

        # 处理数字类型
        if isinstance(value, (int, float)):
            if pd.isna(value):
                return 0.0
            return float(value)

        return float(value)
    except (ValueError, TypeError, OverflowError):
        return 0.0


def mapping_query_page():
    """映射查询页面"""
    st.header("🔍 资产映射关系查询")

    # 加载数据
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)

    # 修改：检查所有三个数据源
    if not all([financial_data, physical_data, mapping_data]):
        missing = []
        if not financial_data:
            missing.append("财务系统数据")
        if not physical_data:
            missing.append("实物台账数据")
        if not mapping_data:
            missing.append("映射关系数据")
        st.warning(f"⚠️ 请先导入：{', '.join(missing)}")
        return
    # ⚙️ 字段映射配置
    st.markdown("### ⚙️ 字段映射配置")

    with st.expander("配置数据字段映射", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**财务系统字段配置**")

            # 获取财务数据的所有字段
            financial_fields = list(financial_data[0].keys()) if financial_data else []

            financial_original_field = st.selectbox(
                "原值字段",
                financial_fields,
                index=financial_fields.index("资产价值") if "资产价值" in financial_fields else 0,
                key="fin_original"
            )

            financial_depreciation_field = st.selectbox(
                "累计折旧字段",
                financial_fields,
                index=financial_fields.index("累计折旧") if "累计折旧" in financial_fields else 0,
                key="fin_depreciation"
            )

            financial_net_field = st.selectbox(
                "净值字段",
                financial_fields,
                index=financial_fields.index("净额") if "净额" in financial_fields else 0,
                key="fin_net"
            )

        with col2:
            st.markdown("**实物系统字段配置**")

            # 获取实物数据的所有字段
            physical_fields = list(physical_data[0].keys()) if physical_data else []

            physical_original_field = st.selectbox(
                "原值字段",
                physical_fields,
                index=physical_fields.index("固定资产原值") if "固定资产原值" in physical_fields else 0,
                key="phy_original"
            )

            physical_depreciation_field = st.selectbox(
                "累计折旧字段",
                physical_fields,
                index=physical_fields.index("累计折旧") if "累计折旧" in physical_fields else 0,
                key="phy_depreciation"
            )

            # 实物系统净值字段（可选，如果没有则计算）
            physical_net_field = st.selectbox(
                "净值字段（可选）",
                ["计算得出"] + physical_fields,
                key="phy_net"
            )

    # 🔍 数据调试信息部分
    st.markdown("### 🔍 数据字段调试信息")

    with st.expander("查看数据字段详情", expanded=False):
        if financial_data:
            st.write("**财务系统数据示例（前3条）：**")
            for i, record in enumerate(financial_data[:3]):
                st.write(f"记录 {i + 1}:")
                st.json(record)

        if physical_data:
            st.write("**实物系统数据示例（前3条）：**")
            for i, record in enumerate(physical_data[:3]):
                st.write(f"记录 {i + 1}:")
                st.json(record)
    # 创建索引以提高查询效率
    financial_index = create_data_index(financial_data, "资产编号+序号")
    physical_index = create_data_index(physical_data, "固定资产编码")
    financial_to_physical_mapping, physical_to_financial_mapping = create_mapping_index(mapping_data)

    # 显示映射统计信息
    st.info(
        f"📊 数据概况：财务资产 {len(financial_data)} 条，实物资产 {len(physical_data)} 条，映射关系 {len(mapping_data)} 条")

    # 查询选项
    query_type = st.selectbox(
        "选择查询方式",
        ["按资产编号选择查询", "按资产编号+序号查询", "按实物台账编号查询", "按资产名称搜索", "批量查询"]
    )

    if query_type == "按资产编号选择查询":
        st.subheader("📋 资产编号选择查询")

        # 🔍 提取所有财务资产的资产编号（去除+序号部分）
        asset_numbers = set()
        asset_number_to_full_codes = {}  # 资产编号到完整编号+序号的映射

        for record in financial_data:
            full_code = str(record.get('资产编号+序号', '')).strip()
            if full_code:
                # 尝试提取资产编号部分（去除序号）
                asset_number = full_code

                # 🔧 智能提取资产编号（去除序号部分）
                import re

                # 方法1：如果包含+号，取+号前的部分
                if '+' in full_code:
                    asset_number = full_code.split('+')[0].strip()
                # 方法2：如果包含-号，取-号前的部分
                elif '-' in full_code:
                    asset_number = full_code.split('-')[0].strip()
                # 方法3：如果包含_号，取_号前的部分
                elif '_' in full_code:
                    asset_number = full_code.split('_')[0].strip()
                # 方法4：使用正则表达式，提取字母+数字的主要部分
                else:
                    # 匹配模式：字母开头，后跟数字，可能有序号
                    match = re.match(r'^([A-Za-z]+\d+)', full_code)
                    if match:
                        asset_number = match.group(1)
                    else:
                        # 如果无法智能提取，使用原始编号
                        asset_number = full_code

                asset_numbers.add(asset_number)

                # 建立资产编号到完整编号的映射
                if asset_number not in asset_number_to_full_codes:
                    asset_number_to_full_codes[asset_number] = []
                asset_number_to_full_codes[asset_number].append(full_code)

        # 排序资产编号列表
        sorted_asset_numbers = sorted(list(asset_numbers))

        if not sorted_asset_numbers:
            st.warning("⚠️ 未找到可用的资产编号")
            return

        # 🎯 资产编号选择器
        col1, col2 = st.columns([2, 1])

        with col1:
            selected_asset_number = st.selectbox(
                f"选择资产编号 (共 {len(sorted_asset_numbers)} 个)",
                ["请选择资产编号..."] + sorted_asset_numbers,
                key="asset_number_selector"
            )

        with col2:
            # 显示统计信息
            if selected_asset_number != "请选择资产编号...":
                related_count = len(asset_number_to_full_codes.get(selected_asset_number, []))
                st.metric("相关资产数量", f"{related_count} 条")

        # 🔍 搜索功能
        search_filter = st.text_input(
            "🔍 搜索资产编号 (可输入部分编号进行筛选)",
            placeholder="输入编号关键词进行快速筛选...",
            key="asset_number_search"
        )

        # 如果有搜索条件，过滤资产编号列表
        if search_filter:
            filtered_asset_numbers = [num for num in sorted_asset_numbers
                                      if search_filter.lower() in num.lower()]

            if filtered_asset_numbers:
                st.info(f"🎯 找到 {len(filtered_asset_numbers)} 个匹配的资产编号")

                # 显示筛选后的选择器
                selected_asset_number_filtered = st.selectbox(
                    "筛选结果中选择:",
                    ["请选择..."] + filtered_asset_numbers,
                    key="filtered_asset_selector"
                )

                if selected_asset_number_filtered != "请选择...":
                    selected_asset_number = selected_asset_number_filtered
            else:
                st.warning(f"⚠️ 没有找到包含 '{search_filter}' 的资产编号")

        # 🔍 执行查询
        if selected_asset_number != "请选择资产编号..." and st.button("🔍 查询选定资产编号", type="primary"):
            # 获取该资产编号下的所有完整编号
            full_codes = asset_number_to_full_codes.get(selected_asset_number, [])

            if full_codes:
                st.success(f"✅ 资产编号 '{selected_asset_number}' 下共有 {len(full_codes)} 条相关资产")

                # 🎯 显示该资产编号下的所有资产详情
                for i, full_code in enumerate(sorted(full_codes), 1):
                    financial_record = financial_index.get(full_code)

                    if financial_record:
                        # 显示财务资产信息
                        with st.expander(f"📊 资产 #{i}: {full_code} - {financial_record.get('资产名称', '')}",
                                         expanded=True):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.info(f"**完整编号**: {financial_record.get('资产编号+序号', '')}")
                                st.info(f"**资产名称**: {financial_record.get('资产名称', '')}")
                                st.info(f"**资产分类**: {financial_record.get('资产分类', '')}")

                            with col2:
                                financial_value = safe_get_value(financial_record, "资产价值")
                                st.info(f"**资产价值**: ¥{financial_value:,.2f}")
                                st.info(f"**所属部门**: {financial_record.get('部门名称', '')}")
                                st.info(f"**保管人**: {financial_record.get('保管人', '')}")

                            # 查找对应的实物资产
                            physical_codes = financial_to_physical_mapping.get(full_code, [])

                            if physical_codes:
                                st.success(f"✅ 已映射到 {len(physical_codes)} 个实物资产")

                                total_physical_value = 0
                                valid_physical_count = 0

                                for j, physical_code in enumerate(physical_codes, 1):
                                    physical_record = physical_index.get(physical_code)

                                    if physical_record:
                                        # 显示实物资产信息
                                        st.markdown(f"**🔗 对应实物资产 #{j}: {physical_code}**")

                                        col_p1, col_p2 = st.columns(2)
                                        with col_p1:
                                            st.write(f"- **资产编码**: {physical_record.get('固定资产编码', '')}")
                                            st.write(f"- **资产名称**: {physical_record.get('固定资产名称', '')}")
                                            st.write(f"- **资产类型**: {physical_record.get('固定资产类型', '')}")

                                        with col_p2:
                                            physical_value = safe_get_value(physical_record, "资产价值")
                                            st.write(f"- **资产价值**: ¥{physical_value:,.2f}")
                                            st.write(f"- **存放部门**: {physical_record.get('存放部门', '')}")
                                            st.write(f"- **使用状态**: {physical_record.get('使用状态', '')}")

                                        total_physical_value += physical_value
                                        valid_physical_count += 1
                                    else:
                                        st.error(f"❌ 实物资产记录不存在: {physical_code}")

                                # 价值比较
                                if valid_physical_count > 0:
                                    value_diff = financial_value - total_physical_value

                                    col_v1, col_v2, col_v3 = st.columns(3)
                                    with col_v1:
                                        st.metric("财务价值", f"¥{financial_value:,.2f}")
                                    with col_v2:
                                        st.metric("实物总价值", f"¥{total_physical_value:,.2f}")
                                    with col_v3:
                                        st.metric("价值差异", f"¥{value_diff:,.2f}")

                                    if abs(value_diff) > 0.01:
                                        if value_diff > 0:
                                            st.warning(f"⚠️ 财务价值高于实物总价值 ¥{value_diff:,.2f}")
                                        else:
                                            st.warning(f"⚠️ 实物总价值高于财务价值 ¥{abs(value_diff):,.2f}")
                                    else:
                                        st.success("✅ 财务与实物价值一致")
                            else:
                                st.warning("⚠️ 该资产未找到对应的实物资产")
                    else:
                        st.error(f"❌ 财务资产记录不存在: {full_code}")

                # 📊 汇总统计
                st.markdown("---")
                st.subheader(f"📊 资产编号 '{selected_asset_number}' 汇总统计")

                # 计算汇总数据
                total_financial_value = 0
                total_physical_value = 0
                mapped_count = 0
                unmapped_count = 0

                for full_code in full_codes:
                    financial_record = financial_index.get(full_code)
                    if financial_record:
                        total_financial_value += safe_get_value(financial_record, "资产价值")

                        physical_codes = financial_to_physical_mapping.get(full_code, [])
                        if physical_codes:
                            mapped_count += 1
                            for physical_code in physical_codes:
                                physical_record = physical_index.get(physical_code)
                                if physical_record:
                                    total_physical_value += safe_get_value(physical_record, "资产价值")
                        else:
                            unmapped_count += 1

                # 显示汇总统计
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("资产总数", len(full_codes))

                with col2:
                    st.metric("已映射", mapped_count)

                with col3:
                    st.metric("未映射", unmapped_count)

                with col4:
                    mapping_rate = (mapped_count / len(full_codes) * 100) if full_codes else 0
                    st.metric("映射率", f"{mapping_rate:.1f}%")

                # 价值汇总
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("财务总价值", f"¥{total_financial_value:,.2f}")

                with col2:
                    st.metric("实物总价值", f"¥{total_physical_value:,.2f}")

                with col3:
                    total_diff = total_financial_value - total_physical_value
                    st.metric("总价值差异", f"¥{total_diff:,.2f}")
            else:
                st.error(f"❌ 资产编号 '{selected_asset_number}' 下没有找到相关资产")

    if query_type == "按资产编号+序号查询":
        st.subheader("🔍 资产编号+序号查询")

        financial_code = st.text_input("请输入资产编号+序号", placeholder="例如: FS001")

        if st.button("🔍 查询财务资产"):
            if financial_code:
                # 查找财务资产记录
                financial_record = financial_index.get(str(financial_code))

                if financial_record:
                    # 显示财务资产信息
                    with st.expander("📊 财务资产详情", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**资产编号**: {financial_record.get('资产编号+序号', '')}")
                            st.info(f"**资产名称**: {financial_record.get('资产名称', '')}")
                            st.info(f"**资产分类**: {financial_record.get('资产分类', '')}")
                        with col2:
                            financial_value = safe_get_value(financial_record, "资产价值")
                            st.info(f"**资产价值**: ¥{financial_value:,.2f}")
                            st.info(f"**所属部门**: {financial_record.get('部门名称', '')}")
                            st.info(f"**保管人**: {financial_record.get('保管人', '')}")

                    # 查找对应的实物资产（支持多对多）
                    physical_codes = financial_to_physical_mapping.get(str(financial_code), [])

                    if physical_codes:
                        st.success(f"✅ 找到 {len(physical_codes)} 个对应的实物资产")

                        # 用于计算总价值
                        total_physical_value = 0
                        valid_physical_count = 0

                        for i, physical_code in enumerate(physical_codes, 1):
                            physical_record = physical_index.get(physical_code)

                            if physical_record:
                                # 显示实物资产信息
                                with st.expander(f"📋 实物资产详情 #{i} - {physical_code}", expanded=True):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"**资产编号**: {physical_record.get('固定资产编码', '')}")
                                        st.info(f"**资产名称**: {physical_record.get('固定资产名称', '')}")
                                        st.info(f"**资产类型**: {physical_record.get('固定资产类型', '')}")
                                    with col2:
                                        physical_value = safe_get_value(physical_record, "资产价值")
                                        st.info(f"**资产价值**: ¥{physical_value:,.2f}")
                                        st.info(f"**存放部门**: {physical_record.get('存放部门', '')}")
                                        st.info(f"**使用状态**: {physical_record.get('使用状态', '')}")

                                # 累计实物资产价值
                                physical_value = safe_get_value(physical_record, '资产价值')
                                total_physical_value += physical_value
                                valid_physical_count += 1

                            else:
                                st.error(f"❌ 映射的实物资产记录不存在: {physical_code}")

                        # 多对多关系的价值比较
                        if valid_physical_count > 0:
                            st.subheader("💰 价值比较分析")

                            financial_value = safe_get_value(financial_record, '资产价值')

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("财务系统价值", f"¥{financial_value:,.2f}")
                            with col2:
                                st.metric("实物资产总价值", f"¥{total_physical_value:,.2f}")
                            with col3:
                                value_diff = financial_value - total_physical_value
                                st.metric("价值差异", f"¥{value_diff:,.2f}")

                            # 价值差异分析
                            if abs(value_diff) > 0.01:
                                if value_diff > 0:
                                    st.warning(f"⚠️ 财务系统价值高于实物总价值 ¥{value_diff:,.2f}")
                                else:
                                    st.warning(f"⚠️ 实物总价值高于财务系统价值 ¥{abs(value_diff):,.2f}")

                                # 差异率计算
                                if financial_value > 0:
                                    diff_rate = abs(value_diff) / financial_value * 100
                                    st.info(f"📊 差异率: {diff_rate:.2f}%")
                            else:
                                st.success("✅ 财务与实物资产价值一致")

                            # 如果是多个实物资产，显示平均价值
                            if valid_physical_count > 1:
                                avg_physical_value = total_physical_value / valid_physical_count
                                st.info(f"📈 实物资产平均价值: ¥{avg_physical_value:,.2f}")

                        else:
                            st.error("❌ 所有映射的实物资产记录都不存在")

                    else:
                        st.warning("⚠️ 该财务资产未找到对应的实物资产")
                else:
                    st.error("❌ 未找到该资产编号+序号对应的资产")
            else:
                st.warning("⚠️ 请输入资产编号+序号")

    elif query_type == "按实物台账编号查询":
        st.subheader("🔍 实物台账编号查询")

        physical_code = st.text_input("请输入实物台账编号", placeholder="例如: PA001")

        if st.button("🔍 查询实物资产"):
            if physical_code:
                # 查找实物资产记录
                physical_record = physical_index.get(str(physical_code))

                if physical_record:
                    # 显示实物资产信息
                    with st.expander("📋 实物资产详情", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**资产编号**: {physical_record.get('固定资产编码', '')}")
                            st.info(f"**资产名称**: {physical_record.get('固定资产名称', '')}")
                            st.info(f"**资产类型**: {physical_record.get('固定资产类型', '')}")
                        with col2:
                            physical_value = safe_get_value(physical_record, "资产价值")
                            st.info(f"**资产价值**: ¥{physical_value:,.2f}")
                            st.info(f"**存放部门**: {physical_record.get('存放部门', '')}")
                            st.info(f"**使用状态**: {physical_record.get('使用状态', '')}")

                    # 查找对应的财务资产（支持多对多）
                    financial_codes = physical_to_financial_mapping.get(str(physical_code), [])

                    if financial_codes:
                        st.success(f"✅ 找到 {len(financial_codes)} 个对应的财务资产")

                        # 用于计算总价值
                        total_financial_value = 0
                        valid_financial_count = 0

                        for i, financial_code in enumerate(financial_codes, 1):
                            financial_record = financial_index.get(financial_code)

                            if financial_record:
                                # 显示财务资产信息
                                with st.expander(f"📊 财务资产详情 #{i} - {financial_code}", expanded=True):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"**资产编号**: {financial_record.get('资产编号+序号', '')}")
                                        st.info(f"**资产名称**: {financial_record.get('资产名称', '')}")
                                        st.info(f"**资产分类**: {financial_record.get('资产分类', '')}")
                                    with col2:
                                        financial_value = safe_get_value(financial_record, "资产价值")
                                        st.info(f"**资产价值**: ¥{financial_value:,.2f}")
                                        st.info(f"**所属部门**: {financial_record.get('部门名称', '')}")
                                        st.info(f"**保管人**: {financial_record.get('保管人', '')}")

                                # 累计财务资产价值
                                financial_value = safe_get_value(financial_record, '资产价值')
                                total_financial_value += financial_value
                                valid_financial_count += 1

                            else:
                                st.error(f"❌ 映射的财务资产记录不存在: {financial_code}")

                        # 多对多关系的价值比较
                        if valid_financial_count > 0:
                            st.subheader("💰 价值比较分析")

                            physical_value = safe_get_value(physical_record, '资产价值')

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("实物资产价值", f"¥{physical_value:,.2f}")
                            with col2:
                                st.metric("财务系统总价值", f"¥{total_financial_value:,.2f}")
                            with col3:
                                value_diff = total_financial_value - physical_value
                                st.metric("价值差异", f"¥{value_diff:,.2f}")

                            # 价值差异分析
                            if abs(value_diff) > 0.01:
                                if value_diff > 0:
                                    st.warning(f"⚠️ 财务系统总价值高于实物价值 ¥{value_diff:,.2f}")
                                else:
                                    st.warning(f"⚠️ 实物价值高于财务系统总价值 ¥{abs(value_diff):,.2f}")

                                # 差异率计算
                                if physical_value > 0:
                                    diff_rate = abs(value_diff) / physical_value * 100
                                    st.info(f"📊 差异率: {diff_rate:.2f}%")
                            else:
                                st.success("✅ 实物与财务资产价值一致")

                            # 如果是多个财务资产，显示平均价值
                            if valid_financial_count > 1:
                                avg_financial_value = total_financial_value / valid_financial_count
                                st.info(f"📈 财务资产平均价值: ¥{avg_financial_value:,.2f}")

                        else:
                            st.error("❌ 所有映射的财务资产记录都不存在")

                    else:
                        st.warning("⚠️ 该实物资产未找到对应的财务资产")
                else:
                    st.error("❌ 未找到该实物资产编号对应的资产")
            else:
                st.warning("⚠️ 请输入实物台账编号")

    elif query_type == "按资产名称搜索":
        st.subheader("🔍 资产名称搜索")

        search_term = st.text_input("请输入资产名称关键词", placeholder="例如: 电脑、桌子、空调")

        if search_term:
            # 在财务资产中搜索
            financial_results = [
                record for record in financial_data
                if search_term.lower() in str(record.get('资产名称', '')).lower()
            ]

            # 在实物资产中搜索
            physical_results = [
                record for record in physical_data
                if search_term.lower() in str(record.get('固定资产名称', '')).lower()
            ]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"📊 财务系统搜索结果 ({len(financial_results)}条)")
                if financial_results:
                    for record in financial_results[:10]:  # 限制显示前10条
                        with st.expander(f"💰 {record.get('资产名称', '')} - {record.get('资产编号+序号', '')}"):
                            st.write(f"**资产分类**: {record.get('资产分类', '')}")
                            asset_value = safe_get_value(record, "资产价值")
                            st.write(f"**资产价值**: ¥{asset_value:,.2f}")
                            st.write(f"**所属部门**: {record.get('部门名称', '')}")

                            # 检查是否有对应的实物资产
                            physical_codes = financial_to_physical_mapping.get(str(record.get('资产编号+序号', '')), [])
                            if physical_codes:
                                st.success(f"✅ 已映射到实物资产: {', '.join(physical_codes)}")
                            else:
                                st.warning("⚠️ 未找到对应的实物资产")
                else:
                    st.info("未找到匹配的财务资产")

            with col2:
                st.subheader(f"📋 实物台账搜索结果 ({len(physical_results)}条)")
                if physical_results:
                    for record in physical_results[:10]:  # 限制显示前10条
                        with st.expander(f"📦 {record.get('固定资产名称', '')} - {record.get('固定资产编码', '')}"):
                            st.write(f"**资产类型**: {record.get('固定资产类型', '')}")
                            asset_value = safe_get_value(record, "资产价值")
                            st.write(f"**资产价值**: ¥{asset_value:,.2f}")
                            st.write(f"**存放部门**: {record.get('存放部门', '')}")
                            st.write(f"**使用状态**: {record.get('使用状态', '')}")

                            # 检查是否有对应的财务资产
                            financial_codes = physical_to_financial_mapping.get(str(record.get('固定资产编码', '')), [])
                            if financial_codes:
                                st.success(f"✅ 已映射到财务资产: {', '.join(financial_codes)}")
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

        query_mode = st.radio("查询模式", ["资产编号+序号", "实物台账编号"])

        if batch_input and st.button("开始批量查询"):
            codes = [code.strip() for code in batch_input.split('\n') if code.strip()]

            if codes:
                results = []

                for code in codes:
                    if query_mode == "资产编号+序号":
                        financial_record = financial_index.get(str(code))
                        if financial_record:
                            physical_codes = financial_to_physical_mapping.get(str(code), [])
                            if physical_codes:
                                # 处理多对多关系
                                physical_names = []
                                total_physical_value = 0
                                for pc in physical_codes:
                                    physical_record = physical_index.get(pc)
                                    if physical_record:
                                        physical_names.append(physical_record.get('固定资产名称', ''))
                                        total_physical_value += safe_get_value(physical_record, '资产价值')

                                results.append({
                                    "查询编号": code,
                                    "财务资产名称": financial_record.get('资产名称', ''),
                                    "财务资产价值": safe_get_value(financial_record, '资产价值'),
                                    "对应实物编号": ', '.join(physical_codes),
                                    "实物资产名称": ', '.join(physical_names),
                                    "实物资产价值": total_physical_value,
                                    "状态": "已映射"
                                })
                            else:
                                results.append({
                                    "查询编号": code,
                                    "财务资产名称": financial_record.get('资产名称', ''),
                                    "财务资产价值": safe_get_value(financial_record, '资产价值'),
                                    "对应实物编号": "未映射",
                                    "实物资产名称": "未映射",
                                    "实物资产价值": 0,
                                    "状态": "未映射"
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
                        physical_record = physical_index.get(str(code))
                        if physical_record:
                            financial_codes = physical_to_financial_mapping.get(str(code), [])
                            if financial_codes:
                                # 处理多对多关系
                                financial_names = []
                                total_financial_value = 0
                                for fc in financial_codes:
                                    financial_record = financial_index.get(fc)
                                    if financial_record:
                                        financial_names.append(financial_record.get('资产名称', ''))
                                        total_financial_value += safe_get_value(financial_record, '资产价值')

                                results.append({
                                    "查询编号": code,
                                    "实物资产名称": physical_record.get('固定资产名称', ''),
                                    "实物资产价值": safe_get_value(physical_record, '资产价值'),
                                    "对应财务编号": ', '.join(financial_codes),
                                    "财务资产名称": ', '.join(financial_names),
                                    "财务资产价值": total_financial_value,
                                    "状态": "已映射"
                                })
                            else:
                                results.append({
                                    "查询编号": code,
                                    "实物资产名称": physical_record.get('固定资产名称', ''),
                                    "实物资产价值": safe_get_value(physical_record, '资产价值'),
                                    "对应财务编号": "未映射",
                                    "财务资产名称": "未映射",
                                    "财务资产价值": 0,
                                    "状态": "未映射"
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
                        try:
                            output = io.BytesIO()
                            df.to_excel(output, index=False, engine='openpyxl')
                            output.seek(0)
                            st.download_button(
                                label="下载Excel文件",
                                data=output,
                                file_name=f"批量查询结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        except Exception as e:
                            st.error(f"导出失败: {str(e)}")


def data_statistics_page():
    """数据统计页面"""
    st.header("📊 数据统计分析")

    # ========== 数据加载和验证 ==========
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)

    if not all([financial_data, physical_data, mapping_data]):
        missing = []
        if not financial_data:
            missing.append("财务系统数据")
        if not physical_data:
            missing.append("实物台账数据")
        if not mapping_data:
            missing.append("映射关系数据")
        st.warning(f"⚠️ 请先导入：{', '.join(missing)}")
        return

    # ========== 创建数据索引 ==========
    financial_index = create_data_index(financial_data, "资产编号+序号")
    physical_index = create_data_index(physical_data, "固定资产编码")
    financial_to_physical_mapping, physical_to_financial_mapping = create_mapping_index(mapping_data)

    # ========== 预计算统计数据 ==========
    # 计算匹配数量
    matched_financial = len(
        [f for f in financial_data if str(f.get("资产编号+序号", "")).strip() in financial_to_physical_mapping])
    matched_physical = len(
        [p for p in physical_data if str(p.get("固定资产编码", "")).strip() in physical_to_financial_mapping])

    # 计算价值
    financial_total_value = sum(safe_get_value(f, "资产价值") for f in financial_data)

    # 处理实物资产价值计算（去重和核算筛选）
    physical_df = pd.DataFrame(physical_data)
    if len(physical_df) > 0 and "固定资产编码" in physical_df.columns:
        if "是否核算" in physical_df.columns:
            accounting_mask = physical_df["是否核算"].astype(str).str.strip().isin(
                ["是", "Y", "y", "Yes", "YES", "1", "True", "true"])
            physical_df_accounting = physical_df[accounting_mask]
            non_accounting_count = len(physical_df) - len(physical_df_accounting)
            physical_df_deduped = physical_df_accounting.drop_duplicates(subset=['固定资产编码'], keep='first')
            physical_duplicate_count = len(physical_df_accounting) - len(physical_df_deduped)
        else:
            physical_df_deduped = physical_df.drop_duplicates(subset=['固定资产编码'], keep='first')
            physical_duplicate_count = len(physical_df) - len(physical_df_deduped)
            non_accounting_count = 0

        physical_total_value = sum(
            safe_get_value(row.to_dict(), "固定资产原值") for _, row in physical_df_deduped.iterrows())

        # 保存统计信息
        st.session_state['physical_duplicate_count'] = physical_duplicate_count
        st.session_state['physical_deduped_count'] = len(physical_df_deduped)
        st.session_state['physical_original_count'] = len(physical_df)
    else:
        physical_total_value = sum(safe_get_value(p, "资产价值") for p in physical_data)
        physical_duplicate_count = 0
        non_accounting_count = 0
        st.session_state['physical_duplicate_count'] = 0
        st.session_state['physical_deduped_count'] = len(physical_data)
        st.session_state['physical_original_count'] = len(physical_data)

    # ========== 主要内容区域 ==========
    tab_summary, tab_analysis, tab_charts = st.tabs(["📊 统计概览", "🔍 差异分析", "📈 可视化分析"])

    # ========== Tab 1: 统计概览 ==========
    with tab_summary:
        # 基础统计
        st.subheader("📋 基础统计信息")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("财务资产总数", f"{len(financial_data):,}")
            st.caption(f"已匹配: {matched_financial:,}")

        with col2:
            deduped_count = st.session_state.get('physical_deduped_count', len(physical_data))
            original_count = st.session_state.get('physical_original_count', len(physical_data))
            duplicate_count = st.session_state.get('physical_duplicate_count', 0)

            st.metric("实物资产总数", f"{deduped_count:,}")
            if duplicate_count > 0:
                st.caption(f"原始: {original_count:,} | 去重: {duplicate_count}")
            else:
                st.caption(f"已匹配: {matched_physical:,}")

        with col3:
            st.metric("映射关系总数", f"{len(mapping_data):,}")

        with col4:
            overall_match_rate = (
                        (matched_financial + matched_physical) / (len(financial_data) + len(physical_data)) * 100) if (
                                                                                                                                  len(financial_data) + len(
                                                                                                                              physical_data)) > 0 else 0
            st.metric("整体匹配率", f"{overall_match_rate:.1f}%")

        st.divider()

        # 匹配率统计
        st.subheader("🎯 匹配率统计")
        col1, col2 = st.columns(2)

        with col1:
            financial_match_rate = (matched_financial / len(financial_data) * 100) if financial_data else 0
            st.metric("财务资产匹配率", f"{financial_match_rate:.1f}%")

            progress_val = financial_match_rate / 100
            st.progress(progress_val)

            unmatched_financial = len(financial_data) - matched_financial
            st.caption(f"未匹配: {unmatched_financial:,} 项")

        with col2:
            physical_match_rate = (matched_physical / len(physical_data) * 100) if physical_data else 0
            st.metric("实物资产匹配率", f"{physical_match_rate:.1f}%")

            progress_val = physical_match_rate / 100
            st.progress(progress_val)

            unmatched_physical = len(physical_data) - matched_physical
            st.caption(f"未匹配: {unmatched_physical:,} 项")

        st.divider()

        # 价值统计
        st.subheader("💰 价值统计")

        # 数据处理说明
        if non_accounting_count > 0 or physical_duplicate_count > 0:
            with st.expander("ℹ️ 数据处理说明", expanded=False):
                if non_accounting_count > 0:
                    st.info(f"💡 已排除 {non_accounting_count:,} 条非核算资产")
                if physical_duplicate_count > 0:
                    st.info(f"💡 已去重 {physical_duplicate_count:,} 条重复记录")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("财务资产总价值", f"¥{financial_total_value:,.2f}")

        with col2:
            st.metric("实物资产总价值", f"¥{physical_total_value:,.2f}")

        with col3:
            total_diff = financial_total_value - physical_total_value
            diff_color = "normal"
            if abs(total_diff) > 100000:
                diff_color = "inverse"

            st.metric("总价值差异", f"¥{total_diff:,.2f}", delta_color=diff_color)

            if abs(total_diff) > 100000:
                st.caption("🔴 差异较大，需要关注")
            elif abs(total_diff) > 10000:
                st.caption("🟡 存在差异")
            else:
                st.caption("🟢 差异较小")

    # ========== Tab 2: 差异分析 ==========
    with tab_analysis:
        st.subheader("🔍 价值差异详细分析")

        # 数据验证
        if not all([financial_data, physical_data, mapping_data]):
            st.warning("⚠️ 缺少必要数据，无法进行差异分析")
            return

        # 计算差异数据
        with st.spinner("正在计算差异数据..."):
            # 创建匹配集合
            matched_financial_codes = set()
            matched_physical_codes = set()

            # 遍历映射数据获取匹配的编码
            for mapping_record in mapping_data:
                financial_code = str(mapping_record.get("资产编号+序号", "")).strip()
                physical_code = str(mapping_record.get("固定资产编码", "")).strip()

                if financial_code and physical_code:
                    if financial_code in financial_index and physical_code in physical_index:
                        matched_financial_codes.add(financial_code)
                        matched_physical_codes.add(physical_code)

            # 分类资产数据
            matched_financial = [f for f in financial_data
                                 if str(f.get("资产编号+序号", "")).strip() in matched_financial_codes]
            matched_physical = [p for p in physical_data
                                if str(p.get("固定资产编码", "")).strip() in matched_physical_codes]

            unmatched_financial = [f for f in financial_data
                                   if str(f.get("资产编号+序号", "")).strip() not in matched_financial_codes]
            unmatched_physical = [p for p in physical_data
                                  if str(p.get("固定资产编码", "")).strip() not in matched_physical_codes]

            # 计算汇总数据
            def calculate_totals(data_list, is_financial=True):
                if is_financial:
                    original_key = "资产价值"
                    depreciation_key = "累计折旧"
                    net_key = "净额"
                else:
                    original_key = "固定资产原值"
                    depreciation_key = "累计折旧"
                    net_key = None

                total_original = sum(safe_get_value(item, original_key, 0) for item in data_list)
                total_depreciation = sum(safe_get_value(item, depreciation_key, 0) for item in data_list)

                if is_financial:
                    total_net = sum(safe_get_value(item, net_key, 0) for item in data_list)
                    if total_net == 0:  # 如果净额为0，用原值-累计折旧计算
                        total_net = max(0, total_original - total_depreciation)
                else:
                    total_net = max(0, total_original - total_depreciation)

                return {
                    'original': total_original,
                    'depreciation': total_depreciation,
                    'net': total_net,
                    'count': len(data_list)
                }

            # 计算各类汇总
            total_financial = calculate_totals(financial_data, True)
            total_physical = calculate_totals(physical_data, False)
            matched_financial_totals = calculate_totals(matched_financial, True)
            matched_physical_totals = calculate_totals(matched_physical, False)
            unmatched_financial_totals = calculate_totals(unmatched_financial, True)
            unmatched_physical_totals = calculate_totals(unmatched_physical, False)

        # ========== 1. 总体差异对比 ==========
        with tab_analysis:
            st.subheader("🔍 价值差异详细分析")

            # 数据验证
            if not all([financial_data, physical_data, mapping_data]):
                st.warning("⚠️ 缺少必要数据，无法进行差异分析")
            else:
                # 计算差异数据
                with st.spinner("正在计算差异数据..."):
                    # 创建匹配集合
                    matched_financial_codes = set()
                    matched_physical_codes = set()

                    # 遍历映射数据获取匹配的编码
                    for mapping_record in mapping_data:
                        financial_code = str(mapping_record.get("资产编号+序号", "")).strip()
                        physical_code = str(mapping_record.get("固定资产编码", "")).strip()

                        if financial_code and physical_code:
                            if financial_code in financial_index and physical_code in physical_index:
                                matched_financial_codes.add(financial_code)
                                matched_physical_codes.add(physical_code)

                    # 分类资产数据
                    matched_financial = [f for f in financial_data
                                         if str(f.get("资产编号+序号", "")).strip() in matched_financial_codes]
                    matched_physical = [p for p in physical_data
                                        if str(p.get("固定资产编码", "")).strip() in matched_physical_codes]

                    unmatched_financial = [f for f in financial_data
                                           if str(f.get("资产编号+序号", "")).strip() not in matched_financial_codes]
                    unmatched_physical = [p for p in physical_data
                                          if str(p.get("固定资产编码", "")).strip() not in matched_physical_codes]

                    # 定义匹配数量变量
                    matched_count = len(matched_financial)

                    # 计算汇总数据
                    def calculate_totals(data_list, is_financial=True):
                        if is_financial:
                            original_key = "资产价值"
                            depreciation_key = "累计折旧"
                            net_key = "净额"
                        else:
                            original_key = "固定资产原值"
                            depreciation_key = "累计折旧"
                            net_key = None

                        total_original = sum(safe_get_value(item, original_key, 0) for item in data_list)
                        total_depreciation = sum(safe_get_value(item, depreciation_key, 0) for item in data_list)

                        if is_financial:
                            total_net = sum(safe_get_value(item, net_key, 0) for item in data_list)
                            if total_net == 0:  # 如果净额为0，用原值-累计折旧计算
                                total_net = max(0, total_original - total_depreciation)
                        else:
                            total_net = max(0, total_original - total_depreciation)

                        return {
                            'original': total_original,
                            'depreciation': total_depreciation,
                            'net': total_net,
                            'count': len(data_list)
                        }

                    # 计算各类汇总
                    total_financial = calculate_totals(financial_data, True)
                    total_physical = calculate_totals(physical_data, False)
                    matched_financial_totals = calculate_totals(matched_financial, True)
                    matched_physical_totals = calculate_totals(matched_physical, False)
                    unmatched_financial_totals = calculate_totals(unmatched_financial, True)
                    unmatched_physical_totals = calculate_totals(unmatched_physical, False)

                # ========== 1. 总体差异对比（横向展示） ==========
                st.markdown("### 💰 总体差异对比")

                # 创建总体对比表格
                total_comparison_data = {
                    "项目": ["资产原值", "累计折旧", "资产净额"],
                    "财务系统": [
                        f"¥{total_financial['original']:,.2f}",
                        f"¥{total_financial['depreciation']:,.2f}",
                        f"¥{total_financial['net']:,.2f}"
                    ],
                    "实物系统": [
                        f"¥{total_physical['original']:,.2f}",
                        f"¥{total_physical['depreciation']:,.2f}",
                        f"¥{total_physical['net']:,.2f}"
                    ],
                    "差异金额": [
                        f"¥{total_financial['original'] - total_physical['original']:,.2f}",
                        f"¥{total_financial['depreciation'] - total_physical['depreciation']:,.2f}",
                        f"¥{total_financial['net'] - total_physical['net']:,.2f}"
                    ]
                }

                total_comparison_df = pd.DataFrame(total_comparison_data)
                st.dataframe(total_comparison_df, use_container_width=True, hide_index=True)

                # 总体差异状态
                total_original_diff = total_financial['original'] - total_physical['original']
                total_depreciation_diff = total_financial['depreciation'] - total_physical['depreciation']
                total_net_diff = total_financial['net'] - total_physical['net']

                def get_status_emoji(diff_value):
                    if abs(diff_value) > 1000000:
                        return "🔴 重大差异"
                    elif abs(diff_value) > 100000:
                        return "🟡 中等差异"
                    elif abs(diff_value) > 1000:
                        return "🟠 轻微差异"
                    else:
                        return "🟢 基本一致"

                col_status1, col_status2, col_status3 = st.columns(3)
                with col_status1:
                    st.info(f"**原值差异状态**: {get_status_emoji(total_original_diff)}")
                with col_status2:
                    st.info(f"**折旧差异状态**: {get_status_emoji(total_depreciation_diff)}")
                with col_status3:
                    st.info(f"**净额差异状态**: {get_status_emoji(total_net_diff)}")

                st.divider()

                # ========== 2. 已匹配资产分析（横向展示） ==========
                st.markdown("### 🎯 已匹配资产分析")

                # 已匹配差异计算
                matched_original_diff = matched_financial_totals['original'] - matched_physical_totals['original']
                matched_depreciation_diff = matched_financial_totals['depreciation'] - matched_physical_totals[
                    'depreciation']
                matched_net_diff = matched_financial_totals['net'] - matched_physical_totals['net']

                # 已匹配对比表格
                matched_comparison_data = {
                    "项目": ["资产原值", "累计折旧", "资产净额"],
                    "财务系统": [
                        f"¥{matched_financial_totals['original']:,.2f}",
                        f"¥{matched_financial_totals['depreciation']:,.2f}",
                        f"¥{matched_financial_totals['net']:,.2f}"
                    ],
                    "实物系统": [
                        f"¥{matched_physical_totals['original']:,.2f}",
                        f"¥{matched_physical_totals['depreciation']:,.2f}",
                        f"¥{matched_physical_totals['net']:,.2f}"
                    ],
                    "差异金额": [
                        f"¥{matched_original_diff:,.2f}",
                        f"¥{matched_depreciation_diff:,.2f}",
                        f"¥{matched_net_diff:,.2f}"
                    ],
                    "占总资产比例": [
                        f"{(matched_financial_totals['original'] / total_financial['original'] * 100):.1f}%" if
                        total_financial['original'] > 0 else "0%",
                        f"{(matched_financial_totals['depreciation'] / total_financial['depreciation'] * 100):.1f}%" if
                        total_financial['depreciation'] > 0 else "0%",
                        f"{(matched_financial_totals['net'] / total_financial['net'] * 100):.1f}%" if total_financial[
                                                                                                          'net'] > 0 else "0%"
                    ]
                }

                matched_comparison_df = pd.DataFrame(matched_comparison_data)
                st.dataframe(matched_comparison_df, use_container_width=True, hide_index=True)

                # 已匹配资产基本信息
                col_matched1, col_matched2, col_matched3 = st.columns(3)
                with col_matched1:
                    st.metric("已匹配资产数量", f"{matched_financial_totals['count']:,} 项")
                with col_matched2:
                    overall_match_rate = (matched_count / len(financial_data) * 100) if financial_data else 0
                    st.metric("总体匹配率", f"{overall_match_rate:.1f}%")
                with col_matched3:
                    st.metric("已匹配资产占比",
                              f"{(matched_financial_totals['original'] / total_financial['original'] * 100):.1f}%" if
                              total_financial['original'] > 0 else "0%")

                st.divider()

                # ========== 3. 未匹配资产分析（横向展示） ==========
                st.markdown("### ⚠️ 未匹配资产分析")

                # 未匹配对比表格
                unmatched_comparison_data = {
                    "资产类型": ["未匹配财务资产", "未匹配实物资产"],
                    "资产原值": [
                        f"¥{unmatched_financial_totals['original']:,.2f}",
                        f"¥{unmatched_physical_totals['original']:,.2f}"
                    ],
                    "累计折旧": [
                        f"¥{unmatched_financial_totals['depreciation']:,.2f}",
                        f"¥{unmatched_physical_totals['depreciation']:,.2f}"
                    ],
                    "资产净额": [
                        f"¥{unmatched_financial_totals['net']:,.2f}",
                        f"¥{unmatched_physical_totals['net']:,.2f}"
                    ],
                    "资产数量": [
                        f"{unmatched_financial_totals['count']:,} 项",
                        f"{unmatched_physical_totals['count']:,} 项"
                    ],
                    "占比": [
                        f"{(unmatched_financial_totals['original'] / total_financial['original'] * 100):.1f}%" if
                        total_financial['original'] > 0 else "0%",
                        f"{(unmatched_physical_totals['original'] / total_physical['original'] * 100):.1f}%" if
                        total_physical['original'] > 0 else "0%"
                    ]
                }

                unmatched_comparison_df = pd.DataFrame(unmatched_comparison_data)
                st.dataframe(unmatched_comparison_df, use_container_width=True, hide_index=True)

                # 未匹配资产差异分析
                unmatched_original_diff = unmatched_financial_totals['original'] - unmatched_physical_totals['original']
                unmatched_depreciation_diff = unmatched_financial_totals['depreciation'] - unmatched_physical_totals[
                    'depreciation']
                unmatched_net_diff = unmatched_financial_totals['net'] - unmatched_physical_totals['net']

                st.markdown("#### 📊 未匹配资产差异")
                col_unmatched1, col_unmatched2, col_unmatched3 = st.columns(3)

                with col_unmatched1:
                    st.metric("原值差异", f"¥{unmatched_original_diff:,.2f}",
                              help="财务未匹配 - 实物未匹配")
                with col_unmatched2:
                    st.metric("折旧差异", f"¥{unmatched_depreciation_diff:,.2f}",
                              help="财务未匹配 - 实物未匹配")
                with col_unmatched3:
                    st.metric("净额差异", f"¥{unmatched_net_diff:,.2f}",
                              help="财务未匹配 - 实物未匹配")

                st.divider()

                # ========== 4. 可视化图表 ==========
                st.markdown("### 📊 差异可视化分析")

                # 创建图表数据
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("#### 📈 匹配状态分布")

                    # 准备匹配状态数据
                    financial_match_data = pd.DataFrame({
                        "状态": ["已匹配", "未匹配"],
                        "数量": [matched_count, len(unmatched_financial)],
                        "金额": [matched_financial_totals['original'], unmatched_financial_totals['original']]
                    })

                    physical_match_data = pd.DataFrame({
                        "状态": ["已匹配", "未匹配"],
                        "数量": [len(matched_physical), len(unmatched_physical)],
                        "金额": [matched_physical_totals['original'], unmatched_physical_totals['original']]
                    })

                    # 尝试使用plotly绘图
                    try:
                        import plotly.express as px
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots

                        # 创建子图
                        fig = make_subplots(
                            rows=1, cols=2,
                            subplot_titles=('财务资产匹配状态', '实物资产匹配状态'),
                            specs=[[{"type": "pie"}, {"type": "pie"}]]
                        )

                        # 财务资产饼图
                        fig.add_trace(
                            go.Pie(
                                labels=financial_match_data["状态"],
                                values=financial_match_data["金额"],
                                name="财务资产",
                                marker_colors=['#2E8B57', '#DC143C']
                            ),
                            row=1, col=1
                        )

                        # 实物资产饼图
                        fig.add_trace(
                            go.Pie(
                                labels=physical_match_data["状态"],
                                values=physical_match_data["金额"],
                                name="实物资产",
                                marker_colors=['#4682B4', '#FF6347']
                            ),
                            row=1, col=2
                        )

                        fig.update_layout(height=400, showlegend=True)
                        st.plotly_chart(fig, use_container_width=True)

                    except ImportError:
                        # 使用streamlit原生图表
                        st.write("**财务资产匹配状态**")
                        fin_chart_data = pd.DataFrame({
                            '已匹配': [matched_financial_totals['original']],
                            '未匹配': [unmatched_financial_totals['original']]
                        })
                        st.bar_chart(fin_chart_data)

                        st.write("**实物资产匹配状态**")
                        phy_chart_data = pd.DataFrame({
                            '已匹配': [matched_physical_totals['original']],
                            '未匹配': [unmatched_physical_totals['original']]
                        })
                        st.bar_chart(phy_chart_data)

                with chart_col2:
                    st.markdown("#### 📊 差异对比分析")

                    # 准备差异对比数据
                    diff_comparison_data = pd.DataFrame({
                        "差异类型": ["资产原值", "累计折旧", "资产净额"],
                        "总体差异": [total_original_diff, total_depreciation_diff, total_net_diff],
                        "已匹配差异": [matched_original_diff, matched_depreciation_diff, matched_net_diff],
                        "未匹配差异": [unmatched_original_diff, unmatched_depreciation_diff, unmatched_net_diff]
                    })

                    try:
                        # 差异对比柱状图
                        fig_diff = px.bar(
                            diff_comparison_data,
                            x="差异类型",
                            y=["总体差异", "已匹配差异", "未匹配差异"],
                            title="各类差异对比分析",
                            barmode="group",
                            color_discrete_map={
                                "总体差异": "#FF6B6B",
                                "已匹配差异": "#4ECDC4",
                                "未匹配差异": "#45B7D1"
                            }
                        )
                        fig_diff.update_layout(
                            xaxis_title="差异类型",
                            yaxis_title="差异金额（元）",
                            height=400
                        )
                        st.plotly_chart(fig_diff, use_container_width=True)

                    except ImportError:
                        # 使用streamlit原生图表
                        chart_data = diff_comparison_data.set_index("差异类型")[
                            ["总体差异", "已匹配差异", "未匹配差异"]]
                        st.bar_chart(chart_data)

                # 关键指标汇总（横向展示）
                st.markdown("#### 📊 关键指标汇总")

                key_metrics_data = {
                    "指标": ["总体匹配率", "总价值差异", "已匹配项目", "待处理项目", "匹配资产占比"],
                    "数值": [
                        f"{overall_match_rate:.1f}%",
                        f"¥{abs(total_original_diff):,.0f}",
                        f"{matched_count:,} 项",
                        f"{unmatched_financial_totals['count'] + unmatched_physical_totals['count']:,} 项",
                        f"{(matched_financial_totals['original'] / total_financial['original'] * 100):.1f}%" if
                        total_financial['original'] > 0 else "0%"
                    ]
                }

                key_metrics_df = pd.DataFrame(key_metrics_data)
                st.dataframe(key_metrics_df, use_container_width=True, hide_index=True)

                # 导出功能
                st.divider()
                if st.button("📥 导出差异分析报告", key="export_analysis"):
                    # 创建导出数据
                    export_data = []

                    # 总体对比数据
                    export_data.extend([
                        {"分类": "总体对比", "项目": "财务资产原值", "金额": total_financial['original']},
                        {"分类": "总体对比", "项目": "实物资产原值", "金额": total_physical['original']},
                        {"分类": "总体对比", "项目": "原值差异", "金额": total_original_diff},
                        {"分类": "总体对比", "项目": "财务累计折旧", "金额": total_financial['depreciation']},
                        {"分类": "总体对比", "项目": "实物累计折旧", "金额": total_physical['depreciation']},
                        {"分类": "总体对比", "项目": "折旧差异", "金额": total_depreciation_diff},
                        {"分类": "总体对比", "项目": "财务资产净额", "金额": total_financial['net']},
                        {"分类": "总体对比", "项目": "实物资产净额", "金额": total_physical['net']},
                        {"分类": "总体对比", "项目": "净额差异", "金额": total_net_diff}
                    ])

                    # 已匹配资产数据
                    export_data.extend([
                        {"分类": "已匹配资产", "项目": "财务资产原值", "金额": matched_financial_totals['original']},
                        {"分类": "已匹配资产", "项目": "实物资产原值", "金额": matched_physical_totals['original']},
                        {"分类": "已匹配资产", "项目": "原值差异", "金额": matched_original_diff},
                        {"分类": "已匹配资产", "项目": "财务累计折旧",
                         "金额": matched_financial_totals['depreciation']},
                        {"分类": "已匹配资产", "项目": "实物累计折旧", "金额": matched_physical_totals['depreciation']},
                        {"分类": "已匹配资产", "项目": "折旧差异", "金额": matched_depreciation_diff},
                        {"分类": "已匹配资产", "项目": "财务资产净额", "金额": matched_financial_totals['net']},
                        {"分类": "已匹配资产", "项目": "实物资产净额", "金额": matched_physical_totals['net']},
                        {"分类": "已匹配资产", "项目": "净额差异", "金额": matched_net_diff},
                        {"分类": "已匹配资产", "项目": "匹配数量", "金额": matched_financial_totals['count']}
                    ])

                    # 未匹配资产数据
                    export_data.extend([
                        {"分类": "未匹配财务资产", "项目": "资产原值", "金额": unmatched_financial_totals['original']},
                        {"分类": "未匹配财务资产", "项目": "累计折旧",
                         "金额": unmatched_financial_totals['depreciation']},
                        {"分类": "未匹配财务资产", "项目": "资产净额", "金额": unmatched_financial_totals['net']},
                        {"分类": "未匹配财务资产", "项目": "数量", "金额": unmatched_financial_totals['count']},
                        {"分类": "未匹配实物资产", "项目": "资产原值", "金额": unmatched_physical_totals['original']},
                        {"分类": "未匹配实物资产", "项目": "累计折旧",
                         "金额": unmatched_physical_totals['depreciation']},
                        {"分类": "未匹配实物资产", "项目": "资产净额", "金额": unmatched_physical_totals['net']},
                        {"分类": "未匹配实物资产", "项目": "数量", "金额": unmatched_physical_totals['count']}
                    ])

                    export_df = pd.DataFrame(export_data)
                    csv = export_df.to_csv(index=False, encoding='utf-8-sig')

                    st.download_button(
                        label="💾 下载差异分析报告 CSV",
                        data=csv,
                        file_name=f"资产差异分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    st.success("✅ 报告已准备就绪，点击上方按钮下载")

    # ========== Tab 3: 可视化分析 ==========
    with tab_charts:
        st.subheader("📈 可视化分析")

        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["💰 价值分布", "🎯 匹配状态", "🏢 部门分析"])

        with chart_tab1:
            # 价值对比图
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                # 总价值对比
                try:
                    import plotly.express as px
                    fig_pie = px.pie(
                        values=[financial_total_value, physical_total_value],
                        names=["财务系统", "实物系统"],
                        title="总价值分布对比",
                        color_discrete_sequence=['#FF6B6B', '#4ECDC4']
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                except:
                    # 使用streamlit原生图表
                    chart_data = pd.DataFrame({
                        "财务系统": [financial_total_value],
                        "实物系统": [physical_total_value]
                    })
                    st.bar_chart(chart_data)

            with col_chart2:
                # 匹配vs未匹配价值对比
                unmatched_financial = [f for f in financial_data if
                                       str(f.get("资产编号+序号", "")).strip() not in financial_to_physical_mapping]
                unmatched_physical = [p for p in physical_data if
                                      str(p.get("固定资产编码", "")).strip() not in physical_to_financial_mapping]

                unmatched_financial_value = sum(safe_get_value(f, "资产价值") for f in unmatched_financial)
                matched_financial_value = financial_total_value - unmatched_financial_value

                # 实物资产去重计算
                if unmatched_physical:
                    unmatched_physical_df = pd.DataFrame(unmatched_physical)
                    if "固定资产编码" in unmatched_physical_df.columns:
                        unmatched_physical_df_deduped = unmatched_physical_df.drop_duplicates(
                            subset=['固定资产编码'], keep='first')
                        unmatched_physical_value = sum(
                            safe_get_value(row.to_dict(), "固定资产原值")
                            for _, row in unmatched_physical_df_deduped.iterrows())
                    else:
                        unmatched_physical_value = sum(safe_get_value(p, "固定资产原值") for p in unmatched_physical)
                else:
                    unmatched_physical_value = 0

                matched_physical_value = physical_total_value - unmatched_physical_value

                try:
                    match_status_data = pd.DataFrame({
                        "状态": ["已匹配财务", "未匹配财务", "已匹配实物", "未匹配实物"],
                        "价值": [matched_financial_value, unmatched_financial_value,
                                 matched_physical_value, unmatched_physical_value]
                    })

                    fig_bar = px.bar(
                        match_status_data,
                        x="状态",
                        y="价值",
                        title="匹配状态价值分布",
                        color="状态",
                        color_discrete_sequence=['#95E1D3', '#F38BA8', '#A8E6CF', '#FFB3BA']
                    )
                    fig_bar.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_bar, use_container_width=True)
                except:
                    st.bar_chart(match_status_data.set_index("状态"))

        with chart_tab2:
            # 匹配状态分布
            col_dist1, col_dist2 = st.columns(2)

            with col_dist1:
                # 财务资产匹配状态
                try:
                    financial_match_data = pd.DataFrame({
                        "状态": ["已匹配", "未匹配"],
                        "数量": [matched_financial, len(financial_data) - matched_financial]
                    })

                    fig_financial = px.pie(
                        financial_match_data,
                        values="数量",
                        names="状态",
                        title="财务资产匹配状态",
                        color_discrete_sequence=['#A8E6CF', '#FFB3BA']
                    )
                    fig_financial.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_financial, use_container_width=True)
                except:
                    st.write("**财务资产匹配状态**")
                    st.dataframe(financial_match_data)

            with col_dist2:
                # 实物资产匹配状态
                try:
                    physical_match_data = pd.DataFrame({
                        "状态": ["已匹配", "未匹配"],
                        "数量": [matched_physical, len(physical_data) - matched_physical]
                    })

                    fig_physical = px.pie(
                        physical_match_data,
                        values="数量",
                        names="状态",
                        title="实物资产匹配状态",
                        color_discrete_sequence=['#95E1D3', '#F38BA8']
                    )
                    fig_physical.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_physical, use_container_width=True)
                except:
                    st.write("**实物资产匹配状态**")
                    st.dataframe(physical_match_data)

        with chart_tab3:
            # 部门分析图表
            # 计算部门统计
            financial_dept_stats = {}
            for f in financial_data:
                dept = f.get("部门名称", "未知部门")
                if dept not in financial_dept_stats:
                    financial_dept_stats[dept] = {"count": 0, "value": 0, "matched": 0}
                financial_dept_stats[dept]["count"] += 1
                financial_dept_stats[dept]["value"] += safe_get_value(f, "资产价值")

                financial_code = str(f.get("资产编号+序号", "")).strip()
                if financial_code in financial_to_physical_mapping:
                    financial_dept_stats[dept]["matched"] += 1

            # 部门价值对比
            dept_chart_data = []
            for dept, stats in financial_dept_stats.items():
                dept_chart_data.append({
                    "部门": dept,
                    "总价值": stats["value"],
                    "资产数量": stats["count"],
                    "匹配率": (stats["matched"] / stats["count"] * 100) if stats["count"] > 0 else 0
                })

            if dept_chart_data:
                dept_df = pd.DataFrame(dept_chart_data)
                dept_df = dept_df.sort_values("总价值", ascending=False).head(10)  # 显示前10个部门

                col_dept1, col_dept2 = st.columns(2)

                with col_dept1:
                    try:
                        fig_dept_value = px.bar(
                            dept_df,
                            x="部门",
                            y="总价值",
                            title="各部门资产价值分布（前10）",
                            color="总价值",
                            color_continuous_scale="Viridis"
                        )
                        fig_dept_value.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_dept_value, use_container_width=True)
                    except:
                        st.write("**各部门资产价值分布**")
                        st.bar_chart(dept_df.set_index("部门")["总价值"])

                with col_dept2:
                    try:
                        fig_dept_match = px.scatter(
                            dept_df,
                            x="资产数量",
                            y="匹配率",
                            size="总价值",
                            hover_data=["部门"],
                            title="部门匹配率 vs 资产数量",
                            color="匹配率",
                            color_continuous_scale="RdYlGn"
                        )
                        st.plotly_chart(fig_dept_match, use_container_width=True)
                    except:
                        st.write("**部门匹配率分析**")
                        st.dataframe(dept_df[["部门", "资产数量", "匹配率"]])

                # 部门详细统计表
                st.markdown("#### 📊 部门统计详情")
                dept_detail_df = dept_df.copy()
                dept_detail_df["总价值"] = dept_detail_df["总价值"].apply(lambda x: f"¥{x:,.2f}")
                dept_detail_df["匹配率"] = dept_detail_df["匹配率"].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    dept_detail_df[["部门", "资产数量", "总价值", "匹配率"]],
                    use_container_width=True
                )

                # 部门匹配率分析
                st.markdown("#### 🎯 部门匹配率分析")

                high_match_depts = dept_df[dept_df["匹配率"] >= 80]
                medium_match_depts = dept_df[(dept_df["匹配率"] >= 50) & (dept_df["匹配率"] < 80)]
                low_match_depts = dept_df[dept_df["匹配率"] < 50]

                match_analysis_col1, match_analysis_col2, match_analysis_col3 = st.columns(3)

                with match_analysis_col1:
                    st.metric("高匹配率部门 (≥80%)", f"{len(high_match_depts)} 个")
                    if len(high_match_depts) > 0:
                        st.caption("✅ 匹配良好")

                with match_analysis_col2:
                    st.metric("中等匹配率部门 (50-80%)", f"{len(medium_match_depts)} 个")
                    if len(medium_match_depts) > 0:
                        st.caption("⚠️ 需要改进")

                with match_analysis_col3:
                    st.metric("低匹配率部门 (<50%)", f"{len(low_match_depts)} 个")
                    if len(low_match_depts) > 0:
                        st.caption("🔴 急需关注")

                # 显示需要关注的部门
                if len(low_match_depts) > 0:
                    with st.expander("🔍 低匹配率部门详情", expanded=False):
                        low_match_display = low_match_depts[["部门", "资产数量", "匹配率"]].copy()
                        low_match_display["匹配率"] = low_match_display["匹配率"].apply(lambda x: f"{x:.1f}%")
                        st.dataframe(low_match_display, use_container_width=True)
                        st.warning("💡 建议优先处理这些部门的资产匹配工作")

            else:
                st.info("暂无部门数据可供分析")
        # ========== 页面底部汇总信息 ==========
    st.divider()
    st.markdown("### 📋 数据统计汇总")

    # 创建汇总信息
    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown("#### 📊 数据概况")
        st.write(f"• 财务资产总数：**{len(financial_data):,}** 项")
        st.write(
            f"• 实物资产总数：**{st.session_state.get('physical_deduped_count', len(physical_data)):,}** 项（去重后）")
        st.write(f"• 映射关系总数：**{len(mapping_data):,}** 条")
        st.write(f"• 整体匹配率：**{overall_match_rate:.1f}%**")

    with summary_col2:
        st.markdown("#### 💰 价值概况")
        st.write(f"• 财务资产总价值：**¥{financial_total_value:,.2f}**")
        st.write(f"• 实物资产总价值：**¥{physical_total_value:,.2f}**")
        st.write(f"• 总价值差异：**¥{total_diff:,.2f}**")

        if matched_count > 0:
            st.write(f"• 已匹配项目：**{matched_count:,}** 项")

    # 数据处理说明
    if non_accounting_count > 0 or physical_duplicate_count > 0:
        st.markdown("#### ℹ️ 数据处理说明")
        if non_accounting_count > 0:
            st.info(f"📌 已排除 **{non_accounting_count:,}** 条非核算资产")
        if physical_duplicate_count > 0:
            st.info(f"📌 已去重 **{physical_duplicate_count:,}** 条重复记录")
    # 最后更新时间
    st.caption(f"📅 统计生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def all_data_view_page():
    """查看全部对应关系页面"""
    st.header("📋 全部资产对应关系")

    # 加载数据
    with st.spinner("加载数据中..."):
        financial_data = load_data(FINANCIAL_DATA_FILE)
        physical_data = load_data(PHYSICAL_DATA_FILE)
        mapping_data = load_data(MAPPING_DATA_FILE)

    # 修改：检查所有三个数据源
    if not all([financial_data, physical_data, mapping_data]):
        missing = []
        if not financial_data:
            missing.append("财务系统数据")
        if not physical_data:
            missing.append("实物台账数据")
        if not mapping_data:
            missing.append("映射关系数据")
        st.warning(f"⚠️ 请先导入：{', '.join(missing)}")
        return
        # 🆕 添加数据格式检查
        if financial_data:
            financial_df_check = pd.DataFrame(financial_data)
            if "资产编号+序号" not in financial_df_check.columns:
                st.error("❌ 财务数据格式错误：缺少'资产编号+序号'列")
                st.write("财务数据当前列名：", list(financial_df_check.columns))
                return

        if physical_data:
            physical_df_check = pd.DataFrame(physical_data)
            if "固定资产编码" not in physical_df_check.columns:
                st.error("❌ 实物数据格式错误：缺少'固定资产编码'列")
                st.write("实物数据当前列名：", list(physical_df_check.columns))
                return
    # 创建索引
    financial_index = create_data_index(financial_data, "资产编号+序号")
    physical_index = create_data_index(physical_data, "固定资产编码")
    financial_to_physical_mapping, physical_to_financial_mapping = create_mapping_index(mapping_data)

    # 选择查看模式
    view_mode = st.selectbox("选择查看模式",
                             ["对应关系汇总", "财务系统明细", "实物台账明细", "未匹配资产"])

    if view_mode == "对应关系汇总":
        st.subheader("🔗 完整对应关系汇总")

        # 构建汇总数据 - 修复：处理多对多关系
        mapping_summary = []

        # 用集合记录已处理的映射关系，避免重复
        processed_pairs = set()

        for mapping_record in mapping_data:
            financial_code = str(mapping_record.get("资产编号+序号", "")).strip()
            physical_code = str(mapping_record.get("固定资产编码", "")).strip()

            # 创建唯一标识符避免重复处理
            pair_key = f"{financial_code}|{physical_code}"
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)

            if financial_code and physical_code:
                financial_record = financial_index.get(financial_code)
                physical_record = physical_index.get(physical_code)

                if financial_record and physical_record:
                    financial_value = safe_get_value(financial_record, "资产价值")
                    physical_value = safe_get_value(physical_record, "资产价值")

                    mapping_summary.append({
                        "资产编号+序号": financial_code,
                        "财务资产名称": financial_record.get("资产名称", ""),
                        "财务资产价值": financial_value,
                        "财务部门": financial_record.get("部门名称", ""),
                        "财务保管人": financial_record.get("保管人", ""),
                        "实物台账编号": physical_code,
                        "实物资产名称": physical_record.get("固定资产名称", ""),
                        "实物资产价值": physical_value,
                        "实物部门": physical_record.get("存放部门", ""),
                        "实物保管人": physical_record.get("保管人", ""),
                        "价值差异": financial_value - physical_value,
                        "状态": "正常匹配"
                    })
                else:
                    # 记录映射存在但数据缺失的情况
                    mapping_summary.append({
                        "资产编号+序号": financial_code,
                        "财务资产名称": "数据缺失" if not financial_record else financial_record.get("资产名称", ""),
                        "财务资产价值": 0 if not financial_record else safe_get_value(financial_record, "资产价值"),
                        "财务部门": "数据缺失" if not financial_record else financial_record.get("部门名称", ""),
                        "财务保管人": "数据缺失" if not financial_record else financial_record.get("保管人", ""),
                        "实物台账编号": physical_code,
                        "实物资产名称": "数据缺失" if not physical_record else physical_record.get("固定资产名称", ""),
                        "实物资产价值": 0 if not physical_record else safe_get_value(physical_record, "资产价值"),
                        "实物部门": "数据缺失" if not physical_record else physical_record.get("存放部门", ""),
                        "实物保管人": "数据缺失" if not physical_record else physical_record.get("保管人", ""),
                        "价值差异": 0,
                        "状态": "数据异常"
                    })

        if mapping_summary:
            df = pd.DataFrame(mapping_summary)

            # 添加筛选功能
            col1, col2, col3 = st.columns(3)
            with col1:
                # 获取所有部门（财务和实物）
                all_financial_depts = [dept for dept in df["财务部门"].unique() if dept and dept != "数据缺失"]
                all_physical_depts = [dept for dept in df["实物部门"].unique() if dept and dept != "数据缺失"]
                all_depts = sorted(list(set(all_financial_depts + all_physical_depts)))
                dept_filter = st.selectbox("按部门筛选", ["全部"] + all_depts)

            with col2:
                diff_filter = st.selectbox("按差异筛选", ["全部", "有差异", "无差异", "数据异常"])

            with col3:
                search_term = st.text_input("搜索资产名称")

            # 应用筛选
            filtered_df = df.copy()

            if dept_filter != "全部":
                filtered_df = filtered_df[
                    (filtered_df["财务部门"] == dept_filter) | (filtered_df["实物部门"] == dept_filter)]

            if diff_filter == "有差异":
                filtered_df = filtered_df[(filtered_df["价值差异"].abs() > 0.01) & (filtered_df["状态"] == "正常匹配")]
            elif diff_filter == "无差异":
                filtered_df = filtered_df[(filtered_df["价值差异"].abs() <= 0.01) & (filtered_df["状态"] == "正常匹配")]
            elif diff_filter == "数据异常":
                filtered_df = filtered_df[filtered_df["状态"] == "数据异常"]

            if search_term:
                filtered_df = filtered_df[
                    filtered_df["财务资产名称"].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df["实物资产名称"].astype(str).str.contains(search_term, case=False, na=False)
                    ]

            st.info(f"共 {len(filtered_df)} 条记录（总映射关系 {len(df)} 条）")

            # 格式化显示数值
            display_df = filtered_df.copy()
            display_df["财务资产价值"] = display_df["财务资产价值"].apply(
                lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)
            display_df["实物资产价值"] = display_df["实物资产价值"].apply(
                lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)
            display_df["价值差异"] = display_df["价值差异"].apply(
                lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)

            st.dataframe(display_df, use_container_width=True)

            # 导出功能
            if st.button("📥 导出为Excel"):
                try:
                    output = io.BytesIO()
                    filtered_df.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    st.download_button(
                        label="下载Excel文件",
                        data=output,
                        file_name=f"资产对应关系汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
        else:
            st.warning("⚠️ 暂无映射关系数据")

    elif view_mode == "财务系统明细":
        st.subheader("📊 财务系统资产明细")

        if not financial_data:
            st.warning("⚠️ 暂无财务系统数据")
            return

        df = pd.DataFrame(financial_data)

        # 检查必需列是否存在
        if "资产编号+序号" not in df.columns:
            st.error("❌ 财务数据中缺少'资产编号+序号'列，请检查数据格式")
            st.write("当前列名：", list(df.columns))
            return

        # 修复：正确添加匹配状态列
        df["匹配状态"] = df["资产编号+序号"].astype(str).apply(
            lambda x: "已匹配" if str(x).strip() in financial_to_physical_mapping else "未匹配")

        # 添加对应实物编号列
        df["对应实物编号"] = df["资产编号+序号"].astype(str).apply(
            lambda x: ", ".join(financial_to_physical_mapping.get(str(x).strip(), [])) if str(
                x).strip() in financial_to_physical_mapping else "无")

        # 筛选功能
        col1, col2, col3 = st.columns(3)
        with col1:
            match_filter = st.selectbox("匹配状态", ["全部", "已匹配", "未匹配"])
        with col2:
            # 部门筛选
            all_depts = sorted([dept for dept in df["部门名称"].unique() if dept and str(dept).strip()])
            dept_filter = st.selectbox("按部门筛选", ["全部"] + all_depts, key="financial_dept_filter")
        with col3:
            search_term = st.text_input("搜索资产", key="financial_search")

        filtered_df = df.copy()

        if match_filter != "全部":
            filtered_df = filtered_df[filtered_df["匹配状态"] == match_filter]

        if dept_filter != "全部":
            filtered_df = filtered_df[filtered_df["部门名称"] == dept_filter]

        if search_term:
            filtered_df = filtered_df[
                filtered_df["资产名称"].astype(str).str.contains(search_term, case=False, na=False) |
                filtered_df["资产编号+序号"].astype(str).str.contains(search_term, case=False, na=False)
                ]

        st.info(f"共 {len(filtered_df)} 条记录（总财务资产 {len(df)} 条）")

        # 选择要显示的列
        available_columns = list(filtered_df.columns)
        default_columns = ["资产编号+序号", "资产名称", "资产分类", "资产价值", "累计折旧", "资产净额", "部门名称", "保管人", "匹配状态", "对应实物编号"]
        display_columns = [col for col in default_columns if col in available_columns]

        # 格式化显示
        display_df = filtered_df[display_columns].copy()
        # 格式化所有金额字段
        for amount_col in ["资产价值", "累计折旧", "资产净额"]:
            if amount_col in display_df.columns:
                display_df[amount_col] = display_df[amount_col].apply(
                    lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)

        st.dataframe(display_df, use_container_width=True)

        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            matched_count = len(filtered_df[filtered_df["匹配状态"] == "已匹配"])
            st.metric("已匹配", matched_count)
        with col2:
            unmatched_count = len(filtered_df[filtered_df["匹配状态"] == "未匹配"])
            st.metric("未匹配", unmatched_count)
        with col3:
            total_value = filtered_df["资产价值"].sum() if "资产价值" in filtered_df.columns else 0
            try:
                total_value = 0.0
                valid_count = 0
                error_count = 0

                for _, row in filtered_df.iterrows():
                    try:
                        value = safe_convert_to_float(row.get("资产价值", 0))
                        if value > 0:
                            total_value += value
                            valid_count += 1
                        elif value == 0:
                            pass  # 价值为0的记录
                        else:
                            error_count += 1
                    except:
                        error_count += 1

                st.metric("总价值", f"¥{total_value:,.2f}")

                if valid_count > 0:
                    success_rate = (valid_count / len(filtered_df)) * 100
                    st.caption(f"有效记录: {valid_count}/{len(filtered_df)} ({success_rate:.1f}%)")

                if error_count > 0:
                    st.caption(f"⚠️ {error_count}条记录数值异常")

            except Exception as e:
                st.metric("总价值", "计算错误")
                st.error(f"❌ 计算错误: {str(e)}")


    elif view_mode == "实物台账明细":

        st.subheader("📋 实物台账资产明细")

        if not physical_data:
            st.warning("⚠️ 暂无实物台账数据")

            return

        df = pd.DataFrame(physical_data)

        # 检查必需列是否存在

        if "固定资产编码" not in df.columns:
            st.error("❌ 实物数据中缺少'固定资产编码'列，请检查数据格式")

            st.write("当前列名：", list(df.columns))

            return

        # ✅ 检查固定资产原值字段是否存在

        if "固定资产原值" not in df.columns:
            st.error("❌ 实物数据中缺少'固定资产原值'列，请检查数据格式")

            st.write("当前列名：", list(df.columns))

            st.info("💡 请确保Excel文件中包含名为'固定资产原值'的列")

            return

        # 修复：正确添加匹配状态列

        df["匹配状态"] = df["固定资产编码"].astype(str).apply(

            lambda x: "已匹配" if str(x).strip() in physical_to_financial_mapping else "未匹配")

        # 添加对应财务编号列

        df["对应财务编号"] = df["固定资产编码"].astype(str).apply(

            lambda x: ", ".join(physical_to_financial_mapping.get(str(x).strip(), [])) if str(

                x).strip() in physical_to_financial_mapping else "无")

        # 筛选功能

        col1, col2, col3 = st.columns(3)

        with col1:

            match_filter = st.selectbox("匹配状态", ["全部", "已匹配", "未匹配"], key="physical_match")

        with col2:

            # 部门筛选

            all_depts = sorted([dept for dept in df["存放部门"].unique() if dept and str(dept).strip()])

            dept_filter = st.selectbox("按部门筛选", ["全部"] + all_depts, key="physical_dept_filter")

        with col3:

            search_term = st.text_input("搜索资产", key="physical_search")

        filtered_df = df.copy()

        if match_filter != "全部":
            filtered_df = filtered_df[filtered_df["匹配状态"] == match_filter]

        if dept_filter != "全部":
            filtered_df = filtered_df[filtered_df["存放部门"] == dept_filter]

        if search_term:
            filtered_df = filtered_df[

                filtered_df["固定资产名称"].astype(str).str.contains(search_term, case=False, na=False) |

                filtered_df["固定资产编码"].astype(str).str.contains(search_term, case=False, na=False)

                ]

        st.info(f"共 {len(filtered_df)} 条记录（总实物资产 {len(df)} 条）")

        # ✅ 固定使用"固定资产原值"字段

        value_field = "固定资产原值"

        default_columns = ["固定资产编码", "固定资产名称", "固定资产类型", "固定资产原值", "累计折旧", "资产净值", "存放部门", "保管人", "使用状态", "匹配状态", "对应财务编号"]

        # 只显示存在的列

        available_columns = list(filtered_df.columns)

        display_columns = [col for col in default_columns if col in available_columns]

        # ✅ 格式化显示固定资产原值

        display_df = filtered_df[display_columns].copy()

        for amount_col in ["固定资产原值", "累计折旧", "资产净值"]:
            if amount_col in display_df.columns:
                display_df[amount_col] = display_df[amount_col].apply(
                    lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else (
                        f"¥0.00" if pd.isna(x) or x == "" else str(x)))

        st.dataframe(display_df, use_container_width=True)

        # ✅ 统计信息 - 仅使用固定资产原值字段

        col1, col2, col3 = st.columns(3)

        with col1:

            matched_count = len(filtered_df[filtered_df["匹配状态"] == "已匹配"])

            st.metric("已匹配", matched_count)

        with col2:

            unmatched_count = len(filtered_df[filtered_df["匹配状态"] == "未匹配"])

            st.metric("未匹配", unmatched_count)

        # ✅ 关键修复：仅使用固定资产原值字段计算总价值，支持核算筛选
        try:
            # 🆕 新增：检查是否有核算字段
            has_accounting_field = "是否核算" in filtered_df.columns

            # 原始计算（包含重复记录，支持核算筛选）
            total_value_raw = 0.0
            valid_count = 0
            error_count = 0
            non_accounting_count = 0  # 非核算资产数量

            for _, row in filtered_df.iterrows():
                try:
                    # 🆕 检查是否核算
                    if has_accounting_field:
                        accounting_status = str(row.get("是否核算", "")).strip()
                        if accounting_status not in ["是", "Y", "y", "Yes", "YES", "1", "True", "true"]:
                            non_accounting_count += 1
                            continue  # 跳过非核算资产

                    value = safe_convert_to_float(row.get("固定资产原值", 0))
                    if value > 0:
                        total_value_raw += value
                        valid_count += 1
                    elif value == 0:
                        pass  # 价值为0的记录
                    else:
                        error_count += 1
                except:
                    error_count += 1

            # 去重计算（按固定资产编码去重）
            df_deduped = filtered_df.drop_duplicates(subset=['固定资产编码'], keep='first')

            # 🆕 新增：对去重后的数据也应用核算筛选
            total_value_dedup = 0.0
            valid_count_dedup = 0
            non_accounting_dedup_count = 0

            for _, row in df_deduped.iterrows():
                try:
                    # 🆕 检查是否核算
                    if has_accounting_field:
                        accounting_status = str(row.get("是否核算", "")).strip()
                        if accounting_status not in ["是", "Y", "y", "Yes", "YES", "1", "True", "true"]:
                            non_accounting_dedup_count += 1
                            continue  # 跳过非核算资产

                    value = safe_convert_to_float(row.get("固定资产原值", 0))
                    if value > 0:
                        total_value_dedup += value
                        valid_count_dedup += 1
                except:
                    pass

            # 显示结果
            duplicate_count = len(filtered_df) - len(df_deduped)

            if duplicate_count > 0:
                st.metric("固定资产原值总计", f"¥{total_value_dedup:,.2f}")
                # ✅ 修复：使用更简洁的说明文字，避免文字过长
                caption_text = f"已去重 ({duplicate_count}条)"
                if has_accounting_field and non_accounting_dedup_count > 0:
                    caption_text += f" | 已排除{non_accounting_dedup_count}条非核算"
                st.caption(caption_text)
            else:
                st.metric("固定资产原值总计", f"¥{total_value_raw:,.2f}")
                caption_text = "无重复记录"
                if has_accounting_field and non_accounting_count > 0:
                    caption_text += f" | 已排除{non_accounting_count}条非核算"
                st.caption(caption_text)

            # ✅ 新增：显示核算筛选统计
            if has_accounting_field:
                total_accounting = valid_count if duplicate_count == 0 else valid_count_dedup
                total_non_accounting = non_accounting_count if duplicate_count == 0 else non_accounting_dedup_count
                total_records = total_accounting + total_non_accounting

                if total_non_accounting > 0:
                    st.info(
                        f"📊 核算筛选统计: 核算资产{total_accounting}条 | 非核算资产{total_non_accounting}条 | 总计{total_records}条")

            # 显示处理统计
            if valid_count > 0:
                success_rate = (valid_count / len(filtered_df)) * 100
                if success_rate < 100:
                    st.warning(f"⚠️ {error_count}条记录数值异常")
            else:
                st.error("❌ 所有记录数值异常")

        except Exception as e:
            st.metric("固定资产原值总计", "计算错误")
            st.error(f"❌ 计算错误: {str(e)}")

            with st.expander("🚨 错误详情"):
                st.code(f"错误类型: {type(e).__name__}\n错误信息: {str(e)}")
                if len(filtered_df) > 0:
                    st.write("数据样本：", filtered_df["固定资产原值"].head(3).tolist())

                # ✅ 修复：将详细信息移到下方单独显示，避免挤压
                if duplicate_count > 0:
                    st.info(f"📊 原始记录: {len(filtered_df)}条 → 去重后: {len(df_deduped)}条")

                # 显示处理统计
                if valid_count > 0:
                    success_rate = (valid_count / len(filtered_df)) * 100
                    if success_rate < 100:
                        st.warning(f"⚠️ {error_count}条记录数值异常")
                else:
                    st.error("❌ 所有记录数值异常")

        # ✅ 新增：将详细统计按钮移到列外，单独显示
        if valid_count > 0:
            st.markdown("---")

            # 创建展开的统计信息区域
            with st.expander("📊 详细统计信息", expanded=False):
                # 使用4列布局显示更多统计信息
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

                with stat_col1:
                    st.metric("原始总价值", f"¥{total_value_raw:,.2f}")
                    st.caption(f"包含 {len(filtered_df)} 条记录")

                with stat_col2:
                    st.metric("去重总价值", f"¥{total_value_dedup:,.2f}")
                    st.caption(f"去重后 {len(df_deduped)} 条记录")

                with stat_col3:
                    if duplicate_count > 0:
                        reduction = total_value_raw - total_value_dedup
                        st.metric("重复金额", f"¥{reduction:,.2f}")
                        st.caption(f"删除 {duplicate_count} 条重复")
                    else:
                        st.metric("重复记录", "0条")
                        st.caption("无重复数据")

                with stat_col4:
                    if valid_count > 0:
                        success_rate = (valid_count / len(filtered_df)) * 100
                        st.metric("数据有效率", f"{success_rate:.1f}%")
                        st.caption(f"{valid_count}/{len(filtered_df)} 条有效")
                    else:
                        st.metric("数据有效率", "0%")
                        st.caption("无有效数据")

                # 显示字段使用情况
                st.info("💡 统计基于 `固定资产原值` 字段")

                # 显示重复记录详情
                if duplicate_count > 0:
                    st.markdown("### 📋 重复记录分析")

                    # 重复记录统计
                    duplicate_analysis = filtered_df[
                        filtered_df.duplicated(subset=['固定资产编码'], keep=False)].groupby('固定资产编码').agg({
                        '固定资产名称': 'first',
                        '固定资产原值': ['first', 'count'],
                        '存放部门': lambda x: ', '.join(x.unique()) if len(x.unique()) > 1 else x.iloc[0]
                    }).reset_index()

                    # 扁平化列名
                    duplicate_analysis.columns = ['固定资产编码', '固定资产名称', '固定资产原值', '重复次数',
                                                  '存放部门']

                    # 格式化显示
                    duplicate_analysis['固定资产原值'] = duplicate_analysis['固定资产原值'].apply(
                        lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)

                    st.dataframe(duplicate_analysis, use_container_width=True)

                    if st.button("📥 导出重复记录", key="export_duplicates"):
                        try:
                            output = io.BytesIO()
                            duplicate_analysis.to_excel(output, index=False, engine='openpyxl')
                            output.seek(0)
                            st.download_button(
                                label="下载重复记录Excel",
                                data=output,
                                file_name=f"重复记录分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_duplicates"
                            )
                        except Exception as e:
                            st.error(f"导出失败: {str(e)}")

                # 推荐使用的总价值
                if duplicate_count > 0:
                    st.success(f"✅ **推荐使用去重后总价值：¥{total_value_dedup:,.2f}**")
                    st.info(f"💡 去重可避免重复计算，节省 ¥{total_value_raw - total_value_dedup:,.2f}")
                else:
                    st.success(f"✅ **固定资产原值总计：¥{total_value_raw:,.2f}**")
                    st.info("💡 数据无重复，可直接使用此总价值")

        # ✅ 如果有数据异常，显示调试信息
        if error_count > 0:
            with st.expander("🔧 数据异常分析", expanded=False):
                st.write("**异常记录的固定资产原值字段内容：**")

                # 找出异常记录
                error_records = []
                for _, row in filtered_df.iterrows():
                    try:
                        value = safe_convert_to_float(row.get("固定资产原值", 0))
                        if value <= 0 and value != 0:  # 排除正常的0值
                            error_records.append({
                                '固定资产编码': row.get('固定资产编码', ''),
                                '固定资产名称': row.get('固定资产名称', ''),
                                '固定资产原值': row.get('固定资产原值', ''),
                                '原值类型': type(row.get('固定资产原值', '')).__name__,
                                '转换结果': value
                            })
                    except:
                        error_records.append({
                            '固定资产编码': row.get('固定资产编码', ''),
                            '固定资产名称': row.get('固定资产名称', ''),
                            '固定资产原值': row.get('固定资产原值', ''),
                            '原值类型': type(row.get('固定资产原值', '')).__name__,
                            '转换结果': '转换失败'
                        })

                if error_records:
                    error_df = pd.DataFrame(error_records[:10])  # 只显示前10条
                    st.dataframe(error_df, use_container_width=True)

                    if len(error_records) > 10:
                        st.info(f"显示前10条，共{len(error_records)}条异常记录")

                st.markdown("**可能的问题及解决方案：**")
                st.markdown("- 🔧 **文本格式**: 原值字段包含文字，需要清理数据")
                st.markdown("- 🔧 **特殊字符**: 包含货币符号或千位分隔符，需要格式化")
                st.markdown("- 🔧 **空值**: 字段为空或NaN，建议填入0或删除记录")
                st.markdown("- 🔧 **负数**: 原值为负数，需要检查数据合理性")

    else:  # 未匹配资产
        st.subheader("⚠️ 未匹配资产列表")

        tab1, tab2 = st.tabs(["未匹配财务资产", "未匹配实物资产"])

        with tab1:
            if not financial_data:
                st.warning("⚠️ 暂无财务系统数据")
            else:
                # 检查数据完整性
                if financial_data and "资产编号+序号" not in pd.DataFrame(financial_data).columns:
                    st.error("❌ 财务数据中缺少'资产编号+序号'列")
                    return

                # 修复：正确筛选未匹配的财务资产
                unmatched_financial = [f for f in financial_data if
                                       str(f.get("资产编号+序号", "")).strip() not in financial_to_physical_mapping]

                if unmatched_financial:  # ✅ 添加：判断是否有未匹配数据
                    df = pd.DataFrame(unmatched_financial)  # ✅ 添加：创建DataFrame
                    st.info(f"共 {len(df)} 条未匹配财务资产（总计 {len(financial_data)} 条）")

                    # 添加搜索功能
                    search_term = st.text_input("搜索未匹配财务资产", key="search_unmatched_financial")
                    if search_term:  # ✅ 修复：正确的缩进
                        df = df[  # ✅ 修复：正确的缩进
                            df["资产名称"].astype(str).str.contains(search_term, case=False, na=False) |
                            df["资产编号+序号"].astype(str).str.contains(search_term, case=False, na=False)
                            ]
                        st.info(f"搜索结果：{len(df)} 条记录")

                    # 选择要显示的列
                    available_columns = list(df.columns)
                    default_columns = ["资产编号+序号", "资产名称", "资产分类", "资产价值", "累计折旧", "资产净额", "部门名称", "保管人"]
                    display_columns = [col for col in default_columns if col in available_columns]

                    # 格式化显示
                    display_df = df[display_columns].copy()
                    # 格式化所有金额字段
                    for amount_col in ["资产价值", "累计折旧", "资产净额"]:
                        if amount_col in display_df.columns:
                            display_df[amount_col] = display_df[amount_col].apply(
                                lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else x)

                    st.dataframe(display_df, use_container_width=True)

                    # 统计信息
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        # 安全计算未匹配财务资产总价值
                        try:
                            total_value = 0.0
                            for record in unmatched_financial:  # ✅ 修复：使用正确的变量
                                if isinstance(record, dict):
                                    # 使用财务系统的价值字段
                                    value = safe_get_value(record, "资产价值", 0)
                                    total_value += value
                            st.metric("未匹配资产总价值", f"¥{total_value:,.2f}")
                        except Exception as e:
                            st.metric("未匹配资产总价值", "计算错误")

                    with col2:
                        match_rate = ((len(financial_data) - len(unmatched_financial)) / len(
                            financial_data) * 100) if financial_data else 0
                        st.metric("财务资产匹配率", f"{match_rate:.1f}%")

                        with col3:
                            # 计算累计折旧总额 - 财务系统，使用"累计折旧"字段
                            try:
                                total_depreciation = 0.0
                                valid_depreciation_count = 0
                                zero_depreciation_count = 0

                                for record in unmatched_financial:
                                    if isinstance(record, dict):
                                        # 直接使用"累计折旧"字段
                                        depreciation_value = safe_get_value(record, "累计折旧", 0)

                                        if depreciation_value > 0:
                                            total_depreciation += depreciation_value
                                            valid_depreciation_count += 1
                                        elif depreciation_value == 0:
                                            zero_depreciation_count += 1

                                st.metric("未匹配累计折旧总额", f"¥{total_depreciation:,.2f}")

                                # 显示详细统计
                                if valid_depreciation_count > 0:
                                    st.caption(f"✅ 有折旧: {valid_depreciation_count}条")
                                if zero_depreciation_count > 0:
                                    st.caption(f"⚪ 零折旧: {zero_depreciation_count}条")

                            except Exception as e:
                                st.metric("未匹配累计折旧总额", "计算错误")
                                st.error(f"计算错误: {str(e)}")

                        with col4:
                            # 计算资产净值总计 - 财务系统，使用"资产净额"字段
                            try:
                                total_net_value = 0.0
                                valid_net_count = 0
                                zero_net_count = 0

                                for record in unmatched_financial:
                                    if isinstance(record, dict):
                                        # 直接使用"资产净额"字段
                                        net_value = safe_get_value(record, "资产净额", 0)

                                        if net_value > 0:
                                            total_net_value += net_value
                                            valid_net_count += 1
                                        elif net_value == 0:
                                            zero_net_count += 1

                                st.metric("未匹配资产净值总计", f"¥{total_net_value:,.2f}")

                                # 显示详细统计
                                if valid_net_count > 0:
                                    st.caption(f"✅ 有净值: {valid_net_count}条")
                                if zero_net_count > 0:
                                    st.caption(f"⚪ 零净值: {zero_net_count}条")

                                st.info("💡 使用财务系统 `资产净额` 字段")

                            except Exception as e:
                                st.metric("未匹配资产净值总计", "计算错误")
                                st.caption(f"错误: {str(e)}")

        with tab2:
            if not physical_data:
                st.warning("⚠️ 暂无实物台账数据")
            else:
                # 检查数据完整性
                if physical_data and "固定资产编码" not in pd.DataFrame(physical_data).columns:
                    st.error("❌ 实物数据中缺少'固定资产编码'列")
                    return

                # 修复：正确筛选未匹配的实物资产
                unmatched_physical = [p for p in physical_data if
                                      str(p.get("固定资产编码", "")).strip() not in physical_to_financial_mapping]

                if unmatched_physical:  # ✅ 添加：判断是否有未匹配数据
                    df = pd.DataFrame(unmatched_physical)  # ✅ 添加：创建DataFrame
                    st.info(f"共 {len(df)} 条未匹配实物资产（总计 {len(physical_data)} 条）")

                    # 添加搜索功能
                    search_term = st.text_input("搜索未匹配实物资产", key="search_unmatched_physical")
                    if search_term:
                        df = df[
                            df["固定资产名称"].astype(str).str.contains(search_term, case=False, na=False) |
                            df["固定资产编码"].astype(str).str.contains(search_term, case=False, na=False)
                            ]
                        st.info(f"搜索结果：{len(df)} 条记录")

                    # 选择要显示的列
                    available_columns = list(df.columns)
                    default_columns = ["固定资产编码", "固定资产名称", "固定资产类型", "固定资产原值", "累计折旧", "资产净值", "存放部门", "保管人", "使用状态"]
                    display_columns = [col for col in default_columns if col in available_columns]

                    # 格式化显示
                    display_df = df[display_columns].copy()
                    # 格式化所有金额字段
                    for amount_col in ["固定资产原值", "资产价值", "累计折旧", "资产净值"]:
                        if amount_col in display_df.columns:
                            display_df[amount_col] = display_df[amount_col].apply(
                                lambda x: f"¥{x:,.2f}" if isinstance(x, (int, float)) else (
                                    f"¥0.00" if pd.isna(x) or x == "" else str(x)))

                    st.dataframe(display_df, use_container_width=True)

                    # 统计信息
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        # 智能识别实物资产价值字段并计算总价值
                        try:
                            total_value = 0.0
                            processed_count = 0
                            field_usage_stats = {}  # 统计各字段的使用情况

                            # 🔍 扩展的实物资产价值字段列表（财务人员常用字段）
                            possible_value_fields = [
                                # 标准财务字段
                                "资产价值", "固定资产原值", "原值", "账面价值", "净值", "账面净值",
                                "资产原值", "购置价值", "评估价值", "市值", "价值", "入账价值",

                                # 常见变体字段
                                "金额", "总价", "单价", "成本", "购买价格", "采购价格", "历史成本",
                                "资产总额", "固定资产净值", "资产净额", "投资成本", "建造成本",

                                # 可能的英文字段
                                "Value", "Amount", "Cost", "Price", "Total", "Net_Value",

                                # 可能包含数字的其他字段
                                "价格", "费用", "支出", "投入", "造价"
                            ]

                            # 🔧 第一步：尝试标准字段识别
                            for record in unmatched_physical:
                                if isinstance(record, dict):
                                    asset_value = 0.0
                                    used_field = None

                                    # 按优先级尝试各个可能的价值字段
                                    for field in possible_value_fields:
                                        if field in record and record[field] is not None:
                                            try:
                                                converted_value = safe_convert_to_float(record[field])
                                                if converted_value > 0:  # 只接受大于0的值
                                                    asset_value = converted_value
                                                    used_field = field
                                                    break
                                            except:
                                                continue

                                    # 如果找到有效价值，累加并记录
                                    if asset_value > 0 and used_field:
                                        total_value += asset_value
                                        processed_count += 1

                                        # 统计字段使用情况
                                        if used_field not in field_usage_stats:
                                            field_usage_stats[used_field] = 0
                                        field_usage_stats[used_field] += 1

                            # 📊 显示计算结果
                            st.metric("未匹配资产总价值", f"¥{total_value:,.2f}")

                            # ✅ 成功处理的情况
                            if processed_count > 0:
                                success_rate = (processed_count / len(unmatched_physical)) * 100
                                st.success(
                                    f"✅ 成功处理 {processed_count}/{len(unmatched_physical)} 条记录 ({success_rate:.1f}%)")

                                # 显示字段使用统计
                                with st.expander("📊 价值字段使用统计", expanded=True):
                                    st.write("**成功识别的价值字段：**")
                                    for field, count in sorted(field_usage_stats.items(), key=lambda x: x[1],
                                                               reverse=True):
                                        percentage = (count / processed_count) * 100
                                        st.write(f"- **{field}**: {count} 条记录 ({percentage:.1f}%)")

                                    st.info(
                                        f"💡 建议：主要使用 `{max(field_usage_stats.items(), key=lambda x: x[1])[0]}` 字段作为价值字段")

                            # ❌ 处理失败的情况
                            else:
                                st.error(f"❌ 无法从 {len(unmatched_physical)} 条记录中提取有效价值")

                                # 🔍 显示详细调试信息
                                with st.expander("🔧 详细字段分析", expanded=True):
                                    if unmatched_physical:
                                        sample_record = unmatched_physical[0]

                                        st.markdown("### 📋 第一条记录的完整字段分析")

                                        # 显示所有字段
                                        col_left, col_right = st.columns(2)

                                        with col_left:
                                            st.write("**所有字段及其值：**")
                                            for key, value in sample_record.items():
                                                # 尝试转换为数字看是否可能是价值字段
                                                converted = safe_convert_to_float(value)
                                                if converted > 0:
                                                    st.write(f"🟢 `{key}`: {value} → **{converted:,.2f}** ⭐")
                                                else:
                                                    st.write(f"🔘 `{key}`: {value}")

                                        with col_right:
                                            st.write("**可能的价值字段（数值>0）：**")
                                            potential_fields = {}
                                            for key, value in sample_record.items():
                                                converted = safe_convert_to_float(value)
                                                if converted > 0:
                                                    potential_fields[key] = converted

                                            if potential_fields:
                                                for key, value in sorted(potential_fields.items(), key=lambda x: x[1],
                                                                         reverse=True):
                                                    st.write(f"💰 **{key}**: ¥{value:,.2f}")
                                            else:
                                                st.warning("⚠️ 未发现包含有效数值的字段")

                                        # 🔧 手动字段选择功能
                                        st.markdown("---")
                                        st.markdown("### 🛠️ 手动指定价值字段")
                                        st.info("如果自动识别失败，您可以手动选择正确的价值字段：")

                                        available_fields = [k for k in sample_record.keys() if
                                                            sample_record[k] is not None]
                                        selected_field = st.selectbox(
                                            "选择包含资产价值的字段：",
                                            ["请选择字段..."] + available_fields,
                                            key="manual_value_field_physical_enhanced"
                                        )

                                        if selected_field != "请选择字段..." and st.button("🔄 使用选定字段重新计算",
                                                                                           key="recalc_physical_enhanced"):
                                            # 使用手动选择的字段重新计算
                                            manual_total = 0.0
                                            manual_count = 0
                                            manual_errors = 0

                                            for record in unmatched_physical:
                                                if isinstance(record, dict) and selected_field in record:
                                                    try:
                                                        value = safe_convert_to_float(record[selected_field])
                                                        if value > 0:
                                                            manual_total += value
                                                            manual_count += 1
                                                        elif value == 0:
                                                            pass  # 价值为0的记录
                                                        else:
                                                            manual_errors += 1
                                                    except:
                                                        manual_errors += 1

                                            # 显示重新计算结果
                                            st.success(f"✅ 使用字段 `{selected_field}` 重新计算完成！")

                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("重新计算总价值", f"¥{manual_total:,.2f}")
                                            with col2:
                                                st.metric("有效记录数", f"{manual_count}/{len(unmatched_physical)}")
                                            with col3:
                                                success_rate = (manual_count / len(unmatched_physical)) * 100
                                                st.metric("成功率", f"{success_rate:.1f}%")

                                            if manual_errors > 0:
                                                st.warning(f"⚠️ {manual_errors} 条记录无法转换为有效数值")

                                            # 提供应用修复的选项
                                            if manual_total > 0:
                                                st.info("💡 如果这个结果正确，建议联系技术人员将此字段设置为默认价值字段")

                        except Exception as e:
                            st.metric("未匹配资产总价值", "计算错误")
                            st.error(f"❌ 计算错误详情: {str(e)}")

                            # 显示异常调试信息
                            with st.expander("🚨 异常详情"):
                                st.code(f"错误类型: {type(e).__name__}\n错误信息: {str(e)}")
                                if unmatched_physical:
                                    st.write("数据样本：", unmatched_physical[0])

                            st.metric("未匹配资产总价值", f"¥{total_value:,.2f}")

                            # 调试信息（可选）
                            if total_value == 0 and len(unmatched_physical) > 0:
                                st.warning(
                                    f"⚠️ 检测到{len(unmatched_physical)}条未匹配资产但总价值为0，可能是数据字段问题")
                                with st.expander("🔧 调试信息"):
                                    sample_record = unmatched_physical[0]
                                    st.write("第一条记录的字段：", list(sample_record.keys()))
                                    st.write("价值相关字段：", {k: v for k, v in sample_record.items() if
                                                               "价值" in k or "金额" in k or "值" in k or "原值" in k})

                        except Exception as e:
                            st.metric("未匹配资产总价值", "计算错误")
                            st.error(f"计算错误详情: {str(e)}")
                    with col2:
                        match_rate = ((len(physical_data) - len(unmatched_physical)) / len(
                            physical_data) * 100) if physical_data else 0
                        st.metric("实物资产匹配率", f"{match_rate:.1f}%")

                    # 导出未匹配实物资产
                    if st.button("📥 导出未匹配实物资产", key="export_unmatched_physical"):
                        try:
                            output = io.BytesIO()
                            df[display_columns].to_excel(output, index=False, engine='openpyxl')
                            output.seek(0)
                            st.download_button(
                                label="下载Excel文件",
                                data=output,
                                file_name=f"未匹配实物资产_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_unmatched_physical"
                            )
                        except Exception as e:
                            st.error(f"导出失败: {str(e)}")
                else:  # ✅ 修复：正确的缩进，与if unmatched_physical对齐
                    st.success("✅ 所有实物资产都已匹配")

                with col3:
                    # 计算累计折旧总额 - 实物系统，使用"累计折旧"字段
                    try:
                        total_depreciation = 0.0
                        valid_depreciation_count = 0
                        zero_depreciation_count = 0

                        for record in unmatched_physical:
                            if isinstance(record, dict):
                                # 直接使用"累计折旧"字段
                                depreciation_value = safe_get_value(record, "累计折旧", 0)

                                if depreciation_value > 0:
                                    total_depreciation += depreciation_value
                                    valid_depreciation_count += 1
                                elif depreciation_value == 0:
                                    zero_depreciation_count += 1

                        st.metric("未匹配累计折旧总额", f"¥{total_depreciation:,.2f}")

                        # 显示详细统计
                        if valid_depreciation_count > 0:
                            st.caption(f"✅ 有折旧: {valid_depreciation_count}条")
                        if zero_depreciation_count > 0:
                            st.caption(f"⚪ 零折旧: {zero_depreciation_count}条")

                        st.info("💡 使用实物系统 `累计折旧` 字段")

                    except Exception as e:
                        st.metric("未匹配累计折旧总额", "计算错误")
                        st.caption(f"错误: {str(e)}")

                with col4:
                    # 计算资产净值总计 - 实物系统，通过"固定资产原值-累计折旧"计算
                    try:
                        total_net_value = 0.0
                        calculated_count = 0
                        no_original_count = 0
                        negative_net_count = 0

                        for record in unmatched_physical:
                            if isinstance(record, dict):
                                # 获取固定资产原值
                                original_value = safe_get_value(record, "固定资产原值", 0)

                                if original_value > 0:
                                    # 获取累计折旧
                                    depreciation_value = safe_get_value(record, "累计折旧", 0)

                                    # 计算净值 = 固定资产原值 - 累计折旧
                                    calculated_net = original_value - depreciation_value

                                    if calculated_net >= 0:
                                        total_net_value += calculated_net
                                        calculated_count += 1
                                    else:
                                        negative_net_count += 1
                                else:
                                    no_original_count += 1

                        st.metric("未匹配资产净值总计", f"¥{total_net_value:,.2f}")

                        # 显示计算统计
                        if calculated_count > 0:
                            st.caption(f"🧮 成功计算: {calculated_count}条")
                        if no_original_count > 0:
                            st.caption(f"⚪ 无原值: {no_original_count}条")
                        if negative_net_count > 0:
                            st.caption(f"⚠️ 负净值: {negative_net_count}条")

                        st.info("💡 净值 = 固定资产原值 - 累计折旧")

                    except Exception as e:
                        st.metric("未匹配资产净值总计", "计算错误")
                        st.caption(f"错误: {str(e)}")


def main():
    """主函数"""
    st.title("🔗 资产映射关系查询")

    # 侧边栏导航
    with st.sidebar:
        st.header("📋 系统导航")

        # 初始化 session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "📥 数据导入"

        # 创建垂直导航按钮
        st.markdown("### 🔧 功能模块")

        if st.button("📥 数据导入",
                     type="primary" if st.session_state.current_page == "📥 数据导入" else "secondary",
                     use_container_width=True, key="nav_import"):
            st.session_state.current_page = "📥 数据导入"
            st.rerun()

        if st.button("🔍 映射查询",
                     type="primary" if st.session_state.current_page == "🔍 映射查询" else "secondary",
                     use_container_width=True, key="nav_query"):
            st.session_state.current_page = "🔍 映射查询"
            st.rerun()

        if st.button("📊 数据统计",
                     type="primary" if st.session_state.current_page == "📊 数据统计" else "secondary",
                     use_container_width=True, key="nav_stats"):
            st.session_state.current_page = "📊 数据统计"
            st.rerun()

        if st.button("📋 全部数据",
                     type="primary" if st.session_state.current_page == "📋 全部数据" else "secondary",
                     use_container_width=True, key="nav_all"):
            st.session_state.current_page = "📋 全部数据"
            st.rerun()

        # 获取当前页面
        page = st.session_state.current_page

        st.markdown("---")
        st.markdown("### 📝 使用说明")
        st.markdown("""
        1. **数据导入**：上传Excel文件导入数据
        2. **映射查询**：查询资产对应关系
        3. **数据统计**：查看统计分析结果
        4. **全部数据**：浏览所有数据记录
        """)

        # ✅ 修复：只显示一次数据状态，并且静默加载
        st.markdown("---")
    st.markdown("### 🔧 GitHub配置检查")
    
    if st.button("🔍 检查GitHub配置", key="check_github"):
        config = get_github_config()
        if config:
            st.success("✅ GitHub配置已找到")
            st.write(f"仓库: {config['repo']}")
            st.write(f"Token: {'*' * (len(config['token']) - 4) + config['token'][-4:]}")
            
            # 测试GitHub连接
            try:
                g = Github(config["token"])
                repo = g.get_repo(config["repo"])
                st.success(f"✅ 仓库连接成功: {repo.full_name}")
                
                # 检查data文件夹
                try:
                    contents = repo.get_contents("data")
                    files = [item.name for item in contents if item.type == "file"]
                    st.write(f"📁 data文件夹文件: {files}")
                except Exception as e:
                    st.error(f"❌ data文件夹访问失败: {str(e)}")
                    
            except Exception as e:
                st.error(f"❌ GitHub连接失败: {str(e)}")
        else:
            st.error("❌ GitHub配置未找到")
 if GITHUB_AVAILABLE and get_github_config():
    st.sidebar.markdown("---")
    
    # 添加文件修复功能
    create_sample_data_files()
    
    # 添加修复指南
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚨 文件修复指南")
    st.sidebar.info("""
    **当前问题**: JSON文件为空或格式错误

    **解决步骤**:
    1. 点击"检查文件内容"查看详情
    2. 点击"创建示例数据"生成模板
    3. 下载模板文件
    4. 上传到GitHub的data文件夹
    5. 确保文件编码为UTF-8
    """)
    
    # 添加验证按钮
    if st.sidebar.button("🔧 验证修复", key="verify_fix"):
        st.sidebar.write("**验证结果:**")
        
        # 测试财务数据
        financial_data = load_data_from_github("financial_data.json")
        if financial_data:
            st.sidebar.success(f"✅ 财务数据: {len(financial_data)} 条")
        else:
            st.sidebar.error("❌ 财务数据仍有问题")
        
        # 测试实物数据  
        physical_data = load_data_from_github("physical_data.json")
        if physical_data:
            st.sidebar.success(f"✅ 实物数据: {len(physical_data)} 条")
        else:
            st.sidebar.error("❌ 实物数据仍有问题")
   
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
