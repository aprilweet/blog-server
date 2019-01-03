CREATE TABLE tag
(
    article_id INT,
    tag_name   TEXT,
    PRIMARY KEY (article_id, tag_name)
);
CREATE TABLE article
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag TINYINT,
    title TEXT,
    author TEXT,
    create_time DATETIME,
    update_time DATETIME,
    source_link TEXT,
    abstract TEXT,
    classification TEXT,
    body TEXT,
    body_format TEXT,
    abstract_format TEXT,
    user_id INT
);
CREATE TABLE user
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id TEXT,
    open_id TEXT,
    union_id TEXT,
    nick_name TEXT,
    avatar_url TEXT,
    gender TINYINT,
    admin TINYINT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE TABLE comment
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag TINYINT,
    target TEXT,
    target_id INT,
    user_id INT,
    create_time DATETIME,
    body TEXT,
    update_time DATETIME
);
CREATE TABLE like
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag TINYINT,
    target TEXT,
    target_id INT,
    user_id INT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE TABLE session
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255),
    data BLOB,
    expiry DATETIME
);
CREATE UNIQUE INDEX session_session_id_uindex ON session (session_id);
CREATE TABLE books
(
    link TEXT,
    title TEXT,
    pub TEXT,
    img TEXT,
    state TEXT,
    rating TINYINT,
    comment TEXT,
    date DATE,
    create_time DATETIME,
    flag TINYINT,
		PRIMARY KEY (link, flag)
);
CREATE TABLE movies
(
    link TEXT,
    title TEXT,
    alias TEXT,
    intro TEXT,
    img TEXT,
    state TEXT,
    rating TINYINT,
    comment TEXT,
    date DATE,
    create_time DATETIME,
    flag TINYINT,
		PRIMARY KEY (link, flag)
);
CREATE TABLE analytics
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT,
    data TEXT,
    create_time DATETIME
);