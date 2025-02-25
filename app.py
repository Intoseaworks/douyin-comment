# app.py
from flask import Flask, render_template, request, jsonify
import requests
import re

app = Flask(__name__)

# 配置参数（需手动更新）
DOUYIN_CONFIG = {
    "sessionid": "435345345345345345345",
    "sid_guard": "53d97c49c3251ce02c54654645645634534534265768-Apr-2025+07%3A16%3A58+GMT",
    "msToken": "UPDATE_EVERY_TIME",
    "a_bogus": "UPDATE_EVERY_TIME"
}

def extract_sec_uid(url):
    """从用户主页URL提取sec_uid"""
    match = re.search(r'/user/(MS4wLjAB[^/?]+)', url)
    return match.group(1) if match else None

def extract_aweme_id(url):
    """从视频URL提取视频ID"""
    patterns = [
        r'/video/(\d+)',
        r'v.douyin.com/\w+/',
        r'www.iesdouyin.com/share/video/(\d+)/'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: 
            return match.group(1) if pattern != r'v.douyin.com/\w+/' else match.group(0).split('/')[-2]
    return None

def douyin_request(url, params=None):
    """通用请求方法"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={DOUYIN_CONFIG['sessionid']}; sid_guard={DOUYIN_CONFIG['sid_guard']}",
        "Referer": "https://www.douyin.com/"
    }
    return requests.get(url, params=params, headers=headers)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_comments', methods=['POST'])
def handle_comments():
    req_data = request.json
    video_url = req_data.get('video_url')
    aweme_id = req_data.get('aweme_id')
    cursor = req_data.get('cursor', 0)
    
    # 参数处理
    if not aweme_id and video_url:
        aweme_id = extract_aweme_id(video_url)
    if not aweme_id:
        return jsonify({"error": "无效的视频参数"}), 400
    
    # 构造请求参数
    params = {
        "device_platform": "webapp",
        "aid": "6383",
        "aweme_id": aweme_id,
        "cursor": cursor,
        "count": 20,
        "msToken": DOUYIN_CONFIG["msToken"],
        "a_bogus": DOUYIN_CONFIG["a_bogus"],
        "channel": "channel_pc_web",
        "locate_query": "false",
        "show_live_replay_strategy": 1
    }
    
    try:
        response = douyin_request(
            "https://www.douyin.com/aweme/v1/web/comment/list/",
            params=params
        )
        data = response.json()
        
        # 关键修复：确保comments字段为列表
        comments = data.get("comments") or []
        
        formatted = []
        for comment in comments:
            user = comment.get("user", {})
            formatted.append({
                "user_id": user.get("uid"),
                "sec_uid": user.get("sec_uid"),
                "avatar": user.get("avatar_thumb", {}).get("url_list", [""])[0],
                "username": user.get("nickname"),
                "content": comment.get("text"),
                "time": comment.get("create_time"),
                "region": user.get("ip_label", "未知"),
                "digg_count": comment.get("digg_count", 0)
            })
        
        return jsonify({
            "comments": formatted,
            "has_more": data.get("has_more", False),
            "cursor": data.get("cursor", 0)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_user_videos', methods=['POST'])
def handle_user_videos():
    profile_url = request.json.get('profile_url')
    sec_uid = extract_sec_uid(profile_url)
    
    if not sec_uid:
        return jsonify({"error": "无效的用户主页链接"}), 400
    
    try:
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "sec_user_id": sec_uid,
            "max_cursor": 0,
            "count": 18,
            "msToken": DOUYIN_CONFIG["msToken"],
            "a_bogus": DOUYIN_CONFIG["a_bogus"],
            "channel": "channel_pc_web",
            "publish_video_strategy_type": 2
        }
        
        response = douyin_request(
            "https://www.douyin.com/aweme/v1/web/aweme/post/",
            params=params
        )
        data = response.json()
        
        videos = []
        for aweme in data.get("aweme_list", []):
            videos.append({
                "aweme_id": aweme.get("aweme_id"),
                "desc": aweme.get("desc") or "未命名视频",
                "cover": aweme.get("video", {}).get("cover", {}).get("url_list", [""])[0]
            })
        
        return jsonify({"videos": videos})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)