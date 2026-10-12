"""Day 17: explicit, consent-based, per-tenant/user durable preferences.

Do not store tokens, passwords, free-form profiles, or arbitrary user statements.
Identity must be provided by a trusted application boundary (not model output).
"""
import re
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ALLOWED = {'support_tier', 'preferred_language'}
LANGUAGES = {'english', 'hindi', 'gujarati', 'spanish', 'french'}
TIERS = {'standard', 'silver', 'gold', 'platinum'}


def _identity(tenant_id, user_id):
    if not all(isinstance(v, str) and v.strip() for v in (tenant_id, user_id)):
        raise ValueError('Trusted tenant_id and user_id are required')


def _validate(key, value):
    if key not in ALLOWED:
        raise ValueError('Only approved memory fields may be stored')
    if not isinstance(value, str):
        raise ValueError('Memory value must be a string')
    clean = value.strip().lower()
    if clean not in (TIERS if key == 'support_tier' else LANGUAGES):
        raise ValueError('Unsupported memory value')
    return clean


class MemoryStore:
    def __init__(self, connection):
        self.db = connection
        self.db.execute('''CREATE TABLE IF NOT EXISTS user_memories (
            tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
            key TEXT NOT NULL, value TEXT NOT NULL,
            PRIMARY KEY (tenant_id, user_id, key)
        )''')
        self.db.commit()

    def remember(self, tenant_id, user_id, key, value, *, consent=False):
        _identity(tenant_id, user_id)
        if consent is not True:
            raise PermissionError('Explicit user consent is required')
        value = _validate(key, value)
        with self.db:
            self.db.execute('''INSERT INTO user_memories VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id, user_id, key) DO UPDATE SET value=excluded.value''',
                (tenant_id, user_id, key, value))
        return {'key': key, 'value': value}

    def recall(self, tenant_id, user_id, question):
        """Retrieve only allowlisted facts relevant to the current question."""
        _identity(tenant_id, user_id)
        if not isinstance(question, str):
            raise ValueError('question must be text')
        text = question.lower()
        keys = []
        if re.search(r'\b(language|speak|translate|translation|hindi|gujarati|english|spanish|french)\b', text):
            keys.append('preferred_language')
        if re.search(r'\b(tier|membership|member|priority|premium|support level|gold|silver|platinum)\b', text):
            keys.append('support_tier')
        if not keys:
            return {}
        placeholders = ','.join('?' for _ in keys)
        rows = self.db.execute(
            f'SELECT key, value FROM user_memories WHERE tenant_id=? AND user_id=? AND key IN ({placeholders})',
            (tenant_id, user_id, *keys)).fetchall()
        return dict(rows)

    def forget(self, tenant_id, user_id, key=None):
        """Delete one fact or every fact for this user. Idempotent."""
        _identity(tenant_id, user_id)
        if key is not None and key not in ALLOWED:
            raise ValueError('Unknown memory field')
        with self.db:
            if key is None:
                cursor = self.db.execute('DELETE FROM user_memories WHERE tenant_id=? AND user_id=?',
                                         (tenant_id, user_id))
            else:
                cursor = self.db.execute('DELETE FROM user_memories WHERE tenant_id=? AND user_id=? AND key=?',
                                         (tenant_id, user_id, key))
        return cursor.rowcount


def invoke_with_memory(graph, store, *, tenant_id, user_id, thread_id, question):
    """Integrate with Day 16 without changing its files; memory is data, not instructions.

    Caller must construct graph/toolbox for the same authenticated identity.
    """
    _identity(tenant_id, user_id)
    if not isinstance(question, str) or not question.strip():
        raise ValueError('question must not be empty')
    relevant = store.recall(tenant_id, user_id, question)
    context = ''.join(f'\nSaved user preference ({k}): {v}.' for k, v in sorted(relevant.items()))
    # Data-only, allowlisted values prevent arbitrary memory prompt injection.
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError('thread_id is required')
    # Matches the corrected Day 16 checkpoint identity encoding.
    internal_id = json.dumps([tenant_id, user_id, thread_id], separators=(',', ':'), ensure_ascii=True)
    config = {'configurable': {'thread_id': internal_id, 'checkpoint_ns': ''}}
    return graph.invoke({'question': question + context}, config=config)


@contextmanager
def open_memory_store(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    try:
        yield MemoryStore(db)
    finally:
        db.close()
