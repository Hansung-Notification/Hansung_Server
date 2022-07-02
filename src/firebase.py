from collections import OrderedDict
import firebase_admin
from firebase_admin import credentials, db, messaging
import inko
import os
import json

NOTICE_IDS_DB_PATH = "notice_ids"
KEYWORDS_DB_PATH = "keywords"

ADMIN_TOPIC = os.environ["admin_error_topic"]

def init():
    """ 
    Firebase 앱을 초기화한다.
    
    Firebase database 인증을 위해 환경변수 값을 읽어온다. 환경변수는 Heroku에서 Setting으로 들어간 뒤 확인하면 된다. 
    """
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
    cred = credentials.Certificate(JSON)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ["databaseURL"]
    })

def sendMessage(topic, title, url):
    """
    title과 url을 데이터로 하여 topic을 주제로 알림을 전송한다.
    """
    data = {
        "url": url,
        "title": title
    }
    # 한글은 키워드로 설정할 수 없기 때문에 한영변환을 한다.
    topic = inko.Inko().ko2en(topic)
    
    message = messaging.Message(data=data, topic=topic)
    response = messaging.send(message)
    print('Successfully sent message:', response)

def sendErrorMessage(message):
    sendMessage(ADMIN_TOPIC, title="ERROR: " + message, url=" ")

def importSubscribedKeywords():
    r"""
    파이어 베이스에서 구독된 키워드 목록을 반환한다.

    키워드를 조회하는 도중 구독자 수가 0 이하인 항목은 제거한다.
    """
    keywords = []
    dir = db.reference().child(KEYWORDS_DB_PATH)
    snapshot = dir.get()
    if snapshot is None:
        return []
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
    if snapshot is None: 
        return ""
    for _, ids in snapshot.items():
        return ids
    return ""

def updateNoticeIdsDatabase(newNoticeIds):
    dir = db.reference().child(NOTICE_IDS_DB_PATH)
    dir.update({NOTICE_IDS_DB_PATH: newNoticeIds})
    print("\nUpdate " + NOTICE_IDS_DB_PATH + " DB:" + newNoticeIds)
