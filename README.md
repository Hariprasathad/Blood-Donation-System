# 🩸 BloodLink - Every Drop Counts
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask-red.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/database-MySQL-orange.svg)](https://www.mysql.com/)

**BloodLink** is a modern, premium Blood Donation Management System designed specifically for the Indian context. It connects blood donors with patients in real-time, featuring a high-end UI, AI-enhanced descriptions, and multi-language support.

---

## ✨ Key Features

- **🚀 Premium UI/UX**: Built with the **Outfit** font, glassmorphism effects, and dynamic gradients for a high-end tech feel.
- **🇮🇳 Indian Context**: All placeholders (Names, Phones, Cities) are tailored for Indian users (e.g., +91 format, Indian cities).
- **🤖 AI Grammar Enhancement**: Integrated with **Google Gemini AI** to automatically polish and enhance blood request descriptions.
- **🌍 Multilingual Ticker**: A smooth scrolling footer featuring humanitarian messages in English, Tamil, Hindi, Telugu, Malayalam, Kannada, Bengali, and Arabic.
- **🔐 Secure Authentication**: 
  - Email OTP verification for registration.
  - Enforced 8-character minimum security codes.
  - Secure session management.
- **📋 Real-time Tracking**: 
  - Manage and track blood requests with serial numbers.
  - Verified contact information for both patients and donors.
  - One-click "Call" functionality for mobile users.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.8+, Flask
- **AI**: Google Generative AI (Gemini Pro)
- **Database**: MySQL
- **Email**: Flask-Mail (SMTP Integration)
- **Styling**: Vanilla CSS3 (Modern Flexbox/Grid, Animations)
- **Icons**: FontAwesome 6.0
- **Environment**: python-dotenv

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.8 or higher installed.
- MySQL Server running on your local machine.

### 2. Clone & Install
```bash
# Clone the repository
git clone <repository-url>
cd Blood-Donation-System

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and fill in your details (refer to `.env.example`):

```ini
SECRET_KEY=your_secret_key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=blood_donation
GEMINI_API_KEY=your-gemini-api-key
```

### 4. Run the Application
```bash
python app.py
```
*The system will automatically initialize the MySQL database and create all required tables on the first run.*

---

## 📊 Database Schema

The system initializes with four core tables:
1. `users`: Stores member profiles and secure credentials.
2. `donors`: Manages blood requests and hospital locations.
3. `approvals`: Tracks donor matches and fulfillment timestamps.
4. `daily_stats`: Monitors AI tool usage for system health.

---

## 🤝 Contributing
Contributions are welcome! If you're looking to help save lives through code, feel free to fork this platform and submit a PR.

---

## 📄 License
Designed for Impact. © 2024 **BloodLink India**. 🇮🇳
