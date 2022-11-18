from scraper import scrapeNotices
from datetime_util import nowKoreaTime
import firebase
from notice import Notice
import time

def sendMessageIfNoticeHasKeyword(notice: Notice, keywords: list[str]):
    r"""
    공지사항 제목에 포함된 키워드를 찾아 해당 키워드를 토픽으로 알림을 보낸다.
    """
    for keyword in keywords:
        if keyword in notice.title:
            print(keyword, end=", ")
            firebase.sendMessage(keyword, notice.title, notice.url)

def createNewNoticeIds(notices: list[Notice]) -> str:
    result = ""
    for notice in notices:
        result += notice.id + ','
    return result.removesuffix(',')

def runBot():
    print("-----------------------------------------------")
    print("Date: " + nowKoreaTime().isoformat())

    try:
        notices = scrapeNotices()
        firebase.sendErrorMessage(notices)
    except Exception:
        firebase.sendErrorMessage('Scraping 실패')
        return
    previousNoticeIds = firebase.importPreviousNoticeIds()
    keywords = firebase.importSubscribedKeywords()
    
    for notice in notices:
        if notice.id not in previousNoticeIds:
            print('New post: ' + notice.title)
            sendMessageIfNoticeHasKeyword(notice, keywords)
        
    newNoticeIds = createNewNoticeIds(notices)
    if newNoticeIds != "" and previousNoticeIds != newNoticeIds:
        firebase.updateNoticeIdsDatabase(newNoticeIds)
    
    print("-----------------------------------------------")

print("실행됨==========VVVVVV")
print(nowKoreaTime().isoformat())
time.sleep(60 * 10)

# NOW = 
# # 매일 8시 ~ 22시 59분 사이에서만 구동한다.
# if 8 <= NOW.hour <= 22:
#     firebase.init()
#     # runBot()