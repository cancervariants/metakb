DO $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_roles WHERE rolname = 'anonymous'
  ) THEN
    CREATE ROLE anonymous LOGIN;
  END IF;
END
$$;
