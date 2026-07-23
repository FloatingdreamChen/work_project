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
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_exam ON positions(exam_year, exam_type);
CREATE INDEX IF NOT EXISTS idx_positions_region ON positions(province, city);
CREATE INDEX IF NOT EXISTS idx_positions_code ON positions(position_code);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

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
