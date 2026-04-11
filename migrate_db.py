import sqlite3
import os

db_path = os.path.join('instance', 'farming.db')
if not os.path.exists(db_path):
    print(f"ERROR: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type, default=None):
    try:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {type}"
        if default is not None:
            sql += f" DEFAULT {default}"
        cursor.execute(sql)
        print(f"Added '{column}' to {table}")
    except Exception as e:
        print(f"Skip '{column}' in {table}: {e}")

# Expense Records
add_column('expense_records', 'type', 'VARCHAR(10)', "'expense'")
add_column('expense_records', 'is_anomaly', 'BOOLEAN', 0)

# Crop History
add_column('crop_history', 'confidence_score', 'FLOAT')
add_column('crop_history', 'soil_suitability', 'FLOAT')

# Pest Detections Table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pest_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path VARCHAR(200),
            result TEXT,
            severity VARCHAR(20),
            risk_score FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    print("Ensured pest_detections table exists")
except Exception as e:
    print(f"Error verifying pest_detections: {e}")

# Missing columns for Pest Detections
add_column('pest_detections', 'location', 'VARCHAR(100)')

conn.commit()
conn.close()
print("Migration script finished successfully!")
