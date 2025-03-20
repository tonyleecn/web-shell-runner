import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///scripts.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 脚本相关配置
    SCRIPTS_FOLDER = os.environ.get('SCRIPTS_FOLDER') or '/path/to/scripts' 