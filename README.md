# EduVesp

Sistema web de comunicação escolar entre pais, professores e alunos.

Projeto Integrador PJI110 – Grupo 14 – UNIVESP 2026.

## Sobre

O EduVesp permite que professores publiquem comunicados e que pais respondam com comentários, tudo em um ambiente simples e centralizado.

## Tecnologias

- Python 3 + Flask
- SQLite (via Flask-SQLAlchemy)
- Bootstrap 5

## Como rodar

```bash
uv sync
uv run python app.py
```

Acesse em `http://127.0.0.1:5000`.

## Perfis de usuário

| Perfil     | Criar comunicado | Comentar |
|------------|:---:|:---:|
| Professor  | Sim | Não |
| Pai        | Não | Sim |
| Aluno      | Não | Não |
