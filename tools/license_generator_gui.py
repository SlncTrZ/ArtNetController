#!/usr/bin/env python3
"""
License Generator GUI - Admin Tool
===================================

Simple GUI application for generating customer licenses.
Just enter customer email and device ID, then click Generate!

Author: Trương Công Định
Email: truongcongdinh97tcd@gmail.com
"""

import sys
import json
import hashlib
import base64
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox,
    QFileDialog, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("❌ Missing cryptography library!")
    print("   Install: pip install cryptography")
    sys.exit(1)


class LicenseGeneratorGUI(QMainWindow):
    """Main window for license generation"""
    
    def __init__(self):
        super().__init__()
        self.private_key = None
        self.init_ui()
        self.load_private_key()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Art-Net Controller - License Generator")
        self.setMinimumSize(700, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🔐 License Generator")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Customer Info Group
        customer_group = QGroupBox("Customer Information")
        customer_layout = QVBoxLayout()
        
        # Email
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("customer@example.com")
        email_layout.addWidget(self.email_input)
        customer_layout.addLayout(email_layout)
        
        # Device ID
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device ID:"))
        self.device_input = QLineEdit()
        self.device_input.setPlaceholderText("Paste device ID from customer here...")
        device_layout.addWidget(self.device_input)
        customer_layout.addLayout(device_layout)
        
        # License Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("License Type:"))
        self.license_type = QComboBox()
        self.license_type.addItems(["perpetual", "trial", "subscription"])
        type_layout.addWidget(self.license_type)
        type_layout.addStretch()
        customer_layout.addLayout(type_layout)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🔑 Generate License")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_license)
        btn_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("💾 Save to File")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_license)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        # Output Group
        output_group = QGroupBox("Generated License JSON")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setPlaceholderText("License JSON will appear here...")
        output_layout.addWidget(self.output_text)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        output_layout.addWidget(copy_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)
    
    def load_private_key(self):
        """Load RSA private key"""
        key_path = Path(__file__).parent / "rsa_keys" / "private_key.pem"
        
        if not key_path.exists():
            self.status_label.setText("❌ Private key not found! Run generate_rsa_keys.py first")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc; color: red;")
            self.generate_btn.setEnabled(False)
            return
        
        try:
            with open(key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            self.status_label.setText(f"✅ Private key loaded: {key_path}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc; color: green;")
        except Exception as e:
            self.status_label.setText(f"❌ Error loading private key: {e}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc; color: red;")
            self.generate_btn.setEnabled(False)
    
    def generate_license(self):
        """Generate license JSON"""
        # Validate inputs
        email = self.email_input.text().strip()
        device_id = self.device_input.text().strip()
        
        if not email:
            QMessageBox.warning(self, "Error", "Please enter customer email!")
            return
        
        if not device_id:
            QMessageBox.warning(self, "Error", "Please enter device ID!")
            return
        
        if '@' not in email:
            QMessageBox.warning(self, "Error", "Invalid email format!")
            return
        
        if len(device_id) != 64:
            QMessageBox.warning(self, "Error", "Device ID should be 64 characters (SHA256)!")
            return
        
        try:
            # Generate license ID
            license_id = hashlib.sha256(f"{email}{device_id}{datetime.now()}".encode()).hexdigest()[:8]
            license_id = f"{license_id[:8]}-{hashlib.sha256(device_id.encode()).hexdigest()[:4]}-{hashlib.sha256(email.encode()).hexdigest()[:4]}-{hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:4]}-{hashlib.sha256(f'{email}{device_id}'.encode()).hexdigest()[:12]}"
            
            # Create license data
            license_data = {
                "device_id": device_id,
                "license_id": license_id,
                "issued_date": datetime.now().isoformat(),
                "customer_email": email,
                "license_type": self.license_type.currentText(),
                "version": "1.0.0"
            }
            
            # Create signature payload
            signature_payload = f"{device_id}{license_id}{license_data['issued_date']}".encode()
            
            # Sign with private key
            signature = self.private_key.sign(
                signature_payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Add signature to license
            license_data["signature"] = base64.b64encode(signature).decode()
            
            # Format JSON
            self.current_license = json.dumps(license_data, indent=2)
            self.output_text.setText(self.current_license)
            
            # Enable save button
            self.save_btn.setEnabled(True)
            
            # Update status
            self.status_label.setText(f"✅ License generated for {email}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc; color: green;")
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"License generated successfully!\n\n"
                f"License ID: {license_id}\n"
                f"Email: {email}\n"
                f"Type: {self.license_type.currentText()}\n\n"
                f"You can now copy or save the license."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate license:\n{e}")
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc; color: red;")
    
    def save_license(self):
        """Save license to file"""
        if not hasattr(self, 'current_license'):
            return
        
        email = self.email_input.text().strip()
        safe_email = email.replace('@', '_at_').replace('.', '_')
        default_name = f"license_{safe_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Create output directory
        output_dir = Path(__file__).parent / "generated_licenses"
        output_dir.mkdir(exist_ok=True)
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save License",
            str(output_dir / default_name),
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.current_license)
                
                QMessageBox.information(
                    self,
                    "Saved",
                    f"License saved to:\n{filename}\n\n"
                    f"Send this file to the customer."
                )
                
                self.status_label.setText(f"✅ License saved: {Path(filename).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
    
    def copy_to_clipboard(self):
        """Copy license JSON to clipboard"""
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("✅ License copied to clipboard!")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc; color: green;")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    window = LicenseGeneratorGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
