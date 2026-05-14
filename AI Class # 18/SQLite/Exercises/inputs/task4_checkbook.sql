-- 04. Checkbook
-- DDL: Delete table checkbook
DROP TABLE IF EXISTS checkbook;

-- DDL: Create table checkbook
CREATE TABLE IF NOT EXISTS checkbook (id INTEGER PRIMARY KEY AUTOINCREMENT, name, transDate, debit, credit);  

-- DML: Dumping data for table Checkbook
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('John Loomis','2025-03-03', 1000 ,0);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Mike Stevenson', '2025-01-14', 0, 0650);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Alex Moore', '2025-02-11', 100, 100);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Nikita Smith', '2025-03-03', 2000, 1000);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Boris Goodwell', '2025-04-12', 0, 3000);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Steve Aaron', '2025-02-02', 500, 1500);
INSERT INTO checkbook (name, transDate, debit, credit) VALUES ('Jordan Bloom', '2025-04-29', 0, 6000);

-- 01. Display the number of rows in the table checkbook.
SELECT COUNT(*) FROM checkbook;
-- 02. Display all table checkbook rows.
SELECT * FROM checkbook;
-- 03. Display the client who made the FIRST transaction.
SELECT * FROM checkbook WHERE transDate = (SELECT MIN(transDate) FROM checkbook);
-- 04. Display the client who made the LAST transaction.
SELECT * FROM checkbook WHERE transDate = (SELECT MAX(transDate) FROM checkbook);
-- 05. List all clients who do not owe any money.
SELECT * FROM checkbook WHERE credit = 0;
-- 06. List all clients whose balance = 0.
SELECT * FROM checkbook WHERE (debit - credit) = 0;
-- 07. List all clients who owe money.
SELECT * FROM checkbook WHERE (debit - credit) < 0;
-- 08. List all clients with a positive balance.
SELECT * FROM checkbook WHERE (debit - credit) > 0;
-- 09. List all clients with their negative balance.
SELECT id, name, (credit - debit) AS `Balance` FROM checkbook WHERE (debit - credit) < 0;
-- 10. List all clients who owe 1000 dollars or more.
SELECT id, name, (credit - debit) AS `Balance` FROM checkbook WHERE (credit - debit) >= 1000;