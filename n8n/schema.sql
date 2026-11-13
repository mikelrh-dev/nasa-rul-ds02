-- Tabla que escribe el nodo "HANGAR Postgres insert" de n8n/flujo.json.
-- Aplicar una vez antes de activar el flujo:
--   psql "$DATABASE_URL" -f n8n/schema.sql
--
-- El orden y los tipos replican la tabla viva en la instancia local, tal como
-- la reporta el esquema cacheado del nodo Postgres (columnas id, decision,
-- unidad, ciclo, rul_punto, limite_inferior, limite_superior, motivo,
-- fingerprint, artefacto_sha256, idempotency_key, created_at).
CREATE TABLE IF NOT EXISTS ds02_decisiones (
    id               bigserial PRIMARY KEY,
    decision         text        NOT NULL,
    unidad           integer,
    ciclo            integer,
    rul_punto        double precision,
    limite_inferior  double precision,
    limite_superior  double precision,
    motivo           text,
    fingerprint      text,
    artefacto_sha256 text,
    idempotency_key  text,
    created_at       timestamptz NOT NULL DEFAULT now()
);

-- Nota: la tabla no garantiza idempotencia por `fingerprint`. Un reintento del
-- nodo Postgres puede duplicar la fila; si molesta, cambiar el nodo a Upsert
-- usando `fingerprint` como columna de match.
