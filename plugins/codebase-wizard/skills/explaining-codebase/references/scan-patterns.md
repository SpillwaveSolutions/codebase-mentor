# Scan Patterns Reference

Heuristics for Phase 1 repo scanning. Read this when first loading a repo.

---

## Entry Point Detection by Language

### JavaScript / TypeScript
- Primary: `index.js`, `index.ts`, `server.js`, `server.ts`, `app.js`, `app.ts`
- Framework-specific:
  - Express/Fastify: look for `app.listen(` or `server.listen(`
  - Next.js: `pages/_app.tsx`, `app/layout.tsx`
  - NestJS: `main.ts` with `NestFactory.create(`
- Fallback: `"main"` field in `package.json`

### Python
- Primary: `main.py`, `app.py`, `run.py`, `manage.py` (Django), `wsgi.py`, `asgi.py`
- Framework-specific:
  - FastAPI/Flask: look for `app = FastAPI()` or `app = Flask(__name__)`
  - Django: `manage.py` + `urls.py`
- Fallback: `[tool.poetry.scripts]` in `pyproject.toml` or `console_scripts` in `setup.py`

### Go
- Primary: `main.go` (file with `func main()`)
- Look for `cmd/` directory pattern: `cmd/server/main.go`

### Java / Kotlin
- Primary: `Main.java`, `Application.java`, class with `public static void main`
- Spring Boot: `@SpringBootApplication` annotation

### Ruby
- Primary: `config.ru`, `app.rb`, `server.rb`
- Rails: `config/application.rb`, `config/routes.rb`

### If no entry point found
> "I can't find a clear entry point - can you point me at the main file?
> Or tell me the framework and I'll look in the right place."

---

## Folder Role Identification

| Folder | Likely role | What to look for inside |
|--------|-------------|--------------------------|
| `routes/` or `routers/` | HTTP route definitions | `app.get(`, `router.post(`, `@app.route` |
| `controllers/` or `handlers/` | Business logic for routes | Functions called by routes |
| `middleware/` | Request interceptors | Auth checks, logging, rate limiting |
| `models/` or `schemas/` | Data shape definitions | DB schema, ORM models, Pydantic/Zod |
| `services/` | Reusable business logic | Functions called by controllers |
| `auth/` | Authentication logic | JWT, session, OAuth handlers |
| `db/` or `database/` | DB connection + queries | Connection pool, migrations |
| `config/` | App configuration | Env loading, constants, feature flags |
| `utils/` or `helpers/` | Shared utility functions | Date formatting, string helpers |
| `lib/` | Internal libraries | Reusable modules not tied to a route |
| `hooks/` | React hooks or lifecycle hooks | Custom `use*` functions |
| `components/` | UI components | React/Vue/Svelte components |
| `tests/` or `__tests__/` | Test files | Skip unless user asks about testing |

---

## Auth Detection

Look for these patterns to identify the auth system:

### JWT
- `jwt.sign(`, `jwt.verify(`, `jsonwebtoken`, `jose`, `PyJWT`
- Note the secret source: `process.env.JWT_SECRET`, `settings.SECRET_KEY`

### Session-based
- `express-session`, `connect-pg-simple`, `flask.session`
- Cookie names, session store config

### OAuth / SSO
- `passport.js`, `authlib`, `next-auth`, `Auth0`, `Clerk`, `Supabase Auth`
- Look for callback routes: `/auth/callback`, `/oauth/redirect`

### API Keys
- Header checks: `x-api-key`, `Authorization: Bearer`
- Key validation against DB or env

### When you find auth, note:
1. Where tokens/sessions are created (signup/login route)
2. Where they are verified (middleware)
3. What they protect (which routes use the middleware)

---

## DB / Data Layer Detection

| Pattern | What it means |
|---------|---------------|
| `mongoose.connect(` | MongoDB via Mongoose |
| `new PrismaClient()` | Prisma ORM (check `schema.prisma`) |
| `sequelize` | Sequelize ORM (MySQL/Postgres) |
| `knex(` | Knex query builder |
| `Pool(` from `pg` | Raw Postgres |
| `sqlite3` | SQLite (likely local dev) |
| `redis.createClient(` | Redis (caching or sessions) |
| `dynamodb` | AWS DynamoDB |
| `firestore` | Firebase Firestore |
| `sqlalchemy` | Python SQLAlchemy ORM |
| `django.db` | Django ORM |

---

## Docs Detection

| Pattern | What to do |
|---------|-----------|
| `README.md` exists | Check for setup steps, API docs, tutorial sections |
| `/docs/` folder | List `.md` files, note any named `tutorial`, `guide`, `quickstart` |
| `CONTRIBUTING.md` | Note for developer workflow questions |
| Inline `// TODO` or `// NOTE` comments | Surface these as interesting points |
| Swagger/OpenAPI (`swagger.json`, `openapi.yaml`) | Offer to walk through API surface |

---

## Monorepo Handling

Signs of a monorepo:
- `packages/` or `apps/` folder at root
- `lerna.json`, `pnpm-workspace.yaml`, `nx.json`, `turborepo.json`
- Multiple `package.json` / `pyproject.toml` files in subfolders

Response:
> "This looks like a monorepo with multiple packages. Which one do you want
> to explore? I can see: `packages/api`, `packages/web`, `packages/shared`."

---

## Mixed Stack Handling

If you see both Python and JS/TS files:
- Check if it's a full-stack app (separate frontend/backend) or scripts
- Common pattern: `frontend/` (React) + `backend/` (FastAPI/Django)
- Ask: "I see both Python and TypeScript here - want to start with the
  backend API or the frontend?"

---

## Large Repo Threshold

If file count exceeds ~100 files or folder depth exceeds 4 levels:
> "This is a big codebase - too much to scan all at once. Want me to focus
> on a specific area? I can see these top-level modules: [list]. Pick one
> and we'll go deep."

Do not attempt to summarize everything. Stay focused.
