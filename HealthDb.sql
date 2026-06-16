use health_db;
select * from users;
describe users;
INSERT INTO users (username, password) VALUES ('root', '12345@Code');
DROP TABLE users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);
select * from users;



