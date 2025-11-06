"""
License Activation Dialog - RSA Hybrid System
==============================================
Dialog for users to:
1. Copy their Device ID to send to admin
2. Paste JSON license received from admin
3. Activate license (offline RSA verification)

NO license generation - only admin has the private key!
"""

import logging
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QFormLayout,
                             QMessageBox, QTextEdit, QApplication, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont



class PasteOnlyTextEdit(QTextEdit):
    """Custom QTextEdit that only allows paste, no copy/cut"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def keyPressEvent(self, event):
        # Block Ctrl+C (copy) and Ctrl+X (cut)
        from PyQt6.QtCore import Qt
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() in (Qt.Key.Key_C, Qt.Key.Key_X):
                return  # Ignore copy/cut
        # Allow everything else (including Ctrl+V for paste)
        super().keyPressEvent(event)

logger = logging.getLogger(__name__)


class LicenseDialog(QDialog):
    """License activation dialog - User interface"""
    
    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("License Activation - DMX Master")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🔐 License Activation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status group - ALWAYS VISIBLE
        status_group = QGroupBox("Current License Status")
        status_layout = QFormLayout(status_group)
        
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        status_layout.addRow("Status:", self.status_label)
        
        self.license_type_label = QLabel("")
        status_layout.addRow("License Type:", self.license_type_label)
        
        self.expiration_label = QLabel("")
        status_layout.addRow("Expiration:", self.expiration_label)
        
        self.device_id_status_label = QLabel("")
        self.device_id_status_label.setFont(QFont("Courier", 8))
        self.device_id_status_label.setWordWrap(True)
        status_layout.addRow("Device ID:", self.device_id_status_label)
        
        self.trial_label = QLabel("")
        status_layout.addRow("Trial Info:", self.trial_label)
        
        self.platform_label = QLabel("")
        status_layout.addRow("Platform:", self.platform_label)
        
        layout.addWidget(status_group)
        
        # ===== ACTIVATION STEPS WIDGET (hidden when activated) =====
        self.activation_steps_widget = QWidget()
        activation_steps_layout = QVBoxLayout(self.activation_steps_widget)
        
        # ===== ACTIVATION STEPS WIDGET (hidden when activated) =====
        self.activation_steps_widget = QWidget()
        activation_steps_layout = QVBoxLayout(self.activation_steps_widget)
        
        # ===== STEP 1: Device ID =====
        device_group = QGroupBox("📋 Step 1: Get Your Device ID")
        device_layout = QVBoxLayout(device_group)
        
        device_info = QLabel(
            "<b>Copy this Device ID and email it to the software author to purchase a license:</b>"
        )
        device_info.setWordWrap(True)
        device_layout.addWidget(device_info)
        
        device_id_layout = QHBoxLayout()
        self.device_id_display = QLineEdit()
        self.device_id_display.setReadOnly(True)
        self.device_id_display.setFont(QFont("Courier", 9))
        self.device_id_display.setText(self.license_manager.get_device_id())
        self.device_id_display.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        device_id_layout.addWidget(self.device_id_display)
        
        self.copy_device_btn = QPushButton("📋 Copy Device ID")
        self.copy_device_btn.clicked.connect(self._copy_device_id)
        self.copy_device_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        device_id_layout.addWidget(self.copy_device_btn)
        
        device_layout.addLayout(device_id_layout)
        
        contact_info = QLabel(
            "Contact: <a href='mailto:truongcongdinh97tcd@gmail.com'>truongcongdinh97tcd@gmail.com</a>"
        )
        contact_info.setOpenExternalLinks(True)
        contact_info.setStyleSheet("color: #666; font-size: 10pt;")
        device_layout.addWidget(contact_info)
        
        activation_steps_layout.addWidget(device_group)
        
        # ===== STEP 2: License JSON =====
        input_group = QGroupBox("📥 Step 2: Enter License from Admin")
        input_layout = QVBoxLayout(input_group)
        
        info_text = QLabel(
            "<b>Paste the entire JSON license file you received:</b>"
        )
        info_text.setWordWrap(True)
        input_layout.addWidget(info_text)
        
        # JSON license input
        self.license_json_input = PasteOnlyTextEdit()
        # Disable copy/cut - only allow paste
        self.license_json_input.setPlaceholderText('''{
  "device_id": "your_device_id_here",
  "license_id": "unique-license-id",
  "issued_date": "2025-11-03T10:30:00",
  "customer_email": "you@example.com",
  "signature": "RSA_signature_base64",
  "license_type": "perpetual",
  "version": "1.0.0"
}''')
        self.license_json_input.setFont(QFont("Courier", 9))
        self.license_json_input.setMinimumHeight(120)
        input_layout.addWidget(self.license_json_input)
        
        # Paste button
        paste_layout = QHBoxLayout()
        paste_layout.addStretch()
        
        self.paste_btn = QPushButton("📋 Paste from Clipboard")
        self.paste_btn.clicked.connect(self._paste_license_json)

        self.load_file_btn = QPushButton(' Load from File')
        self.load_file_btn.clicked.connect(self._load_from_file)
        paste_layout.addWidget(self.load_file_btn)
        paste_layout.addWidget(self.paste_btn)
        
        input_layout.addLayout(paste_layout)
        
        activation_steps_layout.addWidget(input_group)
        
        # Add activation steps widget to main layout
        layout.addWidget(self.activation_steps_widget)
        
        # ===== ACTIVATION BUTTONS =====
        button_layout = QHBoxLayout()
        
        self.activate_btn = QPushButton("✅ Activate License")
        self.activate_btn.clicked.connect(self.activate_license)
        self.activate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; font-size: 12pt;")
        button_layout.addWidget(self.activate_btn)
        
        self.deactivate_btn = QPushButton("🔓 Deactivate License")
        self.deactivate_btn.clicked.connect(self.deactivate_license)
        self.deactivate_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.deactivate_btn.setVisible(False)  # Hidden by default
        button_layout.addWidget(self.deactivate_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # ===== HELP TEXT =====
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(120)
        help_text.setHtml("""
        <h4>ℹ️ How to Activate:</h4>
        <ol>
        <li><b>Copy your Device ID</b> (Step 1) and send it to the author</li>
        <li><b>Receive JSON license</b> file via email</li>
        <li><b>Paste JSON content</b> into the box above (Step 2)</li>
        <li><b>Click "Activate License"</b></li>
        </ol>
        <p><b>🔒 Security:</b> License uses RSA-2048 cryptographic signatures. 
        Only the software author can generate valid licenses. 
        Your license is permanently tied to this computer.</p>
        <p><b>📅 Trial:</b> 7 days free, all features unlocked</p>
        """)
        layout.addWidget(help_text)
    
    def _copy_device_id(self):
        """Copy Device ID to clipboard"""
        device_id = self.license_manager.get_device_id()
        QApplication.clipboard().setText(device_id)
        
        QMessageBox.information(
            self,
            "Copied!",
            f"✅ Device ID copied to clipboard!\n\n"
            f"Send this to the software author:\n{device_id[:32]}...\n\n"
            f"Email: truongcongdinh97tcd@gmail.com"
        )
    
    def _paste_license_json(self):
        """Paste license JSON from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        
        # Validate JSON format
        try:
            json.loads(text)
            self.license_json_input.setPlainText(text)
            QMessageBox.information(
                self,
                "Pasted",
                "✅ License JSON pasted successfully!\n\nClick 'Activate License' to continue."
            )
        except json.JSONDecodeError:
            QMessageBox.warning(
                self,
                "Invalid JSON",
                "❌ Clipboard does not contain valid JSON.\n\n"
                "Make sure you copied the entire license file content."
            )
    

    def _load_from_file(self):
        """Load license from JSON file"""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select License File",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    license_content = f.read()
                
                # Validate JSON
                json.loads(license_content)
                
                # Set to text area
                self.license_json_input.setPlainText(license_content)
                
                QMessageBox.information(
                    self,
                    "Loaded",
                    f"License loaded from file:\n{Path(filename).name}\n\n"
                    f"Click 'Activate License' to continue."
                )
                
            except json.JSONDecodeError:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Invalid JSON file!\n\nPlease select a valid license file."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load file:\n{e}"
                )
    def update_status(self):
        """Update status labels and show/hide activation steps"""
        info = self.license_manager.get_license_info()
        
        # Status
        is_licensed = info['is_licensed']
        
        if is_licensed:
            license_data = info.get('license_data')
            if license_data:
                # Activated - HIDE activation steps
                self.activation_steps_widget.setVisible(False)
                
                self.status_label.setText("✅ ACTIVATED")
                self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 12pt;")
                
                self.trial_label.setText(
                    f"Licensed to: {license_data.get('customer_email', 'N/A')}"
                )
                self.trial_label.setStyleSheet("color: green;")
                
                # Show license details
                license_type = license_data.get('license_type', 'Standard')
                self.license_type_label.setText(f"License Type: {license_type}")
                
                expiration = license_data.get('expiration_date', 'Lifetime')
                self.expiration_label.setText(f"Expiration: {expiration}")
                
                device_id = license_data.get('device_id', 'N/A')
                self.device_id_status_label.setText(f"Device ID: {device_id[:16]}...")
                
                self.activate_btn.setVisible(False)
                self.deactivate_btn.setVisible(True)
                self.deactivate_btn.setEnabled(True)
            else:
                # Trial active - SHOW activation steps
                self.activation_steps_widget.setVisible(True)
                
                days_remaining = info['trial_days_remaining']
                self.status_label.setText(f"⏳ TRIAL MODE ({days_remaining} days left)")
                self.status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12pt;")
                
                self.trial_label.setText(
                    f"Trial expires in {days_remaining} days - All features unlocked"
                )
                self.trial_label.setStyleSheet("color: orange;")
                
                # Clear license details
                self.license_type_label.setText("License Type: Trial")
                self.expiration_label.setText(f"Expiration: {days_remaining} days")
                self.device_id_status_label.setText("")
                
                self.activate_btn.setVisible(True)
                self.deactivate_btn.setVisible(False)
        else:
            # Trial expired - SHOW activation steps
            self.activation_steps_widget.setVisible(True)
            
            self.status_label.setText("❌ TRIAL EXPIRED")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
            
            self.trial_label.setText("Please purchase a license to continue using the software")
            self.trial_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Clear license details
            self.license_type_label.setText("License Type: None")
            self.expiration_label.setText("Expiration: Expired")
            self.device_id_status_label.setText("")
            
            self.activate_btn.setVisible(True)
            self.deactivate_btn.setVisible(False)
        
        # Platform
        import platform
        self.platform_label.setText(
            f"{platform.system()} {platform.release()} ({platform.machine()})"
        )
    
    def activate_license(self):
        """Activate license with JSON from input"""
        license_json = self.license_json_input.toPlainText().strip()
        
        if not license_json:
            QMessageBox.warning(
                self,
                "No License Entered",
                "⚠️ Please paste your license JSON in Step 2 first."
            )
            return
        
        # Validate JSON
        try:
            license_data = json.loads(license_json)
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Invalid JSON",
                f"❌ Invalid JSON format:\n\n{str(e)}\n\n"
                "Please paste the complete license file content."
            )
            return
        
        # Check required fields
        required_fields = ['device_id', 'license_id', 'issued_date', 'signature']
        missing = [f for f in required_fields if f not in license_data]
        if missing:
            QMessageBox.critical(
                self,
                "Incomplete License",
                f"❌ License missing required fields:\n\n"
                + "\n".join(f"- {f}" for f in missing)
            )
            return
        
        # Attempt activation
        success, message = self.license_manager.activate_license(license_json)
        
        if success:
            QMessageBox.information(
                self,
                "✅ Activation Successful!",
                f"{message}\n\n"
                "🎉 Thank you for purchasing DMX Master!\n\n"
                "Your license is now permanently activated on this computer.\n"
                "You can use the software offline anytime."
            )
            self.update_status()
            
            # Auto-close dialog after successful activation
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "❌ Activation Failed",
                f"{message}\n\n"
                "<b>Common issues:</b>\n"
                "• License was generated for a different Device ID\n"
                "• License file is corrupted or incomplete\n"
                "• License signature is invalid\n\n"
                "Please contact support if the problem persists."
            )
    
    def deactivate_license(self):
        """Deactivate current license (for testing)"""
        reply = QMessageBox.question(
            self,
            "Deactivate License?",
            "⚠️ Are you sure you want to deactivate this license?\n\n"
            "You will need to re-enter the license JSON to activate again.\n"
            "This action is typically only needed if you're transferring the license.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Deactivate license in license manager
            self.license_manager.deactivate_license()
            
            # Clear JSON input
            self.license_json_input.clear()
            self.update_status()
            
            QMessageBox.information(
                self,
                "Deactivated",
                " License has been deactivated.\\n\\n"
                "You are now using Trial mode.\\n"
                "Contact the software author if you need to transfer this license to a new computer.\n\n"
                "Contact the software author if you need to transfer this license to a new computer."
            )
