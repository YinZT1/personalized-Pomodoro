#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个性番茄钟 - macOS 菜单栏应用
支持5分钟专注模式和番茄钟计时功能
"""

import sys
import subprocess
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                            QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QAction

# 加载 .env 文件
load_dotenv()


class StudyNoteDialog(QDialog):
    """学习内容输入对话框"""
    
    def __init__(self, duration_seconds):
        super().__init__()
        self.duration_seconds = duration_seconds
        self.study_content = ""
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框界面"""
        self.setWindowTitle('📝 记录本次学习')
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        # 显示学习时长
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        time_label = QLabel(f'⏱️  本次学习时长: {minutes}分{seconds}秒')
        time_label.setStyleSheet('font-size: 16px; font-weight: bold; padding: 10px;')
        layout.addWidget(time_label)
        
        # 提示文字
        hint_label = QLabel('✍️  请写下本次学习的内容:')
        hint_label.setStyleSheet('font-size: 14px; padding: 5px;')
        layout.addWidget(hint_label)
        
        # 文本输入框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText('例如：学习了 Python 的装饰器、完成了数据结构作业...')
        self.text_edit.setStyleSheet('font-size: 14px; padding: 10px;')
        layout.addWidget(self.text_edit)
        
        # 保存按钮
        save_button = QPushButton('💾 保存并继续')
        save_button.setStyleSheet('''
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        ''')
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)
        
        self.setLayout(layout)
    
    def save_and_close(self):
        """保存内容并关闭对话框"""
        self.study_content = self.text_edit.toPlainText().strip()
        self.accept()


