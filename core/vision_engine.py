import os
import time
import pyautogui
import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal


class VisionSignalCommunicator(QObject):
    """ 专用跨线程安全通讯器 """
    log_sig = pyqtSignal(str, str)


class YuanhuiVisionEngine:
    def __init__(self, signal_communicator=None, confidence=0.85):
        self.signals = signal_communicator if signal_communicator else VisionSignalCommunicator()
        self.confidence = confidence

        # 🌟 绝杀兼容修改：如果是打包运行状态，去 EXE 同级目录找 assets；否则用开发路径
        import sys
        if getattr(sys, 'frozen', False):
            # 获取当前 EXE 所在的目录（不是临时解压目录）
            exe_dir = os.path.dirname(sys.executable)
            self.assets_dir = os.path.join(exe_dir, "assets")
        else:
            # 正常的开发环境路径
            self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

        # 🌟 4张核心特征图合围
        self.img_start_btn = os.path.join(self.assets_dir, "初始入口_按包裹号导入轨迹.png")
        self.img_confirm_btn = os.path.join(self.assets_dir, "提交按钮_确认导入.png")
        self.img_nav_doc = os.path.join(self.assets_dir, "弹窗_导航栏文档.png")
        self.img_target_folder = os.path.join(self.assets_dir, "弹窗_文件夹目标.png")

    def emit_log(self, text, color_hex="#2c3e50"):
        self.signals.log_sig.emit(text, color_hex)

    def locate_image_on_screen(self, template_path, custom_confidence=None):
        """ 利用 OpenCV 执行全屏像素矩阵匹配 """
        if not os.path.exists(template_path): return None
        screenshot = pyautogui.screenshot()
        screen_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        try:
            template_array = np.fromfile(template_path, dtype=np.uint8)
            template = cv2.imdecode(template_array, cv2.IMREAD_GRAYSCALE)
            if template is None: return None
            h, w = template.shape[:2]
        except:
            return None
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        target_confidence = custom_confidence if custom_confidence else self.confidence
        if max_val >= target_confidence:
            return max_loc[0] + w // 2, max_loc[1] + h // 2
        return None

    def execute_pure_visual_pipeline(self, file_tasks_list):
        """
        🦾 绝杀总控：从第一单开始完整循环，双图反向死锁，至全自动文件选择，直至全部导完
        """
        total_tasks = len(file_tasks_list)
        try:
            for idx, task in enumerate(file_tasks_list):
                bl_no = task["bl_no"]  # 11位核心单号
                row_idx = task["row_idx"]
                file_idx = idx + 1

                # 同步前台高亮
                self.signals.log_sig.emit(f"SELECT_ROW:{row_idx}", "ROW_OP")
                self.emit_log(f"▶️ 开始流转第 {file_idx}/{total_tasks} 单: {bl_no}...", "#2c3e50")

                # ---- 🛑 动作 1: 寻找并点击亮橙色主入口按钮 ----
                self.emit_log("🔍 正在检索亮橙色 [按包裹号导入轨迹] 主按钮...", "#2980b9")

                # 留出 1.5 秒空档，确保前一单彻底让出焦点
                time.sleep(1.5)

                start_coords = self.locate_image_on_screen(self.img_start_btn)
                if not start_coords:
                    self.emit_log("❌ 在屏幕上找不到亮橙色主入口按钮，流程强行中断！", "#e74c3c")
                    return False

                # 点击主按钮唤出弹窗
                pyautogui.moveTo(start_coords[0], start_coords[1], duration=0.2)
                pyautogui.click()

                # 🌟 留足 2.0 秒：死等 Windows 文件大弹窗探头
                time.sleep(2.0)

                # ---- 🛑 动作 1.5: 🔥 自导航连招（文档 ➔ 目标文件夹） ----
                self.emit_log("📂 弹窗已现，正在自动检索 Windows [文档] 快捷入口...", "#34495e")
                # 弹窗内小文字与侧边栏适配，降信度到 0.8 防止匹配失败
                doc_coords = self.locate_image_on_screen(self.img_nav_doc, custom_confidence=0.80)
                if doc_coords:
                    pyautogui.moveTo(doc_coords[0], doc_coords[1], duration=0.2)
                    pyautogui.click()
                    time.sleep(1.0)  # 等待右侧列表刷新

                    self.emit_log("📂 正在定位目标工作目录...", "#34495e")
                    # 文件夹匹配使用 0.85 高精度，避开左侧类似图标的干扰
                    folder_coords = self.locate_image_on_screen(self.img_target_folder, custom_confidence=0.85)
                    if folder_coords:
                        # 找到后双击进入！
                        pyautogui.moveTo(folder_coords[0], folder_coords[1], duration=0.2)
                        pyautogui.doubleClick()
                        time.sleep(1.2)  # 等待文件夹打开并加载完毕
                    else:
                        self.emit_log("⚠️ 提示：未在右侧列表看到目标挂载目录，可能已经处于该目录下。继续运行...",
                                      "#e67e22")
                else:
                    self.emit_log("⚠️ 提示：未能精准捕获 Windows 左侧 [文档] 入口，继续尝试直接喂单...", "#e67e22")

                # ---- 🛑 动作 2: 🔥 天才物理连招（强锁输入框 ➔ 输单号 ➔ 下 ➔ 回车） ----
                self.emit_log(f"📂 正在向 Windows 文件名框物理盲喂单号: {bl_no}", "#8e44ad")

                # 🌟 绝杀保险：强行按下 Alt + N，逼迫 Windows 焦点砸在“文件名(N):”输入框里！
                pyautogui.hotkey('alt', 'n')
                time.sleep(0.3)

                # 模拟硬件打字输入纯单号
                pyautogui.typewrite(bl_no, interval=0.005)
                time.sleep(0.5)

                # 按一下键盘下箭头，强行把焦点砸在下方被高亮选中的文件上
                pyautogui.press('down')
                time.sleep(0.3)

                # 敲回车，Windows 大弹窗闭合，文件塞入客户端
                pyautogui.press('enter')

                # 🌟 留足 2.0 秒长延迟：留给客户端充分的时间去读取、解构表格
                time.sleep(2.0)

                # ---- 🛑 动作 3: 寻找并点击【确认导入】提交按钮 ----
                self.emit_log("🚀 文件已喂入，正在寻找界面内部的 [确认导入] 按钮...", "#2980b9")
                confirm_coords = self.locate_image_on_screen(self.img_confirm_btn)
                if confirm_coords:
                    pyautogui.moveTo(confirm_coords[0], confirm_coords[1], duration=0.1)
                    pyautogui.click()
                    time.sleep(1.0)
                else:
                    self.emit_log("💡 未发现二次确认按钮，判定客户端可能已直接触发上传...", "#e67e22")

                # ---- 🛑 动作 4: 🔥 核心反向监测：死等主按钮【重新恢复亮橙色可点】 ----
                self.emit_log("⏳ 服务端正在深度解析中... 启动 10 分钟高级反向死锁防线...", "#e67e22")

                processing_timeout = 600  # 10 分钟死等
                loop_start = time.time()
                is_ok = False
                last_heartbeat = time.time()

                while time.time() - loop_start < processing_timeout:
                    is_recovered = self.locate_image_on_screen(self.img_start_btn)

                    if is_recovered:
                        self.emit_log(f"✅ 成功复苏！检测到主按钮重新变回亮橙常态色！", "#27ae60")
                        self.signals.log_sig.emit(f"ROW_SUCCESS:{row_idx}", "STATUS_OP")
                        is_ok = True
                        break  # 瞬间轰碎死锁

                    time.sleep(1.5)

                    if time.time() - last_heartbeat > 25:
                        elapsed_min = int((time.time() - loop_start) // 60)
                        elapsed_sec = int((time.time() - loop_start) % 60)
                        self.emit_log(f"⏳ 正在反向检索按钮原色... 已顽强等待 {elapsed_min} 分 {elapsed_sec} 秒...",
                                      "#e67e22")
                        last_heartbeat = time.time()

                if not is_ok:
                    self.emit_log(f"⚠️ 单号 {bl_no} 狂等 10 分钟仍未变回原色，流程强行阻断！", "#e74c3c")
                    self.signals.log_sig.emit(f"ROW_FAILED:{row_idx}", "STATUS_OP")
                    return False

                # 刷新主进度条
                progress_val = int((file_idx / total_tasks) * 100)
                self.signals.log_sig.emit("UPDATE_PROGRESS", str(progress_val))

                time.sleep(2.5)

            self.emit_log("🎉 全量文件流水线已 100% 悉数精准导入，大获全胜！", "#27ae60")
            return True

        except Exception as e:
            self.emit_log(f"🚨 突发硬件层电控异常中断: {str(e)}", "#e74c3c")
            return False