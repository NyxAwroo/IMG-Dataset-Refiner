# **📊 Datasets Images EditSelect (v2.0)**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Gradio](https://img.shields.io/badge/Gradio-Framework-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-Libre-green?style=for-the-badge)

LANGUAGES : FR / EN

**An ultra-responsive local dataset manager and balancer for AI model training preparation (Flux, Qwen, SDXL, LoRA).**  
[Installation](#bookmark=id.r78gz1o935wj) • [New in v2.0](#bookmark=id.k7st63vr03ju) • [Features](#bookmark=id.a21ym3xlglf5) • [Workflow](#bookmark=id.wsejnwy0fpx0)

</div>

## **🎯 About**

Built with **Gradio** and powered by native JavaScript injections for optimal performance, this tool allows you to **visualize, clean, analyze, and export** your image datasets. Far from a simple web interface, the application offers ergonomics worthy of true desktop software ("desktop-like"), designed to drastically speed up your data preparation workflow.

## **📸 Interface Preview**
![Datasets Images EditSelect - Vue Principale](https://github.com/NyxAwroo/Datasets-Images-EditSelect/blob/main/screenshots%20demo/Firefox_Screenshot_2026-05-04T14-19-20.248Z.png)


## **🚀 Major New Features in v2.0**

This update completely transforms the user experience through extensive JavaScript optimizations and full compatibility with Gradio 4+.

### **🖱️ "Windows-Style" Navigation**

* **Instant selection (zero blinking):** Processing is now 100% JavaScript.  
* **Native shortcuts:** Support for \[Ctrl \+ Click\] (add/remove), \[Shift \+ Click\] (range selection), and \[Ctrl \+ A\] (select all).  
* **Context Menu (Right Click):** Quick actions directly on gallery images (Save, Add to stats, Clear selection).

### **⚡ Editing and Productivity**

* **Silent Auto-Save:** No need to click "Save" anymore. Saving is done automatically in the background, creating a .bak security file while you navigate.  
* **"Excel-like" Tables:** Click on a cell and type your value to instantly overwrite the old one (without using the Backspace key).  
* **Smart Swap 2.0:** Anti-duplicate protection when modifying priorities; tags swap spots intelligently.  
* **Indestructible Drag & Drop:** Reorganize table rows via drag & drop, rewritten to withstand dynamic UI reloads.

### **⌨️ New Keyboard Shortcuts**

* **Secured (AZERTY/QWERTY):** Total independence from your keyboard layout language.  
* \[Alt \+ Up/Down Arrow\]: Move the selected row in the recipe table.  
* \[Ctrl \+ F\]: Direct focus on the search bar.

## **🌟 Main Features**

### **👁️ Advanced Viewer & Editor**

* **Robust Highlighting (Regex):** Tracked keywords light up in yellow in your captions, even with complex terms or HTML.  
* **CLIP Token Counter:** Visual red warning if your caption exceeds the usual limit (\> 225 tokens).  
* **Quick Input Panel:** Dropdown menus under the recipe table for instant target changes.

### **⚡ Batch Editing (Mass Actions)**

* **Synonym Management (LoRA Expert):** Intelligent replacement of repetitive tags with a rotating list of synonyms.  
* **Find/Replace (Regex):** Support for regular expressions for deep cleaning.  
* **Automatic Cleaning:** Removal of multiple commas, extra spaces, and duplicate tags.

### **📈 Statistics & Balancing**

* **Instant Calculation:** Charts (Plotly) update in real-time as you type without triggering infinite loops.  
* **Orphan Tag Hunter:** Detects typos or unique tags.  
* **Markdown/CivitAI Export:** One-click generation of a clean table of your statistics, ready to be shared.

### **📁 Intelligent Export Assistant**

Three export strategies for all needs:

1. **Auto Balancing (Greedy):** Selects the combination of images that comes closest to your target (%).  
2. **Priority:** Fills the dataset in the priority order of your tags.  
3. **Classic Filter:** Only keeps images containing specific tags.

## **💡 Recommended Workflow**

1. 📂 **Load your folder** (containing your image \+ .txt pairs).  
2. 📊 **Analyze your data** (*Statistics* Tab → "Fill with Top 20").  
3. 🎯 **Define your targets** (Adjust priorities and percentages in the Export Assistant).  
4. 🧹 **Clean & Edit** (Use multi-selection mode and the Batch Editor).  
5. 🚀 **Export** (Simulate, then export your final dataset).

## **💻 Installation & Launch**

**Prerequisites:** Python 3.10+ and Git.  
\# 1\. Clone the repository  
git clone \[https://github.com/BC8069EA84/Datasets-Images-EditSelect.git\](https://github.com/BC8069EA84/Datasets-Images-EditSelect.git)  
cd Datasets-Images-EditSelect

\# 2\. Install dependencies  
pip install gradio pandas plotly

\# 3\. Launch the tool  
python lora\_manager.py

*The interface will automatically open in your default browser at 127.0.0.1.*

## **📦 Project Structure**

Datasets-Images-EditSelect/  
├── lora\_manager.py          \# Main entry point (Backend logic & UI)  
├── Changelog.md             \# Update history  
├── en.json                  \# Dictionary (English)  
├── fr.json                  \# Dictionary (French)  
├── README.md                \# Documentation (This file)  
├── requirements.txt         \# Dependencies  
└── screenshots demo/        \# Presentation images

## **🎓 Use Cases**

* ✅ Dataset preparation for **LoRA fine-tuning**.  
* ✅ Balancing **multi-concept** datasets.  
* ✅ **Mass** cleaning and correction of captions.  
* ✅ Intelligent export with precise constraints.

## **🤝 Contribution & License**

This project is **Open-Source** and free to use or modify for your AI workflows.  
Contributions are welcome\! Feel free to report bugs via *Issues*, or submit your *Pull Requests*.
