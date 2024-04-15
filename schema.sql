CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT CHECK( status IN ('Atlikta', 'Neatlikta', 'Nukelta') ) NOT NULL DEFAULT 'Neatlikta',
    user_name TEXT NOT NULL,
    FOREIGN KEY (user_name) REFERENCES users(name)
);