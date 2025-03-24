document.addEventListener('DOMContentLoaded', function() {
    // 删除脚本
    const deleteButtons = document.querySelectorAll('.delete-script');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteForm = document.getElementById('deleteForm');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const scriptId = this.getAttribute('data-id');
            deleteForm.action = `/delete/${scriptId}`;
            deleteModal.show();
        });
    });
    
    // 运行脚本
    const runButtons = document.querySelectorAll('.run-script');
    const runModal = new bootstrap.Modal(document.getElementById('runModal'));
    const runButton = document.getElementById('runButton');
    const runStatus = document.getElementById('runStatus');
    let currentScriptId = null;
    let currentOperation = null;
    let currentPid = null;
    let outputInterval = null;
    let outputContainer = null;
    
    runButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentScriptId = this.getAttribute('data-id');
            currentOperation = this.getAttribute('data-operation');
            runStatus.classList.add('d-none');
            runStatus.textContent = '';
            runButton.disabled = false;
            
            // 创建输出容器
            if (!outputContainer) {
                outputContainer = document.createElement('div');
                outputContainer.className = 'script-output mt-3 p-2 bg-dark text-light';
                outputContainer.style.height = '300px';
                outputContainer.style.overflowY = 'auto';
                outputContainer.style.fontFamily = 'monospace';
                outputContainer.style.fontSize = '0.9rem';
                outputContainer.style.whiteSpace = 'pre-wrap';
                outputContainer.style.display = 'none';
                
                // 添加到模态框
                document.querySelector('#runModal .modal-body').appendChild(outputContainer);
            }
            
            // 清空输出容器
            outputContainer.innerHTML = '';
            outputContainer.style.display = 'none';
            
            runModal.show();
        });
    });
    
    runButton.addEventListener('click', function() {
        runButton.disabled = true;
        runStatus.classList.remove('d-none');
        runStatus.textContent = '正在运行脚本...';
        runStatus.className = 'alert alert-info';
        
        // 显示输出容器
        outputContainer.style.display = 'block';
        outputContainer.innerHTML = '<div class="text-info">正在执行脚本，等待输出...</div>';
        
        fetch(`/run/${currentScriptId}/${currentOperation}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                runStatus.textContent = data.message;
                runStatus.className = 'alert alert-success';
                currentPid = data.pid;
                
                // 清除之前的定时器
                if (outputInterval) {
                    clearInterval(outputInterval);
                }
                
                // 定期获取脚本输出
                outputInterval = setInterval(() => {
                    fetchScriptOutput(currentPid);
                }, 1000);
            } else {
                runStatus.textContent = data.message;
                runStatus.className = 'alert alert-danger';
                runButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('运行脚本出错:', error);
            runStatus.textContent = '运行脚本时发生错误';
            runStatus.className = 'alert alert-danger';
            runButton.disabled = false;
        });
    });
    
    // 获取脚本输出
    function fetchScriptOutput(pid) {
        console.log(`获取PID ${pid}的输出`);
        fetch(`/script_output/${pid}`)
            .then(response => {
                console.log(`响应状态: ${response.status}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error(`响应内容: ${text}`);
                        throw new Error(`HTTP error! Status: ${response.status}, Body: ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('获取到输出数据:', data);
                
                // 检查是否有错误
                if (data.error) {
                    console.error('API返回错误:', data.error);
                    appendOutput(`\n获取输出时出错: ${data.error}`, 'text-danger');
                    clearInterval(outputInterval);
                    outputInterval = null;
                    runButton.disabled = false;
                    return;
                }
                
                if (data.output && data.output.length > 0) {
                    console.log(`处理 ${data.output.length} 行输出`);
                    
                    // 清空初始等待消息
                    if (outputContainer.querySelector('.text-info')) {
                        outputContainer.innerHTML = '';
                    }
                    
                    // 处理输出
                    let scriptCompleted = false;
                    
                    data.output.forEach(line => {
                        console.log('处理输出行:', line);
                        if (line.type === 'stdout') {
                            appendOutput(line.content, 'text-light');
                        } else if (line.type === 'stderr') {
                            appendOutput(line.content, 'text-danger');
                        } else if (line.type === 'exit') {
                            // 脚本执行完成
                            scriptCompleted = true;
                            clearInterval(outputInterval);
                            outputInterval = null;
                            
                            // 更新状态信息
                            if (line.code === 0) {
                                runStatus.textContent = `服务 ${getScriptName(currentScriptId)} 的 ${getOperationName(currentOperation)} 操作已成功完成`;
                                appendOutput('\n脚本执行成功 (退出码: 0)', 'text-success');
                            } else {
                                runStatus.textContent = `服务 ${getScriptName(currentScriptId)} 的 ${getOperationName(currentOperation)} 操作执行失败 (退出码: ${line.code})`;
                                runStatus.className = 'alert alert-warning';
                                appendOutput(`\n脚本执行失败 (退出码: ${line.code})`, 'text-warning');
                            }
                            
                            runButton.disabled = false;
                        }
                    });
                    
                    // 滚动到底部
                    outputContainer.scrollTop = outputContainer.scrollHeight;
                    
                    // 如果脚本已完成，不需要继续检查
                    if (scriptCompleted) {
                        return;
                    }
                } else {
                    console.log('没有新的输出');
                }
                
                // 检查进程是否仍在运行
                if (!data.running) {
                    console.log('进程已结束，但没有收到退出码');
                    // 如果进程已结束但没有收到退出码，可能是因为队列中没有捕获到exit事件
                    clearInterval(outputInterval);
                    outputInterval = null;
                    
                    if (outputContainer.querySelector('.text-info')) {
                        outputContainer.innerHTML = '';
                    }
                    
                    // 更新状态信息
                    runStatus.textContent = `服务 ${getScriptName(currentScriptId)} 的 ${getOperationName(currentOperation)} 操作已完成`;
                    appendOutput('\n脚本执行已完成，但未能获取退出状态', 'text-warning');
                    runButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('获取脚本输出出错:', error);
                clearInterval(outputInterval);
                outputInterval = null;
                appendOutput(`\n获取脚本输出时发生错误: ${error.message}`, 'text-danger');
                runButton.disabled = false;
            });
    }
    
    // 添加输出到容器
    function appendOutput(text, className) {
        console.log(`添加输出: ${text.substring(0, 30)}... (${className})`);
        const span = document.createElement('span');
        span.className = className;
        span.textContent = text;
        outputContainer.appendChild(span);
    }
    
    // 获取脚本名称
    function getScriptName(scriptId) {
        const scriptItem = document.querySelector(`.script-item[data-id="${scriptId}"]`);
        if (scriptItem) {
            const nameElement = scriptItem.querySelector('.card-header h5');
            if (nameElement) {
                return nameElement.textContent.trim();
            }
        }
        return '未知服务';
    }
    
    // 获取操作名称
    function getOperationName(operation) {
        const operationNames = {
            'start': '启动',
            'stop': '停止',
            'restart': '重启',
            'deploy': '发布'
        };
        return operationNames[operation] || operation;
    }
    
    // 关闭模态框时清理
    document.getElementById('runModal').addEventListener('hidden.bs.modal', function () {
        if (outputInterval) {
            clearInterval(outputInterval);
            outputInterval = null;
        }
    });
    
    // 拖拽排序功能
    const scriptList = document.getElementById('scriptList');
    if (scriptList) {
        const sortable = new Sortable(scriptList, {
            handle: '.handle',
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: function() {
                // 获取排序后的脚本 ID 列表
                const scriptIds = Array.from(scriptList.querySelectorAll('.script-item'))
                    .map(item => parseInt(item.getAttribute('data-id')));
                
                // 发送到服务器保存新的排序
                fetch('/reorder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ scriptIds: scriptIds })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status !== 'success') {
                        console.error('保存排序失败:', data.message);
                    }
                })
                .catch(error => {
                    console.error('保存排序出错:', error);
                });
            }
        });
    }
    
    // 端口状态刷新
    function refreshPortStatus() {
        const portBadges = document.querySelectorAll('.port-badge');
        
        portBadges.forEach(badge => {
            const scriptId = badge.getAttribute('data-script-id');
            
            fetch(`/check_ports/${scriptId}`)
                .then(response => response.json())
                .then(data => {
                    const port = badge.getAttribute('data-port');
                    const statusSpan = badge.querySelector('.port-status');
                    
                    if (data[port]) {
                        badge.classList.remove('bg-danger');
                        badge.classList.add('bg-success');
                        statusSpan.textContent = '开放';
                    } else {
                        badge.classList.remove('bg-success');
                        badge.classList.add('bg-danger');
                        statusSpan.textContent = '关闭';
                    }
                })
                .catch(error => {
                    console.error('检查端口状态出错:', error);
                });
        });
    }
    
    // 每3秒刷新一次端口状态
    if (document.querySelectorAll('.port-badge').length > 0) {
        setInterval(refreshPortStatus, 3000);
    }
    
    // 查看脚本内容
    const viewScriptButtons = document.querySelectorAll('.view-script');
    const viewScriptModal = new bootstrap.Modal(document.getElementById('viewScriptModal'));
    const scriptContent = document.getElementById('scriptContent');
    const scriptPath = document.getElementById('scriptPath');
    const copyScriptBtn = document.getElementById('copyScriptBtn');
    
    viewScriptButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const scriptId = this.getAttribute('data-id');
            const scriptType = this.getAttribute('data-type');
            const path = this.getAttribute('data-path');
            
            // 清空内容
            scriptContent.textContent = '加载中...';
            scriptPath.textContent = path;
            
            // 获取脚本内容
            fetch('/script_content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: path })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    scriptContent.textContent = data.content;
                    scriptPath.textContent = data.path;
                } else {
                    scriptContent.textContent = `获取脚本内容失败: ${data.message}`;
                }
            })
            .catch(error => {
                console.error('获取脚本内容出错:', error);
                scriptContent.textContent = `获取脚本内容出错: ${error.message}`;
            });
            
            viewScriptModal.show();
        });
    });
    
    // 复制脚本内容
    copyScriptBtn.addEventListener('click', function() {
        try {
            // 获取脚本内容
            const content = scriptContent.textContent;
            
            // 选择文本内容
            const range = document.createRange();
            range.selectNodeContents(scriptContent);
            
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            
            // 尝试复制
            const successful = document.execCommand('copy');
            
            // 清除选择
            selection.removeAllRanges();
            
            // 显示复制结果
            const originalText = this.innerHTML;
            if (successful) {
                this.innerHTML = '<i class="bi bi-check"></i> 已复制';
            } else {
                this.innerHTML = '<i class="bi bi-x"></i> 复制失败';
            }
            
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        } catch (err) {
            console.error('复制失败:', err);
            // 显示复制失败提示
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="bi bi-x"></i> 复制失败';
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        }
    });
}); 