import sqlite3
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL is not None and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "user_data.db")

# Ensure the data directory exists
if not IS_POSTGRES:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    if IS_POSTGRES:
        import psycopg2.extras
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        return conn.cursor()

def execute_sql(cursor, sql, params=()):
    if IS_POSTGRES:
        # Convert ? parameters to %s for PostgreSQL
        sql = sql.replace("?", "%s")
        # Convert SQLite autoincrement to PostgreSQL serial
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        
        # Convert INSERT OR REPLACE specifically
        if "INSERT OR REPLACE INTO match_votes" in sql:
            sql = """
            INSERT INTO match_votes (match_key, user_id, vote, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_key, user_id) 
            DO UPDATE SET vote = EXCLUDED.vote, created_at = EXCLUDED.created_at
            """
            
        # Convert UPSERT syntax for points addition
        if "ON CONFLICT(user_id) DO UPDATE SET" in sql:
            if "points = points + %s" in sql or "points = points + ?" in sql:
                sql = """
                INSERT INTO leaderboard (user_id, username, points)
                VALUES (%s, %s, %s)
                ON CONFLICT(user_id) DO UPDATE SET 
                    points = leaderboard.points + EXCLUDED.points,
                    username = EXCLUDED.username
                """
    cursor.execute(sql, params)
    return cursor

def init_db():
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    # 1. Favorites Table
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        team_a TEXT NOT NULL,
        team_b TEXT NOT NULL,
        xg_a REAL,
        xg_b REAL,
        prob_a REAL,
        prob_draw REAL,
        prob_b REAL,
        notes TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. User Presets Table
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS user_presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        preset_name TEXT NOT NULL,
        fifa_weight REAL NOT NULL,
        h2h_weight REAL NOT NULL,
        decay REAL NOT NULL,
        override_a REAL NOT NULL,
        override_b REAL NOT NULL,
        altitude INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 3. Match Votes Table (Community Pre-match polls)
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS match_votes (
        match_key TEXT NOT NULL,
        user_id TEXT NOT NULL,
        vote TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (match_key, user_id)
    )
    """)
    
    # 4. User Pronostics Table (For Leaderboard guesses)
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS user_pronostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        team_a TEXT NOT NULL,
        team_b TEXT NOT NULL,
        match_key TEXT NOT NULL,
        guess TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        is_correct INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)
    
    # 5. Leaderboard Table
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        points INTEGER DEFAULT 0
    )
    """)
    
    # 6. AI Analyses Table
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS ai_analyses (
        id BIGINT PRIMARY KEY,
        match_key TEXT NOT NULL,
        team_a TEXT NOT NULL,
        team_b TEXT NOT NULL,
        analysis_text TEXT NOT NULL,
        key_tips TEXT,
        confidence INTEGER,
        predicted_score TEXT,
        model_name TEXT,
        stage TEXT,
        key_players TEXT,
        odds_a REAL,
        odds_draw REAL,
        odds_b REAL,
        odds TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)
    
    # 7. Logged Predictions Table (For tracking predictions and their results)
    execute_sql(cursor, """
    CREATE TABLE IF NOT EXISTS logged_predictions (
        id BIGINT PRIMARY KEY,
        team_a TEXT NOT NULL,
        team_b TEXT NOT NULL,
        prob_win_a REAL NOT NULL,
        prob_draw REAL NOT NULL,
        prob_win_b REAL NOT NULL,
        xg_a REAL NOT NULL,
        xg_b REAL NOT NULL,
        strength_override_a REAL NOT NULL,
        strength_override_b REAL NOT NULL,
        altitude INTEGER NOT NULL,
        actual_result TEXT,
        actual_score TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        is_correct INTEGER,
        pick TEXT,
        rps REAL,
        timestamp TEXT NOT NULL,
        date TEXT NOT NULL
    )
    """)
    
    try:
        migrate_ai_analyses_from_json(cursor)
    except Exception as e:
        print("Error executing migrate_ai_analyses_from_json:", str(e))
        
    try:
        migrate_logged_predictions_from_json(cursor)
    except Exception as e:
        print("Error executing migrate_logged_predictions_from_json:", str(e))
        
    conn.commit()
    conn.close()

