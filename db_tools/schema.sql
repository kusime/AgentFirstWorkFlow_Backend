CREATE TABLE "accountflowgroup" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL
);

CREATE TABLE "currencytype" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL
);

CREATE TABLE "account" (
  "id" SERIAL PRIMARY KEY,
  "currency_type" integer NOT NULL,
  "name" text NOT NULL,
  "max_debt_capacity" double precision,
  "soft_limit" double precision,
  "logic_account" integer
);

CREATE TABLE "account_accountflowgroup" (
  "account" integer NOT NULL,
  "accountflowgroup" integer NOT NULL,
  PRIMARY KEY ("account", "accountflowgroup")
);

CREATE TABLE "flowtype" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL
);

CREATE TABLE "actiontype" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL,
  "flow_type" integer NOT NULL
);

CREATE TABLE "fxexchangecontrolrate" (
  "id" SERIAL PRIMARY KEY,
  "from_currency" integer NOT NULL,
  "to_currency" integer NOT NULL,
  "currency_rate" double precision
);

CREATE TABLE "holetype" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL
);

CREATE TABLE "theholelevel" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL,
  "level" text NOT NULL
);

CREATE TABLE "hole" (
  "id" uuid PRIMARY KEY,
  "the_hole_level" integer NOT NULL,
  "currency_type" integer NOT NULL,
  "amount" double precision,
  "is_currency_locked" boolean,
  "detail" text NOT NULL,
  "account" integer NOT NULL,
  "hole_type" integer NOT NULL,
  "created_at" timestamp,
  "require_physical_account" boolean
);

CREATE TABLE "tracetype" (
  "id" SERIAL PRIMARY KEY,
  "name" text NOT NULL
);

CREATE TABLE "holetrace" (
  "id" SERIAL PRIMARY KEY,
  "source_account" integer NOT NULL,
  "action_type" integer NOT NULL,
  "execute_at_fx_rate" double precision,
  "realtime_fx_rate" double precision,
  "currency_type" integer NOT NULL,
  "from_currency" integer,
  "detail" text NOT NULL,
  "amount" double precision,
  "trace_type" integer NOT NULL
);

CREATE TABLE "hole_holetrace" (
  "hole" uuid NOT NULL,
  "holetrace" integer NOT NULL,
  PRIMARY KEY ("hole", "holetrace")
);

ALTER TABLE "account" ADD FOREIGN KEY ("currency_type") REFERENCES "currencytype" ("id") ON DELETE CASCADE;

ALTER TABLE "account" ADD FOREIGN KEY ("logic_account") REFERENCES "account" ("id") ON DELETE SET NULL;

ALTER TABLE "account_accountflowgroup" ADD FOREIGN KEY ("account") REFERENCES "account" ("id");

ALTER TABLE "account_accountflowgroup" ADD FOREIGN KEY ("accountflowgroup") REFERENCES "accountflowgroup" ("id");

ALTER TABLE "actiontype" ADD FOREIGN KEY ("flow_type") REFERENCES "flowtype" ("id") ON DELETE CASCADE;

ALTER TABLE "fxexchangecontrolrate" ADD FOREIGN KEY ("from_currency") REFERENCES "currencytype" ("id") ON DELETE CASCADE;

ALTER TABLE "fxexchangecontrolrate" ADD FOREIGN KEY ("to_currency") REFERENCES "currencytype" ("id") ON DELETE CASCADE;

ALTER TABLE "hole" ADD FOREIGN KEY ("account") REFERENCES "account" ("id") ON DELETE CASCADE;

ALTER TABLE "hole" ADD FOREIGN KEY ("currency_type") REFERENCES "currencytype" ("id") ON DELETE CASCADE;

ALTER TABLE "hole" ADD FOREIGN KEY ("hole_type") REFERENCES "holetype" ("id") ON DELETE CASCADE;

ALTER TABLE "hole" ADD FOREIGN KEY ("the_hole_level") REFERENCES "theholelevel" ("id") ON DELETE CASCADE;

ALTER TABLE "holetrace" ADD FOREIGN KEY ("action_type") REFERENCES "actiontype" ("id") ON DELETE CASCADE;

ALTER TABLE "holetrace" ADD FOREIGN KEY ("currency_type") REFERENCES "currencytype" ("id") ON DELETE CASCADE;

ALTER TABLE "holetrace" ADD FOREIGN KEY ("from_currency") REFERENCES "currencytype" ("id") ON DELETE SET NULL;

ALTER TABLE "holetrace" ADD FOREIGN KEY ("source_account") REFERENCES "account" ("id") ON DELETE CASCADE;

ALTER TABLE "holetrace" ADD FOREIGN KEY ("trace_type") REFERENCES "tracetype" ("id") ON DELETE CASCADE;

ALTER TABLE "hole_holetrace" ADD FOREIGN KEY ("hole") REFERENCES "hole" ("id");

ALTER TABLE "hole_holetrace" ADD FOREIGN KEY ("holetrace") REFERENCES "holetrace" ("id");

