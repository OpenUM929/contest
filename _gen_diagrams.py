# -*- coding: utf-8 -*-
"""기획서 구성도 3종 생성: 문제의식 / 7단계 파이프라인+기능 / 가치(구현→실증→확산)."""
import math
from PIL import Image, ImageDraw, ImageFont

S = 2
OUT = r"C:\dev\contest\제출본\_md_img"
NAVY = "#1A2A4A"

def F(sz, bold=False):
    return ImageFont.truetype(r"C:\Windows\Fonts\malgun" + ("bd" if bold else "") + ".ttf", sz * S)

def new(w, h):
    img = Image.new("RGB", (w * S, h * S), "white")
    return img, ImageDraw.Draw(img)

def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([c * S for c in box], radius=r * S, fill=fill, outline=outline, width=width * S)

def ct(d, cx, cy, s, font, fill=NAVY):
    lines = s.split("\n")
    lh = font.size * 1.32
    y0 = cy * S - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        d.text((cx * S, y0 + i * lh), ln, font=font, fill=fill, anchor="mm")

def arrow(d, x1, y1, x2, y2, fill="#6B7280", w=3):
    d.line([(x1 * S, y1 * S), (x2 * S, y2 * S)], fill=fill, width=w * S)
    ang = math.atan2(y2 - y1, x2 - x1); l = 11
    for a in (ang - 0.42, ang + 0.42):
        d.line([(x2 * S, y2 * S), ((x2 - l * math.cos(a)) * S, (y2 - l * math.sin(a)) * S)], fill=fill, width=w * S)

def save(img, name):
    img.resize((img.width // S, img.height // S), Image.LANCZOS).save(OUT + "\\" + name)

TB = F(19, True); SB = F(14, True); SM = F(13)

# ───────────────────── 1) 문제의식 구성도 ─────────────────────
img, d = new(1180, 500)
probs = [("노인 고독사", "안부 확인이 사람 발품에\n의존 → 사각지대", 60),
         ("청년 고립·은둔", "끌어낼 '역할·동기'\n설계 부재", 200),
         ("세대 단절", "서로의 자원이 될 두 세대\n만날 접점이 없음", 340)]
for title, sub, y in probs:
    rr(d, [50, y, 360, y + 120], 16, fill="#FDEDEC", outline="#E74C3C", width=2)
    ct(d, 205, y + 35, title, SB, "#C0392B")
    ct(d, 205, y + 80, sub, SM)
    arrow(d, 365, y + 60, 520, 250)
rr(d, [520, 175, 770, 325], 18, fill="#E8572A", outline="#C0392B", width=2)
ct(d, 645, 222, "이음(以音)", F(22, True), "white")
ct(d, 645, 270, "지역문화 데이터로\n동시에 연결", F(13, True), "white")
arrow(d, 775, 250, 905, 250, "#E8572A", 4)
rr(d, [905, 150, 1140, 350], 16, fill="#FEF5EC", outline="#E8572A", width=2)
ct(d, 1022, 200, "하나의 매개로", SB, "#A0410F")
ct(d, 1022, 255, "대화  →  관계", F(16, True), NAVY)
ct(d, 1022, 300, "→  사회안전망", F(16, True), NAVY)
save(img, "diag_problem.png")

# ──────────────── 2) 7단계 파이프라인 + 주요 기능 ────────────────
img, d = new(1180, 560)
def stage(box, letter, title, fn, fill, oc):
    rr(d, box, 14, fill=fill, outline=oc, width=2)
    cx = (box[0] + box[2]) / 2
    ct(d, cx, box[1] + 26, f"{letter}  {title}", SB, NAVY)
    ct(d, cx, box[1] + 70, fn, SM)
top = [("A", "주제 발행", "문화데이터 수집·검증\n→ 매주 자동 발행", 40),
       ("B", "세대 대화", "노인 음성(STT/TTS)\n청년 텍스트·공감응답", 325),
       ("C", "심리·성향 분석", "감정·TTR·반복표현\n누적 MBTI 집계", 610),
       ("D", "결과물 생성", "수필·시·이미지\n자동 창작·낭독", 895)]
BLUE, BO = "#EAF2FB", "#2E6BB0"
for letter, title, fn, x in top:
    stage([x, 60, x + 245, 170], letter, title, fn, BLUE, BO)
for i in range(3):
    arrow(d, top[i][3] + 245, 115, top[i + 1][3], 115, BO)
# 분기: C → E → F
RED, RO = "#FDECEA", "#E74C3C"
arrow(d, 610 + 122, 170, 610 + 122, 300, RO)
stage([610, 300, 855, 410], "E", "안전 감지", "위기 키워드→1393\n3일 미접속 자동점검", RED, RO)
stage([895, 300, 1140, 410], "F", "복지사 연결", "위험도 등급 대시보드\n전화·방문·상담 개입", RED, RO)
arrow(d, 855, 355, 895, 355, RO)
# G 횡단 밴드
rr(d, [40, 460, 1140, 520], 12, fill="#EEF1F4", outline="#7A8699", width=2)
ct(d, 590, 490, "G  데이터 보안 — 전 과정 횡단 : 항목별 동의 · 비식별 · 암호화 · 복지사 검수(Human-in-the-loop)", SB, "#3B4658")
save(img, "diag_pipeline.png")

# ──────────────── 3) 구현→실증→확산 + 사회적 가치 ────────────────
img, d = new(1180, 470)
rr(d, [50, 45, 400, 185], 16, fill="#E9F7EF", outline="#27AE60", width=2)
ct(d, 225, 80, "구현 완료 (MVP)", SB, "#1E8449")
ct(d, 225, 130, "백엔드 · 복지사 대시보드\n· 모바일 앱 동작 검증", SM)
rr(d, [470, 45, 710, 185], 16, fill="#FEF9E7", outline="#D4AC0D", width=2)
ct(d, 590, 90, "지자체·복지관", SB, "#9A7D0A")
ct(d, 590, 135, "실증(파일럿)", SB, "#9A7D0A")
rr(d, [780, 45, 1130, 185], 16, fill="#EBF5FB", outline="#2980B9", width=2)
ct(d, 955, 80, "광역 → 전국 확산", SB, "#1F618D")
ct(d, 955, 130, "경로당·치매안심센터\n·청년지원센터 연계", SM)
arrow(d, 405, 115, 465, 115, "#27AE60", 4)
arrow(d, 715, 115, 775, 115, "#D4AC0D", 4)
arrow(d, 590, 190, 590, 250, "#E8572A", 4)
ct(d, 590, 225, "사회적 가치 창출", F(15, True), "#A0410F")
chips = [("고독사 위험\n조기 발견", 50), ("청년 사회\n재연결", 330),
         ("세대 통합·\n공감 회복", 610), ("지역문화\n재발견", 890)]
for txt, x in chips:
    rr(d, [x, 285, x + 240, 400], 16, fill="#FDF2E9", outline="#E8572A", width=2)
    ct(d, x + 120, 342, txt, SB, "#A0410F")
save(img, "diag_value.png")

print("diagrams saved: diag_problem.png, diag_pipeline.png, diag_value.png")
