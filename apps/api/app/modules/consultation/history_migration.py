"""Add an account owner for chat sessions, including administrator accounts."""
from sqlalchemy import inspect,text

def ensure_chat_owner(engine):
    with engine.begin() as conn:
        columns={c['name'] for c in inspect(conn).get_columns('chat_sessions')}
        if 'owner_user_id' not in columns:
            conn.execute(text('ALTER TABLE chat_sessions ADD COLUMN owner_user_id VARCHAR(36) REFERENCES users(user_id)'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_chat_sessions_owner_user_id ON chat_sessions(owner_user_id)'))
        conn.execute(text('UPDATE chat_sessions SET owner_user_id=student_id WHERE owner_user_id IS NULL AND student_id IS NOT NULL'))
