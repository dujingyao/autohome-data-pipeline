import pandas as pd
import os
import re
import numpy as np # 确保导入 numpy


def extract_brand(car_name):
    """
    从车名中提取品牌。
    规则：
    1. 如果车名含中文，则只提取第一个连续的中文字符串作为品牌。
       例如 "途观L" -> "途观", "奥迪A4L" -> "奥迪", "奔驰GLC" -> "奔驰"
    2. 如果提取出的中文字符串仅为 "款"，则视为无效品牌，返回None。
    3. 如果车名不含中文（例如全英文、数字等），则返回None（表示该品牌应被舍弃）。
    """
    if pd.isna(car_name):
        return None
    
    name_str = str(car_name)
    
    # 查找第一个连续的中文字符串
    match = re.search(r'([\u4e00-\u9fa5]+)', name_str)
    
    if match:
        extracted_brand = match.group(1)
        # 如果提取出的品牌仅为 "款"，则视为无效
        if extracted_brand == "款":
            return None
        return extracted_brand
    else:
        # 如果没有中文字符（例如全英文），则返回None
        return None


# --- 新增或修改的辅助函数 ---
def clean_text_value(text):
    """清洗单个文本数据，去除不可见字符和常见乱码，规范化空格"""
    if not isinstance(text, str):
        return text
    text = text.replace('\u3000', ' ').replace('\xa0', ' ').replace('\u200b', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:\'"()\[\]{}<>@#$%^&*\-_+=/\\|`~·！￥（）——【】《》？，。；：‘’“”€£¥]', '', text, flags=re.UNICODE)
    return text.strip()

def clean_text_series(series):
    """对整个 Series 应用文本清理"""
    if series is None or series.empty:
        return series
    return series.astype(str).apply(clean_text_value)

def clean_price_value(price_str):
    if not isinstance(price_str, str):
        return np.nan
    cleaned_price = re.sub(r'[^\d.]', '', price_str)
    if not cleaned_price:
        return np.nan
    try:
        price = float(cleaned_price)
        return price if price > 0 else np.nan # 价格必须为正
    except ValueError:
        return np.nan

def clean_mileage_value(mileage_str):
    if not isinstance(mileage_str, str):
        return np.nan
    cleaned_mileage = re.sub(r'[^\d.]', '', mileage_str)
    if not cleaned_mileage:
        return np.nan
    try:
        return float(cleaned_mileage)
    except ValueError:
        return np.nan

def parse_registration_date_value(date_str):
    if not isinstance(date_str, str):
        return pd.NaT
    match = re.match(r'(\d{4})[/-年](\d{1,2})', date_str.strip())
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if 1900 <= year <= pd.Timestamp.now().year + 2 and 1 <= month <= 12: # 放宽年份上限一点
            return pd.Timestamp(f"{year}-{month}-01")
    return pd.NaT


