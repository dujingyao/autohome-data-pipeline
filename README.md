# 汽车之家二手车数据爬取项目

这是一个用于爬取汽车之家网站二手车信息的Python项目。

## 项目结构

```
汽车之家爬取/
├── 数据爬取.py              # 主要的数据爬取脚本
├── 河南二手车详细数据.csv    # 爬取到的河南地区二手车数据
├── README.md               # 项目说明文档
└── .idea/                  # PyCharm IDE配置文件夹
```

## 环境要求

- Python 3.11
- 建议使用 PyCharm IDE 进行开发

## 安装与运行

1. 克隆项目到本地：

```bash
git clone https://github.com/dujingyao/-.git
cd 汽车之家爬取
```

2. 创建虚拟环境（可选但推荐）：

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# 或
source .venv/bin/activate  # macOS/Linux
```

3. 安装依赖包：

```bash
pip install -r requirements.txt
```

4. 运行爬虫脚本：

```bash
python 数据爬取.py
```

## 功能特性

- 爬取汽车之家网站的二手车信息
- 支持河南地区二手车数据采集
- 数据导出为CSV格式便于后续分析

## 数据说明

项目已包含 `河南二手车详细数据.csv` 文件，包含了爬取到的河南地区二手车的详细信息。

## 注意事项

- 请遵守网站的robots.txt协议和使用条款
- 建议在爬取时添加适当的延时以避免对目标网站造成过大压力
- 爬取的数据仅供学习和研究使用

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

请确保遵守相关法律法规和网站使用条款。

---

**免责声明**：本项目仅供学习和研究目的使用，请确保在合法合规的前提下使用本工具。
