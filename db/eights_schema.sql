CREATE TABLE IF NOT EXISTS GameSessions (
    game_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    lobby_id BIGINT NOT NULL,
    alpha_id BIGINT NOT NULL,
    bravo_id BIGINT NOT NULL,
    host_id BIGINT NOT NULL,
    isStarted BOOLEAN DEFAULT FALSE,
    team_message_id BIGINT
);

CREATE TABLE IF NOT EXISTS Players (
    game_ref BIGINT NOT NULL,
    user_id BIGINT NOT NULL UNIQUE,
    isHost BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (game_ref, user_id),
    FOREIGN KEY (game_ref) REFERENCES GameSessions(game_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS role_views (
    id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    custom_button_id VARCHAR
);

