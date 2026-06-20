# FILE_STRUCTURE.md - Leadership Label Vector DB Project

> 이 문서는 프로젝트의 전체 파일 구조, 데이터 흐름, 라벨 관계도, 그리고 각 파일의 역할과 상호 의존성을 정의합니다.  
> 자세한 프로젝트 개요와 품질 기준은 [AGENTS.md](AGENTS.md)를 참조하세요.

---

## 1. 디렉토리 구조

```
C:\dev\leadership\
├── AGENTS.md                          # 프로젝트 개요 및 품질 기준
├── FILE_STRUCTURE.md                  # 이 파일
├── label_audit_report.md              # v2.1 라벨 감사 보고서 (178개 라벨 정의)
├── build_vector_db.py                 # FAISS 인덱스 빌더
├── app.py / app_new.py                # 메인 애플리케이션
├── src/                               # 애플리케이션 소스 코드
│   ├── routes/                        # API 라우트
│   ├── auth.py
│   ├── vector_search.py
│   ├── hybrid_search.py
│   ├── leadership_engine.py
│   └── ...
├── data/                              # 중앙 데이터 저장소
│   ├── labels/
│   │   ├── positive_labels.json       # 48개 긍정 매크로 카테고리
│   │   └── negative_labels.json       # 32개 부정 매크로 카테고리
│   ├── micro_labels/
│   │   ├── positive_micro_labels.json # v1.0 긍정 마이크로 라벨
│   │   ├── negative_micro_labels.json # v1.0 부정 마이크로 라벨
│   │   ├── positive/                  # 개별 마이크로 라벨 JSON (M01-01 ~ M48-01)
│   │   └── negative/                  # 개별 마이크로 라벨 JSON (N01-01 ~ N43-01)
│   ├── vectors/
│   │   ├── label_vectors.faiss        # FAISS 인덱스 (KoE5, 768-dim, 178 vectors)
│   │   ├── metadata.json              # 라벨 메타데이터
│   │   └── test_results.json          # T04-B, T105-A 테스트 결과
│   ├── engine/                        # 검색 엔진 규칙
│   ├── traits/                        # 특성(Trait) 정의
│   └── patterns/                      # 벡터 검색 패턴
├── dataset/                           # 학습 데이터 세트
│   ├── ori/                           # 권위 데이터 소스 (원본)
│   │   ├── positive_micro_labels_enhanced.json   # 98 긍정 enhanced 라벨
│   │   ├── negative_micro_labels_enhanced.json   # 80 부정 enhanced 라벨
│   │   ├── positive_v2_micro_labels.json         # v2.0 추가 긍정 라벨
│   │   ├── negative_v2_micro_labels.json         # v2.0 추가 부정 라벨
│   │   ├── batch1_M01-01_to_M03-03.json          # Positive wave 1
│   │   ├── batch2_M04-01_to_M07-02.json          # Positive wave 1
│   │   ├── batch3_M08-01_to_M12-03.json          # Positive wave 1
│   │   ├── batch4_M13-01_to_M18-02.json          # Positive wave 1
│   │   ├── batch5_M19-01_to_M24-02.json          # Positive wave 1
│   │   ├── batch6_M25-01_to_M31-01.json          # Positive wave 2
│   │   ├── batch7_M32-01_to_M37-02.json          # Positive wave 2
│   │   ├── batch8_M38-01_to_M43-03.json          # Positive wave 2
│   │   ├── batch9_M44-01_to_M48-01.json          # Positive wave 2
│   │   ├── batch10_N01-01_to_N04-02.json         # Negative wave 1
│   │   ├── batch11_N05-01_to_N08-03.json         # Negative wave 1
│   │   ├── batch12_N09-01_to_N16-01.json         # Negative wave 2
│   │   ├── batch13_N17-01_to_N25-01.json         # Negative wave 2
│   │   ├── batch14_N26-01_to_N31-01.json         # Negative wave 2
│   │   ├── batch15_N33-01_to_N43-01.json         # Negative wave 3
│   │   ├── batch16_missing_pos_1.json            # Backfill: M01-04 ~ M47-02
│   │   ├── batch17_missing_neg_1.json            # Backfill: N01-01 ~ N03-04
│   │   ├── batch18_missing_neg_2.json            # Backfill: N04-01 ~ N06-03
│   │   ├── batch19_missing_neg_3.json            # Backfill: N07-01 ~ N08-03
│   │   ├── batch20_N24-02.json                   # Backfill: N24-02
│   │   └── training_data_all_labels.json         # 18개 배치 통합 파일
│   └── real_world/                    # 실제 한국 기업 사례 데이터
├── docs/                              # 설계 문서
│   ├── architecture.md
│   └── leadership_trait_system.md
├── templates/                         # 웹 UI 템플릿
├── static/                            # CSS/JS 정적 파일
└── temp/                              # 임시 작업 파일 (버전 관리 대상 아님)
```

