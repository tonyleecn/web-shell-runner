from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Script(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    urls = db.Column(db.Text, nullable=True)  # 修改为URLs字段，存储多个URL
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)
    
    # 四种操作的脚本路径
    start_script = db.Column(db.String(255), nullable=True)
    stop_script = db.Column(db.String(255), nullable=True)
    restart_script = db.Column(db.String(255), nullable=True)
    deploy_script = db.Column(db.String(255), nullable=True)
    
    # 脚本参数
    start_user_param = db.Column(db.String(100), nullable=True)
    start_action_param = db.Column(db.String(100), nullable=True)
    stop_user_param = db.Column(db.String(100), nullable=True)
    stop_action_param = db.Column(db.String(100), nullable=True)
    restart_user_param = db.Column(db.String(100), nullable=True)
    restart_action_param = db.Column(db.String(100), nullable=True)
    deploy_user_param = db.Column(db.String(100), nullable=True)
    deploy_action_param = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Script {self.name}>' 