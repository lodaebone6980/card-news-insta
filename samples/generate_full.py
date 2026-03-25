"""3개 카테고리 x 6장 카드뉴스 생성 + Supabase 저장"""
import asyncio
import json
import os
import sys
from pathlib import Path

# 환경변수 설정
os.environ.setdefault("SUPABASE_URL", "https://wtgjiuwivdhyidxyigza.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0Z2ppdXdpdmRoeWlkeHlpZ3phIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTc5ODY1MSwiZXhwIjoyMDg1Mzc0NjUxfQ.8gO_i233IGzFRVr_h6S4vcjnPiL3HS5tiNXPgkjduw8")

sys.path.insert(0, str(Path(__file__).parent.parent))
from playwright.async_api import async_playwright
from pipeline.database import save_card_history

SAMPLES_DIR = Path(__file__).parent
ADMIN_USER_ID = "26fc27da-9cb8-4805-8b0a-fae841c506a4"

# ─── 쇼핑 6장 HTML ───
SHOPPING_SLIDES = [
    # Slide 1: 표지
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#FF6B6B,#E74C3C,#C0392B);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:80px;position:relative}
    .badge{background:#FFF;color:#E74C3C;font-size:26px;font-weight:900;padding:12px 32px;border-radius:50px;margin-bottom:32px;letter-spacing:2px}
    .num{font-size:160px;font-weight:900;color:rgba(255,255,255,0.12);line-height:1;margin-bottom:-20px}
    h1{font-size:58px;font-weight:900;color:#FFF;line-height:1.3;margin-bottom:20px}
    p{font-size:28px;color:rgba(255,255,255,0.8)}
    .tag{position:absolute;bottom:80px;right:80px;background:#FFF200;color:#E74C3C;font-size:28px;font-weight:900;padding:14px 28px;border-radius:12px;transform:rotate(-4deg)}
    </style></head><body><div class="s"><span class="badge">SHOPPING PICK</span><div class="num">TOP 6</div><h1>2026 봄 시즌<br>가성비 꿀템 모음</h1><p>지금 안 사면 후회할 아이템만 골랐어요</p><div class="tag">최대 70% OFF</div></div></body></html>""",

    # Slide 2
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#FFF;padding:80px;display:flex;flex-direction:column;justify-content:center}
    .tag{display:inline-block;background:#E74C3C;color:#FFF;font-size:20px;font-weight:700;padding:8px 20px;border-radius:6px;margin-bottom:24px;letter-spacing:3px}
    .bg{font-size:100px;font-weight:900;color:rgba(231,76,60,0.06);line-height:1;margin-bottom:-12px}
    h2{font-size:42px;font-weight:900;color:#1A1A1A;margin-bottom:16px}
    .desc{font-size:26px;color:#555;line-height:1.6;border-left:4px solid #E74C3C;padding-left:20px;margin-bottom:28px}
    .price{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}
    .orig{font-size:26px;color:#999;text-decoration:line-through}
    .sale{font-size:48px;font-weight:900;color:#E74C3C}
    .off{background:#FFF200;color:#E74C3C;font-size:22px;font-weight:900;padding:6px 14px;border-radius:6px}
    .box{background:#FFF5F5;border-radius:14px;padding:24px;margin-top:24px}
    .box b{color:#E74C3C;font-size:18px}
    .box p{font-size:22px;color:#333;line-height:1.5;margin-top:8px}
    </style></head><body><div class="s"><span class="tag">PICK 01</span><div class="bg">01</div><h2>접이식 노트북 거치대</h2><p class="desc">자세 교정 + 발열 방지 일석이조<br>6단계 각도 조절, 알루미늄 소재</p><div class="price"><span class="orig">35,000원</span><span class="sale">14,900원</span><span class="off">57%</span></div><div class="box"><b>추천 이유</b><p>재택근무/카페 작업 시 거북목 방지에 진짜 효과 있어요. 무게 230g이라 가방에 쏙 들어감</p></div></div></body></html>""",

    # Slide 3
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#FFF;padding:80px;display:flex;flex-direction:column;justify-content:center}
    .tag{display:inline-block;background:#E74C3C;color:#FFF;font-size:20px;font-weight:700;padding:8px 20px;border-radius:6px;margin-bottom:24px;letter-spacing:3px}
    .bg{font-size:100px;font-weight:900;color:rgba(231,76,60,0.06);line-height:1;margin-bottom:-12px}
    h2{font-size:42px;font-weight:900;color:#1A1A1A;margin-bottom:16px}
    .desc{font-size:26px;color:#555;line-height:1.6;border-left:4px solid #E74C3C;padding-left:20px;margin-bottom:28px}
    .price{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}
    .orig{font-size:26px;color:#999;text-decoration:line-through}
    .sale{font-size:48px;font-weight:900;color:#E74C3C}
    .off{background:#FFF200;color:#E74C3C;font-size:22px;font-weight:900;padding:6px 14px;border-radius:6px}
    .box{background:#FFF5F5;border-radius:14px;padding:24px;margin-top:24px}
    .box b{color:#E74C3C;font-size:18px}
    .box p{font-size:22px;color:#333;line-height:1.5;margin-top:8px}
    </style></head><body><div class="s"><span class="tag">PICK 02</span><div class="bg">02</div><h2>무선 미니 가습기</h2><p class="desc">USB-C 충전식, 8시간 연속 사용<br>무소음 설계로 사무실에서도 OK</p><div class="price"><span class="orig">29,900원</span><span class="sale">12,900원</span><span class="off">57%</span></div><div class="box"><b>추천 이유</b><p>건조한 사무실 필수템. 물탱크 300ml라 하루 한 번만 채우면 돼요</p></div></div></body></html>""",

    # Slide 4
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#FFF;padding:80px;display:flex;flex-direction:column;justify-content:center}
    .tag{display:inline-block;background:#E74C3C;color:#FFF;font-size:20px;font-weight:700;padding:8px 20px;border-radius:6px;margin-bottom:24px;letter-spacing:3px}
    .bg{font-size:100px;font-weight:900;color:rgba(231,76,60,0.06);line-height:1;margin-bottom:-12px}
    h2{font-size:42px;font-weight:900;color:#1A1A1A;margin-bottom:16px}
    .desc{font-size:26px;color:#555;line-height:1.6;border-left:4px solid #E74C3C;padding-left:20px;margin-bottom:28px}
    .price{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}
    .orig{font-size:26px;color:#999;text-decoration:line-through}
    .sale{font-size:48px;font-weight:900;color:#E74C3C}
    .off{background:#FFF200;color:#E74C3C;font-size:22px;font-weight:900;padding:6px 14px;border-radius:6px}
    .box{background:#FFF5F5;border-radius:14px;padding:24px;margin-top:24px}
    .box b{color:#E74C3C;font-size:18px}
    .box p{font-size:22px;color:#333;line-height:1.5;margin-top:8px}
    </style></head><body><div class="s"><span class="tag">PICK 03</span><div class="bg">03</div><h2>다용도 데스크 정리함</h2><p class="desc">3단 서랍 + 펜꽂이 + 폰거치대 올인원<br>화이트/블랙 2컬러, 조립 불필요</p><div class="price"><span class="orig">25,000원</span><span class="sale">9,900원</span><span class="off">60%</span></div><div class="box"><b>추천 이유</b><p>책상 위 잡동사니 한방에 정리. 영상통화 할 때 깔끔한 배경 만들어줘요</p></div></div></body></html>""",

    # Slide 5
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#FFF;padding:80px;display:flex;flex-direction:column;justify-content:center}
    .tag{display:inline-block;background:#E74C3C;color:#FFF;font-size:20px;font-weight:700;padding:8px 20px;border-radius:6px;margin-bottom:24px;letter-spacing:3px}
    .bg{font-size:100px;font-weight:900;color:rgba(231,76,60,0.06);line-height:1;margin-bottom:-12px}
    h2{font-size:42px;font-weight:900;color:#1A1A1A;margin-bottom:16px}
    .desc{font-size:26px;color:#555;line-height:1.6;border-left:4px solid #E74C3C;padding-left:20px;margin-bottom:28px}
    .price{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}
    .orig{font-size:26px;color:#999;text-decoration:line-through}
    .sale{font-size:48px;font-weight:900;color:#E74C3C}
    .off{background:#FFF200;color:#E74C3C;font-size:22px;font-weight:900;padding:6px 14px;border-radius:6px}
    .box{background:#FFF5F5;border-radius:14px;padding:24px;margin-top:24px}
    .box b{color:#E74C3C;font-size:18px}
    .box p{font-size:22px;color:#333;line-height:1.5;margin-top:8px}
    </style></head><body><div class="s"><span class="tag">PICK 04</span><div class="bg">04</div><h2>블루라이트 차단 안경</h2><p class="desc">도수 없이 쓰는 보호 안경<br>초경량 16g, UV400 차단</p><div class="price"><span class="orig">19,900원</span><span class="sale">7,900원</span><span class="off">60%</span></div><div class="box"><b>추천 이유</b><p>하루 8시간 모니터 보는 직장인한테 진짜 필요해요. 두통 줄어든다는 후기 다수</p></div></div></body></html>""",

    # Slide 6: CTA
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#E74C3C,#C0392B);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:100px}
    h2{font-size:50px;font-weight:900;color:#FFF;line-height:1.4;margin-bottom:36px}
    .d{width:80px;height:3px;background:rgba(255,255,255,0.3);margin-bottom:36px}
    p{font-size:28px;color:rgba(255,255,255,0.8);line-height:1.6;margin-bottom:48px}
    .cta{background:#FFF;border-radius:16px;padding:28px 44px}
    .cta span{font-size:26px;font-weight:700;color:#E74C3C}
    </style></head><body><div class="s"><h2>가격은 매일 바뀌니까<br>지금이 제일 싸요</h2><div class="d"></div><p>저장해두고 하나씩 장바구니에 담아보세요<br>링크는 프로필에 있어요</p><div class="cta"><span>팔로우하면 매주 꿀딜 알려드려요</span></div></div></body></html>""",
]

# ─── 사주 6장 ───
FORTUNE_SLIDES = [
    # 표지
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#0F0A2E,#1B1464,#2D1B69);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:80px;position:relative}
    .moon{width:140px;height:140px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#FFF8DC,#FFD700);box-shadow:0 0 60px 20px rgba(255,215,0,0.15);margin-bottom:40px}
    .badge{border:2px solid rgba(255,215,0,0.4);color:#FFD700;font-size:20px;font-weight:700;padding:10px 28px;border-radius:50px;margin-bottom:32px;letter-spacing:4px}
    h1{font-size:56px;font-weight:900;color:#FFF;line-height:1.35;margin-bottom:24px}
    p{font-size:26px;color:rgba(255,255,255,0.55)}
    .yr{position:absolute;bottom:80px;font-size:20px;color:rgba(255,215,0,0.25);letter-spacing:6px}
    </style></head><body><div class="s"><div class="moon"></div><span class="badge">FORTUNE 2026</span><h1>2026년 띠별<br>3월 운세 총정리</h1><p>스와이프해서 내 띠를 찾아보세요</p><span class="yr">丙午年 三月</span></div></body></html>""",

    # 용띠
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(180deg,#1B1464,#2D1B69);padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;color:rgba(255,255,255,0.2)}
    .icon{font-size:72px;margin-bottom:12px}
    .name{font-size:22px;font-weight:700;color:#FFD700;letter-spacing:4px;margin-bottom:4px}
    .year{font-size:16px;color:rgba(255,255,255,0.35);margin-bottom:36px}
    h2{font-size:44px;font-weight:900;color:#FFF;margin-bottom:32px}
    .grid{display:flex;flex-direction:column;gap:16px}
    .row{background:rgba(255,255,255,0.05);border:1px solid rgba(255,215,0,0.12);border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:16px}
    .lb{font-size:16px;font-weight:700;color:#FFD700;min-width:70px}
    .st{font-size:18px;color:#FFD700;min-width:90px}
    .tx{font-size:20px;color:rgba(255,255,255,0.8);flex:1}
    .adv{margin-top:32px;background:rgba(255,215,0,0.06);border-left:4px solid #FFD700;padding:20px 24px;border-radius:0 12px 12px 0}
    .adv b{color:#FFD700;font-size:16px}
    .adv p{font-size:22px;color:rgba(255,255,255,0.75);line-height:1.5;margin-top:6px}
    </style></head><body><div class="s"><span class="pg">2 / 6</span><div class="icon">🐉</div><div class="name">용띠 (辰)</div><div class="year">1988 · 2000 · 2012년생</div><h2>3월, 기회가 몰려온다</h2><div class="grid"><div class="row"><span class="lb">종합운</span><span class="st">★★★★★</span><span class="tx">막혔던 일이 한꺼번에 풀리는 달</span></div><div class="row"><span class="lb">재물운</span><span class="st">★★★★☆</span><span class="tx">예상치 못한 수입이 들어올 수 있어요</span></div><div class="row"><span class="lb">연애운</span><span class="st">★★★☆☆</span><span class="tx">급하게 결정하지 말고 천천히</span></div></div><div class="adv"><b>이 달의 조언</b><p>주변 사람의 제안에 귀 기울여보세요.<br>거절하려던 것 중에 좋은 기회가 숨어 있어요.</p></div></div></body></html>""",

    # 뱀띠
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(180deg,#1B1464,#2D1B69);padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;color:rgba(255,255,255,0.2)}
    .icon{font-size:72px;margin-bottom:12px}
    .name{font-size:22px;font-weight:700;color:#FFD700;letter-spacing:4px;margin-bottom:4px}
    .year{font-size:16px;color:rgba(255,255,255,0.35);margin-bottom:36px}
    h2{font-size:44px;font-weight:900;color:#FFF;margin-bottom:32px}
    .grid{display:flex;flex-direction:column;gap:16px}
    .row{background:rgba(255,255,255,0.05);border:1px solid rgba(255,215,0,0.12);border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:16px}
    .lb{font-size:16px;font-weight:700;color:#FFD700;min-width:70px}
    .st{font-size:18px;color:#FFD700;min-width:90px}
    .tx{font-size:20px;color:rgba(255,255,255,0.8);flex:1}
    .adv{margin-top:32px;background:rgba(255,215,0,0.06);border-left:4px solid #FFD700;padding:20px 24px;border-radius:0 12px 12px 0}
    .adv b{color:#FFD700;font-size:16px}
    .adv p{font-size:22px;color:rgba(255,255,255,0.75);line-height:1.5;margin-top:6px}
    </style></head><body><div class="s"><span class="pg">3 / 6</span><div class="icon">🐍</div><div class="name">뱀띠 (巳)</div><div class="year">1989 · 2001 · 2013년생</div><h2>올해의 주인공, 빛나는 달</h2><div class="grid"><div class="row"><span class="lb">종합운</span><span class="st">★★★★☆</span><span class="tx">본인의 해! 자신감이 운을 끌어당겨요</span></div><div class="row"><span class="lb">재물운</span><span class="st">★★★★★</span><span class="tx">투자/부업에서 좋은 결과가 기대돼요</span></div><div class="row"><span class="lb">건강운</span><span class="st">★★★☆☆</span><span class="tx">과로 주의, 수면 패턴 관리하세요</span></div></div><div class="adv"><b>이 달의 조언</b><p>새로운 도전을 시작하기 좋은 시기예요.<br>미뤄둔 일이 있다면 지금이 타이밍!</p></div></div></body></html>""",

    # 호랑이띠
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(180deg,#1B1464,#2D1B69);padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;color:rgba(255,255,255,0.2)}
    .icon{font-size:72px;margin-bottom:12px}
    .name{font-size:22px;font-weight:700;color:#FFD700;letter-spacing:4px;margin-bottom:4px}
    .year{font-size:16px;color:rgba(255,255,255,0.35);margin-bottom:36px}
    h2{font-size:44px;font-weight:900;color:#FFF;margin-bottom:32px}
    .grid{display:flex;flex-direction:column;gap:16px}
    .row{background:rgba(255,255,255,0.05);border:1px solid rgba(255,215,0,0.12);border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:16px}
    .lb{font-size:16px;font-weight:700;color:#FFD700;min-width:70px}
    .st{font-size:18px;color:#FFD700;min-width:90px}
    .tx{font-size:20px;color:rgba(255,255,255,0.8);flex:1}
    .adv{margin-top:32px;background:rgba(255,215,0,0.06);border-left:4px solid #FFD700;padding:20px 24px;border-radius:0 12px 12px 0}
    .adv b{color:#FFD700;font-size:16px}
    .adv p{font-size:22px;color:rgba(255,255,255,0.75);line-height:1.5;margin-top:6px}
    </style></head><body><div class="s"><span class="pg">4 / 6</span><div class="icon">🐅</div><div class="name">호랑이띠 (寅)</div><div class="year">1986 · 1998 · 2010년생</div><h2>조용하지만 확실한 변화</h2><div class="grid"><div class="row"><span class="lb">종합운</span><span class="st">★★★☆☆</span><span class="tx">겉으로 안 보이지만 내면의 성장기</span></div><div class="row"><span class="lb">재물운</span><span class="st">★★★★☆</span><span class="tx">알뜰한 소비가 큰 차이를 만들어요</span></div><div class="row"><span class="lb">직장운</span><span class="st">★★★★☆</span><span class="tx">묵묵히 한 일이 드디어 인정받아요</span></div></div><div class="adv"><b>이 달의 조언</b><p>성과를 조급하게 기대하지 마세요.<br>씨앗을 심는 달이에요. 결실은 하반기에 옵니다.</p></div></div></body></html>""",

    # 토끼띠
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(180deg,#1B1464,#2D1B69);padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;color:rgba(255,255,255,0.2)}
    .icon{font-size:72px;margin-bottom:12px}
    .name{font-size:22px;font-weight:700;color:#FFD700;letter-spacing:4px;margin-bottom:4px}
    .year{font-size:16px;color:rgba(255,255,255,0.35);margin-bottom:36px}
    h2{font-size:44px;font-weight:900;color:#FFF;margin-bottom:32px}
    .grid{display:flex;flex-direction:column;gap:16px}
    .row{background:rgba(255,255,255,0.05);border:1px solid rgba(255,215,0,0.12);border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:16px}
    .lb{font-size:16px;font-weight:700;color:#FFD700;min-width:70px}
    .st{font-size:18px;color:#FFD700;min-width:90px}
    .tx{font-size:20px;color:rgba(255,255,255,0.8);flex:1}
    .adv{margin-top:32px;background:rgba(255,215,0,0.06);border-left:4px solid #FFD700;padding:20px 24px;border-radius:0 12px 12px 0}
    .adv b{color:#FFD700;font-size:16px}
    .adv p{font-size:22px;color:rgba(255,255,255,0.75);line-height:1.5;margin-top:6px}
    </style></head><body><div class="s"><span class="pg">5 / 6</span><div class="icon">🐇</div><div class="name">토끼띠 (卯)</div><div class="year">1987 · 1999 · 2011년생</div><h2>인간관계에서 행운이 온다</h2><div class="grid"><div class="row"><span class="lb">종합운</span><span class="st">★★★★☆</span><span class="tx">사람을 통해 좋은 소식이 들려와요</span></div><div class="row"><span class="lb">연애운</span><span class="st">★★★★★</span><span class="tx">솔로라면 소개팅 적극 추천!</span></div><div class="row"><span class="lb">건강운</span><span class="st">★★★★☆</span><span class="tx">봄나들이가 컨디션 회복에 도움</span></div></div><div class="adv"><b>이 달의 조언</b><p>혼자 고민하지 말고 가까운 사람에게 먼저 연락해보세요.<br>의외의 도움을 받게 될 거예요.</p></div></div></body></html>""",

    # CTA
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#2D1B69,#1B1464);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:100px}
    h2{font-size:48px;font-weight:900;color:#FFF;line-height:1.4;margin-bottom:32px}
    .g{color:#FFD700}
    .d{width:60px;height:2px;background:rgba(255,215,0,0.3);margin-bottom:32px}
    p{font-size:26px;color:rgba(255,255,255,0.65);line-height:1.6;margin-bottom:48px}
    .cta{border:2px solid #FFD700;border-radius:14px;padding:24px 40px}
    .cta span{font-size:24px;font-weight:700;color:#FFD700}
    </style></head><body><div class="s"><h2>운은 <span class="g">아는 만큼</span><br>대비할 수 있어요</h2><div class="d"></div><p>저장해두고 매달 확인하세요<br>친구 띠도 찾아서 공유해보세요</p><div class="cta"><span>팔로우하면 매월 운세를 보내드려요</span></div></div></body></html>""",
]

# ─── 지원금 6장 ───
SUBSIDY_SLIDES = [
    # 표지
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#1B2A4A,#2563EB);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:80px;position:relative}
    .pills{display:flex;gap:12px;margin-bottom:36px}
    .pill{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#FFF;font-size:18px;font-weight:600;padding:8px 20px;border-radius:50px}
    .amt{font-size:90px;font-weight:900;color:#FFF;line-height:1;margin-bottom:4px}
    .sub{font-size:32px;color:rgba(255,255,255,0.65);margin-bottom:36px}
    h1{font-size:52px;font-weight:900;color:#FFF;line-height:1.35;margin-bottom:20px}
    p{font-size:24px;color:rgba(255,255,255,0.6)}
    .badge{position:absolute;top:80px;right:80px;background:#FF4757;color:#FFF;font-size:20px;font-weight:900;padding:10px 22px;border-radius:10px;transform:rotate(3deg)}
    </style></head><body><div class="s"><div class="badge">2026년 최신</div><div class="pills"><span class="pill">청년</span><span class="pill">근로자</span><span class="pill">출산/육아</span></div><div class="amt">최대 300만원</div><div class="sub">모르면 못 받는 돈</div><h1>2026 청년 지원금<br>TOP 5 총정리</h1><p>지금 바로 신청 가능한 것만 모았어요</p></div></body></html>""",

    # 청년도약계좌
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#F0F4FF;padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;font-weight:700;color:#2563EB}
    .n{width:52px;height:52px;background:#2563EB;color:#FFF;font-size:26px;font-weight:900;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:20px}
    h2{font-size:40px;font-weight:900;color:#1A1A1A;margin-bottom:8px}
    .amt{font-size:48px;font-weight:900;color:#2563EB;margin-bottom:28px}
    .grid{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
    .row{display:flex;gap:14px;background:#FFF;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,0.04)}
    .lb{font-size:16px;font-weight:700;color:#2563EB;min-width:60px;padding-top:2px}
    .val{font-size:20px;color:#333;line-height:1.5;flex:1}
    .tip{background:#2563EB;border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:14px}
    .tip span{font-size:20px;color:#FFF;line-height:1.5}
    </style></head><body><div class="s"><span class="pg">2 / 6</span><div class="n">1</div><h2>청년도약계좌</h2><div class="amt">최대 5,000만원</div><div class="grid"><div class="row"><span class="lb">대상</span><span class="val">만 19~34세, 개인소득 7,500만원 이하</span></div><div class="row"><span class="lb">내용</span><span class="val">매월 70만원 납입 시 정부 최대 6% 기여금 추가 (5년 만기)</span></div><div class="row"><span class="lb">신청</span><span class="val">시중 11개 은행 앱에서 수시 신청</span></div></div><div class="tip"><span>💡 소득 2,400만원 이하면 최대 6% 매칭!</span></div></div></body></html>""",

    # 청년월세지원
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#F0F4FF;padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;font-weight:700;color:#2563EB}
    .n{width:52px;height:52px;background:#2563EB;color:#FFF;font-size:26px;font-weight:900;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:20px}
    h2{font-size:40px;font-weight:900;color:#1A1A1A;margin-bottom:8px}
    .amt{font-size:48px;font-weight:900;color:#2563EB;margin-bottom:28px}
    .grid{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
    .row{display:flex;gap:14px;background:#FFF;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,0.04)}
    .lb{font-size:16px;font-weight:700;color:#2563EB;min-width:60px;padding-top:2px}
    .val{font-size:20px;color:#333;line-height:1.5;flex:1}
    .tip{background:#2563EB;border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:14px}
    .tip span{font-size:20px;color:#FFF;line-height:1.5}
    </style></head><body><div class="s"><span class="pg">3 / 6</span><div class="n">2</div><h2>청년월세 한시 특별지원</h2><div class="amt">월 최대 20만원</div><div class="grid"><div class="row"><span class="lb">대상</span><span class="val">만 19~34세, 독립거주 청년</span></div><div class="row"><span class="lb">내용</span><span class="val">최대 12개월간 월세 20만원 지원 (연 240만원)</span></div><div class="row"><span class="lb">신청</span><span class="val">복지로 또는 주민센터 방문</span></div></div><div class="tip"><span>💡 부모님과 다른 주소지에 살고 있으면 신청 가능!</span></div></div></body></html>""",

    # 근로장려금
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#F0F4FF;padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;font-weight:700;color:#2563EB}
    .n{width:52px;height:52px;background:#2563EB;color:#FFF;font-size:26px;font-weight:900;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:20px}
    h2{font-size:40px;font-weight:900;color:#1A1A1A;margin-bottom:8px}
    .amt{font-size:48px;font-weight:900;color:#2563EB;margin-bottom:28px}
    .grid{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
    .row{display:flex;gap:14px;background:#FFF;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,0.04)}
    .lb{font-size:16px;font-weight:700;color:#2563EB;min-width:60px;padding-top:2px}
    .val{font-size:20px;color:#333;line-height:1.5;flex:1}
    .tip{background:#2563EB;border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:14px}
    .tip span{font-size:20px;color:#FFF;line-height:1.5}
    </style></head><body><div class="s"><span class="pg">4 / 6</span><div class="n">3</div><h2>근로장려금 (EITC)</h2><div class="amt">최대 330만원</div><div class="grid"><div class="row"><span class="lb">대상</span><span class="val">근로/사업/종교인 소득자 (소득 기준 충족 시)</span></div><div class="row"><span class="lb">내용</span><span class="val">단독가구 165만원, 홑벌이 285만원, 맞벌이 330만원</span></div><div class="row"><span class="lb">신청</span><span class="val">5월 정기신청 (국세청 홈택스)</span></div></div><div class="tip"><span>💡 작년에 일했으면 올해 5월에 꼭 신청하세요. 환급이에요!</span></div></div></body></html>""",

    # 국민취업지원제도
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:#F0F4FF;padding:80px;display:flex;flex-direction:column;justify-content:center;position:relative}
    .pg{position:absolute;top:60px;right:80px;font-size:18px;font-weight:700;color:#2563EB}
    .n{width:52px;height:52px;background:#2563EB;color:#FFF;font-size:26px;font-weight:900;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:20px}
    h2{font-size:40px;font-weight:900;color:#1A1A1A;margin-bottom:8px}
    .amt{font-size:48px;font-weight:900;color:#2563EB;margin-bottom:28px}
    .grid{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
    .row{display:flex;gap:14px;background:#FFF;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,0.04)}
    .lb{font-size:16px;font-weight:700;color:#2563EB;min-width:60px;padding-top:2px}
    .val{font-size:20px;color:#333;line-height:1.5;flex:1}
    .tip{background:#2563EB;border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:14px}
    .tip span{font-size:20px;color:#FFF;line-height:1.5}
    </style></head><body><div class="s"><span class="pg">5 / 6</span><div class="n">4</div><h2>국민취업지원제도</h2><div class="amt">월 50만원 × 6개월</div><div class="grid"><div class="row"><span class="lb">대상</span><span class="val">15~69세 미취업자 (소득/재산 기준)</span></div><div class="row"><span class="lb">내용</span><span class="val">구직촉진수당 월 50만원 + 취업 상담 + 직업훈련</span></div><div class="row"><span class="lb">신청</span><span class="val">고용24 (work24.go.kr) 온라인 신청</span></div></div><div class="tip"><span>💡 직업훈련까지 받으면 300만원 이상 지원 가능해요!</span></div></div></body></html>""",

    # CTA
    """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1350px;overflow:hidden;font-family:'Noto Sans KR',sans-serif}
    .s{width:1080px;height:1350px;background:linear-gradient(160deg,#2563EB,#1B2A4A);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:100px}
    h2{font-size:48px;font-weight:900;color:#FFF;line-height:1.4;margin-bottom:32px}
    .a{color:#60A5FA}
    .d{width:80px;height:3px;background:rgba(255,255,255,0.25);margin-bottom:32px}
    .cl{text-align:left;margin-bottom:40px}
    .ci{font-size:24px;color:rgba(255,255,255,0.8);line-height:2;padding-left:8px}
    .ci::before{content:'✓ ';color:#60A5FA;font-weight:900}
    .cta{background:#FFF;border-radius:14px;padding:24px 40px}
    .cta span{font-size:24px;font-weight:700;color:#2563EB}
    </style></head><body><div class="s"><h2><span class="a">내 돈</span>인데<br>안 받으면 손해예요</h2><div class="d"></div><div class="cl"><div class="ci">저장해두고 하나씩 신청하세요</div><div class="ci">해당되는 친구에게 공유해주세요</div><div class="ci">마감일 전에 꼭 확인하세요</div></div><div class="cta"><span>팔로우하면 새로운 지원금 알려드려요</span></div></div></body></html>""",
]

CATEGORIES = [
    ("shopping", "쇼핑", "2026 봄 가성비 꿀템 TOP 6", SHOPPING_SLIDES),
    ("fortune", "사주/운세", "2026년 띠별 3월 운세 총정리", FORTUNE_SLIDES),
    ("subsidy", "지원금", "2026 청년 지원금 TOP 5 총정리", SUBSIDY_SLIDES),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        for cat_key, cat_name, topic, slides_html in CATEGORIES:
            print(f"\n{'='*40}")
            print(f"  {cat_name} 카드뉴스 ({len(slides_html)}장)")
            print(f"{'='*40}")

            out_dir = SAMPLES_DIR / cat_key
            out_dir.mkdir(exist_ok=True)

            # 기존 PNG 삭제
            for old in out_dir.glob("slide_*.png"):
                old.unlink()

            png_urls = []
            for i, html in enumerate(slides_html):
                page = await browser.new_page(viewport={"width": 1080, "height": 1350})
                await page.set_content(html, wait_until="networkidle")
                png_path = out_dir / f"slide_{i+1}.png"
                await page.screenshot(path=str(png_path), full_page=False)
                await page.close()
                png_urls.append(f"/samples/{cat_key}/slide_{i+1}.png")
                print(f"  [OK] slide_{i+1}.png")

            # Supabase에 저장
            try:
                session_name = f"sample_{cat_key}"
                result = save_card_history(
                    user_id=ADMIN_USER_ID,
                    session_name=session_name,
                    category=cat_name,
                    topic=topic,
                    slides_count=len(png_urls),
                    slides_data={"slides": [{"type": cat_key}]},
                    png_urls=png_urls,
                )
                print(f"  [DB] Supabase 저장 완료 (id: {result.get('id', '?')})")
            except Exception as e:
                print(f"  [DB 오류] {e}")

        await browser.close()

    print("\n모든 카테고리 생성 완료!")


asyncio.run(main())