---

## 2. 데이터 흐름 및 의존성

```
[라벨 정의 소스]
  ├── data/labels/positive_labels.json ──────┐
  ├── data/labels/negative_labels.json ──────┤
  ├── dataset/ori/positive_micro_labels_enhanced.json ──┤──> build_vector_db.py
  └── dataset/ori/negative_micro_labels_enhanced.json ──┤     └──> data/vectors/label_vectors.faiss
                                                          │           └──> data/vectors/metadata.json
[학습 데이터 소스]                                          │
  ├── dataset/ori/batch1.json ~ batch20.json ─────────────┤──> (병합)
  └── dataset/ori/training_data_all_labels.json <─────────┘
```

**의존성 규칙:**
- `build_vector_db.py`는 **반드시** `*_enhanced.json` 파일을 읽습니다. 개별 `data/micro_labels/` 파일은 참조하지 않습니다.
- `training_data_all_labels.json`은 18개 `batch*.json`의 **단순 병합**입니다. 직접 수정하지 말고, 개별 배치를 수정한 후 재병합하세요.

---

## 3. 라벨 계층 구조 (Macro → Micro)

### 긍정 리더십 (Positive): 48 Macro → 98 Micro

| Macro ID | Macro Name | Micro Labels (ID Range) |
|----------|------------|------------------------|
| M01 | 비전 및 방향 설정 | M01-01 ~ M01-04 (4개) |
| M02 | 동기 부여 및 영감 | M02-01 ~ M02-04 (4개) |
| M03 | 창의성 및 혁신 촉진 | M03-01 ~ M03-03 (3개) |
| M04 | 카리스마 및 영향력 | M04-01 ~ M04-02 (2개) |
| M05 | 변화 관리 및 실행 | M05-01 ~ M05-03 (3개) |
| M06 | 명확한 목표 설정 및 전달 | M06-01 ~ M06-02 (2개) |
| M07 | 피드백 및 코칭 | M07-01 ~ M07-02 (2개) |
| M08 | 윤리 및 공정성 | M08-01 ~ M08-02 (2개) |
| M09 | 공정한 성과 인정 | M09-01 (1개) |
| M10 | 실행력 및 완수 | M10-01 ~ M10-02 (2개) |
| M11 | 적극적 경청 및 소통 | M11-01 ~ M11-02 (2개) |
| M12 | 공감 및 감정적 지지 | M12-01 ~ M12-03 (3개) |
| M13 | 회복력 및 인내 | M13-01 (1개) |
| M14 | 희생 및 서번트 리더십 | M14-01 ~ M14-02 (2개) |
| M15 | 심리적 안전감 및 신뢰 | M15-01 ~ M15-06 (6개) |
| M16 | 이해관계자 관리 | M16-01 (1개) |
| M17 | 적응력 및 유연성 | M17-01 (1개) |
| M18 | 데이터 및 근거 기반 | M18-01 ~ M18-02 (2개) |
| M19 | 의사결정 | M19-01 (1개) |
| M20 | 위기 대응 | M20-01 (1개) |
| M21 | 학습 및 디지털 민첩성 | M21-01 ~ M21-02 (2개) |
| M22 | 혁신 기회 탐색 | M22-01 ~ M22-03 (3개) |
| M23 | 아이디어 발굴 | M23-01 ~ M23-02 (2개) |
| M24 | 운영 안정성 | M24-01 ~ M24-02 (2개) |
| M25 | 글로벌/다문화 | M25-01 (1개) |
| M26 | 실험 및 도전 | M26-01 (1개) |
| M27 | 자원 관리 | M27-01 ~ M27-02 (2개) |
| M28 | 투명성 및 포용성 | M28-01 ~ M28-02 (2개) |
| M29 | 팀 웰빙 | M29-01 (1개) |
| M30 | 언행 일치 | M30-01 (1개) |
| M31 | 포용성 | M31-01 (1개) |
| M32 | 자기성찰 | M32-01 ~ M32-02 (2개) |
| M33 | 도덕적 용기 | M33-01 ~ M33-05 (5개) |
| M34 | 데이터 의사결정 | M34-01 (1개) |
| M35 | 디지털 도구 | M35-01 (1개) |
| M36 | 전략적 사고 | M36-01 ~ M36-04 (4개) |
| M37 | AI 및 기술 혁신 | M37-01 ~ M37-02 (2개) |
| M38 | 경청과 공감 | M38-01 ~ M38-02 (2개) |
| M39 | 인재 육성 | M39-01 (1개) |
| M40 | 예외 관리 | M40-01 ~ M40-02 (2개) |
| M41 | 자기인식 | M41-01 ~ M41-02 (2개) |
| M42 | 직원 중심성 | M42-01 (1개) |
| M43 | 참여적 리더십 | M43-01 ~ M43-03 (3개) |
| M44 | 정치적 인식 | M44-01 ~ M44-02 (2개) |
| M45 | 환경/사회 책임 | M45-01 ~ M45-02 (2개) |
| M46 | 주도성 및 기회 | M46-01 ~ M46-02 (2개) |
| M47 | 공유 리더십 | M47-01 ~ M47-02 (2개) |
| M48 | 자애적 리더십 | M48-01 (1개) |

