import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
from functools import lru_cache

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

# ========== 缓存和性能优化 ==========

@st.cache_data(ttl=300)  # 缓存5分钟
def load_data_cached(file_path):
  """加载数据（带缓存）"""
  if os.path.exists(file_path):
      try:
          with open(file_path, 'r', encoding='utf-8') as f:
              return json.load(f)
      except:
          return []
  return []

def load_data(file_path):
  """加载数据"""
  return load_data_cached(file_path)

def save_data(data, file_path):
  """保存数据并清除缓存"""
  with open(file_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2, default=str)
  # 清除缓存以确保数据一致性
  load_data_cached.clear()

@st.cache_data
def create_mapping_index(mapping_data):
  """创建映射索引以提高查询效率"""
  financial_to_physical = {}
  physical_to_financial = {}
  
  for mapping in mapping_data:
      financial_code = mapping.get("财务系统编号")
      physical_code = mapping.get("实物台账编号")
      
      if financial_code and physical_code:
          financial_to_physical[financial_code] = physical_code
          physical_to_financial[physical_code] = financial_code
  
  return financial_to_physical, physical_to_financial

@st.cache_data
def create_data_index(data, key_field):
  """创建数据索引"""
  return {item[key_field]: item for item in data if item.get(key_field)}

# ========== 数据处理函数 ==========

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

def update_data_generic(existing_data, new_data, key_field):
  """通用数据更新函数"""
  existing_dict = {item[key_field]: item for item in existing_data if item.get(key_field)}
  
  updated_count = 0
  new_count = 0
  
  for new_item in new_data:
      key_value = new_item.get(key_field)
      if key_value and key_value in existing_dict:
          existing_dict[key_value].update(new_item)
          existing_dict[key_value]["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          updated_count += 1
      elif key_value:
          existing_dict[key_value] = new_item
          new_count += 1
  
  st.info(f"📊 更新统计：更新 {updated_count} 条，新增 {new_count} 条")
  return list(existing_dict.values())

# ========== 数据导入函数 ==========

def import_financial_data(df):
  """导入财务系统数据"""
  processed_data = []
  
  for index, row in df.iterrows():
      try:
          financial_record = {
              "财务系统编号": safe_str_convert(row.iloc[0] if len(row) > 0 else ""),
              "序号": safe_str_convert(row.iloc[1] if len(row) > 1 else ""),
              "所属公司": safe_str_convert(row.iloc[2] if len(row) > 2 else ""),
              "资产分类": safe_str_convert(row.iloc[3] if len(row) > 3 else ""),
              "资产编号": safe_str_convert(row.iloc[4] if len(row) > 4 else ""),
              "资产名称": safe_str_convert(row.iloc[5] if len(row) > 5 else ""),
              "资产规格": safe_str_convert(row.iloc[6] if len(row) > 6 else ""),
              "取得日期": safe_str_convert(row.iloc[9] if len(row) > 9 else ""),
              "资产价值": safe_float_convert(row.iloc[24] if len(row) > 24 else 0),
              "累积折旧": safe_float_convert(row.iloc[26] if len(row) > 26 else 0),
              "账面价值": safe_float_convert(row.iloc[27] if len(row) > 27 else 0),
              "部门名称": safe_str_convert(row.iloc[36] if len(row) > 36 else ""),
              "保管人": safe_str_convert(row.iloc[38] if len(row) > 38 else ""),
              "备注": safe_str_convert(row.iloc[28] if len(row) > 28 else ""),
              "导入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "原始行号": index + 1
          }
          
          if financial_record["财务系统编号"] or financial_record["资产编号"]:
              processed_data.append(financial_record)
      except Exception as e:
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

# ========== 页面函数 ==========

def data_import_page():
  """数据导入页面"""
  st.header("📥 数据导入")
  
  tab1, tab2, tab3 = st.tabs(["📊 财务系统数据", "📋 实物台账数据", "🔗 对应关系数据"])
  
  with tab1:
      st.subheader("财务系统数据导入")
      financial_file = st.file_uploader("选择财务系统Excel文件", type=['xlsx', 'xls'], key="financial")
      
      if financial_file is not None:
          try:
              df = pd.read_excel(financial_file)
              st.success("✅ 文件上传成功！")
              
              with st.expander("数据预览", expanded=False):
                  st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入财务数据", type="primary"):
                  with st.spinner("正在处理数据..."):
                      processed_data = import_financial_data(df)
                      
                      if processed_data:
                          existing_data = load_data(FINANCIAL_DATA_FILE)
                          updated_data = update_data_generic(existing_data, processed_data, "财务系统编号")
                          save_data(updated_data, FINANCIAL_DATA_FILE)
                          st.success(f"✅ 成功导入 {len(processed_data)} 条财务数据！")
                          st.rerun()
                      else:
                          st.warning("没有有效数据可导入")
                          
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")
  
  with tab2:
      st.subheader("实物台账数据导入")
      physical_file = st.file_uploader("选择实物台账Excel文件", type=['xlsx', 'xls'], key="physical")
      
      if physical_file is not None:
          try:
              df = pd.read_excel(physical_file)
              st.success("✅ 文件上传成功！")
              
              with st.expander("数据预览", expanded=False):
                  st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入实物数据", type="primary"):
                  with st.spinner("正在处理数据..."):
                      processed_data = import_physical_data(df)
                      
                      if processed_data:
                          existing_data = load_data(PHYSICAL_DATA_FILE)
                          updated_data = update_data_generic(existing_data, processed_data, "固定资产编号")
                          save_data(updated_data, PHYSICAL_DATA_FILE)
                          st.success(f"✅ 成功导入 {len(processed_data)} 条实物数据！")
                          st.rerun()
                      else:
                          st.warning("没有有效数据可导入")
                          
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")
  
  with tab3:
      st.subheader("对应关系数据导入")
      mapping_file = st.file_uploader("选择对应关系Excel文件", type=['xlsx', 'xls'], key="mapping")
      
      if mapping_file is not None:
          try:
              df = pd.read_excel(mapping_file)
              st.success("✅ 文件上传成功！")
              
              with st.expander("数据预览", expanded=False):
                  st.dataframe(df.head(), use_container_width=True)
              
              if st.button("确认导入对应关系", type="primary"):
                  with st.spinner("正在处理数据..."):
                      processed_data = import_mapping_data(df)
                      
                      if processed_data:
                          existing_data = load_data(MAPPING_DATA_FILE)
                          updated_data = update_data_generic(existing_data, processed_data, "实物台账编号")
                          save_data(updated_data, MAPPING_DATA_FILE)
                          st.success(f"✅ 成功导入 {len(processed_data)} 条对应关系！")
                          st.rerun()
                      else:
                          st.warning("没有有效数据可导入")
                          
          except Exception as e:
              st.error(f"❌ 文件读取失败：{str(e)}")

def mapping_query_page():
  """映射关系查询页面"""
  st.header("🔍 资产映射关系查询")
  st.info("请先导入数据后再进行查询")

def data_statistics_page():
  """数据统计分析页面"""
  st.header("📊 数据统计分析")
  st.info("请先导入数据后再查看统计")

def all_data_view_page():
  """查看全部对应关系页面"""
  st.header("📋 全部资产对应关系")
  st.info("请先导入数据后再查看详情")

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
