"""常量定义"""


class BilibiliAPI:
    """Bilibili API 接口地址"""
    # 收藏夹相关接口
    FAVORITE_LIST = "https://api.bilibili.com/x/v3/fav/folder/created/list"  # 获取用户收藏夹列表
    FAVORITE_INFO = "https://api.bilibili.com/x/v3/fav/resource/list"  # 获取收藏夹内容
    
    # 视频相关接口
    VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"  # 获取视频信息
    VIDEO_PLAY_URL = "https://api.bilibili.com/x/player/playurl"  # 获取视频播放链接


class BilibiliSelectors:
    """Bilibili 页面选择器"""
    # 视频卡片选择器
    VIDEO_CARD_SELECTORS = [
        "a.bili-cover-card",
        "div.bili-video-card__cover > a",
        "a[href*='bilibili.com/video/BV']"
    ]
    
    # 分页相关选择器
    PAGINATION_CONTAINER = "div.vui_pagenation"
    PAGE_COUNT = "span.vui_pagenation-go__count"
    PAGE_BUTTONS = "button.vui_pagenation--btn-num"
    ACTIVE_PAGE_BUTTON = "button.vui_button--active.vui_pagenation--btn-num"
    NEXT_BUTTON = "button.vui_pagenation--btn-side:not([disabled])"
    PAGE_INPUT = "input.vui_input__input"


class BilibiliPatterns:
    """Bilibili 页面正则模式"""
    BV_NUMBER = r"(BV\w+)"
    TOTAL_PAGES = r"共\s*(\d+)\s*页"
    
    # 标题匹配模式
    TITLE_PATTERNS = [
        r'<h1[^>]*class="video-title[^"]*"[^>]*>([^<]*)</h1>',
        r'<h1[^>]*data-title="([^"]*)"[^>]*>',
        r'<h1[^>]*title="([^"]*)"[^>]*>',
        r'<title data-vue-meta="true">(.*?)</title>',
        r'<title>(.*?)</title>',
        r'"title":"([^"]*)"',
        r'"name":"([^"]*)"'
    ]
    
    # 播放信息匹配模式
    PLAYINFO_PATTERNS = [
        r'window\.__playinfo__=(.*?)</script>',
        r'window\.__INITIAL_STATE__=(.*?)</script>',
        r'"playurl":"([^"]*)"',
        r'"audio":"([^"]*)"'
    ]


class DownloadConfig:
    """下载配置"""
    MAX_RETRIES = 3
    PAGE_LOAD_TIMEOUT = 10
    PAGE_CHANGE_TIMEOUT = 15
    NETWORK_TIMEOUT = 30
    
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "audio",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site"
    }