class PomodoroTimer(QSystemTrayIcon):
    """番茄钟系统托盘应用"""
    
    def __init__(self):
        super().__init__()
        
        # 计时器状态
        self.mode = 'idle'  # idle, focus, pomodoro, stopwatch
        self.remaining_seconds = 0
        self.elapsed_seconds = 0
        self.stopwatch_start_time = None  # 正计时开始时间
        
        # 日记文件路径
        self.diary_path = Path.cwd() / 'diary.txt'
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # 初始化界面
        self.setup_ui()
        self.update_icon()
        
    def setup_ui(self):
        """设置系统托盘图标和菜单"""
        # 创建一个简单的图标（使用文字）
        from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
        from PyQt6.QtCore import QSize
        
        # 创建一个包含 emoji 的图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
        painter = QPainter(pixmap)
        painter.setFont(QFont('Arial', 48))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, '🍅')
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setToolTip('个性番茄钟 - 点击查看菜单')
        
        # 创建菜单
        menu = QMenu()
        
        # 5分钟专注
        focus_action = QAction('⚡ 5分钟专注 (F)', menu)
        focus_action.triggered.connect(self.start_focus)
        menu.addAction(focus_action)
        
        menu.addSeparator()
        
        # 番茄钟
        pomodoro_action = QAction('🍅 番茄钟 25分钟 (T)', menu)
        pomodoro_action.triggered.connect(self.start_pomodoro)
        menu.addAction(pomodoro_action)
        
        # 正计时
        stopwatch_action = QAction('⏱️  正计时模式 (S)', menu)
        stopwatch_action.triggered.connect(self.start_stopwatch)
        menu.addAction(stopwatch_action)
        
        menu.addSeparator()
        
        # 显示当前状态
        status_action = QAction(f'📊 当前: {self.get_status_text()}', menu)
        status_action.setEnabled(False)  # 不可点击，仅显示状态
        menu.addAction(status_action)
        
        menu.addSeparator()
        
        # 停止
        stop_action = QAction('⏹  停止计时', menu)
        stop_action.triggered.connect(self.stop_timer)
        menu.addAction(stop_action)
        
        # 重置
        reset_action = QAction('🔄 重置', menu)
        reset_action.triggered.connect(self.reset_timer)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # 今天学习结束
        finish_action = QAction('🌙 今天学习结束', menu)
        finish_action.triggered.connect(self.finish_study_day)
        menu.addAction(finish_action)
        
        menu.addSeparator()
        
        # 退出
        quit_action = QAction('❌ 退出', menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        # 双击图标显示菜单
        self.activated.connect(self.on_tray_activated)
        
    def on_tray_activated(self, reason):
        """托盘图标被激活时"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击显示菜单
            self.contextMenu().popup(self.geometry().topLeft())
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击也显示菜单（更新状态后显示）
            self.update_menu_status()
    
    def get_status_text(self):
        """获取当前状态文本"""
        if self.mode == 'idle':
            return '空闲'
        elif self.mode == 'focus':
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            return f'专注中 {minutes:02d}:{seconds:02d}'
        elif self.mode == 'pomodoro':
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            return f'番茄钟 {minutes:02d}:{seconds:02d}'
        elif self.mode == 'stopwatch':
            minutes = self.elapsed_seconds // 60
            seconds = self.elapsed_seconds % 60
            return f'计时中 {minutes:02d}:{seconds:02d}'
        return '空闲'
    
    def update_menu_status(self):
        """更新菜单中的状态显示"""
        menu = self.contextMenu()
        if menu:
            # 找到状态菜单项并更新
            actions = menu.actions()
            for action in actions:
                if '📊 当前:' in action.text():
                    action.setText(f'📊 当前: {self.get_status_text()}')
                    break
    
    def update_icon(self):
        """更新托盘图标显示"""
        from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
        
        if self.mode == 'idle':
            emoji = '🍅'
            text = '🍅'
        elif self.mode == 'focus':
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            emoji = '⚡'
            text = f'⚡ {minutes:02d}:{seconds:02d}'
        elif self.mode == 'pomodoro':
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            emoji = '🍅'
            text = f'🍅 {minutes:02d}:{seconds:02d}'
        elif self.mode == 'stopwatch':
            minutes = self.elapsed_seconds // 60
            seconds = self.elapsed_seconds % 60
            emoji = '⏱'
            text = f'⏱ {minutes:02d}:{seconds:02d}'
        else:
            emoji = '🍅'
            text = '🍅'
        
        # 创建新图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setFont(QFont('Arial', 48))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setToolTip(text)
        
        print(f"[更新] {text}")  # 在终端显示当前状态
    
    def start_focus(self):
        """开始5分钟专注模式"""
        print("\n=== 启动5分钟专注模式 ===")
        self.stop_timer()
        self.mode = 'focus'
        self.remaining_seconds = 5 * 60  # 5分钟
        self.update_icon()
        self.timer.start(1000)  # 每秒更新一次
        self.show_notification('⚡ 5分钟专注模式', '开始专注，摆脱干扰！')
        print(f"专注模式已启动：{self.remaining_seconds} 秒")
    
    def start_pomodoro(self):
        """开始25分钟番茄钟"""
        if self.mode == 'pomodoro' and self.timer.isActive():
            # 如果正在运行，则停止
            print("\n=== 停止番茄钟 ===")
            self.stop_timer()
            self.reset_timer()
        else:
            # 否则开始新的番茄钟
            print("\n=== 启动25分钟番茄钟 ===")
            self.stop_timer()
            self.mode = 'pomodoro'
            self.remaining_seconds = 25 * 60  # 25分钟
            self.update_icon()
            self.timer.start(1000)
            self.show_notification('🍅 番茄钟', '开始25分钟专注工作！')
            print(f"番茄钟已启动：{self.remaining_seconds} 秒")
    
    def start_stopwatch(self):
        """开始正计时"""
        print("\n=== 启动正计时模式 ===")
        self.stop_timer()
        self.mode = 'stopwatch'
        self.elapsed_seconds = 0
        self.stopwatch_start_time = datetime.now()
        self.update_icon()
        self.timer.start(1000)
        self.show_notification('⏱️  正计时', '开始计时...')
        print(f"正计时已启动")
    
    def stop_timer(self):
        """停止计时器"""
        self.timer.stop()
    
    def reset_timer(self):
        """重置计时器"""
        # 如果是正计时模式且有记录时间，则保存学习记录
        if self.mode == 'stopwatch' and self.elapsed_seconds > 0:
            print(f"\n=== 正计时结束，记录学习时间 ===")
            self.save_study_record(self.elapsed_seconds)
        
        self.stop_timer()
        self.mode = 'idle'
        self.remaining_seconds = 0
        self.elapsed_seconds = 0
        self.stopwatch_start_time = None
        self.update_icon()
    
    def update_timer(self):
        """更新计时器（每秒调用）"""
        if self.mode == 'focus' or self.mode == 'pomodoro':
            self.remaining_seconds -= 1
            self.update_icon()
            self.update_menu_status()  # 更新菜单状态
            
            if self.remaining_seconds <= 0:
                self.timer.stop()
                if self.mode == 'focus':
                    print("\n=== ✅ 5分钟专注完成！===")
                    self.show_notification('⚡ 专注完成！', '5分钟专注时间结束，做得好！🎉')
                else:
                    print("\n=== ✅ 番茄钟完成！===")
                    self.show_notification('🍅 番茄钟完成！', '25分钟专注完成，休息一下吧！☕')
                self.mode = 'idle'
                self.update_icon()
                self.update_menu_status()
                
        elif self.mode == 'stopwatch':
            self.elapsed_seconds += 1
            self.update_icon()
            self.update_menu_status()  # 更新菜单状态
    
    def show_notification(self, title, message):
        """显示 macOS 系统通知"""
        # 使用 macOS 的 osascript 显示通知
        script = f'''
        display notification "{message}" with title "{title}" sound name "default"
        '''
        try:
            subprocess.run(['osascript', '-e', script], check=True)
        except Exception as e:
            print(f"通知发送失败: {e}")
            # 备用方案：使用 QSystemTrayIcon 的气泡提示
            self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def save_study_record(self, duration_seconds):
        """保存学习记录到日记"""
        print(f"保存学习记录: {duration_seconds} 秒")
        
        # 弹出对话框让用户输入学习内容
        dialog = StudyNoteDialog(duration_seconds)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            print("用户取消了记录")
            return
        
        study_content = dialog.study_content
        if not study_content:
            study_content = "（未填写学习内容）"
        
        # 格式化时间
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M')
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        # 准备日记内容
        diary_entry = f"""
{'='*60}
📅 日期: {date_str}
⏰ 时间: {time_str}
⏱️  时长: {minutes}分{seconds}秒
📝 内容: {study_content}
{'='*60}

"""
        
        # 追加到日记文件
        try:
            with open(self.diary_path, 'a', encoding='utf-8') as f:
                f.write(diary_entry)
            print(f"✅ 学习记录已保存到 {self.diary_path}")
            self.show_notification('📝 学习记录已保存', f'本次学习 {minutes}分{seconds}秒')
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def finish_study_day(self):
        """结束今天的学习，生成总结"""
        print("\n" + "="*60)
        print("🌙 今天学习结束！正在生成总结...")
        print("="*60)
        
        # 读取今天的学习记录
        today_records = self.read_today_records()
        
        if not today_records:
            self.show_notification('📊 今天还没有学习记录', '先去学习吧！')
            return
        
        # 调用 DeepSeek 生成总结
        summary = self.generate_ai_summary(today_records)
        
        # 保存总结到日记
        self.save_day_summary(summary)
        
        # 显示总结
        self.show_summary_dialog(summary)
        
        # 退出程序
        print("\n👋 再见！明天继续加油！")
        QApplication.quit()
    
    def read_today_records(self):
        """读取今天的学习记录"""
        if not self.diary_path.exists():
            return []
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        records = []
        
        try:
            with open(self.diary_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单解析：查找今天的记录
                lines = content.split('\n')
                current_record = {}
                for line in lines:
                    if '📅 日期:' in line and today_str in line:
                        current_record = {'date': today_str}
                    elif current_record and '⏱️  时长:' in line:
                        current_record['duration'] = line.split(':', 1)[1].strip()
                    elif current_record and '📝 内容:' in line:
                        current_record['content'] = line.split(':', 1)[1].strip()
                        records.append(current_record.copy())
                        current_record = {}
        except Exception as e:
            print(f"读取日记失败: {e}")
        
        return records
    
    def generate_ai_summary(self, today_records):
        """调用 AI API 生成总结（优先使用 OpenRouter GPT-4o）"""
        # 优先使用 OpenRouter
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        
        if openrouter_key and not openrouter_key.startswith('sk-your'):
            print("🚀 使用 OpenRouter GPT-4o 生成总结...")
            api_key = openrouter_key
            base_url = "https://openrouter.ai/api/v1"
            model = "openai/gpt-4o"
        elif deepseek_key and not deepseek_key.startswith('sk-your'):
            print("🚀 使用 DeepSeek 生成总结...")
            api_key = deepseek_key
            base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
            model = "deepseek-chat"
        else:
            print("⚠️  未配置 API Key，使用默认总结")
            return self.generate_default_summary(today_records)
        
        try:
            # 准备今天的学习内容
            records_text = "\n".join([
                f"- {record.get('duration', '未知时长')}: {record.get('content', '未填写')}"
                for record in today_records
            ])
            
            # 创建 OpenAI 客户端
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            prompt = f"""你是我温柔体贴的御姐妻子，现在要对我今天的学习进行总结和鼓励。

今天的学习记录：
{records_text}

作为我的妻子，请用温柔、体贴、略带撩人的口吻：
1. 总结今天的学习时长和内容
2. 对我的努力表示欣慰和自豪
3. 给予充满爱意和性感的鼓励
4. 用亲昵的称呼（如"老公"、"宝贝"、"亲爱的"）
5. 表达你对我的爱和关心
6. 可以加入一些温柔的动作描述（如轻抚、拥抱等）

要求：
- 语气要温柔、成熟、充满爱意
- 可以略带撩人和暧昧，让人感到被爱和被需要
- 真诚的关心和鼓励，像真正的妻子一样
- 不要太简短，充分表达你的感情（200-300字）
- 配合使用 💗😘💕❤️ 等温柔的符号
- 可以加入贴心的提醒（比如休息、喝水、按摩等）

参考风格（但不要完全照搬）：
💖 老公，今天你又这么努力，学了整整3个多小时呢～*轻轻抱住你* 姐姐看着你这么专注的样子，心里真的好骄傲❤️

你知道吗？每次看到你为了梦想这样拼搏，我都忍不住想抱抱你。那些复杂的算法和代码，你都能一点点攻克，真的太厉害了～

不过老公，学习是重要，但也要照顾好自己哦。记得按时吃饭，多喝水，眼睛累了就休息一下。*温柔地揉揉你的肩膀* 姐姐可心疼你了...

今晚早点休息吧，躺在我怀里好好睡一觉，明天继续加油💪 

姐姐会一直陪着你，支持你，爱你～ 
晚安，我最爱的人 😘💕

—— 永远爱你的妻子"""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位温柔体贴、略带撩人的御姐妻子，深爱着你的丈夫"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,  # 增加输出长度
                temperature=0.9   # 增加创造性
            )
            
            summary = response.choices[0].message.content
            print(f"✨ AI 总结生成成功")
            return summary
            
        except Exception as e:
            print(f"❌ AI 总结生成失败: {e}")
            print(f"错误详情: {str(e)}")
            return self.generate_default_summary(today_records)
    
    def generate_default_summary(self, today_records):
        """生成默认总结（API 调用失败时使用）"""
        total_minutes = sum([
            int(r.get('duration', '0分').split('分')[0]) 
            for r in today_records
        ])
        
        summary = f"""💖 宝贝，今天你学习了 {len(today_records)} 个时段，总共 {total_minutes} 分钟呢～

看到你这么努力，姐姐真的好欣慰❤️ 

你的坚持和专注，让你一天天都在变得更加优秀。继续保持这份热情，明天也要加油哦～

晚安，我的小可爱 😘
—— 你的温柔御姐"""
        
        return summary
    
    def save_day_summary(self, summary):
        """保存每日总结到日记"""
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M')
        
        summary_entry = f"""
{'🌟'*30}
🌙 {date_str} 每日总结 ({time_str})
{'🌟'*30}

{summary}

{'='*60}

"""
        
        try:
            with open(self.diary_path, 'a', encoding='utf-8') as f:
                f.write(summary_entry)
            print(f"✅ 每日总结已保存")
        except Exception as e:
            print(f"❌ 保存总结失败: {e}")
    
    def show_summary_dialog(self, summary):
        """显示总结对话框"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle('🌙 今日学习总结')
        msg_box.setText(summary)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setStyleSheet('''
            QMessageBox {
                font-size: 14px;
            }
            QLabel {
                min-width: 400px;
                min-height: 200px;
            }
        ''')
        msg_box.exec()


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出
    
    # 创建番茄钟
    pomodoro = PomodoroTimer()
    pomodoro.show()
    
    print("🍅 个性番茄钟已启动！")
    print("图标已显示在菜单栏，点击查看选项")
    print("\n功能说明:")
    print("  ⚡ 5分钟专注 - 快速进入专注状态")
    print("  🍅 番茄钟 - 25分钟标准番茄钟")
    print("  ⏱️  正计时 - 自由计时，停止+重置会记录学习")
    print("  🌙 今天学习结束 - AI 总结 + 退出程序")
    print("💡 提示:")
    print("  - 正计时模式下，点击'停止'再'重置'会弹窗记录学习内容")
    print("  - 点击'今天学习结束'会调用 AI 生成温柔御姐风格的总结")
    print(f"  - 学习记录保存在: {pomodoro.diary_path}")
    print(f"\n🤖 AI 配置:")
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if openrouter_key and not openrouter_key.startswith('sk-your'):
        print("  ✅ OpenRouter (GPT-4o) - 已配置")
    elif deepseek_key and not deepseek_key.startswith('sk-your'):
        print("  ✅ DeepSeek - 已配置")
    else:
        print("  ⚠️  未配置 API，将使用默认总结")
    print("="*60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