### 부정 리더십 (Negative): 32 Macro → 80 Micro

| Macro ID | Macro Name | Micro Labels (ID Range) |
|----------|------------|------------------------|
| N01 | 비현실적 기대 | N01-01 ~ N01-03 (3개) |
| N02 | 공포 및 조작 | N02-01 ~ N02-03 (3개) |
| N03 | 불공정성 및 편파 | N03-01 ~ N03-04 (4개) |
| N04 | 권위 남용 | N04-01 ~ N04-02 (2개) |
| N05 | 변화 저항 | N05-01 ~ N05-04 (4개) |
| N06 | 혼란 및 불명확 | N06-01 ~ N06-03 (3개) |
| N07 | 성과 편파 | N07-01 ~ N07-02 (2개) |
| N08 | 책임 회피 | N08-01 ~ N08-03 (3개) |
| N09 | 정보 독점 | N09-01 ~ N09-02 (2개) |
| N10 | 감정 억압 | N10-01 ~ N10-02 (2개) |
| N11 | 소통 단절 | N11-01 ~ N11-02 (2개) |
| N12 | 팀 분열 조장 | N12-01 ~ N12-03 (3개) |
| N13 | 이중잣대 | N13-01 (1개) |
| N14 | 약속 불이행 | N14-01 ~ N14-03 (3개) |
| N15 | 독단 및 배제 | N15-01 ~ N15-07 (7개) |
| N16 | 감정적 무관심 | N16-01 (1개) |
| N17 | 적대적 경쟁 | N17-01 (1개) |
| N18 | 불공정 자원 배분 | N18-01 ~ N18-02 (2개) |
| N19 | 독단 결정 | N19-01 (1개) |
| N21 | 모순적 메시지 | N21-01 (1개) |
| N22 | 부정적 피드백 | N22-01 ~ N22-02 (2개) |
| N23 | 감시 및 통제 | N23-01 (1개) |
| N24 | 미세관리 | N24-01 ~ N24-02 (2개) |
| N25 | 차별 및 배제 | N25-01 (1개) |
| N26 | 실패 처벌 | N26-01 (1개) |
| N27 | 자원 독점 | N27-01 (1개) |
| N28 | 정보 은폐 | N28-01 (1개) |
| N30 | 말과 행동 불일치 | N30-01 (1개) |
| N31 | 차별 행동 | N31-01 (1개) |
| N33 | 문제 회피 | N33-01 ~ N33-02 (2개) |
| N34 | 기회 무시 | N34-01 (1개) |
| N35 | 기술 거부 | N35-01 (1개) |
| N37 | 디지털 무능 | N37-01 (1개) |
| N38 | 수동적 관리 | N38-01 ~ N38-03 (3개) |
| N39 | 변화 거부 | N39-01 ~ N39-04 (4개) |
| N40 | 보상 편파 | N40-01 ~ N40-02 (2개) |
| N41 | 자기 인식 결여 | N41-01 ~ N41-03 (3개) |
| N42 | 직원 무시 | N42-01 (1개) |
| N43 | 배제적 리더십 | N43-01 (1개) |

