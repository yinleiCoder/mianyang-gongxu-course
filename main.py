import os
import re
import json
import time
import math
import requests
import subprocess
import itertools
import execjs
import ddddocr
from tqdm import tqdm

JSESSIONID = ''

def check_four_digits(var, exact_match=True):
    """
    检查变量中的4位数字
    
    Parameters:
    var: 要检查的变量
    exact_match: 是否要求正好是4位数字（True），还是包含4位数字即可（False）
    """
    if exact_match:
        # 正好是4位数字
        if isinstance(var, str):
            return len(var) == 4 and var.isdigit()
        elif isinstance(var, int):
            return 1000 <= var <= 9999
    else:
        # 包含4位数字
        if isinstance(var, str):
            return bool(re.search(r'\d{4}', var))
    
    return False

# 验证码
def verify_code() -> str:
    headers = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://rsjapp.mianyang.cn/jxjy/pc/member/login.jhtml",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/code/getImgCode.do"
    params = {
        "sid": execjs.eval('Math.random()')
    }
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    code = ''
    with open('verifyCode.jpg', 'wb') as file:
        file.write(response.content)
        ocr = ddddocr.DdddOcr()
        code = ocr.classification(response.content)
    print(f"识别的验证码: {code}")
    if(len(code) != 4 and not(check_four_digits(code))):
        return verify_code()
    return code

