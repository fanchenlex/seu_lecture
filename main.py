import requests
import base64
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

# 验证码解析参数
verify_code_params = {
    'user': 'syyshitu',
    'pass': 'al31ue3e',
    'softid': '974790',
    'codetype': 1902,
    'file_base64': ''
}

# 讲座系统请求头
lecture_headers = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
  'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
  'Cache-Control': 'max-age=0',
  'Connection': 'keep-alive',
  'Cookie': 'route=de1353bd2eecd92e44c51ddb2c26661d; route=de1353bd2eecd92e44c51ddb2c26661d; GS_SESSIONID=2343ce4b86e7ebd5e7f9c60ff41381d8; _WEU=vZaWHpjpo23wtpwx4BhEraOukshqOSZBejLNAP81T8xNaHVQ8xYPb2SvWpHv3*JNsBYYkwRfYE4MBeBwU*UhaFM8XzCq9tcSE5luvyys_dm7iK7QXX*jzoz09jmoCkqma17M0qHy7bwbI1um91IPbv462UaTi3HJCxjRZxCG8J6GGPIhaWaHDWBGYXh*WqG*BQh1lV9AO9zXwQz9KUqbhY1CfpGtN8kf_ZaAY0CWNcLfBlt6pZoFPo0JV*vFygi*cVgBq7nFbDEiFDPyo9QyeUSFSH3wAI9EuYNbzhCHJM0C7xZocwCMIyjAJnKEOfRekLv6kHMJ5iP0XvlR*fl5cj..; amp.locale=zh_CN; iPlanetDirectoryPro=NRyb5l13NELJpPRceAUtRd; JSESSIONID=vAYNDjmJdBsryoKip2o-iOk2a4OXfUe5XsYJrHsxaHIbikDtIOsj!1584378074',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'none',
  'Sec-Fetch-User': '?1',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
  'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"'
}

# 验证码解析请求头
verify_code_headers = {
    'Connection': 'Keep-Alive',
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
}

# 目标讲座关键词，请尽可能指向唯一目标
lecture_keys = ["【线上】【法律】xxx"]

# 预约开始时间（24小时制）
reserve_hour = 19  # 19点
reserve_minute = 0  # 0分

def parse_verify_code(img_base64):
    """
    解析验证码

    Args:
        img_base64 (bytes): 验证码图片的base64字节码

    Returns:
        str: 解析的验证码
    """
    
    verify_code_params['file_base64'] = img_base64
    
    r = requests.post(
        url='http://upload.chaojiying.net/Upload/Processing.php', 
        data=verify_code_params, 
        headers=verify_code_headers,
    )
    res = r.json()

    if res['err_no'] == 0:
        return res['pic_str']
    else:
        print(f"解析验证码出错: {res['err_str']}")
        return None

def get_target_lectures(keys):
    """
    获取目标讲座信息

    Args:
        keys (list): 讲座名称关键词列表

    Returns:
        list: 讲座数据列表
    """
    payload = {}

    url = "https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/modules/hdyy/queryActivityList.do"

    r = requests.request("GET", url, headers=lecture_headers, data=payload)
    
    if r.status_code != 200 or len(r.text) == 0:
        print("讲座列表接口响应不成功，请检查cookie！")
        return None
    
    res = r.json()  
    lecture_list = res['datas']['hdlbList']
    if lecture_list is None or len(lecture_list) == 0:
        print("当前没有任何讲座可预约！")
        return None
    
    target_list = []
    for key in keys:
        for item in lecture_list:
            if key in item['JZMC']:
                target_list.append(item)
                break
    
    if len(target_list) == 0:
        print("当前关键词没有搜索到任何讲座！")
        return None
    
    return target_list

def get_lecture_verify_code(wid):
    """
   获取指定讲座的验证码

    Args:
        wid (str): 讲座id
        
    Returns:
        bytes: 验证码图片的base64字节码
    """
    url='https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/modules/hdyy/vcode.do'
    r = requests.request("GET", url, headers=lecture_headers, params={'_': int(time.time() * 1000)})
    res = r.json()
    
    base64_str = res['datas']
    base64_str = base64_str[(base64_str.index("base64,") + 7):]
    return bytes(base64_str, encoding='utf-8')

