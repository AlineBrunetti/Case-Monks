import pandas as pd
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os
import time

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mydb")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users_csv_path = "/app/data/users.csv"

def hash_passwords_and_insert():
    print("Iniciando a importação de usuários...")

    # Espera o banco de dados estar pronto
    for i in range(5):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                print("Conexão com o banco de dados estabelecida!")
            break
        except Exception as e:
            print(f"Tentativa {i+1} de conexão com o DB falhou. Esperando 2 segundos...")
            time.sleep(2)
    else:
        print("Não foi possível conectar ao banco de dados.")
        return

    try:
        if not os.path.exists(users_csv_path):
            print(f"Erro: Arquivo {users_csv_path} não encontrado.")
            return

        df = pd.read_csv(users_csv_path)

        # Criptografa as senhas
        df['password_hash'] = df['password'].apply(lambda p: pwd_context.hash(p))
        df = df.drop(columns=['password'])

        with engine.connect() as conn:
            with conn.begin() as transaction:
                # Limpa a tabela antes de inserir
                conn.execute(text("TRUNCATE TABLE users CASCADE"))
                
                # Insere os usuários hasheadas
                for _, row in df.iterrows():
                    conn.execute(text("INSERT INTO users (email, password_hash, role) VALUES (:email, :password_hash, :role)"),
                                 {"email": row['email'], "password_hash": row['password_hash'], "role": row['role']})
            
        print("Usuários importados e senhas hasheadas com sucesso!")

    except Exception as e:
        print(f"Erro durante a importação de usuários: {e}")

if __name__ == "__main__":
    hash_passwords_and_insert()