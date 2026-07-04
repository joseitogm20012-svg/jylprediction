import sqlite3
conn = sqlite3.connect(r'C:\Users\Equipo\Desktop\predecirv2\scrapycoco\scrapycoco.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, scraper_id, status, error_message, duration_ms FROM execution_history WHERE scraper_id='results' ORDER BY id DESC LIMIT 3").fetchall()
for r in rows:
    print(dict(r))
conn.close()
