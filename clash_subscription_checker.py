import requests
import csv
import yaml
import concurrent.futures
from urllib.parse import urlparse, parse_qs

def fetch_subscription(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

def parse_clash_config(config_text):
    if not config_text:
        return False
    try:
        config = yaml.safe_load(config_text)
        if not isinstance(config, dict):
            return False
        proxies = config.get('proxies', [])
        return len(proxies) > 0
    except yaml.YAMLError:
        return False

def get_traffic_info(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    traffic_info = query_params.get('traffic', ['未知'])[0]
    return traffic_info

def check_subscription(url):
    config_text = fetch_subscription(url)
    if config_text and parse_clash_config(config_text):
        traffic_info = get_traffic_info(url)
        print(f"有效订阅: {url} (流量: {traffic_info})")
        return url, traffic_info
    return None

def main(input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error reading input file: {e}")
        return

    valid_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_subscription, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                result = future.result()
                if result:
                    valid_results.append(result)
            except Exception:
                pass  # 静默处理异常

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['订阅链接', '流量信息'])
            for url, traffic_info in valid_results:
                writer.writerow([url, traffic_info])
        print(f"有效结果已保存到 {output_file}")
    except IOError as e:
        print(f"Error writing to output file: {e}")

if __name__ == '__main__':
    input_file = 'urls.txt'  # 包含订阅链接的输入文件
    output_file = 'valid_subscriptions.csv'  # 结果输出的CSV文件
    main(input_file, output_file)
