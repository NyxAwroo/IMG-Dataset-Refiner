# **📊 IMG Dataset Refiner (v3.0 Pro)**

<div align="center">
  <img src="https://github.com/NyxAwroo/IMG-Dataset-Refiner/raw/main/logotype/logo.jpg" alt="IMG Dataset Refiner Logo" width="250"/>
</div>

![English](https://img.shields.io/badge/Language-English-blue?style=flat-square) ![Français](https://img.shields.io/badge/Langue-Fran%C3%A7ais-blue?style=flat-square)

**The ultimate tool for management, balancing, pre-processing, and AI assistance (VLM/LLM) for model training preparation (LoRA, SDXL, Flux)** [Installation](#bookmark=id.93ne4h8eoc6q) • [What's new in v3](#bookmark=id.uer02e3me5fz) • [Features](#bookmark=id.4b2b3rabed25) • [Workflow](#bookmark=id.o7c1e8yukqn)

## **🎯 About**

![Main Interface Preview](https://github.com/NyxAwroo/IMG-Dataset-Refiner/raw/main/screenshots%20demo/Firefox_Screenshot_2026-05-04T14-19-20.248Z.png)

**IMG Dataset Refiner** (formerly *Datasets Images EditSelect*) is a "desktop-like" software suite designed for AI model creators. Powered by **Gradio** with native JavaScript injections for optimal performance, this tool allows you to **visualize, pre-process, clean, analyze via AI, and export** your image datasets with surgical precision.

## **🚀 What's New in v3.0 Pro**

This major update transforms the tool into a true Data Engineering suite with visual and semantic analysis capabilities:

* **🤖 Local AI Assistant (Ollama / LM Studio):** Connect the tool to your local LLMs and VLMs (Llama 3, Qwen-VL, LLaVA) to auto-tag, track hallucinations, isolate concepts, or translate your tags into natural language (ideal for Flux).  
* **🖼️ Duplicate Tracking & Pre-processing:** Visual duplicate scanner (Perceptual Hashing), intelligent face cropping (OpenCV), automatic transparency (Alpha) correction, and mass resizing/renaming.  
* **🧬 Advanced Audits:** Co-occurrence matrix (Heatmap) to spot "Concept Bleeding", resolution distribution chart (Bucketing), and logical contradiction hunter.  
* **🪄 Native Intellisense:** The viewer now integrates an ultra-fast smart autocomplete that suggests existing tags from your dataset as you type.  
* **Pro Interface & Onboarding:** Added contextual help menus, quick start guides, and on-the-fly language switching (FR/EN) across all advanced modules.

*(Check the Changelog.md to review the ergonomic additions from v2.0 like Windows-style selection and auto-save).*

## **📸 Gallery & Preview**

### **🎬 Main Interface & Autocomplete**

*(Insert your screenshots here)*

### **🤖 Local AI Assistant & Profiling**

*(Insert your screenshots here)*

### **📈 Advanced Charts (Co-occurrence & Bucketing)**

*(Insert your screenshots here)*

## **🌟 Main Features**

### **🤖 AI Assistant (VLM & LLM)**

| Feature | Description |
| :---- | :---- |
| **Auto-Tagging / Super OCR** | The VLM reads the image from scratch, extracts visual details and embedded text (text: "..."). |
| **Reality Check (Anti-Hallucination)** | The VLM verifies your existing tags and automatically removes those that are not in the image. |
| **Concept Isolator (LoRA Special)** | The AI describes the environment but intentionally *ignores* the central subject to protect your Trigger Word. |
| **Visual Translator (Flux/SD3)** | An LLM converts your Booru-style keyword lists into beautiful, fluent descriptive sentences. |
| **Custom Prompt & Templates** | Create your own AI instructions and save them as "Templates". |

### **🖼️ Image Pre-processing & Duplicates**

| Feature | Description |
| :---- | :---- |
| **Visual Duplicate Scanner** | Detects near-identical images (cropped, resized) via ImageHash with a tolerance slider. |
| **Smart Face Crop** | Automatically crops the image around the face detected by OpenCV AI. |
| **Alpha Standardization** | Spots transparent PNGs and replaces the background with white to avoid noise during training. |
| **Batch Resize & Rename** | Resizing (Pillow), conversion (WebP/JPEG), and global folder renaming in 1 click. |

### **👁️ Gallery, Viewer & Editor**

| Feature | Description |
| :---- | :---- |
| **Ultra-Fast Selection** | \[Ctrl+Click\], \[Shift+Click\], \[Ctrl+A\] with dynamic highlighting handled client-side. |
| **Intellisense** | Dynamic tag autocomplete during manual entry. |
| **Custom Context Menu** | Right-click on the image for quick access to essential actions. |
| **Batch Editing** | Regex, synonym replacement, spaces and commas cleanup on thousands of images at once. |

### **📈 Statistics & Balancing**

| Feature | Description |
| :---- | :---- |
| **Dataset Audits** | Co-occurrence heatmap, resolutions scatter plot, and logical contradictions detection (e.g., *day* AND *night*). |
| **"Excel-like" Table & Drag/Drop** | Drag and drop to reorganize your tag priorities instantly. |
| **Smart Export Assistant** | "Greedy" algorithm to balance image distribution according to precise target percentages. |

## **🚀 Installation & Launch**

### **Prerequisites**

* **Python 3.10+**  
* A local AI engine (e.g., **Ollama**, **LM Studio**, or **KoboldCPP**) for the AI Assistant features.  
* Git

### **Steps**

1. **Clone the repository**  
   git clone \[https://github.com/BC8069EA84/Datasets-Images-EditSelect.git\](https://github.com/BC8069EA84/Datasets-Images-EditSelect.git)  
   cd Datasets-Images-EditSelect

2. **Install dependencies** *(Updated for v3.0)*  
   pip install gradio pandas plotly imagehash opencv-python requests Pillow

3. **Launch the tool**  
   python lora\_manager.py

4. **Access the interface** The interface will automatically open in your default browser (on 127.0.0.1).

## **💡 How it works? (Recommended Workflow)**

1️⃣ **Pre-processing (🖼️ Tab)** └─ Clean visual duplicates, rename your files, and crop/resize your images in bulk.  
2️⃣ **Artificial Intelligence (🤖 Tab)** └─ Run auto-tagging via VLM, or convert your tags to sentences via LLM if you are targeting a Flux model.  
3️⃣ **Audit & Statistics (📈 Tab)** └─ Use the *Reality Check* and generate advanced charts to ensure no unwanted tags "bleed" onto your concept (Concept Bleeding).  
4️⃣ **Final Cleanup & Editing (👁️ and ⚡ Tabs)** └─ Complete your tags manually with Intellisense and use the Batch Editor to fix remaining typos.  
5️⃣ **Strategic Export (📁 Tab)** └─ Enter your target %, simulate the balance, and export a perfect dataset ready for training\!

## **📦 Project Structure**

IMG-Dataset-Refiner/    
├── lora\_manager.py          \# Main entry point (Business logic and UI)    
├── Changelog.md             \# Update history (v2.0 & v3.0 Pro)    
├── en.json                  \# English language dictionary    
├── fr.json                  \# French language dictionary    
├── lora\_recipes.json        \# Saves of your export configurations  
├── ai\_recipes.json          \# Saves of your Custom AI prompts  
├── README.md                \# This documentation    
├── requirements.txt         \# Python dependencies    
└── screenshots demo/        \# Visual demonstration

## **🎓 Use Cases**

✅ Preparation of demanding datasets for **LoRA fine-tuning** (SD 1.5, SDXL, Flux)  
✅ Privacy-respecting **local auto-captioning**  
✅ Mathematical balancing of **multi-concept** datasets  
✅ Identification and resolution of **overfitting** issues via visual audits

## **📄 License**

Free to use and modify for your AI workflows.

## **🤝 Contribution**

Contributions are welcome\! Feel free to:

* Report bugs via Issues  
* Propose improvements  
* Submit Pull Requests

**Forged with ❤️ for the AI community** [⬆️ Back to top](#bookmark=id.jsyvg8l7x16z)
