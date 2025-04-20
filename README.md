# 基于 Python Flask 服务器架构与 HTML 网页渲染的视频检测可视化网页

这个项目是一个基于 Flask 的 Web 应用，用于实时监控指定目录中的新文件（特别是视频文件），并在 Web 界面上显示这些文件。它允许用户查看检测到的文件，播放视频，以及删除文件。

## 功能特点

- 实时监控指定目录中的新文件
- 支持检测和显示 MP4 视频文件
- 在 Web 界面上实时显示检测到的文件
- 允许用户播放视频文件
- 提供文件删除功能
- 可以暂停和恢复文件检测

## 技术栈

- 后端：Python Flask
- 前端：HTML, JavaScript, CSS
- 文件系统监控：Watchdog
- 文件存储：Redis 键值对数据库（单机，无 clustering）
- 持久化文件存储：Redis RDB 机制

## 安装要求

- Python 3.9 - 3.10（建议使用这个版本范围，更高版本可能导致部分库无法正常安装）
- Flask
- Watchdog
- Redis-server

## 安装步骤

1. 克隆此仓库到本地机器
2. 创建并激活虚拟环境（推荐，作者本人的测试环境就是 python3.9 venv）
3. 安装所需的 Python 包：

```bash
pip install flask watchdog
```
4. 安装 Redis 服务器（如果本机没有）
``` bash
brew instal redis  # On Mac
```
或者
``` bash 
apt install redis
```

## 使用方法
1. 设置要监控的目录： 在 Python 文件中修改 WATCH_DIRECTORY 变量为您想要监控的目录路径。
    - (默认为项目根目录下的 ～/FYPCodes/venv/files 文件夹，测试时可以把新文件放到这个目录下，目前支持 pdf, mp4, doc, txt 以及 docx 文件)
2. 使用本 github 仓库根目录下的 redis.conf 配置文件运行 redis-server。
``` bash
sudo redis-server ./redis.conf
```
- 或者，如果自己有兴趣，可以尝试 redis 的其它配置，修改 redis.conf 配置文件即可
- 这里推荐一款很好用的 Redis GUI 软件：Medis（仅限 Mac 端用户），这个应用提供了傻瓜式一键管理 Redis 数据库的界面
3. 运行 Flask 应用：
```bash
python Try.py # 如果你用的是 不同的 python 解释器，这里请切换成自己解释器的名字
```
- 或者用 VScode 自带的 python 解释器运行
4. 在本机浏览器中打开 http://localhost:5000 即可访问 web 界面。
5. 当新文件被添加到监控目录时，它们将自动显示在 Web 界面上。(网页会先提示用户有新文件产生，事件检测已停止)
6. 使用 Web 界面上的控件来播放视频、查看文档或删除文件。
7. 如果检测被暂停（当检测到新文件时会自动暂停），点击"继续检测"按钮来恢复检测。
8. 用户可以手动点击 "pause detection" 按钮来停止检测。
9. 每次有新的文件产生时，检测会自动暂停，直到用户点击"continue detection"按钮，系统才会继续检测。
-- - 
### 面向其它 project 添加的额外功能模块
- 针对小组开发的跌倒检测项目提供了额外的数据分析模块
- 网站接收到了跌倒视频数据，默认格式：
``` Python
date = datetime.strptime(date_str, '%Y:%m:%d').date()
time = datetime.strptime(time_str, '%H:%M:%S').time()
```
- 之后，会对文件的时间进行分块解析，并记录跌倒次数至 Redis 服务器，在网页端提供了可视化处理结果的按钮
-- -

## 注意事项
- 确保您有适当的权限来访问和修改监控的目录。
- 此应用目前配置为在开发模式下运行。在生产环境中使用时，请确保进行适当的安全配置。