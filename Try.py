import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
from flask import Flask, render_template, send_file, Response, jsonify
import mimetypes

app = Flask(__name__)

# 设置要监控的目录
WATCH_DIRECTORY = os.path.expanduser("~/FYPCodes/venv")
app.config['UPLOAD_FOLDER'] = WATCH_DIRECTORY

# 存储检测到的文件
detected_files = []

# 创建一个事件对象来控制观察者
observer_event = Event()

# 创建一个自定义事件处理器
class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_name)
            
            if file_extension.lower() in ['.mp4', '.pdf', '.doc', '.docx']:
                print(f"File {file_path} has been created")
                new_file = {
                    'name': file_name,
                    'path': os.path.relpath(file_path, WATCH_DIRECTORY),
                    'type': file_extension.lower()
                }
                if new_file not in detected_files:
                    detected_files.append(new_file)

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
    
    # 如果是视频文件，使用流式响应
    if mime_type and mime_type.startswith('video'):
        def generate():
            with open(file_path, 'rb') as video_file:
                data = video_file.read(1024 * 1024)  # 每次读取 1MB
                while data:
                    yield data
                    data = video_file.read(1024 * 1024)

        return Response(generate(), mimetype=mime_type)
    
    # 对于其他文件类型，使用 send_file
    return send_file(file_path, conditional=True)

@app.route('/favicon.ico')
def favicon():
    return '', 200

@app.route('/start_detection')
def start_detection():
    observer_event.set()
    return jsonify({"status": "started"})

@app.route('/get_new_files')
def get_new_files():
    return jsonify(detected_files)

if __name__ == '__main__':
    # 在单独的线程中启动文件系统观察者
    observer_thread = Thread(target=start_observer)
    observer_thread.start()

    # 初始化观察者为暂停状态
    observer_event.clear()

    # 启动 Flask 应用
    app.run(debug=True, use_reloader=False)