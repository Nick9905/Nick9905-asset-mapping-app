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
    
 # 添加模板展示功能
def data_import_page():
    """数据导入页面"""
    st.header("📥 数据导入")
    
    # 添加模板展示功能
    with st.expander("📋 查看数据导入模板格式", expanded=False):
        st.markdown("### 📊 财务系统数据模板")
        st.markdown("**Excel列顺序要求：**")
        financial_template = pd.DataFrame({
            "A列-财务系统编号": ["FS001", "FS002", "FS003"],
            "B列-序号": ["1", "2", "3"],
            "C列-所属公司": ["公司A", "公司B", "公司C"],
            "D列-资产分类": ["电子设备", "办公设备", "运输设备"],
            "E列-资产编号": ["AS001", "AS002", "AS003"],
            "F列-资产名称": ["笔记本电脑", "办公桌", "汽车"],
            "G列-资产规格": ["联想ThinkPad", "1.2m办公桌", "奥迪A4"],
            "J列-取得日期": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Y列-资产价值": [8000.00, 1200.00, 250000.00],
            "AA列-累积折旧": [2000.00, 300.00, 50000.00],
            "AB列-账面价值": [6000.00, 900.00, 200000.00],
            "AK列-部门名称": ["IT部", "行政部", "销售部"],
            "AM列-保管人": ["张三", "李四", "王五"]
        })
        st.dataframe(financial_template, use_container_width=True)
        
        st.markdown("### 📋 实物台账数据模板")
        st.markdown("**Excel列顺序要求：**")
        physical_template = pd.DataFrame({
            "A列-所属公司": ["公司A", "公司B", "公司C"],
            "B列-一级部门": ["技术部", "行政部", "销售部"],
            "C列-固定资产编号": ["PA001", "PA002", "PA003"],
            "D列-原固定资产编号": ["OLD001", "OLD002", "OLD003"],
            "E列-固定资产类型": ["电子设备", "办公家具", "交通工具"],
            "F列-固定资产名称": ["笔记本电脑", "办公桌", "汽车"],
            "G列-规格型号": ["ThinkPad X1", "实木办公桌", "奥迪A4L"],
            "H列-存放部门": ["IT部", "行政部", "销售部"],
            "I列-地点": ["办公室A", "办公室B", "停车场"],
            "J列-使用人": ["张三", "李四", "王五"],
            "K列-保管人": ["张三", "李四", "王五"],
            "L列-实盘数量": ["1", "1", "1"],
            "N列-入账日期": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "Q列-资产价值": [8000.00, 1200.00, 250000.00],
            "U列-累计折旧额": [2000.00, 300.00, 50000.00],
            "V列-使用状态": ["正常", "正常", "正常"]
        })
        st.dataframe(physical_template, use_container_width=True)
        
        st.markdown("### 🔗 关系对照表模板")
        st.markdown("**Excel列顺序要求：**")
        mapping_template = pd.DataFrame({
            "A列-实物台账编号": ["PA001", "PA002", "PA003"],
            "B列-财务系统编号": ["FS001", "FS002", "FS003"],
            "C列-资产编号": ["AS001", "AS002", "AS003"]
        })
        st.dataframe(mapping_template, use_container_width=True)
        
        st.markdown("---")
        st.markdown("**📝 导入说明：**")
        st.markdown("""
        1. **Excel文件格式**：支持 .xlsx 和 .xls 格式
        2. **数据从第2行开始**：第1行为表头，系统会自动跳过
        3. **必填字段**：各表的编号字段不能为空
        4. **数值格式**：金额字段支持带逗号分隔符，系统会自动处理
        5. **日期格式**：建议使用 YYYY-MM-DD 格式
        6. **更新模式**：如果编号已存在，将更新该记录；如果不存在，将新增记录
        """)
    
    tab1, tab2, tab3 = st.tabs(["财务系统数据", "实物台账数据", "关系对照表"])
    
    with tab1:
        st.subheader("📊 财务系统-资产明细账")
        financial_file = st.file_uploader("上传财务系统Excel文件", type=['xlsx', 'xls'], key="financial")
        
        # 后续代码保持不变...

        
        if financial_file:
            try:
                df = pd.read_excel(financial_file)
                st.success(f"✅ 读取成功：{len(df)}行数据")
                
                with st.expander("数据预览"):
                    st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("导入财务数据", key="import_financial"):
                        with st.spinner("处理中..."):
                            processed = import_financial_data(df.iloc[1:])
                            save_data(processed, FINANCIAL_DATA_FILE)
                            st.success(f"✅ 成功导入 {len(processed)} 条财务数据")
                            st.rerun()

                with col2:
                    if st.button("更新财务数据", key="update_financial"):
                        with st.spinner("更新中..."):
                            existing_data = load_data(FINANCIAL_DATA_FILE)
                            new_data = import_financial_data(df.iloc[1:])
                            updated_data = update_financial_data(existing_data, new_data)
                            save_data(updated_data, FINANCIAL_DATA_FILE)
                            st.success(f"✅ 成功更新财务数据")
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")
    
    with tab2:
        st.subheader("📋 实物台账")
        physical_file = st.file_uploader("上传实物台账Excel文件", type=['xlsx', 'xls'], key="physical")
        
        if physical_file:
            try:
                df = pd.read_excel(physical_file)
                st.success(f"✅ 读取成功：{len(df)}行数据")
                
                with st.expander("数据预览"):
                    st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("导入实物数据", key="import_physical"):
                        with st.spinner("处理中..."):
                            processed = import_physical_data(df.iloc[1:])
                            save_data(processed, PHYSICAL_DATA_FILE)
                            st.success(f"✅ 成功导入 {len(processed)} 条实物数据")
                            st.rerun()

                with col2:
                    if st.button("更新实物数据", key="update_physical"):
                        with st.spinner("更新中..."):
                            existing_data = load_data(PHYSICAL_DATA_FILE)
                            new_data = import_physical_data(df.iloc[1:])
                            updated_data = update_physical_data(existing_data, new_data)
                            save_data(updated_data, PHYSICAL_DATA_FILE)
                            st.success(f"✅ 成功更新实物数据")
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")
    
    with tab3:
        st.subheader("🔗 关系对照表")
        mapping_file = st.file_uploader("上传关系对照表Excel文件", type=['xlsx', 'xls'], key="mapping")
        
        if mapping_file:
            try:
                df = pd.read_excel(mapping_file)
                st.success(f"✅ 读取成功：{len(df)}行数据")
                
                with st.expander("数据预览"):
                    st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("导入对照关系", key="import_mapping"):
                        with st.spinner("处理中..."):
                            processed = import_mapping_data(df.iloc[1:])
                            save_data(processed, MAPPING_DATA_FILE)
                            st.success(f"✅ 成功导入 {len(processed)} 条对照关系")
                            st.rerun()

                with col2:
                    if st.button("更新对照关系", key="update_mapping"):
                        with st.spinner("更新中..."):
                            existing_data = load_data(MAPPING_DATA_FILE)
                            new_data = import_mapping_data(df.iloc[1:])
                            updated_data = update_mapping_data(existing_data, new_data)
                            save_data(updated_data, MAPPING_DATA_FILE)
                            st.success(f"✅ 成功更新对照关系")
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ 文件处理失败：{str(e)}")

    # 导出功能部分
    st.markdown("---")
    st.subheader("📤 导出已导入数据")

    col1, col2, col3 = st.columns(3)

    with col1:
        financial_data = load_data(FINANCIAL_DATA_FILE)
        if financial_data:
            df_financial = pd.DataFrame(financial_data)
            csv_financial = df_financial.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出财务系统数据",
                data=csv_financial,
                file_name=f"财务系统数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.info(f"财务数据：{len(financial_data)} 条")
        else:
            st.info("暂无财务数据")

    with col2:
        physical_data = load_data(PHYSICAL_DATA_FILE)
        if physical_data:
            df_physical = pd.DataFrame(physical_data)
            csv_physical = df_physical.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出实物台账数据",
                data=csv_physical,
                file_name=f"实物台账数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.info(f"实物数据：{len(physical_data)} 条")
        else:
            st.info("暂无实物数据")

    with col3:
        mapping_data = load_data(MAPPING_DATA_FILE)
        if mapping_data:
            df_mapping = pd.DataFrame(mapping_data)
            csv_mapping = df_mapping.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出映射关系数据",
                data=csv_mapping,
                file_name=f"映射关系数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.info(f"映射数据：{len(mapping_data)} 条")
        else:
            st.info("暂无映射数据")


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
      st.info("💡 点击下方表格中的复选框选择资产，系统将自动显示对应的实物资产信息")
      
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
                      help="选择要查看对应关系的资产",
                      default=False,
                  )
              },
              disabled=[col for col in df_display.columns if col != "选择"]
          )
          
          # 检查是否有选中的行
          selected_rows = edited_df[edited_df["选择"] == True]
          
          if len(selected_rows) > 0:
              # 自动显示第一个选中行的对应资产信息
              selected_financial = selected_rows.iloc[0]
              financial_code = selected_financial['财务系统编号']
              
              st.success(f"✅ 已选择资产：{financial_code} - {selected_financial['资产名称']}")
              
              # 查找对应的实物资产
              corresponding_asset, physical_code = get_mapping_info(
                  financial_code, "financial", mapping_data, financial_data, physical_data
              )
              
              if corresponding_asset:
                  st.success(f"✅ 找到对应的实物资产：{physical_code}")
                  
                  # 显示对比信息
                  col1, col2 = st.columns(2)
                  
                  with col1:
                      st.markdown("### 📊 财务系统信息")
                      st.write(f"**编号**：{selected_financial['财务系统编号']}")
                      st.write(f"**名称**：{selected_financial['资产名称']}")
                      st.write(f"**分类**：{selected_financial['资产分类']}")
                      st.write(f"**规格**：{selected_financial['资产规格']}")
                      st.write(f"**价值**：¥{selected_financial['资产价值']:,.2f}")
                      st.write(f"**累积折旧**：¥{selected_financial['累积折旧']:,.2f}")
                      st.write(f"**账面价值**：¥{selected_financial['账面价值']:,.2f}")
                      st.write(f"**取得日期**：{selected_financial['取得日期']}")
                      st.write(f"**部门**：{selected_financial['部门名称']}")
                      st.write(f"**保管人**：{selected_financial['保管人']}")
                      st.write(f"**备注**：{selected_financial['备注']}")
                  
                  with col2:
                      st.markdown("### 📋 实物台账信息")
                      st.write(f"**编号**：{corresponding_asset['固定资产编号']}")
                      st.write(f"**名称**：{corresponding_asset['固定资产名称']}")
                      st.write(f"**类型**：{corresponding_asset['固定资产类型']}")
                      st.write(f"**规格**：{corresponding_asset['规格型号']}")
                      st.write(f"**价值**：¥{corresponding_asset['资产价值']:,.2f}")
                      st.write(f"**累计折旧**：¥{corresponding_asset['累计折旧额']:,.2f}")
                      net_value = corresponding_asset['资产价值'] - corresponding_asset['累计折旧额']
                      st.write(f"**净值**：¥{net_value:,.2f}")
                      st.write(f"**入账日期**：{corresponding_asset['入账日期']}")
                      st.write(f"**存放部门**：{corresponding_asset['存放部门']}")
                      st.write(f"**地点**：{corresponding_asset['地点']}")
                      st.write(f"**使用人**：{corresponding_asset['使用人']}")
                      st.write(f"**保管人**：{corresponding_asset['保管人']}")
                      st.write(f"**使用状态**：{corresponding_asset['使用状态']}")
                  
                  # 差异分析
                  st.markdown("### 📊 差异分析")
                  value_diff = selected_financial['资产价值'] - corresponding_asset['资产价值']
                  depreciation_diff = selected_financial['累积折旧'] - corresponding_asset['累计折旧额']
                  
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
                      if selected_financial['部门名称'] != corresponding_asset['存放部门']:
                          st.warning("⚠️ 部门不一致")
                      else:
                          st.success("✅ 部门一致")
              else:
                  st.error(f"❌ 未找到财务编号 {financial_code} 对应的实物资产")
          else:
              st.info("👆 请在上方表格中勾选要查看的资产")
      else:
          st.info("没有找到符合条件的财务资产")
  
  elif view_mode == "实物台账明细":
      # 显示实物台账汇总
      show_physical_summary(physical_data)
      
      st.markdown("---")
      st.subheader("📋 实物台账明细")
      st.info("💡 点击下方表格中的复选框选择资产，系统将自动显示对应的财务系统信息")
      
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
                      help="选择要查看对应关系的资产",
                      default=False,
                  )
              },
              disabled=[col for col in df_display.columns if col != "选择"]
          )
          
          # 检查是否有选中的行
          selected_rows = edited_df[edited_df["选择"] == True]
          
          if len(selected_rows) > 0:
              # 自动显示第一个选中行的对应资产信息
              selected_physical = selected_rows.iloc[0]
              physical_code = selected_physical['固定资产编号']
              
              st.success(f"✅ 已选择资产：{physical_code} - {selected_physical['固定资产名称']}")
              
              # 查找对应的财务资产
              corresponding_asset, financial_code = get_mapping_info(
                  physical_code, "physical", mapping_data, financial_data, physical_data
              )
              
              if corresponding_asset:
                  st.success(f"✅ 找到对应的财务资产：{financial_code}")
                  
                  # 显示对比信息
                  col1, col2 = st.columns(2)
                  
                  with col1:
                      st.markdown("### 📋 实物台账信息")
                      st.write(f"**编号**：{selected_physical['固定资产编号']}")
                      st.write(f"**名称**：{selected_physical['固定资产名称']}")
                      st.write(f"**类型**：{selected_physical['固定资产类型']}")
                      st.write(f"**规格**：{selected_physical['规格型号']}")
                      st.write(f"**价值**：¥{selected_physical['资产价值']:,.2f}")
                      st.write(f"**累计折旧**：¥{selected_physical['累计折旧额']:,.2f}")
                      net_value = selected_physical['资产价值'] - selected_physical['累计折旧额']
                      st.write(f"**净值**：¥{net_value:,.2f}")
                      st.write(f"**入账日期**：{selected_physical['入账日期']}")
                      st.write(f"**存放部门**：{selected_physical['存放部门']}")
                      st.write(f"**地点**：{selected_physical['地点']}")
                      st.write(f"**使用人**：{selected_physical['使用人']}")
                      st.write(f"**保管人**：{selected_physical['保管人']}")
                      st.write(f"**使用状态**：{selected_physical['使用状态']}")
                  
                  with col2:
                      st.markdown("### 📊 财务系统信息")
                      st.write(f"**编号**：{corresponding_asset['财务系统编号']}")
                      st.write(f"**名称**：{corresponding_asset['资产名称']}")
                      st.write(f"**分类**：{corresponding_asset['资产分类']}")
                      st.write(f"**规格**：{corresponding_asset['资产规格']}")
                      st.write(f"**价值**：¥{corresponding_asset['资产价值']:,.2f}")
                      st.write(f"**累积折旧**：¥{corresponding_asset['累积折旧']:,.2f}")
                      st.write(f"**账面价值**：¥{corresponding_asset['账面价值']:,.2f}")
                      st.write(f"**取得日期**：{corresponding_asset['取得日期']}")
                      st.write(f"**部门**：{corresponding_asset['部门名称']}")
                      st.write(f"**保管人**：{corresponding_asset['保管人']}")
                      st.write(f"**备注**：{corresponding_asset['备注']}")
                  
                  # 差异分析
                  st.markdown("### 📊 差异分析")
                  value_diff = selected_physical['资产价值'] - corresponding_asset['资产价值']
                  depreciation_diff = selected_physical['累计折旧额'] - corresponding_asset['累积折旧']
                  
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
                      if selected_physical['存放部门'] != corresponding_asset['部门名称']:
                          st.warning("⚠️ 部门不一致")
                      else:
                          st.success("✅ 部门一致")
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
