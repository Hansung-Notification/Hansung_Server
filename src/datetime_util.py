from pytz import timezone
from datetime import datetime

def nowKoreaTime() -> datetime:
    return datetime.now(timezone('Asia/Seoul'))

# 테스트용 코드
if __name__ == "__main__":
    print(nowKoreaTime().weekday())