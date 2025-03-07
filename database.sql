CREATE TABLE IF NOT EXISTS urls (
  id integer primary key NOT NULL GENERATED ALWAYS AS IDENTITY,
  name varchar(255) not null,
  created_at timestamp null
)
