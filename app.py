from flask import Flask, render_template
from flask_bootstrap import Bootstrap4
from apscheduler.schedulers.background import BackgroundScheduler
import yaml
import mysql.connector
from mcstatus import JavaServer
from modules.mc_formatter import mc_to_html

app = Flask(__name__)
app.config['BOOTSTRAP_BOOTSTRAP_VERSION'] = '5'  # 指定Bootstrap5
bootstrap = Bootstrap4(app)  # 使用Bootstrap4的类但实际使用Bootstrap5样式
app.jinja_env.filters['mc_to_html'] = mc_to_html

# 加载配置
with open('config/config.yml') as f:
    config = yaml.safe_load(f)

app.config.update(config['server'])

def get_db():
    return mysql.connector.connect(
        host=config['database']['host'],
        user=config['database']['user'],
        password=config['database']['password'],
        database=config['database']['db']
    )


def update_server_status():
    """定时更新服务器状态"""
    db = get_db()
    cursor = db.cursor()
    
    for server in config['servers']:
        try:
            mc_server = JavaServer.lookup(server['address'])
            status = mc_server.status()
            
            cursor.execute("""
                INSERT INTO server_status 
                (server_address, online, players_online, players_max, motd)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                server['address'],
                True,
                status.players.online,
                status.players.max,
                status.description
            ))
            
        except Exception as e:
            print(f"无法获取服务器 {server['address']} 状态: {e}")
            cursor.execute("""
                INSERT INTO server_status 
                (server_address, online, players_online, players_max, motd)
                VALUES (%s, %s, %s, %s, %s)
            """, (server['address'], False, 0, 0, "Offline"))
            
    db.commit()
    cursor.close()
    db.close()
    
# 配置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(update_server_status, 'interval', minutes=1)
scheduler.start()


# 每天凌晨清理旧数据
def clean_old_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM server_status 
        WHERE timestamp < DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    db.commit()
    cursor.close()
    db.close()

# 添加定时任务
scheduler.add_job(clean_old_data, 'cron', hour=3)


@app.route('/')
def index():
    return render_template(
        'index.html',
        site_info=config['site_info'],  # 网站信息
        servers=config['servers']      # 服务器列表
    )

@app.route('/status')
def server_status():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取最近状态
    status_data = {}
    for server in config['servers']:
        cursor.execute("""
            SELECT * FROM server_status 
            WHERE server_address = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (server['address'],))
        status_data[server['address']] = cursor.fetchone()
    
    #获取历史状态
    history_data = {}
    for server in config['servers']:
        # 读取配置
        hours = config.get('history', {}).get('hours', 48)
        # 动态生成查询语句
        cursor.execute(f"""
            SELECT 
                UNIX_TIMESTAMP(timestamp) * 1000 as timestamp_ms, 
                players_online,
                players_max,
                online
            FROM server_status
            WHERE 
                server_address = %s AND 
                timestamp > DATE_SUB(NOW(), INTERVAL {hours} HOUR)
            ORDER BY timestamp ASC
        """, (server['address'],))
        
        history_data[server['address']] = []
        for row in cursor:
            history_data[server['address']].append({
                "time": row['timestamp_ms'],
                "players": row['players_online'],
                "max": row['players_max'],
                "online": row['online']  # 携带在线状态
            })
    
    cursor.close()
    db.close()
    
    return render_template(
        'status.html',
        site_info=config['site_info'],
        servers=config['servers'],
        status_data=status_data,
        history_data=history_data
    )

if __name__ == '__main__':
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug']
    )

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error"}), 500