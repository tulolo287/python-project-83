CREATE TABLE IF NOT EXISTS urls (
  id integer primary key NOT NULL GENERATED ALWAYS AS IDENTITY,
  name varchar(255) not null,
  created_at date null
);

CREATE TABLE IF NOT EXISTS url_checks (
  id integer primary key NOT NULL GENERATED ALWAYS AS IDENTITY,
  url_id integer not null,
  status_code integer,
  h1 varchar(100),
  title varchar(100),
  description text,
  created_at date null
);
