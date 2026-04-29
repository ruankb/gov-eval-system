import sqlite3
import json
from datetime import datetime

DB_PATH = "evaluation_history.db"


def init_db():
    """初始化数据库，创建所有必要的表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 评价记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            project_name TEXT,
            project_type TEXT,
            project_scale TEXT,
            security_level TEXT,
            filename TEXT,
            total_score REAL,
            scores_json TEXT,
            alerts_json TEXT,
            risks_json TEXT,
            extracted_budget REAL,
            iteration_name TEXT,
            iteration_version INTEGER
        )
    ''')
    
    # 语义组配置表（可自定义扩展）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semantic_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE,
            keywords TEXT,
            created_at TEXT
        )
    ''')
    
    # 项目类型权重表（可自定义）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_type TEXT,
            indicator TEXT,
            weight REAL,
            updated_at TEXT,
            UNIQUE(project_type, indicator)
        )
    ''')
    
    conn.commit()
    conn.close()


def save_evaluation(project_name, project_type, project_scale, security_level,
                    filename, total_score, scores, alerts, risks, extracted_budget,
                    iteration_name=None, iteration_version=None):
    """保存一次评价结果"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO evaluations 
        (timestamp, project_name, project_type, project_scale, security_level, 
         filename, total_score, scores_json, alerts_json, risks_json, extracted_budget,
         iteration_name, iteration_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        project_name,
        project_type,
        project_scale,
        security_level,
        filename,
        total_score,
        json.dumps(scores, ensure_ascii=False),
        json.dumps(alerts, ensure_ascii=False),
        json.dumps(risks, ensure_ascii=False),
        extracted_budget,
        iteration_name,
        iteration_version
    ))
    
    conn.commit()
    conn.close()


def get_history(project_name=None):
    """获取历史记录，可按项目名筛选"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if project_name:
        cursor.execute('''
            SELECT id, timestamp, project_name, project_type, project_scale, 
                   security_level, filename, total_score, scores_json, alerts_json, 
                   risks_json, extracted_budget, iteration_name, iteration_version
            FROM evaluations 
            WHERE project_name = ? 
            ORDER BY timestamp DESC
        ''', (project_name,))
    else:
        cursor.execute('''
            SELECT id, timestamp, project_name, project_type, project_scale, 
                   security_level, filename, total_score, scores_json, alerts_json, 
                   risks_json, extracted_budget, iteration_name, iteration_version
            FROM evaluations 
            ORDER BY timestamp DESC
        ''')
    
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_project_names():
    """获取所有项目名称列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT project_name FROM evaluations ORDER BY timestamp DESC')
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def get_iteration_history(iteration_name):
    """获取同一方案的迭代历史（按版本号排序）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT iteration_version, total_score, timestamp 
        FROM evaluations 
        WHERE iteration_name = ? AND iteration_version IS NOT NULL
        ORDER BY iteration_version ASC
    ''', (iteration_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_project_statistics(project_type=None):
    """获取项目统计信息（平均分、最高分、最低分、评价次数）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if project_type:
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                MIN(total_score) as min_score
            FROM evaluations 
            WHERE project_type = ?
        ''', (project_type,))
    else:
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                MIN(total_score) as min_score
            FROM evaluations
        ''')
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] > 0:
        return {
            "count": row[0],
            "avg_score": round(row[1], 2),
            "max_score": round(row[2], 2),
            "min_score": round(row[3], 2)
        }
    return None


def get_score_trend(project_name, limit=10):
    """获取某个项目的历史评分趋势"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, total_score, filename
        FROM evaluations 
        WHERE project_name = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (project_name, limit))
    rows = cursor.fetchall()
    conn.close()
    
    # 按时间正序返回
    return list(reversed(rows))


def delete_evaluation(eval_id):
    """删除指定的评价记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM evaluations WHERE id = ?', (eval_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


# ========== 语义组配置操作 ==========
def get_semantic_groups():
    """获取所有自定义语义组"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT group_name, keywords FROM semantic_groups')
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: json.loads(row[1]) for row in rows}


def save_semantic_group(group_name, keywords):
    """保存或更新语义组"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO semantic_groups (group_name, keywords, created_at)
        VALUES (?, ?, ?)
    ''', (group_name, json.dumps(keywords, ensure_ascii=False), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def delete_semantic_group(group_name):
    """删除语义组"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM semantic_groups WHERE group_name = ?', (group_name,))
    conn.commit()
    conn.close()


# ========== 权重配置操作 ==========
def get_project_weights(project_type):
    """获取指定项目类型的权重配置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT indicator, weight FROM project_weights 
        WHERE project_type = ?
    ''', (project_type,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def save_project_weight(project_type, indicator, weight):
    """保存或更新权重"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO project_weights (project_type, indicator, weight, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (project_type, indicator, weight, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def delete_project_weight(project_type, indicator):
    """删除权重配置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM project_weights 
        WHERE project_type = ? AND indicator = ?
    ''', (project_type, indicator))
    conn.commit()
    conn.close()