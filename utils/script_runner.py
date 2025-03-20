import os
import subprocess
import threading
import queue
from datetime import datetime


class ScriptRunner:
    # 存储脚本输出的队列字典
    output_queues = {}

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
            process_id: 进程ID
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
            start_new_session=True,
            bufsize=1  # 行缓冲
        )

        # 创建输出队列
        output_queue = queue.Queue()
        ScriptRunner.output_queues[process.pid] = output_queue

        # 创建一个线程来处理输出
        def handle_output():
            try:
                output = []
                # 确保逐行读取输出
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    output.append(line)
                    output_queue.put(('stdout', line))
                    print(f"STDOUT: {line.strip()}")

                stderr = []
                for line in iter(process.stderr.readline, ''):
                    if not line:
                        break
                    stderr.append(line)
                    output_queue.put(('stderr', line))
                    print(f"STDERR: {line.strip()}")

                # 确保在进程结束后发送退出码
                return_code = process.wait()
                output_queue.put(('exit', return_code))
                print(f"进程退出，返回码: {return_code}")

                if callback:
                    callback(return_code, ''.join(output), ''.join(stderr))
            except Exception as e:
                print(f"处理输出时出错: {e}")
                output_queue.put(('stderr', f"处理输出时出错: {str(e)}\n"))
                output_queue.put(('exit', -1))

        # 启动一个单独的线程来确保在主线程结束后发送退出码
        def ensure_exit_code():
            try:
                # 等待进程结束
                process.wait()
                # 检查队列中是否已有退出码
                has_exit_code = False

                # 修复这里的错误 - 不能直接遍历队列
                if process.pid in ScriptRunner.output_queues:
                    # 我们不能直接检查队列内容，所以添加一个标记
                    ScriptRunner.output_queues[process.pid].put(
                        ('exit', process.returncode))
                    print(f"确保进程 {process.pid} 的退出码: {process.returncode}")
            except Exception as e:
                print(f"确保退出码时出错: {e}")

        output_thread = threading.Thread(target=handle_output)
        output_thread.daemon = True
        output_thread.start()

        exit_thread = threading.Thread(target=ensure_exit_code)
        exit_thread.daemon = True
        exit_thread.start()

        return process, output_thread, process.pid

    @staticmethod
    def get_output(pid, timeout=0.1):
        """
        获取指定进程的输出

        Args:
            pid: 进程ID
            timeout: 队列等待超时时间

        Returns:
            list: 输出行列表
        """
        if pid not in ScriptRunner.output_queues:
            return []

        output_queue = ScriptRunner.output_queues[pid]
        output_lines = []

        try:
            # 尝试获取所有可用的输出行
            while True:
                try:
                    # 使用非阻塞模式获取队列项
                    line_type, line = output_queue.get(block=False)
                    output_lines.append((line_type, line))
                    output_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error getting output: {e}")

        return output_lines

    @staticmethod
    def cleanup_queue(pid):
        """
        清理指定进程的输出队列

        Args:
            pid: 进程ID
        """
        if pid in ScriptRunner.output_queues:
            del ScriptRunner.output_queues[pid]
