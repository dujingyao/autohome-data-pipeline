import requests
from lxml import etree
import time
import csv
import random
import re


def parse_cookies(cookie_str):
    """将cookie字符串转换为字典形式"""
    cookies = {}
    for item in cookie_str.split(';'):
        if item.strip():
            key, value = item.strip().split('=', 1)
            cookies[key] = value
    return cookies


def get_html(url, headers, cookies, retries=3):
    """获取网页HTML，支持重试机制"""
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"第{i + 1}次尝试获取页面失败 {url}: {e}")
            if i < retries - 1:
                sleep_time = 2 + random.random() * 2
                print(f"等待 {sleep_time:.2f} 秒后重试...")
                time.sleep(sleep_time)
            else:
                print("达到最大重试次数，跳过此页")
    return None


def parse_car_detail(html):
    """解析车辆详情页面"""
    if not html:
        return {}

    tree = etree.HTML(html)
    car_detail = {}

    try:
        # 解析车辆名称
        car_name = tree.xpath('//h3[@class="car-brand-name"]/text()')
        car_detail['车辆名称'] = car_name[0].strip() if car_name else ''

        # 解析价格
        price_element = tree.xpath('//span[@class="price"]/text()')
        car_detail['价格(万)'] = price_element[0].strip() if price_element else ''

        # 解析基本信息区域
        brand_items = tree.xpath('//ul[@class="brand-unit-item fn-clear"]/li')
        for item in brand_items:
            label = item.xpath('./p/text()')
            value = item.xpath('./h4/text()')
            if label and value:
                label_text = label[0].strip()
                value_text = value[0].strip()
                if '表显里程' in label_text:
                    car_detail['表显里程'] = value_text
                elif '上牌时间' in label_text:
                    car_detail['上牌时间'] = value_text
                elif '挡位' in label_text or '排量' in label_text:
                    car_detail['挡位排量'] = value_text
                elif '车辆所在地' in label_text:
                    car_detail['车辆所在地'] = value_text

        # 解析车辆档案
        basic_items = tree.xpath('//ul[@class="basic-item-ul"]/li')
        for item in basic_items:
            item_text = item.xpath('.//text()')
            if item_text:
                full_text = ''.join(item_text).strip()

                if '上牌时间' in full_text:
                    car_detail['档案_上牌时间'] = full_text.replace('上牌时间', '').strip()
                elif '表显里程' in full_text:
                    car_detail['档案_表显里程'] = full_text.replace('表显里程', '').strip()
                elif '变速箱' in full_text:
                    car_detail['变速箱'] = full_text.replace('变速箱', '').strip()
                elif '排放标准' in full_text:
                    car_detail['排放标准'] = full_text.replace('排放标准', '').strip()
                elif '排量' in full_text and '排放标准' not in full_text:
                    car_detail['排量'] = full_text.replace('排量', '').strip()
                elif '发布时间' in full_text:
                    car_detail['发布时间'] = full_text.replace('发布时间', '').strip()
                elif '年检到期' in full_text:
                    car_detail['年检到期'] = full_text.replace('年检到期', '').strip()
                elif '保险到期' in full_text:
                    car_detail['保险到期'] = full_text.replace('保险到期', '').strip()
                elif '质保到期' in full_text:
                    car_detail['质保到期'] = full_text.replace('质保到期', '').strip()
                elif '过户次数' in full_text:
                    car_detail['过户次数'] = full_text.replace('过户次数', '').strip()
                elif '所在地' in full_text:
                    car_detail['档案_所在地'] = full_text.replace('所在地', '').strip()
                elif '发动机' in full_text:
                    car_detail['发动机'] = full_text.replace('发动机', '').strip()
                elif '车辆级别' in full_text:
                    car_detail['车辆级别'] = full_text.replace('车辆级别', '').strip()
                elif '车身颜色' in full_text:
                    car_detail['车身颜色'] = full_text.replace('车身颜色', '').strip()
                elif '燃油标号' in full_text:
                    car_detail['燃油标号'] = full_text.replace('燃油标号', '').strip()
                elif '驱动方式' in full_text:
                    car_detail['驱动方式'] = full_text.replace('驱动方式', '').strip()

        # 解析留言框中的信息
        message_box = tree.xpath('//div[contains(@class,"leave-message-box")]//p[@id="messageBox"]/text()')
        if message_box:
            message_text = message_box[0].strip()
            car_detail['留言信息'] = message_text

            # 使用正则表达式提取留言框中的详细信息
            patterns = {
                '留言_车辆名称': r'【车辆名称】(.*?)【',
                '留言_驱动方式': r'【驱动方式】(.*?)【',
                '留言_颜色': r'【颜色】(.*?)【',
                '留言_出厂时间': r'【出厂时间】(.*?)【',
                '留言_交强日期': r'【交强日期】(.*?)【',
                '留言_行驶里程': r'【行驶里程】(.*?)【',
                '留言_车辆排量': r'【车辆排量】(.*?)【',
                '留言_车辆状态': r'【车辆状态】(.*?)【',
                '留言_钥匙': r'【���匙】(.*?)【',
                '留言_车况': r'【车况】(.*?)【',
            }

            # 车辆配置信息通常是最后一项，需要特殊处理
            config_match = re.search(r'【车辆配置】(.*?)$', message_text)
            if config_match:
                car_detail['留言_车辆配置'] = config_match.group(1).strip()

            # 提取其他信息
            for key, pattern in patterns.items():
                match = re.search(pattern, message_text)
                if match:
                    car_detail[key] = match.group(1).strip()

    except Exception as e:
        print(f"解析车辆详情出错: {e}")

    return car_detail


