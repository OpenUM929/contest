CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS welfare_workers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(50)  NOT NULL,
    region      VARCHAR(100),
    email       VARCHAR(200),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type    VARCHAR(10)  NOT NULL CHECK (user_type IN ('elder', 'youth')),
    nickname     VARCHAR(50),
    is_anonymous BOOLEAN DEFAULT FALSE,
    welfare_id   UUID REFERENCES welfare_workers(id),
    last_seen_at TIMESTAMP,
    created_at   TIMESTAMP DEFAULT NOW()
);

-- 마이그레이션: 기존 weekly_topics 테이블 구조 변경
DO $$
BEGIN
    -- media_type CHECK 제약 확장 (text 추가)
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'weekly_topics_media_type_check' 
               AND table_name = 'weekly_topics') THEN
        ALTER TABLE weekly_topics DROP CONSTRAINT weekly_topics_media_type_check;
    END IF;
    
    -- active_week UNIQUE 제약을 복합 유니크로 변경
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'weekly_topics_active_week_key' 
               AND table_name = 'weekly_topics') THEN
        ALTER TABLE weekly_topics DROP CONSTRAINT weekly_topics_active_week_key;
        ALTER TABLE weekly_topics ADD CONSTRAINT unique_week_region UNIQUE (active_week, region);
    END IF;
END $$;

-- 새로운 weekly_topics 테이블 (처음 생성 시)
CREATE TABLE IF NOT EXISTS weekly_topics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    media_url       TEXT,
    media_type      VARCHAR(20)  CHECK (media_type IN ('image', 'audio', 'video', 'text')),
    source          VARCHAR(100),
    source_url      TEXT,
    ai_question     TEXT,
    active_week     DATE NOT NULL,
    region          VARCHAR(100) DEFAULT 'default',
    welfare_id      UUID REFERENCES welfare_workers(id),
    question_type   VARCHAR(20) DEFAULT 'narrative',
    is_customized   BOOLEAN DEFAULT FALSE,
    parent_topic_id UUID REFERENCES weekly_topics(id),
    text_content    TEXT,
    preview_thumbnail TEXT,
    duration_seconds INT,
    choices         TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_week_region UNIQUE (active_week, region)
);

CREATE TABLE IF NOT EXISTS conversations (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    topic_id      UUID REFERENCES weekly_topics(id),
    role          VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    emotion_label VARCHAR(20),
    emotion_score FLOAT,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS essays (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id        UUID REFERENCES weekly_topics(id),
    title           VARCHAR(200),
    content         TEXT NOT NULL,
    content_type    VARCHAR(20) DEFAULT 'essay',   -- essay | poem | novel
    contributor_cnt INTEGER DEFAULT 0,
    prompt_version  VARCHAR(10) DEFAULT 'v0',
    published_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS safety_alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    alert_type  VARCHAR(50) NOT NULL,
    severity    VARCHAR(10) CHECK (severity IN ('red', 'yellow')),
    note        TEXT,
    resolved    BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- topic_proposals 테이블 (관리자-AI 협의 이력)
CREATE TABLE IF NOT EXISTS topic_proposals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welfare_id      UUID REFERENCES welfare_workers(id),
    mode            VARCHAR(20) NOT NULL,  -- 'detailed' | 'simple'
    welfare_input   TEXT,                   -- 관리자 의도/선택 내용
    ai_suggestions  JSONB,                    -- AI 제안 후보 목록
    welfare_selection UUID REFERENCES weekly_topics(id), -- 최종 선택
    question_type   VARCHAR(20),            -- 'choice' | 'narrative' | 'mixed'
    status          VARCHAR(20) DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
    question_set_json JSONB,                -- 복지사가 편집한 QuestionSet 전체
    is_draft        BOOLEAN DEFAULT FALSE,  -- 임시 저장 여부
    published_topic_id UUID REFERENCES weekly_topics(id), -- 발행된 주제 연결
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 설문지 템플릿 (복지사가 자주 쓰는 질문 패턴 저장)
CREATE TABLE IF NOT EXISTS survey_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welfare_id      UUID REFERENCES welfare_workers(id) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    question_set_json JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 설문 응답 (집계/분석용 — conversations과 분리)
CREATE TABLE IF NOT EXISTS survey_responses (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id              UUID REFERENCES weekly_topics(id) NOT NULL,
    user_id               UUID NOT NULL,
    question_id           VARCHAR(10) NOT NULL,        -- 'q1', 'q2'
    question_type         VARCHAR(10) NOT NULL,        -- 'choice' | 'narrative'
    selected_option_id    VARCHAR(20),                 -- 'opt_1', 'opt_other'
    selected_option_label VARCHAR(100),                -- 보기 문구 스냅샷
    narrative_text        TEXT,                        -- 서술형 답변 (STT 결과 또는 텍스트)
    responded_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE (topic_id, user_id, question_id)
);

-- 보기별 집계 쿼리용 인덱스
CREATE INDEX IF NOT EXISTS idx_survey_resp_topic  ON survey_responses(topic_id);
CREATE INDEX IF NOT EXISTS idx_survey_resp_option ON survey_responses(topic_id, question_id, selected_option_id);

-- 샘플 복지사 데이터
INSERT INTO welfare_workers (name, region, email)
VALUES ('김복지', '서울 종로구', 'welfare1@ium.kr')
ON CONFLICT DO NOTHING;
