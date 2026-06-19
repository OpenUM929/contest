#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KF_AREA 지역문화 멀티미디어 데이터 병합 스크립트

[사용법]
1. 새로운 CSV 파일을 C:\\dev\\contest\\ 디렉토리에 복사
   (파일명: KF_AREA_FLPNTG_DATA_LIST_*.csv)
2. 본 스크립트 실행:
   python merge_kf_area.py
3. KF_AREA_IMAGE.csv / KF_AREA_TEXT.csv / KF_AREA_TOP10_KEYWORDS.json 자동 갱신

[동작]
- C:\\dev\\contest\\ 내의 KF_AREA_FLPNTG_DATA_LIST_*.csv 파일을 모두 검색
- 기존 KF_AREA_IMAGE.csv / KF_AREA_TEXT.csv와 병합
- DATA_MANAGE_NO 기준 중복 제거 (기존 데이터 유지, 새 데이터 추가)
- MAIN_THUMB_URL 유무로 IMAGE / TEXT 분할
- TOP 10 키워드(CORE_KWRD_CN) 재계산
"""

import csv
import json
import glob
from collections import Counter
from pathlib import Path

# 설정
DATA_DIR = Path(r"C:\dev\contest")
INPUT_PATTERN = "KF_AREA_FLPNTG_DATA_LIST_*.csv"
OUTPUT_IMAGE = DATA_DIR / "KF_AREA_IMAGE.csv"
OUTPUT_TEXT = DATA_DIR / "KF_AREA_TEXT.csv"
OUTPUT_KEYWORDS = DATA_DIR / "KF_AREA_TOP10_KEYWORDS.json"

# ============================================================
# 키워드 정제 매핑: raw 키워드 → 상위 카테고리
# ============================================================
KEYWORD_CATEGORY_MAP = {
    # 이야기/설화
    "설화": "이야기/설화", "전설": "이야기/설화", "신화": "이야기/설화",
    "구전": "이야기/설화", "민담": "이야기/설화", "이야기": "이야기/설화",
    "지명유래": "이야기/설화",  # 대부분 지명 유래 설화

    # 역사/인물
    "이성계": "역사/인물", "인조": "역사/인물", "헌종": "역사/인물",
    "강세황": "역사/인물", "도선국사": "역사/인물", "은진송씨": "역사/인물",
    "원님": "역사/인물", "임진왜란": "역사/인물", "의병": "역사/인물",
    "독립운동": "역사/인물", "독립운동가": "역사/인물",
    "조선 후기 문인": "역사/인물", "문인": "역사/인물", "선비": "역사/인물",
    "유생": "역사/인물", "효종": "역사/인물", "왕": "역사/인물",
    "임금": "역사/인물", "후비": "역사/인물",

    # 전통가옥/건축
    "양반집": "전통가옥", "ㅁ자형구조": "전통가옥", "ㅁ자형 가옥": "전통가옥",
    "한옥체험": "전통가옥", "한옥": "전통가옥", "초가집": "전통가옥",
    "가옥": "전통가옥",

    # 자연/약수/관광
    "탄산약수": "자연/약수", "약수": "자연/약수", "온천": "자연/약수",
    "약수터": "자연/약수",

    # 불교/문화유산
    "마애불": "불교/문화유산", "불상": "불교/문화유산", "사찰": "불교/문화유산",
    "석불": "불교/문화유산", "불교": "불교/문화유산", "마애": "불교/문화유산",
    "지석묘": "불교/문화유산",

    # 민속/의례
    "기자신앙": "민속/의례", "제사": "민속/의례", "세시풍속": "민속/의례",
    "의례": "민속/의례", "민속": "민속/의례", "민속놀이": "민속/의례",
    "관혼상제": "민속/의례", "풍속": "민속/의례",

    # 예술/공예
    "현대미술": "예술/공예", "동판화": "예술/공예", "복합문화공간": "예술/공예",
    "그림": "예술/공예", "회화": "예술/공예", "공예": "예술/공예",
    "미술": "예술/공예", "판화": "예술/공예", "조각": "예술/공예",

    # 노동/민요
    "민요": "노동/민요", "노동요": "노동/민요", "소리": "노동/민요",
    "농요": "노동/민요",

    # 생활/문화
    "은혜": "생활/문화", "용": "생활/문화",
    "복합문화공간": "생활/문화",

    # 전쟁/호국
    "임진왜란": "전쟁/호국", "의병": "전쟁/호국",
    "독립운동": "전쟁/호국", "독립운동가": "전쟁/호국",
    "한국전쟁": "전쟁/호국", "6.25": "전쟁/호국",
}

# 설화/이야기 판정 키워드 (media_subtype = story)
STORY_KEYWORDS = {"설화", "전설", "신화", "구전", "민담", "이야기", "지명유래"}


def extract_raw_keywords(row: dict) -> list[str]:
    """CORE_KWRD_CN에서 개별 키워드 리스트 추출"""
    kw = row.get("CORE_KWRD_CN", "").strip()
    if not kw:
        return []
    return [p.strip() for p in kw.replace(";", ",").split(",") if p.strip()]


def compute_refined_keywords(raw_keywords: list[str]) -> list[str]:
    """
    raw 키워드 → refined 카테고리로 변환
    exact match 우선, 없으면 substring match
    """
    refined = []
    seen = set()
    for rk in raw_keywords:
        cat = KEYWORD_CATEGORY_MAP.get(rk)
        if cat and cat not in seen:
            refined.append(cat)
            seen.add(cat)
        elif cat is None:
            # substring match 시도
            for map_key, map_cat in KEYWORD_CATEGORY_MAP.items():
                if map_key in rk and map_cat not in seen:
                    refined.append(map_cat)
                    seen.add(map_cat)
                    break
    return refined


def is_story_row(row: dict) -> bool:
    """이야기(설화/전설) 여부 판정"""
    raw = extract_raw_keywords(row)
    for rk in raw:
        for sk in STORY_KEYWORDS:
            if sk in rk:  # substring match (e.g. "해령사에 얽힌 전설" -> 전설)
                return True
    # LWPRT_THEME_NM으로도 판정
    sub = row.get("LWPRT_THEME_NM", "").strip()
    if sub in ("한국인의 일생", "구비문학", "한국 구전문학", "한국인의 설화", "한국인의 이야기"):
        return True
    return False


def load_csv(path: Path) -> list[dict]:
    """CSV 파일을 읽어 dict 리스트로 반환"""
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def save_csv(path: Path, rows: list[dict]) -> None:
    """dict 리스트를 CSV 파일로 저장"""
    if not rows:
        print(f"[WARN] {path.name}에 저장할 데이터가 없습니다.")
        return
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] {path.name} 저장 완료 ({len(rows)}개)")


def merge_data():
    """메인 병합 로직"""
    print("=" * 60)
    print("KF_AREA 데이터 병합 시작")
    print("=" * 60)

    # 1. 기존 데이터 로드 (이미 병합된 IMAGE/TEXT)
    existing_image = load_csv(OUTPUT_IMAGE)
    existing_text = load_csv(OUTPUT_TEXT)
    existing_ids = set()
    for row in existing_image + existing_text:
        data_id = row.get("DATA_MANAGE_NO", "").strip()
        if data_id:
            existing_ids.add(data_id)

    print(f"\n[1] 기존 데이터: IMAGE={len(existing_image)}개, TEXT={len(existing_text)}개")
    print(f"    기존 고유 ID: {len(existing_ids)}개")

    # 2. 새로운 입력 파일 검색
    input_files = glob.glob(str(DATA_DIR / INPUT_PATTERN))
    print(f"\n[2] 입력 파일 검색: {len(input_files)}개 발견")
    for f in input_files:
        print(f"    - {Path(f).name}")

    # 3. 새 파일들을 읽어서 병합 (중복 제거)
    new_rows = []
    new_ids = set()
    skipped_count = 0

    for f in input_files:
        rows = load_csv(Path(f))
        for row in rows:
            data_id = row.get("DATA_MANAGE_NO", "").strip()
            if not data_id:
                continue
            if data_id in existing_ids or data_id in new_ids:
                skipped_count += 1
                continue
            new_ids.add(data_id)
            new_rows.append(row)

    print(f"\n[3] 신규 데이터: {len(new_rows)}개")
    print(f"    중복 제거: {skipped_count}개")

    # 4. 기존 + 신규 데이터 합치기
    all_rows = existing_image + existing_text + new_rows
    print(f"\n[4] 전체 데이터: {len(all_rows)}개")

    # 5. 키워드 정제 + 이야기 판정
    for row in all_rows:
        raw_keywords = extract_raw_keywords(row)
        refined = compute_refined_keywords(raw_keywords)
        row["REFINED_KWRD_CN"] = "; ".join(refined) if refined else ""
        row["IS_STORY"] = "Y" if is_story_row(row) else "N"

    # 6. IMAGE / TEXT 분할
    image_rows = []
    text_rows = []

    for row in all_rows:
        thumb_url = row.get("MAIN_THUMB_URL", "").strip()
        if thumb_url and thumb_url.startswith("http"):
            row["media_type"] = "image"
            row["media_subtype"] = "image"
            image_rows.append(row)
        else:
            row["media_type"] = "text"
            row["media_subtype"] = "story" if row.get("IS_STORY") == "Y" else "text"
            text_rows.append(row)

    print(f"\n[5] 분할 결과: IMAGE={len(image_rows)}개, TEXT={len(text_rows)}개")
    story_count = sum(1 for r in text_rows if r.get("media_subtype") == "story")
    print(f"       이야기(설화/전설): {story_count}개")

    # 7. 저장 (REFINED_KWRD_CN, IS_STORY, media_subtype 컬럼 포함)
    save_csv(OUTPUT_IMAGE, image_rows)
    save_csv(OUTPUT_TEXT, text_rows)

    # 8. TOP 10 키워드 추출 (REFINED_KWRD_CN 기준)
    refined_keywords = []
    for row in all_rows:
        rk = row.get("REFINED_KWRD_CN", "").strip()
        if rk:
            parts = [p.strip() for p in rk.replace(";", ",").split(",") if p.strip()]
            refined_keywords.extend(parts)

    counter = Counter(refined_keywords)
    top20 = [{"keyword": k, "count": v} for k, v in counter.most_common(20) if v >= 2]
    top10 = top20[:10]

    with open(OUTPUT_KEYWORDS, "w", encoding="utf-8") as fh:
        json.dump(top10, fh, ensure_ascii=False, indent=2)

    print(f"\n[6] TOP 10 키워드 (정제):")
    for item in top10:
        print(f"    {item['keyword']}: {item['count']}")
    print(f"\n[OK] {OUTPUT_KEYWORDS.name} 저장 완료")

    print("\n" + "=" * 60)
    print("병합 완료!")
    print(f"  - IMAGE: {len(image_rows)}개")
    print(f"  - TEXT: {len(text_rows)}개 (이야기: {story_count}개)")
    print(f"  - TOTAL: {len(all_rows)}개")
    print("=" * 60)


if __name__ == "__main__":
    merge_data()
