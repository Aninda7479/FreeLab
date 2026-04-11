import sqlite3
import os

DB_NAME = 'screentime.db'

def migrate():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Migrate logs table
    try:
        c.execute("ALTER TABLE logs ADD COLUMN device_id TEXT DEFAULT 'windows_main'")
        c.execute("ALTER TABLE logs ADD COLUMN platform TEXT DEFAULT 'windows'")
        print("Migrated logs table successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Columns already exist in logs table.")
        else:
            print(f"Error migrating logs: {e}")

    # Migrate daily_stats table
    try:
        # Since primary key changing (date, app_name) -> (date, app_name, device_id)
        # SQLite doesn't support ALTER TABLE ... ADD PRIMARY KEY directly.
        # We need to recreate the table.
        
        c.execute("PRAGMA foreign_keys=off;")
        c.execute("BEGIN TRANSACTION;")
        
        c.execute('''CREATE TABLE daily_stats_new
                 (date TEXT, app_name TEXT, total_seconds INTEGER, 
                  device_id TEXT DEFAULT 'windows_main', platform TEXT DEFAULT 'windows',
                  PRIMARY KEY (date, app_name, device_id))''')
                  
        c.execute('''INSERT INTO daily_stats_new (date, app_name, total_seconds)
                     SELECT date, app_name, total_seconds FROM daily_stats''')
                     
        c.execute("DROP TABLE daily_stats")
        c.execute("ALTER TABLE daily_stats_new RENAME TO daily_stats")
        
        c.execute("COMMIT;")
        c.execute("PRAGMA foreign_keys=on;")
        print("Migrated daily_stats table successfully.")
    except Exception as e:
        print(f"Error migrating daily_stats: {e}")
        c.execute("ROLLBACK;")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
