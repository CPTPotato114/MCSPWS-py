import mysql.connector
from mysql.connector import Error
import yaml  # 改用yaml解析器

def init_database():
    # 加载YAML配置
    with open('config/config.yml') as f:
        config = yaml.safe_load(f)
    
    db_config = config['database']

    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['db']}")
        
        # 创建状态记录表
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {db_config['db']}.server_status (
            id INT AUTO_INCREMENT PRIMARY KEY,
            server_address VARCHAR(255) NOT NULL,
            online BOOLEAN NOT NULL,
            players_online INT NOT NULL,
            players_max INT NOT NULL,
            motd TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建索引优化查询
        cursor.execute(f"""
        CREATE INDEX idx_server_timestamp 
        ON {db_config['db']}.server_status (server_address, timestamp)
        """)
        
        print("数据库初始化成功！")
        
    except Error as e:
        print(f"数据库错误: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_database()