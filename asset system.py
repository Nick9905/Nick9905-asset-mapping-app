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

# ========== 数据导入函数（简化版）==========

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

# ========== 优化的查询函数 ==========

def find_corresponding_asset(code, code_type, financial_index, physical_index, f_to_p_mapping, p_to_f_mapping):
  """优化的资产查找函数"""
  if code_type == "financial":
      physical_code = f_to_p_mapping.get(code)
      if physical_code:
          return physical_index.get(physical_code), physical_code
  else:
      financial_code = p_to_f_mapping.get(code)
      if financial_code:
          return financial_index.get(financial_code), financial_code
  return None, None

# ========== 简化的数据导入页面 ==========

def data_import_page():
  """数据导入页面（简化版）"""
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

# ========== 优化的查询页面 ==========

def mapping_query_page():
  """映射关系查询页面（优化版）"""
  st.header("🔍 资产映射关系查询")
  
  # 加载数据和创建索引
  financial_data = load_data(FINANCIAL_DATA_FILE)
  physical_data = load_data(PHYSICAL_DATA_FILE)
  mapping_data = load_data(MAPPING_DATA_FILE)
  
  if not all([financial_data, physical_data, mapping_data]):
      st.warning("⚠️ 请先导入所有必要的数据")
      return
  
  # 创建索引以提高查询效率
  financial_index = create_data_index(financial_data, "财务系统编号")
  physical_index = create_data_index(physical_data, "固定资产编号")
  f_to_p_mapping, p_to_f_mapping = create_mapping_index(mapping_data)
  
  # 查询界面
  col1, col2 = st.columns(2)
  
  with col1:
      query_type = st.selectbox("查询方式", ["按财务系统编号查询", "按实物台账编号查询", "按资产名称查询"])
  
  with col2:
      if query_type == "按财务系统编号查询":
          query_value = st.selectbox("选择财务系统编号", [""] + list(financial_index.keys()))
      elif query_type == "按实物台账编号查询":
          query_value = st.selectbox("选择实物台账编号", [""] + list(physical_index.keys()))
      else:
          query_value = st.text_input("输入资产名称关键词")
  
  if query_value and st.button("🔍 查询", type="primary"):
      with st.spinner("查询中..."):
          results = []
          
          if query_type == "按财务系统编号查询":
              financial_record = financial_index.get(query_value)
              if financial_record:
                  physical_record, physical_code = find_corresponding_asset(
                      query_value, "financial", financial_index, physical_index, f_to_p_mapping, p_to_f_mapping
                  )
                  if physical_record:
                      results.append({
                          "financial": financial_record,
                          "physical": physical_record
                      })
          
          elif query_type == "按实物台账编号查询":
              physical_record = physical_index.get(query_value)
              if physical_record:
                  financial_record, financial_code = find_corresponding_asset(
                      query_value, "physical", financial_index, physical_index, f_to_p_mapping, p_to_f_mapping
                  )
                  if financial_record:
                      results.append({
                          "financial": financial_record,
                          "physical": physical_record
                      })
          
          else:  # 按资产名称查询
              # 在财务系统中查找
              for code, record in financial_index.items():
                  if query_value.lower() in record["资产名称"].lower():
                      physical_record, _ = find_corresponding_asset(
                          code, "financial", financial_index, physical_index, f_to_p_mapping, p_to_f_mapping
                      )
                      if physical_record:
                          results.append({
                              "financial": record,
                              "physical": physical_record
                          })
              
              # 在实物台账中查找
              for code, record in physical_index.items():
                  if query_value.lower() in record["固定资产名称"].lower():
                      financial_record, _ = find_corresponding_asset(
                          code, "physical", financial_index, physical_index, f_to_p_mapping, p_to_f_mapping
                      )
                      if financial_record:
                          # 避免重复
                          if not any(r["financial"]["财务系统编号"] == financial_record["财务系统编号"] for r in results):
                              results.append({
                                  "financial": financial_record,
                                  "physical": record
                              })
          
          # 显示结果
          display_query_results(results)

def display_query_results(results):
  """显示查询结果"""
  if results:
      st.success(f"✅ 找到 {len(results)} 条匹配记录")
      
      for idx, result in enumerate(results):
          with st.expander(f"📌 记录 {idx + 1}: {result['financial']['资产名称']}", expanded=idx==0):
              col1, col2 = st.columns(2)
              
              with col1:
                  st.markdown("### 📊 财务系统信息")
                  display_financial_info_simple(result["financial"])
              
              with col2:
                  st.markdown("### 📋 实物台账信息")
                  display_physical_info_simple(result["physical"])
              
              # 简化的差异分析
              display_simple_difference_analysis(result["financial"], result["physical"])
  else:
      st.warning("❌ 未找到匹配的记录")

def display_financial_info_simple(financial_asset):
  """简化的财务信息显示"""
  info_data = {
      "编号": financial_asset.get('财务系统编号', 'N/A'),
      "名称": financial_asset.get('资产名称', 'N/A'),
      "分类": financial_asset.get('资产分类', 'N/A'),
      "价值": f"¥{financial_asset.get('资产价值', 0):,.2f}",
      "累积折旧": f"¥{financial_asset.get('累积折旧', 0):,.2f}",
      "账面价值": f"¥{financial_asset.get('账面价值', 0):,.2f}",
      "部门": financial_asset.get('部门名称', 'N/A'),
      "保管人": financial_asset.get('保管人', 'N/A')
  }
  
  for key, value in info_data.items():
      st.write(f"**{key}**：{value}")

