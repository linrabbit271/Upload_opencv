# TEMU 卖家中心全视觉自动导入系统 (TEMU Visual Upload System)

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/UI-PyQt6-orange.svg)](https://www.qt.io/)
[![Engine](https://img.shields.io/badge/Engine-OpenCV%20%2B%20PyAutoGUI-green.svg)](https://opencv.org/)

一个基于 **PyQt6** 现代化界面与 **OpenCV 像素矩阵匹配** 技术构建的硬核“全视觉”自动化轨迹文件导入系统。该系统彻底告别了传统 Tkinter 的简陋感，专门用于规避 TEMU 卖家中心客户端的死锁限制，通过模拟硬件层物理连招，实现全自动、高精度的文件批量轰炸式导入。

🚀 **[点此一键下载打包好的成品程序 (default.zip)](https://github.com/linrabbit271/Upload_opencv/releases/download/1/default.zip)**

---

## 🌟 核心技术亮点与“绝杀”机制

- **双图反向死锁防线**：内置独创的 10 分钟反向监测机制。系统在喂单后不会盲目等待固定时间，而是利用 OpenCV 像素雷达深度检索 TEMU 导入按钮的“亮橙常态色”。一旦服务端解析完毕、按钮复苏，系统瞬间轰碎死锁，流转下一单。
- **天才物理连招（盲喂技术）**：系统通过强锁键盘 `Alt + N` 砸向 Windows 文件选择器文件名输入框，配合高频模拟硬件打字及动态焦点下移技术，实现无需 API 接口的硬核底层文件塞入。
- **现代化 PyQt6 视图与多线程分离**：彻底重构了旧版的 Tkinter 外壳。采用纯正的 **信号与槽 (Signals and Slots)** 机制与 `QThread` 电控异步处理，确保在大批量 AI 像素匹配和重度 I/O 操作时，TEMU 自动化控制 GUI 界面丝滑流畅、绝不卡死。
- **特征资产实时渲染配置中心**：支持用户自主导入 4 组核心 TEMU 界面特征截图。右侧自带红绿灯状态点亮及等比例缩略图肉眼核对框，极大提升了跨屏幕、跨分辨率环境适配的弹性和容错率。
- **全局致命崩溃拦截**：挂载了最高优先级的 `global_main_crash_catcher` 运行时拦截器。一旦发生硬件电控或环境异常，自动抓取 Traceback 并通过图形化 `QMessageBox` 拦截报错，防止程序悄无声息地闪退。

---

## 📁 模块化项目架构

项目采用了典型的 **MVC/视图与引擎分离** 的高内聚低耦合设计。视觉识别的核心资产（`assets`）已完全规范化归档：

```text
Upload_opencv/
├── main.py                     # 总调度室：负责 QApplication 生命周期、三段式启动及所有 UI 布局
├── core/
│   └── vision_engine.py        # 核心引擎：负责 OpenCV 像素匹配、PyAutoGUI 硬件模拟及跨线程安全通讯
└── assets/                     # ⚙️ 核心视觉特征资产库（匹配 TEMU 系统界面）
    ├── 初始入口_按包裹号导入轨迹.png
    ├── 提交按钮_确认导入.png
    ├── 文件选择_进入文档文件夹.png
    └── 文件选择_轨迹表格挂载目录.png
