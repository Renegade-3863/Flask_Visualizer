import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from threading import Event
from flask import Flask
from flask import render_template
from flask import send_file
from flask import Response
from flask import jsonify
from flask import request
from flask import copy_current_request_context
import mimetypes
import matplotlib.pyplot
from concurrent.futures import ThreadPoolExecutor
# Use Redis to store the average high frequency falling time interval 
import redis

app = Flask(__name__)

# No need for a global results array
# results = []
matplotlib.use('Agg')  # Use the 'Agg' backend for non-interactive mode

# 设置要监控的目录
WATCH_DIRECTORY = os.path.expanduser("~/FYPfiles/venv/files")
app.config['UPLOAD_FOLDER'] = WATCH_DIRECTORY

# 存储检测到的文件
detected_files = []

# 创建一个事件对象来控制观察者
observer_event = Event()

# 创建一个全局变量来跟踪检测状态
detection_active = True

executor = ThreadPoolExecutor(max_workers=8)

# Handle redis connection, use the default localhost and port for testing
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Initialize the Redis configuration, reset corresponding data
def init_redis():
    # Don't Flush the database，this will destroy the RDB persistant sotrage
    # redis_client.flushdb()
    return

# 创建一个自定义事件处理器
# 个人认为本项目的处理流程并不需要用到 on_changed 方法，不过还是写入进来以防万一
class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            useless, file_extension = os.path.splitext(file_name)
            
            if file_extension == '.mp4':
                print(f"File {file_path} has been created")
                new_file = {
                    'name': file_name,
                    'path': os.path.relpath(file_path, WATCH_DIRECTORY),
                    'type': file_extension
                }
                if new_file not in detected_files:
                    detected_files.append(new_file)
                    # 检测到新文件后暂停观察者
                    observer_event.clear()
                    global detection_active
                    detection_active = False

                    date_str = file_name.split('_')[1]
                    time_str = file_name.split('_')[2]
                    # Need to remove the .mp4 suffix
                    time_str = time_str.replace('.mp4', '')
                    date = datetime.strptime(date_str, '%Y:%m:%d').date()
                    time = datetime.strptime(time_str, '%H:%M:%S').time()

                    # For testing purpose
                    print("When updating:\n")
                    print(date)
                    print(time)
                    
                    is_fall = 1 if 'FALL' in file_name else 0

                    # Update Redis if is_fall 
                    # No need to do extra useless work if is_fall == 0
                    if is_fall == 1:
                        redis_key = f"fall_data:{date}"
                        redis_client.hincrby(redis_key, (2*time.hour+1)/2, 1)

    def on_changed(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            useless, file_extension = os.path.splitext(file_name)

            if file_extension == '.mp4':
                print(f"File {file_path} has been changed")
                new_file = {
                    'name': file_name,
                    'path': os.path.relpath(file_path, WATCH_DIRECTORY),
                    'type': file_extension
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

    @copy_current_request_context
    def send_file_async(file_path, mime_type):
        return send_file(file_path, mimetype=mime_type, conditional=True)
    
    # 如果是视频文件，使用 send_file 并支持范围请求
    if mime_type and mime_type.startswith('video'):
        future = executor.submit(send_file_async, file_path, mime_type)
        return future.result()
        # return send_file(file_path, mimetype=mime_type, conditional=True)
    
    # 对于其他文件类型，使用 send_file
    future = executor.submit(send_file_async, file_path, None)
    return future.result()
    # return send_file(file_path, conditional=True)

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

@app.route('/get_detection_chart', methods=['GET'])
def get_detection_chart():
    # Acquire the current date information from the HTTP request header
    date_str = request.args.get('date')
    # For testing purpose
    print(date_str)

    # Defensive programming
    if not date_str:
        return jsonify({"status": "error", "message": "Invalid date format"})
    
    # Still defensive programming
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format"}) 

    # Retrieve data from Redis
    redis_key = f"fall_data:{date}"
    fall_data = redis_client.execute_command('HGETALL', redis_key)

    print(fall_data)
    # The fall_data consists of a list of key-value pairs, but in bytes format
    # We need to convert it to string format
    # fall_data = {fall_data[i].decode('utf-8'): fall_data[i+1].decode('utf-8') for i in range(0, len(fall_data), 2)}

    hours = list(range(24))
    # add 0.5 to each element of hours
    pts = [i+0.5 for i in range(24)]
    values = [int(fall_data.get(str(pt).encode('utf-8'), 0)) for pt in pts]

    # Print values in hours and values for testing
    print("Hours:", hours)
    print("Values:", values)

    matplotlib.pyplot.figure(figsize=(10, 5))
    matplotlib.pyplot.bar(pts, values)
    matplotlib.pyplot.xlabel('Hour')
    matplotlib.pyplot.ylabel('Number of Falls')
    matplotlib.pyplot.title(f'Falls on {date}')
    matplotlib.pyplot.grid(True)
    matplotlib.pyplot.xticks(hours)
    
    max_value = max(values) if values else 0
    matplotlib.pyplot.yticks(range(0, max_value+1))

    chart_path = 'static/detection_chart.png'
    matplotlib.pyplot.savefig(chart_path)
    matplotlib.pyplot.close()

    @copy_current_request_context
    def send_file_async(file_path, mime_type):
        return send_file(file_path, mimetype=mime_type, conditional=True)

    # 绘制完成，返回结果，不允许缓存
    return send_file_async(chart_path, 'image/png')
    # return send_file(chart_path, mimetype='image/png', max_age=0)

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
            return jsonify({"status": "success", "message": "file deleted"})
    return jsonify({"status": "error", "message": "file deletion failed"}), 400

@app.route('/pause_observation', methods=['POST'])
def pause_observation():
    global detection_active
    observer_event.clear()
    detection_active = False
    return jsonify({"status": "paused", "message": "observation is now suspended"})

if __name__ == '__main__':
    init_redis()
    Thread(target=start_observer).start()

    observer_event.set()

    app.run(debug=True, use_reloader=False)