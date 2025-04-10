import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
from flask import Flask, render_template, send_file, Response, jsonify, request
import mimetypes

app = Flask(__name__)

# 设置要监控的目录
WATCH_DIRECTORY = os.path.expanduser("~/FYPCodes/venv/files")
app.config['UPLOAD_FOLDER'] = WATCH_DIRECTORY

# 存储检测到的文件
detected_files = []

# 创建一个事件对象来控制观察者
observer_event = Event()

# 创建一个全局变量来跟踪检测状态
detection_active = True

# 创建一个自定义事件处理器
# 个人认为本项目的处理流程并不需要用到 on_changed 方法，不过还是写入进来以防万一
class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_name)
            
            if file_extension.lower() in ['.mp4', '.pdf', '.doc', '.docx', '.txt']:
                print(f"File {file_path} has been created")
                new_file = {
                    'name': file_name,
                    'path': os.path.relpath(file_path, WATCH_DIRECTORY),
                    'type': file_extension.lower()
                }
                if new_file not in detected_files:
                    detected_files.append(new_file)
                    # 检测到新文件后暂停观察者
                    observer_event.clear()
                    global detection_active
                    detection_active = False
    def on_changed(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_name)

            if file_extension.lower() in ['.mp4', '.pdf', '.doc', '.docx', '.txt']:
                print(f"File {file_path} has been changed")
                new_file = {
                    'name': file_name,
                    'path': os.path.relpath(file_path, WATCH_DIRECTORY),
                    'type': file_extension.lower()
                }
                if new_file not in detected_files:
                    detected_files.append(new_file)
                    # 检测到新文件后暂停观察者
                    observer_event.clear()
                    global detection_active
                    detection_active = False


# 创建观察者并启动
def start_observer():
    observer = Observer()
    event_handler = MyHandler()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
    observer.start()

    try:
        while True:
            if observer_event.is_set():
                time.sleep(1)
            else:
                observer_event.wait()
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

# Flask 路由
@app.route('/')
def index():
    return render_template('index.html', files=detected_files)

@app.route('/uploads/<path:filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # 获取文件的 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # 如果是视频文件，使用 send_file 并支持范围请求
    if mime_type and mime_type.startswith('video'):
        return send_file(file_path, mimetype=mime_type, conditional=True)
    
    # 对于其他文件类型，使用 send_file
    return send_file(file_path, conditional=True)

@app.route('/favicon.ico')
def favicon():
    return '', 200

@app.route('/resume_detection')
def resume_detection():
    global detection_active
    observer_event.set()
    detection_active = True
    return jsonify({"status": "resumed"})

@app.route('/get_new_files')
def get_new_files():
    global detection_active
    if detection_active:
        return jsonify(get_sorted_files())
    else:
        return jsonify({"status": "paused", "files": get_sorted_files()})

def get_sorted_files():
    files = []
    upload_folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        created_time = os.path.getctime(file_path)
        files.append({
            "name": filename,
            "path": filename,
            "type": os.path.splitext(filename)[1],
            "created_at": datetime.fromtimestamp(created_time).isoformat()
        })
    
    # 按创建时间降序排序
    return sorted(files, key=lambda x: x['created_at'], reverse=True)

@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_path = request.json.get('file_path')
    if file_path:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            global detected_files
            detected_files = [f for f in detected_files if f['path'] != file_path]
            return jsonify({"status": "success", "message": "文件已删除"})
    return jsonify({"status": "error", "message": "文件删除失败"}), 400

@app.route('/read_text_file/<path:filename>')
def read_text_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pause_observation', methods=['POST'])
def pause_observation():
    global detection_active
    observer_event.clear()
    detection_active = False
    return jsonify({"status": "paused", "message": "观察已手动暂停"})

if __name__ == '__main__':
    # 在单独的线程中启动文件系统观察者
    observer_thread = Thread(target=start_observer)
    observer_thread.start()

    # 初始化观察者为运行状态
    observer_event.set()

    # 启动 Flask 应用
    app.run(debug=True, use_reloader=False)