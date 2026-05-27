#.venv\Scripts\activate
#py main.py

import sys
import os
import shutil


def cleanup_image_temp():
    """Remove leftover temp images from previous runs."""
    print("Delete image_temp")
    for dirpath in ("image/raw", "image/to_llm"):
        if not os.path.isdir(dirpath):
            continue
        for name in os.listdir(dirpath):
            path = os.path.join(dirpath, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                print(f"Failed to delete {path}: {e}")


# Avast and some AV tools set SSLKEYLOGFILE; on Windows that triggers
# "no OPENSSL_Applink" when urllib3/OpenSSL initialize.
if sys.platform == "win32":
    os.environ.pop("SSLKEYLOGFILE", None)
    import ssl  # noqa: F401 — load Python's OpenSSL before other DLLs
import keyboard
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor
from dotenv import load_dotenv
from datetime import datetime
from PyQt6.QtCore import QSettings
import capture
import ocr
import translator
from setting import SettingsDialog
from region_utils import ratios_to_bbox
from region_selector import select_region
class WorkerSignals(QObject):
    translation_done = pyqtSignal(tuple, str)
    status_update = pyqtSignal(str)
    toggle_translation = pyqtSignal()
    hide_translation = pyqtSignal()

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # Setup hotkey hook
        self.signals = WorkerSignals()
        self.signals.translation_done.connect(self.display_translation)
        self.signals.status_update.connect(self.update_status)

        self.settings = QSettings("MyGameTool", "TranslatorApp")
        self._settings_dialog_open = False

        self.signals.toggle_translation.connect(self.toggle_translation_visibility)
        self._setup_hotkeys()
        self.signals.hide_translation.connect(self.translation_label.hide)
        
        self.is_processing = False
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.translation_label.hide)

    def _bind_hotkey(self, key: str, callback):
        # Normalize common user inputs to what the keyboard library expects
        key_mapping = {
            "enter": "enter",
            "space": "space",
            "spacebar": "space",
        }
        
        # Convert to lowercase and look up special keys
        lookup_key = key.lower().strip()
        normalized_key = key_mapping.get(lookup_key, key)

        # If it's a multi-character key combination like "po" (and not a special key name)
        if len(normalized_key) == 2 and normalized_key not in key_mapping.values():
            keyboard.add_hotkey("+".join(list(normalized_key)), callback)
        else:
            # Using add_hotkey for single/special keys keeps callback behavior consistent
            keyboard.add_hotkey(normalized_key, callback)

    def _setup_hotkeys(self):
        keyboard.unhook_all()
        self.settings = QSettings("MyGameTool", "TranslatorApp")
        self._bind_hotkey(self.settings.value("hotkey_translate", "p"), self.on_hotkey_pressed)
        self._bind_hotkey(
            self.settings.value("hotkey_translate_full_screen", "f"),
            self.on_hotkey_pressed_full_screen,
        )
        self._bind_hotkey(
            self.settings.value("hotkey_translate_manual_seg_input", "f"),
            self.on_hotkey_pressed_translate_manual_segment,
        )
        self._bind_hotkey(self.settings.value("hotkey_quit", "q"), self.quit_app)
        self._bind_hotkey(
            self.settings.value("hotkey_toggle", "o"),
            lambda: self.signals.toggle_translation.emit(),
        )
        self._bind_hotkey(
            self.settings.value("hotkey_settings", "s"),
            self.on_hotkey_open_settings,
        )

    def update_hotkeys(self):
        self._setup_hotkeys()

    def on_hotkey_open_settings(self, event=None):
        QTimer.singleShot(0, self.open_settings)

    def initUI(self):
        # Make the window transparent and frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get screen size
        screen = QApplication.primaryScreen().geometry() # type: ignore
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        # Create a status label at the bottom left
        self.status_label = QLabel("Active", self)
        self.status_label.setStyleSheet("color: green; font-size: 20px; font-weight: bold; background-color: rgba(0,0,0,150); padding: 5px;")
        self.status_label.adjustSize()
        self.status_label.move(20, screen.height() - 50)
        
        # Label to show the translated text
        self.translation_label = QLabel("", self)
        self.translation_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 200); padding: 10px; border: 2px solid white; border-radius: 5px;")
        self.translation_label.hide()
        
        self.show()

    def quit_app(self, event=None):
        cleanup_image_temp()
        print("Quitting application...")
        os._exit(0)




    def on_hotkey_pressed(self, event=None):
        if self.is_processing:
            return
            
        self.is_processing = True
        self.signals.hide_translation.emit()
        self.signals.status_update.emit("Processing...")
        
        # Run the heavy processing in a short timer to avoid blocking keyboard hook thread completely
        QTimer.singleShot(10, self.process_screen)
        
    def _translate_settings(self):
        self.settings = QSettings("MyGameTool", "TranslatorApp")
        return (
            self.settings.value("extract_text_mode"),
            self.settings.value("language_mode"),
            self.settings.value("api_key"),
            self.settings.value("model"),
            self.settings.value("story_name"),
        )

    def _is_fixed_region(self) -> bool:
        return self.settings.value("region_mode", "ocr") == "fixed"

    def _display_bbox_for_fullscreen(self) -> tuple[int, int, int, int]:
        """Full-screen capture; overlay uses fixed region when configured."""
        if self._is_fixed_region():
            return ratios_to_bbox(self.settings)
        screen_rect = QApplication.primaryScreen().geometry() # type: ignore
        return (0, 0, screen_rect.width(), screen_rect.height())

    def process_screen(self):
        try:
            # 1. Capture screen
            img, monitor = capture.capture_screen()
            
            # Create directories if they don't exist
            os.makedirs("image/raw", exist_ok=True)
            os.makedirs("image/to_llm", exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Save raw image
            raw_path = os.path.join("image/raw", f"{timestamp}.png")
            img.save(raw_path)

            self.settings = QSettings("MyGameTool", "TranslatorApp")

            bbox, text = ocr.extract_dialogue(img)
            if not text or not bbox:
                self.signals.status_update.emit("No text found.")
                QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
                return
            x, y, w, h = bbox
            cropped_img = img.crop((x, y, x + w, y + h))

            #reassign bbox for render
            if self._is_fixed_region():
                bbox = ratios_to_bbox(self.settings)
                x, y, w, h = bbox


            extract_text_mode, language_mode, api_key, llm_model_name, story_name = self._translate_settings()
            has_content = bool(text) or extract_text_mode == "llm"

            if has_content and bbox:
                to_llm_path = os.path.join("image/to_llm", f"{timestamp}.png")
                cropped_img.save(to_llm_path)

                self.signals.status_update.emit("Translating...")
                translated_text = translator.translate_text(
                    text, to_llm_path, llm_model_name, extract_text_mode, language_mode, story_name, api_key
                )
                self.signals.translation_done.emit(bbox, translated_text)
            else:
                self.signals.status_update.emit("No text found.")
                QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
                
        except Exception as e:
            print(f"Error processing screen: {e}")
            self.signals.status_update.emit("Error!")
            QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
        finally:
            self.is_processing = False

    def on_hotkey_pressed_full_screen(self, event=None):
        if self.is_processing:
            return
            
        self.is_processing = True
        self.signals.hide_translation.emit()
        self.signals.status_update.emit("Processing...")
        
        # Run the heavy processing in a short timer to avoid blocking keyboard hook thread completely
        QTimer.singleShot(10, self.process_screen_full_screen)

    def process_screen_full_screen(self):
        try:
            # 1. Capture screen
            img, monitor = capture.capture_screen()
            
            # Create directories if they don't exist
            os.makedirs("image/raw", exist_ok=True)
            os.makedirs("image/to_llm", exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Save raw image
            raw_path = os.path.join("image/raw", f"{timestamp}.png")
            img.save(raw_path)
            
            # Save as to_llm image for full screen
            to_llm_path = os.path.join("image/to_llm", f"{timestamp}.png")
            img.save(to_llm_path)
            
            extract_text_mode, language_mode, api_key, llm_model_name, story_name = self._translate_settings()
            display_bbox = self._display_bbox_for_fullscreen()
            # LLM reads the image directly — skip OCR on full screen (too slow).
            if extract_text_mode == "llm":
                text = ""
            else:
                text = ocr.extract_all_text(img)
            
            if text or extract_text_mode == "llm":
                self.signals.status_update.emit("Translating...")
                # 3. Translate                
                translated_text = translator.translate_text(text, to_llm_path, llm_model_name, extract_text_mode, language_mode, story_name, api_key)
                # 4. Show
                self.signals.translation_done.emit(display_bbox, translated_text)
            else:
                self.signals.status_update.emit("No text found.")
                QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
                
        except Exception as e:
            print(f"Error processing full screen: {e}")
            self.signals.status_update.emit("Error!")
            QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
        finally:
            self.is_processing = False

    def on_hotkey_pressed_translate_manual_segment(self, event=None):
        if self.is_processing:
            return
            
        self.is_processing = True
        self.signals.hide_translation.emit()
        self.signals.status_update.emit("Processing...")
        
        # Run the heavy processing in a short timer to avoid blocking keyboard hook thread completely
        QTimer.singleShot(10, self.process_translate_manual_segment)

    def process_translate_manual_segment(self):
        try:
            # 1. Capture screen
            img, monitor = capture.capture_screen()
            
            # Create directories if they don't exist
            os.makedirs("image/raw", exist_ok=True)
            os.makedirs("image/to_llm", exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Save raw image
            raw_path = os.path.join("image/raw", f"{timestamp}.png")
            img.save(raw_path)

            self.settings = QSettings("MyGameTool", "TranslatorApp")
            
            bbox = select_region(parent=self)
            if not bbox:
                self.signals.status_update.emit("No text found.")
                QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
                return
            x, y, w, h = bbox
            cropped_img = img.crop((x, y, x + w, y + h))

            extract_text_mode, language_mode, api_key, llm_model_name, story_name = self._translate_settings()

            if extract_text_mode == "llm":
                text = ""
            else:
                text = ocr.extract_all_text(img)

            #reassign bbox for render
            if self._is_fixed_region():
                bbox = ratios_to_bbox(self.settings)
                x, y, w, h = bbox
            
            has_content = bool(text) or extract_text_mode == "llm"
            
            if has_content and bbox:
                to_llm_path = os.path.join("image/to_llm", f"{timestamp}.png")
                cropped_img.save(to_llm_path)

                self.signals.status_update.emit("Translating...")
                translated_text = translator.translate_text(
                    text, to_llm_path, llm_model_name, extract_text_mode, language_mode, story_name, api_key
                )
                self.signals.translation_done.emit(bbox, translated_text)
            else:
                self.signals.status_update.emit("No text found.")
                QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
                
        except Exception as e:
            print(f"Error processing screen: {e}")
            self.signals.status_update.emit("Error!")
            QTimer.singleShot(2000, lambda: self.signals.status_update.emit("Active"))
        finally:
            self.is_processing = False


    def display_translation(self, bbox, translated_text):
        x, y, w, h = bbox
        
        screen_rect = QApplication.primaryScreen().geometry() # type: ignore
        max_w = int(screen_rect.width() * 0.667)

        # Update label text
        self.translation_label.setWordWrap(True)
        self.translation_label.setFixedWidth(max_w)
        self.translation_label.setText(translated_text)
        self.translation_label.adjustSize()
        
        # Position the label roughly over the detected bounding box
        # Ensure it doesn't go off screen
        screen = QApplication.primaryScreen().geometry() # type: ignore
        label_w = self.translation_label.width()
        label_h = self.translation_label.height()
        
        # Center the label at bottom-center of the screen if the bounding box represents the full screen
        if w >= screen.width() - 10 and h >= screen.height() - 10:
            pos_x = (screen.width() - label_w) // 2
            pos_y = int(screen.height() * 0.75) - (label_h // 2)
        else:
            pos_x = min(x, screen.width() - label_w)
            pos_y = min(y, screen.height() - label_h)
        
        self.translation_label.move(pos_x, pos_y)
        self.translation_label.show()
        
        self.signals.status_update.emit("Active")
        
        # Hide the translation after 12 seconds
        TIME_SHOW_TRANSLATE = self.settings.value("time_show_translate", "15")
        self.hide_timer.start(int(TIME_SHOW_TRANSLATE) * 1000)

    def toggle_translation_visibility(self):
        if self.translation_label.text():
            if self.translation_label.isVisible():
                self.translation_label.hide()
            else:
                self.translation_label.show()

    def update_status(self, text):
        self.status_label.setText(text)
        self.status_label.adjustSize()

    def open_settings(self):
        if self._settings_dialog_open:
            return
        self._settings_dialog_open = True
        try:
            dialog = SettingsDialog(parent=self)
            if dialog.exec():
                self.settings = QSettings("MyGameTool", "TranslatorApp")
                self.update_hotkeys()
        finally:
            self._settings_dialog_open = False



if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Overlay is a Tool window; closing settings must not quit the app.
    app.setQuitOnLastWindowClosed(False)

    # Clear temp images on startup as well.
    cleanup_image_temp()

    dialog = SettingsDialog()


    if dialog.exec():
        ex = Overlay()
        ex.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

    # # Now start the actual overlay
    # ex = Overlay()
    # ex.show() # Make sure you have .show() if it's not in initUI
    # sys.exit(app.exec())
