# 이음(以音) — 데이터 관리 가이드

> 이 문서는 이음(以音) 프로젝트의 **신규 데이터 추가 방법**을 안내합니다.
> 공통 지침 및 개발 규칙은 [.clinerules/core/00-core.md](.clinerules/core/00-core.md)를 참조하세요.

---

## 1. 개요

이음(以音)은 은둔 청년과 고독사 위험 노인을 연결하는 AI 사회안전망 플랫폼입니다.

본 프로젝트에서는 **지역문화 멀티미디어 데이터**를 활용하여 세대공감 대화 주제를 생성합니다.

---

## 2. 데이터 추가 방법

### 2-1. 새로운 CSV 파일 준비

문화 빅데이터 플랫폼([bigdata-culture.kr](https://www.bigdata-culture.kr))에서 다운로드한 CSV 파일을 준비합니다.

**파일명 규칙**:
```
KF_AREA_FLPNTG_DATA_LIST_YYYYMMDD.csv
```

예시:
- `KF_AREA_FLPNTG_DATA_LIST_202312.csv`
- `KF_AREA_FLPNTG_DATA_LIST_202401.csv`

### 2-2. 파일 복사

준비한 CSV 파일을 프로젝트 **루트 디렉토리**에 복사합니다:

```
C:\dev\contest\
  ├── KF_AREA_FLPNTG_DATA_LIST_202312.csv  ← 기존
  ├── KF_AREA_FLPNTG_DATA_LIST_202401.csv  ← 신규
  └── merge_kf_area.py
```

### 2-3. 병합 스크립트 실행

```bash
# PowerShell
python merge_kf_area.py

# 또는 Python 직접 실행
C:\Program Files\Python313\python.exe merge_kf_area.py
```

**동작**:
1. `C:\dev\contest\` 내의 `KF_AREA_FLPNTG_DATA_LIST_*.csv` 파일을 자동 검색
2. 기존 `KF_AREA_IMAGE.csv` / `KF_AREA_TEXT.csv`와 병합
3. `DATA_MANAGE_NO` 기준 중복 제거 (기존 데이터 유지, 새 데이터만 추가)
4. `MAIN_THUMB_URL` 유무로 **IMAGE** / **TEXT** 분할
5. `KF_AREA_TOP10_KEYWORDS.json` 갱신
6. 결과 출력

### 2-4. 생성되는 파일

| 파일 | 설명 | 용도 |
|------|------|------|
| `KF_AREA_IMAGE.csv` | 이미지 URL 있는 데이터 | `media_type=image` 주제 |
| `KF_AREA_TEXT.csv` | 이미지 URL 없는 데이터 | `media_type=text` 주제 |
| `KF_AREA_TOP10_KEYWORDS.json` | TOP 10 키워드 JSON | 복지사 대시보드 필터 |

### 2-5. 백엔드에 반영

스크립트 실행 후, **백엔드 서버를 재시작**하면 새로운 데이터가 즉시 사용됩니다.

```python
# public_data.py에서 자동으로 로드
fetch_local_culture_data(media_type="image")  # KF_AREA_IMAGE.csv
fetch_local_culture_data(media_type="text")   # KF_AREA_TEXT.csv
```

---

## 3. 데이터 구조

### CSV 컬럼 설명

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `DATA_MANAGE_NO` | 고유 ID | 6597 |
| `DATA_TITLE_NM` | 제목 | 그림 - 200년이 넘은 초가집... |
| `SUMRY_CN` | 상세 설명 | 200~300자 서사 |
| `MAIN_THUMB_URL` | 이미지 URL | `https://minio.nculture.org/...` |
| `CNTNTS_URL` | 상세 페이지 | `https://ncms.nculture.org/...` |
| `CTPRVN_NM` | 시도 | 경상남도, 충청남도 |
| `SIGNGU_NM` | 시군구 | 합천군, 태안군 |
| `CORE_KWRD_CN` | 핵심 키워드 | 설화, 전설, 지명유래 |
| `THEME_NM` | 대분류 | 생활문화, 역사문화유산 |
| `LWPRT_THEME_NM` | 소분류 | 한국의 가옥, 지명유래 |

---

## 4. 현재 데이터 현황

| 구분 | 파일 | 행 수 |
|------|------|------|
| IMAGE | `KF_AREA_IMAGE.csv` | 101개 |
| TEXT | `KF_AREA_TEXT.csv` | 88개 |
| **합계** | | **189개** |

---

## 5. 공통 지침

이 프로젝트의 모든 개발 규칙, 작업 유형 분류, 문서 작성 가이드는 아래 위치에서 확인하세요:

**📍 [.clinerules/core/00-core.md](.clinerules/core/00-core.md)**

핵심 내용:
- 작업 유형별 이동 문서
- 계획서 작성 규칙
- Git 작업 규칙
- 테스트 규칙
- 복구/롤백 규칙

---

## 6. 참고 문서

| 문서 | 내용 | 위치 |
|------|------|------|
| 통합 구현 계획 | 전체 파이프라인 설명 | `plan/이음_통합구현계획_20260604.md` |
| 이미지 프롬프트 설계 | 이미지 분석 프롬프트 설계 | `plan/0609_01_image-prompt-design/0609_01_image-prompt-design.md` |
| 공공데이터 API | API 연동 설명 | `plan/reference/pipeline-A/plan_A_public-data.md` |

---

> **문의**: 데이터 추가나 백엔드 연동에 문제가 있으면 `public_data.py`의 `fetch_local_culture_data()` 함수를 확인하세요.
