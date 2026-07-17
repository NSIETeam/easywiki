# OrgMind v2.1 — Organizational Memory System

## Quick Start (Windows)
1. Double-click `scripts\start_app.bat`
2. Browser opens at http://localhost:8080
3. Login with admin@local / orgmind2026

## Requirements
- Python 3.10+ installed (https://python.org)
- Internet connection (first run installs dependencies)

## Accounts
| Email | Role | Password |
|------|------|---------|
| admin@local | admin (all departments) | orgmind2026 |
| tech@local | manager (tech dept) | orgmind2026 |
| dev@local | employee (frontend) | orgmind2026 |
| backend@local | employee (backend) | orgmind2026 |
| market@local | manager (marketing) | orgmind2026 |

## Features
- Zero Docker / PostgreSQL — SQLite + Python, runs anywhere
- Real semantic search (sentence-transformers embedding)
- Auto memory extraction from AI conversations (LLM + rules)
- Role-based access: admin sees all, manager sees dept+children, employee sees own dept
- Invite codes for team onboarding
- Audit logs, data export, memory edit/delete
- SPA frontend with bilingual Chinese/English toggle