def parse_car_list(html, city_name, page_num, headers, cookies):
    """解析车辆列表页面并获取详情"""
    if not html:
        return []

    tree = etree.HTML(html)
    car_items = tree.xpath('//li[contains(@class, "cards-li")]')

    if not car_items:
        print(f"警告：{city_name}第{page_num}页未找到符合条件的车辆信息")
        return []

    print(f"{city_name}第{page_num}页找到{len(car_items)}个车辆信息项")

    car_list = []
    for index, item in enumerate(car_items):
        try:
            # 提取基本字段
            car_name = item.xpath('@carname')[0] if item.xpath('@carname') else '未知'
            price = item.xpath('@price')[0] if item.xpath('@price') else '未知'
            milage = item.xpath('@milage')[0] if item.xpath('@milage') else '未知'
            reg_date = item.xpath('@regdate')[0] if item.xpath('@regdate') else '未知'
            info_id = item.xpath('@infoid')[0] if item.xpath('@infoid') else '未知'
            dealer_id = item.xpath('@dealerid')[0] if item.xpath('@dealerid') else '未知'

            # 正确构建详情页URL - 使用dealer_id和info_id
            detail_url = f"https://www.che168.com/dealer/{dealer_id}/{info_id}.html"
            print(f"  正在获取第{index + 1}辆车的详情: {car_name}")

            # 获取详情页内容
            detail_html = get_html(detail_url, headers, cookies)
            detail_data = parse_car_detail(detail_html) if detail_html else {}

            # 合并基本信息和详情信息
            car_info = {
                "列表_车名": car_name,
                "列表_价格(万)": price,
                "列表_里程(万公里)": milage,
                "列表_上牌时间": reg_date,
                "车辆ID": info_id,
                "经销商ID": dealer_id,
                "城市": city_name,
                "页码": page_num,
                "详情URL": detail_url
            }

            # 添加详情页数据
            car_info.update(detail_data)
            car_list.append(car_info)

            # 每获取一个详情页后稍作延迟
            time.sleep(1 + random.random())

        except Exception as e:
            print(f"解析车辆信息出错: {e}")

    return car_list


def save_to_csv(car_data, filename="河南二手车详细数据.csv"):
    """保存数据到CSV文件"""
    if not car_data:
        print("没有数据可保存")
        return

    # 扩展字段顺序，包含留言信息
    fields = [
        "列表_车名", "列表_价格(万)", "列表_里程(万公里)", "列表_上牌时间", "车辆ID",
        "经销商ID", "城市", "页码", "详情URL", "车辆名称", "价格(万)", "表显里程", "上牌时间",
        "挡位排量", "车辆所在地", "档案_上牌时间", "档案_表显里程", "变速箱",
        "排放标准", "排量", "发布时间", "年检到期", "保险到期", "质保到期",
        "过户次数", "档案_所在地", "发动机", "车辆级别", "车身颜色", "燃油标号", "驱动方式",
        "留言信息", "留言_车辆名称", "留言_驱动方式", "留言_颜色", "留言_出厂时间",
        "留言_交强日期", "留言_行驶里程", "留言_车辆排量", "留言_车辆状态",
        "留言_钥匙", "留言_车况", "留言_车辆配置"
    ]

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(car_data)
        print(f"数据已保存至 {filename}")
    except Exception as e:
        print(f"保存CSV文件时出错: {e}")


def get_henan_cities():
    """获取河南省所有城市及其拼音"""
    return [
        {"name": "郑州", "pinyin": "zhengzhou"},
        {"name": "开封", "pinyin": "kaifeng"},
        {"name": "洛阳", "pinyin": "luoyang"},
        {"name": "平顶山", "pinyin": "pingdingshan"},
        {"name": "安阳", "pinyin": "anyang"},
        {"name": "鹤壁", "pinyin": "hebi"},
        {"name": "新乡", "pinyin": "xinxiang"},
        {"name": "焦作", "pinyin": "jiaozuo"},
        {"name": "濮阳", "pinyin": "puyang"},
        {"name": "许昌", "pinyin": "xuchang"},
        {"name": "漯河", "pinyin": "luohe"},
        {"name": "三门峡", "pinyin": "sanmenxia"},
        {"name": "南阳", "pinyin": "nanyang"},
        {"name": "商丘", "pinyin": "shangqiu"},
        {"name": "信阳", "pinyin": "xinyang"},
        {"name": "周口", "pinyin": "zhoukou"},
        {"name": "驻马店", "pinyin": "zhumadian"},
        {"name": "济源", "pinyin": "jiyuan"}
    ]