# 登录流程
def login():
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Referer": "https://rsjapp.mianyang.cn/jxjy/pc/index.jhtml",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/member/login.jhtml"
    response = requests.get(url, headers=headers)
    global JSESSIONID
    JSESSIONID = response.cookies.get('JSESSIONID')
    code = verify_code()
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://rsjapp.mianyang.cn",
        "Referer": "https://rsjapp.mianyang.cn/jxjy/pc/member/login.jhtml",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcUserCoreController/login.do"
    account = input('绵阳公需课用户名:')
    password = input('绵阳公需课密码:')
    payload = execjs.compile(open('index.js', 'r', encoding='utf-8').read()).call('getLoginPayload', account, password, code)
    data = {
        "pspUserAccount": payload["pspUserAccount"],
        "pspUserPwd": payload["pspUserPwd"],
        "verCode": payload["verCode"],
        "loginType": payload["loginType"],
        "pspUserType": payload["pspUserType"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    return_data = execjs.compile(open('index.js', 'r', encoding='utf-8').read()).call('decryptReturnData', response.text)
    data_dict = json.loads(return_data)
    try:
        user_info = data_dict['resultData']['userInfo']# 一般是验证码有问题
    except KeyError:
        print("[tip]: 用户名、密码或验证码不正确，请重试！")
        return login()
    return {
        "userInfo": user_info,
        "aac001": data_dict['resultData']['aac001'],
    }

# 解密数据
def decrypt_data(data):
    return_data = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('decryptResultData', data)
    return json.loads(return_data)

# 课程列表
def get_course_list(aac001, pageNum):
    # aac001：1097306909651341312
    # 用户信息：myf003.do
    # 课程列表：myd001.do
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://rsjapp.mianyang.cn",
        "Referer": "https://rsjapp.mianyang.cn/jxjy/pc/wdkc_1646108788000/index.jhtml",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd001.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('getCourseList', aac001, pageNum)
    data = {
        "pageNum": payload["pageNum"],
        "size": payload["size"],
        "adz121": payload["adz121"],
        "adz123": payload["adz123"],
        "adf088": payload["adf088"],
        "sort": payload["sort"],
        "adz280": payload["adz280"],
        "aac001": payload["aac001"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    data_dict = decrypt_data(response.text)
    return data_dict["resultData"]["data"]["data"]

# 获取某课程的章节视频数据
def get_chapter_list(courseInfo, aac001):
    # aac001是用户唯一id
    # courseInfo["adz280"]是课程的id
    # myd003.do 查询课程详细信息
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://rsjapp.mianyang.cn",
        "Pragma": "no-cache",
        "Referer": f"https://rsjapp.mianyang.cn/jxjy/pc/zxxx_1646619915000/index.jhtml?adz280={courseInfo["adz280"]}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd003.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('getChapterList', courseInfo["adz280"], aac001)
    data = {
        "adz280": payload["adz280"],
        "aac001": payload["aac001"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    data_dict = decrypt_data(response.text)
    return data_dict['resultData']['data']['data']

# 获取mp4文件的总时长(ffprobe)ffprobe -i https://rsjapp.mianyang.cn/jxjy/psp/resource/ZJSITE/CYYQPC/video/videoFile/1713856016594.mp4 -show_entries format=duration -v quiet -of csv="p=0"
def get_video_duration_ffprobe_json(video_url):
    try:
        cmd = [
            'ffprobe', 
            '-i', video_url,
            '-show_entries', 'format=duration',
            '-v', 'quiet',
            '-print_format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"ffprobe执行失败: {result.stderr}")
            return None
            
        # 解析JSON输出
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
    except Exception as e:
        print(f"错误: {e}")
        return None
    
# 观看课程
def watch_chapter_video(courseInfo, aac001, video_data):
    courseId = courseInfo["adz280"]
    videoId = video_data["adz290"]
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://rsjapp.mianyang.cn",
        "Referer": f"https://rsjapp.mianyang.cn/jxjy/pc/zxxx_1646619915000/index.jhtml?adz280={courseId}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd004.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('getVideoData', video_data.get("adz127", ""), videoId, aac001)
    data = {
        "adz127": payload["adz127"],
        "adz290": payload["adz290"],
        "aac001": payload["aac001"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    antiStealingLinkMap = decrypt_data(response.text)['resultData']['data']['data']

    # 获取mp4视频文件，并得到视频的总长度
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getVideoData.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('getVideoDetailData', antiStealingLinkMap.get("adz166", ""), antiStealingLinkMap["adz168"])
    data = {
        "adz168": payload["adz168"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    data_dict = decrypt_data(response.text)['resultData']
    fileFormat = data_dict['fileFormat']
    fileId = data_dict['fileId']
    video_src = f"https://rsjapp.mianyang.cn/jxjy/psp/resource/ZJSITE/CYYQPC/video/videoFile/{fileId}"
    video_type = f"video/{fileFormat}"
    video_duration = get_video_duration_ffprobe_json(video_src)
    # print(video_duration)
    # 秒刷课程
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd007.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('finishWatchCourse',videoId, aac001, video_duration)
    data = {
        "adz290": payload["adz290"],
        "aac001": payload["aac001"],
        "adz341": payload["adz341"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    data_dict = decrypt_data(response.text)
    # print(data_dict)
    if data_dict["resultData"]["data"]["code"] == "1":
        # 保存播放记录
        url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd005.do"
        payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('saveVideoPlayRecord',videoId, aac001, video_duration)
        data = {
            "adz290": payload["adz290"],
            "aac001": payload["aac001"],
            "adz341": payload["adz341"],
            "encodeKey": payload["encodeKey"]
        }
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        data_dict = decrypt_data(response.text)
        if data_dict["resultData"]["data"]["code"] == "1" and data_dict["resultData"]["data"]["data"]["complete"] == "0":
            # print(f"视频《{video_data["adz125"]}》")
            # time.sleep(20)
            pass

# 展示某课程章节信息
def summary_chapter_info(chapter):
    print(f"\n课程标题：{chapter["adz121"]}")
    print(f"课程ID：{chapter["adz280"]}")
    print(f"课程简介：{chapter["adz124"]}")
    print(f"课程时间：{chapter["aae036"]}")
    print(f"课程章节信息：")
    directory = chapter["directory"]
    for dir in directory:
        print(f"\t视频标题：{dir["adz125"]}\tVideoID：{dir["adz290"]}\t{"已学完" if dir["videoOver"]==1 else ""}")
    print()

# 在线考试
def do_online_test(exam_url, adz012, adz280, aac001):
    currentAnsweringQuestionIndex = 1# 当前正在答题的题目
    currentAnsweringQuestion = {}
    questionList_1 = []# 单选题
    questionList_2 = []# 多选题
    questionList_3 = []# 判断题
    questions = list(itertools.chain(questionList_1, questionList_2, questionList_3))# 答题卡

    # adz012是否正式考试，adz280是当前课程id，aac001是当前考试用户
    if adz012 == 0:# 测试考试
        print(f"[tip]: 模拟测试: {adz280}, 考试地址：{exam_url}")
    elif adz012 == 1:# 正式考试
        print(f"[tip]: 正式考试: {adz280}，考试地址：{exam_url}")
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://rsjapp.mianyang.cn",
        "Referer": f"https://rsjapp.mianyang.cn/jxjy/pc/ksz_1646185391000/index.jhtml?&adz012={adz012}&adz280={adz280}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "JSESSIONID": JSESSIONID
    }
    
    # 1.查询卷面头部信息
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/mye001.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('queryTestPaper', aac001, adz012, adz280)
    data = {
        "aac001": payload["aac001"],
        "adz012": payload["adz012"],
        "adz280": payload["adz280"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    data_dict = decrypt_data(response.text)["resultData"]["data"]["data"]
    print(f"\t试卷题目: {data_dict["adz401"]}")
    print(f"\t考试时长: {data_dict["adz614"]} 分钟\t题目总数: {data_dict["cunt"]} 道")
    # 通过adz420拿到人员考试信息, adz420和adz012 adz280 aac001作为请求头
    adz420 = data_dict["adz420"]

    # 2.查询答题卡、试题
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/mye002.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('queryTestQuestionCards', aac001, adz012, adz280, adz420)
    data = {
        "aac001": payload["aac001"],
        "adz012": payload["adz012"],
        "adz280": payload["adz280"],
        "adz420": payload["adz420"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    questionsMap = decrypt_data(response.text)['resultData']['data']['data']['questionsMap']
    questionList_1 = questionsMap["questionList_1"]
    questionList_2 = questionsMap["questionList_2"]
    questionList_3 = questionsMap["questionList_3"]
    questions = list(itertools.chain(questionList_1, questionList_2, questionList_3))# 答题卡
    for item in questions:
        if currentAnsweringQuestionIndex == item["xh"]:
            currentAnsweringQuestion = item
    adz010 = currentAnsweringQuestion["adz010"]# adz010也是必须传递, adz010是题目ID

    # 3.查询试题
    url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/mye003.do"
    payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('queryTestQuestions', aac001, adz012, adz280, adz420, adz010)
    data = {
        "aac001": payload["aac001"],
        "adz012": payload["adz012"],
        "adz280": payload["adz280"],
        "adz420": payload["adz420"],
        "adz010": payload["adz010"],
        "encodeKey": payload["encodeKey"]
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    questionMap = decrypt_data(response.text)['resultData']['data']['data']['questionMap']
    print(questionMap)
    option = questionMap["option"]# 题目题干
    adz001 = option["adz001"]# adz001也是必须要传的参数, 1为单选、3为判断、2为多选
    currentAnsweringQuestion["adz430"] = option["adz430"]
    currentAnsweringQuestion["option.adz010"] = option["adz010"]# data-component
    currentAnsweringQuestion["title"] = option["adz002"]# 当前题目的试题题干
    optionList = questionMap["optionList"]# 题目选项
    # optionList[0]["adz004"] # 选项序号 data-Value=" + item.adz004
    # optionList[0]["adz005"] # 选项描述
    
# 获取全部课程
def get_all_course():
    courseData = get_course_list(aac001, "1")
    pageTotal = math.ceil(int(courseData["total"])/int(courseData["size"]))
    allCourses = []
    for pageNum in range(pageTotal):
        courseData = get_course_list(aac001, str(pageNum+1))
        allCourses.extend(courseData["list"])
    return allCourses

# 选择一门课并刷课
def select_single_course(courses, aac001):
    isFirstSelect = True
    while isFirstSelect:
        print(f"[tip]: 公需平台现有全部课程：")
        for index, course in enumerate(courses):
            print(f"\t{index+1}.{course["adz121"]}\t->\t{"已选课" if course["adz175"]==1 else "未选课"}\t{"学习完成" if course["study"]==1 else "未完成"}\t{"考试合格" if course["test"]==1 else "考试未通过或未开始"}")
        
        currentCourse = courses[int(input("[tip] 请输入要刷课程的索引：")) - 1]
        currentCourseId = currentCourse["adz280"]
        currentCourseTitle = currentCourse["adz121"]
        if currentCourse["adz175"] != 1:# 未选课
            # 选课
            headers = {
                "sec-ch-ua-platform": "\"Windows\"",
                "Referer": "https://rsjapp.mianyang.cn/jxjy/pc/wdkc_1646108788000/index.jhtml",
                "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
            url = "https://rsjapp.mianyang.cn/jxjy/pc/lcService/getData/myd002.do"
            cookies = {
                "JSESSIONID": JSESSIONID
            }
            payload = execjs.compile(open('course.js', 'r', encoding='utf-8').read()).call('selectCourse', currentCourseId,aac001)
            data = {
                "adz280": payload["adz280"],
                "aac001": payload["aac001"],
                "encodeKey": payload["encodeKey"]
            }
            response = requests.post(url, headers=headers, cookies=cookies, data=data)
            data_dict = decrypt_data(response.text)
            print("[tip]: 选课成功...")
        if currentCourse["study"] != 1:# 未学完，秒课
            # 获取adz280同时adz175=1则为开始学习：https://rsjapp.mianyang.cn/jxjy/pc/zxxx_1646619915000/index.jhtml?adz280=
            # adz280是大视频标识（位于locaiton.href = url中）
            chapter = get_chapter_list(currentCourse, aac001)
            summary_chapter_info(chapter)
            directory = chapter["directory"]
            print(f"[tip]: 课程《{currentCourseTitle}》，共{len(directory)}个视频，现在开始刷课！")
            for videoData in tqdm(directory):
                watch_chapter_video(currentCourse, aac001, videoData)
            print(f"[tip]: 课程《{currentCourseTitle}》结束刷课！")
        else: # 学完！考试
            print("[tip]: 在线考试功能的代码正在开发中...")
        
        isStillWork = input("是否继续?(请输入Y/N): ")
        if "y" in isStillWork.lower() or "yes" in isStillWork.lower():
            isFirstSelect = True
        elif "n" in isStillWork.lower() or "no" in isStillWork.lower():
            isFirstSelect = False

if __name__ == '__main__':
    logined_data = login()
    user, aac001 = logined_data['userInfo'], logined_data['aac001']
    # aac001是用户标识
    print(f"\n[tip]: 欢迎 {user["adz501"]} - {user["adz50b_desc"]} - {user["aac003"]} 老师！")
    print("[tip]: 绵阳市专业技术人员继续教育公需科目培训平台：https://rsjapp.mianyang.cn/jxjy/pc/wdkc_1646108788000/index.jhtml\n")
    
    # 分页获取所有课程
    all_courses = get_all_course()
    
    # 展示并选择课程
    select_single_course(all_courses, aac001)

    print("[tip]: 感谢您的使用，我是代码开发者尹磊老师")

    # # 考试！
    # print(f"[tip]: 课程《{currentCourseTitle}，现在开始考试！")
    # param = 0 # 0为测试考试，1为正式考试
    # exam_online_url = f"https://rsjapp.mianyang.cn/jxjy/pc/ksz_1646185391000/index.jhtml?&adz012={param}&adz280={currentCourse["adz280"]}"
    # do_online_test(exam_online_url, param, currentCourseId, aac001)
    # print(f"[tip]: 课程《{currentCourseTitle}，结束考试！")