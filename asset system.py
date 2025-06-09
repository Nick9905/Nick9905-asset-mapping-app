import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io

# 页面配置
st.set_page_config(
  page_title="资产映射关系查询系统",
  page_icon="🔗",
  layout="wide"
)

# 数据文件路径
FINANCIAL_DATA_FILE = "financial_assets.json"
PHYSICAL_DATA_FILE = "physical_assets.json"
MAPPING_DATA_FILE = "asset_mapping.json"

def load_data(file_path):
  """加载数据"""
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
def update_financial_data(existing_data, new_data):
    """更新财务系统数据"""
    # 创建现有数据的字典，以财务系统编号为键
    existing_dict = {item["财务系统编号"]: item for item in existing_data if item.get("财务系统编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        financial_code = new_item.get("财务系统编号")
        if financial_code and financial_code in existing_dict:
            # 更新现有记录
            existing_dict[financial_code].update(new_item)
            existing_dict[financial_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif financial_code:
            # 添加新记录
            existing_dict[financial_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())

def update_physical_data(existing_data, new_data):
    """更新实物台账数据"""
    # 创建现有数据的字典，以固定资产编号为键
    existing_dict = {item["固定资产编号"]: item for item in existing_data if item.get("固定资产编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        asset_code = new_item.get("固定资产编号")
        if asset_code and asset_code in existing_dict:
            # 更新现有记录
            existing_dict[asset_code].update(new_item)
            existing_dict[asset_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif asset_code:
            # 添加新记录
            existing_dict[asset_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())

def update_mapping_data(existing_data, new_data):
    """更新映射关系数据"""
    # 创建现有数据的字典，以实物台账编号为键
    existing_dict = {item["实物台账编号"]: item for item in existing_data if item.get("实物台账编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        physical_code = new_item.get("实物台账编号")
        if physical_code and physical_code in existing_dict:
            # 更新现有记录
            existing_dict[physical_code].update(new_item)
            existing_dict[physical_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif physical_code:
            # 添加新记录
            existing_dict[physical_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())


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

def import_financial_data(df):
  """导入财务系统数据"""
  processed_data = []
  
  # 添加调试信息，显示列名
  st.info(f"📋 Excel文件列数：{len(df.columns)}")
  with st.expander("🔍 查看Excel列信息（用于调试）"):
      for i, col in enumerate(df.columns):
          st.write(f"列 {i}: {col}")
  
  for index, row in df.iterrows():
      try:
          # 更灵活的列索引处理
          financial_record = {
              "财务系统编号": safe_str_convert(row.iloc[0] if len(row) > 0 else ""),
              "序号": safe_str_convert(row.iloc[1] if len(row) > 1 else ""),
              "所属公司": safe_str_convert(row.iloc[2] if len(row) > 2 else ""),
              "资产分类": safe_str_convert(row.iloc[3] if len(row) > 3 else ""),
              "资产编号": safe_str_convert(row.iloc[4] if len(row) > 4 else ""),
              "资产名称": safe_str_convert(row.iloc[5] if len(row) > 5 else ""),
              "资产规格": safe_str_convert(row.iloc[6] if len(row) > 6 else ""),
              "取得日期": safe_str_convert(row.iloc[9] if len(row) > 9 else ""),
              # 尝试多个可能的价值列位置
              "资产价值": safe_float_convert(
                  row.iloc[24] if len(row) > 24 else (
                      row.iloc[7] if len(row) > 7 else (
                          row.iloc[8] if len(row) > 8 else 0
                      )
                  )
              ),
              # 尝试多个可能的折旧列位置
              "累积折旧": safe_float_convert(
                  row.iloc[26] if len(row) > 26 else (
                      row.iloc[25] if len(row) > 25 else 0
                  )
              ),
              # 尝试多个可能的账面价值列位置
              "账面价值": safe_float_convert(
                  row.iloc[27] if len(row) > 27 else (
                      row.iloc[26] if len(row) > 26 else 0
                  )
              ),
              "部门名称": safe_str_convert(row.iloc[36] if len(row) > 36 else ""),
              "保管人": safe_str_convert(row.iloc[38] if len(row) > 38 else ""),
              "备注": safe_str_convert(row.iloc[28] if len(row) > 28 else ""),
              "导入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "原始行号": index + 1
          }
          
          # 添加调试信息，显示前几行的价值数据
          if index < 3:
              st.write(f"第{index+1}行数据预览：")
              st.write(f"  - 资产价值: {financial_record['资产价值']}")
              st.write(f"  - 累积折旧: {financial_record['累积折旧']}")
              st.write(f"  - 账面价值: {financial_record['账面价值']}")
          
          if financial_record["财务系统编号"] or financial_record["资产编号"]:
              processed_data.append(financial_record)
      except Exception as e:
          st.warning(f"处理第{index+1}行时出错: {str(e)}")
          continue
  return processed_data

def import_physical_data(df):
  """导入实物台账数据"""
  processed_data = []
  for index, row in df.iterrows():
      try:
          physical_record = {
              "所属公司": safe_str_convert(row.iloc[0] if len(row) > 0 else ""),
              "一级部门": safe_str_convert(row.iloc[1] if len(row) > 1 else ""),
              "固定资产编号": safe_str_convert(row.iloc[2] if len(row) > 2 else ""),
              "原固定资产编号": safe_str_convert(row.iloc[3] if len(row) > 3 else ""),
              "固定资产类型": safe_str_convert(row.iloc[4] if len(row) > 4 else ""),
              "固定资产名称": safe_str_convert(row.iloc[5] if len(row) > 5 else ""),
              "规格型号": safe_str_convert(row.iloc[6] if len(row) > 6 else ""),
              "存放部门": safe_str_convert(row.iloc[7] if len(row) > 7 else ""),
              "地点": safe_str_convert(row.iloc[8] if len(row) > 8 else ""),
              "使用人": safe_str_convert(row.iloc[9] if len(row) > 9 else ""),
              "保管人": safe_str_convert(row.iloc[10] if len(row) > 10 else ""),
              "实盘数量": safe_str_convert(row.iloc[11] if len(row) > 11 else ""),
              "入账日期": safe_str_convert(row.iloc[13] if len(row) > 13 else ""),
              "资产价值": safe_float_convert(row.iloc[16] if len(row) > 16 else 0),
              "累计折旧额": safe_float_convert(row.iloc[20] if len(row) > 20 else 0),
              "使用状态": safe_str_convert(row.iloc[21] if len(row) > 21 else ""),
              "导入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "原始行号": index + 1
          }
          if physical_record["固定资产编号"]:
              processed_data.append(physical_record)
      except Exception as e:
          continue
  return processed_data
def update_financial_data(existing_data, new_data):
    """更新财务系统数据"""
    # 创建现有数据的字典，以财务系统编号为键
    existing_dict = {item["财务系统编号"]: item for item in existing_data if item.get("财务系统编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        financial_code = new_item.get("财务系统编号")
        if financial_code and financial_code in existing_dict:
            # 更新现有记录
            existing_dict[financial_code].update(new_item)
            existing_dict[financial_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif financial_code:
            # 添加新记录
            existing_dict[financial_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())

def update_physical_data(existing_data, new_data):
    """更新实物台账数据"""
    # 创建现有数据的字典，以固定资产编号为键
    existing_dict = {item["固定资产编号"]: item for item in existing_data if item.get("固定资产编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        asset_code = new_item.get("固定资产编号")
        if asset_code and asset_code in existing_dict:
            # 更新现有记录
            existing_dict[asset_code].update(new_item)
            existing_dict[asset_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif asset_code:
            # 添加新记录
            existing_dict[asset_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())

def update_mapping_data(existing_data, new_data):
    """更新映射关系数据"""
    # 创建现有数据的字典，以实物台账编号为键
    existing_dict = {item["实物台账编号"]: item for item in existing_data if item.get("实物台账编号")}
    
    updated_count = 0
    new_count = 0
    
    for new_item in new_data:
        physical_code = new_item.get("实物台账编号")
        if physical_code and physical_code in existing_dict:
            # 更新现有记录
            existing_dict[physical_code].update(new_item)
            existing_dict[physical_code]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count += 1
        elif physical_code:
            # 添加新记录
            existing_dict[physical_code] = new_item
            new_count += 1
    
    st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
    return list(existing_dict.values())


def import_mapping_data(df):
  """导入关系对照表数据"""
  processed_data = []
  for index, row in df.iterrows():
      try:
          mapping_record = {
              "实物台账编号": safe_str_convert(row.iloc[0] if len(row) > 0 else ""),
              "财务系统编号": safe_str_convert(row.iloc[1] if len(row) > 1 else ""),
              "资产编号": safe_str_convert(row.iloc[2] if len(row) > 2 else ""),
              "导入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "原始行号": index + 1
          }
          if mapping_record["实物台账编号"] or mapping_record["财务系统编号"]:
              processed_data.append(mapping_record)
      except Exception as e:
          continue
  return processed_data

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

def data_import_page():
  """数据导入页面"""
  st.header("📥 数据导入")
  
  # 创建标签页
  tab1, tab2, tab3, tab4 = st.tabs(["📊 财务系统数据", "📋 实物台账数据", "🔗 对应关系数据", "📋 查看模板格式"])
  
  with tab1:
      st.subheader("财务系统数据导入")
      financial_file = st.file_uploader("选择财务系统Excel文件", type=['xlsx', 'xls'], key="financial")
      
      if financial_file is not None:
          try:
              df = pd.read_excel(financial_file)
              st.success("✅ 文件上传成功！")
              st.write("数据预览：")
              st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入财务数据", type="primary"):
                  # 验证和导入数据
                  success_data, failed_data, error_summary = validate_and_import_financial_data(df)
                  
                  if success_data:
                      save_data(success_data, FINANCIAL_DATA_FILE)
                      st.success(f"✅ 成功导入 {len(success_data)} 条财务数据！")
                  
                  # 显示失败数据处理
                  handle_import_errors("财务系统", failed_data, error_summary)
                  
                  if success_data:  # 只有成功导入数据时才刷新
                      st.rerun()
                      
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")
              st.info("💡 请确保文件格式正确，或尝试另存为新的Excel文件后重新上传")
  
  with tab2:
      st.subheader("实物台账数据导入")
      physical_file = st.file_uploader("选择实物台账Excel文件", type=['xlsx', 'xls'], key="physical")
      
      if physical_file is not None:
          try:
              df = pd.read_excel(physical_file)
              st.success("✅ 文件上传成功！")
              st.write("数据预览：")
              st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入实物数据", type="primary"):
                  # 验证和导入数据
                  success_data, failed_data, error_summary = validate_and_import_physical_data(df)
                  
                  if success_data:
                      save_data(success_data, PHYSICAL_DATA_FILE)
                      st.success(f"✅ 成功导入 {len(success_data)} 条实物数据！")
                  
                  # 显示失败数据处理
                  handle_import_errors("实物台账", failed_data, error_summary)
                  
                  if success_data:  # 只有成功导入数据时才刷新
                      st.rerun()
                      
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")
              st.info("💡 请确保文件格式正确，或尝试另存为新的Excel文件后重新上传")
  
  with tab3:
      st.subheader("对应关系数据导入")
      mapping_file = st.file_uploader("选择对应关系Excel文件", type=['xlsx', 'xls'], key="mapping")
      
      if mapping_file is not None:
          try:
              df = pd.read_excel(mapping_file)
              st.success("✅ 文件上传成功！")
              st.write("数据预览：")
              st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入对应关系", type="primary"):
                  # 验证和导入数据
                  success_data, failed_data, error_summary = validate_and_import_mapping_data(df)
                  
                  if success_data:
                      save_data(success_data, MAPPING_DATA_FILE)
                      st.success(f"✅ 成功导入 {len(success_data)} 条对应关系！")
                  
                  # 显示失败数据处理
                  handle_import_errors("对应关系", failed_data, error_summary)
                  
                  if success_data:  # 只有成功导入数据时才刷新
                      st.rerun()
                      
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")
              st.info("💡 请确保文件格式正确，或尝试另存为新的Excel文件后重新上传")
  
  with tab4:
      display_template_download_section()


def display_template_download_section():
  """显示模板下载区域"""
  st.subheader("📋 数据导入模板格式")
  st.info("💡 点击下载按钮获取标准格式的Excel模板，模板中已预设好所有必需的列标题，您只需填入数据即可。")
  
  # 创建三列布局
  col1, col2, col3 = st.columns(3)
  
  # 模板配置
  templates = {
      "财务系统": {
          "columns": ["财务系统编号", "资产名称", "资产分类", "资产规格", "资产价值", "累积折旧", "账面价值", "取得日期", "部门名称", "保管人", "备注"],
          "icon": "📊"
      },
      "实物台账": {
          "columns": ["固定资产编号", "固定资产名称", "固定资产类型", "规格型号", "资产价值", "累计折旧额", "入账日期", "存放部门", "地点", "使用人", "保管人", "使用状态"],
          "icon": "📋"
      },
      "对应关系": {
          "columns": ["财务系统编号", "实物台账编号", "备注"],
          "icon": "🔗"
      }
  }
  
  columns = [col1, col2, col3]
  template_names = ["财务系统", "实物台账", "对应关系"]
  
  for i, (col, template_name) in enumerate(zip(columns, template_names)):
      with col:
          template_info = templates[template_name]
          st.markdown(f"### {template_info['icon']} {template_name}数据模板")
          st.write("**包含以下字段：**")
          for field in template_info["columns"]:
              st.write(f"• {field}")
          
          # 创建模板数据
          template_df = pd.DataFrame(columns=template_info["columns"])
          
          # 下载按钮
          try:
              excel_data = create_excel_file(template_df, f"{template_name}数据模板")
              st.download_button(
                  label=f"📥 下载{template_name}模板",
                  data=excel_data,
                  file_name=f"{template_name}数据模板_{get_current_date()}.xlsx",
                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                  use_container_width=True
              )
          except Exception as e:
              # 备用CSV下载
              csv_data = template_df.to_csv(index=False, encoding='utf-8-sig')
              st.download_button(
                  label=f"📥 下载{template_name}模板(CSV)",
                  data=csv_data,
                  file_name=f"{template_name}数据模板_{get_current_date()}.csv",
                  mime="text/csv",
                  use_container_width=True
              )
  
  # 使用说明
  display_usage_instructions()
  
  # 示例数据
  display_sample_data()


def display_usage_instructions():
  """显示使用说明"""
  st.markdown("---")
  st.markdown("### 📖 使用说明")
  
  with st.expander("📋 详细使用指南", expanded=False):
      st.markdown("""
      #### 🔧 模板使用步骤：
      1. **下载模板**：点击上方对应的下载按钮获取Excel模板
      2. **填写数据**：在模板中填入您的实际数据（请勿修改列标题）
      3. **保存文件**：将填写完成的文件保存为Excel格式
      4. **导入数据**：在对应的导入标签页中上传您的文件
      
      #### 📋 数据格式说明：
      - **编号字段**：必填，建议使用唯一标识符
      - **名称字段**：必填，资产的具体名称
      - **数值字段**：支持多种格式（如：1000、1,000、1000.00）
      - **日期字段**：支持多种格式（如：2024-01-15、2024/1/15、20240115）
      - **其他字段**：可选填写，支持中英文
      
      #### ⚠️ 重要提醒：
      - 系统会自动验证数据格式并提供详细的错误报告
      - 导入失败的数据可以下载查看具体错误原因
      - 建议先用少量数据测试导入效果
      """)


def display_sample_data():
  """显示示例数据"""
  st.markdown("---")
  st.markdown("### 👀 模板数据示例")
  
  # 示例数据
  financial_sample = pd.DataFrame([
      {
          "财务系统编号": "FA001", "资产名称": "联想台式电脑", "资产分类": "电子设备",
          "资产规格": "ThinkCentre M720q", "资产价值": 4500.00, "累积折旧": 1500.00,
          "账面价值": 3000.00, "取得日期": "2023-01-15", "部门名称": "财务部",
          "保管人": "张三", "备注": "办公用电脑"
      }
  ])
  
  physical_sample = pd.DataFrame([
      {
          "固定资产编号": "PA001", "固定资产名称": "联想台式电脑", "固定资产类型": "计算机设备",
          "规格型号": "ThinkCentre M720q", "资产价值": 4500.00, "累计折旧额": 1500.00,
          "入账日期": "2023-01-15", "存放部门": "财务部", "地点": "财务部办公室",
          "使用人": "张三", "保管人": "张三", "使用状态": "正常使用"
      }
  ])
  
  mapping_sample = pd.DataFrame([
      {"财务系统编号": "FA001", "实物台账编号": "PA001", "备注": "同一台联想电脑"}
  ])
  
  example_tab1, example_tab2, example_tab3 = st.tabs(["财务系统示例", "实物台账示例", "对应关系示例"])
  
  with example_tab1:
      st.dataframe(financial_sample, use_container_width=True, hide_index=True)
  
  with example_tab2:
      st.dataframe(physical_sample, use_container_width=True, hide_index=True)
  
  with example_tab3:
      st.dataframe(mapping_sample, use_container_width=True, hide_index=True)


# ========== 数据验证函数 ==========

def validate_and_import_financial_data(df):
  """验证并导入财务系统数据"""
  return validate_data(df, {
      "required_columns": ["财务系统编号", "资产名称"],
      "numeric_columns": ["资产价值", "累积折旧", "账面价值"],
      "date_columns": ["取得日期"],
      "data_type": "财务系统"
  })

def validate_and_import_physical_data(df):
  """验证并导入实物台账数据"""
  return validate_data(df, {
      "required_columns": ["固定资产编号", "固定资产名称"],
      "numeric_columns": ["资产价值", "累计折旧额"],
      "date_columns": ["入账日期"],
      "data_type": "实物台账"
  })

def validate_and_import_mapping_data(df):
  """验证并导入对应关系数据"""
  return validate_data(df, {
      "required_columns": ["财务系统编号", "实物台账编号"],
      "numeric_columns": [],
      "date_columns": [],
      "data_type": "对应关系"
  })

def validate_data(df, config):
  """通用数据验证函数"""
  success_data = []
  failed_data = []
  error_summary = {"总行数": len(df), "成功": 0, "失败": 0, "错误类型": {}}
  
  required_columns = config["required_columns"]
  numeric_columns = config["numeric_columns"]
  date_columns = config["date_columns"]
  
  # 检查必需列是否存在
  missing_columns = [col for col in required_columns if col not in df.columns]
  if missing_columns:
      error_msg = f"缺少必需列：{', '.join(missing_columns)}"
      for idx, row in df.iterrows():
          failed_record = row.to_dict()
          failed_record['行号'] = idx + 2
          failed_record['错误原因'] = error_msg
          failed_data.append(failed_record)
      
      error_summary["失败"] = len(df)
      error_summary["错误类型"]["缺少必需列"] = len(df)
      return success_data, failed_data, error_summary
  
  # 逐行验证数据
  for idx, row in df.iterrows():
      errors = []
      excel_row = idx + 2
      
      # 验证必填字段
      for col in required_columns:
          if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
              errors.append(f"{col}不能为空")
      
      # 验证数值字段
      for col in numeric_columns:
          if col in row and not pd.isna(row[col]):
              if not is_valid_number(row[col]):
                  errors.append(f"{col}格式不正确，应为数值")
      
      # 验证日期字段
      for col in date_columns:
          if col in row and not pd.isna(row[col]):
              if not is_valid_date(row[col]):
                  errors.append(f"{col}格式不正确，建议使用YYYY-MM-DD格式")
      
      # 处理验证结果
      if errors:
          failed_record = row.to_dict()
          failed_record['行号'] = excel_row
          failed_record['错误原因'] = "; ".join(errors)
          failed_data.append(failed_record)
          
          error_summary["失败"] += 1
          for error in errors:
              error_type = error.split("不能为空")[0] if "不能为空" in error else error.split("格式不正确")[0] if "格式不正确" in error else "其他错误"
              error_summary["错误类型"][error_type] = error_summary["错误类型"].get(error_type, 0) + 1
      else:
          clean_record = clean_record_data(row, numeric_columns, date_columns)
          success_data.append(clean_record)
          error_summary["成功"] += 1
  
  return success_data, failed_data, error_summary

def handle_import_errors(data_type, failed_data, error_summary):
  """处理导入错误，显示错误信息并提供下载"""
  if failed_data:
      st.error(f"❌ {data_type}数据导入部分失败")
      
      # 显示错误汇总
      col1, col2, col3 = st.columns(3)
      with col1:
          st.metric("总行数", error_summary["总行数"])
      with col2:
          st.metric("成功导入", error_summary["成功"], delta=f"+{error_summary['成功']}")
      with col3:
          st.metric("导入失败", error_summary["失败"], delta=f"-{error_summary['失败']}")
      
      # 显示错误类型统计
      if error_summary["错误类型"]:
          st.write("**错误类型统计：**")
          error_df = pd.DataFrame(list(error_summary["错误类型"].items()), 
                                columns=["错误类型", "数量"])
          st.dataframe(error_df, use_container_width=True, hide_index=True)
      
      # 显示失败数据详情
      with st.expander(f"📋 查看失败数据详情 ({len(failed_data)} 条)", expanded=False):
          failed_df = pd.DataFrame(failed_data)
          st.dataframe(failed_df, use_container_width=True, hide_index=True)
      
      # 提供失败数据下载
      failed_df = pd.DataFrame(failed_data)
      
      # Excel下载
      try:
          excel_data = create_excel_file(failed_df, f"{data_type}导入失败数据")
          st.download_button(
              label=f"📥 下载失败数据 (Excel格式)",
              data=excel_data,
              file_name=f"{data_type}_导入失败数据_{get_current_date()}.xlsx",
              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              use_container_width=True
          )
      except:
          # 备用CSV下载
          csv_data = failed_df.to_csv(index=False, encoding='utf-8-sig')
          st.download_button(
              label=f"📥 下载失败数据 (CSV格式)",
              data=csv_data,
              file_name=f"{data_type}_导入失败数据_{get_current_date()}.csv",
              mime="text/csv",
              use_container_width=True
          )
      
      st.info("💡 请修正失败数据中的错误后重新导入")
  else:
      if error_summary["成功"] > 0:
          st.success(f"🎉 {data_type}数据全部导入成功！")


# ========== 辅助函数 ==========

def get_current_date():
  """获取当前日期字符串"""
  try:
      from datetime import datetime
      return datetime.now().strftime('%Y%m%d')
  except:
      return "20240101"

def is_valid_number(value):
  """验证是否为有效数字"""
  if pd.isna(value):
      return True
  try:
      value_str = str(value).replace(",", "").replace("￥", "").replace("¥", "").strip()
      if value_str and value_str != "":
          float(value_str)
      return True
  except (ValueError, TypeError):
      return False

def is_valid_date(date_value):
  """验证是否为有效日期"""
  if pd.isna(date_value):
      return True
  
  date_str = str(date_value).strip()
  if not date_str:
      return True
  
  # 尝试多种日期格式
  date_formats = [
      "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d",
      "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
      "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y"
  ]
  
  for fmt in date_formats:
      try:
          pd.to_datetime(date_str, format=fmt)
          return True
      except:
          continue
  
  try:
      pd.to_datetime(date_str)
      return True
  except:
      return False

def clean_record_data(row, numeric_columns, date_columns):
  """清洗记录数据"""
  clean_record = {}
  
  # 处理所有字段
  for col, value in row.items():
      if col in numeric_columns:
          # 数值字段清洗
          try:
              if not pd.isna(value):
                  value_str = str(value).replace(",", "").replace("￥", "").replace("¥", "").strip()
                  clean_record[col] = float(value_str) if value_str else 0.0
              else:
                  clean_record[col] = 0.0
          except:
              clean_record[col] = 0.0
      elif col in date_columns:
          # 日期字段清洗
          try:
              if not pd.isna(value):
                  date_str = str(value).strip()
                  if date_str:
                      parsed_date = pd.to_datetime(date_str)
                      clean_record[col] = parsed_date.strftime("%Y-%m-%d")
                  else:
                      clean_record[col] = ""
              else:
                  clean_record[col] = ""
          except:
              clean_record[col] = str(value) if not pd.isna(value) else ""
      else:
          # 字符串字段
          clean_record[col] = str(value).strip() if not pd.isna(value) else ""
  
  return clean_record

def create_excel_file(df, sheet_name):
  """创建Excel文件"""
  from io import BytesIO
  
  output = BytesIO()
  
  # 尝试使用openpyxl
  try:
      with pd.ExcelWriter(output, engine='openpyxl') as writer:
          df.to_excel(writer, sheet_name=sheet_name, index=False)
      return output.getvalue()
  except ImportError:
      pass
  
  # 备用：使用xlsxwriter
  try:
      import xlsxwriter
      with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
          df.to_excel(writer, sheet_name=sheet_name, index=False)
          
          # 简单格式化
          workbook = writer.book
          worksheet = writer.sheets[sheet_name]
          
          # 设置标题行格式
          header_format = workbook.add_format({
              'bold': True,
              'fg_color': '#4CAF50',
              'font_color': 'white',
              'border': 1
          })
          
          # 应用标题格式
          for col_num, value in enumerate(df.columns.values):
              worksheet.write(0, col_num, value, header_format)
          
          # 自动调整列宽
          for i, col in enumerate(df.columns):
              max_len = max(len(str(col)), 12)
              worksheet.set_column(i, i, min(max_len, 30))
      
      return output.getvalue()
  except ImportError:
      raise Exception("需要安装 openpyxl 或 xlsxwriter 库")
def create_financial_template(with_sample=False):
  """创建财务系统数据模板"""
  columns = [  
      "财务系统编号", "资产名称", "资产分类", "资产规格", 
      "资产价值", "累积折旧", "账面价值", "取得日期", 
      "部门名称", "保管人", "备注"
  ]
  
  if with_sample:
      # 创建示例数据
      sample_data = [
          {
              "财务系统编号": "FA001",
              "资产名称": "联想台式电脑",
              "资产分类": "电子设备",
              "资产规格": "ThinkCentre M720q",
              "资产价值": 4500.00,
              "累积折旧": 1500.00,
              "账面价值": 3000.00,
              "取得日期": "2023-01-15",
              "部门名称": "财务部",
              "保管人": "张三",
              "备注": "办公用电脑"
          },
          {
              "财务系统编号": "FA002",
              "资产名称": "惠普激光打印机",
              "资产分类": "办公设备",
              "资产规格": "LaserJet Pro M404n",
              "资产价值": 1200.00,
              "累积折旧": 400.00,
              "账面价值": 800.00,
              "取得日期": "2023-03-20",
              "部门名称": "行政部",
              "保管人": "李四",
              "备注": "公共打印设备"
          }
      ]
      return pd.DataFrame(sample_data)
  else:
      # 创建空模板
      return pd.DataFrame(columns=columns)

def create_physical_template(with_sample=False):
  """创建实物台账数据模板"""
  columns = [
      "固定资产编号", "固定资产名称", "固定资产类型", "规格型号",
      "资产价值", "累计折旧额", "入账日期", "存放部门",
      "地点", "使用人", "保管人", "使用状态"
  ]
  
  if with_sample:
      # 创建示例数据
      sample_data = [
          {
              "固定资产编号": "PA001",
              "固定资产名称": "联想台式电脑",
              "固定资产类型": "计算机设备",
              "规格型号": "ThinkCentre M720q",
              "资产价值": 4500.00,
              "累计折旧额": 1500.00,
              "入账日期": "2023-01-15",
              "存放部门": "财务部",
              "地点": "财务部办公室",
              "使用人": "张三",
              "保管人": "张三",
              "使用状态": "正常使用"
          },
          {
              "固定资产编号": "PA002",
              "固定资产名称": "惠普激光打印机",
              "固定资产类型": "办公设备",
              "规格型号": "LaserJet Pro M404n",
              "资产价值": 1200.00,
              "累计折旧额": 400.00,
              "入账日期": "2023-03-20",
              "存放部门": "行政部",
              "地点": "行政部打印室",
              "使用人": "全体员工",
              "保管人": "李四",
              "使用状态": "正常使用"
          }
      ]
      return pd.DataFrame(sample_data)
  else:
      # 创建空模板
      return pd.DataFrame(columns=columns)

def create_mapping_template(with_sample=False):
  """创建对应关系数据模板"""
  columns = ["财务系统编号", "实物台账编号", "备注"]
  
  if with_sample:
      # 创建示例数据
      sample_data = [
          {
              "财务系统编号": "FA001",
              "实物台账编号": "PA001",
              "备注": "同一台联想电脑"
          },
          {
              "财务系统编号": "FA002",
              "实物台账编号": "PA002",
              "备注": "同一台惠普打印机"
          }
      ]
      return pd.DataFrame(sample_data)
  else:
      # 创建空模板
      return pd.DataFrame(columns=columns)

def create_excel_download(df, sheet_name):
  """创建Excel文件用于下载"""
  try:
      from io import BytesIO
      
      # 优先尝试使用openpyxl（更稳定）
      try:
          output = BytesIO()
          with pd.ExcelWriter(output, engine='openpyxl') as writer:
              df.to_excel(writer, sheet_name=sheet_name, index=False)
          processed_data = output.getvalue()
          return processed_data
      except ImportError:
          pass
      
      # 备用方案：使用xlsxwriter
      try:
          import xlsxwriter
          output = BytesIO()
          
          with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
              # 写入数据
              df.to_excel(writer, sheet_name=sheet_name, index=False)
              
              # 获取工作簿和工作表对象
              workbook = writer.book
              worksheet = writer.sheets[sheet_name]
              
              # 设置标题行格式
              header_format = workbook.add_format({
                  'bold': True,
                  'text_wrap': True,
                  'valign': 'top',
                  'fg_color': '#4CAF50',
                  'font_color': 'white',
                  'border': 1
              })
              
              # 应用格式到标题行
              for col_num, value in enumerate(df.columns.values):
                  worksheet.write(0, col_num, value, header_format)
              
              # 设置列宽
              for i, col in enumerate(df.columns):
                  # 根据列名长度调整列宽
                  max_len = max(len(str(col)), 12)  # 最小宽度12
                  if '编号' in col:
                      max_len = max(max_len, 15)
                  elif '名称' in col:
                      max_len = max(max_len, 20)
                  elif '价值' in col or '折旧' in col:
                      max_len = max(max_len, 12)
                  elif '日期' in col:
                      max_len = max(max_len, 12)
                  
                  worksheet.set_column(i, i, min(max_len, 30))  # 最大宽度30
              
              # 冻结标题行
              worksheet.freeze_panes(1, 0)
          
          processed_data = output.getvalue()
          return processed_data
          
      except ImportError:
          # 最后备用方案：抛出异常，让调用者处理
          raise Exception("需要安装 openpyxl 或 xlsxwriter 库来生成Excel文件")
          
  except Exception as e:
      # 如果所有Excel方案都失败，抛出异常
      raise Exception(f"Excel文件生成失败：{str(e)}")
def all_data_view_page():
  """查看全部对应关系页面"""
  st.header("📋 全部资产对应关系")
  
  # 加载数据
  financial_data = load_data(FINANCIAL_DATA_FILE)
  physical_data = load_data(PHYSICAL_DATA_FILE)
  mapping_data = load_data(MAPPING_DATA_FILE)
  
  if not all([financial_data, physical_data, mapping_data]):
      st.warning("⚠️ 请先导入所有必要的数据")
      return
  
  # 选择查看模式
  view_mode = st.selectbox("选择查看模式", ["财务系统明细", "实物台账明细", "对应关系汇总"])
  
  if view_mode == "财务系统明细":
      # 显示财务系统汇总
      show_financial_summary(financial_data)
      
      st.markdown("---")
      st.subheader("📊 财务系统-资产明细账")
      st.info("💡 点击下方表格中的复选框选择资产，支持多选。系统将为每个选中的资产显示对应的实物资产信息")
      
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
      
      # 显示数据表格 - 使用st.data_editor实现行选择
      if len(df) > 0:
          # 添加选择列
          df_display = df.copy()
          df_display.insert(0, "选择", False)
          
          # 使用data_editor显示可编辑表格
          edited_df = st.data_editor(
              df_display, 
              use_container_width=True, 
              hide_index=True,
              column_config={
                  "选择": st.column_config.CheckboxColumn(
                      "选择",
                      help="选择要查看对应关系的资产（支持多选）",
                      default=False,
                  )
              },
              disabled=[col for col in df_display.columns if col != "选择"]
          )
          
          # 检查是否有选中的行
          selected_rows = edited_df[edited_df["选择"] == True]
          
          if len(selected_rows) > 0:
              st.success(f"✅ 已选择 {len(selected_rows)} 个资产")
              
              # 创建选择显示方式的选项
              if len(selected_rows) > 1:
                  display_option = st.radio(
                      "选择显示方式：",
                      ["标签页显示（推荐）", "列表显示", "对比显示"],
                      horizontal=True
                  )
              else:
                  display_option = "标签页显示（推荐）"
              
              # 根据选择的显示方式展示结果
              if display_option == "标签页显示（推荐）":
                  # 为每个选中的资产创建标签页
                  tab_names = []
                  for idx, (_, row) in enumerate(selected_rows.iterrows()):
                      asset_name = row['资产名称']
                      if len(asset_name) > 10:
                          asset_name = asset_name[:10] + "..."
                      tab_names.append(f"{row['财务系统编号']} - {asset_name}")
                  
                  tabs = st.tabs(tab_names)
                  
                  for tab_idx, (tab, (_, selected_financial)) in enumerate(zip(tabs, selected_rows.iterrows())):
                      with tab:
                          financial_code = selected_financial['财务系统编号']
                          
                          # 查找对应的实物资产
                          corresponding_asset = None
                          physical_code = None
                          
                          # 在映射数据中查找对应关系
                          for mapping in mapping_data:
                              if mapping.get("财务系统编号") == financial_code:
                                  physical_code = mapping.get("实物台账编号")
                                  # 在实物数据中查找对应资产
                                  for physical in physical_data:
                                      if physical.get("固定资产编号") == physical_code:
                                          corresponding_asset = physical
                                          break
                                  break
                          
                          if corresponding_asset:
                              st.success(f"✅ 找到对应的实物资产：{physical_code}")
                              
                              # 显示对比信息
                              col1, col2 = st.columns(2)
                              
                              with col1:
                                  st.markdown("### 📊 财务系统信息")
                                  display_financial_info(selected_financial)
                              
                              with col2:
                                  st.markdown("### 📋 实物台账信息")
                                  display_physical_info(corresponding_asset)
                              
                              # 差异分析
                              st.markdown("### 📊 差异分析")
                              display_difference_analysis(selected_financial, corresponding_asset)
                          else:
                              st.error(f"❌ 未找到财务编号 {financial_code} 对应的实物资产")
              
              elif display_option == "列表显示":
                  for idx, (_, selected_financial) in enumerate(selected_rows.iterrows()):
                      with st.expander(f"📊 资产 {idx+1}: {selected_financial['财务系统编号']} - {selected_financial['资产名称']}", expanded=idx==0):
                          financial_code = selected_financial['财务系统编号']
                          
                          # 查找对应的实物资产
                          corresponding_asset = None
                          physical_code = None
                          
                          # 在映射数据中查找对应关系
                          for mapping in mapping_data:
                              if mapping.get("财务系统编号") == financial_code:
                                  physical_code = mapping.get("实物台账编号")
                                  # 在实物数据中查找对应资产
                                  for physical in physical_data:
                                      if physical.get("固定资产编号") == physical_code:
                                          corresponding_asset = physical
                                          break
                                  break
                          
                          if corresponding_asset:
                              st.success(f"✅ 找到对应的实物资产：{physical_code}")
                              
                              # 显示对比信息
                              col1, col2 = st.columns(2)
                              
                              with col1:
                                  st.markdown("#### 📊 财务系统信息")
                                  display_financial_info(selected_financial)
                              
                              with col2:
                                  st.markdown("#### 📋 实物台账信息")
                                  display_physical_info(corresponding_asset)
                              
                              # 差异分析
                              st.markdown("#### 📊 差异分析")
                              display_difference_analysis(selected_financial, corresponding_asset)
                          else:
                              st.error(f"❌ 未找到财务编号 {financial_code} 对应的实物资产")
              
              else:  # 对比显示
                  if len(selected_rows) <= 5:  # 限制对比数量
                      st.markdown("### 📊 多资产对比")
                      
                      # 创建对比表格
                      comparison_data = []
                      for _, selected_financial in selected_rows.iterrows():
                          financial_code = selected_financial['财务系统编号']
                          
                          # 查找对应的实物资产
                          corresponding_asset = None
                          physical_code = None
                          
                          # 在映射数据中查找对应关系
                          for mapping in mapping_data:
                              if mapping.get("财务系统编号") == financial_code:
                                  physical_code = mapping.get("实物台账编号")
                                  # 在实物数据中查找对应资产
                                  for physical in physical_data:
                                      if physical.get("固定资产编号") == physical_code:
                                          corresponding_asset = physical
                                          break
                                  break
                          
                          if corresponding_asset:
                              financial_value = selected_financial.get('资产价值', 0)
                              physical_value = corresponding_asset.get('资产价值', 0)
                              comparison_data.append({
                                  "财务编号": financial_code,
                                  "实物编号": physical_code,
                                  "资产名称": selected_financial.get('资产名称', ''),
                                  "财务价值": financial_value,
                                  "实物价值": physical_value,
                                  "价值差异": financial_value - physical_value,
                                  "财务部门": selected_financial.get('部门名称', ''),
                                  "实物部门": corresponding_asset.get('存放部门', ''),
                                  "状态": "✅ 匹配" if abs(financial_value - physical_value) < 0.01 else "⚠️ 差异"
                              })
                          else:
                              financial_value = selected_financial.get('资产价值', 0)
                              comparison_data.append({
                                  "财务编号": financial_code,
                                  "实物编号": "未找到",
                                  "资产名称": selected_financial.get('资产名称', ''),
                                  "财务价值": financial_value,
                                  "实物价值": 0,
                                  "价值差异": financial_value,
                                  "财务部门": selected_financial.get('部门名称', ''),
                                  "实物部门": "无",
                                  "状态": "❌ 未匹配"
                              })
                      
                      if comparison_data:
                          comparison_df = pd.DataFrame(comparison_data)
                          st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                          
                          # 汇总统计
                          col1, col2, col3, col4 = st.columns(4)
                          with col1:
                              matched_count = len([d for d in comparison_data if "匹配" in d["状态"]])
                              st.metric("匹配数量", f"{matched_count}/{len(comparison_data)}")
                          with col2:
                              total_financial = sum(d["财务价值"] for d in comparison_data)
                              st.metric("财务总值", f"¥{total_financial:,.2f}")
                          with col3:
                              total_physical = sum(d["实物价值"] for d in comparison_data)
                              st.metric("实物总值", f"¥{total_physical:,.2f}")
                          with col4:
                              total_diff = sum(d["价值差异"] for d in comparison_data)
                              st.metric("总差异", f"¥{total_diff:,.2f}")
                  else:
                      st.warning("⚠️ 对比显示最多支持5个资产，请减少选择数量或使用其他显示方式")
          else:
              st.info("👆 请在上方表格中勾选要查看的资产")
      else:
          st.info("没有找到符合条件的财务资产")
  
  elif view_mode == "实物台账明细":
      # 显示实物台账汇总
      show_physical_summary(physical_data)
      
      st.markdown("---")
      st.subheader("📋 实物台账明细")
      st.info("💡 点击下方表格中的复选框选择资产，支持多选。系统将为每个选中的资产显示对应的财务系统信息")
      
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
      
      # 显示数据表格 - 使用st.data_editor实现行选择
      if len(df) > 0:
          # 添加选择列
          df_display = df.copy()
          df_display.insert(0, "选择", False)
          
          # 使用data_editor显示可编辑表格
          edited_df = st.data_editor(
              df_display, 
              use_container_width=True, 
              hide_index=True,
              column_config={
                  "选择": st.column_config.CheckboxColumn(
                      "选择",
                      help="选择要查看对应关系的资产（支持多选）",
                      default=False,
                  )
              },
              disabled=[col for col in df_display.columns if col != "选择"]
          )
          
          # 检查是否有选中的行
          selected_rows = edited_df[edited_df["选择"] == True]
          
          if len(selected_rows) > 0:
              st.success(f"✅ 已选择 {len(selected_rows)} 个资产")
              
              # 创建选择显示方式的选项
              if len(selected_rows) > 1:
                  display_option = st.radio(
                      "选择显示方式：",
                      ["标签页显示（推荐）", "列表显示"],
                      horizontal=True,
                      key="physical_display_option"
                  )
              else:
                  display_option = "标签页显示（推荐）"
              
              # 根据选择的显示方式展示结果
              if display_option == "标签页显示（推荐）":
                  # 为每个选中的资产创建标签页
                  tab_names = []
                  for idx, (_, row) in enumerate(selected_rows.iterrows()):
                      asset_name = row['固定资产名称']
                      if len(asset_name) > 10:
                          asset_name = asset_name[:10] + "..."
                      tab_names.append(f"{row['固定资产编号']} - {asset_name}")
                  
                  tabs = st.tabs(tab_names)
                  
                  for tab_idx, (tab, (_, selected_physical)) in enumerate(zip(tabs, selected_rows.iterrows())):
                      with tab:
                          physical_code = selected_physical['固定资产编号']
                          
                          # 查找对应的财务资产
                          corresponding_asset = None
                          financial_code = None
                          
                          # 在映射数据中查找对应关系
                          for mapping in mapping_data:
                              if mapping.get("实物台账编号") == physical_code:
                                  financial_code = mapping.get("财务系统编号")
                                  # 在财务数据中查找对应资产
                                  for financial in financial_data:
                                      if financial.get("财务系统编号") == financial_code:
                                          corresponding_asset = financial
                                          break
                                  break
                          
                          if corresponding_asset:
                              st.success(f"✅ 找到对应的财务资产：{financial_code}")
                              
                              # 显示对比信息
                              col1, col2 = st.columns(2)
                              
                              with col1:
                                  st.markdown("### 📋 实物台账信息")
                                  display_physical_info(selected_physical)
                              
                              with col2:
                                  st.markdown("### 📊 财务系统信息")
                                  display_financial_info(corresponding_asset)
                              
                              # 差异分析
                              st.markdown("### 📊 差异分析")
                              display_difference_analysis(corresponding_asset, selected_physical, reverse=True)
                          else:
                              st.error(f"❌ 未找到实物编号 {physical_code} 对应的财务资产")
              
              else:  # 列表显示
                  for idx, (_, selected_physical) in enumerate(selected_rows.iterrows()):
                      with st.expander(f"📋 资产 {idx+1}: {selected_physical['固定资产编号']} - {selected_physical['固定资产名称']}", expanded=idx==0):
                          physical_code = selected_physical['固定资产编号']
                          
                          # 查找对应的财务资产
                          corresponding_asset = None
                          financial_code = None
                          
                          # 在映射数据中查找对应关系
                          for mapping in mapping_data:
                              if mapping.get("实物台账编号") == physical_code:
                                  financial_code = mapping.get("财务系统编号")
                                  # 在财务数据中查找对应资产
                                  for financial in financial_data:
                                      if financial.get("财务系统编号") == financial_code:
                                          corresponding_asset = financial
                                          break
                                  break
                          
                          if corresponding_asset:
                              st.success(f"✅ 找到对应的财务资产：{financial_code}")
                              
                              # 显示对比信息
                              col1, col2 = st.columns(2)
                              
                              with col1:
                                  st.markdown("#### 📋 实物台账信息")
                                  display_physical_info(selected_physical)
                              
                              with col2:
                                  st.markdown("#### 📊 财务系统信息")
                                  display_financial_info(corresponding_asset)
                              
                              # 差异分析
                              st.markdown("#### 📊 差异分析")
                              display_difference_analysis(corresponding_asset, selected_physical, reverse=True)
                          else:
                              st.error(f"❌ 未找到实物编号 {physical_code} 对应的财务资产")
          else:
              st.info("👆 请在上方表格中勾选要查看的资产")
      else:
          st.info("没有找到符合条件的实物资产")
  
  else:  # 对应关系汇总
      st.subheader("🔗 完整对应关系汇总")
      
      # 构建完整的对应关系表
      mapping_summary = []
      for mapping in mapping_data:
          financial_record = next((f for f in financial_data if f.get("财务系统编号") == mapping.get("财务系统编号")), {})
          physical_record = next((p for p in physical_data if p.get("固定资产编号") == mapping.get("实物台账编号")), {})
          
          if financial_record and physical_record:
              financial_value = financial_record.get("资产价值", 0)
              physical_value = physical_record.get("资产价值", 0)
              summary_record = {
                  "财务系统编号": mapping.get("财务系统编号", ""),
                  "实物台账编号": mapping.get("实物台账编号", ""),
                  "财务-资产名称": financial_record.get("资产名称", ""),
                  "实物-资产名称": physical_record.get("固定资产名称", ""),
                  "财务-价值": financial_value,
                  "实物-价值": physical_value,
                  "价值差异": financial_value - physical_value,
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
          
          # 导出功能
          csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
          st.download_button(
              label="📥 导出对应关系表",
              data=csv,
              file_name=f"资产对应关系_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
              mime="text/csv"
          )
      else:
          st.info("暂无完整的对应关系数据")


# 辅助函数
def display_financial_info(financial_asset):
  """显示财务系统信息"""
  st.write(f"**编号**：{financial_asset.get('财务系统编号', 'N/A')}")
  st.write(f"**名称**：{financial_asset.get('资产名称', 'N/A')}")
  st.write(f"**分类**：{financial_asset.get('资产分类', 'N/A')}")
  st.write(f"**规格**：{financial_asset.get('资产规格', 'N/A')}")
  st.write(f"**价值**：¥{financial_asset.get('资产价值', 0):,.2f}")
  st.write(f"**累积折旧**：¥{financial_asset.get('累积折旧', 0):,.2f}")
  st.write(f"**账面价值**：¥{financial_asset.get('账面价值', 0):,.2f}")
  st.write(f"**取得日期**：{financial_asset.get('取得日期', 'N/A')}")
  st.write(f"**部门**：{financial_asset.get('部门名称', 'N/A')}")
  st.write(f"**保管人**：{financial_asset.get('保管人', 'N/A')}")
  st.write(f"**备注**：{financial_asset.get('备注', 'N/A')}")

def display_physical_info(physical_asset):
  """显示实物台账信息"""
  st.write(f"**编号**：{physical_asset.get('固定资产编号', 'N/A')}")
  st.write(f"**名称**：{physical_asset.get('固定资产名称', 'N/A')}")
  st.write(f"**类型**：{physical_asset.get('固定资产类型', 'N/A')}")
  st.write(f"**规格**：{physical_asset.get('规格型号', 'N/A')}")
  st.write(f"**价值**：¥{physical_asset.get('资产价值', 0):,.2f}")
  st.write(f"**累计折旧**：¥{physical_asset.get('累计折旧额', 0):,.2f}")
  asset_value = physical_asset.get('资产价值', 0)
  depreciation = physical_asset.get('累计折旧额', 0)
  net_value = asset_value - depreciation
  st.write(f"**净值**：¥{net_value:,.2f}")
  st.write(f"**入账日期**：{physical_asset.get('入账日期', 'N/A')}")
  st.write(f"**存放部门**：{physical_asset.get('存放部门', 'N/A')}")
  st.write(f"**地点**：{physical_asset.get('地点', 'N/A')}")
  st.write(f"**使用人**：{physical_asset.get('使用人', 'N/A')}")
  st.write(f"**保管人**：{physical_asset.get('保管人', 'N/A')}")
  st.write(f"**使用状态**：{physical_asset.get('使用状态', 'N/A')}")

def display_difference_analysis(financial_asset, physical_asset, reverse=False):
  """显示差异分析"""
  financial_value = financial_asset.get('资产价值', 0)
  physical_value = physical_asset.get('资产价值', 0)
  financial_depreciation = financial_asset.get('累积折旧', 0)
  physical_depreciation = physical_asset.get('累计折旧额', 0)
  financial_dept = financial_asset.get('部门名称', '')
  physical_dept = physical_asset.get('存放部门', '')
  
  if reverse:
      # 实物台账视角
      value_diff = physical_value - financial_value
      depreciation_diff = physical_depreciation - financial_depreciation
  else:
      # 财务系统视角
      value_diff = financial_value - physical_value
      depreciation_diff = financial_depreciation - physical_depreciation
  
  dept_match = financial_dept == physical_dept
  
  col1, col2, col3 = st.columns(3)
  with col1:
      if abs(value_diff) > 0.01:
          st.error(f"价值差异：¥{value_diff:,.2f}")
      else:
          st.success("✅ 价值一致")
  
  with col2:
      if abs(depreciation_diff) > 0.01:
          st.error(f"折旧差异：¥{depreciation_diff:,.2f}")
      else:
          st.success("✅ 折旧一致")
  
  with col3:
      if not dept_match:
          st.warning("⚠️ 部门不一致")
      else:
          st.success("✅ 部门一致")
def mapping_query_page():
  """映射关系查询页面"""
  st.header("🔍 资产映射关系查询")
  
  # 加载数据
  financial_data = load_data(FINANCIAL_DATA_FILE)
  physical_data = load_data(PHYSICAL_DATA_FILE)
  mapping_data = load_data(MAPPING_DATA_FILE)
  
  if not all([financial_data, physical_data, mapping_data]):
      st.warning("⚠️ 请先导入所有必要的数据（财务系统、实物台账、关系对照表）")
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
                  physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), None)
                  
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
                  financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), None)
                  
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
                  physical_record = next((p for p in physical_data if p["固定资产编号"] == mapping["实物台账编号"]), None)
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
                  financial_record = next((f for f in financial_data if f["财务系统编号"] == mapping["财务系统编号"]), None)
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
              with st.expander(f"📌 记录 {idx + 1}"):
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

def data_statistics_page():
  """数据统计分析页面"""
  st.header("📊 数据统计分析")
  
  # 加载数据
  financial_data = load_data(FINANCIAL_DATA_FILE)
  physical_data = load_data(PHYSICAL_DATA_FILE)
  mapping_data = load_data(MAPPING_DATA_FILE)
  
  if not all([financial_data, physical_data, mapping_data]):
      st.warning("⚠️ 请先导入所有必要的数据")
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
  
  # 未匹配资产列表
  st.subheader("⚠️ 未匹配资产")
  
  tab1, tab2 = st.tabs(["财务系统未匹配", "实物台账未匹配"])
  
  with tab1:
      unmatched_financial = [f for f in financial_data if f["财务系统编号"] not in financial_mapped]
      if unmatched_financial:
          st.warning(f"发现 {len(unmatched_financial)} 项财务资产未建立映射关系")
          
          # 创建DataFrame显示
          df_unmatched = pd.DataFrame(unmatched_financial)
          display_cols = ["财务系统编号", "资产名称", "资产分类", "资产价值", "部门名称"]
          df_display = df_unmatched[display_cols]
          
          st.dataframe(df_display, use_container_width=True, hide_index=True)
          
          # 导出功能
          csv = df_display.to_csv(index=False, encoding='utf-8-sig')
          st.download_button(
              label="📥 导出未匹配财务资产",
              data=csv,
              file_name=f"未匹配财务资产_{datetime.now().strftime('%Y%m%d')}.csv",
              mime="text/csv"
          )
      else:
          st.success("✅ 所有财务资产都已建立映射关系")
  
  with tab2:
      unmatched_physical = [p for p in physical_data if p["固定资产编号"] not in physical_mapped]
      if unmatched_physical:
          st.warning(f"发现 {len(unmatched_physical)} 项实物资产未建立映射关系")
          
          # 创建DataFrame显示
          df_unmatched = pd.DataFrame(unmatched_physical)
          display_cols = ["固定资产编号", "固定资产名称", "固定资产类型", "资产价值", "存放部门"]
          df_display = df_unmatched[display_cols]
          
          st.dataframe(df_display, use_container_width=True, hide_index=True)
          
          # 导出功能
          csv = df_display.to_csv(index=False, encoding='utf-8-sig')
          st.download_button(
              label="📥 导出未匹配实物资产",
              data=csv,
              file_name=f"未匹配实物资产_{datetime.now().strftime('%Y%m%d')}.csv",
              mime="text/csv"
          )
      else:
          st.success("✅ 所有实物资产都已建立映射关系")
  
  # 差异分析
  st.subheader("💰 价值差异分析")
  
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
          
          # 导出差异数据
          csv = df_diff.to_csv(index=False, encoding='utf-8-sig')
          st.download_button(
              label="📥 导出差异明细",
              data=csv,
              file_name=f"资产价值差异_{datetime.now().strftime('%Y%m%d')}.csv",
              mime="text/csv"
          )
  else:
      st.success("✅ 所有已匹配资产的价值完全一致")

def main():
  """主函数"""
  st.title("🔗 资产映射关系查询系统")
  
  # 侧边栏导航
  st.sidebar.title("导航菜单")
  page = st.sidebar.radio(
      "选择功能",
      ["数据导入", "映射关系查询", "查看全部数据", "数据统计分析"]
  )
  
  # 显示当前数据状态
  st.sidebar.markdown("---")
  st.sidebar.subheader("📊 数据状态")
  
  financial_count = len(load_data(FINANCIAL_DATA_FILE))
  physical_count = len(load_data(PHYSICAL_DATA_FILE))
  mapping_count = len(load_data(MAPPING_DATA_FILE))
  
  st.sidebar.info(f"""
  - 财务系统：{financial_count} 条
  - 实物台账：{physical_count} 条
  - 映射关系：{mapping_count} 条
  """)
  
  # 根据选择显示不同页面
  if page == "数据导入":
      data_import_page()
  elif page == "映射关系查询":
      mapping_query_page()
  elif page == "查看全部数据":
      all_data_view_page()
  elif page == "数据统计分析":
      data_statistics_page()

if __name__ == "__main__":
  main()
