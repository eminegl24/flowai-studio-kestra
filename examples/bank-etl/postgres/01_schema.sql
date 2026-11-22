CREATE TABLE customers (
  customer_id bigint PRIMARY KEY,
  customer_name varchar(100) NOT NULL,
  city varchar(60) NOT NULL
);
CREATE TABLE accounts (
  account_id bigint PRIMARY KEY,
  customer_id bigint NOT NULL REFERENCES customers,
  currency char(3) NOT NULL,
  balance numeric(14,2) NOT NULL
);
CREATE TABLE transactions (
  transaction_id bigint PRIMARY KEY,
  account_id bigint NOT NULL REFERENCES accounts,
  booked_at timestamp NOT NULL,
  amount numeric(14,2) NOT NULL,
  transaction_type varchar(20) NOT NULL
);

INSERT INTO customers VALUES
  (1, 'Deniz Kaya', 'Istanbul'),
  (2, 'Ece Arslan', 'Ankara'),
  (3, 'Mert Aydin', 'Izmir');
INSERT INTO accounts VALUES
  (101, 1, 'TRY', 1500.75),
  (102, 1, 'EUR', 550.25),
  (103, 2, 'TRY', 8200.00),
  (104, 3, 'TRY', 915.40);
INSERT INTO transactions VALUES
  (1001, 101, TIMESTAMP '2026-11-18 09:30:00', 1600.75, 'DEPOSIT'),
  (1002, 101, TIMESTAMP '2026-11-19 11:10:00', -100.00, 'PAYMENT'),
  (1003, 102, TIMESTAMP '2026-11-19 12:00:00', 550.25, 'DEPOSIT'),
  (1004, 103, TIMESTAMP '2026-11-20 15:20:00', 8500.00, 'DEPOSIT'),
  (1005, 103, TIMESTAMP '2026-11-21 16:45:00', -300.00, 'PAYMENT'),
  (1006, 104, TIMESTAMP '2026-11-22 10:05:00', 915.40, 'DEPOSIT');
