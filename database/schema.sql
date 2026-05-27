-- ===== ОБЩИЕ =====
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id        INTEGER PRIMARY KEY,
    log_channel     INTEGER,
    mod_role        INTEGER,
    admin_role      INTEGER,
    welcome_channel INTEGER,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS permission_overrides (
    guild_id  INTEGER NOT NULL,
    command   TEXT    NOT NULL,
    role_id   INTEGER NOT NULL,
    PRIMARY KEY (guild_id, command, role_id)
);

-- ===== ЗАЯВКИ =====
CREATE TABLE IF NOT EXISTS application_types (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id      INTEGER NOT NULL,
    name          TEXT    NOT NULL,            -- 'family', 'faction', 'promo', custom
    title         TEXT    NOT NULL,
    description   TEXT,
    channel_id    INTEGER NOT NULL,            -- куда отправляются заявки
    review_hours  INTEGER DEFAULT 24,
    questions_json TEXT   NOT NULL,            -- JSON: [{label,style,required,max_length}, ...]
    accept_role   INTEGER,
    image_url     TEXT,
    color         TEXT    DEFAULT '#8B0000',
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id     INTEGER NOT NULL,
    guild_id    INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    message_id  INTEGER,
    answers_json TEXT   NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending',  -- pending|review|call|accepted|declined
    moderator_id INTEGER,
    comment     TEXT,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (type_id) REFERENCES application_types(id) ON DELETE CASCADE
);

-- ===== КОНТРАКТЫ =====
CREATE TABLE IF NOT EXISTS contracts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT,
    reward      TEXT,
    deadline    TEXT,
    executor_id INTEGER,
    creator_id  INTEGER NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'active',  -- active|done|cancelled
    reward_role INTEGER,
    message_id  INTEGER,
    channel_id  INTEGER,
    created_at  TEXT    DEFAULT (datetime('now')),
    completed_at TEXT
);

-- ===== УЧЁТ =====
CREATE TABLE IF NOT EXISTS inventory_categories (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    name     TEXT    NOT NULL,
    UNIQUE (guild_id, name)
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    category_id INTEGER,
    name        TEXT    NOT NULL,
    owner_id    INTEGER,
    description TEXT,
    data_json   TEXT,
    created_at  TEXT    DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES inventory_categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS inventory_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id   INTEGER NOT NULL,
    actor_id  INTEGER NOT NULL,
    action    TEXT    NOT NULL,   -- create|update|delete
    diff_json TEXT,
    at        TEXT DEFAULT (datetime('now'))
);

-- ===== ПЛЮСЫ (сборы) =====
CREATE TABLE IF NOT EXISTS plus_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id     INTEGER NOT NULL,
    channel_id   INTEGER NOT NULL,
    message_id   INTEGER,
    title        TEXT    NOT NULL,
    event_date   TEXT,
    slots        INTEGER NOT NULL DEFAULT 0,        -- 0 = безлимит
    extra_slots  INTEGER NOT NULL DEFAULT 0,        -- доп-слоты (запас)
    role_id      INTEGER,
    branch       TEXT,
    comment      TEXT,
    image_url    TEXT,
    creator_id   INTEGER NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'open',   -- open|closed
    created_at   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plus_participants (
    event_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    queue     INTEGER NOT NULL,           -- порядковый номер «по очереди»
    is_extra  INTEGER NOT NULL DEFAULT 0,
    joined_at TEXT    DEFAULT (datetime('now')),
    PRIMARY KEY (event_id, user_id),
    FOREIGN KEY (event_id) REFERENCES plus_events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plus_queue ON plus_participants(event_id, queue);

-- ===== TEMP VOICE =====
CREATE TABLE IF NOT EXISTS tempvoice_settings (
    guild_id      INTEGER PRIMARY KEY,
    creator_id    INTEGER NOT NULL,        -- голосовой канал-создатель
    category_id   INTEGER NOT NULL,
    default_limit INTEGER DEFAULT 0,
    panel_channel INTEGER
);

CREATE TABLE IF NOT EXISTS tempvoice_channels (
    channel_id INTEGER PRIMARY KEY,
    guild_id   INTEGER NOT NULL,
    owner_id   INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ===== РОЛИ ПО КНОПКЕ =====
CREATE TABLE IF NOT EXISTS role_panels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    message_id  INTEGER,
    title       TEXT,
    description TEXT,
    color       TEXT DEFAULT '#5865F2',
    multi       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS role_panel_roles (
    panel_id INTEGER NOT NULL,
    role_id  INTEGER NOT NULL,
    label    TEXT,
    emoji    TEXT,
    style    TEXT DEFAULT 'secondary',
    position INTEGER DEFAULT 0,
    PRIMARY KEY (panel_id, role_id),
    FOREIGN KEY (panel_id) REFERENCES role_panels(id) ON DELETE CASCADE
);

-- ===== EMBED-конструктор (сохранённые шаблоны) =====
CREATE TABLE IF NOT EXISTS embed_templates (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    name     TEXT    NOT NULL,
    payload  TEXT    NOT NULL,        -- JSON
    author_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE (guild_id, name)
);

-- ===== МОНИТОРИНГ MAJESTIC =====
CREATE TABLE IF NOT EXISTS monitor_panels (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER,
    server_ids TEXT NOT NULL,           -- '1,2,3'
    last_state TEXT
);

-- ===== AFK =====
CREATE TABLE IF NOT EXISTS afk_users (
    guild_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    reason   TEXT,
    since    TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (guild_id, user_id)
);

-- ===== ЛОГИ =====
CREATE TABLE IF NOT EXISTS log_channels (
    guild_id  INTEGER NOT NULL,
    category  TEXT    NOT NULL,        -- messages|voice|moderation|members|roles|channels
    channel_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, category)
);
