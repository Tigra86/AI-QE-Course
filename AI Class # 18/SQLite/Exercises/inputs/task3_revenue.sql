-- 03. Display who made the most gross revenue
-- DDL: Delete table tbl_revenue
DROP TABLE IF EXISTS tbl_revenue;
-- DDL: Create table tbl_revenue
CREATE TABLE tbl_revenue (id, name, revenue);
-- DML: Insert data into the table tbl_revenue
INSERT INTO tbl_revenue (name,revenue) VALUES ('Alex', 100);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Ben',   50);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Alex',  35);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Chris', 40);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Chris', 70);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Ben',   55);
INSERT INTO tbl_revenue (name,revenue) VALUES ('Ben',   65);

-- 01. DQL: Using LIMIT
SELECT name, SUM(revenue) AS total FROM tbl_revenue GROUP BY name ORDER BY total DESC LIMIT 1;
-- 02. DQL: Using subquery
SELECT name, total FROM (SELECT name, SUM(revenue) AS total
FROM tbl_revenue GROUP BY name) AS gross WHERE total = (SELECT MAX(mg.total) 
FROM (SELECT name, SUM(revenue) AS total FROM tbl_revenue GROUP BY name) AS mg);