import sys
import os
import threading
import traceback
import re
import time

# 自动将当前项目根目录加入环境变量
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFrame, QLineEdit,
                             QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QFileDialog, QDialog, QTextEdit, QStyle)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor


# ---------------- 核心运行时崩溃强制拦截 ----------------
def global_main_crash_catcher(exctype, value, tb):
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    print("🚨 [CRASH]:\n", err_msg)
    try:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("插件运行异常拦截")
        error_box.setText("⚠️ 触发致命运行时错误！")
        error_box.setInformativeText(err_msg[:500])
        error_box.exec()
    except:
        pass
    sys.__excepthook__(exctype, value, tb)


sys.excepthook = global_main_crash_catcher

# 引入底层引擎
from core.vision_engine import YuanhuiVisionEngine, VisionSignalCommunicator

CURRENT_VERSION = "v3.1.0-Final"


# ---------------- 1. 独立法律免责协议窗口 ----------------
# ---------------- 1. 独立法律免责协议窗口（个人自研绝对免责版） ----------------
class DisclaimerWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("软件使用协议与免责声明")
        self.setFixedSize(620, 520)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.CustomizeWindowHint)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("⚠️ 使用条款与开发者风险责任豁免协议")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin: 5px 0;")
        layout.addWidget(title)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dee2e6; font-size: 13px; line-height: 1.6; padding: 12px; color: #2c3e50;")

        disclaimer_text = (
            "欢迎使用本自动化视觉同步插件。在正式进入系统前，请使用者务必仔细阅读、充分理解以下条款。一旦点击“我同意并进入系统”，即代表您及您所代表的机构已完全知悉并自愿接受以下所有约束与免责条款：\n\n"
            "1. 版权归属与个人自研声明\n"
            "本插件（包括但不限于所有底层架构、图形识别算法及核心代码）属于原开发者个人独立自研的技术资产，其完整版权、所有权及最终解释权永久归属原作者个人所有。本插件未与任何机构或雇主签署排他性交付协议。原作者当前仅以技术交流与模拟测试目的，授予使用者临时的、非排他性的使用许可。原作者保留在任何时间，无条件收回、终止或撤销授权的绝对权利。\n\n"
            "2. 技术资产保护与禁止滥用\n"
            "未经原作者书面明确授权，严禁任何组织或个人对本插件进行破解、反编译、逆向工程、篡改或将其用于商业售卖。本插件仅供技术学习与个人日常办公效能提升之用，任何机构或个人不得将本插件用于非合规的大规模高频轰炸或恶意扰乱第三方系统运行的场景。\n\n"
            "3. 业务风险与第三方平台变动完全免责\n"
            "本插件作为纯个人研究项目，按“现状（AS-IS）”提供，原作者不对其功能的稳定性、绝对无错性做任何技术担保。因第三方圆汇客户端更新升级、界面UI像素调整导致插件失效，或因使用者日常操作不当、误操作引发的任何业务纠纷、数据清洗偏差、经济损失或平台风控处罚，全部风险与法律责任均由使用者自行承担，原开发者不承担任何直接或连带的赔偿责任。\n\n"
            "4. 无技术支持义务与永久责任豁免\n"
            "作为个人自研的免费技术试验品，原作者没有义务对本插件提供长期的技术支持、缺陷修复、版本更新或环境维护。无论在何种时间、何种运行环境下，由本插件引发的任何形式的技术故障、工作延误或业务流转异常，原作者均享有永久、完全且无条件的民事与刑事责任豁免权。"
        )
        self.text_area.setPlainText(disclaimer_text)
        layout.addWidget(self.text_area)

        btn_layout = QHBoxLayout()
        self.btn_exit = QPushButton(" 拒绝并退出 ")
        self.btn_exit.setFixedSize(140, 38)
        self.btn_exit.clicked.connect(self.reject)
        self.btn_exit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_exit.setStyleSheet(
            "background-color: #6c757d; color: white; border-radius: 4px; font-weight: bold; font-size: 13px;")

        self.btn_agree = QPushButton(" 我同意并进入系统 ")
        self.btn_agree.setFixedSize(190, 38)
        self.btn_agree.clicked.connect(self.accept)
        self.btn_agree.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_agree.setStyleSheet(
            "background-color: #198754; color: white; border-radius: 4px; font-weight: bold; font-size: 13px;")

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_exit)
        btn_layout.addWidget(self.btn_agree)
        layout.addLayout(btn_layout)