def get_match_key(team_a: str, team_b: str) -> str:
    sorted_teams = sorted([team_a.strip().lower(), team_b.strip().lower()])
    return f"{sorted_teams[0]}_vs_{sorted_teams[1]}"

# ==========================================
# FAVORITES CRUD
# ==========================================
def add_favorite(user_id: str, team_a: str, team_b: str, xg_a: float, xg_b: float, prob_a: float, prob_draw: float, prob_b: float, notes: str):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    created_at = datetime.now().isoformat()
    
    sql = """
    INSERT INTO favorites (user_id, team_a, team_b, xg_a, xg_b, prob_a, prob_draw, prob_b, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    if IS_POSTGRES:
        sql = sql.replace("?", "%s") + " RETURNING id"
        cursor.execute(sql, (user_id, team_a, team_b, xg_a, xg_b, prob_a, prob_draw, prob_b, notes, created_at))
        fav_id = cursor.fetchone()[0]
    else:
        cursor.execute(sql, (user_id, team_a, team_b, xg_a, xg_b, prob_a, prob_draw, prob_b, notes, created_at))
        fav_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return fav_id

def get_user_favorites(user_id: str):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT * FROM favorites WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_favorite(user_id: str, favorite_id: int) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "DELETE FROM favorites WHERE user_id = ? AND id = ?", (user_id, favorite_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# ==========================================
# CUSTOM PRESETS CRUD
# ==========================================
def add_user_preset(user_id: str, preset_name: str, fifa_weight: float, h2h_weight: float, decay: float, override_a: float, override_b: float, altitude: int):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    created_at = datetime.now().isoformat()
    
    sql = """
    INSERT INTO user_presets (user_id, preset_name, fifa_weight, h2h_weight, decay, override_a, override_b, altitude, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    if IS_POSTGRES:
        sql = sql.replace("?", "%s") + " RETURNING id"
        cursor.execute(sql, (user_id, preset_name, fifa_weight, h2h_weight, decay, override_a, override_b, altitude, created_at))
        preset_id = cursor.fetchone()[0]
    else:
        cursor.execute(sql, (user_id, preset_name, fifa_weight, h2h_weight, decay, override_a, override_b, altitude, created_at))
        preset_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return preset_id

def get_user_presets(user_id: str):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT * FROM user_presets WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user_preset(user_id: str, preset_id: int) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "DELETE FROM user_presets WHERE user_id = ? AND id = ?", (user_id, preset_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# ==========================================
# MATCH POLL VOTES
# ==========================================
def cast_vote(match_key: str, user_id: str, vote: str) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    created_at = datetime.now().isoformat()
    try:
        execute_sql(cursor, """
        INSERT OR REPLACE INTO match_votes (match_key, user_id, vote, created_at)
        VALUES (?, ?, ?, ?)
        """, (match_key, user_id, vote, created_at))
        conn.commit()
        success = True
    except Exception as e:
        print("Error voting:", e)
        success = False
    finally:
        conn.close()
    return success

def get_match_votes_stats(match_key: str):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, """
    SELECT vote, COUNT(*) as cnt 
    FROM match_votes 
    WHERE match_key = ? 
    GROUP BY vote
    """, (match_key,))
    rows = cursor.fetchall()
    conn.close()
    
    stats = {"A": 0, "Draw": 0, "B": 0}
    total = 0
    for r in rows:
        stats[r["vote"]] = r["cnt"]
        total += r["cnt"]
        
    percentages = {"A": 0, "Draw": 0, "B": 0}
    if total > 0:
        percentages["A"] = round((stats["A"] / total) * 100)
        percentages["Draw"] = round((stats["Draw"] / total) * 100)
        percentages["B"] = round((stats["B"] / total) * 100)
        
    return {
        "votes": stats,
        "percentages": percentages,
        "total": total
    }

def get_user_vote_for_match(match_key: str, user_id: str):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT vote FROM match_votes WHERE match_key = ? AND user_id = ?", (match_key, user_id))
    row = cursor.fetchone()
    conn.close()
    return row["vote"] if row else None

# ==========================================
# OFFICIAL PRONOSTICS & LEADERBOARD
# ==========================================
def register_official_pronostic(user_id: str, username: str, team_a: str, team_b: str, guess: str) -> bool:
    match_key = get_match_key(team_a, team_b)
    conn = get_db_connection()
    cursor = get_cursor(conn)
    created_at = datetime.now().isoformat()
    
    execute_sql(cursor, """
    SELECT id FROM user_pronostics 
    WHERE user_id = ? AND match_key = ? AND status = 'pending'
    """, (user_id, match_key))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return False
        
    try:
        execute_sql(cursor, """
        INSERT INTO user_pronostics (user_id, username, team_a, team_b, match_key, guess, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, team_a, team_b, match_key, guess, created_at))
        conn.commit()
        success = True
    except Exception as e:
        print("Error registering pronostic:", e)
        success = False
    finally:
        conn.close()
    return success

def get_user_match_pronostic(user_id: str, team_a: str, team_b: str):
    match_key = get_match_key(team_a, team_b)
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, """
    SELECT guess, status, is_correct FROM user_pronostics 
    WHERE user_id = ? AND match_key = ?
    ORDER BY id DESC LIMIT 1
    """, (user_id, match_key))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_leaderboard_rankings():
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT * FROM leaderboard ORDER BY points DESC, username ASC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_user_pronostics(team_a: str, team_b: str, actual_outcome: str):
    match_key = get_match_key(team_a, team_b)
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    execute_sql(cursor, """
    SELECT id, user_id, username, guess FROM user_pronostics 
    WHERE match_key = ? AND status = 'pending'
    """, (match_key,))
    pronostics = cursor.fetchall()
    
    for p in pronostics:
        p_id = p["id"]
        user_id = p["user_id"]
        username = p["username"]
        guess = p["guess"]
        
        is_correct = 1 if guess == actual_outcome else 0
        points_to_add = 10 if is_correct == 1 else 0
        
        execute_sql(cursor, """
        UPDATE user_pronostics 
        SET status = 'completed', is_correct = ? 
        WHERE id = ?
        """, (is_correct, p_id))
        
        if points_to_add > 0:
            execute_sql(cursor, """
            INSERT INTO leaderboard (user_id, username, points)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                points = points + ?,
                username = EXCLUDED.username
            """, (user_id, username, points_to_add, points_to_add))
        else:
            execute_sql(cursor, """
            INSERT INTO leaderboard (user_id, username, points)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO NOTHING
            """, (user_id, username))
            
    conn.commit()
    conn.close()

# ==========================================
# AI ANALYSES CRUD
# ==========================================
def migrate_ai_analyses_from_json(cursor):
    import json
    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM ai_analyses")
    count = cursor.fetchone()[0]
    if count > 0:
        return # Already migrated
        
    ai_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ai_analyses.json")
    if os.path.exists(ai_json_path):
        try:
            with open(ai_json_path, "r", encoding="utf-8") as f:
                analyses = json.load(f)
            
            for item in analyses:
                sql = """
                INSERT INTO ai_analyses (
                    id, match_key, team_a, team_b, analysis_text, key_tips, confidence, 
                    predicted_score, model_name, stage, key_players, odds_a, odds_draw, odds_b, odds, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                if IS_POSTGRES:
                    sql = sql.replace("?", "%s")
                    
                key_tips_str = json.dumps(item.get("key_tips", []))
                odds_str = json.dumps(item.get("odds", {}))
                
                cursor.execute(sql, (
                    item.get("id"),
                    item.get("match_key"),
                    item.get("teamA"),
                    item.get("teamB"),
                    item.get("analysis_text"),
                    key_tips_str,
                    item.get("confidence"),
                    item.get("predicted_score"),
                    item.get("model_name"),
                    item.get("stage", "Fase de Grupos"),
                    item.get("key_players", ""),
                    item.get("odds_a"),
                    item.get("odds_draw"),
                    item.get("odds_b"),
                    odds_str,
                    item.get("created_at", datetime.now().isoformat()),
                    item.get("updated_at")
                ))
            print(f"Successfully migrated {len(analyses)} AI analyses from JSON to database.")
        except Exception as e:
            print("Error during migration of AI analyses:", str(e))

def db_get_all_ai_analyses():
    import json
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT * FROM ai_analyses ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["key_tips"] = json.loads(item["key_tips"]) if item.get("key_tips") else []
        except:
            item["key_tips"] = []
            
        try:
            item["odds"] = json.loads(item["odds"]) if item.get("odds") else {}
        except:
            item["odds"] = {}
            
        results.append({
            "id": item["id"],
            "teamA": item["team_a"],
            "teamB": item["team_b"],
            "match_key": item["match_key"],
            "analysis_text": item["analysis_text"],
            "key_tips": item["key_tips"],
            "confidence": item["confidence"],
            "predicted_score": item["predicted_score"],
            "model_name": item["model_name"],
            "stage": item["stage"],
            "key_players": item["key_players"],
            "odds_a": item["odds_a"],
            "odds_draw": item["odds_draw"],
            "odds_b": item["odds_b"],
            "odds": item["odds"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"]
        })
    return results

def db_get_ai_analysis(team_a: str, team_b: str):
    import json
    conn = get_db_connection()
    cursor = get_cursor(conn)
    match_key = f"{min(team_a, team_b)}-{max(team_a, team_b)}"
    
    execute_sql(cursor, "SELECT * FROM ai_analyses WHERE match_key = ?", (match_key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    item = dict(row)
    try:
        item["key_tips"] = json.loads(item["key_tips"]) if item.get("key_tips") else []
    except:
        item["key_tips"] = []
        
    try:
        item["odds"] = json.loads(item["odds"]) if item.get("odds") else {}
    except:
        item["odds"] = {}
        
    return {
        "id": item["id"],
        "teamA": item["team_a"],
        "teamB": item["team_b"],
        "match_key": item["match_key"],
        "analysis_text": item["analysis_text"],
        "key_tips": item["key_tips"],
        "confidence": item["confidence"],
        "predicted_score": item["predicted_score"],
        "model_name": item["model_name"],
        "stage": item["stage"],
        "key_players": item["key_players"],
        "odds_a": item["odds_a"],
        "odds_draw": item["odds_draw"],
        "odds_b": item["odds_b"],
        "odds": item["odds"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"]
    }

def db_save_ai_analysis(req_data: dict) -> dict:
    import json
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    team_a = req_data["teamA"]
    team_b = req_data["teamB"]
    match_key = f"{min(team_a, team_b)}-{max(team_a, team_b)}"
    
    existing_id = req_data.get("id")
    if existing_id:
        execute_sql(cursor, "SELECT id FROM ai_analyses WHERE id = ?", (existing_id,))
        row = cursor.fetchone()
    else:
        execute_sql(cursor, "SELECT id FROM ai_analyses WHERE match_key = ?", (match_key,))
        row = cursor.fetchone()
        
    key_tips_str = json.dumps(req_data.get("keyTips", []))
    odds_str = json.dumps(req_data.get("odds", {}))
    now_str = datetime.now().isoformat()
    
    if row:
        saved_id = row[0]
        sql = """
        UPDATE ai_analyses SET 
            team_a = ?, team_b = ?, match_key = ?, analysis_text = ?, key_tips = ?, 
            confidence = ?, predicted_score = ?, model_name = ?, stage = ?, key_players = ?, 
            odds_a = ?, odds_draw = ?, odds_b = ?, odds = ?, updated_at = ?
        WHERE id = ?
        """
        if IS_POSTGRES:
            sql = sql.replace("?", "%s")
        cursor.execute(sql, (
            team_a, team_b, match_key, req_data["analysisText"], key_tips_str,
            req_data["confidence"], req_data["predictedScore"], req_data["modelName"],
            req_data.get("stage", "Fase de Grupos"), req_data.get("keyPlayers", ""),
            req_data.get("oddsA"), req_data.get("oddsDraw"), req_data.get("oddsB"),
            odds_str, now_str, saved_id
        ))
        created_at_val = now_str
    else:
        saved_id = req_data.get("id") if req_data.get("id") else int(datetime.now().timestamp() * 1000)
        sql = """
        INSERT INTO ai_analyses (
            id, match_key, team_a, team_b, analysis_text, key_tips, confidence, 
            predicted_score, model_name, stage, key_players, odds_a, odds_draw, odds_b, odds, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        if IS_POSTGRES:
            sql = sql.replace("?", "%s")
        cursor.execute(sql, (
            saved_id, match_key, team_a, team_b, req_data["analysisText"], key_tips_str,
            req_data["confidence"], req_data["predictedScore"], req_data["modelName"],
            req_data.get("stage", "Fase de Grupos"), req_data.get("keyPlayers", ""),
            req_data.get("oddsA"), req_data.get("oddsDraw"), req_data.get("oddsB"),
            odds_str, now_str, None
        ))
        created_at_val = now_str
        
    conn.commit()
    conn.close()
    
    return {
        "id": saved_id,
        "teamA": team_a,
        "teamB": team_b,
        "match_key": match_key,
        "analysis_text": req_data["analysisText"],
        "key_tips": req_data.get("keyTips", []),
        "confidence": req_data["confidence"],
        "predicted_score": req_data["predictedScore"],
        "model_name": req_data["modelName"],
        "stage": req_data.get("stage", "Fase de Grupos"),
        "key_players": req_data.get("keyPlayers", ""),
        "odds_a": req_data.get("oddsA"),
        "odds_draw": req_data.get("oddsDraw"),
        "odds_b": req_data.get("oddsB"),
        "odds": req_data.get("odds", {}),
        "created_at": created_at_val,
        "updated_at": now_str
    }

def db_delete_ai_analysis(analysis_id: int) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    execute_sql(cursor, "SELECT id FROM ai_analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
        
    execute_sql(cursor, "DELETE FROM ai_analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()
    return True

# ==========================================
# LOGGED PREDICTIONS CRUD
# ==========================================
def migrate_logged_predictions_from_json(cursor):
    import json
    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM logged_predictions")
    count = cursor.fetchone()[0]
    if count > 0:
        return  # Already migrated
    
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logged_predictions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                predictions = json.load(f)
            
            for item in predictions:
                sql = """
                INSERT INTO logged_predictions (
                    id, team_a, team_b, prob_win_a, prob_draw, prob_win_b,
                    xg_a, xg_b, strength_override_a, strength_override_b,
                    altitude, actual_result, actual_score, status, is_correct,
                    pick, rps, timestamp, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                if IS_POSTGRES:
                    sql = sql.replace("?", "%s")
                
                cursor.execute(sql, (
                    item.get("id"),
                    item.get("teamA"),
                    item.get("teamB"),
                    item.get("probWinA"),
                    item.get("probDraw"),
                    item.get("probWinB"),
                    item.get("xgA"),
                    item.get("xgB"),
                    item.get("strengthOverrideA"),
                    item.get("strengthOverrideB"),
                    item.get("altitude", 0),
                    item.get("actualResult"),
                    item.get("actualScore"),
                    item.get("status", "pending"),
                    1 if item.get("isCorrect") else 0 if item.get("isCorrect") is not None else None,
                    item.get("pick"),
                    item.get("rps"),
                    item.get("timestamp"),
                    item.get("date")
                ))
            print(f"Successfully migrated {len(predictions)} logged predictions from JSON to database.")
        except Exception as e:
            print("Error during migration of logged predictions:", str(e))

def db_get_all_logged_predictions():
    conn = get_db_connection()
    cursor = get_cursor(conn)
    execute_sql(cursor, "SELECT * FROM logged_predictions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        results.append({
            "id": item["id"],
            "teamA": item["team_a"],
            "teamB": item["team_b"],
            "probWinA": item["prob_win_a"],
            "probDraw": item["prob_draw"],
            "probWinB": item["prob_win_b"],
            "xgA": item["xg_a"],
            "xgB": item["xg_b"],
            "strengthOverrideA": item["strength_override_a"],
            "strengthOverrideB": item["strength_override_b"],
            "altitude": item["altitude"],
            "actualResult": item["actual_result"],
            "actualScore": item["actual_score"],
            "status": item["status"],
            "isCorrect": bool(item["is_correct"]) if item["is_correct"] is not None else None,
            "pick": item["pick"],
            "rps": item["rps"],
            "timestamp": item["timestamp"],
            "date": item["date"]
        })
    return results

def db_save_logged_prediction(req_data: dict) -> dict:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    now_str = datetime.now().isoformat()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    sql = """
    INSERT INTO logged_predictions (
        id, team_a, team_b, prob_win_a, prob_draw, prob_win_b,
        xg_a, xg_b, strength_override_a, strength_override_b,
        altitude, actual_result, actual_score, status, is_correct,
        pick, rps, timestamp, date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    if IS_POSTGRES:
        sql = sql.replace("?", "%s")
    
    pred_id = req_data.get("id", int(datetime.now().timestamp() * 1000))
    
    cursor.execute(sql, (
        pred_id,
        req_data["teamA"],
        req_data["teamB"],
        req_data["probWinA"],
        req_data["probDraw"],
        req_data["probWinB"],
        req_data["xgA"],
        req_data["xgB"],
        req_data["strengthOverrideA"],
        req_data["strengthOverrideB"],
        req_data.get("altitude", 0),
        req_data.get("actualResult"),
        req_data.get("actualScore"),
        req_data.get("status", "pending"),
        1 if req_data.get("isCorrect") else 0 if req_data.get("isCorrect") is not None else None,
        req_data.get("pick"),
        req_data.get("rps"),
        req_data.get("timestamp", now_str),
        req_data.get("date", date_str)
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "id": pred_id,
        "teamA": req_data["teamA"],
        "teamB": req_data["teamB"],
        "probWinA": req_data["probWinA"],
        "probDraw": req_data["probDraw"],
        "probWinB": req_data["probWinB"],
        "xgA": req_data["xgA"],
        "xgB": req_data["xgB"],
        "strengthOverrideA": req_data["strengthOverrideA"],
        "strengthOverrideB": req_data["strengthOverrideB"],
        "altitude": req_data.get("altitude", 0),
        "actualResult": req_data.get("actualResult"),
        "actualScore": req_data.get("actualScore"),
        "status": req_data.get("status", "pending"),
        "isCorrect": req_data.get("isCorrect"),
        "pick": req_data.get("pick"),
        "rps": req_data.get("rps"),
        "timestamp": req_data.get("timestamp", now_str),
        "date": req_data.get("date", date_str)
    }

def db_update_logged_prediction(pred_id: int, updates: dict) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    # Build dynamic UPDATE statement
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        col_name = key
        if key == "teamA":
            col_name = "team_a"
        elif key == "teamB":
            col_name = "team_b"
        elif key == "probWinA":
            col_name = "prob_win_a"
        elif key == "probDraw":
            col_name = "prob_draw"
        elif key == "probWinB":
            col_name = "prob_win_b"
        elif key == "xgA":
            col_name = "xg_a"
        elif key == "xgB":
            col_name = "xg_b"
        elif key == "strengthOverrideA":
            col_name = "strength_override_a"
        elif key == "strengthOverrideB":
            col_name = "strength_override_b"
        elif key == "actualResult":
            col_name = "actual_result"
        elif key == "actualScore":
            col_name = "actual_score"
        elif key == "isCorrect":
            col_name = "is_correct"
            value = 1 if value else 0 if value is not None else None
        
        set_clauses.append(f"{col_name} = ?")
        params.append(value)
    
    if not set_clauses:
        conn.close()
        return False
    
    params.append(pred_id)
    
    sql = f"UPDATE logged_predictions SET {', '.join(set_clauses)} WHERE id = ?"
    if IS_POSTGRES:
        sql = sql.replace("?", "%s")
    
    cursor.execute(sql, tuple(params))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def db_delete_logged_prediction(pred_id: int) -> bool:
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    execute_sql(cursor, "SELECT id FROM logged_predictions WHERE id = ?", (pred_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
        
    execute_sql(cursor, "DELETE FROM logged_predictions WHERE id = ?", (pred_id,))
    conn.commit()
    conn.close()
    return True

# Initialize tables
init_db()
