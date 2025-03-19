import os
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from models import db, Script
from config import Config
from utils.script_runner import ScriptRunner
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()

# 表单类
class ScriptForm(FlaskForm):
    name = StringField('服务名称', validators=[DataRequired()])
    urls = TextAreaField('应用访问URL')
    description = TextAreaField('描述')
    
    # 四种操作的脚本路径
    start_script = StringField('启动脚本路径')
    stop_script = StringField('停止脚本路径')
    restart_script = StringField('重启脚本路径')
    deploy_script = StringField('发布脚本路径')
    
    # 脚本参数
    start_user_param = StringField('启动用户参数')
    start_action_param = StringField('启动操作参数')
    stop_user_param = StringField('停止用户参数')
    stop_action_param = StringField('停止操作参数')
    restart_user_param = StringField('重启用户参数')
    restart_action_param = StringField('重启操作参数')
    deploy_user_param = StringField('发布用户参数')
    deploy_action_param = StringField('发布操作参数')
    
    submit = SubmitField('提交')
    
    def validate_start_script(self, field):
        if field.data and not os.path.isfile(field.data):
            raise ValidationError('启动脚本文件不存在')
    
    def validate_stop_script(self, field):
        if field.data and not os.path.isfile(field.data):
            raise ValidationError('停止脚本文件不存在')
    
    def validate_restart_script(self, field):
        if field.data and not os.path.isfile(field.data):
            raise ValidationError('重启脚本文件不存在')
    
    def validate_deploy_script(self, field):
        if field.data and not os.path.isfile(field.data):
            raise ValidationError('发布脚本文件不存在')

# 导入表单
class ImportForm(FlaskForm):
    file = FileField('导入文件', validators=[
        FileRequired(),
        FileAllowed(['json'], '只允许上传JSON文件')
    ])
    submit = SubmitField('导入')

# 路由
@app.route('/')
def index():
    scripts = Script.query.order_by(Script.position).all()
    return render_template('index.html', scripts=scripts)

@app.route('/add', methods=['GET', 'POST'])
def add_script():
    form = ScriptForm()
    if form.validate_on_submit():
        # 获取最大的 position 值
        max_position = db.session.query(db.func.max(Script.position)).scalar() or 0
        
        script = Script(
            name=form.name.data,
            urls=form.urls.data,
            description=form.description.data,
            position=max_position + 1,
            
            # 脚本路径
            start_script=form.start_script.data,
            stop_script=form.stop_script.data,
            restart_script=form.restart_script.data,
            deploy_script=form.deploy_script.data,
            
            # 脚本参数
            start_user_param=form.start_user_param.data,
            start_action_param=form.start_action_param.data,
            stop_user_param=form.stop_user_param.data,
            stop_action_param=form.stop_action_param.data,
            restart_user_param=form.restart_user_param.data,
            restart_action_param=form.restart_action_param.data,
            deploy_user_param=form.deploy_user_param.data,
            deploy_action_param=form.deploy_action_param.data
        )
        db.session.add(script)
        db.session.commit()
        flash('服务添加成功！')
        return redirect(url_for('index'))
    return render_template('add.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_script(id):
    script = Script.query.get_or_404(id)
    form = ScriptForm(obj=script)
    if form.validate_on_submit():
        script.name = form.name.data
        script.urls = form.urls.data
        script.description = form.description.data
        
        # 脚本路径
        script.start_script = form.start_script.data
        script.stop_script = form.stop_script.data
        script.restart_script = form.restart_script.data
        script.deploy_script = form.deploy_script.data
        
        # 脚本参数
        script.start_user_param = form.start_user_param.data
        script.start_action_param = form.start_action_param.data
        script.stop_user_param = form.stop_user_param.data
        script.stop_action_param = form.stop_action_param.data
        script.restart_user_param = form.restart_user_param.data
        script.restart_action_param = form.restart_action_param.data
        script.deploy_user_param = form.deploy_user_param.data
        script.deploy_action_param = form.deploy_action_param.data
        
        db.session.commit()
        flash('服务更新成功！')
        return redirect(url_for('index'))
    return render_template('edit.html', form=form, script=script)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_script(id):
    script = Script.query.get_or_404(id)
    db.session.delete(script)
    db.session.commit()
    flash('脚本删除成功！')
    return redirect(url_for('index'))

@app.route('/run/<int:id>/<string:operation>', methods=['POST'])
def run_script(id, operation):
    script = Script.query.get_or_404(id)
    
    # 根据操作类型选择对应的脚本和参数
    script_path = None
    user_param = None
    action_param = None
    
    if operation == 'start':
        script_path = script.start_script
        user_param = script.start_user_param
        action_param = script.start_action_param
    elif operation == 'stop':
        script_path = script.stop_script
        user_param = script.stop_user_param
        action_param = script.stop_action_param
    elif operation == 'restart':
        script_path = script.restart_script
        user_param = script.restart_user_param
        action_param = script.restart_action_param
    elif operation == 'deploy':
        script_path = script.deploy_script
        user_param = script.deploy_user_param
        action_param = script.deploy_action_param
    
    if not script_path:
        return jsonify({
            'status': 'error',
            'message': f'未设置 {operation} 脚本路径'
        }), 400
    
    # 运行脚本
    try:
        process, _ = ScriptRunner.run_script(script_path, user_param, action_param)
        return jsonify({
            'status': 'success',
            'message': f'服务 {script.name} 的 {operation} 操作正在执行',
            'pid': process.pid
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'运行脚本时出错: {str(e)}'
        }), 500

@app.route('/status/<int:pid>', methods=['GET'])
def script_status(pid):
    try:
        # 检查进程是否存在
        os.kill(pid, 0)
        return jsonify({'running': True})
    except OSError:
        return jsonify({'running': False})

@app.route('/reorder', methods=['POST'])
def reorder_scripts():
    try:
        # 获取排序后的脚本 ID 列表
        script_ids = request.json.get('scriptIds', [])
        
        # 更新每个脚本的 position
        for position, script_id in enumerate(script_ids):
            script = Script.query.get(script_id)
            if script:
                script.position = position
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 导出功能
@app.route('/export', methods=['GET'])
def export_scripts():
    try:
        scripts = Script.query.order_by(Script.position).all()
        
        # 将脚本数据转换为字典列表
        scripts_data = []
        for script in scripts:
            scripts_data.append({
                'name': script.name,
                'urls': script.urls,
                'description': script.description,
                'position': script.position,
                
                # 脚本路径
                'start_script': script.start_script,
                'stop_script': script.stop_script,
                'restart_script': script.restart_script,
                'deploy_script': script.deploy_script,
                
                # 脚本参数
                'start_user_param': script.start_user_param,
                'start_action_param': script.start_action_param,
                'stop_user_param': script.stop_user_param,
                'stop_action_param': script.stop_action_param,
                'restart_user_param': script.restart_user_param,
                'restart_action_param': script.restart_action_param,
                'deploy_user_param': script.deploy_user_param,
                'deploy_action_param': script.deploy_action_param
            })
        
        # 创建导出数据
        export_data = {
            'version': '1.0',
            'exported_at': datetime.datetime.now().isoformat(),
            'scripts': scripts_data
        }
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        
        # 写入JSON数据
        with open(temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # 发送文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'services_export_{timestamp}.json',
            mimetype='application/json'
        )
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('index'))

