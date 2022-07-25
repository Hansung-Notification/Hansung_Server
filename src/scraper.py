from http.client import HTTPException
from bs4 import BeautifulSoup 

import requests
from notice import Notice

BASE_URL = "https://www.hansung.ac.kr/"
REQUEST_URL = BASE_URL + "hansung/8385/subview.do"

def extractNumberFrom(string: str) -> int:
    return int(''.join(filter(str.isdigit, string)))

def scrapeNotices() -> list[Notice]:
    r"""
    한성대학교 전체 공지사항 첫 페이지를 헤더 공지를 제외하고 스크래핑하여 :class:`notice` 리스트를 반환한다.

    `BASE_URL`이 잘못된 경우 :class:`HTTPException`을 raise한다.
    """

    try:
        response = requests.get(REQUEST_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        if response.status_code is not requests.codes['ok']:
            raise HTTPException('잘못된 URL을 요청했습니다. (status code: {response.status_code})')
    except Exception as e:
        raise e

    result = []
    tableRows = soup.select('tbody>tr')
    for tableRow in tableRows:
        # 헤더 공지 혹은 블라인드 처리된 공지는 건너뛴다.
        if any(className in tableRow.attrs['class'] for className in ['notice', 'blind']):
            continue

        subject = tableRow.select_one('.td-subject > a[href]')
        href = subject['href']
        
        id = str(extractNumberFrom(href))
        title = subject.text.strip()
        url = BASE_URL + href.removeprefix("/")
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break
    
    return result

# 테스트용 코드
if __name__ == "__main__":
    testResult = scrapeNotices()
    for it in testResult:
        print(it.id)
    