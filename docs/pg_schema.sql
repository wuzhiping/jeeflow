-- jeeflow PostgreSQL schema (reverse-engineered from vendor/jeeflow/repository/{base,ext}.py INSERT/UPDATE 列清单).
-- Apply once:
--   psql "postgresql://postgres:postgres@127.0.0.1:5432/jeeflow" -f docs/pg_schema.sql
-- Idempotent: 用 IF NOT EXISTS，可重复执行。

CREATE TABLE IF NOT EXISTS wf_process_define (
    id              BIGINT PRIMARY KEY,
    name            VARCHAR(128),
    display_name    VARCHAR(255),
    type            VARCHAR(64),
    state           INT,
    content         TEXT,
    version         INT,
    create_time     TIMESTAMP,
    create_user     VARCHAR(64),
    update_time     TIMESTAMP,
    update_user     VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_instance (
    id                  BIGINT PRIMARY KEY,
    parent_id           BIGINT,
    process_define_id   BIGINT,
    state               INT,
    parent_node_name    VARCHAR(255),
    business_no         VARCHAR(128),
    operator            VARCHAR(64),
    owner_id            VARCHAR(64),  -- FIX-T9 (2026-09-17) §66 实例所有者（流程发起人 userId）
    expire_time         TIMESTAMP,
    variable            TEXT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS idx_wf_process_instance_owner  ON wf_process_instance(owner_id);

CREATE TABLE IF NOT EXISTS wf_process_task (
    id                  BIGINT PRIMARY KEY,
    process_instance_id BIGINT,
    task_name           VARCHAR(128),
    display_name        VARCHAR(255),
    task_type           VARCHAR(64),
    perform_type        VARCHAR(64),
    task_state          INT,
    operator            VARCHAR(64),
    finish_time         TIMESTAMP,
    expire_time         TIMESTAMP,
    form_key            VARCHAR(255),
    task_parent_id      BIGINT,
    variable            TEXT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_task_actor (
    id              BIGINT PRIMARY KEY,
    process_task_id BIGINT,
    actor_id        VARCHAR(64),
    create_time     TIMESTAMP,
    create_user     VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_cc_instance (
    id                  BIGINT PRIMARY KEY,
    process_instance_id BIGINT,
    actor_id            VARCHAR(64),
    state               INT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64),
    update_time         TIMESTAMP,
    update_user         VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_design (
    id              BIGINT PRIMARY KEY,
    name            VARCHAR(128),
    display_name    VARCHAR(255),
    type            VARCHAR(64),
    icon            VARCHAR(255),
    is_deployed     BOOLEAN,
    remark          VARCHAR(500),
    create_time     TIMESTAMP,
    create_user     VARCHAR(64),
    update_time     TIMESTAMP,
    update_user     VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_design_his (
    id                  BIGINT PRIMARY KEY,
    process_design_id   BIGINT,
    content             TEXT,
    create_time         TIMESTAMP,
    create_user         VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS wf_process_surrogate (
    id              BIGINT PRIMARY KEY,
    process_name    VARCHAR(128),
    operator        VARCHAR(64),
    surrogate       VARCHAR(64),
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    enabled         BOOLEAN,
    create_time     TIMESTAMP,
    create_user     VARCHAR(64),
    update_time     TIMESTAMP,
    update_user     VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_wf_process_instance_define   ON wf_process_instance(process_define_id);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_instance     ON wf_process_task(process_instance_id);
CREATE INDEX IF NOT EXISTS idx_wf_process_task_actor_task   ON wf_process_task_actor(process_task_id);
CREATE INDEX IF NOT EXISTS idx_wf_process_cc_instance_inst  ON wf_process_cc_instance(process_instance_id);
CREATE INDEX IF NOT EXISTS idx_wf_process_design_his_design ON wf_process_design_his(process_design_id);