# --- 重构 clean_used_car_data 函数 ---
def clean_used_car_data():
    try:
        # 1. & 2. 文件路径定义 (与原代码类似)
        current_dir = os.getcwd()
        print(f"\n当前工作目录: {current_dir}")
        input_file = '全国省会二手车详细数据.csv' # 确保这是正确的文件名
        output_dir = 'datas'
        output_file = os.path.join(output_dir, '二手车清洗结果.csv') # 更新输出文件名

        # 3. 检查输入文件 (与原代码类似)
        file_exists = False
        actual_filename = None

        for f in os.listdir():
            if f.lower() == input_file.lower():
                file_exists = True
                actual_filename = f
                break

        if not file_exists:
            raise FileNotFoundError(f"未找到文件: {input_file}")

        print(f"\n找到文件: {actual_filename}")

        # 4. 尝试多种编码方式读取
        encodings = ['utf-8', 'gbk', 'utf-16', 'latin1']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(actual_filename, encoding=encoding)
                print(f"成功使用编码: {encoding}")
                break
            except UnicodeDecodeError as e:
                print(f"尝试编码 {encoding} 失败: {str(e)}")
                continue
            except Exception as e:
                print(f"读取文件时出错({encoding}): {str(e)}")
                continue

        if df is None:
            raise ValueError("无法用任何编码读取文件")

        print(f"\n原始数据读取成功，行数: {len(df)}")
        print(f"原始列名: {df.columns.tolist()}")


        # --- 开始重构的数据清洗和特征工程流程 ---
        print("\n开始详细数据预处理...")

        # 步骤 A: 初始列名清理和统一化 (例如，去除列名中的空格)
        df.columns = df.columns.str.strip()

        # 步骤 B: 合并相似列，优先使用更详细或可靠的来源
        # (与 CarDataProcessor 中的逻辑类似)
        df['车辆ID'] = df['车辆ID'].astype(str).replace('未知', np.nan)
        
        # 合并价格，并重命名为 价格_万
        df['价格_万'] = df['价格(万)'].combine_first(df['列表_价格(万)'])
        if '价格(万)' in df.columns: df.drop(columns=['价格(万)'], inplace=True, errors='ignore')
        if '列表_价格(万)' in df.columns: df.drop(columns=['列表_价格(万)'], inplace=True, errors='ignore')

        # 合并里程，并重命名为 里程_万公里
        df['里程_万公里'] = df['表显里程'].combine_first(df['列表_里程(万公里)']).combine_first(df['档案_表显里程'])
        if '表显里程' in df.columns: df.drop(columns=['表显里程'], inplace=True, errors='ignore')
        if '列表_里程(万公里)' in df.columns: df.drop(columns=['列表_里程(万公里)'], inplace=True, errors='ignore')
        if '档案_表显里程' in df.columns: df.drop(columns=['档案_表显里程'], inplace=True, errors='ignore')
        
        df['上牌时间_原始'] = df['上牌时间'].combine_first(df['列表_上牌时间']).combine_first(df['档案_上牌时间'])
        if '上牌时间' in df.columns: df.drop(columns=['上牌时间'], inplace=True, errors='ignore')
        if '列表_上牌时间' in df.columns: df.drop(columns=['列表_上牌时间'], inplace=True, errors='ignore')
        if '档案_上牌时间' in df.columns: df.drop(columns=['档案_上牌时间'], inplace=True, errors='ignore')

        # 合并车名，并重命名为 车名
        df['车名'] = df['车辆名称'].combine_first(df['列表_车名'])
        if '车辆名称' in df.columns: df.drop(columns=['车辆名称'], inplace=True, errors='ignore')
        if '列表_车名' in df.columns: df.drop(columns=['列表_车名'], inplace=True, errors='ignore')
        
        # 发动机信息也可能来自多个列，这里简化处理，假设原始 '发动机' 列存在
        
        # 步骤 C: 提取品牌 (与原代码类似，但确保在列合并后)
        if '车名' in df.columns:
            df['品牌'] = df['车名'].apply(extract_brand)
            # df['品牌'] = df['品牌'].replace('T', 'T-ROC探歌') # 此特定替换可能不再需要或需要调整
            print("品牌提取完成。")
        else:
            df['品牌'] = np.nan
            print("警告: '车名' 列不存在，无法提取品牌。")

        # 步骤 D: 数据类型转换和特定列清洗
        # 价格
        if '价格_万' in df.columns:
            df['价格_万'] = df['价格_万'].apply(clean_price_value)
        # 里程
        if '里程_万公里' in df.columns:
            df['里程_万公里'] = df['里程_万公里'].apply(clean_mileage_value)
        # 上牌时间 -> 年份和月份
        if '上牌时间_原始' in df.columns:
            parsed_dates = df['上牌时间_原始'].apply(parse_registration_date_value)
            df['上牌年份'] = parsed_dates.dt.year.astype('Int64')
            df['上牌月份'] = parsed_dates.dt.month.astype('Int64')
            df.drop(columns=['上牌时间_原始'], inplace=True, errors='ignore')
        
        # 挡位排量 -> 变速箱类型 (不再提取排量(L) 从这里)
        if '挡位排量' in df.columns:
            df['挡位排量_str'] = df['挡位排量'].astype(str)
            df['变速箱类型'] = df['挡位排量_str'].apply(lambda x: x.split('/')[0].strip() if isinstance(x, str) and '/' in x else x.strip() if isinstance(x, str) else np.nan)
            df.drop(columns=['挡位排量_str'], inplace=True, errors='ignore')
            if '挡位排量' in df.columns: df.drop(columns=['挡位排量'], inplace=True, errors='ignore')

        
        # 发动机信息解析
        if '发动机' in df.columns:
            df['发动机_str'] = df['发动机'].astype(str).str.upper()
            displacement_pattern = r'(\d+\.\d+|\d+)\s*([TL])?' 
            displacement_matches = df['发动机_str'].str.extract(displacement_pattern)
            df['排量_L'] = pd.to_numeric(displacement_matches[0], errors='coerce') # 重命名为 排量_L
            
            horsepower_pattern = r'(\d+)\s*(?:马力|PS)'
            df['发动机马力_PS'] = df['发动机_str'].str.extract(horsepower_pattern, flags=re.IGNORECASE)[0]
            df['发动机马力_PS'] = pd.to_numeric(df['发动机马力_PS'], errors='coerce').astype('Int64')
            
            df.drop(columns=['发动机_str'], inplace=True, errors='ignore')
            df.drop(columns=['发动机'], inplace=True, errors='ignore') # 删除原始发动机列
        else: # 如果原始发动机列不存在，则创建空的派生列
            df['排量_L'] = np.nan
            df['发动机马力_PS'] = np.nan

        
        # 过户次数
        if '过户次数' in df.columns:
            df['过户次数'] = df['过户次数'].astype(str).str.extract(r'(\d+)').iloc[:, 0]
            df['过户次数'] = pd.to_numeric(df['过户次数'], errors='coerce').astype('Int64')

        # 燃油标号 (与原代码类似，但确保在列合并和类型转换后)
        if '燃油标号' in df.columns:
            df = df[df['燃油标号'].astype(str).str.contains('92|95', na=False)]
            print(f"燃油标号过滤后，剩余行数: {len(df)}")

        # 步骤 E: 文本列统一清理
        text_columns_to_clean = ['车名', '品牌', '城市', '经销商ID', '排放标准', '车辆级别', 
                                 '车身颜色', '燃油标号', '驱动方式', '变速箱类型']
                                 # '发动机进气形式', '发动机气缸排列' 已移除
        for col in text_columns_to_clean:
            if col in df.columns:
                df[col] = clean_text_series(df[col])
                df[col].replace('', np.nan, inplace=True) # 清理后的空字符串转为NaN

        # 步骤 F: 定义最终保留的列 (已更新列名和顺序)
        final_columns_ordered = [
            '车辆ID', '车名', '品牌', '城市', 
            '价格_万', '里程_万公里', '上牌年份', '上牌月份',
            '变速箱类型', '排量_L', '发动机马力_PS', # 更新为 排量_L
            '排放标准', '过户次数', '车辆级别', '车身颜色', 
            '燃油标号', '驱动方式', '经销商ID' 
        ]
        existing_final_columns = [col for col in final_columns_ordered if col in df.columns]
        df_selected = df[existing_final_columns].copy()
        print(f"\n选择最终列后，数据形状: {df_selected.shape}")
        print(f"最终列: {df_selected.columns.tolist()}")


        # 步骤 G: 去重和处理缺失值
        # 移除无效车辆ID的行 (如果之前未完全处理)
        df_selected.dropna(subset=['车辆ID'], inplace=True)
        # 基于车辆ID去重
        df_selected.sort_values(by=['车辆ID'], ascending=[True], inplace=True) # 确保去重一致性
        df_selected.drop_duplicates(subset=['车辆ID'], keep='first', inplace=True)
        # 移除完全重复的行
        df_selected.drop_duplicates(inplace=True)
        print(f"去重后，数据形状: {df_selected.shape}")

        # 移除在所有最终选定列上存在任何缺失值的行
        # 特别注意，如果 extract_brand 返回 None (例如品牌为全英文或仅为"款")，品牌列会有 NaN，这一步会移除这些行
        rows_before_final_dropna = len(df_selected)
        df_cleaned = df_selected.dropna(subset=df_selected.columns) # dropna on all columns of df_selected
        rows_after_final_dropna = len(df_cleaned)
        print(f"移除所有列中含任何NaN的行后，数据形状: {df_cleaned.shape}. 移除了 {rows_before_final_dropna - rows_after_final_dropna} 行.")

        # 步骤 H: 保存结果 (与原代码类似)
        if len(df_cleaned) > 0:
            os.makedirs(output_dir, exist_ok=True)
            df_cleaned.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n清洗完成，结果保存到: {output_file}")
            print(f"最终保存行数: {len(df_cleaned)}")
        else:
            print("\n清洗后没有数据可保存。")
        
        print("操作成功完成！")
        return True

    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        print("\n调试建议:")
        print("1. 确认文件是否被其他程序打开")
        print("2. 检查数据列是否存在")
        print("3. 检查文件名是否有隐藏字符")
        return False


# 执行清洗函数
if clean_used_car_data():
    print("程序执行成功")
else:
    print("程序执行失败")