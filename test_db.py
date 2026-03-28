import dj_database_url
import os

# Test with a fake postgres URL
os.environ['DATABASE_URL'] = 'postgres://user:pass@host:5432/dbname'
config = dj_database_url.config()
print(f"Postgres Config: {config}")

# Test with no URL (should use default)
del os.environ['DATABASE_URL']
config = dj_database_url.config(default='sqlite:///db.sqlite3')
print(f"Default Config: {config}")
