-- Runtime login for app processes. Schema owner stays the cluster POSTGRES_USER.
-- Password is set by the apply wrapper from POSTGRES_PASSWORD; none here.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aegis_app') THEN
    CREATE ROLE aegis_app NOSUPERUSER LOGIN;
  END IF;
END
$$;

ALTER ROLE aegis_app NOSUPERUSER LOGIN;

GRANT USAGE, CREATE ON SCHEMA public TO aegis_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aegis_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aegis_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aegis_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO aegis_app;

-- Ledger is append-only (see CONTEXT.md): the app role may read and insert,
-- but never mutate or truncate.
GRANT SELECT, INSERT ON TABLE agent_events TO aegis_app;
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE agent_events FROM aegis_app;
