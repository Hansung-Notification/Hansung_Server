from collections import OrderedDict
import datetime
from pyfcm import FCMNotification
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import inko
import os
import json
from scraper import scrapeNotices
from datetime_util import nowKoreaTime

# Firebase database 인증을 위해 환경변수 값을 읽어온다. Heroku의 환경변수를 확인하면 된다.
cred_json = OrderedDict()
cred_json["type"] = os.environ["type"]
cred_json["project_id"] = os.environ["project_id"]
cred_json["private_key_id"] = os.environ["private_key_id"]
cred_json["private_key"] = os.environ["private_key"].replace('\\n', '\n')
cred_json["client_email"] = os.environ["client_email"]
cred_json["client_id"] = os.environ["client_id"]
cred_json["auth_uri"] = os.environ["auth_uri"]
cred_json["token_uri"] = os.environ["token_uri"]
cred_json["auth_provider_x509_cert_url"] = os.environ["auth_provider_x509_cert_url"]
cred_json["client_x509_cert_url"] = os.environ["client_x509_cert_url"]
JSON = json.dumps(cred_json)
JSON = json.loads(JSON)

APIKEY = os.environ["APIKEY"]
NOTICE_IDS_DB_PATH = "notice_ids"
KEYWORDS_DB_PATH = "keywords"
ADMIN_TOPIC = "admin_monitoring"

cred = credentials.Certificate(JSON)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ["databaseURL"]
})

# 파이어베이스 콘솔에서 얻어 온 API키를 넣어 줌
push_service = FCMNotification(api_key=APIKEY)

def importSubscribedKeywords():
    r"""
    파이어 베이스에서 구독된 키워드 목록을 반환한다.

    키워드를 조회하는 도중 구독자 수가 0 이하인 항목은 제거한다.
    """
    keywords = []
    dir = db.reference().child(KEYWORDS_DB_PATH)
    snapshot = dir.get()
    for keyword, count in snapshot.items():
        if int(count) <= 0:
            dir.child(keyword).delete()
            print("[", keyword, "]", "가 삭제되었습니다: ", count)
        else:
            keywords.append(keyword)

    return keywords

def importPreviousNoticeIds():
    r"""
    이전 공지사항의 id들을 하나의 문자열로 반환한다.

    이전 항목이 없는 경우 빈 문자열을 반환한다.
    """
    dir = db.reference().child(NOTICE_IDS_DB_PATH)
    snapshot = dir.get()
    for _, ids in snapshot.items():
        return ids
    return ""

def sendMessage(topic, title, url):
    data_message = {
        "url": url,
        "title": title
    }
    # 한글은 키워드로 설정할 수 없기 때문에 한영변환을 한다.
    topic = inko.Inko().ko2en(topic)
    # 구독한 사용자에게만 알림 전송
    push_service.notify_topic_subscribers(topic_name=topic, data_message=data_message)

def sendErrorMessage(message):
    now = datetime.datetime.now().isoformat()
    sendMessage(ADMIN_TOPIC, "ERROR at " + now + ", " + message, " ")

def sendMessageIfNoticeHasKeyword(notice, keywords):
    r"""
    공지사항 제목에 포함된 키워드를 찾아 해당 키워드를 토픽으로 알림을 보낸다.
    """
    for keyword in keywords:
        if keyword in notice.title:
            print(keyword, end=", ")
            sendMessage(keyword, notice.title, notice.url)

def updateNoticeIdsDatabase(newNoticeIds):
    dir = db.reference().child(NOTICE_IDS_DB_PATH)
    dir.update({NOTICE_IDS_DB_PATH: newNoticeIds})
    print("\n" + "newPost IDs: " + newNoticeIds)

def createNewNoticeIds(notices):
    result = ""
    for notice in notices:
        result += notice.id + ','
    return result.removesuffix(',')

def runBot():
    print("-----------------------------------------------")
    now = datetime.datetime.now()
    print("Date: " + now.isoformat())

    try:
        notices = scrapeNotices()
    except Exception:
        sendErrorMessage('Scraping 실패')
        return
    previousNoticeIds = importPreviousNoticeIds()
    keywords = importSubscribedKeywords()
    
    for notice in notices:
        if notice.id in previousNoticeIds:
            break
        sendMessageIfNoticeHasKeyword(notice, keywords)
        
    newNoticeIds = createNewNoticeIds(notices)
    if newNoticeIds is not None and newNoticeIds != "" and previousNoticeIds != newNoticeIds:
        updateNoticeIdsDatabase(newNoticeIds)
    
    print("-----------------------------------------------")

now = nowKoreaTime()
weekday = now.weekday()
# 월 ~ 금, 9시 ~ 20시 59분 사이에서만 구동한다.
if 0 <= weekday <= 4 and 9 <= now.hour <= 20:
    runBot()