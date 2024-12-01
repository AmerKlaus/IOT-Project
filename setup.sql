DROP TABLE IF EXISTS rfid_users;

CREATE TABLE rfid_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfid_tag_number TEXT NOT NULL UNIQUE,
    user_name TEXT NOT NULL,
    user_picture TEXT NOT NULL,
    temperature_threshold INTEGER NOT NULL,
    light_intensity_threshold INTEGER NOT NULL
);

INSERT INTO rfid_users (rfid_tag_number, user_name, user_picture, temperature_threshold, light_intensity_threshold)
VALUES
    ('13c2e024', 'Alice', '/static/images/alice.jpg', 24, 300),
    ('b3198df7', 'Bob', '/static/images/bob.jpg', 22, 400);

SELECT * FROM rfid_users;
