import os
import re
import sys
import requests

# 替代 notify 功能
def send(title, message):
    print(f"{title}:\n{message}")

# 获取环境变量 
def get_env(): 
    # 判断 COOKIE_QUARK是否存在于环境变量 
    if "COOKIE_QUARK" in os.environ: 
        # 读取系统变量以 \n 或 && 分割变量 
        cookie_list = re.split(r'\n|&&', os.environ.get('COOKIE_QUARK')) 
        # 过滤掉空字符串
        cookie_list = [c for c in cookie_list if c.strip()]
    else: 
        # 标准日志输出 
        print('❌未添加COOKIE_QUARK变量') 
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量') 
        sys.exit(1) # 改为异常退出状态码

    return cookie_list 

class Quark:
    '''
    Quark类封装了签到、领取签到奖励的方法
    '''
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            response = requests.get(url=url, params=querystring).json()
            if response.get("data"):
                return response["data"]
        except Exception as e:
            print(f"请求成长信息失败: {e}")
        return False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        try:
            response = requests.post(url=url, json=data, params=querystring).json()
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            else:
                return False, response.get("message", "未知错误")
        except Exception as e:
            return False, str(e)

    def do_sign(self):
        log = ""
        is_success = True # 标记当前账号是否成功
        
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user', '未知')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：")
            if "sign_reward" in growth_info['cap_composition']:
                log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
            else:
                log += "0 MB\n"
                
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
                )
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                        f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                    )
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
                    is_success = False
        else:
            log += "❌ 签到异常: 获取成长信息失败(Cookie可能已失效)\n"
            is_success = False
            
        return log, is_success


def main():
    msg = ""
    cookie_quark = get_env()
    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    has_error = False # 全局错误标记

    for i, cookie_str in enumerate(cookie_quark):
        user_data = {} 
        for a in cookie_str.replace(" ", "").split(';'):
            if a:
                # 安全地分割键值对
                parts = a.split('=', 1)
                if len(parts) == 2:
                    user_data[parts[0]] = parts[1]
        
        log_header = f"🙍🏻‍♂️ 第{i + 1}个账号:\n"
        msg += log_header
        
        log_body, is_success = Quark(user_data).do_sign()
        msg += log_body + "\n"
        
        if not is_success:
            has_error = True

    try:
        send('夸克自动签到结果', msg)
    except Exception as err:
        print(f"❌ 消息发送错误: {err}")

    # 如果有任何一个账号失败，抛出异常，让 Github Actions 标记为失败，从而触发邮件/通知提醒
    if has_error:
        print("\n❌ 检测到部分或全部账号签到失败，脚本异常退出，请检查 Cookie。")
        sys.exit(1) 


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
