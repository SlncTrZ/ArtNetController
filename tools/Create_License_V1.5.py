#!/usr/bin/env python3
"""
DMX Master - License Generator V1.5
====================================

Professional GUI tool for generating worldwide licenses for DMX Master application.

Features:
- Parse customer Device ID (64 character hex string)
- Generate cryptographically signed licenses
- Support for perpetual and trial licenses
- Copy to clipboard or save to file
- Input validation and error handling

Author: Truong Cong Dinh
Version: 1.5.0
Date: 2025-11-04

FIXED: Message format now uses pipe separators (device_id|license_id|issued_date)
       to match the application's verification logic.
"""

import sys
import os
import json
import base64
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QMessageBox, QFileDialog, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class LicenseGeneratorWindow(QMainWindow):
    """Main window for License Generator"""
    
    def __init__(self):
        super().__init__()
        self.private_key = None
        self.init_ui()
        self.load_private_key()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("DMX Master - License Generator V1.5")
        self.setMinimumSize(800, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🔑 DMX Master License Generator V1.5")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Generate worldwide licenses for DMX Master customers")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Customer Information Group
        customer_group = QGroupBox("Customer Information")
        customer_layout = QFormLayout()
        customer_layout.setSpacing(10)
        
        # Device ID input
        self.device_id_input = QLineEdit()
        self.device_id_input.setPlaceholderText("Paste 64-character Device ID from customer...")
        self.device_id_input.setMaxLength(64)
        self.device_id_input.textChanged.connect(self.validate_device_id)
        customer_layout.addRow("Device ID:", self.device_id_input)
        
        # Device ID validation label
        self.device_id_status = QLabel("")
        customer_layout.addRow("", self.device_id_status)
        
        # Customer email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("customer@example.com")
        customer_layout.addRow("Customer Email:", self.email_input)
        
        # License type
        self.license_type_combo = QComboBox()
        self.license_type_combo.addItems(["perpetual", "trial", "subscription"])
        customer_layout.addRow("License Type:", self.license_type_combo)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Generate Button
        self.generate_btn = QPushButton("🎯 Generate License")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_license)
        self.generate_btn.setEnabled(False)
        layout.addWidget(self.generate_btn)
        
        # Output Group
        output_group = QGroupBox("Generated License (JSON)")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(250)
        self.output_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        output_layout.addWidget(self.output_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        button_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("💾 Save to File")
        self.save_btn.clicked.connect(self.save_to_file)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        output_layout.addLayout(button_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Status bar
        self.statusBar().showMessage("Ready to generate licenses")
        
    def load_private_key(self):
        """Load RSA private key"""
        try:
            key_path = Path(__file__).parent / "rsa_keys" / "private_key.pem"
            
            if not key_path.exists():
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Private key not found at:\n{key_path}\n\nPlease ensure rsa_keys folder exists."
                )
                return
            
            with open(key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            self.statusBar().showMessage(f"✅ Private key loaded from {key_path.name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Private Key",
                f"Failed to load private key:\n{str(e)}"
            )
            
    def validate_device_id(self):
        """Validate Device ID input"""
        device_id = self.device_id_input.text().strip()
        
        if len(device_id) == 0:
            self.device_id_status.setText("")
            self.generate_btn.setEnabled(False)
            return
        
        # Check if it's valid hex and correct length
        if len(device_id) == 64 and all(c in '0123456789abcdefABCDEF' for c in device_id):
            self.device_id_status.setText("✅ Valid Device ID")
            self.device_id_status.setStyleSheet("color: green;")
            self.generate_btn.setEnabled(True)
        else:
            self.device_id_status.setText("❌ Invalid - must be 64 hex characters")
            self.device_id_status.setStyleSheet("color: red;")
            self.generate_btn.setEnabled(False)
            
    def generate_license(self):
        """Generate license with RSA signature"""
        try:
            # Get inputs
            device_id = self.device_id_input.text().strip().lower()
            email = self.email_input.text().strip()
            license_type = self.license_type_combo.currentText()
            
            # Validate
            if not email or '@' not in email:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid email address")
                return
            
            if not self.private_key:
                QMessageBox.critical(self, "Error", "Private key not loaded")
                return
            
            # Generate license data
            license_id = str(uuid.uuid4())
            issued_date = datetime.now().isoformat()
            
            license_data = {
                "device_id": device_id,
                "license_id": license_id,
                "issued_date": issued_date,
                "customer_email": email,
                "license_type": license_type,
                "version": "1.0.0"
            }
            
            # Create signature payload with CORRECT format (with pipe separators)
            # IMPORTANT: This matches the verification format in src/utils/license.py
            signature_payload = f"{device_id}|{license_id}|{issued_date}".encode()
            
            # Sign with RSA PSS
            signature = self.private_key.sign(
                signature_payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Add base64 encoded signature
            license_data["signature"] = base64.b64encode(signature).decode()
            
            # Display JSON
            license_json = json.dumps(license_data, indent=2)
            self.output_text.setPlainText(license_json)
            
            # Enable action buttons
            self.copy_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            # Store for later use
            self.current_license = license_json
            self.current_device_id = device_id
            
            self.statusBar().showMessage(f"✅ License generated successfully for {email}")
            
            QMessageBox.information(
                self,
                "Success",
                f"License generated successfully!\n\n"
                f"License ID: {license_id}\n"
                f"Device ID: {device_id[:16]}...\n"
                f"Type: {license_type}\n\n"
                f"You can now copy or save the license."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate license:\n{str(e)}"
            )
            self.statusBar().showMessage("❌ License generation failed")
            
    def copy_to_clipboard(self):
        """Copy license JSON to clipboard"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_license)
            self.statusBar().showMessage("✅ License copied to clipboard")
            QMessageBox.information(self, "Copied", "License copied to clipboard!\n\nYou can now paste it to send to customer.")
        except Exception as e:
            QMessageBox.warning(self, "Copy Failed", f"Failed to copy to clipboard:\n{str(e)}")
            
    def save_to_file(self):
        """Save license to JSON file"""
        try:
            # Suggest filename
            suggested_name = f"license_{self.current_device_id[:8]}.json"
            
            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save License File",
                suggested_name,
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_license)
                
                self.statusBar().showMessage(f"✅ License saved to {Path(file_path).name}")
                QMessageBox.information(
                    self,
                    "Saved",
                    f"License saved successfully to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save license:\n{str(e)}"
            )


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DMX Master License Generator")
    app.setApplicationVersion("1.5.0")
    
    window = LicenseGeneratorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
