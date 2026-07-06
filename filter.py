import socket
import urllib.request
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# 常见国家/地区代码转中文映射字典
COUNTRY_MAP = {
    "US": "美国", "HK": "中国香港", "TW": "中国台湾", "SG": "新加坡", "JP": "日本", 
    "KR": "韩国", "DE": "德国", "GB": "英国", "FR": "法国", "CA": "加拿大", 
    "AU": "澳大利亚", "RU": "俄罗斯", "IN": "印度", "CN": "中国", "NL": "荷兰", 
    "FI": "芬兰", "SE": "瑞典", "NO": "挪威", "DK": "丹麦", "CH": "瑞士", 
    "AT": "奥地利", "IT": "意大利", "ES": "西班牙", "PT": "葡萄牙", "MY": "马来西亚", 
    "TH": "泰国", "VN": "越南", "PH": "菲律宾", "ID": "印度尼西亚", "KH": "柬埔寨", 
    "LA": "老挝", "MM": "缅甸", "BR": "巴西", "AR": "阿根廷", "CL": "智利", 
    "CO": "哥伦比亚", "MX": "墨西哥", "ZA": "南非", "EG": "埃及", "NG": "尼日利亚", 
    "KE": "肯尼亚", "AE": "阿联酋", "SA": "沙特", "TR": "土耳其", "UA": "乌克兰", 
    "PL": "波兰", "NZ": "新西兰", "IE": "爱尔兰", "BE": "比利时", "LU": "卢森堡"
}

def check_ip(item):
    ip, port, country_code = item
    start_time = time.perf_counter()
    try:
        with socket.create_connection((ip, int(port)), timeout=2.5):
            latency = (time.perf_counter() - start_time) * 1000
            return {
                "ip": ip,
                "port": port,
                "cc": country_code,
                "latency": latency
            }
    except Exception:
        return None

def main():
    url = "https://zip.cm.edu.kg/all.txt"
    print("正在从网络获取全量 IP 列表...")
    
    # 【关键升级】伪装成正常浏览器，防止被对方服务器或 Cloudflare 拦截
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            lines = [line.strip() for line in html.split('\n') if line.strip()]
    except Exception as e:
        print(f"❌ 错误：获取网络 IP 列表失败。原因: {e}")
        sys.exit(1) # 明确通知系统在这里报错拦截

    tasks = []
    for line in lines:
        if "#" in line and ":" in line:
            ip_port, country_code = line.split("#", 1)
            ip, port = ip_port.split(":", 1)
            tasks.append((ip.strip(), port.strip(), country_code.strip()))

    print(f"解析成功，总计 {len(tasks)} 个 IP 待测。开始稳健测试（50并发）...")
    
    alive_nodes = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_ip, tasks)
        for res in results:
            if res:
                alive_nodes.append(res)

    print(f"测试完毕！共有 {len(alive_nodes)} 个活节点。开始执行全球国家均摊算法...")

    if not alive_nodes:
        print("❌ 错误：未检测到任何存活节点，请检查网络源或稍后再试。")
        sys.exit(1)

    country_buckets = {}
    for node in alive_nodes:
        cc = node["cc"]
        if cc not in country_buckets:
            country_buckets[cc] = []
        country_buckets[cc].append(node)

    for cc in country_buckets:
        country_buckets[cc].sort(key=lambda x: x["latency"])

    selected_nodes = []
    bucket_lists = [country_buckets[cc] for cc in country_buckets]
    
    while len(selected_nodes) < 600 and bucket_lists:
        next_round_buckets = []
        for bucket in bucket_lists:
            if bucket:
                selected_nodes.append(bucket.pop(0))
                if len(selected_nodes) >= 600:
                    break
                next_round_buckets.append(bucket)
        bucket_lists = next_round_buckets

    selected_nodes.sort(key=lambda x: x["latency"])

    with open("ip_list.txt", "w", encoding="utf-8") as f:
        for node in selected_nodes:
            country_name = COUNTRY_MAP.get(node["cc"], node["cc"])
            line_str = f"{node['ip']}:{node['port']}#{node['cc']}{country_name} [{node['latency']:.2f}ms]\n"
            f.write(line_str)
            
    print(f"大功告成！已筛选出 {len(selected_nodes)} 个节点，并成功保存至 ip_list.txt")

if __name__ == "__main__":
    main()
