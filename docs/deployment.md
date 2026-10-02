\# Backend Deployment



VoltNest uses Docker Compose for the local containerized backend environment.



\## Services



\- `postgres` — PostgreSQL 18 with pgvector

\- `backend` — FastAPI + LangGraph application



\## Fresh Environment Setup



Start PostgreSQL:



```powershell

docker compose up -d postgres

