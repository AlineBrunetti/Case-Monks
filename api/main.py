from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import pandas as pd
import time
from typing import List, Dict, Any, Optional

# --- Configurações ---
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Inicialização da Aplicação ---
app = FastAPI(title="Case de Desempenho de Marketing Digital")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Conexão com o Banco de Dados ---
for i in range(5):
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Conexão com o banco de dados estabelecida!")
        break
    except Exception as e:
        print(f"Tentativa {i+1} de conexão falhou. Esperando 2 segundos...")
        time.sleep(2)
else:
    raise Exception("Não foi possível conectar ao banco de dados.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Autenticação e Segurança ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

# --- Rota de Login ---
@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user_row = db.execute(text("SELECT email, password_hash, role FROM users WHERE email = :email"), {"email": form_data.username}).fetchone()
    if not user_row or not verify_password(form_data.password, user_row.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_access_token({"sub": user_row.email, "role": user_row.role})
    return {"access_token": token, "token_type": "bearer", "role": user_row.role}

# --- Rota de Métricas ---
@app.get("/metrics")
def get_metrics(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    sort: Optional[str] = None,
    order: str = "desc",
    page: int = 1,
    page_size: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    base_query_select = "SELECT account_id, campaign_id, clicks, conversions, impressions, interactions, date"
    if current_user['role'] == 'admin':
        base_query_select += ", cost_micros"
    
    base_query_from = " FROM metrics WHERE 1=1"
    
    params = {}
    if start_date:
        base_query_from += " AND date >= :start_date"
        params['start_date'] = start_date
    if end_date:
        base_query_from += " AND date <= :end_date"
        params['end_date'] = end_date

    # --- Ordenação e Paginação ---
    allowed_sort = {"account_id", "campaign_id", "clicks", "conversions", "impressions", "interactions", "date", "cost_micros"}
    
    order_by_clause = ""
    if sort and sort in allowed_sort:
        order_direction = "ASC" if order.lower() == 'asc' else "DESC"
        order_by_clause = f" ORDER BY {sort} {order_direction}"
    else:
        order_by_clause = " ORDER BY date DESC"

    # Total de itens para a paginação
    count_query = text(f"SELECT COUNT(*) {base_query_from}")
    total_items = db.execute(count_query, params).scalar()

    # Query principal com paginação
    offset = (page - 1) * page_size
    main_query = text(f"{base_query_select} {base_query_from} {order_by_clause} LIMIT :limit OFFSET :offset")
    
    params['limit'] = page_size
    params['offset'] = offset

    rows = db.execute(main_query, params).mappings().fetchall()
    
    # Converte os resultados para um formato JSON amigável
    result = [dict(r) for r in rows]
    
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "data": result
    }

# --- Funções para Ingestão de Dados (Opcional, mas útil para o case) ---
def setup_db_and_import_data():
    db = SessionLocal()
    
    print("Verificando/Criando tabelas...")
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin','user')),
                created_at TIMESTAMP DEFAULT now()
            );
        """))
        db.execute(text("""
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
        """))
        db.commit()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        db.rollback()

    print("Importando dados de usuários...")
    users_csv_path = "/app/data/users.csv"
    if os.path.exists(users_csv_path):
        df_users = pd.read_csv(users_csv_path)
        
        # Hash das senhas
        df_users['password'] = df_users['password'].apply(lambda p: pwd_context.hash(p))
        df_users = df_users.drop(columns=['password'])
        
        for _, row in df_users.iterrows():
            try:
                db.execute(text("INSERT INTO users (email, password, role) VALUES (:email, :password, :role) ON CONFLICT (email) DO NOTHING"),
                           {"email": row['email'], "password": row['password'], "role": row['role']})
            except Exception as e:
                print(f"Erro ao importar usuário {row['email']}: {e}")
        db.commit()
        print("Usuários importados com sucesso.")
    else:
        print(f"Arquivo {users_csv_path} não encontrado.")

    print("Importando dados de métricas (via COPY)...")
    try:
        # Nota: O COPY FROM precisa que o arquivo esteja acessível ao servidor Postgres.
        # No nosso setup, o container 'db' tem acesso à pasta 'data' do host via volume.
        # Mas para o COPY o caminho é relativo ao container db.
        # Se o script está sendo executado no container API, ele não pode rodar o COPY
        # no servidor Postgres diretamente, então essa parte precisa ser feita manualmente
        # ou com um script separado. Vamos deixar a instrução para o README.
        print("Por favor, execute o comando de importação de métricas manualmente no container do banco de dados, conforme o README.md.")
    except Exception as e:
        print(f"Erro ao importar métricas: {e}")
        db.rollback()

@app.on_event("startup")
def on_startup():
    setup_db_and_import_data()