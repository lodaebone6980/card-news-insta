-- 카드뉴스 자동생성기 전용 테이블

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS cn_users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  created_at TIMESTAMPTZ DEFAULT now(),
  last_login_at TIMESTAMPTZ
);

-- 2. 접속 기록 테이블
CREATE TABLE IF NOT EXISTS cn_access_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES cn_users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. 카드뉴스 히스토리 테이블
CREATE TABLE IF NOT EXISTS cn_card_history (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES cn_users(id) ON DELETE SET NULL,
  session_name TEXT NOT NULL,
  category TEXT,
  topic TEXT,
  slides_count INT,
  slides_data JSONB,
  png_urls TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_cn_access_logs_user ON cn_access_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cn_card_history_user ON cn_card_history(user_id, created_at DESC);
