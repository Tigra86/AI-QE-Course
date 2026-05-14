-- 02. Display second highest salary
-- DDL: Delete table tbl_2salary
DROP TABLE IF EXISTS tbl_2salary;
-- DDL: Create table tbl_2salary
CREATE TABLE tbl_2salary (id, name, salary);
-- DML: Insert data into the table tbl_2salary
INSERT INTO tbl_2salary VALUES (1, 'Alex',  275000);
INSERT INTO tbl_2salary VALUES (2, 'Ben',   175000);
INSERT INTO tbl_2salary VALUES (3, 'Chris', 205000);
INSERT INTO tbl_2salary VALUES (4, 'Nik',   150000);

-- 01. DDL: Using LIMIT
SELECT * FROM tbl_2salary ORDER BY salary DESC LIMIT 1,1;
-- 02. DQL: Using self-join
SELECT * FROM tbl_2salary WHERE salary = (SELECT max(a.salary) FROM tbl_2salary  a, tbl_2salary  b WHERE a.salary < b.salary);
-- 03. DQL: Using subquery
SELECT * FROM tbl_2salary WHERE salary = (SELECT max(salary) FROM tbl_2salary WHERE salary < (SELECT max(salary) FROM tbl_2salary));