def reserve_lecture(wid, verify_code):
    """
   预约指定讲座

    Args:
        wid (str): 讲座id
        verify_code (str): 验证码
    
    Returns:
        bool: 预约结果
    """
    
    params = {
        'wid': wid,
        'vcode': verify_code,
    }
    url='https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/modules/hdyy/addReservation.do'
    
    r = requests.request("POST", url, headers=lecture_headers, data=params)

    res = r.json()
    print('预约接口响应数据: ', res)
    
    return res['code'] == 0 and res['datas'] == 1
    
def keep_alive(wid):
    """
    获取指定讲座信息以保活

    Args:
        wid (str): 讲座id
    """
    url='https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/modules/hdyy/getActivityDetail.do'
    
    r = requests.request("POST", url, headers=lecture_headers, data={'wid': wid})
    
    res = r.json()
    if res['code'] != 0:
        print('保活失效，请检查cookie！')
    else:
        print('用户身份有效，登录状态保活')
    
def rob(lecture):
    """
    抢讲座任务（尝试多次）

    Args:
        lecture (dict): 讲座信息
    """
    
    print(f"\n{'='*60}")
    print(f"⏰ 定时预约任务开始！")
    print(f"📚 讲座: {lecture['JZMC']}")
    print(f"🆔 WID: {lecture['WID']}")
    print(f"{'='*60}\n")
    
    for attempt in range(3):
        print(f"[尝试 {attempt + 1}/3]")
        try:
            # 获取验证码图片
            verify_code_img_base64 = get_lecture_verify_code(lecture['WID'])
            # 解析验证码
            verify_code = parse_verify_code(verify_code_img_base64)
            if verify_code:
                print(f"✓ 验证码识别成功: {verify_code}")
            else:
                print("✗ 验证码识别失败，跳过本次尝试")
                continue
            
            # 尝试预约讲座
            res = reserve_lecture(lecture['WID'], verify_code)
            
            if res:
                print(f"\n{'='*60}")
                print("🎉 恭喜！预约成功！")
                print(f"{'='*60}\n")
                return True
            else:
                print(f"✗ 预约失败")
                
            if attempt < 2:
                print(f"⏱ 等待1秒后重试...\n")
                time.sleep(1)
        except Exception as e:
            print(f"✗ 发生错误: {e}")
            if attempt < 2:
                time.sleep(1)
    
    print(f"\n{'='*60}")
    print("❌ 3次尝试均失败")
    print(f"{'='*60}\n")
    return False