---

## 4. 배치 파일 매핑 (Batch → Label IDs)

각 배치 파일은 연속된 라벨 ID 범위를 담당합니다. **합산 178개 라벨 × 70개 샘플 = 12,460개 레코드**를 포함합니다.

### 긍정 (Positive) 배치

| Batch File | Label Range | Labels | Samples | Wave |
|------------|-------------|--------|---------|------|
| `batch1_M01-01_to_M03-03.json` | M01-01 ~ M03-03 | 9 | 630 | 1 |
| `batch2_M04-01_to_M07-02.json` | M04-01 ~ M07-02 | 8 | 560 | 1 |
| `batch3_M08-01_to_M12-03.json` | M08-01 ~ M12-03 | 10 | 700 | 1 |
| `batch4_M13-01_to_M18-02.json` | M13-01 ~ M18-02 | 13 | 910 | 1 |
| `batch5_M19-01_to_M24-02.json` | M19-01 ~ M24-02 | 11 | 770 | 1 |
| `batch6_M25-01_to_M31-01.json` | M25-01 ~ M31-01 | 7 | 490 | 2 |
| `batch7_M32-01_to_M37-02.json` | M32-01 ~ M37-02 | 15 | 1,050 | 2 |
| `batch8_M38-01_to_M43-03.json` | M38-01 ~ M43-03 | 11 | 770 | 2 |
| `batch9_M44-01_to_M48-01.json` | M44-01 ~ M48-01 | 5 | 350 | 2 |
| `batch16_missing_pos_1.json` | M01-04, M02-04, M05-03, M24-02, M27-02, M28-02, M44-02, M45-02, M46-02, M47-02 | 10 | 700 | Backfill |

### 부정 (Negative) 배치

| Batch File | Label Range | Labels | Samples | Wave |
|------------|-------------|--------|---------|------|
| `batch10_N01-01_to_N04-02.json` | N01-01 ~ N04-02 | 10 | 700 | 1 |
| `batch11_N05-01_to_N08-03.json` | N05-01 ~ N08-03 | 11 | 770 | 1 |
| `batch12_N09-01_to_N16-01.json` | N09-01 ~ N16-01 | 21 | 1,470 | 2 |
| `batch13_N17-01_to_N25-01.json` | N17-01 ~ N25-01 | 10 | 700 | 2 |
| `batch14_N26-01_to_N31-01.json` | N26-01 ~ N31-01 (N29 제외) | 5 | 350 | 2 |
| `batch15_N33-01_to_N43-01.json` | N33-01 ~ N43-01 (N32, N36 제외) | 19 | 1,330 | 3 |
| `batch17_missing_neg_1.json` | N01-01 ~ N03-04 | 10 | 700 | Backfill |
| `batch18_missing_neg_2.json` | N04-01 ~ N06-03 | 9 | 630 | Backfill |
| `batch19_missing_neg_3.json` | N07-01 ~ N08-03 | 5 | 350 | Backfill |
| `batch20_N24-02.json` | N24-02 | 1 | 70 | Backfill |

