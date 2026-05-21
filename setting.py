import sys
import json
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont 

# Import Fluent replacements
from qfluentwidgets import (
    setTheme, 
    setThemeColor, 
    Theme,
    FluentStyleSheet,  
    LineEdit,
    ComboBox,
    PushButton,
    PrimaryPushButton,
    BodyLabel,
    TitleLabel,
    MessageBox,
    ScrollArea
)

from region_selector import select_region
from region_utils import bbox_to_ratios, default_bbox_ratios, format_bbox, ratios_to_bbox

with open("llm_prompt.json", 'r', encoding='utf-8') as f:
    llm_prompt_dict = json.load(f)
    story_list = list(llm_prompt_dict.get("specific_story_prompt", {}).keys())


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("App Settings")
        self.resize(600, 1000)  # Reset to a balanced UI window depth
        
        # 1. Theme Configuration
        setTheme(Theme.LIGHT)  
        setThemeColor('#E67E22') 
        FluentStyleSheet.DIALOG.apply(self) 

        # 2. Typography Definitions
        title_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        label_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        button_font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        input_font = QFont("Segoe UI", 10, QFont.Weight.Medium) 
        importance_button_font = QFont("Segoe UI", 12, QFont.Weight.Bold)

        self.settings = QSettings("MyGameTool", "TranslatorApp")
        self._pending_ratios = None

        # --- Main Layout Engine Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 12, 24, 12)
        
        self.title_label = TitleLabel("Configuration Panel", self)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(26) 

        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QDialog()
        scroll_content.setStyleSheet("background-color: #F5F5F7;")
        
        # --- FIXED Layout Structure ---
        # Master form container uses standard vertical spacing layout rules
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(8)  # <-- FAR Spacing: Distance between distinct option blocks

        # Custom block injector utility function
        def add_setting_item(label_text, input_widget):
            item_block = QVBoxLayout()
            item_block.setContentsMargins(0, 0, 0, 0)
            item_block.setSpacing(1)  # <-- NEAR Spacing: Distance between label text and input box
            
            lbl = BodyLabel(label_text)
            lbl.setFont(label_font)
            
            item_block.addWidget(lbl)
            item_block.addWidget(input_widget)
            form_layout.addLayout(item_block)

        # --- Injecting UI Form Items ---
        self.api_input = LineEdit()
        self.api_input.setFont(input_font) 
        self.api_input.setPlaceholderText("sk-or-...")
        self.api_input.setText(self.settings.value("api_key", ""))
        add_setting_item("OpenRouter API Key:", self.api_input)

        self.language_mode_input = ComboBox()
        self.language_mode_input.setFont(input_font) 
        self.language_mode_input.addItems(["EN->TH", "JP->TH", "JP->EN"])
        self.language_mode_input.setCurrentText(self.settings.value("language_mode", "EN->TH"))
        add_setting_item("Language Processing Direction:", self.language_mode_input)

        self.hotkey_translate_full_screen_input = LineEdit()
        self.hotkey_translate_full_screen_input.setFont(input_font) 
        self.hotkey_translate_full_screen_input.setText(self.settings.value("hotkey_translate_full_screen", "f"))
        add_setting_item("Translate Full Screen Hotkey:", self.hotkey_translate_full_screen_input)

        self.hotkey_translate_manual_seg_input = LineEdit()
        self.hotkey_translate_manual_seg_input.setFont(input_font) 
        self.hotkey_translate_manual_seg_input.setText(self.settings.value("hotkey_translate_manual_seg_input", "i"))
        add_setting_item("Translate Manual Segmentation Hotkey:", self.hotkey_translate_manual_seg_input)

        self.hotkey_translate_input = LineEdit()
        self.hotkey_translate_input.setFont(input_font) 
        self.hotkey_translate_input.setText(self.settings.value("hotkey_translate", "p"))
        add_setting_item("Translate Auto Segmentation Hotkey:", self.hotkey_translate_input)

        self.hotkey_toggle_input = LineEdit()
        self.hotkey_toggle_input.setFont(input_font) 
        self.hotkey_toggle_input.setText(self.settings.value("hotkey_toggle", "o"))
        add_setting_item("Toggle HUD Overlay Hotkey:", self.hotkey_toggle_input)

        self.hotkey_settings_input = LineEdit()
        self.hotkey_settings_input.setFont(input_font) 
        self.hotkey_settings_input.setText(self.settings.value("hotkey_settings", "s"))
        add_setting_item("Open Settings Menu Hotkey:", self.hotkey_settings_input)

        self.hotkey_quit_input = LineEdit()
        self.hotkey_quit_input.setFont(input_font) 
        self.hotkey_quit_input.setText(self.settings.value("hotkey_quit", "q"))
        add_setting_item("Quit Application Hotkey:", self.hotkey_quit_input)

        self.extract_text_mode_input = ComboBox()
        self.extract_text_mode_input.setFont(input_font) 
        self.extract_text_mode_input.addItems(["llm", "ocr"])
        self.extract_text_mode_input.setCurrentText(self.settings.value("extract_text_mode", "llm"))
        add_setting_item("Text Extraction Engine Mode:", self.extract_text_mode_input)

        self.region_mode_input = ComboBox()
        self.region_mode_input.setFont(input_font) 
        self.region_mode_input.addItems(["fixed", "ocr"])
        self.region_mode_input.setCurrentText(self.settings.value("region_mode", "ocr"))
        self.region_mode_input.currentTextChanged.connect(self._update_region_controls)
        add_setting_item("Translation Display Box Region:", self.region_mode_input)

        # Region Configuration Complex Container
        region_complex_block = QVBoxLayout()
        region_complex_block.setContentsMargins(0, 0, 0, 0)
        region_complex_block.setSpacing(6)
        
        self.region_info_label = BodyLabel("")
        self.region_info_label.setFont(label_font)
        region_complex_block.addWidget(self.region_info_label)

        region_btn_row = QHBoxLayout()
        region_btn_row.setSpacing(10)
        self.pick_region_btn = PushButton("Pick Region on Screen")
        self.pick_region_btn.setFont(button_font)
        self.pick_region_btn.clicked.connect(self.pick_region)
        region_btn_row.addWidget(self.pick_region_btn)
        
        self.reset_region_btn = PushButton("Reset to Default")
        self.reset_region_btn.setFont(button_font)
        self.reset_region_btn.clicked.connect(self.reset_region_defaults)
        region_btn_row.addWidget(self.reset_region_btn)
        region_complex_block.addLayout(region_btn_row)
        form_layout.addLayout(region_complex_block)

        self.story_name_input = ComboBox()
        self.story_name_input.setFont(input_font) 
        self.story_name_input.addItems(story_list)
        self.story_name_input.setCurrentText(self.settings.value("story_name", "None"))
        add_setting_item("Target Story Dataset (Context Tuning):", self.story_name_input)

        self.model_input = LineEdit()
        self.model_input.setFont(input_font) 
        self.model_input.setText(self.settings.value("model", "google/gemma-4-26b-a4b-it"))
        add_setting_item("Inference Translation Model Node:", self.model_input)

        self.time_show_translate_input = LineEdit()
        self.time_show_translate_input.setFont(input_font) 
        self.time_show_translate_input.setText(self.settings.value("time_show_translate", "15"))
        add_setting_item("Subtitles Display Duration (Seconds):", self.time_show_translate_input)

        # Invisible layout spacer to lock all controls neatly upward
        form_layout.addStretch()

        # Bind Content Widget to Scroll Structure
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Action Execution Layout Footer
        main_layout.addSpacing(10)
        self.save_btn = PrimaryPushButton("Save System Settings", self)
        self.save_btn.setFont(importance_button_font)
        self.save_btn.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)
        self._refresh_region_label()
        self._update_region_controls()

    def _update_region_controls(self):
        fixed = self.region_mode_input.currentText() == "fixed"
        self.pick_region_btn.setEnabled(fixed)
        self.reset_region_btn.setEnabled(fixed)

    def _refresh_region_label(self):
        if self._pending_ratios:
            screen = QApplication.primaryScreen().geometry()
            x = int(screen.width() * self._pending_ratios["region_x_ratio"])
            y = int(screen.height() * self._pending_ratios["region_y_ratio"])
            w = int(screen.width() * self._pending_ratios["region_w_ratio"])
            h = int(screen.height() * self._pending_ratios["region_h_ratio"])
            bbox = (x, y, w, h)
        else:
            bbox = ratios_to_bbox(self.settings)
        self.region_info_label.setText(f"Active Display Coordinates: {format_bbox(bbox)}")

    def pick_region(self):
        bbox = select_region(parent=self)
        if bbox:
            self._pending_ratios = bbox_to_ratios(bbox)
            self._refresh_region_label()
            self.raise_()
            self.activateWindow()

    def reset_region_defaults(self):
        self._pending_ratios = default_bbox_ratios()
        self._refresh_region_label()

    def save_settings(self):
        self.settings.setValue("api_key", self.api_input.text())
        self.settings.setValue("hotkey_translate", self.hotkey_translate_input.text())
        self.settings.setValue("hotkey_translate_manual_seg_input", self.hotkey_translate_manual_seg_input.text())
        self.settings.setValue("hotkey_translate_full_screen", self.hotkey_translate_full_screen_input.text())
        self.settings.setValue("hotkey_quit", self.hotkey_quit_input.text())
        self.settings.setValue("hotkey_toggle", self.hotkey_toggle_input.text())
        self.settings.setValue("hotkey_settings", self.hotkey_settings_input.text())
        self.settings.setValue("time_show_translate", self.time_show_translate_input.text())
        self.settings.setValue("extract_text_mode", self.extract_text_mode_input.currentText())
        self.settings.setValue("model", self.model_input.text())
        self.settings.setValue("language_mode", self.language_mode_input.currentText())
        self.settings.setValue("story_name", self.story_name_input.currentText())
        self.settings.setValue("region_mode", self.region_mode_input.currentText())
        
        if self._pending_ratios:
            for key, value in self._pending_ratios.items():
                self.settings.setValue(key, value)
        elif self.region_mode_input.currentText() == "fixed":
            for key, value in default_bbox_ratios().items():
                if self.settings.value(key) is None:
                    self.settings.setValue(key, value)

        msg = MessageBox("Success", "Configuration successfully initialized and saved!", self)
        msg.exec()
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # global_font = QFont("Segoe UI", 10)
    # global_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    # app.setFont(global_font)

    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())