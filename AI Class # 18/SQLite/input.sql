-- 01.DDL DELETE TABLE customer
DROP TABLE IF EXISTS customer;

-- 02.DDL DELETE TABLE credit_card
DROP TABLE IF EXISTS credit_card;

-- 03.DDL CREATE TABLE customer
CREATE TABLE IF NOT EXISTS customer (id, name);

-- 04.DDL CREATE TABLE credit_card
CREATE TABLE IF NOT EXISTS credit_card (id, cc_type, cc_number, cc_exp);

-- 05.DML INSERT DATA
INSERT INTO customer VALUES (1,'John Smith');
INSERT INTO credit_card VALUES (1, 'VISA', '4532547106994816', '02/29');
INSERT INTO credit_card VALUES (1, 'MasterCard', '5584398929973080', '10/29');

-- 06.DDL SHOW TABLES
SELECT tbl_name FROM sqlite_master WHERE type = 'table';

-- 07.DDL SHOW COLUMNS
PRAGMA table_info('customer');
  
-- 08.DQL RETRIEVE DATA FROM TABLE customer
SELECT * FROM customer;

-- 09.DQL RETRIEVE DATA FROM TABLE credit_card
SELECT * FROM credit_card;

-- 10.DQL RETRIEVE DATA FROM TABLES customer AND credit_card USING JOIN CLAUSE
SELECT customer.id, name, cc_type, cc_number, cc_exp
FROM   customer JOIN credit_card 
ON     customer.id = credit_card.id;

