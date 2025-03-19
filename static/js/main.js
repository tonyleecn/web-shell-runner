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
    
    runButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentScriptId = this.getAttribute('data-id');
            currentOperation = this.getAttribute('data-operation');
            runStatus.classList.add('d-none');
            runStatus.textContent = '';
            runButton.disabled = false;
            runModal.show();
        });
    });
    
    runButton.addEventListener('click', function() {
        runButton.disabled = true;
        runStatus.classList.remove('d-none');
        runStatus.textContent = '正在运行脚本...';
        runStatus.className = 'alert alert-info';
        
        fetch(`/run/${currentScriptId}/${currentOperation}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                runStatus.textContent = data.message;
                runStatus.className = 'alert alert-success';
                currentPid = data.pid;
                
                // 定期检查脚本状态
                const checkInterval = setInterval(() => {
                    fetch(`/status/${currentPid}`)
                        .then(response => response.json())
                        .then(statusData => {
                            if (!statusData.running) {
                                clearInterval(checkInterval);
                                runStatus.textContent = '脚本执行完成';
                                runButton.disabled = false;
                            }
                        })
                        .catch(error => {
                            console.error('检查状态出错:', error);
                            clearInterval(checkInterval);
                        });
                }, 2000);
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
}); 