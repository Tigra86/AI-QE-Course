-- 01. Display second row
-- DDL: Delete table tbl_2row
DROP TABLE IF EXISTS tbl_2row;
-- DDL: Create table tbl_2row
CREATE TABLE tbl_2row (id, name);
-- DML: Insert data into the table tbl_2row
INSERT INTO tbl_2row (id, name) VALUES (5,  'Alex');
INSERT INTO tbl_2row (id, name) VALUES (18, 'Ben');
INSERT INTO tbl_2row (id, name) VALUES (44, 'Chris');
INSERT INTO tbl_2row (id, name) VALUES (65, 'Nik');

-- 01. DQL: Using LIMIT                     
SELECT * FROM tbl_2row LIMIT 0,10;
-- 02. DQL: Using Subquery
SELECT * FROM tbl_2row WHERE id = (SELECT min(a.id) FROM tbl_2row a, tbl_2row b WHERE a.id > b.id);