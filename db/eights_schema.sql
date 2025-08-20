CREATE TABLE IF NOT EXISTS game_sessions (
    game_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    lobby_id BIGINT NOT NULL,
    alpha_id BIGINT NOT NULL,
    bravo_id BIGINT NOT NULL,
    host_id BIGINT NOT NULL,
    isStarted BOOLEAN NOT NULL,
    team_message_id BIGINT
);

CREATE TABLE IF NOT EXISTS players (
    game_ref BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    isHost BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (game_ref, user_id),
    FOREIGN KEY (game_ref) REFERENCES game_sessions(game_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS role_views (
    custom_button_id VARCHAR PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
);