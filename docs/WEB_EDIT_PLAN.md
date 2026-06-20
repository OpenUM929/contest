# 라벨/트레이트 웹 기반 수정 시스템 계획서 (v2.1)

> **작성일:** 2026-05-18  
> **상태:** 구현 완료, 운영 중  
> **핵심 변경:** 개별 라벨/트레이트 파일 관리 + AI 검토용 통합 버튼

**참고:** 최신 파일 구조는 [FILE_STRUCTURE.md](../FILE_STRUCTURE.md)를 참조하세요.

---

## 1. 시스템 아키텍처

### 데이터 관리 방식
- **기존:** `positive_micro_labels.json` (통합)
- **현재:** `data/micro_labels/positive/M01-01.json` (개별 파일)
- **이유:** 웹에서 개별 수정 용이, Git diff友好, AI 통합 시 선택적 로드

### 통합 워크플로우
```
[개별 수정] → [저장] → [백업] → [통합 버튼] → [integrated_data.json]
                                              ↓
                                         [AI에게 검토 요청]
```

---

## 2. 구현 완료 항목

| Phase | 목표 | 상태 | 파일 |
|-------|------|------|------|
| Phase 1 | 데이터 분할 및 통합 스크립트 | ✅ | `src/data_integrator.py` |
| Phase 2 | 백업 시스템 | ✅ | `src/backup_manager.py` |
| Phase 3 | Flask API 및 웹 UI | ✅ | `src/routes/edit_labels.py`, `templates/edit_labels.html` |
| Phase 4 | 트레이트 개별 파일화 | ✅ | `data/traits/positive/`, `data/traits/negative/` |

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 개별 라벨/트레이트 수정 | 웹 폼에서 직접 편집 (정의, 가중치, 컨텍스트 등) |
| Macro별 그룹화 | 카테고리별 라벨 분류 표시 |
| 검색 기능 | 라벨 ID, 이름으로 실시간 필터링 |
| 자동 백업 | 수정 전 `data/*/backups/`에 타임스탬프 백업 생성 |
| AI 검토용 통합 | **통합 버튼 클릭 시 `temp/integrated_data.json` 생성** |

---

## 4. API 엔드포인트

### 라벨 API (`/api/edit/labels/...`)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/labels/<type>` | 타입별 라벨 목록 |
| GET | `/labels/<type>/<label_id>` | 개별 라벨 조회 |
| PUT | `/labels/<type>/<label_id>` | 라벨 수정 (자동 백업) |
| POST | `/labels/<type>` | 새 라벨 추가 |
| DELETE | `/labels/<type>/<label_id>` | 라벨 삭제 |
| POST | `/integrate` | 통합 파일 생성 |

### 트레이트 API (`/api/edit/traits/...`)
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/traits` | 전체 트레이트 조회 |
| GET | `/traits/<trait_id>` | 개별 트레이트 조회 |
| PUT | `/traits/<trait_id>` | 트레이트 수정 |
| POST | `/traits` | 새 트레이트 추가 |
| DELETE | `/traits/<trait_id>` | 트레이트 삭제 |

---

## 5. 데이터 마이그레이션 결과

```bash
python -c "from src.data_integrator import split_labels, split_traits; split_labels(); split_traits()"
```

**결과:**
- `data/micro_labels/positive/`: 98개 파일 (M01-01.json ~ M48-01.json)
- `data/micro_labels/negative/`: 80개 파일 (N01-01.json ~ N43-01.json)
- `data/traits/positive/`: 14개 파일 (T01.json ~ T14.json)
- `data/traits/negative/`: 6개 파일 (T101.json ~ T106.json)

---

## 6. 실행 방법

```bash
cd C:\dev\leadership
python app.py
```

- **라벨 수정:** http://localhost:5000/edit/labels
- **트레이트 수정:** http://localhost:5000/edit/traits

---

## 7. 향후 계획

- [ ] Vector DB 자동 재빌드 연동 (라벨 수정 후)
- [ ] AI 피드백 자동 반영 로직
- [ ] 수정 이력 UI (`edit_history.html`)

---

**최종 업데이트:** 2026-05-18 (178개 라벨 반영)
