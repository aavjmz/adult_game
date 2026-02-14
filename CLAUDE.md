# CLAUDE.md

This file provides guidance for AI assistants working on this codebase.

## Project Overview

A web-based collectible card game (CCG) with a Three Kingdoms (三国) theme. Players collect hero cards, level them up, equip gear, and battle through PVE stages and PVP arenas.

- **Backend:** Python 3.12, Flask 3.0.0
- **Database:** SQLite (default), PostgreSQL supported
- **ORM:** Flask-SQLAlchemy 3.1.1
- **Auth:** Flask-Login 0.6.3
- **Real-time:** Flask-SocketIO 5.3.6 (for battle systems)
- **Frontend:** HTML5 + CSS3 + vanilla JavaScript (no frontend build step)
- **Deployment:** Docker + Docker Compose

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize/migrate database (run in order)
python migrate_complete.py
python init_stages.py
python init_equipment_data.py
python init_enemy_cards.py

# Run the app (default: http://localhost:8080)
python run.py

# Or via Docker
docker-compose up
```

The default port is **8080** (not 5000). Set `FLASK_PORT` and `FLASK_HOST` env vars to change.

## Repository Structure

```
adult_game/
├── app/                        # Main application package
│   ├── __init__.py             # Flask app factory (create_app), blueprint registration
│   ├── models.py               # All SQLAlchemy models (User, Card, Equipment, Stage, etc.)
│   ├── battle_engine.py        # Enhanced battle engine v2 (speed-based, elemental)
│   ├── growth_utils.py         # Growth system calculations (leveling, starring)
│   ├── equipment_utils.py      # Equipment stat calculations
│   ├── routes/                 # Flask blueprints (one per feature)
│   │   ├── auth.py             # /register, /login, /logout
│   │   ├── main.py             # /, /dashboard, /api/user/info
│   │   ├── gacha.py            # /gacha, /pull (card pulling)
│   │   ├── cards.py            # /cards, /api/all (collection)
│   │   ├── battle.py           # /battle (basic PVP)
│   │   ├── battle_v2.py        # /battle2/* (enhanced Three Kingdoms battles)
│   │   ├── growth.py           # /growth/* (leveling, starring, skills — 10 endpoints)
│   │   ├── equipment.py        # /equipment/* (enhance, craft, dismantle, sets)
│   │   ├── pve.py              # /api/pve/* (PVE stage API)
│   │   └── pve_frontend.py     # /pve/* (PVE UI pages)
│   ├── game/                   # Game logic modules
│   │   ├── match_queue.py      # PvP matching queue
│   │   └── room_manager.py     # Battle room management
│   ├── utils/                  # Utility modules
│   │   ├── stamina.py          # Stamina/energy system
│   │   └── pve_battle.py       # PVE battle engine (~300 lines)
│   ├── templates/              # Jinja2 HTML templates (27 files)
│   │   ├── base.html           # Base layout
│   │   └── pve/                # PVE-specific templates (10 files)
│   └── static/                 # CSS, JS, images, PWA assets
│       ├── css/style.css
│       ├── js/main.js
│       ├── images/cards/       # Card artwork (PNG)
│       ├── manifest.json       # PWA manifest
│       └── service-worker.js   # PWA service worker
├── config.py                   # Config class (rarity rates, gacha settings, resources)
├── run.py                      # App entry point
├── requirements.txt            # Python dependencies (10 packages)
├── Dockerfile                  # Python 3.12-slim container
├── docker-compose.yml          # Single-service orchestration (port 8080)
├── entrypoint.sh               # Docker startup (auto-initializes DB)
├── migrate_complete.py         # Full DB migration script
├── migrate_pve_system.py       # PVE tables migration
├── migrate_three_kingdoms.py   # Three Kingdoms theme migration
├── migrate_equipment_system.py # Equipment tables migration
├── migrate_growth_system.py    # Growth tables migration
├── init_stages.py              # Seed 30 PVE stages
├── init_equipment_data.py      # Seed 30+ equipment templates
├── init_enemy_cards.py         # Seed enemy card configs
├── test_*.py                   # Test files (7 total, in root)
└── docs/                       # Additional design documents
```

## Architecture

### App Factory Pattern

The app is created via `create_app()` in `app/__init__.py`. It initializes extensions (db, login_manager), registers all blueprints, creates tables, and seeds initial card data if the database is empty.

### Blueprints

Each game feature lives in its own blueprint under `app/routes/`. Blueprints are registered with URL prefixes in `__init__.py`. When adding a new feature, create a new blueprint file and register it in `create_app()`.

### Database Models

All models are in `app/models.py`. Key models:

| Model | Purpose |
|-------|---------|
| `User` | Accounts, resources (tickets, coins, gems), PVE stats |
| `Card` | Card templates — 23 attributes (stats, element, faction, job, skills) |
| `UserCard` | Player-owned cards (level, exp, stars, awaken, breakthrough) |
| `GachaRecord` | Pull history |
| `Equipment` | Equipment instances with enhancement level |
| `EquipmentTemplate` | Base equipment definitions |
| `EquipmentStat` | Random stat rolls on equipment |
| `EquipmentSet` | Set bonus configs (2-piece, 4-piece) |
| `UserItem` | Inventory items (materials, potions, books) |
| `Stage` | PVE stage definitions (30 stages, 3 chapters) |
| `UserStageProgress` | Player progress per stage (stars, clears) |
| `BattleRecord` | PVE battle logs |

### Game Systems

- **Card system:** 14 Three Kingdoms hero cards across 5 rarities (N/R/SR/SSR/UR). Cards have elements (金木水火土), factions (魏蜀吴群), and job classes.
- **Gacha:** Single/multi pull with pity system (SR at 10, SSR at 90). Rates: N 50%, R 30%, SR 15%, SSR 4.5%, UR 0.5%.
- **Battle v2:** Speed-based turn order, Five Element counter system (金→木→土→水→火→金), crit mechanics, skill cooldowns, buff/debuff, 30-round cap.
- **Growth:** Leveling (1-100), starring (1-5 stars), skill upgrades, awakening, breakthrough. Logic in `growth_utils.py`.
- **Equipment:** Weapon/Armor/Accessory/Treasure with 5 quality tiers. Enhancement (+0 to +30), crafting, set bonuses, exclusive hero equipment.
- **PVE:** 30 stages across 3 chapters with stamina system (auto-recovery: 1 per 6 min, max 120). AI strategies: balanced, aggressive, defensive. Star rating (1-3).
- **PWA:** Full Progressive Web App support with service worker caching and install-to-home-screen.

## Running Tests

Tests are standalone Python scripts in the project root. No test framework (pytest/unittest) is configured — each file runs directly:

```bash
python test_pve_system.py
python test_battle_system.py
python test_battle_v2.py
python test_equipment_system.py
python test_growth_system.py
python test_three_kingdoms_battle.py
python test_battle_debug.py
```

Tests validate database structure, card initialization, battle calculations, equipment functions, and growth formulas.

## Database Migrations

There is no Alembic/Flask-Migrate setup. Migrations are manual Python scripts:

1. `migrate_complete.py` — Primary migration (creates tables, seeds 14 cards, adds columns)
2. `migrate_three_kingdoms.py` — Adds Three Kingdoms-specific fields
3. `migrate_pve_system.py` — Creates PVE tables
4. `migrate_equipment_system.py` — Creates equipment tables
5. `migrate_growth_system.py` — Creates growth-related columns

Run `migrate_complete.py` first for a fresh setup. The Docker entrypoint runs it automatically.

When modifying models, update the relevant migration script or create a new one. The app also calls `db.create_all()` on startup, which creates missing tables (but does not alter existing ones).

## Key Conventions

### Code Style
- **Python:** snake_case for functions/variables, PascalCase for classes
- **Routes:** `/feature/action` URL pattern
- **Comments:** Chinese (中文) for game-specific logic, English acceptable for technical comments
- **Docstrings:** Present on most functions and classes

### Configuration
- Game balance constants live in `config.py` (rarity rates, gacha costs, initial resources)
- Database path controlled by `DB_PATH` or `DATABASE_URL` env vars
- Flask settings via `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG` env vars

### Frontend
- Vanilla JavaScript (no React/Vue/bundler)
- Templates use Jinja2 with `base.html` as the layout
- Static files in `app/static/` — no build step needed
- Card images in `app/static/images/cards/`

### Database
- SQLite for development/single-instance deployment
- All models in a single `models.py` file
- Foreign keys with cascading deletes
- Timestamps via `created_at`/`updated_at` fields
- `db.create_all()` runs on every app start

### Adding a New Feature
1. Define models in `app/models.py`
2. Create a blueprint in `app/routes/new_feature.py`
3. Register the blueprint in `app/__init__.py` `create_app()`
4. Add templates in `app/templates/`
5. Write a migration script if altering existing tables
6. Add a test file as `test_new_feature.py`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Server bind address |
| `FLASK_PORT` | `8080` | Server port |
| `FLASK_DEBUG` | `False` | Debug mode |
| `SECRET_KEY` | `dev-secret-key-...` | Flask secret key |
| `DATABASE_URL` | SQLite at `data/game.db` | Database connection URI |
| `DB_PATH` | `<project>/data/game.db` | SQLite file path |

## Docker Deployment

```bash
docker-compose up          # Build and run
docker-compose up -d       # Detached mode
docker-compose down        # Stop
```

- Port mapping: host 8080 -> container 8080
- Database persisted in `game_data` Docker volume at `/app/data/`
- `entrypoint.sh` auto-runs `migrate_complete.py` if no database found

## Project Status

The game is approximately 40% complete. Fully implemented: auth, card collection, gacha, PWA. Partially implemented: battle systems, growth, equipment, PVE. Not yet started: PvP matchmaking, guilds, friends, leaderboards, real-time multiplayer.

Refer to `PROJECT_STATUS.md` for detailed progress and `TODO.md` for the development roadmap.
