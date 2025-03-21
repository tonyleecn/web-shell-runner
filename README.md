# 脚本管理系统

这是一个简单的服务器脚本（.sh文件）运行系统，允许用户执行服务器脚本，并查看执行结果。程序未经详细测试，用来测试服务的发布，请勿在生产环境中使用。解决运行脚本环境不同导致脚本运行错误。

## 功能特点

- 服务脚本执行
- 拖拽排序功能

## 技术栈

- 后端：Python Flask
- 前端：HTML, CSS, JavaScript
- 数据库：SQLite
- UI框架：Bootstrap

## 截图展示

### 主界面
![主界面](demo-page/首页.png)

### 脚本执行
![脚本执行](demo-page/添加服务.png)

## 安装步骤

### 前提条件

- Python 3.7+
- pip (Python包管理器)

### 安装过程

1. **克隆仓库**
   ```bash
   git clone https://github.com/tonyleecn/web-shell-runner.git
   cd web-shell-runner
   ```

2. **安装依赖**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **运行项目**
   ```bash
   python app.py
   ```

4. **访问项目**
   ```
   http://localhost:4446
   ```

## 注意事项

- 本项目仅用于测试和学习目的
- 不建议在生产环境中使用
- 确保脚本执行权限设置正确