# 导入页面
@app.route('/import', methods=['GET', 'POST'])
def import_scripts():
    form = ImportForm()
    
    if form.validate_on_submit():
        try:
            # 读取上传的文件
            file = form.file.data
            content = file.read().decode('utf-8')
            data = json.loads(content)
            
            # 验证数据格式
            if 'version' not in data or 'scripts' not in data:
                flash('无效的导入文件格式', 'error')
                return redirect(url_for('import_scripts'))
            
            # 获取当前最大位置
            max_position = db.session.query(db.func.max(Script.position)).scalar() or 0
            
            # 导入脚本
            imported_count = 0
            for script_data in data['scripts']:
                # 检查是否已存在相同名称的服务
                existing_script = Script.query.filter_by(name=script_data['name']).first()
                
                # 检查脚本路径是否存在
                start_script = script_data.get('start_script', '')
                stop_script = script_data.get('stop_script', '')
                restart_script = script_data.get('restart_script', '')
                deploy_script = script_data.get('deploy_script', '')
                
                # 验证脚本路径
                if start_script and not os.path.isfile(start_script):
                    flash(f'启动脚本路径不存在: {start_script}', 'warning')
                    start_script = ''
                
                if stop_script and not os.path.isfile(stop_script):
                    flash(f'停止脚本路径不存在: {stop_script}', 'warning')
                    stop_script = ''
                
                if restart_script and not os.path.isfile(restart_script):
                    flash(f'重启脚本路径不存在: {restart_script}', 'warning')
                    restart_script = ''
                
                if deploy_script and not os.path.isfile(deploy_script):
                    flash(f'发布脚本路径不存在: {deploy_script}', 'warning')
                    deploy_script = ''
                
                if existing_script:
                    # 更新现有脚本
                    existing_script.urls = script_data.get('urls', '')
                    existing_script.description = script_data.get('description', '')
                    
                    # 脚本路径
                    existing_script.start_script = start_script
                    existing_script.stop_script = stop_script
                    existing_script.restart_script = restart_script
                    existing_script.deploy_script = deploy_script
                    
                    # 脚本参数
                    existing_script.start_user_param = script_data.get('start_user_param', '')
                    existing_script.start_action_param = script_data.get('start_action_param', '')
                    existing_script.stop_user_param = script_data.get('stop_user_param', '')
                    existing_script.stop_action_param = script_data.get('stop_action_param', '')
                    existing_script.restart_user_param = script_data.get('restart_user_param', '')
                    existing_script.restart_action_param = script_data.get('restart_action_param', '')
                    existing_script.deploy_user_param = script_data.get('deploy_user_param', '')
                    existing_script.deploy_action_param = script_data.get('deploy_action_param', '')
                else:
                    # 创建新脚本
                    script = Script(
                        name=script_data['name'],
                        urls=script_data.get('urls', ''),
                        description=script_data.get('description', ''),
                        position=max_position + 1 + imported_count,
                        
                        # 脚本路径
                        start_script=start_script,
                        stop_script=stop_script,
                        restart_script=restart_script,
                        deploy_script=deploy_script,
                        
                        # 脚本参数
                        start_user_param=script_data.get('start_user_param', ''),
                        start_action_param=script_data.get('start_action_param', ''),
                        stop_user_param=script_data.get('stop_user_param', ''),
                        stop_action_param=script_data.get('stop_action_param', ''),
                        restart_user_param=script_data.get('restart_user_param', ''),
                        restart_action_param=script_data.get('restart_action_param', ''),
                        deploy_user_param=script_data.get('deploy_user_param', ''),
                        deploy_action_param=script_data.get('deploy_action_param', '')
                    )
                    db.session.add(script)
                
                imported_count += 1
            
            db.session.commit()
            flash(f'成功导入 {imported_count} 个服务', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'error')
    
    return render_template('import.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4446, debug=True) 