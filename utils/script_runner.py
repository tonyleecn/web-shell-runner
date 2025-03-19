import os
import subprocess
import threading
from datetime import datetime

class ScriptRunner:
    @staticmethod
    def run_script(script_path, user=None, action=None, callback=None):
        """
        运行Shell脚本
        
        Args:
            script_path: 脚本的完整路径
            user: 可选的用户参数
            action: 可选的操作参数
            callback: 脚本执行完成后的回调函数
            
        Returns:
            process: 子进程对象
            output_thread: 输出线程
        """
        # 构建命令列表
        cmd = ['bash']
        cmd.append(script_path)
        
        if user:
            cmd.append(user)
        if action:
            cmd.append(action)

        # 设置执行环境
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = "1"
        env['LC_ALL'] = "C.UTF-8"
        env['LANG'] = "C.UTF-8"
        env['PATH'] = f"/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
        
        # 添加Flask特定的环境变量
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'production'
        env['FLASK_DEBUG'] = '0'
        
        # 移除可能导致问题的环境变量
        env.pop('WERKZEUG_SERVER_FD', None)
        env.pop('WERKZEUG_RUN_MAIN', None)
        
        # 使用 Popen 执行命令
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=os.path.dirname(script_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True
        )
        
        # 创建一个线程来处理输出
        def handle_output():
            output = []
            for line in process.stdout:
                output.append(line)
            
            stderr = []
            for line in process.stderr:
                stderr.append(line)
                
            return_code = process.wait()
            
            if callback:
                callback(return_code, ''.join(output), ''.join(stderr))
        
        output_thread = threading.Thread(target=handle_output)
        output_thread.start()
        
        return process, output_thread 