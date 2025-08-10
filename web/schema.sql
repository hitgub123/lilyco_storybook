-- 删除已存在的表，以便重新创建
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Novels;
DROP TABLE IF EXISTS Comics;

-- 用户表
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 小说表
CREATE TABLE Novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 漫画表
CREATE TABLE Comics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    novel_id INTEGER NOT NULL, -- 外键关联到小说表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES Novels(id)
);
