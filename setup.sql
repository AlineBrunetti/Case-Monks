DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS metrics CASCADE;

-- Comando para criar a tabela de usuários
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin','user')),
  created_at TIMESTAMP DEFAULT now()
);

-- Comando para criar a tabela de métricas
CREATE TABLE IF NOT EXISTS metrics (
  id BIGSERIAL PRIMARY KEY,
  account_id BIGINT NOT NULL,
  campaign_id BIGINT NOT NULL,
  cost_micros NUMERIC NOT NULL,
  clicks NUMERIC,
  conversions NUMERIC,
  impressions NUMERIC,
  interactions NUMERIC,
  date DATE NOT NULL
);

-- Comando para copiar os dados da tabela de métricas
COPY metrics(account_id, campaign_id, cost_micros, clicks, conversions, impressions, interactions, date)
FROM '/app/data/metrics.csv'
CSV HEADER;

-- Comando para criar a tabela de usuários a partir do CSV
COPY users(email, password_hash, role)
FROM '/app/data/users.csv'
CSV HEADER;

-- (Opcional) Adicione os índices para otimizar as consultas
CREATE INDEX idx_metrics_date ON metrics(date);
CREATE INDEX idx_metrics_account ON metrics(account_id);
CREATE INDEX idx_metrics_date_account ON metrics(date, account_id);