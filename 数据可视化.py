import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

import os

os.makedirs('images',exist_ok=True)

# 设置中文字体，确保图片中的中文正常显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置图表风格
plt.style.use('seaborn-v0_8-whitegrid')
custom_palette = sns.color_palette("Set2", 10)
sns.set(font="Microsoft YaHei", palette=custom_palette)

# 读取数据
df = pd.read_csv("./datas/二手车预处理结果.csv")

# 选择分析所需的字段并去除缺失值
df_viz = df[['价格_万', '里程_万公里', '上牌年份', '品牌', '车辆级别']].dropna()

# 图1：价格 vs. 行驶里程（按车辆级别区分）
plt.figure(figsize=(8, 6))
sns.scatterplot(
    data=df_viz, x='里程_万公里', y='价格_万', hue='车辆级别', palette='tab20', s=80, edgecolor='k', alpha=0.8
)
plt.title('价格 vs. 行驶里程', fontsize=16, fontweight='bold')
plt.xlabel('行驶里程（万公里）', fontsize=13)
plt.ylabel('价格（万元）', fontsize=13)
plt.legend(title='车辆级别', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('./images/价格_vs_行驶里程.png', dpi=150)
plt.show()

# 图2：不同上牌年份的价格分布（箱线图）
plt.figure(figsize=(11, 6))
sns.boxplot(data=df_viz, x='上牌年份', y='价格_万', width=0.6, fliersize=2, linewidth=1.5, boxprops=dict(alpha=0.7))
plt.title('不同上牌年份的价格分布', fontsize=16, fontweight='bold')
plt.xlabel('上牌年份', fontsize=13)
plt.ylabel('价格（万元）', fontsize=13)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle=':', alpha=0.4)
plt.tight_layout()
plt.savefig('./images/上牌年份_价格分布.png', dpi=150)
plt.show()

# 图3：品牌平均价格（前15）
plt.figure(figsize=(10, 8))
brand_price = df_viz.groupby('品牌')['价格_万'].mean().sort_values(ascending=False).head(15)
sns.barplot(
    x=brand_price.values, y=brand_price.index,
    palette='Spectral',
    edgecolor='k',
    hue=brand_price.index,
    legend=False
)
plt.title('品牌平均价格（前15）', fontsize=16, fontweight='bold')
plt.xlabel('平均价格（万元）', fontsize=13)
plt.ylabel('品牌', fontsize=13)
for i, v in enumerate(brand_price.values):
    plt.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=11, color='black')
plt.tight_layout()
plt.savefig('./images/品牌平均价格前15.png', dpi=150)
plt.show()

# 图4：不同车辆级别的价格分布（小提琴图）
plt.figure(figsize=(10, 6))
sns.violinplot(
    data=df_viz, x='车辆级别', y='价格_万',
    palette='Pastel2',
    inner='quartile',
    linewidth=1.2,
    hue=df_viz['车辆级别'],
    legend=False
)
plt.title('不同车辆级别的价格分布', fontsize=16, fontweight='bold')
plt.xlabel('车辆级别', fontsize=13)
plt.ylabel('价格（万元）', fontsize=13)
plt.xticks(rotation=30)
plt.grid(axis='y', linestyle=':', alpha=0.4)
plt.tight_layout()
plt.savefig('./images/车辆级别_价格分布.png', dpi=150)
plt.show()

# ------------------- 机器学习特征重要性分析 -------------------

# 选择相关特征
features = ['里程_万公里', '上牌年份', '品牌', '车辆级别']
target = '价格_万'

# 丢弃缺失值
df_ml = df[features + [target]].dropna()

# 编码分类特征
df_encoded = df_ml.copy()
label_encoders = {}
for col in ['品牌', '车辆级别']:
    le = LabelEncoder()
    df_encoded[col] = le.fit_transform(df_ml[col])
    label_encoders[col] = le

# 分割数据集
X = df_encoded[features]
y = df_encoded[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 模型训练：随机森林
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 模型评估
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
rmse = mse ** 0.5
r2 = r2_score(y_test, y_pred)

print(f"模型评估结果：")
print(f"  RMSE 均方根误差: {rmse:.2f} 万元")
print(f"  R² 决定系数: {r2:.2f}")

# 特征重要性可视化
importances = model.feature_importances_
feature_names = X.columns
feature_importance_df = pd.DataFrame({
    '特征': feature_names,
    '重要性': importances
}).sort_values(by='重要性', ascending=False)

plt.figure(figsize=(8, 6))
sns.barplot(
    x='重要性', y='特征', data=feature_importance_df,
    palette="Oranges",
    edgecolor='k',
    hue='特征',
    legend=False
)
plt.title('影响二手车价格的重要因素', fontsize=16, fontweight='bold')
plt.xlabel('特征重要性', fontsize=13)
plt.ylabel('特征', fontsize=13)
for i, v in enumerate(feature_importance_df['重要性']):
    plt.text(v + 0.01, i, f'{v:.2f}', va='center', fontsize=11, color='black')
plt.tight_layout()
plt.savefig('./images/特征重要性分析.png', dpi=150)
plt.show()