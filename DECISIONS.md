# DECISIONS.md - Architecture and Implementation Decisions

## 1. Dual-Engine DB Strategy (PostgreSQL/PostGIS + SQLite Geo Fallback)
- **Context**: The hackathon spec targets PostgreSQL 16 + PostGIS via docker-compose. In environments where Docker is not running or during local offline evaluation, the backend must still run seamlessly without crashing.
- **Decision**: Use SQLAlchemy with dynamic geo distance calculations:
  - If connected to Postgres, utilize PostGIS `ST_DWithin` and spatial functions.
  - If running in SQLite mode (`DATABASE_URL=sqlite:///./bharosa.db`), implement Haversine formula directly in Python/SQL functions for distance computations.
  - This ensures 100% test and demo reliability offline while maintaining full PostGIS production readiness.

## 2. Simulated Clock (`clock.py`)
- **Context**: Demonstrating 72-hour SLAs, escalation ladders, and auto-close timeouts in a 90-second pitch is impossible with real time.
- **Decision**: All datetime access flows strictly through `clock.now() = datetime.now(timezone.utc) + timedelta(hours=DEMO_OFFSET_HOURS)`. The `/api/demo/advance-time` endpoint increments `DEMO_OFFSET_HOURS` in memory/db, allowing instant fast-forwarding of hours or days during live demos.

## 3. Decoupled Channel Architecture (`ChannelAdapter`)
- **Context**: WhatsApp Cloud API requires Meta developer verification, phone number registrations, and active internet. Demonstrations must never fail due to API rate limits or lack of mobile signal.
- **Decision**: All messaging logic communicates through the abstract `ChannelAdapter` interface (`send_message`, `send_interactive_buttons`, `send_media`). Three concrete adapters exist:
  - `ConsoleAdapter`: Outputs to in-memory event bus connected to `/sim` web chat simulator. Zero external dependencies.
  - `TelegramAdapter`: Connects to Telegram Bot API webhook.
  - `WhatsAppCloudAdapter`: Connects to Meta WhatsApp Cloud API.
- Switchable simply via `CHANNEL=console|telegram|whatsapp`.

## 4. Deterministic Mock AI (`MOCK_AI=true`)
- **Context**: Live Gemini API calls may experience network latency or API rate limit issues during hackathon presentations.
- **Decision**: If `MOCK_AI=true`, the `ai.py` service yields high-fidelity, deterministic responses:
  - Classification: extracts realistic category, severity, and safety flags based on keywords.
  - Transcription: simulates bilingual Hindi/English voice note speech-to-text.
  - Embeddings: generates deterministic 768-dim pseudo-embeddings that match semantically similar phrases.
  - Vision check: validates image comparison with plausible confidence scores and reasoning.

## 5. Tamper-Evident Audit Log via SHA-256 Chaining
- **Context**: Preventing corrupt officer closures and fake resolution logs.
- **Decision**: Every status change, assignment, report, and resolution writes an immutable row into `ticket_events`.
  - `hash = sha256(prev_hash + ticket_id + type + canonical_json(payload) + created_at_iso)`.
  - The first event uses `prev_hash = 'GENESIS'`.
  - `/api/public/tickets/{code}/verify-chain` verifies the entire cryptographic chain and displays a prominent "Cryptographically Verified" badge on the public ticket page.

## 6. Privacy & Data Protection
- **Decision**:
  - No phone numbers or citizen channel IDs are ever exposed in public or officer APIs.
  - Public ticket views show fuzzed location (ward level and nearby landmark) rather than exact house coordinates.
  - Citizens are identified solely by their channel user ID hashed/abstracted internally.
