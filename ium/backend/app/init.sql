-- ============================================================
-- 이음(以音) 데이터베이스 초기화 스크립트
-- ============================================================

-- welfare_workers
CREATE TABLE IF NOT EXISTS welfare_workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    region VARCHAR(100),
    email VARCHAR(200),
    -- 관리자 회원 관리 모듈 확장 (0615_02)
    status VARCHAR(20) DEFAULT 'active',  -- active | inactive
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'worker',    -- admin | worker
    note TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type VARCHAR(10) NOT NULL,      -- elder | youth
    nickname VARCHAR(50),
    is_anonymous BOOLEAN DEFAULT FALSE,
    welfare_id UUID REFERENCES welfare_workers(id),
    last_seen_at TIMESTAMP,
    -- 관리자 회원 관리 모듈 확장 (0615_02)
    status VARCHAR(20) DEFAULT 'active',  -- active | dormant | withdrawn
    phone VARCHAR(20),
    email VARCHAR(200),
    name VARCHAR(50),                     -- 실명
    region VARCHAR(100),                  -- 시도/시군구
    note TEXT,                            -- 관리자 메모
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- weekly_topics
CREATE TABLE IF NOT EXISTS weekly_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    media_url TEXT,
    media_type VARCHAR(20),              -- image | audio | video | text
    source VARCHAR(100),
    source_url TEXT,
    ai_question TEXT,
    active_week DATE,
    region VARCHAR(100) DEFAULT 'default',
    welfare_id UUID REFERENCES welfare_workers(id),
    question_type VARCHAR(20) DEFAULT 'narrative',  -- choice | narrative | mixed
    is_customized BOOLEAN DEFAULT FALSE,
    parent_topic_id UUID REFERENCES weekly_topics(id),
    text_content TEXT,
    preview_thumbnail TEXT,
    duration_seconds INTEGER,
    choices TEXT,                        -- JSON 문자열
    created_at TIMESTAMP DEFAULT NOW()
);

-- conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES weekly_topics(id),
    role VARCHAR(10) NOT NULL,           -- user | assistant
    content TEXT NOT NULL,
    emotion_label VARCHAR(20),
    emotion_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- essays
CREATE TABLE IF NOT EXISTS essays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES weekly_topics(id),
    title VARCHAR(200),
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'essay',   -- essay | poem | novel
    contributor_cnt INTEGER DEFAULT 0,
    prompt_version VARCHAR(10) DEFAULT 'v0',
    published_at TIMESTAMP DEFAULT NOW()
);

-- essay_contributors (수필 기여자 중간 테이블)
CREATE TABLE IF NOT EXISTS essay_contributors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    essay_id UUID NOT NULL REFERENCES essays(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(essay_id, user_id)
);

-- safety_alerts
CREATE TABLE IF NOT EXISTS safety_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,     -- no_contact | crisis | emotion_drop
    severity VARCHAR(10),                  -- red | yellow
    note TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- intervention_logs (복지사 개입 이력)
CREATE TABLE IF NOT EXISTS intervention_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    welfare_id UUID REFERENCES welfare_workers(id),
    action_type VARCHAR(50) NOT NULL,    -- phone | visit | counseling | detail | alert_resolve
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- topic_proposals
CREATE TABLE IF NOT EXISTS topic_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welfare_id UUID REFERENCES welfare_workers(id),
    mode VARCHAR(20) NOT NULL,           -- detailed | simple
    welfare_input TEXT,
    ai_suggestions JSONB,
    welfare_selection UUID REFERENCES weekly_topics(id),
    question_type VARCHAR(20),           -- choice | narrative | mixed
    status VARCHAR(20) DEFAULT 'pending', -- pending | approved | rejected
    question_set_json JSONB,
    is_draft BOOLEAN DEFAULT FALSE,
    published_topic_id UUID REFERENCES weekly_topics(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- survey_templates
CREATE TABLE IF NOT EXISTS survey_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welfare_id UUID NOT NULL REFERENCES welfare_workers(id),
    name VARCHAR(100) NOT NULL,
    question_set_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- survey_responses
CREATE TABLE IF NOT EXISTS survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES weekly_topics(id),
    user_id UUID NOT NULL,
    question_id VARCHAR(10) NOT NULL,    -- q1, q2
    question_type VARCHAR(10) NOT NULL,  -- choice | narrative
    selected_option_id VARCHAR(20),
    selected_option_label VARCHAR(100),
    narrative_text TEXT,
    responded_at TIMESTAMP DEFAULT NOW()
);

-- psych_indices (Phase 3 — 심리 지수)
CREATE TABLE IF NOT EXISTS psych_indices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    loneliness SMALLINT NOT NULL,      -- 외로움 0~100
    vitality SMALLINT NOT NULL,        -- 활력 0~100
    cognition SMALLINT NOT NULL,       -- 인지 0~100
    relationship SMALLINT NOT NULL,    -- 관계 0~100
    future SMALLINT NOT NULL,          -- 미래 0~100
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- topic_distributions (배포 이력 + 확인 추적)
CREATE TABLE IF NOT EXISTS topic_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES weekly_topics(id),
    user_id UUID NOT NULL REFERENCES users(id),
    welfare_id UUID REFERENCES welfare_workers(id),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- user_consents (Phase 3 — 동의 이력)
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    agreed BOOLEAN NOT NULL,
    agreed_at TIMESTAMP DEFAULT NOW()
);

-- admin_logs (0615_02 — 관리자 회원/복지사 관리 작업 이력)
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id VARCHAR(50) NOT NULL,       -- 현재 "admin" 고정
    action VARCHAR(50) NOT NULL,         -- create_user | update_user | delete_user | assign_worker | create_worker | update_worker | delete_worker
    target_type VARCHAR(20) NOT NULL,    -- user | worker
    target_id VARCHAR(36) NOT NULL,
    payload TEXT,                        -- JSON 문자열 (변경 전/후)
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── 기존 DB 호환: 컬럼 보강 (이미 존재하면 무시) ──
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS region VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
ALTER TABLE welfare_workers ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE welfare_workers ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE welfare_workers ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'worker';
ALTER TABLE welfare_workers ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE welfare_workers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
ALTER TABLE essays ADD COLUMN IF NOT EXISTS content_type VARCHAR(20) DEFAULT 'essay';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_users_welfare ON users(welfare_id);
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_topic ON conversations(topic_id);
CREATE INDEX IF NOT EXISTS idx_weekly_topics_active_week ON weekly_topics(active_week);
CREATE INDEX IF NOT EXISTS idx_weekly_topics_region ON weekly_topics(region);
CREATE INDEX IF NOT EXISTS idx_safety_alerts_user ON safety_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_safety_alerts_resolved ON safety_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_intervention_logs_user ON intervention_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_essay_contributors_essay ON essay_contributors(essay_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_topic ON survey_responses(topic_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_user ON survey_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_psych_indices_user ON psych_indices(user_id);
CREATE INDEX IF NOT EXISTS idx_psych_indices_user_calc ON psych_indices(user_id, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_topic_distributions_topic ON topic_distributions(topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_distributions_user ON topic_distributions(user_id);
CREATE INDEX IF NOT EXISTS idx_topic_distributions_welfare ON topic_distributions(welfare_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_welfare_workers_status ON welfare_workers(status);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_target ON admin_logs(target_type, target_id);