### 통합 파일

| File | Source | Description |
|------|--------|-------------|
| `training_data_all_labels.json` | batch1~20 병합 | 12,460개 레코드의 단일 마스터 파일 |

---

## 5. JSON 스키마 명세

### 배치 파일 스키마 (`batch*.json`)

```json
[
  {
    "text": "Korean workplace sentence string (20-120 chars)",
    "label_id": "M01-01",
    "label_name": "비전 공유",
    "label_type": "positive",
    "data_type": "clean",
    "style": "direct_speech"
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | 한국어 직장 문장 (20-120자) |
| `label_id` | string | Yes | 라벨 ID (예: M01-01, N05-03) |
| `label_name` | string | Yes | 한국어 라벨명 |
| `label_type` | string | Yes | `"positive"` 또는 `"negative"` |
| `data_type` | string | Yes | `"clean"` 또는 `"hard_negative"` |
| `style` | string | Yes | `"direct_speech"`, `"indirect_report"`, `"scene_description"`, `"euphemism"` |

### Enhanced 라벨 정의 스키마 (`*_micro_labels_enhanced.json`)

```json
{
  "schema_version": "2.1",
  "type": "positive",
  "total_count": 98,
  "micro_labels": [
    {
      "label_id": "M01-01",
      "label_name": "명확한 비전 제시",
      "macro_category": "M01",
      "definition": "리더가 명확하고 구체적인 비전을 제시하는 행동",
      "when": "비전 제시, 방향 설정, 장기 목표 공유",
      "not_when": "모호한 방향, 일방적 결정"
    }
  ]
}
```

---

## 6. 파일 상태 분류

### Source Files (수정 금지 / 버전 관리 필수)
- `data/labels/*.json` — 매크로 카테고리 정의
- `dataset/ori/*_enhanced.json` — 벡터DB의 유일한 소스
- `dataset/ori/training_data_all_labels.json` — 통합 마스터 파일

### Generated Files (재생성 가능)
- `data/vectors/label_vectors.faiss` — `build_vector_db.py`로 재생성
- `data/vectors/metadata.json` — `build_vector_db.py`로 재생성
- `data/vectors/test_results.json` — `build_vector_db.py`로 재생성

### Batch Files (수정 가능 / 재병합 필요)
- `dataset/ori/batch1.json` ~ `batch20.json` — 개별 수정 후 `training_data_all_labels.json` 재생성

### Deprecated (사용하지 않음)
- `dataset/batch1_M01-01_to_M03-02.json` — 저품질 자동 생성 데이터 (신규 배치로 대체)
- `dataset/batch1_extended_*.json` — 확장 버전 (현재 불필요)

### Temporary (임시 파일 / 삭제 가능)
- `temp/` 디렉토리 내 모든 파일
- 루트의 `e.md`, `issues.txt`, `short_strings.txt` 등

---

## 7. 라벨 ID 네이밍 규칙

- **Positive**: `M{매크로번호}-{시퀀스}` (예: M01-01, M15-04)
- **Negative**: `N{매크로번호}-{시퀀스}` (예: N01-01, N33-02)
- **Backfill 배치명**: `batch{번호}_missing_{pos|neg}_{순번}.json` (예: batch16_missing_pos_1.json)

**주의**: 매크로 번호가 연속적이지 않을 수 있습니다 (예: N32, N36은 현재 정의되지 않음).
