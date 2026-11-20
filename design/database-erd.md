# Database ERD

```mermaid
erDiagram
    USERS ||--o{ TICKETS : "raises (member_id)"
    USERS |o--o{ TICKETS : "assigned to (assignee_id)"
    TAT_TARGETS ||--o{ TICKETS : "sets target for (priority)"
    TICKETS ||--o{ TICKET_MESSAGES : "has conversation"
    USERS ||--o{ TICKET_MESSAGES : "writes"
    TICKETS ||--o{ TICKET_EVENTS : "history log"
    USERS |o--o{ TICKET_EVENTS : "performs (NULL = system)"
    USERS ||--o{ NOTIFICATIONS : "receives"
    TICKETS |o--o{ NOTIFICATIONS : "about"
    TICKETS ||--o{ INTERNAL_TICKETS : "spawns"
    USERS ||--o{ INTERNAL_TICKETS : "creates"
    USERS |o--o{ INTERNAL_TICKETS : "completes"
    USERS ||--o{ SAVED_REPLIES : "authors"
    USERS |o--o{ TAT_TARGETS : "updated by"
    USERS |o--o{ APP_SETTINGS : "updated by"
    USERS { int id PK string name string email UK string password_hash string role bool is_active datetime created_at }
    TAT_TARGETS { string priority PK int target_minutes datetime updated_at int updated_by FK }
    APP_SETTINGS { string key PK int value_int datetime updated_at int updated_by FK }
    TICKETS { int id PK int member_id FK int assignee_id FK string category string subject text description string priority FK string status bool waiting_for_member datetime waiting_since int tat_elapsed_seconds datetime tat_running_since datetime due_at datetime escalated_at text escalation_reason datetime resolved_at datetime closed_at int resolution_seconds int reopen_count int version datetime created_at datetime updated_at }
    TICKET_MESSAGES { int id PK int ticket_id FK int author_id FK text body bool requests_info datetime created_at }
    TICKET_EVENTS { int id PK int ticket_id FK int actor_id FK string event_type string old_value string new_value text reason datetime created_at }
    NOTIFICATIONS { int id PK int user_id FK int ticket_id FK string type string message bool is_read datetime created_at }
    INTERNAL_TICKETS { int id PK int ticket_id FK string team string title text description string status int created_by FK datetime created_at int completed_by FK datetime completed_at text completion_note }
    SAVED_REPLIES { int id PK string title UK text body string category bool is_active int created_by FK datetime created_at datetime updated_at }
```


Users have unique lower-cased email. Ticket IDs are SQLite autoincrement primary keys displayed as `TKT-{id:04d}` and never reused. Enum-like values use lowercase strings and checks. Foreign keys are enabled; ticket list/search, status, due time, creation time, notification ownership/read state, and message chronology are indexed.

The planned SQLAlchemy models and one initial Alembic migration must match this ERD column by column. All datetimes are UTC-aware in Python and serialized as ISO-8601 `Z` values.