def display_physical_info_simple(physical_asset):
  """简化的实物信息显示"""
  asset_value = physical_asset.get('资产价值', 0)
  depreciation = physical_asset.get('累计折旧额', 0)
  net_value = asset_value - depreciation
  
  info_data = {
      "编号": physical_asset.get('固定资产编号', 'N/A'),
      "名称": physical_asset.get('固定资产名称', 'N/A'),
      "类型": physical_asset.get('固定资产类型', 'N/A'),
      "价值": f"¥{asset_value:,.2f}",
      "累计折旧": f"¥{depreciation:,.2f}",
      "净值": f"¥{net_value:,.2f}",
      "部门": physical_asset.get('存放部门', 'N/A'),
      "保管人": physical_asset.get('保管人', 'N/A')
  }
  
  for key, value in info_data.items():
      st.write(f"**{key}**：{value}")

def display_simple_difference_analysis(financial_asset, physical_asset):
  """简化的差异分析"""
  st.markdown("### 📊 差异分析")
  
  financial_value = financial_asset.get('资产价值', 0)
  physical_value = physical_asset.get('资产价值', 0)
  value_diff = financial_value - physical_value
  
  col1, col2, col3 = st.columns(3)
  
  with col1:
      if abs(value_diff) > 0.01:
          st.error(f"价值差异：¥{value_diff:,.2f}")
      else:
          st.success("✅ 价值一致")
  
  with col2:
      financial_dept = financial_asset.get('部门名称', '')
      physical_dept = physical_asset.get('存放部门', '')
      if financial_dept != physical_dept:
          st.warning("⚠️ 部门不一致")
      else:
          st.success("✅ 部门一致")
  
  with col3:
      financial_keeper = financial_asset.get('保管人', '')
      physical_keeper = physical_asset.get('保管人', '')
      if financial_keeper != physical_keeper:
          st.warning("⚠️ 保管人不一致")
      else:
          st.success("✅ 保管人一致")

# ========== 简化的数据统计页面 ==========

def data_statistics_page():
  """数据统计分析页面（简化版）"""
  st.header("📊 数据统计分析")
  
  # 加载数据
  financial_data = load_data(FINANCIAL_DATA_FILE)
  physical_data = load_data(PHYSICAL_DATA_FILE)
  mapping_data = load_data(MAPPING_DATA_FILE)
  
  if not all([financial_data, physical_data, mapping_data]):
      st.warning("⚠️ 请先导入所有必要的数据")
      return
  
  # 基础统计
  col1, col2, col3 = st.columns(3)
  
  with col1:
      st.metric("财务系统资产数", len(financial_data))
  with col2:
      st.metric("实物台账资产数", len(physical_data))
  with col3:
      st.metric("已建立映射关系数", len(mapping_data))
  
  # 匹配率分析
  financial_mapped = set(m["财务系统编号"] for m in mapping_data)
  physical_mapped = set(m["实物台账编号"] for m in mapping_data)
  
  financial_match_rate = len(financial_mapped) / len(financial_data) * 100 if financial_data else 0
  physical_match_rate = len(physical_mapped) / len(physical_data) * 100 if physical_data else 0
  
  st.subheader("🔗 匹配率分析")
  col1, col2 = st.columns(2)
  
  with col1:
      st.metric("财务系统匹配率", f"{financial_match_rate:.1f}%")
      st.progress(financial_match_rate / 100)
  
  with col2:
      st.metric("实物台账匹配率", f"{physical_match_rate:.1f}%")
      st.progress(physical_match_rate / 100)
  
  # 未匹配资产统计
  st.subheader("⚠️ 未匹配资产统计")
  
  unmatched_financial = len(financial_data) - len(financial_mapped)
  unmatched_physical = len(physical_data) - len(physical_mapped)
  
  col1, col2 = st.columns(2)
  with col1:
      st.metric("未匹配财务资产", unmatched_financial)
  with col2:
      st.metric("未匹配实物资产", unmatched_physical)
  
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
              value_differences.append(diff)
  
  if value_differences:
      total_diff = sum(value_differences)
      avg_diff = total_diff / len(value_differences)
      
      col1, col2, col3 = st.columns(3)
      with col1:
          st.metric("差异项数", len(value_differences))
      with col2:
          st.metric("差异总额", f"¥{total_diff:,.2f}")
      with col3:
          st.metric("平均差异", f"¥{avg_diff:,.2f}")
  else:
      st.success("✅ 所有已匹配资产的价值完全一致")

# ========== 简化的全部数据查看页面 ==========

def all_data_view_page():
  """查看全部对应关系页面（简化版）"""
  st.header("📋 全部资产对应关系")
  
  # 加载数据
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
  view_mode = st.selectbox("选择查看模式", ["对应关系汇总", "财务系统明细", "实物台账明细"])
  
  if view_mode == "对应关系汇总":
      st.subheader("🔗 完整对应关系汇总")
      
      # 构建汇总数据
      mapping_summary = []
      for financial_code, physical_code in f_to_p_mapping.items():
          financial_record = financial_
