# Leadership Analysis System - 인수인계 문서 v2.1

> **프로젝트 상태:** v2.1 완료 (2026-05-18 기준)  
> **데이터 규모:** 178개 라벨, 12,460개 학습 샘플  
> **목적:** 시스템 구조 및 운영 방법 정리

**참고:** 최신 파일 구조는 [FILE_STRUCTURE.md](../FILE_STRUCTURE.md)를 참조하세요.

---

## 1. 시스템 아키텍처 (v2.1)

### 1.1 표준 파이프라인
```
[사용자 텍스트 입력]
         ↓
[Vector DB 검색] ← KoE5 + FAISS (178개 라벨)
         ↓
[임계값 판단] ← should_call_llm()
         ↓
[하이브리드 파이프라인] ← Vector 또는 Vector+LLM
         ↓
[후처리] ← Calibration, 필터링, Conflict 처리
         ↓
[Trait 추론] ← LeadershipEngine
         ↓
[웹 UI 표시] ← http://localhost:5000
```

### 1.2 웹 기반 데이터 수정 시스템
```
[웹 수정] → [저장(개별 파일 + 자동백업)] → [통합 버튼]
                                            ↓
                               [temp/integrated_data.json]
                                            ↓
                               [AI에게 검토 요청]
```

---

## 2. 실행 방법

### 2.1 웹 서버 시작
```bash
cd C:\dev\leadership
python app.py
```
- **접속:** http://localhost:5000
- **라벨 수정:** http://localhost:5000/edit/labels
- **트레이트 수정:** http://localhost:5000/edit/traits

### 2.2 Vector DB 재구축
```bash
python build_vector_db.py
```

### 2.3 통합 파일 수동 생성 (AI 검토용)
```bash
python -c "from src.data_integrator import full_integrate; print(full_integrate())"
```

---

## 3. 데이터 수정 워크플로우

1. 브라우저에서 `http://localhost:5000/edit/labels` 접속
2. 카테고리 선택 → 개별 라벨 클릭 → 수정
3. **저장** 버튼 클릭 (자동 백업 생성)
4. 상단 **[AI 검토용 통합]** 버튼 클릭
5. AI에게 `"temp/integrated_data.json 읽고 검토해줘"` 요청
6. 피드백 반영 후 재수정

---

## 4. 주요 변경사항 (v2.0 → v2.1)

| 항목 | v2.0 | v2.1 |
|------|------|------|
| 라벨 수 | 125개 | **178개** (+53개) |
| 학습 샘플 | 8,750개 | **12,460개** |
| Vector DB | 125 vectors | **178 vectors** |
| 배치 파일 | 15개 | **18개** |
| 통합 파일 | 없음 | `training_data_all_labels.json` 추가 |
| 문서 | 분산 | **AGENTS.md + FILE_STRUCTURE.md** 중앙화 |

---

## 5. 해결된 주요 이슈

- ✅ Python 3.13 호환성
- ✅ Vector DB 결과 웹 UI 표시
- ✅ 개별 라벨/트레이트 파일 관리 시스템
- ✅ 178개 라벨 전체 커버리지
- ✅ 중복 텍스트 제거 (0개)
- ✅ 스타일 태그 표준화

---

## 6. 남은 과제

| 우선순위 | 항목 | 상태 |
|----------|------|------|
| High | `google.genai` 완전 전환 | Pending |
| High | Python 3.11/3.12 다운그레이드 권장 | Pending |
| Medium | Vector DB 자동 재빌드 (라벨 수정 시) | Pending |
| Medium | LLM JSON 파싱 강화 | Pending |
| Low | 실시간 협업 (WebSocket) | Future |
| Low | AI 피드백 자동 반영 | Future |

---

## 7. 참고 자료

- **파이프라인 상세:** [docs/core.md](core.md)
- **개발 계획:** [docs/vector_db_vs_llm_plan.md](vector_db_vs_llm_plan.md)
- **웹 수정 계획:** [docs/WEB_EDIT_PLAN.md](WEB_EDIT_PLAN.md)
- **라벨 감사:** [label_audit_report.md](../label_audit_report.md)

---

> **작성일:** 2026-05-18  
> **상태:** v2.1 데이터 완료, 웹 시스템 운영 중  
> **특이사항:**
> - 라벨/트레이트 개별 파일화 완료
> - AI 검토용 통합 파일 생성 기능 정상 동작
