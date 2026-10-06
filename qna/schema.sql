-- 묻고 답하기 게시판 (2026-10-06). 개인정보 칸 없음: 닉네임·비밀번호 해시·글뿐.
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nick TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  pw_hash TEXT NOT NULL,      -- PBKDF2-SHA256, 원문 비밀번호는 저장하지 않는다
  pw_salt TEXT NOT NULL,
  created INTEGER NOT NULL,   -- ms
  updated INTEGER,
  answer TEXT,
  answered INTEGER,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS posts_list ON posts (hidden, id);
-- 도배·비밀번호 맞히기 막기용. k = 종류:HMAC(IP+날짜) 앞 16글자. 2일 뒤 지운다(IP 원문 없음)
CREATE TABLE IF NOT EXISTS hits (k TEXT NOT NULL, ts INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS hits_k ON hits (k, ts);
