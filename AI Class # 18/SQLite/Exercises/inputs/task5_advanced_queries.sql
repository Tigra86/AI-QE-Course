-- 05. Self-Join
-- DDL: Delete table tbl_salary
DROP TABLE IF EXISTS tbl_salary;
-- DDL: Create table tbl_salary
CREATE TABLE tbl_salary (empid, empname, mgrid, salary);
-- DML: Dumping data for table managers
INSERT INTO tbl_salary VALUES (1, 'John Loomis', NULL, 200000);
INSERT INTO tbl_salary VALUES (2, 'James Johnson', 1, 180000);
INSERT INTO tbl_salary VALUES (3, 'Sophia Yates', 2, 160000);
INSERT INTO tbl_salary VALUES (4, 'Arnold Wise', 3, 170000);
INSERT INTO tbl_salary VALUES (5, 'Eleanora Finlay', 4, 150000);

-- Find the employees whose salaries are higher than those of their managers.
-- DQL
SELECT B.empid AS `EMPLOYEE ID`, B.empname AS `EMPLOYEE NAME`, A.empname AS `MANAGER NAME`, B.salary AS `SALLARY`
FROM tbl_salary A JOIN tbl_salary B ON A.empid = B.mgrid WHERE A.salary < B.salary;

-- 06. Advanced Queries
-- DDL: Delete table emp
DROP TABLE IF EXISTS emp;
-- DDL: Create table emp
CREATE TABLE IF NOT EXISTS emp (empid, empname, mgrid, deptid, dob);
-- DML: Dumping data into the table emp
INSERT INTO emp VALUES (1, 'John Smith',   null, 10, '1970-01-14'), (2, 'Mike Loomis', 1, 10, '1965-10-20'), (3, 'Sam Martinez', 2, 10, '1968-03-08'), (4, 'Ann Moore', 2, 10, '1994-02-18'), (5, 'Jose Ganzales', 2, 10, '1983-03-20'), (6, 'Ann Morisen', 3, 20, '1972-11-25'), (7, 'Susan Noulden', 6, 20, '1981-09-11'), (8, 'Nikolas Bonjovi', 7, 20, '1986-02-28'), (9, 'Alvaro Nova', 7, 20, '1980-07-27'), (10,'Dav McGrooven', 7, 20, '1979-03-04'), (11,'Jemmy Bouly', 10, 30, '1982-11-25'), (12,'Mark Lay', 11, 30, '1989-03-04'), (13,'Andy Davis', 12, 30, '1989-03-04'), (14,'Sam Short', 12, 30, '1989-03-04'), (15,'Dack Demmel', 12, 30, '1989-03-04');

-- DDL: Delete table dept
DROP TABLE IF EXISTS dept;
-- DDL: Create table dept
CREATE TABLE dept (deptid, deptname);
-- DML: Dumping data into the table dept
INSERT INTO dept VALUES (10,'QA'), (20,'DEV'), (30,'IT');

-- 01. List of all employees, DOB, department of QA department, sort by EMPLOYEE (ASC).
SELECT empname AS 'EMPLOYEE', dob AS 'DOB', deptname AS 'DEPARTMENT' FROM emp JOIN dept ON emp.deptid = dept.deptid AND deptname = 'QA' ORDER BY empname;

-- 02. List of all employees, their age, department, by AGE (DESC).
SELECT empname AS 'EMPLOYEE', (STRFTIME('%s','now') - STRFTIME('%s', dob)) / 31557600 AS AGE, deptname AS 'DEPARTMENT' FROM emp JOIN dept ON emp.deptid = dept.deptid ORDER BY AGE DESC;

-- 03. List of all departments and numbers of employees.
SELECT deptname AS 'DEPARTMENT', COUNT(empname) AS 'EMPLOYEES' FROM emp JOIN dept ON emp.deptid = dept.deptid GROUP BY deptname HAVING COUNT(empname) > 0;

-- 04. List of all employees, their managers, department, including ones who have no manager.
SELECT B.empname AS 'EMPLOYEE',A.empname AS 'MANAGER', C.deptname AS 'DEPARTMENT' FROM emp AS A JOIN emp AS B ON A.empid = B.mgrid JOIN dept AS C ON B.deptid = C.deptid;

-- 05. List of all employees, their managers which have more than one employee.
SELECT A.empname AS 'MANAGER WITH MORE THAN 1 EMPLOYEE', C.empname AS 'MANAGER' FROM emp AS A JOIN emp AS B ON A.empid = B.mgrid JOIN emp AS C ON A.mgrid = C.empid GROUP BY A.empid HAVING COUNT(A.empname) > 1 ORDER BY A.empid ASC;