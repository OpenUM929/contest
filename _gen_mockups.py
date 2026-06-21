# -*- coding: utf-8 -*-
"""이음 모바일 앱 기능별 UI 목업 생성 (실제 소스 색상·문구 기반). 이모지 미사용, 도형 직접 묘사."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:\dev\contest\제출본\img"
os.makedirs(OUT, exist_ok=True)
RF = r"C:\Windows\Fonts\malgun.ttf"
BF = r"C:\Windows\Fonts\malgunbd.ttf"
S = 2  # supersample

def F(size, bold=False):
    return ImageFont.truetype(BF if bold else RF, size * S)

def new(w, h, bg):
    return Image.new("RGB", (w * S, h * S), bg)

def rr(d, xy, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([c * S for c in xy], radius=r * S, fill=fill, outline=outline, width=width * S)

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw * S:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def text(d, xy, s, font, fill, maxw=None, lh=1.4):
    x, y = xy
    if maxw is None:
        d.text((x * S, y * S), s, font=font, fill=fill)
        return y + font.size / S * lh
    for ln in wrap(d, s, font, maxw):
        d.text((x * S, y * S), ln, font=font, fill=fill)
        y += font.size / S * lh
    return y

def save(img, name):
    img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    p = os.path.join(OUT, name)
    img.save(p)
    print("saved", name, img.size)

def checkbox(d, x, y, on, sz=22, color="#E8572A"):
    if on:
        rr(d, [x, y, x + sz, y + sz], 5, fill=color)
        d.line([(x + 5) * S, (y + sz * 0.55) * S, (x + sz * 0.42) * S, (y + sz * 0.8) * S], fill="#FFF", width=3 * S)
        d.line([(x + sz * 0.42) * S, (y + sz * 0.8) * S, (x + sz * 0.85) * S, (y + sz * 0.25) * S], fill="#FFF", width=3 * S)
    else:
        rr(d, [x, y, x + sz, y + sz], 5, outline="#C0B4A0", width=2)

# ---------------- 1. 로그인 (공통) ----------------
def login():
    W, H = 460, 360
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    rr(d, [30, 24, W - 30, H - 24], 18, fill="#FFF8EE")
    cx = W / 2
    t = F(30, True); d.text(((cx - d.textlength("이음(以音)", font=t) / 2 / S) * S, 50 * S), "이음(以音)", font=t, fill="#4A3728")
    sf = F(13); d.text(((cx - d.textlength("세대를 잇는 따뜻한 이야기", font=sf) / 2 / S) * S, 90 * S), "세대를 잇는 따뜻한 이야기", font=sf, fill="#888")
    y = 130
    for lab, ph in [("이메일", "admin@ium.kr"), ("비밀번호", "••••••••")]:
        text(d, (55, y), lab, F(13), "#666"); y += 24
        rr(d, [55, y, W - 55, y + 38], 10, fill="#FFF", outline="#DDD", width=2)
        d.text((68 * S, (y + 11) * S), ph, font=F(14), fill="#AAA"); y += 52
    rr(d, [55, y + 4, W - 55, y + 46], 12, fill="#E8572A")
    bt = F(17, True); d.text(((cx - d.textlength("로그인", font=bt) / 2 / S) * S, (y + 16) * S), "로그인", font=bt, fill="#FFF")
    save(img, "01_login.png")

# ---------------- 2. 이용 동의 (개인정보 보호) ----------------
def consent():
    W, H = 460, 380
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    y = text(d, (32, 28), "이음(以音) 시작하기", F(22, True), "#4A3728")
    y = text(d, (32, y + 2), "서비스를 이용하려면 아래 약관에 동의해 주세요.", F(12), "#888") + 6
    checkbox(d, 32, y, True); text(d, (66, y + 1), "전체 동의", F(15, True), "#4A3728"); y += 36
    d.line([32 * S, y * S, (W - 32) * S, y * S], fill="#E0D8CE", width=1 * S); y += 14
    for title in ["[필수] 개인정보 처리 방침", "[필수] 서비스 이용 약관", "[필수] AI 대화 분석 활용 동의"]:
        checkbox(d, 32, y, True, sz=20)
        text(d, (64, y), title, F(13), "#333")
        bv = F(11, True); d.text(((W - 70) * S, (y + 2) * S), "보기 ▼", font=bv, fill="#E8572A")
        y += 38
    rr(d, [32, y + 8, W - 32, y + 52], 13, fill="#E8572A")
    bt = F(16, True); d.text(((W / 2 - d.textlength("시작하기", font=bt) / 2 / S) * S, (y + 22) * S), "시작하기", font=bt, fill="#FFF")
    save(img, "02_consent.png")

# ---------------- 3. 세대공감 주제 카드 (노인) ----------------
def topic_elder():
    W, H = 460, 330
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    rr(d, [24, 20, W - 24, H - 20], 16, fill="#FFF8EE")
    y = text(d, (44, 40), "이번 주 이야기", F(14), "#888")
    rr(d, [44, y + 4, W - 44, y + 150], 12, fill="#E7E0D4")
    ph = F(15); d.text(((W / 2 - d.textlength("[ 지역문화 사진 ]", font=ph) / 2 / S) * S, (y + 70) * S), "[ 지역문화 사진 ]", font=ph, fill="#998")
    y = y + 166
    y = text(d, (44, y), "강천용소와 노총각", F(18, True), "#4A3728")
    y = text(d, (44, y + 4), "전라북도 순창군 · 지역설화  |  문화 빅데이터 플랫폼 제공", F(11), "#AAA")
    text(d, (44, y + 4), "○ 김복지 복지사님 준비", F(12, True), "#7B7BFF")
    save(img, "03_topic_elder.png")

# ---------------- 4. 노인 설문 — 선택형 ----------------
def survey_choice():
    W, H = 460, 360
    img = new(W, H, "#FFF8EE"); d = ImageDraw.Draw(img)
    y = text(d, (32, 28), "질문 1 / 3", F(13), "#888")
    y = text(d, (32, y), "강천용소 전설처럼, 어릴 적 우리 동네에도 어른들이 들려주던 '이야기 깃든 곳'이 있었나요?", F(15, True), "#333", maxw=W - 64) + 8
    for opt in ["마을 뒷산의 큰 바위나 굴", "동구 밖 오래된 정자나무", "물 맑던 냇가와 깊은 소(沼)", "그 외에 문득 떠오르는 것"]:
        rr(d, [32, y, W - 32, y + 46], 12, fill="#FFF", outline="#DDD", width=2)
        bt = F(15, True); d.text(((W / 2 - d.textlength(opt, font=bt) / 2 / S) * S, (y + 13) * S), opt, font=bt, fill="#333")
        y += 56
    save(img, "04_survey_choice.png")

# ---------------- 5. 노인 설문 — 서술형(음성) ----------------
def survey_voice():
    W, H = 460, 300
    img = new(W, H, "#FFF8EE"); d = ImageDraw.Draw(img)
    y = text(d, (32, 28), "질문 3 / 3", F(13), "#888")
    y = text(d, (32, y), "그 시절, 외롭고 고단할 때 곁에서 힘이 되어준 사람은 누구였나요?", F(16, True), "#333", maxw=W - 64) + 10
    rr(d, [60, y, W - 60, y + 130], 20, fill="#E8572A")
    mcx = W / 2
    # 마이크 도형
    d.rounded_rectangle([(mcx - 13) * S, (y + 22) * S, (mcx + 13) * S, (y + 60) * S], radius=13 * S, fill="#FFF")
    d.arc([(mcx - 22) * S, (y + 30) * S, (mcx + 22) * S, (y + 74) * S], 20, 160, fill="#FFF", width=4 * S)
    d.line([mcx * S, (y + 74) * S, mcx * S, (y + 88) * S], fill="#FFF", width=4 * S)
    lt = F(16, True); d.text(((mcx - d.textlength("누르고 말씀해 주세요", font=lt) / 2 / S) * S, (y + 98) * S), "누르고 말씀해 주세요", font=lt, fill="#FFF")
    save(img, "05_survey_voice.png")

# ---------------- 6. AI 응답 (TTS) ----------------
def ai_response():
    W, H = 460, 240
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    rr(d, [24, 24, W - 24, H - 24], 16, fill="#EEF7EE")
    y = text(d, (44, 44), "○ 이음", F(14, True), "#4CAF50")
    y = text(d, (44, y + 4), "물 맑던 냇가라니, 그 시원한 물소리가 지금도 들리는 듯하네요. 그곳에서 함께 어울리던 동무가 있었나요?", F(15), "#222", maxw=W - 88, lh=1.5) + 6
    text(d, (44, y), "○ 읽어드리고 있어요...", F(12), "#4CAF50")
    save(img, "06_ai_response.png")

# ---------------- 7. 위기 감지 팝업 ----------------
def crisis():
    W, H = 460, 280
    img = new(W, H, "#EFEDE6"); d = ImageDraw.Draw(img)
    rr(d, [40, 60, W - 40, H - 60], 16, fill="#FFF8EE")
    y = text(d, (70, 86), "지금 힘드신가요?", F(18, True), "#4A3728")
    y = text(d, (70, y + 6), "전문가와 바로 연결해 드릴게요.", F(14), "#666") + 16
    rr(d, [70, y, W - 70, y + 46], 12, fill="#E8572A")
    bt = F(16, True); d.text(((W / 2 - d.textlength("1393 전화하기", font=bt) / 2 / S) * S, (y + 13) * S), "1393 전화하기", font=bt, fill="#FFF")
    y += 56
    rr(d, [70, y, W - 70, y + 42], 12, outline="#CCC", width=2)
    ct = F(15); d.text(((W / 2 - d.textlength("닫기", font=ct) / 2 / S) * S, (y + 11) * S), "닫기", font=ct, fill="#888")
    save(img, "07_crisis.png")

# ---------------- 8. 청년 화면 (익명·다크) ----------------
def youth_home():
    W, H = 460, 340
    img = new(W, H, "#1A1A2E"); d = ImageDraw.Draw(img)
    text(d, (28, 26), "이음", F(20, True), "#E8E8FF")
    rr(d, [W - 110, 24, W - 28, 52], 14, fill="#2D2D4A")
    at = F(12); d.text(((W - 95) * S, 32 * S), "○ 익명", font=at, fill="#AAA")
    rr(d, [24, 70, W - 24, H - 24], 16, fill="#16213E")
    y = text(d, (44, 90), "이번 주 주제", F(12), "#7B7BFF")
    y = text(d, (44, y + 2), "강천용소와 노총각", F(17, True), "#E8E8FF")
    y = text(d, (44, y + 4), "전라북도 순창군 · 지역설화 · 문화 빅데이터 플랫폼", F(11), "#666")
    y = text(d, (44, y + 2), "○ 김복지 복지사님 준비", F(11, True), "#7B7BFF") + 8
    rr(d, [44, y, W - 44, y + 46], 10, fill="#0F3460")
    # play 삼각형
    d.polygon([(64 * S, (y + 13) * S), (64 * S, (y + 33) * S), (80 * S, (y + 23) * S)], fill="#7B7BFF")
    text(d, (92, y + 13), "재생하기", F(14), "#AAA")
    save(img, "08_youth_home.png")

# ---------------- 9. 통계 보기 ----------------
def stats():
    W, H = 460, 320
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    rr(d, [24, 24, W - 24, H - 24], 14, fill="#FFF8EE")
    y = text(d, (44, 44), "강천용소 전설처럼, 동네에 이야기 깃든 곳이 있었나요?", F(14, True), "#333", maxw=W - 88)
    y = text(d, (44, y + 2), "나의 답변: 물 맑던 냇가와 깊은 소  (내가 선택)", F(12), "#E8572A") + 10
    for lab, pct in [("물 맑던 냇가·소", 48), ("뒷산 바위·굴", 32), ("동구밖 정자나무", 20)]:
        text(d, (44, y), lab, F(13), "#333")
        barx, barw = 250, W - 44 - 250 - 46
        rr(d, [barx, y + 2, barx + barw, y + 16], 7, fill="#EEE")
        rr(d, [barx, y + 2, barx + int(barw * pct / 100), y + 16], 7, fill="#E8572A")
        d.text(((W - 42) * S, (y) * S), f"{pct}%", font=F(11), fill="#888")
        y += 34
    text(d, (44, y + 4), "총 25명 참여", F(12), "#888")
    save(img, "09_stats.png")

# ---------------- 10. 결과물(수필) 전달 ----------------
def essay():
    W, H = 460, 320
    img = new(W, H, "#FFFDF7"); d = ImageDraw.Draw(img)
    rr(d, [24, 24, W - 24, H - 24], 14, fill="#FFF8EE")
    y = text(d, (44, 44), "수필 「강천용소와 노총각」", F(16, True), "#4A3728")
    y = text(d, (44, y + 4), "○ 18명의 이야기 · 2026-06 셋째 주", F(12), "#888") + 8
    y = text(d, (44, y), "누군가는 뒷산 바위에 깃든 옛이야기를, 누군가는 물 맑던 냇가를 떠올렸다. 서로 다른 시절을 살아온 이들의 기억은, 그렇게 한자리에 모여 한 편의 글이 되었다.", F(13), "#333", maxw=W - 88, lh=1.55) + 10
    rr(d, [44, y, 170, y + 40], 10, fill="#E8572A")
    bt = F(13, True); d.text(((107 - d.textlength("읽어 듣기", font=bt) / 2 / S) * S, (y + 11) * S), "읽어 듣기", font=bt, fill="#FFF")
    save(img, "10_essay.png")

# ---------------- 11. 복지사 — AI 질의 생성 (대시보드) ----------------
def welfare_topic():
    W, H = 620, 470
    img = new(W, H, "#ECECF1"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 16, fill="#FFFFFF")
    y = text(d, (40, 36), "주간 주제 관리 — AI 질문 생성", F(18, True), "#1A1A2E") + 6
    text(d, (40, y), "주제 제목", F(11), "#888"); y += 22
    rr(d, [40, y, W - 40, y + 36], 8, fill="#F7F7FA", outline="#DDD", width=1)
    d.text((52 * S, (y + 9) * S), "강천용소와 노총각", font=F(13), fill="#333"); y += 50
    text(d, (40, y), "대상  노인     |     질문 유형  혼합형", F(11), "#888"); y += 26
    rr(d, [40, y, 180, y + 34], 17, fill="#E8572A")
    d.text(((110 - d.textlength("자동 미리보기", font=F(12, True)) / 2 / S) * S, (y + 9) * S), "자동 미리보기", font=F(12, True), fill="#FFF")
    rr(d, [190, y, 330, y + 34], 17, outline="#E8572A", width=2)
    d.text(((260 - d.textlength("수동 미리보기", font=F(12)) / 2 / S) * S, (y + 9) * S), "수동 미리보기", font=F(12), fill="#E8572A")
    rr(d, [W - 200, y, W - 40, y + 34], 10, fill="#1A1A2E")
    d.text(((W - 120 - d.textlength("미리보기 생성", font=F(12, True)) / 2 / S) * S, (y + 9) * S), "미리보기 생성", font=F(12, True), fill="#FFF")
    y += 52
    d.line([40 * S, y * S, (W - 40) * S, y * S], fill="#EEE", width=1 * S); y += 12
    text(d, (40, y), "AI 생성 미리보기", F(12, True), "#1A1A2E"); y += 26
    rr(d, [40, y, W - 40, y + 96], 10, fill="#FFF8EE")
    yy = text(d, (54, y + 12), "Q1. 강천용소 전설처럼, 동네에 이야기 깃든 곳이 있었나요?", F(12, True), "#4A3728", maxw=W - 110)
    cx = 54
    for chip in ["뒷산 바위·굴", "동구밖 정자나무", "물 맑던 냇가·소"]:
        wch = d.textlength(chip, font=F(10)) / S + 24
        rr(d, [cx, yy + 4, cx + wch, yy + 28], 12, fill="#FFF", outline="#E0C0A0", width=1)
        d.text(((cx + 12) * S, (yy + 9) * S), chip, font=F(10), fill="#888")
        cx += wch + 10
    y += 108
    rr(d, [40, y, W - 40, y + 50], 10, fill="#FFF8EE")
    text(d, (54, y + 13), "Q2. (음성) 외롭고 고단할 때 곁에 있어준 사람은?", F(12, True), "#4A3728", maxw=W - 110)
    save(img, "11_welfare_topic.png")

# ---------------- 12. 프롬프트 요청·수령 양식 ----------------
def prompt_format():
    W, H = 620, 500
    img = new(W, H, "#ECECF1"); d = ImageDraw.Draw(img)
    rr(d, [20, 16, W - 20, H - 16], 16, fill="#FFFFFF")
    y = text(d, (40, 30), "AI 프롬프트 요청 방법과 수령 양식", F(17, True), "#1A1A2E") + 6
    text(d, (40, y), "① AI 요청 — 결정적 프롬프트(템플릿 자동 완성)", F(11, True), "#E8572A"); y += 22
    rr(d, [40, y, W - 40, y + 118], 8, fill="#1E1E2E")
    yy = y + 12
    for ln in ["[역할] 노인·청년의 옛 기억을 잇는 설문 설계자",
               "[주제] 강천용소와 노총각  [대상] 노인  [유형] 혼합형",
               "[지시] 향수를 자극하는 선택형 1 + 서술형 1 생성,",
               "       각 보기에 MBTI 성향 축(EI/SN/TF/JP) 태그 부여"]:
        d.text((54 * S, yy * S), ln, font=F(10.5), fill="#A8E0A8"); yy += 24
    y += 134
    text(d, (40, y), "② AI 수령 — 구조화 JSON 양식 (QuestionSet)", F(11, True), "#E8572A"); y += 22
    rr(d, [40, y, W - 40, y + 156], 8, fill="#1E1E2E")
    yy = y + 12
    for ln in ['{ "schema_version":"1.0", "question_type":"mixed",',
               '  "questions":[',
               '    {"type":"choice","text":"동네에 이야기 깃든 곳이 있었나요?",',
               '     "options":[{"label":"물 맑던 냇가와 소",',
               '                 "mbti_axis":"SN","mbti_pole":"S"}, ...]},',
               '    {"type":"narrative","text":"곁에 있어준 사람은?"} ] }']:
        d.text((54 * S, yy * S), ln, font=F(10), fill="#9FD0FF"); yy += 24
    save(img, "12_prompt_format.png")

# ---------------- 13. 결과물 생성 페이지 ----------------
def deliverable_gen():
    W, H = 560, 430
    img = new(W, H, "#ECECF1"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 16, fill="#FFFFFF")
    y = text(d, (40, 36), "결과물 생성 — 수필 · 시 · 이미지", F(17, True), "#1A1A2E") + 8
    text(d, (40, y), "형식 선택", F(11), "#888"); y += 24
    cx = 40
    for name, on in [("수필", True), ("시", False), ("소설", False), ("이미지", False)]:
        wch = d.textlength(name, font=F(12, True)) / S + 30
        if on:
            rr(d, [cx, y, cx + wch, y + 34], 17, fill="#E8572A")
        else:
            rr(d, [cx, y, cx + wch, y + 34], 17, outline="#CCC", width=2)
        d.text(((cx + 15) * S, (y + 9) * S), name, font=F(12, True), fill="#FFF" if on else "#888")
        cx += wch + 12
    y += 50
    rr(d, [40, y, 220, y + 38], 10, fill="#1A1A2E")
    d.text((58 * S, (y + 11) * S), "AI로 생성하기", font=F(12, True), fill="#FFF"); y += 54
    d.line([40 * S, y * S, (W - 40) * S, y * S], fill="#EEE", width=1 * S); y += 12
    rr(d, [40, y, W - 40, H - 40], 10, fill="#FFF8EE")
    yy = text(d, (54, y + 12), "「강천용소와 노총각」", F(13, True), "#4A3728")
    yy = text(d, (54, yy + 2), "기여자 18명 · 2026-06 셋째 주", F(10), "#888") + 4
    text(d, (54, yy), "누군가는 뒷산 바위에 깃든 옛이야기를, 누군가는 물 맑던 냇가를 떠올렸다. 서로 다른 시절의 기억이 한자리에 모여 한 편의 글이 되었다...", F(11), "#333", maxw=W - 110, lh=1.5)
    save(img, "13_deliverable_gen.png")

# ---------------- 14. 청년 설문 (선택형, 다크) ----------------
def youth_survey():
    W, H = 460, 360
    img = new(W, H, "#1A1A2E"); d = ImageDraw.Draw(img)
    rr(d, [24, 24, W - 24, H - 24], 16, fill="#16213E")
    y = text(d, (44, 44), "질문 1 / 3", F(12), "#7B7BFF")
    y = text(d, (44, y), "강천용소 전설처럼, 우리 동네에도 이야기 깃든 곳이 있었나요?", F(14, True), "#E8E8FF", maxw=W - 88) + 8
    for opt in ["마을 뒷산의 큰 바위나 굴", "동구 밖 오래된 정자나무", "물 맑던 냇가와 깊은 소(沼)", "그 외에 문득 떠오르는 것"]:
        rr(d, [44, y, W - 44, y + 44], 12, fill="#0F1A33", outline="#2D2D4A", width=2)
        bt = F(13, True); d.text(((W / 2 - d.textlength(opt, font=bt) / 2 / S) * S, (y + 12) * S), opt, font=bt, fill="#E8E8FF")
        y += 54
    save(img, "14_youth_survey.png")

# ---------------- 15. 복지사 대시보드 — 실시간 모니터링 ----------------
def welfare_dashboard():
    W, H = 650, 500
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    text(d, (28, 24), "복지사 대시보드", F(18, True), "#1A1A2E")
    rr(d, [210, 22, 372, 52], 6, fill="#FFF", outline="#DDD", width=1)
    d.text((222 * S, 31 * S), "김복지 (전북 순창)", font=F(11), fill="#333")
    rr(d, [W - 200, 22, W - 28, 52], 8, fill="#E8572A")
    d.text(((W - 188) * S, 30 * S), "주간 주제 관리 →", font=F(11, True), fill="#FFF")
    y = 66
    rr(d, [28, y, W - 28, y + 50], 10, fill="#FFF", outline="#7B7BFF", width=2)
    d.text((44 * S, (y + 8) * S), "이번 주 주제 확인 현황", font=F(11), fill="#888")
    d.text((44 * S, (y + 26) * S), "18 / 25 명 확인", font=F(15, True), fill="#1A1A2E")
    y += 62
    cards = [("긴급", "2명", "#FF4444"), ("주의", "5명", "#FFA500"), ("정상", "18명", "#44BB44"), ("이번 주 참여", "18/25", "#888")]
    cw = (W - 56 - 30) / 4
    cx = 28
    for lab, val, col in cards:
        rr(d, [cx, y, cx + cw, y + 72], 10, fill="#FFF", outline=col, width=2)
        d.text(((cx + cw / 2 - d.textlength(val, font=F(17, True)) / 2 / S) * S, (y + 16) * S), val, font=F(17, True), fill=col)
        d.text(((cx + cw / 2 - d.textlength(lab, font=F(10)) / 2 / S) * S, (y + 48) * S), lab, font=F(10), fill="#888")
        cx += cw + 10
    y += 88
    for nm, meta, badge, col in [("이순자 어르신", "마지막 접속 6/14 · 알림 2건 · 주제 미확인", "긴급", "#FF4444"),
                                  ("박영수 어르신", "마지막 접속 6/18 · 주제 확인", "주의", "#FFA500"),
                                  ("김말순 어르신", "마지막 접속 6/20 · 주제 확인", "정상", "#44BB44")]:
        rr(d, [28, y, W - 28, y + 52], 8, fill="#FFF")
        d.rectangle([28 * S, y * S, 34 * S, (y + 52) * S], fill=col)
        d.text((50 * S, (y + 9) * S), nm, font=F(13, True), fill="#222")
        d.text((50 * S, (y + 30) * S), meta, font=F(10), fill="#888")
        bw = d.textlength(badge, font=F(10, True)) / S + 24
        rr(d, [W - 44 - bw, y + 14, W - 44, y + 38], 12, fill=col)
        d.text(((W - 44 - bw + 12) * S, (y + 20) * S), badge, font=F(10, True), fill="#FFF")
        y += 60
    ax = 50
    for lab, col in [("전화하기", "#E8572A"), ("방문 요청", "#555"), ("상담 연결", "#4CAF50"), ("상세 보기", "#2196F3"), ("알림 해결", "#9C27B0")]:
        bw = d.textlength(lab, font=F(10, True)) / S + 22
        rr(d, [ax, y, ax + bw, y + 30], 6, fill=col)
        d.text(((ax + 11) * S, (y + 8) * S), lab, font=F(10, True), fill="#FFF")
        ax += bw + 8
    save(img, "15_welfare_dashboard.png")

# ---------------- 16. 설문 분석 — 응답 통계 + 누적 MBTI ----------------
def survey_analytics():
    W, H = 620, 480
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 14, fill="#FFF")
    y = text(d, (40, 36), "설문 분석 — 「강천용소와 노총각」", F(16, True), "#1A1A2E")
    y = text(d, (40, y + 2), "응답 25명 · 응답률 72%", F(11), "#888") + 10
    text(d, (40, y), "선택형 Q1 응답 분포", F(12, True), "#E8572A"); y += 26
    for lab, pct in [("물 맑던 냇가·소", 48), ("뒷산 바위·굴", 32), ("동구밖 정자나무", 20)]:
        d.text((40 * S, y * S), lab, font=F(11), fill="#333")
        bx, bw = 230, W - 230 - 90
        rr(d, [bx, y + 1, bx + bw, y + 15], 7, fill="#EEE")
        rr(d, [bx, y + 1, bx + int(bw * pct / 100), y + 15], 7, fill="#E8572A")
        d.text(((W - 78) * S, y * S), f"{pct}%", font=F(10), fill="#888")
        y += 30
    y += 8
    text(d, (40, y), "누적 성향(MBTI) 분석 — 응답이 쌓일수록 성향이 드러남", F(12, True), "#7B7BFF"); y += 26
    for left, right, lp in [("외향 E", "내향 I", 40), ("감각 S", "직관 N", 68), ("사고 T", "감정 F", 45), ("판단 J", "인식 P", 52)]:
        d.text((40 * S, y * S), left, font=F(10, True), fill="#1A1A2E")
        bx, bw = 110, W - 110 - 120
        rr(d, [bx, y + 1, bx + bw, y + 15], 7, fill="#D9E0FF")
        rr(d, [bx, y + 1, bx + int(bw * lp / 100), y + 15], 7, fill="#7B7BFF")
        d.text(((W - 100) * S, y * S), right, font=F(10, True), fill="#1A1A2E")
        d.text(((bx + bw / 2 - 14) * S, (y - 1) * S), f"{lp}·{100 - lp}", font=F(9), fill="#33406A")
        y += 28
    save(img, "16_survey_analytics.png")

# ---------------- 17. 멀티 AI 공급자 · API 키 관리 ----------------
def settings_apikey():
    W, H = 580, 420
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 14, fill="#FFF")
    y = text(d, (40, 34), "AI 공급자 · API 키 관리", F(16, True), "#1A1A2E")
    y = text(d, (40, y + 2), "한 공급자가 실패하면 다음 공급자로 자동 전환(Fallback)", F(10.5), "#888") + 12
    for nm, model, st, col in [("Claude", "claude-sonnet-4-6", "연결됨", "#44BB44"),
                                ("OpenAI", "gpt-4o", "연결됨", "#44BB44"),
                                ("Gemini", "gemini-2.0-flash", "대기", "#FFA500"),
                                ("OpenCode Zen", "big-pickle (최종 폴백)", "대기", "#888")]:
        rr(d, [40, y, W - 40, y + 52], 10, fill="#FAFAFC", outline="#EEE", width=1)
        d.ellipse([54 * S, (y + 21) * S, 66 * S, (y + 33) * S], fill=col)
        d.text((80 * S, (y + 9) * S), nm, font=F(12, True), fill="#1A1A2E")
        d.text((80 * S, (y + 30) * S), model, font=F(10), fill="#888")
        bw = d.textlength(st, font=F(10, True)) / S + 22
        rr(d, [W - 52 - bw, y + 15, W - 52, y + 39], 12, fill=col)
        d.text(((W - 52 - bw + 11) * S, (y + 21) * S), st, font=F(10, True), fill="#FFF")
        y += 60
    save(img, "17_settings_apikey.png")

# ---------------- 18. 회원·복지사 관리 (관리자) ----------------
def admin_members():
    W, H = 620, 430
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 14, fill="#FFF")
    text(d, (40, 32), "회원 · 복지사 관리", F(16, True), "#1A1A2E")
    rr(d, [W - 156, 28, W - 40, 58], 8, fill="#E8572A")
    d.text(((W - 144) * S, 36 * S), "+ 복지사 등록", font=F(11, True), fill="#FFF")
    y = 72
    rr(d, [40, y, 128, y + 30], 8, fill="#1A1A2E"); d.text((62 * S, (y + 7) * S), "복지사", font=F(11, True), fill="#FFF")
    rr(d, [134, y, 222, y + 30], 8, outline="#CCC", width=1); d.text((164 * S, (y + 7) * S), "회원", font=F(11), fill="#888")
    y += 44
    for name, x in [("이름", 55), ("지역", 195), ("역할", 320), ("담당 회원", 475)]:
        d.text((x * S, y * S), name, font=F(11, True), fill="#888")
    y += 22
    d.line([40 * S, y * S, (W - 40) * S, y * S], fill="#EEE", width=1 * S); y += 8
    for nm, reg, role, cnt in [("김복지", "전북 순창", "현장 복지사", "12명"),
                                ("이상담", "서울 성북", "현장 복지사", "9명"),
                                ("정관리", "본부", "상위 관리자", "-")]:
        d.text((55 * S, y * S), nm, font=F(12, True), fill="#222")
        d.text((195 * S, y * S), reg, font=F(11), fill="#444")
        d.text((320 * S, y * S), role, font=F(11), fill="#444")
        d.text((475 * S, y * S), cnt, font=F(11), fill="#444")
        y += 30
        d.line([40 * S, y * S, (W - 40) * S, y * S], fill="#F2F2F5", width=1 * S); y += 8
    rr(d, [40, y + 6, W - 40, y + 46], 8, fill="#FFF8EE")
    text(d, (54, y + 15), "복지사 클릭 → '담당 회원' 모달에서 노인·청년을 체크로 배정/해제", F(10.5), "#8A6D3B", maxw=W - 110)
    save(img, "18_admin_members.png")

# ---------------- 19. AI와 설문 협의 (refine) ----------------
def refine_chat():
    W, H = 560, 420
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 14, fill="#FFF")
    y = text(d, (40, 30), "AI와 설문 협의 (refine)", F(16, True), "#1A1A2E") + 10
    m1 = "두 번째 질문을 어르신께 더 친근한 말로 바꿔줘"
    w1 = d.textlength(m1, font=F(11)) / S + 28
    rr(d, [W - 56 - w1, y, W - 56, y + 40], 12, fill="#E8572A")
    d.text(((W - 56 - w1 + 14) * S, (y + 11) * S), m1, font=F(11), fill="#FFF")
    y += 54
    rr(d, [56, y, 56 + 400, y + 78], 12, fill="#EEF1F8")
    d.text((70 * S, (y + 9) * S), "AI", font=F(9, True), fill="#7B7BFF")
    text(d, (70, y + 26), "네, '가장 그리운 사람은?'을 '곁에 있어준 고마운 분은?'으로 다듬었어요. 미리보기에 반영했습니다.", F(11), "#333", maxw=376)
    y += 92
    m3 = "좋아요, 그대로 발행할게요"
    w3 = d.textlength(m3, font=F(11)) / S + 28
    rr(d, [W - 56 - w3, y, W - 56, y + 38], 12, fill="#E8572A")
    d.text(((W - 56 - w3 + 14) * S, (y + 10) * S), m3, font=F(11), fill="#FFF")
    rr(d, [40, H - 68, W - 122, H - 34], 10, fill="#FAFAFC", outline="#DDD", width=1)
    d.text((52 * S, (H - 59) * S), "예: 보기를 더 쉬운 말로 바꿔주세요", font=F(10.5), fill="#AAA")
    rr(d, [W - 112, H - 68, W - 40, H - 34], 10, fill="#1A1A2E")
    d.text(((W - 92) * S, (H - 59) * S), "전송", font=F(11, True), fill="#FFF")
    save(img, "19_refine_chat.png")

# ---------------- 20. 결과물 — AI 생성 그림 ----------------
def image_result():
    W, H = 520, 440
    img = new(W, H, "#F5F7FA"); d = ImageDraw.Draw(img)
    rr(d, [20, 20, W - 20, H - 20], 14, fill="#FFF")
    y = text(d, (40, 34), "AI 생성 그림 — 「강천용소와 노총각」", F(15, True), "#1A1A2E") + 8
    fx0, fy0, fx1, fy1 = 40, y, W - 40, y + 250
    rr(d, [fx0, fy0, fx1, fy1], 10, fill="#DCEAF5")
    d.ellipse([(fx1 - 92) * S, (fy0 + 24) * S, (fx1 - 48) * S, (fy0 + 68) * S], fill="#F6C453")
    d.polygon([(fx0) * S, (fy1) * S, (fx0 + 150) * S, (fy0 + 90) * S, (fx0 + 300) * S, (fy1) * S], fill="#8FB996")
    d.polygon([(fx0 + 180) * S, (fy1) * S, (fx0 + 320) * S, (fy0 + 55) * S, (fx1) * S, (fy1) * S], fill="#6FA383")
    d.ellipse([(fx0 + 120) * S, (fy1 - 72) * S, (fx0 + 300) * S, (fy1 - 8) * S], fill="#5B8FB9")
    text(d, (40, fy1 + 14), "문화데이터(설화)를 소재로 AI가 생성한 삽화 예시 — 수필·시와 함께 결과물로 전달", F(10.5), "#888", maxw=W - 80)
    save(img, "20_image_result.png")

if __name__ == "__main__":
    login(); consent(); topic_elder(); survey_choice(); survey_voice()
    ai_response(); crisis(); youth_home(); stats(); essay()
    welfare_topic(); prompt_format(); deliverable_gen(); youth_survey()
    welfare_dashboard(); survey_analytics(); settings_apikey()
    admin_members(); refine_chat(); image_result()
    print("ALL DONE")
