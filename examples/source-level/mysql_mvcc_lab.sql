-- MANUAL LAB ONLY. Use an empty, dedicated MySQL 8 test database.
-- This file was not executed against a local or remote server in this task.
-- Run setup once in that dedicated database. No DROP/TRUNCATE statements.
CREATE TABLE source_mvcc_lab (
  id BIGINT PRIMARY KEY,
  balance INT NOT NULL
) ENGINE=InnoDB;
INSERT INTO source_mvcc_lab VALUES (1,100);

-- SESSION A: run until the first SELECT, then pause.
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT balance FROM source_mvcc_lab WHERE id=1; -- establishes ordinary snapshot:100

-- SESSION B: in a different connection, run these two statements.
-- UPDATE source_mvcc_lab SET balance=200 WHERE id=1;
-- COMMIT; -- ensure autocommit/transaction handling is as intended in this connection

-- SESSION A: after B has committed, run separately.
-- SELECT balance FROM source_mvcc_lab WHERE id=1; -- RR ordinary snapshot:100
-- SELECT balance FROM source_mvcc_lab WHERE id=1 FOR UPDATE; -- locking/current read:200
-- ROLLBACK;

-- Repeat with READ COMMITTED and a reset fixture in a new experiment.
-- Do not run this whole file in one connection and claim it tests concurrency.
