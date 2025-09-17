# Case: Dashboard de Marketing Digital

Este projeto consiste em uma aplicação web para gestores de marketing digital, onde são exibidos dados de performance extraídos de uma plataforma. A aplicação é composta por um back-end (API em Python) e um front-end (HTML, CSS e JavaScript).

## Arquitetura da Solução

-   **Backend:** Desenvolvido em Python com o framework **FastAPI**. Ele é responsável por expor os dados via API REST.
-   **Banco de Dados:** Utiliza **PostgreSQL** para persistência dos dados de performance e usuários.
-   **Frontend:** Construído com **HTML, CSS e JavaScript** puros para demonstrar a integração completa com a API.
-   **Orquestração:** Todo o ambiente é gerenciado com **Docker Compose**, garantindo que a aplicação seja executada de forma consistente em qualquer máquina.

## Requisitos para Execução

Para rodar o projeto, é necessário ter o **Docker** e o **Docker Compose** instalados.

## Como Executar

Siga os passos abaixo para subir a aplicação:

1.  **Clone o Repositório:**

    ```bash
    git clone [https://www.youtube.com/watch?v=GRf6so_sois](https://www.youtube.com/watch?v=GRf6so_sois)
    cd [nome-da-pasta]
    ```

2.  **Subir o Ambiente Docker:**
    No diretório raiz do projeto, execute o comando para construir as imagens e iniciar os serviços em segundo plano.

    ```bash
    docker compose up --build -d
    ```

3.  **Configurar o Banco de Dados:**
    Após o ambiente estar de pé, execute os scripts de setup e ingestão de dados.

    ```bash
    # Cria as tabelas e importa os dados de métricas e usuários
    docker exec -it case_db psql -U postgres -d mydb -f /setup.sql

    # Hasheia as senhas e popula a tabela de usuários
    docker exec -it case_api python /app/ingest_users.py
    ```

4.  **Acessar a Aplicação:**
    -   **Frontend:** Abra o navegador e acesse `http://localhost:8080`.
    -   **API (Docs):** A documentação interativa da sua API está disponível em `http://localhost:8000/docs`.

## Credenciais de Acesso

Use as seguintes credenciais para testar o login:

-   **Usuário Administrador:**
    -   **Email:** `user1@email.com`
    -   **Senha:** `oeiruhn56146`
-   **Usuário Padrão:**
    -   **Email:** `user2@email.com`
    -   **Senha:** `908ijofff`

## Funcionalidades Implementadas

-   Sistema de login com autenticação por e-mail e senha.
-   Tabela de dados com paginação e ordenação por colunas.
-   Filtro de dados por intervalo de datas.
-   A coluna "cost_micros" é exibida apenas para usuários com o papel "admin".
-   Feedback visual de erros e sucesso para o usuário (pop-ups).
-   Botões de logout e de limpeza de filtros.