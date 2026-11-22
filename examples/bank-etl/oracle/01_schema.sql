WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;

CREATE TABLE bank_dwh.customers (
  customer_id NUMBER(19) PRIMARY KEY,
  customer_name VARCHAR2(100 CHAR) NOT NULL,
  city VARCHAR2(60 CHAR) NOT NULL
);
CREATE TABLE bank_dwh.accounts (
  account_id NUMBER(19) PRIMARY KEY,
  customer_id NUMBER(19) NOT NULL REFERENCES bank_dwh.customers(customer_id),
  currency CHAR(3) NOT NULL,
  balance NUMBER(14,2) NOT NULL
);
CREATE TABLE bank_dwh.transactions (
  transaction_id NUMBER(19) PRIMARY KEY,
  account_id NUMBER(19) NOT NULL REFERENCES bank_dwh.accounts(account_id),
  booked_at TIMESTAMP NOT NULL,
  amount NUMBER(14,2) NOT NULL,
  transaction_type VARCHAR2(20 CHAR) NOT NULL
);