def main():
    # 请求头设置
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.che168.com/'
    }

    # 解析cookie字符串
    cookie_str = 'userarea=410700; listuserarea=410700; fvlid=1749875752311N60ZQ6Bh993X; Hm_lvt_d381ec2f88158113b9b76f14c497ed48=1749875752; HMACCOUNT=661F2DF96ACD0C72; sessionid=3f0072de-495c-4cbd-b66e-505ec390979f; sessionip=117.159.38.165; area=410702; sessionvisit=ffbecc0c-c63e-4c3b-8523-c475d81b82df; sessionvisitInfo=3f0072de-495c-4cbd-b66e-505ec390979f|www.autohome.com.cn|110965; che_sessionid=6213B8CC-3D86-45A8-9B83-4D287063A4D8%7C%7C2025-06-14+12%3A35%3A54.090%7C%7Cwww.autohome.com.cn; che_sessionvid=DD75A578-E54A-4427-877C-36873F86C710; UsedCarBrowseHistory=0%3A55070919; carDownPrice=1; ahpvno=8; Hm_lpvt_d381ec2f88158113b9b76f14c497ed48=1749877548; ahuuid=F013ED35-6B66-4797-B157-795F21FA3349; showNum=8; v_no=7; visit_info_ad=6213B8CC-3D86-45A8-9B83-4D287063A4D8||DD75A578-E54A-4427-877C-36873F86C710||-1||-1||7; che_ref=www.autohome.com.cn%7C0%7C110965%7C0%7C2025-06-14+13%3A05%3A48.535%7C2025-06-14+12%3A35%3A54.090; sessionuid=3f0072de-495c-4cbd-b66e-505ec390979f'
    cookies = parse_cookies(cookie_str)

    all_cars = []
    max_pages = 8  # 每个城市爬取8页
    cities = get_henan_cities()

    # 遍历每个城市
    for city in cities:
        city_name = city["name"]
        city_pinyin = city["pinyin"]

        print(f"\n开始爬取{city_name}的二手车详细数据...")

        # 遍历每一页
        for page in range(1, max_pages + 1):
            # 根据城市构建URL，郑州等城市使用一种URL格式，其他城市可能使用另一种
            if city_pinyin == "zhengzhou" or city_pinyin == "xinxiang":
                url = f'https://www.che168.com/{city_pinyin}/a0_0msdgscncgpi1ltocsp{page}exx0/?pvareaid=102179'
            else:
                # 对于第一页和其他页的处理可能不同
                if page == 1:
                    url = f'https://www.che168.com/{city_pinyin}/list/#pvareaid=100943'
                else:
                    url = f'https://www.che168.com/{city_pinyin}/list/p{page}/#pvareaid=100943'

            print(f"正在爬取{city_name}第{page}页... URL: {url}")

            # 获取页面内容
            html = get_html(url, headers, cookies)
            if not html:
                continue

            # 解析车辆列表并获取详情
            cars = parse_car_list(html, city_name, page, headers, cookies)
            if cars:
                all_cars.extend(cars)
                print(f"第{page}页获取到{len(cars)}条详细数据")
                # 打印当前页面爬取到的第一条数据作为示例
                if len(cars) > 0:
                    print("示例数据:")
                    for key, value in cars[0].items():
                        print(f"{key}: {value}")
                    print("-" * 50)

            # 更新cookie中的某些值
            cookies['v_no'] = str(int(cookies.get('v_no', '7')) + 1)
            cookies['ahpvno'] = str(int(cookies.get('ahpvno', '8')) + 1)

            # 随机延迟，避免被反爬
            sleep_time = 2 + random.random() * 3
            print(f"等待 {sleep_time:.2f} 秒后继续...")
            time.sleep(sleep_time)

        # 城市间更长的延迟
        city_sleep = 5 + random.random() * 5
        print(f"完成{city_name}的爬取，等待{city_sleep:.2f}秒后继续下一个城市...")
        time.sleep(city_sleep)

    # 统计结果
    print(f"\n爬取完成！总共获取了{len(all_cars)}辆车的详细信息")

    # 按城市统计数据量
    city_stats = {}
    for car in all_cars:
        city = car.get('城市', '未知')
        city_stats[city] = city_stats.get(city, 0) + 1

    print("\n各城市数据统计:")
    for city, count in city_stats.items():
        print(f"{city}: {count}条数据")

    # 保存数据到CSV
    save_to_csv(all_cars)


if __name__ == "__main__":
    main()