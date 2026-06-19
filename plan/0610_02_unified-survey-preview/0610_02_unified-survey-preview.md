# Unified Survey Preview — 주제 정보 + AI 질문 통합 미리보기

> 상태: PND | 작성일: 2026-06-10 | 작업 유형: 🔴 계획서

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-10 | 초안 작성 | 최초 계획 수립 |

---

## 1. 배경

### 1.1 현재 문제

`TopicManager.tsx`의 Step 3(발행 확인)에서 주제 정보와 AI 질문 미리보기가 **분리**되어 있어 사용자 경험이 나쁨:

1. **`selectedPreview`** (lines 490-527) — form **위**에 주제 정보 표시
2. **`SurveyPreview`** (line 682) — form **아래**에 질문 목록 표시
3. 동일한 `selected` 객체가 `selectedPreview`와 `SurveyPreview` 내 `candidate` 블록에서 **중복 렌더링**

→ 사용자가 전체 설문지를 보려면 form controls를 스크롤로 넘겨야 함

### 1.2 목표

- `selectedPreview`(주제 정보)를 `SurveyPreview`로 통합
- 하나의 프리뷰에서 주제 정보 + AI 질문을 함께 표시
- 중복 제거, 레이아웃 단순화

---

## 2. 변경 사항

### 2.1 `TopicManager.tsx` — selectedPreview 제거

- **삭제**: lines 490-527 (`selectedPreview` div 전체)
- **삭제**: 관련 스타일 (`s.selectedPreview`, `s.candidateImg`, `s.mediaPlaceholder`, `s.selectedTitle`, `s.candidateSource`, `s.candidateDesc`, `s.analysisSummary`, `s.analysisLine`, `s.topicChip`)
- **유지**: `SurveyPreview` 호출 (`candidate={selected}` prop)

### 2.2 `SurveyPreview.tsx` — 통합 프리뷰로 확장

| 항목 | 현재 | 변경 |
|------|------|------|
| 이미지 높이 | 120px | **200px** |
| 특징(features) 표시 | 첫 2개만 | **전체** |
| 주제 칩(topic_candidates) | 첫 2개만 | **전체** |
| 레이아웃 | candidate → title+토글 → 질문 | candidate → **구분선+헤더** → 질문 |
| 구분선 | 없음 | `──── 🤖 AI 생성 질문 ──── [노인용|청년용]` |

### 2.3 최종 배치 순서

```
┌─ 발행 확인 (card) ─────────────────────┐
│ ← 후보 다시 보기                        │
│                                         │
│ ┌─ SurveyPreview ────────────────────┐  │
│ │ [이미지 200px / 오디오 / 플레이스홀더] │  │
│ │ [제목]                              │  │
│ │ [출처] · 사진                        │  │
│ │ [설명 또는 "설명 정보가 없습니다"]    │  │
│ │ ┌─ 분석 요약 ─────────────────┐    │  │
│ │ │ 🏺 시대 · 유형 · 특징(전체)  │    │  │
│ │ │ 🎨 분위기                   │    │  │
│ │ │ 💡 주제칩(전체)              │    │  │
│ │ └─────────────────────────────┘    │  │
│ │ ──── 🤖 AI 생성 질문 ──── [노인|청년] │  │
│ │ [질문 목록]                        │  │
│ └────────────────────────────────────┘  │
│                                         │
│ [질문 유형 / 수량 선택]                 │
│ [AI 생성 질문 textarea]                 │
│ [미리보기 생성 버튼]                    │
│                                         │
│ [AI 협의 / 직접 수정 / 발행]            │
└─────────────────────────────────────────┘
```

---

## 3. 파일별 상세 변경 내역

### 3.1 `dashboard/src/pages/TopicManager.tsx`

| 라인 | 변경 |
|------|------|
| 490-527 | `selectedPreview` div 블록 **삭제** |
| 682 | `SurveyPreview` 호출 **유지** (변경 없음) |
| 826-875 | `s.candidateImg`, `s.mediaPlaceholder`, `s.selectedPreview`, `s.selectedTitle`, `s.candidateSource`, `s.candidateDesc`, `s.analysisSummary`, `s.analysisLine`, `s.topicChip` **삭제** |

### 3.2 `dashboard/src/components/SurveyPreview.tsx`

| 라인 | 변경 |
|------|------|
| 41 | 이미지 `height: 120` → `height: 200` |
| 71 | features `slice(0, 2)` → 전체 표시 |
| 77 | topic_candidates `slice(0, 2)` → 전체 표시 |
| 88-89 | `gap: 4, marginTop: 4` → `gap: 6, marginTop: 6` |
| 90-124 | title + elder/youth toggle 통째로 구분선 컴포넌트로 교체 |

---

## 4. 검증

1. **TypeScript 빌드**: `cd dashboard && npx vite build` 통과 확인
2. **기능 확인**:
   - Step 2(후보보기) → Step 3(발행확인) 전환 정상
   - 주제 정보(이미지, 설명, 분석)가 SurveyPreview 내에 표시
   - "🤖 AI 생성 질문" 구분선 정상 렌더링
   - 노인용/청년용 토글 정상 동작
3. **중복 제거 확인**: `selectedPreview` div 제거 후 중복 없음

---

## 5. 위험 요소

| 위험 | 대응 |
|------|------|
| `selectedPreview` 제거로 정보 손실 | SurveyPreview candidate 블록이 모든 정보 포함하므로 무손실 |
| 스타일 중복 (`s.*` vs inline) | 삭제된 스타일이 다른 곳에서 참조되지 않는지 빌드로 확인 |
| 이미지 height 200px로 인한 레이아웃 깨짐 | 부모 컨테이너가 flex column이므로 자연스럽게 확장 |
