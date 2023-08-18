DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS info;
DROP TABLE IF EXISTS playlist;
DROP TABLE IF EXISTS video;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE playlist (
    playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    playlist_title TEXT NOT NULL,
    playlist_url TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (user_id)
);

CREATE TABLE video (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    video_title TEXT NOT NULL,
    video_url TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    sub_count INTEGER NOT NULL,
    video_date TEXT NOT NULL,
    views INTEGER NOT NULL,
    tags TEXT,
    FOREIGN KEY (playlist_id) REFERENCES playlist (playlist_id)
);