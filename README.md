# 🛡️ AI-Powered Real-Time Phishing Website Detector

Real-time phishing website detection using Machine Learning with automatic browser protection.

![Project Banner](https://img.shields.io/badge/AI-Phishing%20Detector-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![Accuracy](https://img.shields.io/badge/Accuracy-96.8%25-success)

---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Model Performance](#model-performance)
- [Screenshots](#screenshots)
- [Team](#team)
- [License](#license)

---

## 🎯 Overview

Phishing attacks are one of the most dangerous cyber threats, causing billions in financial losses annually. This project implements an **AI-powered real-time phishing detection system** that automatically protects users while browsing.

### Key Highlights:
- ✅ **96.8% Accuracy** on 235K URL dataset
- ✅ **Real-time Protection** via Chrome extension
- ✅ **Automatic Detection** - No manual checking needed
- ✅ **Indian Domain Support** - Government & banking sites
- ✅ **Instant Warnings** - Visual alerts and notifications

---

## ✨ Features

### 🔒 Security Features
- **Automatic URL Scanning** - Every website checked in real-time
- **Visual Warnings** - Red banner alerts for phishing sites
- **Desktop Notifications** - System-level threat alerts
- **Badge Indicators** - Quick visual status on extension icon
- **Smart Caching** - Avoid re-checking same URLs (1-hour cache)

### 🧠 Machine Learning Features
- **50+ Features Analyzed** - URL structure, webpage content, security indicators
- **Random Forest Algorithm** - Ensemble learning for high accuracy
- **Feature Importance** - Understand what makes sites suspicious
- **Confidence Scores** - Percentage-based threat assessment
- **Adaptive Learning** - Regular model updates possible

### 🌐 User Features
- **One-Click Manual Check** - Extension popup for detailed analysis
- **Risk Level Classification** - Very Low, Low, Medium, High, Very High
- **Trusted Domain Whitelist** - Pre-approved safe sites
- **Government Domain Support** - Auto-trust .gov.in, .edu.in, etc.
- **HTTPS Preference** - Boost secure connections

---

## 🛠️ Technology Stack

### Backend
- **Language:** Python 3.8+
- **Framework:** Flask 3.0
- **ML Library:** scikit-learn 1.3.2
- **Data Processing:** pandas, numpy
- **Web Scraping:** BeautifulSoup4, Requests

### Frontend
- **Browser Extension:** Chrome Extension API (Manifest V3)
- **UI:** HTML5, CSS3, JavaScript (ES6)
- **Notifications:** Chrome Notifications API
- **Storage:** Chrome Storage API

### Dataset
- **Name:** PhiUSIIL Phishing URL Dataset
- **Size:** 235,795 URLs
- **Legitimate URLs:** 134,850 (57.2%)
- **Phishing URLs:** 100,945 (42.8%)
- **Features:** 54 attributes (50 used after preprocessing)
- **Source:** Kaggle

---

## 📁 Project Structure