def rob_scheduled(lecture):
    """
    定时抢座任务（在19:00:00触发，在5个精确时间点尝试）
    
    Args:
        lecture (dict): 讲座信息
    """
    print(f"\n{'='*60}")
    print(f"⏰ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 抢座任务启动！")
    print(f"📚 讲座: {lecture['JZMC']}")
    print(f"{'='*60}\n")
    
    # 计算19:00:00的准确时间戳
    target_time = datetime.now().replace(hour=reserve_hour, minute=reserve_minute, second=0, microsecond=0)
    target_timestamp = target_time.timestamp()
    
    # 定义5个精确的尝试时间点（相对于19:00:00的偏移，单位：秒）
    attempt_times = [
        0.5,     # 19:00:00.500 (500毫秒)
        1.0,     # 19:00:01.000 (1秒整)
        1.1,     # 19:00:01.100 (1秒100毫秒)
        2.0,     # 19:00:02.000 (2秒整)
        3.0      # 19:00:03.000 (3秒整)
    ]
    
    for i, offset in enumerate(attempt_times, 1):
        # 计算目标时间
        target = target_timestamp + offset
        
        # 等待到目标时间
        current_time = time.time()
        wait_time = target - current_time
        
        if wait_time > 0:
            print(f"⏱ 等待 {wait_time:.3f}秒 到下一个时间点...")
            # 粗等待（留0.01秒精确等待）
            if wait_time > 0.01:
                time.sleep(wait_time - 0.01)
            # 精确等待
            while time.time() < target:
                time.sleep(0.0001)
        
        actual_time = datetime.now()
        offset_str = f"{reserve_hour:02d}:{reserve_minute:02d}:{int(offset):02d}.{int((offset % 1) * 1000):03d}" if offset >= 0 else f"{reserve_hour:02d}:{reserve_minute-1:02d}:59.{int(1000 + offset * 1000):03d}"
        print(f"\n[{actual_time.strftime('%H:%M:%S.%f')[:-3]}] 第{i}次尝试 (目标时间: {offset_str})")
        
        try:
            # 获取验证码图片
            verify_code_img_base64 = get_lecture_verify_code(lecture['WID'])
            # 解析验证码
            verify_code = parse_verify_code(verify_code_img_base64)
            
            if verify_code:
                print(f"  ✓ 验证码: {verify_code}")
                # 尝试预约讲座
                res = reserve_lecture(lecture['WID'], verify_code)
                
                if res:
                    print(f"  ✓ 预约成功！")
                    print(f"\n{'='*60}")
                    print("🎉🎉🎉 预约成功！🎉🎉🎉")
                    print(f"{'='*60}\n")
                    return True
                else:
                    print(f"  ✗ 预约失败")
            else:
                print(f"  ✗ 验证码识别失败")
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    print(f"\n{'='*60}")
    print(f"❌ 5次尝试均未成功")
    print(f"{'='*60}\n")
    return False
    

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("🎓 东南大学讲座预约脚本启动")
    print(f"{'='*60}\n")
    
    # 获取目标讲座信息
    lectures = get_target_lectures(lecture_keys)
    if lectures is None:
        print("❌ 未找到目标讲座，程序退出")
        exit(1)
    
    print(f"✓ 搜索到 {len(lectures)} 个目标讲座：")
    for i, lecture in enumerate(lectures, 1):
        print(f"  {i}. {lecture['JZMC']}")
    print()
    
    # 立即检查一次保活
    print("🔍 检查登录状态...")
    keep_alive(lectures[0]['WID'])
    print()
    
    # 显示预约时间配置
    now = datetime.now()
    reserve_time = now.replace(hour=reserve_hour, minute=reserve_minute, second=0, microsecond=0)
    
    # 如果配置的时间已经过了，则设置为明天的这个时间
    if reserve_time <= now:
        reserve_time = reserve_time + timedelta(days=1)
    
    print(f"⏰ 预约开始时间设置: {reserve_hour:02d}:{reserve_minute:02d}")
    print(f"📅 预约时间: {reserve_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏳ 距离预约开始还有: {(reserve_time - now).total_seconds() / 60:.1f} 分钟")
    print()
    
    # 启动定时任务
    scheduler = BlockingScheduler()
    
    # 添加保活任务，每30秒执行一次
    scheduler.add_job(keep_alive, 'interval', seconds=30, args=[lectures[0]['WID']])
    
    # 在整点前1秒执行一次保活，确保整点时状态最佳
    if reserve_minute > 0:
        pre_minute = reserve_minute - 1
        pre_second = 59
    else:
        pre_minute = 59
        pre_second = 59
    
    def pre_warm():
        """整点前预热"""
        print(f"\n⚡ [{datetime.now().strftime('%H:%M:%S')}] 整点前预热，最后一次保活...")
        keep_alive(lectures[0]['WID'])
        print(f"✓ 预热完成，等待整点开始抢座！\n")
    
    scheduler.add_job(
        pre_warm,
        'cron',
        hour=reserve_hour if reserve_minute > 0 else (reserve_hour - 1) % 24,
        minute=pre_minute,
        second=pre_second
    )
    
    # 在指定时间开始抢座，每个讲座都会尝试
    for lecture in lectures:
        # 在整点启动
        scheduler.add_job(
            rob_scheduled, 
            'cron', 
            hour=reserve_hour, 
            minute=reserve_minute,
            second=0,
            args=[lecture]
        )
    
    print("✓ 定时任务已配置")
    print(f"  - 保活任务: 每30秒执行一次，保持登录状态")
    print(f"  - 预热任务: 在 {reserve_hour:02d}:{pre_minute:02d}:{pre_second:02d} 执行最后一次保活")
    print(f"  - 抢座任务: 将在 {reserve_hour:02d}:{reserve_minute:02d}:00 准时启动")
    print(f"  - 抢座策略: 5次精确尝试")
    print(f"    1. {reserve_hour:02d}:{reserve_minute:02d}:00.500 (500毫秒)")
    print(f"    2. {reserve_hour:02d}:{reserve_minute:02d}:01.000 (1秒)")
    print(f"    3. {reserve_hour:02d}:{reserve_minute:02d}:01.100 (1秒100毫秒)")
    print(f"    4. {reserve_hour:02d}:{reserve_minute:02d}:02.000 (2秒)")
    print(f"    5. {reserve_hour:02d}:{reserve_minute:02d}:03.000 (3秒)")
    print()
    print("💡 提示: 脚本会在后台保持运行，到达预约时间后自动开始抢座")
    print("⚠️  请保持终端运行，不要关闭！按 Ctrl+C 可以停止脚本")
    print(f"{'='*60}\n")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
        scheduler.shutdown()
        print("再见！")
