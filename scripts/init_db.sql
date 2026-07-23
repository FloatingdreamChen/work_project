CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(80) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    target_exam VARCHAR(80),
    target_region VARCHAR(120),
    education VARCHAR(80),
    degree VARCHAR(80),
    major VARCHAR(160),
    graduation_year INTEGER,
    fresh_graduate_status VARCHAR(80),
    political_status VARCHAR(80),
    household_region VARCHAR(120),
    grassroots_experience TEXT,
    work_years NUMERIC(4, 1),
    certificates TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_year INTEGER NOT NULL,
    exam_type VARCHAR(80) NOT NULL,
    province VARCHAR(120),
    city VARCHAR(120),
    department VARCHAR(255),
    bureau VARCHAR(255),
    position_name VARCHAR(255) NOT NULL,
    position_code VARCHAR(120),
    recruitment_count INTEGER,
    applicant_count INTEGER,
    competition_ratio NUMERIC(8, 2),
    previous_min_score NUMERIC(6, 2),
    education_requirement TEXT,
    degree_requirement TEXT,
    major_requirement TEXT,
    political_requirement TEXT,
    grassroots_requirement TEXT,
    work_years_requirement TEXT,
    household_requirement TEXT,
    remarks TEXT,
    source_name VARCHAR(255),
    source_url TEXT,
    source_published_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_exam ON positions(exam_year, exam_type);
CREATE INDEX IF NOT EXISTS idx_positions_region ON positions(province, city);
CREATE INDEX IF NOT EXISTS idx_positions_code ON positions(position_code);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

CREATE TABLE IF NOT EXISTS position_import_audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255),
    file_path TEXT,
    total_rows INTEGER NOT NULL DEFAULT 0,
    imported_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS position_match_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_snapshot JSONB NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_type VARCHAR(80) NOT NULL,
    topic VARCHAR(255),
    user_answer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS practice_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    score NUMERIC(5, 2),
    strengths TEXT,
    problems TEXT,
    improved_answer TEXT,
    next_steps TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wrong_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES practice_sessions(id) ON DELETE CASCADE,
    practice_type VARCHAR(80) NOT NULL,
    module_name VARCHAR(120),
    topic VARCHAR(255),
    question TEXT,
    user_answer TEXT,
    error_reason TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS practice_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES practice_sessions(id) ON DELETE CASCADE,
    practice_type VARCHAR(80) NOT NULL,
    module_name VARCHAR(120),
    accuracy NUMERIC(5, 2),
    duration_minutes NUMERIC(6, 2),
    question_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS essay_dimension_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    reading_score NUMERIC(5, 2),
    structure_score NUMERIC(5, 2),
    argument_score NUMERIC(5, 2),
    expression_score NUMERIC(5, 2),
    policy_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_position VARCHAR(255),
    stage VARCHAR(80) NOT NULL DEFAULT 'warmup',
    turns JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wrong_questions_user_status ON wrong_questions(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_practice_metrics_user_module ON practice_metrics(user_id, module_name, created_at DESC);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL,
    source_path TEXT,
    source_url TEXT,
    source_type VARCHAR(80) NOT NULL DEFAULT 'local',
    published_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version VARCHAR(80) NOT NULL DEFAULT 'v1',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id VARCHAR(64) PRIMARY KEY,
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    token_count INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_imported ON knowledge_documents(imported_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id, chunk_index);

CREATE TABLE IF NOT EXISTS current_information_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(80) NOT NULL DEFAULT 'web',
    provider VARCHAR(80),
    query TEXT,
    title TEXT,
    url TEXT NOT NULL,
    domain VARCHAR(255),
    published_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    credibility VARCHAR(40),
    credibility_score INTEGER,
    credibility_reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_current_sources_url ON current_information_sources(url);
CREATE INDEX IF NOT EXISTS idx_current_sources_imported ON current_information_sources(imported_at DESC);
CREATE INDEX IF NOT EXISTS idx_current_sources_published ON current_information_sources(published_at DESC);