# ---------------- 2. 极简无图启动加载进度窗 ----------------
class LoadingSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(420, 180)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        self.container = QFrame(self)
        self.container.setFixedSize(420, 180)
        self.container.setStyleSheet(
            "QFrame { background-color: #2c3e50; border: 2px solid #34495e; border-radius: 8px; }")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(25, 20, 25, 20)

        self.icon_lbl = QLabel()
        standard_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CommandLink)
        self.icon_lbl.setPixmap(standard_icon.pixmap(40, 40))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("自动化视觉同步插件")
        self.title_lbl.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_lbl)

        layout.addStretch()
        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setStyleSheet(
            "QProgressBar { border: 1px solid #4b6584; border-radius: 5px; background-color: #34495e; } QProgressBar::chunk { background-color: #198754; border-radius: 4px; }")
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("正在初始化底层视觉雷达...")
        self.status_lbl.setStyleSheet("color: #95a5a6; font-size: 11px; border: none; font-weight: bold;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)


# ---------------- 3. 主程序界面 ----------------
class YuanhuiUploadApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"圆汇客户端全视觉自动导入系统 {CURRENT_VERSION}")
        self.resize(1150, 700)
        self.center_window()
        self.tasks_queue = []
        self.selected_folder_path = ""

        # 白嫖系统自带的飞镖图标
        standard_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CommandLink)
        self.setWindowIcon(standard_icon)

        self.communicator = VisionSignalCommunicator()
        self.communicator.log_sig.connect(self._update_status_slot)
        self.engine = YuanhuiVisionEngine(signal_communicator=self.communicator)

        self.setup_ui()

    def center_window(self):
        qr = self.frameGeometry()
        qr.moveCenter(self.screen().availableGeometry().center())
        self.move(qr.topLeft())

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QLabel(" 📤 圆汇客户端全视觉导入系统 (极简双图死锁版)")
        header.setStyleSheet(
            "background-color: #2c3e50; color: white; font-size: 16px; font-weight: bold; padding: 15px 20px; border-bottom: 2px solid #1a252f;")
        main_layout.addWidget(header)

        workspace = QWidget()
        workspace.setStyleSheet("background-color: #ecf0f1;")
        work_layout = QHBoxLayout(workspace)
        work_layout.setContentsMargins(25, 20, 25, 20)
        work_layout.setSpacing(20)
        main_layout.addWidget(workspace, stretch=1)

        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        path_card = QFrame()
        path_card.setStyleSheet("background-color: white; border: 1px solid #ced4da; border-radius: 6px;")
        path_lyt = QVBoxLayout(path_card)
        path_lyt.setContentsMargins(15, 12, 15, 12)
        path_lyt.setSpacing(8)

        lbl_path_title = QLabel("1. 定位需要导入的文件夹")
        lbl_path_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px; border: none;")
        path_lyt.addWidget(lbl_path_title)

        path_row = QHBoxLayout()
        self.txt_folder_path = QLineEdit()
        self.txt_folder_path.setReadOnly(True)
        self.txt_folder_path.setPlaceholderText("请点击右侧选择存放轨迹文件的文件夹...")
        self.txt_folder_path.setStyleSheet(
            "QLineEdit { background-color: #f8f9fa; border: 1px solid #cbd5e1; border-radius: 4px; padding: 7px; color: #333333; }")

        btn_browse = QPushButton(" 📁 浏览文件夹... ")
        btn_browse.clicked.connect(self.select_target_folder)
        btn_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_browse.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; border: 1px solid #2980b9; border-radius: 4px; padding: 6px 12px; font-weight: bold; }")

        path_row.addWidget(self.txt_folder_path, stretch=1)
        path_row.addWidget(btn_browse)
        path_lyt.addLayout(path_row)
        left_layout.addWidget(path_card)

        queue_card = QFrame()
        queue_card.setStyleSheet("background-color: white; border: 1px solid #ced4da; border-radius: 6px;")
        queue_lyt = QVBoxLayout(queue_card)
        queue_lyt.setContentsMargins(15, 12, 15, 15)
        queue_lyt.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["提取的核心单号", "长文件名完整预览", "实时同步状态"])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { border: 1px solid #ced4da; alternate-background-color: #f9f9f9; background-color: white; gridline-color: #e2e8f0; font-size: 13px; } QHeaderView::section { background-color: #f1f2f6; font-weight: bold; color: #2c3e50; padding: 6px; border: 1px solid #dcdde1; }")
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(2, 140)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(28)

        queue_lyt.addWidget(self.table)
        left_layout.addWidget(queue_card, stretch=1)
        work_layout.addWidget(left_box, stretch=1)

        right_frame = QFrame()
        right_frame.setFixedWidth(330)
        right_lyt = QVBoxLayout(right_frame)
        right_lyt.setContentsMargins(0, 0, 0, 0)
        right_lyt.setSpacing(15)

        action_card = QFrame()
        action_card.setStyleSheet("background-color: white; border: 1px solid #ced4da; border-radius: 6px;")
        action_lyt = QVBoxLayout(action_card)
        action_lyt.setContentsMargins(15, 15, 15, 15)
        action_lyt.setSpacing(12)

        lbl_act_title = QLabel("2. 自动化执行中心")
        lbl_act_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px; border: none;")
        action_lyt.addWidget(lbl_act_title)

        lbl_warn = QLabel(
            "💡 极简操作：\n1. 确保圆汇处于导入轨迹初始页面。\n2. 选好文件夹，点击下方大绿按钮开启托管轰炸，双手即可离开键盘鼠标！")
        lbl_warn.setWordWrap(True)
        lbl_warn.setStyleSheet(
            "color: #1e3a8a; font-size: 11.5px; font-weight: bold; border: none; line-height: 1.5; background-color: #eff6ff; padding: 10px; border-radius: 4px; border: 1px solid #bfdbfe;")
        action_lyt.addWidget(lbl_warn)

        self.btn_execute = QPushButton(" 🚀 开启全视觉精准轰炸 ")
        self.btn_execute.clicked.connect(self.launch_visual_pipeline)
        self.btn_execute.setStyleSheet("""
            QPushButton { background-color: #198754; color: white; border: 1px solid #157347; border-radius: 4px; border-bottom: 4px solid #146c43; }
            QPushButton:hover { background-color: #157347; }
            QPushButton:pressed { border-bottom: 1px solid #146c43; padding-top: 14px; }
            QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; border-bottom: none; }
        """)
        action_lyt.addWidget(self.btn_execute)

        twin_lyt = QHBoxLayout()
        twin_lyt.setSpacing(10)
        self.btn_refresh = QPushButton(" 🔄 刷新扫描 ")
        self.btn_refresh.clicked.connect(self.scan_and_load_folder_files)
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #cbd5e1; color: #333333; border: 1px solid #b1bfc1; border-radius: 4px; border-bottom: 3px solid #94a3b8; } QPushButton:hover { background-color: #b2bec3; } QPushButton:pressed { padding-top: 10px; border-bottom: 1px solid #94a3b8; }")

        self.btn_clear = QPushButton(" 🧹 清空队列 ")
        self.btn_clear.clicked.connect(self.clear_all_queues)
        self.btn_clear.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: white; border: 1px solid #5a6268; border-radius: 4px; border-bottom: 3px solid #545b62; } QPushButton:hover { background-color: #5a6268; } QPushButton:pressed { padding-top: 10px; border-bottom: 1px solid #545b62; }")
        twin_lyt.addWidget(self.btn_refresh)
        twin_lyt.addWidget(self.btn_clear)
        action_lyt.addLayout(twin_lyt)

        for btn in [self.btn_execute, self.btn_refresh, self.btn_clear]:
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            btn.setFixedHeight(40)

        right_lyt.addWidget(action_card)

        status_card = QFrame()
        status_card.setStyleSheet("background-color: white; border: 1px solid #ced4da; border-radius: 6px;")
        status_lyt = QVBoxLayout(status_card)
        status_lyt.setContentsMargins(15, 12, 15, 15)
        status_lyt.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #e5e7eb; border-radius: 4px; background-color: #f3f4f6; } QProgressBar::chunk { background-color: #198754; border-radius: 3px; }")
        status_lyt.addWidget(self.progress_bar)

        self.log_badge = QLabel("系统就绪，等待扫描路径...")
        self.log_badge.setStyleSheet(
            "QLabel { background-color: #f3f4f6; color: #495057; font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 4px; border: 1px solid #ced4da; }")
        status_lyt.addWidget(self.log_badge)
        right_lyt.addWidget(status_card)

        right_lyt.addStretch()
        work_layout.addWidget(right_frame)

    def select_target_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择装有小表格文件的文件夹", "")
        if dir_path:
            self.selected_folder_path = os.path.abspath(dir_path)
            self.txt_folder_path.setText(self.selected_folder_path)
            self.scan_and_load_folder_files()

    def scan_and_load_folder_files(self):
        if not self.selected_folder_path or not os.path.exists(self.selected_folder_path): return
        self.clear_all_queues()

        raw_files = [f for f in os.listdir(self.selected_folder_path) if f.lower().endswith((".xlsx", ".xls", ".csv"))]

        import re
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        clean_files = sorted(raw_files, key=alphanum_key)

        bl_pattern = re.compile(r"^(\d{3}-\d{8})")
        self.table.setRowCount(0)
        row_counter = 0

        for fname in clean_files:
            match = bl_pattern.match(fname)
            bl_no = match.group(1) if match else fname[:11]

            self.table.insertRow(row_counter)
            item_bl = QTableWidgetItem(bl_no)
            item_full = QTableWidgetItem(fname)
            item_status = QTableWidgetItem("📦 队列待命")

            item_bl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row_counter, 0, item_bl)
            self.table.setItem(row_counter, 1, item_full)
            self.table.setItem(row_counter, 2, item_status)

            self.tasks_queue.append({"bl_no": bl_no, "full_name": fname, "row_idx": row_counter})
            row_counter += 1

        self.log_badge.setText(f"✅ 成功扫描到 {len(self.tasks_queue)} 个有效文件单号")

    def launch_visual_pipeline(self):
        if not self.tasks_queue:
            QMessageBox.warning(self, "提示", "队列为空，请先选择包含表格的文件夹！")
            return
        self.btn_execute.setEnabled(False)
        self.btn_execute.setText("⏳ 纯视觉硬核自转中...")
        self.btn_refresh.setEnabled(False)
        self.btn_clear.setEnabled(False)

        def worker():
            self.engine.execute_pure_visual_pipeline(self.tasks_queue)
            self.btn_execute.setEnabled(True)
            self.btn_execute.setText(" 🚀 开启全视觉精准轰炸 ")
            self.btn_refresh.setEnabled(True)
            self.btn_clear.setEnabled(True)

        threading.Thread(target=worker, daemon=True).start()

    def clear_all_queues(self):
        self.tasks_queue.clear()
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.log_badge.setText("队列已清空...")

    def _update_status_slot(self, text, state_val):
        if state_val == "ROW_OP" and text.startswith("SELECT_ROW:"):
            row = int(text.split(":")[1])
            self.table.selectRow(row)
            self.table.item(row, 2).setText("⏳ 正在精准盲喂...")
            self.table.item(row, 2).setForeground(Qt.GlobalColor.blue)
            return
        elif state_val == "STATUS_OP":
            row = int(text.split(":")[1])
            if "SUCCESS" in text:
                self.table.item(row, 2).setText("✅ 同步成功")
                self.table.item(row, 2).setForeground(Qt.GlobalColor.darkGreen)
            else:
                self.table.item(row, 2).setText("❌ 超时失败")
                self.table.item(row, 2).setForeground(Qt.GlobalColor.red)
            return
        elif text == "UPDATE_PROGRESS":
            self.progress_bar.setValue(int(state_val))
            return

        self.log_badge.setText(text)
        if "❌" in text or "🚨" in text:
            self.log_badge.setStyleSheet(
                "QLabel { background-color: #f3f4f6; color: #e74c3c; font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 4px; border: 1px solid #ced4da; }")
        elif "✅" in text or "🎉" in text:
            self.log_badge.setStyleSheet(
                "QLabel { background-color: #f3f4f6; color: #198754; font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 4px; border: 1px solid #ced4da; }")
        else:
            self.log_badge.setStyleSheet(
                "QLabel { background-color: #f3f4f6; color: #2980b9; font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 4px; border: 1px solid #ced4da; }")


# ---------------- 🏁 全新三段式启动总闸门 ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 步骤 1：拦截弹出硬核法律免责声明窗口
    disclaimer = DisclaimerWindow()
    if disclaimer.exec() == QDialog.DialogCode.Accepted:

        # 步骤 2：通过免责协议后，拉起无图进度条加载窗
        splash = LoadingSplash()
        splash.show()

        # 纯血 Qt 事件流无感自增模拟初始化
        for i in range(1, 101):
            time.sleep(0.012)  # 高速丝滑移动
            splash.progress.setValue(i)
            if i == 20: splash.status_lbl.setText("正在绑定系统原生图形总线...")
            if i == 50: splash.status_lbl.setText("正在加载 OpenCV 像素矩阵切片...")
            if i == 85: splash.status_lbl.setText("正在建立一单一结死锁防线...")
            app.processEvents()  # 强行刷新图形界面，防止程序假死

        # 步骤 3：加载结束，秒开主程序界面
        main_win = YuanhuiUploadApp()
        splash.close()
        main_win.show()
        sys.exit(app.exec())
    else:
        # 拒绝直接强行退栈安全闪退
        sys.exit()