import gradio as gr
import os
import re
import shutil
import json
import io
import copy
import requests
import base64
import plotly.express as px
import pandas as pd
from collections import Counter, defaultdict
from PIL import Image

# Import ImageHash (Point 8)
try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

# Import OpenCV pour le Smart Crop (Point 10)
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# ==========================================
# CONFIGURATION & DICTIONNAIRES DE LANGUE
# ==========================================

RECIPES_FILE = "lora_recipes.json"
AI_RECIPES_FILE = "ai_recipes.json" 
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"

MSG = {"FR": {}, "EN": {}}
UI_T = {"FR": {}, "EN": {}}

# Dictionnaire de contradictions logiques
CONTRADICTIONS_LOGIQUES = [
    ("day", "night"), ("daytime", "night"),
    ("solo", "multiple girls"), ("solo", "multiple boys"),
    ("indoors", "outdoors"), ("outside", "inside"),
    ("1girl", "1boy"), ("monochrome", "colorful")
]

def load_languages():
    for lang in ["FR", "EN"]:
        filepath = f"{lang.lower()}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                MSG[lang] = data.get("MSG", {})
                UI_T[lang] = data.get("UI_T", {})
        else:
            print(f"⚠️ Fichier de langue '{filepath}' introuvable.")

load_languages()

# ==========================================
# STYLES CSS NATIFS & JAVASCRIPT GLOBAL
# ==========================================
css_code = """
#left_panel { resize: horizontal; overflow-x: hidden; overflow-y: auto; width: 380px; min-width: 250px; max-width: 70vw; flex: none !important; border-right: 2px solid #374151; padding-right: 15px; transition: min-width 0.3s ease, width 0.3s ease, padding 0.3s ease, opacity 0.3s ease; }
#left_panel.collapsed { width: 0px !important; min-width: 0px !important; padding: 0px !important; margin: 0px !important; border: none !important; opacity: 0; pointer-events: none; }
.caption-label { font-size: 14px !important; font-weight: bold !important; color: #4ade80 !important; display: none !important; }
.custom-selected { outline: 4px solid #ff8800 !important; outline-offset: -4px !important; box-shadow: inset 0 0 20px rgba(255, 136, 0, 0.9) !important; border-radius: 8px !important; }
.custom-selected img { filter: sepia(0.8) hue-rotate(330deg) saturate(3) !important; opacity: 0.8 !important; }
#hidden_sync_input, #hidden_sync_btn, #hidden_calc_btn, #hidden_dnd_input, #hidden_dnd_btn, #hidden_tags_input, #hidden_ai_prompt_update { display: none !important; }
.gradio-dataframe tbody tr { transition: background-color 0.2s, opacity 0.2s; }
.gradio-dataframe tbody tr[draggable="true"] { cursor: grab !important; }
.gradio-dataframe tbody tr.dragging { opacity: 0.4; background-color: rgba(255, 136, 0, 0.3) !important; outline: 2px dashed #ff8800; outline-offset: -2px;}
#autocomplete-list { position: absolute; border: 1px solid #555; background-color: #1f2937; z-index: 9999; max-height: 150px; overflow-y: auto; border-radius: 4px; box-shadow: 0px 4px 6px rgba(0,0,0,0.5); }
#autocomplete-list div { padding: 8px; cursor: pointer; color: #fff; font-size: 14px; }
#autocomplete-list div:hover, #autocomplete-list div.autocomplete-active { background-color: #4ade80; color: #000; }
.info-box { background-color: rgba(74, 222, 128, 0.1); border-left: 4px solid #4ade80; padding: 10px; margin-bottom: 15px; border-radius: 4px; }
.ai-desc-box { background-color: #1e293b; border: 1px solid #334155; padding: 12px; border-radius: 6px; font-size: 0.95em; color: #cbd5e1; margin-top: 5px; }
"""

custom_js = """
function() {
    if (window.__DIES_INJECTED) return;
    window.__DIES_INJECTED = true;
    document.body.classList.add('dark');
    window.gallerySelectedIndices = new Set();
    window.lastClickedIndex = -1;
    window.allDatasetTags = [];

    function updateGalleryVisuals() { document.querySelectorAll('#main_gallery button').forEach((btn, idx) => { btn.classList.toggle('custom-selected', window.gallerySelectedIndices.has(idx)); }); }
    function syncWithPython(viewIndex) {
        const payload = { selected: Array.from(window.gallerySelectedIndices), viewIndex: viewIndex };
        const wrapper = document.getElementById('hidden_sync_input');
        const inputEl = wrapper ? wrapper.querySelector('textarea, input') : null;
        if (inputEl) {
            inputEl.value = JSON.stringify(payload);
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(() => { const btn = document.getElementById('hidden_sync_btn'); if (btn) btn.click(); }, 30);
        }
    }

    function setupAutocomplete() {
        const captionWrappers = document.querySelectorAll('#viewer_caption_area textarea');
        if (captionWrappers.length === 0) return;
        const inp = captionWrappers[0];
        if(inp.dataset.acSetup) return;
        inp.dataset.acSetup = "true";
        let currentFocus;
        inp.addEventListener("input", function(e) {
            let a, b, i, val = this.value; closeAllLists(); if (!val) return false;
            let lastCommaIdx = val.lastIndexOf(','); let currentWord = val.substring(lastCommaIdx + 1).trimStart();
            let prefix = val.substring(0, lastCommaIdx + 1); if(val.length > 0 && val[lastCommaIdx+1] === ' ') prefix += ' ';
            if (currentWord.length < 2) return false;
            currentFocus = -1; a = document.createElement("DIV"); a.setAttribute("id", "autocomplete-list"); this.parentNode.appendChild(a);
            const tagsInput = document.getElementById('hidden_tags_input');
            if(tagsInput) { const rawTags = tagsInput.querySelector('textarea, input')?.value || ""; if(rawTags) window.allDatasetTags = rawTags.split('|'); }
            let matches = 0;
            for (i = 0; i < window.allDatasetTags.length; i++) {
                if (window.allDatasetTags[i].toLowerCase().includes(currentWord.toLowerCase())) {
                    matches++; if(matches > 10) break;
                    b = document.createElement("DIV");
                    let matchIdx = window.allDatasetTags[i].toLowerCase().indexOf(currentWord.toLowerCase());
                    let highlighted = window.allDatasetTags[i].substring(0, matchIdx) + "<strong>" + window.allDatasetTags[i].substring(matchIdx, matchIdx + currentWord.length) + "</strong>" + window.allDatasetTags[i].substring(matchIdx + currentWord.length);
                    b.innerHTML = highlighted; b.innerHTML += "<input type='hidden' value='" + window.allDatasetTags[i] + "'>";
                    b.addEventListener("click", function(e) { inp.value = prefix + this.getElementsByTagName("input")[0].value + ", "; inp.dispatchEvent(new Event('input', { bubbles: true })); closeAllLists(); });
                    a.appendChild(b);
                }
            }
        });
        inp.addEventListener("keydown", function(e) {
            let x = document.getElementById("autocomplete-list"); if (x) x = x.getElementsByTagName("div");
            if (e.keyCode == 40) { currentFocus++; addActive(x); } else if (e.keyCode == 38) { currentFocus--; addActive(x); }
            else if (e.keyCode == 13 || e.keyCode == 9) { if (currentFocus > -1 && x) { e.preventDefault(); x[currentFocus].click(); } }
        });
        function addActive(x) { if (!x) return false; removeActive(x); if (currentFocus >= x.length) currentFocus = 0; if (currentFocus < 0) currentFocus = (x.length - 1); x[currentFocus].classList.add("autocomplete-active"); }
        function removeActive(x) { for (var i = 0; i < x.length; i++) x[i].classList.remove("autocomplete-active"); }
        function closeAllLists(elmnt) { var x = document.getElementsByClassName("autocomplete-list"); for (var i = 0; i < x.length; i++) { if (elmnt != x[i] && elmnt != inp) x[i].parentNode.removeChild(x[i]); } let list = document.getElementById("autocomplete-list"); if(list) list.remove(); }
        document.addEventListener("click", function (e) { closeAllLists(e.target); });
    }

    const observer = new MutationObserver(() => { 
        updateGalleryVisuals(); setupAutocomplete(); 
        const trackedWrapper = document.getElementById('tracked_words_input'); const trackedInput = trackedWrapper ? trackedWrapper.querySelector('textarea') : null;
        if (trackedInput && !trackedInput.dataset.commaListener) {
            trackedInput.dataset.commaListener = "true";
            trackedInput.addEventListener('keyup', function(e) { if (e.key === ',' || e.key === 'Enter') { setTimeout(() => document.getElementById('hidden_calc_btn')?.click(), 50); } });
            trackedInput.addEventListener('blur', function(e) { setTimeout(() => document.getElementById('hidden_calc_btn')?.click(), 50); });
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // SÉLECTION EXCEL-LIKE
    const svelteInputObserver = new MutationObserver((mutations) => {
        mutations.forEach(m => {
            m.addedNodes.forEach(node => {
                if (node.nodeType === 1) {
                    const input = node.tagName === 'INPUT' ? node : node.querySelector('input');
                    if (input && input.closest('.gradio-dataframe')) {
                        let tries = 0;
                        const selectInterval = setInterval(() => {
                            input.select();
                            if (tries++ > 15) clearInterval(selectInterval);
                        }, 20);
                    }
                }
            });
        });
    });
    svelteInputObserver.observe(document.body, { childList: true, subtree: true });

    // DRAG & DROP TABLEAU
    let dragStartIndex = -1;
    document.addEventListener('mousedown', function(e) {
        const tr = e.target.closest('.gradio-dataframe tbody tr');
        if (!tr) return;
        if (e.target.closest('input') || e.target.closest('textarea')) { tr.removeAttribute('draggable'); } 
        else { tr.setAttribute('draggable', 'true'); }
    });

    document.addEventListener('dragstart', function(e) {
        const tr = e.target.closest('tbody tr[draggable="true"]');
        if (tr) {
            dragStartIndex = Array.from(tr.parentNode.children).indexOf(tr);
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', dragStartIndex);
            setTimeout(() => tr.classList.add('dragging'), 0);
        }
    });

    document.addEventListener('dragover', function(e) {
        const draggingTr = document.querySelector('.dragging');
        const tr = e.target.closest('tbody tr');
        if (tr && draggingTr && tr !== draggingTr && tr.parentNode === draggingTr.parentNode) {
            e.preventDefault(); 
            const rect = tr.getBoundingClientRect();
            const mid = rect.top + rect.height / 2;
            if (e.clientY < mid) { tr.before(draggingTr); } else { tr.after(draggingTr); }
        }
    });

    document.addEventListener('dragend', function(e) {
        const tr = e.target.closest('tbody tr');
        if (tr) { tr.classList.remove('dragging'); tr.removeAttribute('draggable'); }
    });

    document.addEventListener('drop', function(e) {
        const tr = e.target.closest('tbody tr');
        if (tr) {
            e.preventDefault();
            const draggingTr = document.querySelector('.dragging');
            if(draggingTr) { draggingTr.classList.remove('dragging'); draggingTr.removeAttribute('draggable'); }
            
            const dragEndIndex = Array.from(tr.parentNode.children).indexOf(tr);
            if (dragStartIndex !== -1 && dragStartIndex !== dragEndIndex) {
                const wrapper = document.getElementById('hidden_dnd_input');
                const hiddenInput = wrapper ? wrapper.querySelector('textarea, input') : null;
                const hiddenBtn = document.getElementById('hidden_dnd_btn');
                if (hiddenInput && hiddenBtn) {
                    hiddenInput.value = dragStartIndex + "," + dragEndIndex;
                    hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => hiddenBtn.click(), 50);
                }
            }
        }
        dragStartIndex = -1;
    });

    // RACCOURCIS CLAVIERS
    window.addEventListener('keydown', function(e) {
        const tag = e.target.tagName.toLowerCase();
        const isInput = (tag === 'input' || tag === 'textarea');

        if (e.altKey && e.code === 'ArrowUp') { 
            e.preventDefault(); e.stopPropagation(); 
            document.getElementById('btn_move_up')?.click(); return; 
        }
        if (e.altKey && e.code === 'ArrowDown') { 
            e.preventDefault(); e.stopPropagation(); 
            document.getElementById('btn_move_down')?.click(); return; 
        }

        if (isInput && !e.altKey && !e.ctrlKey && !e.metaKey) return;

        if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyA' || e.key.toLowerCase() === 'a')) {
            if (isInput) return;
            e.preventDefault(); e.stopPropagation();
            const btns = document.querySelectorAll('#main_gallery button');
            window.gallerySelectedIndices.clear();
            btns.forEach((b, i) => window.gallerySelectedIndices.add(i));
            updateGalleryVisuals();
            syncWithPython(window.lastClickedIndex !== -1 ? window.lastClickedIndex : 0);
            return;
        }

        if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyF' || e.key.toLowerCase() === 'f')) {
            e.preventDefault(); e.stopPropagation();
            const searchBox = document.querySelector('input[placeholder*="mot"], input[placeholder*="word"]');
            if (searchBox) { searchBox.focus(); searchBox.select(); }
            return;
        }

        if (e.altKey && (e.code === 'KeyS' || e.key.toLowerCase() === 's')) {
            e.preventDefault(); e.stopPropagation();
            document.getElementById('toggle_tag_btn')?.click();
            return;
        }
        
        if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyS' || e.key.toLowerCase() === 's')) {
            e.preventDefault(); e.stopPropagation();
            document.getElementById('save_single_btn')?.click();
            return;
        }
        
        if (e.altKey && (e.code === 'KeyC' || e.key.toLowerCase() === 'c')) {
            e.preventDefault(); e.stopPropagation();
            document.getElementById('clear_sel_btn')?.click();
            return;
        }
        
        if (isInput) return;
        
        if (e.code === 'ArrowLeft' || e.key === 'ArrowLeft') { e.preventDefault(); document.getElementById('prev_btn')?.click(); }
        if (e.code === 'ArrowRight' || e.key === 'ArrowRight') { e.preventDefault(); document.getElementById('next_btn')?.click(); }
    }, true); 

    document.addEventListener('mousedown', function(e) {
        if (e.shiftKey && e.target.closest('#main_gallery')) { e.preventDefault(); }
    });

    // GESTION DU CLIC GALERIE
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('#main_gallery button');
        if (!btn) return;

        e.preventDefault(); e.stopPropagation();

        const btns = Array.from(document.querySelectorAll('#main_gallery button'));
        const index = btns.indexOf(btn);
        if (index === -1) return;

        const cbWrapper = document.getElementById('multi_cb');
        const isMultiChecked = cbWrapper ? (cbWrapper.querySelector('input[type="checkbox"]')?.checked || false) : false;

        if (e.shiftKey && window.lastClickedIndex !== -1) {
            const start = Math.min(window.lastClickedIndex, index);
            const end = Math.max(window.lastClickedIndex, index);
            if (!e.ctrlKey && !e.metaKey && !isMultiChecked) { window.gallerySelectedIndices.clear(); }
            for (let i = start; i <= end; i++) window.gallerySelectedIndices.add(i);
        } 
        else if (e.ctrlKey || e.metaKey || isMultiChecked) {
            if (window.gallerySelectedIndices.has(index)) window.gallerySelectedIndices.delete(index);
            else window.gallerySelectedIndices.add(index);
        } 
        else {
            window.gallerySelectedIndices.clear();
            window.gallerySelectedIndices.add(index); 
        }

        window.lastClickedIndex = index;
        updateGalleryVisuals();
        syncWithPython(index);
    }, true);

    // MENU CONTEXTUEL CLIC DROIT
    document.addEventListener('contextmenu', function(e) {
        const galleryBtn = e.target.closest('#main_gallery button');
        if (galleryBtn) {
            e.preventDefault();
            
            const btns = Array.from(document.querySelectorAll('#main_gallery button'));
            const index = btns.indexOf(galleryBtn);
            if(!window.gallerySelectedIndices.has(index)) {
                window.gallerySelectedIndices.clear();
                window.gallerySelectedIndices.add(index);
                window.lastClickedIndex = index;
                updateGalleryVisuals();
                syncWithPython(index);
            }

            let menu = document.getElementById('customContextMenu');
            if (!menu) {
                menu = document.createElement('div');
                menu.id = 'customContextMenu';
                menu.innerHTML = `
                    <div class="menu-item" onclick="document.getElementById('save_single_btn')?.click(); this.parentNode.style.display='none';">💾 Sauver Caption (Ctrl+S)</div>
                    <div class="menu-item" onclick="document.getElementById('toggle_tag_btn')?.click(); this.parentNode.style.display='none';">🪄 Ajouter Stats (Alt+S)</div>
                    <hr style="margin:4px 0; border-color:#444;">
                    <div class="menu-item" onclick="document.getElementById('clear_sel_btn')?.click(); this.parentNode.style.display='none';">🧹 Vider Sélection (Alt+C)</div>
                `;
                document.body.appendChild(menu);
            }
            menu.style.display = 'block';
            let x = e.pageX; let y = e.pageY;
            if (x + 200 > window.innerWidth) x = window.innerWidth - 210;
            if (y + 120 > window.innerHeight) y = window.innerHeight - 130;
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';
        }
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('#customContextMenu')) {
            const menu = document.getElementById('customContextMenu');
            if(menu) menu.style.display = 'none';
        }
    });
    
    setInterval(() => {
        const wrapper = document.getElementById('hidden_sync_input');
        const selInput = wrapper ? wrapper.querySelector('textarea, input') : null;
        if (selInput && selInput.value === '{}' && window.gallerySelectedIndices.size > 0) {
            window.gallerySelectedIndices.clear();
            updateGalleryVisuals();
        }
    }, 150);
}
"""

# ==========================================
# FONCTIONS LOGIQUES PYTHON & UTILITAIRES
# ==========================================

def get_gallery_items(filtered_dataset, lang): return [(item['img_path'], "") for item in filtered_dataset]

def extract_all_tags(dataset):
    all_tags = set()
    for item in dataset:
        tags = [t.strip() for t in item['caption'].split(',') if t.strip()]
        all_tags.update(tags)
    return "|".join(sorted(list(all_tags)))

def browse_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        folder_path = filedialog.askdirectory(title="Folder")
        root.destroy()
        return folder_path if folder_path else ""
    except Exception as e: return ""

def load_dataset(directory, lang):
    msg_no_sel = "Aucune sélection"
    if not os.path.isdir(directory): 
        return [], [], [], "Dossier introuvable", [], [], msg_no_sel, "{}", ""
    dataset = []
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    idx = 0
    for filename in sorted(os.listdir(directory)):
        if filename.lower().endswith(valid_extensions):
            img_path = os.path.join(directory, filename)
            txt_path = os.path.splitext(img_path)[0] + '.txt'
            caption = ""
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f: caption = f.read().strip()
            else:
                with open(txt_path, 'w', encoding='utf-8') as f: pass
            dataset.append({'id': idx, 'img_name': filename, 'img_path': img_path, 'txt_path': txt_path, 'caption': caption})
            idx += 1
    gal_items = get_gallery_items(dataset, lang)
    success_msg = f"{len(dataset)} images chargées."
    gr.Info(success_msg)
    return dataset, dataset, [], success_msg, gal_items, [], msg_no_sel, "{}", extract_all_tags(dataset)

def filter_gallery(dataset, search_text, lang):
    if not dataset: return [], [], [], "", "{}"
    if not search_text: return dataset, get_gallery_items(dataset, lang), [], "", "{}"
    filtered = [item for item in dataset if search_text.lower() in item['caption'].lower()]
    return filtered, get_gallery_items(filtered, lang), [], "", "{}"

def get_highlighted_html(caption, tracked_words_str):
    if not caption: return "<div style='padding:10px; background:var(--bg-color); border-radius:5px;'></div>"
    html_caption = caption
    if tracked_words_str:
        tracked_words = [w.split(':')[0].strip() for w in tracked_words_str.split(',') if w.strip()]
        tracked_words = sorted([w for w in tracked_words if w], key=len, reverse=True)
        if tracked_words:
            escaped_words = [re.escape(w) for w in tracked_words]
            pattern = re.compile(r'(?i)\b(' + '|'.join(escaped_words) + r')\b')
            html_caption = pattern.sub(r'<mark style="background-color: #ffcc00; color: #000; font-weight: bold; padding: 2px 4px; border-radius: 4px; box-shadow: 0 0 5px rgba(255, 204, 0, 0.5);">\1</mark>', html_caption)
    return f"<div style='padding:15px; border:1px solid #555; background-color: #222; border-radius:8px; line-height:1.6; font-size:1.1em;'>{html_caption}</div>"

def update_word_count(text, lang):
    if not text: return MSG[lang].get("0_words", "0 words")
    words = len(text.split())
    tokens = int(words * 1.3)
    color = "#ff4444" if tokens > 225 else "#44ff44"
    warning = MSG[lang].get("truncation_risk", "") if tokens > 225 else ""
    return f"<div style='color:{color}; font-weight:bold;'>{words} {MSG[lang].get('word_count','words')} (~{tokens} {MSG[lang].get('token_count','tokens')}){warning}</div>"

def update_viewer(filtered_dataset, idx, tracked_words, lang):
    if not filtered_dataset or idx < 0 or idx >= len(filtered_dataset): 
        return None, "", "", MSG[lang].get("0_words", "0 words"), 0, MSG[lang].get("no_img_sel", "No image")
    item = filtered_dataset[idx]
    msg = MSG[lang].get("viewing_img", "Viewing: {name}").format(name=item['img_name'])
    return item['img_path'], get_highlighted_html(item['caption'], tracked_words), item['caption'], update_word_count(item['caption'], lang), idx, msg

def silent_save(dataset, filtered_dataset, idx, new_caption, lang):
    if not filtered_dataset or idx < 0 or idx >= len(filtered_dataset): return
    item_filtered = filtered_dataset[idx]
    if item_filtered['caption'] == new_caption: return 
    real_id = item_filtered['id']
    if os.path.exists(item_filtered['txt_path']): shutil.copy2(item_filtered['txt_path'], item_filtered['txt_path'] + ".bak")
    item_filtered['caption'] = new_caption
    dataset[real_id]['caption'] = new_caption
    with open(item_filtered['txt_path'], 'w', encoding='utf-8') as f: f.write(new_caption)

def handle_sync(payload_str, dataset, filtered_dataset, old_idx, old_caption, tracked_words, lang):
    silent_save(dataset, filtered_dataset, old_idx, old_caption, lang)
    try:
        data = json.loads(payload_str)
        sel_js = data.get("selected", [])
        view_idx = int(data.get("viewIndex", 0))
    except:
        sel_js = []; view_idx = 0
    real_ids = [filtered_dataset[i]['id'] for i in sel_js if 0 <= i < len(filtered_dataset)] if filtered_dataset else []
    sel_text = f"{len(real_ids)} sélectionnée(s)" if real_ids else ""
    img_path, hl_html, cap, wc, c_idx, v_status = update_viewer(filtered_dataset, view_idx, tracked_words, lang)
    return dataset, filtered_dataset, real_ids, sel_text, img_path, hl_html, cap, wc, c_idx, v_status, extract_all_tags(dataset)

def save_all_captions(dataset):
    for item in dataset:
        with open(item['txt_path'], 'w', encoding='utf-8') as f: f.write(item['caption'])

def undo_last_action(dataset, history, lang):
    if not history: return dataset, dataset, MSG[lang].get("nothing_to_undo", "Nothing")
    dataset = copy.deepcopy(history)
    save_all_captions(dataset)
    gr.Warning(MSG[lang].get("undo_success", "Undone"))
    return dataset, dataset, MSG[lang].get("undo_success", "Undone")

def nav_prev(dataset, filtered_dataset, idx, current_caption, tracked_words, lang):
    silent_save(dataset, filtered_dataset, idx, current_caption, lang)
    if not filtered_dataset: return dataset, filtered_dataset, None, "", "", MSG[lang].get("0_words", "0 words"), 0, ""
    new_idx = (idx - 1) % len(filtered_dataset)
    res = update_viewer(filtered_dataset, new_idx, tracked_words, lang)
    return (dataset, filtered_dataset) + res

def nav_next(dataset, filtered_dataset, idx, current_caption, tracked_words, lang):
    silent_save(dataset, filtered_dataset, idx, current_caption, lang)
    if not filtered_dataset: return dataset, filtered_dataset, None, "", "", MSG[lang].get("0_words", "0 words"), 0, ""
    new_idx = (idx + 1) % len(filtered_dataset)
    res = update_viewer(filtered_dataset, new_idx, tracked_words, lang)
    return (dataset, filtered_dataset) + res

def save_single_caption(dataset, filtered_dataset, idx, new_caption, lang):
    if not filtered_dataset or idx < 0 or idx >= len(filtered_dataset): 
        return dataset, filtered_dataset, MSG[lang].get("error", "Error")
    item_filtered = filtered_dataset[idx]
    real_id = item_filtered['id']
    if os.path.exists(item_filtered['txt_path']): shutil.copy2(item_filtered['txt_path'], item_filtered['txt_path'] + ".bak")
    item_filtered['caption'] = new_caption
    dataset[real_id]['caption'] = new_caption
    with open(item_filtered['txt_path'], 'w', encoding='utf-8') as f: f.write(new_caption)
    msg_success = MSG[lang].get("saved", "Saved: {name}").format(name=item_filtered['img_name'])
    gr.Info(msg_success)
    return dataset, filtered_dataset, msg_success

def clear_selection(lang): 
    return [], MSG[lang].get("no_sel_all", ""), "{}"

def toggle_tracked_word(current_tracker, selected_text):
    if not selected_text: return gr.update()
    word = selected_text.strip(', ')
    if not word: return gr.update()
    current_list = [w.strip() for w in current_tracker.split(',') if w.strip()]
    existing = []; found = False
    for w in current_list:
        if w.split(':')[0].strip().lower() == word.lower(): found = True 
        else: existing.append(w)
    if not found: existing.append(word) 
    return ", ".join(existing)

def df_to_tracked_words(df):
    if df is None or df.empty: return ""
    words = []
    for _, row in df.iterrows():
        mot = str(row.get("Mot-clé", row.get("Keyword", ""))).strip()
        if not mot or mot.lower() in ["aucun", "none"]: continue
        cible = str(row.get("Cible %", row.get("Target %", ""))).replace('%', '').strip()
        if cible and cible != "-" and cible != "0.0" and cible != "0": words.append(f"{mot}:{cible}")
        else: words.append(mot)
    return ", ".join(words)

def norm_tracked_words(s):
    """Normalise la chaîne de mots-clés pour éviter les boucles de mise à jour inutiles."""
    if not s or not isinstance(s, str): return ""
    return ",".join(sorted([w.strip().lower() for w in s.split(',') if w.strip()]))

def safe_df_to_tracked_words(df, current_str):
    new_str = df_to_tracked_words(df)
    if norm_tracked_words(new_str) == norm_tracked_words(current_str): return gr.update()
    return new_str

def get_row_index(evt: gr.SelectData, state_json):
    row_idx = evt.index[0]
    if not state_json or state_json == "{}": return row_idx, gr.update(), gr.update()
    df = pd.read_json(io.StringIO(state_json), orient='records')
    if df.empty or row_idx >= len(df): return row_idx, gr.update(), gr.update()
    
    prio_col = "Priorité" if "Priorité" in df.columns else "Priority"
    tgt_col = "Cible %" if "Cible %" in df.columns else "Target %"
    
    prio_val = str(df.at[row_idx, prio_col])
    tgt_val = str(df.at[row_idx, tgt_col]).replace('%', '')
    try: tgt_val = float(tgt_val)
    except: tgt_val = 0.0
    return row_idx, prio_val, tgt_val

def apply_quick_prio(new_prio, row_idx, state_json):
    if row_idx < 0 or not state_json or state_json == "{}": return gr.update(), state_json, gr.update(), row_idx
    df = pd.read_json(io.StringIO(state_json), orient='records')
    if df.empty or row_idx >= len(df): return gr.update(), state_json, gr.update(), row_idx
    
    prio_col = "Priorité" if "Priorité" in df.columns else "Priority"
    try: new_prio_int = int(new_prio)
    except: return gr.update(), state_json, gr.update(), row_idx
        
    max_prio = len(df)
    if new_prio_int < 1: new_prio_int = 1
    if new_prio_int > max_prio: new_prio_int = max_prio
        
    old_prio = df.at[row_idx, prio_col]
    if old_prio == new_prio_int: return gr.update(), state_json, gr.update(), row_idx
    
    conflict_mask = df[prio_col] == new_prio_int
    if conflict_mask.any():
        conflict_idx = conflict_mask.idxmax()
        df.at[conflict_idx, prio_col] = old_prio
        
    df.at[row_idx, prio_col] = new_prio_int
    df = df.sort_values(by=prio_col).reset_index(drop=True)
    df[prio_col] = range(1, len(df) + 1)
    
    new_row_idx = df.index[df[prio_col] == new_prio_int].tolist()[0]
    new_json = df.to_json(orient='records')
    return df, new_json, df_to_tracked_words(df), new_row_idx

def apply_quick_target(new_tgt, row_idx, state_json):
    if row_idx < 0 or not state_json or state_json == "{}": return gr.update(), state_json, gr.update()
    df = pd.read_json(io.StringIO(state_json), orient='records')
    if df.empty or row_idx >= len(df): return gr.update(), state_json, gr.update()
    
    tgt_col = "Cible %" if "Cible %" in df.columns else "Target %"
    
    old_tgt = str(df.at[row_idx, tgt_col]).replace('%', '')
    try: old_tgt = float(old_tgt)
    except: old_tgt = 0.0
    
    if new_tgt is None: new_tgt = 0.0
    if old_tgt == new_tgt: return gr.update(), state_json, gr.update()
    
    df.at[row_idx, tgt_col] = new_tgt
    new_json = df.to_json(orient='records')
    return df, new_json, df_to_tracked_words(df)

def df_move_up(df, row_idx):
    if df is None or df.empty or row_idx <= 0 or row_idx >= len(df): return df, row_idx, df_to_tracked_words(df)
    d = df.to_dict('records')
    d[row_idx], d[row_idx-1] = d[row_idx-1], d[row_idx]
    ndf = pd.DataFrame(d)
    col = "Priorité" if "Priorité" in ndf.columns else "Priority"
    ndf[col] = range(1, len(ndf)+1)
    return ndf, row_idx - 1, df_to_tracked_words(ndf)

def df_move_down(df, row_idx):
    if df is None or df.empty or row_idx < 0 or row_idx >= len(df)-1: return df, row_idx, df_to_tracked_words(df)
    d = df.to_dict('records')
    d[row_idx], d[row_idx+1] = d[row_idx+1], d[row_idx]
    ndf = pd.DataFrame(d)
    col = "Priorité" if "Priorité" in ndf.columns else "Priority"
    ndf[col] = range(1, len(ndf)+1)
    return ndf, row_idx + 1, df_to_tracked_words(ndf)

def df_delete_row(df, row_idx):
    if df is None or df.empty or row_idx < 0 or row_idx >= len(df): return df, -1, df_to_tracked_words(df)
    d = df.to_dict('records')
    d.pop(row_idx)
    ndf = pd.DataFrame(d) if d else pd.DataFrame(columns=df.columns)
    if not ndf.empty:
        col = "Priorité" if "Priorité" in ndf.columns else "Priority"
        ndf[col] = range(1, len(ndf)+1)
    return ndf, -1, df_to_tracked_words(ndf)

def handle_df_edit(new_df, old_df):
    if new_df is None or new_df.empty: return new_df, new_df, df_to_tracked_words(new_df)
    prio_col = "Priorité" if "Priorité" in new_df.columns else "Priority"

    if old_df is not None and not old_df.empty and len(new_df) == len(old_df):
        try:
            new_series = pd.to_numeric(new_df[prio_col], errors='coerce').fillna(999).astype(int)
            old_series = pd.to_numeric(old_df[prio_col], errors='coerce').fillna(999).astype(int)
            diff_mask = new_series != old_series
            if diff_mask.any():
                changed_idx = diff_mask.idxmax()
                new_prio = new_series.iloc[changed_idx]
                old_prio = old_series.iloc[changed_idx]
                max_prio = len(new_df)
                if new_prio < 1: new_prio = 1
                if new_prio > max_prio: new_prio = max_prio
                new_df.at[changed_idx, prio_col] = new_prio
                new_series.iloc[changed_idx] = new_prio
                conflict_mask = (new_series == new_prio) & (new_series.index != changed_idx)
                if conflict_mask.any():
                    conflict_idx = conflict_mask.idxmax()
                    new_df.at[conflict_idx, prio_col] = old_prio
        except Exception: pass
            
    try:
        new_df[prio_col] = pd.to_numeric(new_df[prio_col], errors='coerce').fillna(999).astype(int)
        new_df = new_df.sort_values(by=prio_col).reset_index(drop=True)
        new_df[prio_col] = range(1, len(new_df) + 1)
    except: pass
    
    return new_df, new_df, df_to_tracked_words(new_df)

def handle_recipe_df_safe(new_df, state_json, current_str):
    if new_df is None or new_df.empty: return gr.update(), "{}", gr.update()
    new_json = new_df.to_json(orient='records')
    if new_json == state_json: return gr.update(), state_json, gr.update()
    
    old_df = pd.read_json(io.StringIO(state_json), orient='records') if state_json != "{}" else pd.DataFrame()
    processed_df, _, new_str = handle_df_edit(new_df, old_df)
    processed_json = processed_df.to_json(orient='records')
    
    str_update = new_str if norm_tracked_words(new_str) != norm_tracked_words(current_str) else gr.update()
    return processed_df, processed_json, str_update

def handle_stats_df_safe(new_df, state_json, current_str):
    if new_df is None or new_df.empty: return gr.update(), "{}", gr.update()
    new_json = new_df.to_json(orient='records')
    if new_json == state_json: return gr.update(), state_json, gr.update()
    
    new_str = df_to_tracked_words(new_df)
    str_update = new_str if norm_tracked_words(new_str) != norm_tracked_words(current_str) else gr.update()
    return gr.update(), new_json, str_update

def handle_drag_and_drop(dnd_data, current_df):
    if not dnd_data or current_df is None or current_df.empty: return current_df, gr.update()
    try:
        old_idx, new_idx = map(int, dnd_data.split(','))
        if old_idx < 0 or old_idx >= len(current_df) or new_idx < 0 or new_idx >= len(current_df): return current_df, gr.update()
        df_list = current_df.to_dict('records')
        item = df_list.pop(old_idx)
        df_list.insert(new_idx, item)
        new_df = pd.DataFrame(df_list)
        prio_col = "Priorité" if "Priorité" in new_df.columns else "Priority"
        new_df[prio_col] = range(1, len(new_df) + 1)
        return new_df, df_to_tracked_words(new_df)
    except: return current_df, gr.update()

def generate_civitai_format(df):
    if df is None or df.empty: return ""
    md = "| " + " | ".join(df.columns) + " |\n"
    md += "|" + "|".join(["---" for _ in df.columns]) + "|\n"
    for _, row in df.iterrows(): md += "| " + " | ".join(str(x) for x in row.values) + " |\n"
    gr.Info("✅ Format CivitAI généré ! Copiez le texte ci-dessous.")
    return md

def analyze_dataset(dataset, tracked_words_str, lang):
    lang = lang or "FR"
    if not dataset: 
        empty_df = pd.DataFrame()
        return None, None, empty_df, "{}", empty_df, "{}", MSG[lang].get("no_dataset", "")
        
    if not tracked_words_str: 
        empty_conf = pd.DataFrame([{MSG[lang].get("df_prio", "Prio"): 1, MSG[lang].get("df_kw", "Kw"): "", MSG[lang].get("df_tgt", "Tgt"): 0}])
        empty_stats = pd.DataFrame([{MSG[lang].get("df_kw", "Kw"): "", MSG[lang].get("df_tgt", "Tgt"): ""}])
        return None, None, empty_stats, "{}", empty_conf, "{}", MSG[lang].get("enter_keywords", "")
    
    total_images = len(dataset)
    raw_words = [w.strip() for w in tracked_words_str.split(',') if w.strip()]
    targets = {}; stats = {}
    for w in raw_words:
        if ':' in w:
            parts = w.split(':'); word = parts[0].strip()
            try: targets[word] = float(parts[1].strip())
            except: targets[word] = 0.0
            stats[word] = 0
        else: stats[w] = 0
    for item in dataset:
        cap = item['caption'].lower()
        for word in stats.keys():
            if re.search(r'\b' + re.escape(word.lower()) + r'\b', cap): stats[word] += 1
    
    df_stats = []
    for word, count in stats.items():
        pct = (count / total_images) * 100 if total_images > 0 else 0
        row = {MSG[lang].get("df_kw", "Keyword"): word, "Count" if lang=="EN" else "Compte": count, "Current %" if lang=="EN" else "Actuel %": f"{pct:.1f}%"}
        if word in targets:
            row[MSG[lang].get("df_tgt", "Target %")] = f"{targets[word]}%"
            row["Diff" if lang=="EN" else "Écart"] = f"{'+' if (pct - targets[word])>0 else ''}{pct - targets[word]:.1f}%"
        else:
            row[MSG[lang].get("df_tgt", "Target %")] = "-"; row["Diff" if lang=="EN" else "Écart"] = "-"
        df_stats.append(row)
        
    df = pd.DataFrame(df_stats).sort_values(by="Count" if lang=="EN" else "Compte", ascending=False)
    df_json = df.to_json(orient='records')
    
    df_config = []
    for i, word in enumerate(stats.keys()):
        cible = targets.get(word, 0)
        df_config.append({MSG[lang].get("df_prio", "Priority"): i+1, MSG[lang].get("df_kw", "Keyword"): word, MSG[lang].get("df_tgt", "Target %"): cible})
    df_conf = pd.DataFrame(df_config)
    df_conf_json = df_conf.to_json(orient='records')

    pie_data = {k: v for k, v in stats.items() if v > 0}
    if not pie_data:
        fig_pie = px.pie(names=[MSG[lang].get("none", "None")], values=[1], title=MSG[lang].get("no_tag_found", "No tag"))
        fig_bar = px.bar(x=[MSG[lang].get("none", "None")], y=[0], title=MSG[lang].get("no_tag_found", "No tag"))
    else:
        fig_pie = px.pie(names=list(pie_data.keys()), values=list(pie_data.values()), title=MSG[lang].get("overall_dist", "Distribution"))
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_bar = px.bar(x=list(pie_data.keys()), y=list(pie_data.values()), title=MSG[lang].get("occ_by_keyword", "Occurrences"))
    
    return fig_pie, fig_bar, df, df_json, df_conf, df_conf_json, MSG[lang].get("stats_updated", "Updated")

def find_orphans(dataset, lang):
    lang = lang or "FR"
    if not dataset: return MSG[lang].get("no_dataset", "")
    all_words = []
    for item in dataset:
        tags = [t.strip().lower() for t in item['caption'].split(',')]
        all_words.extend(tags)
    counts = Counter(all_words)
    orphans = [tag for tag, count in counts.items() if count == 1 and len(tag) > 2]
    if not orphans: return MSG[lang].get("no_orphans", "No orphans")
    return MSG[lang].get("unique_tags", "Unique:\n") + ", ".join(sorted(orphans))

def auto_fill_top_tags(dataset):
    if not dataset: return ""
    all_words = []
    for item in dataset:
        tags = [t.strip().lower() for t in item['caption'].split(',')]
        all_words.extend([t for t in tags if t])
    counts = Counter(all_words)
    return ", ".join([tag for tag, count in counts.most_common(20)])

def load_recipes():
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, 'r') as f: return json.load(f)
    return {"Default": "1girl, solo, looking at viewer"}

def save_recipe(name, words):
    if not name: return gr.update(), "Empty name"
    recipes = load_recipes()
    recipes[name] = words
    with open(RECIPES_FILE, 'w') as f: json.dump(recipes, f)
    gr.Info("✅ Recette sauvegardée avec succès !")
    return gr.update(choices=list(recipes.keys()), value=name), "✅ Saved"

def apply_recipe(name): return load_recipes().get(name, "")

def save_all_captions(dataset):
    for item in dataset:
        with open(item['txt_path'], 'w', encoding='utf-8') as f: f.write(item['caption'])

def undo_last_action(dataset, history, lang):
    if not history: return dataset, dataset, MSG[lang].get("nothing_to_undo", "Nothing")
    dataset = copy.deepcopy(history)
    save_all_captions(dataset)
    gr.Warning(MSG[lang].get("undo_success", "Undone"))
    return dataset, dataset, MSG[lang].get("undo_success", "Undone")

def create_preview_df(old_dataset, new_dataset, lang):
    changes = []
    for old, new in zip(old_dataset, new_dataset):
        if old['caption'] != new['caption']:
            changes.append({"File" if lang=="EN" else "Fichier": old['img_name'], "Avant" if lang=="FR" else "Before": old['caption'], "Après" if lang=="FR" else "After": new['caption']})
            if len(changes) >= 10: break
    if not changes: return pd.DataFrame([{"Message": MSG[lang].get("no_changes", "No change")}])
    return pd.DataFrame(changes)

def batch_add(dataset, text, pos, selected_ids, search_text, lang):
    if not text: return dataset, dataset, dataset, MSG[lang].get("text_empty", ""), pd.DataFrame()
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        if pos in ["Début", "Start"]:
            sep = ", " if item['caption'] else ""
            item['caption'] = text + sep + item['caption']
        else:
            sep = ", " if item['caption'] and not item['caption'].endswith(", ") else ""
            item['caption'] = item['caption'] + sep + text
        count += 1
    save_all_captions(dataset)
    msg = MSG[lang].get("added_to", "Added").format(count=count)
    gr.Info(msg)
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_replace(dataset, old_text, new_text, use_regex, selected_ids, search_text, lang):
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        if use_regex:
            try:
                new_cap = re.sub(old_text, new_text, item['caption'])
                if new_cap != item['caption']: item['caption'] = new_cap; count += 1
            except: return dataset, dataset, history, MSG[lang].get("regex_error", "Regex error"), pd.DataFrame()
        else:
            if old_text in item['caption']: item['caption'] = item['caption'].replace(old_text, new_text); count += 1
    save_all_captions(dataset)
    msg = MSG[lang].get("replaced_in", "Replaced").format(count=count)
    gr.Info(msg)
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_clean_commas(dataset, selected_ids, search_text, lang):
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        cap = item['caption']
        cap = re.sub(r'\s+', ' ', cap)
        cap = re.sub(r'\s*,\s*', ', ', cap)
        cap = re.sub(r'(,\s*){2,}', ', ', cap)
        cap = cap.strip(', ')
        if cap != item['caption']: item['caption'] = cap; count += 1
    save_all_captions(dataset)
    msg = MSG[lang].get("cleaned_in", "Cleaned").format(count=count)
    gr.Info(msg)
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_remove_duplicates(dataset, selected_ids, search_text, lang):
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        parts = [p.strip() for p in item['caption'].split(',')]
        seen = set(); new_parts = []
        for p in parts:
            if p.lower() not in seen and p != "": seen.add(p.lower()); new_parts.append(p)
        new_cap = ", ".join(new_parts)
        if new_cap != item['caption']: item['caption'] = new_cap; count += 1
    save_all_captions(dataset)
    msg = MSG[lang].get("dups_removed", "Removed").format(count=count)
    gr.Info(msg)
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_synonyms(dataset, target_tag, synonyms_str, selected_ids, search_text, lang):
    if not target_tag: return dataset, dataset, dataset, MSG[lang].get("target_empty", ""), pd.DataFrame()
    history = copy.deepcopy(dataset)
    count = 0
    syn_list = [s.strip() for s in synonyms_str.split(',')] if synonyms_str else []
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        original = item['caption']
        tags = [t.strip() for t in original.split(',')]
        first_found = False; syn_idx = 0; new_tags = []
        for t in tags:
            if t.lower() == target_tag.strip().lower():
                if not first_found: first_found = True; new_tags.append(t)
                else:
                    if syn_list and syn_list[0]: new_tags.append(syn_list[syn_idx % len(syn_list)]); syn_idx += 1
            else: new_tags.append(t)
        new_cap = ", ".join([t for t in new_tags if t])
        if new_cap != original: item['caption'] = new_cap; count += 1
    save_all_captions(dataset)
    msg = MSG[lang].get("synonyms_replaced", "Replaced").format(count=count)
    gr.Info(msg)
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, create_preview_df(history, dataset, lang)

def simulate_and_export(dataset, export_dir, config_df, is_simulation, selected_ids, strategy, max_images, lang):
    if not dataset: return MSG[lang].get("no_dataset", ""), [], None, None
    if config_df is None or config_df.empty: 
        config_df = pd.DataFrame([{MSG[lang].get("df_prio", "Prio"): 1, MSG[lang].get("df_kw", "Kw"): "", MSG[lang].get("df_tgt", "Tgt"): 0}])
    else:
        prio_col = "Priority" if "Priority" in config_df.columns else "Priorité"
        config_df[prio_col] = pd.to_numeric(config_df[prio_col], errors='coerce').fillna(999).astype(int)
        config_df = config_df.sort_values(by=prio_col)
    
    targets = {}; ordered_tags = []
    for _, row in config_df.iterrows():
        tag = str(row.get("Mot-clé", row.get("Keyword", ""))).strip().lower()
        if tag and tag not in ["aucun", "none"]:
            try: c = float(str(row.get("Cible %", row.get("Target %", 0))).replace('%', '').strip())
            except: c = 0.0
            targets[tag] = c
            ordered_tags.append(tag)

    base_pool = [item for item in dataset if not selected_ids or item['id'] in selected_ids]
    to_export = []
    limit = int(max_images)

    if strategy in ["Filtre Classique (Contient au moins un tag)", "Classic Filter (Contains at least one tag)"]:
        for item in base_pool:
            if not ordered_tags or any(re.search(r'\b' + re.escape(t) + r'\b', item['caption'].lower()) for t in ordered_tags):
                to_export.append(item)
        if limit > 0: to_export = to_export[:limit]

    elif strategy in ["Priorité (Ordre du tableau)", "Priority (Table Order)"]:
        seen = set()
        lim = limit if limit > 0 else len(base_pool)
        for tag in ordered_tags:
            for item in base_pool:
                if len(to_export) >= lim: break
                if item['id'] not in seen and re.search(r'\b' + re.escape(tag) + r'\b', item['caption'].lower()):
                    to_export.append(item); seen.add(item['id'])
            if len(to_export) >= lim: break

    elif strategy in ["Équilibrage Auto (Pourcentages)", "Auto Balancing (Percentages)"]:
        relevant = [it for it in base_pool if not ordered_tags or any(re.search(r'\b'+re.escape(t)+r'\b', it['caption'].lower()) for t in ordered_tags)]
        lim = limit if limit > 0 else len(relevant)
        if lim > 0 and ordered_tags:
            needs = {tag: int((pct / 100.0) * lim) for tag, pct in targets.items() if pct > 0}
            if sum(needs.values()) == 0: to_export = relevant[:lim]
            else:
                available = relevant.copy()
                while len(to_export) < lim and available:
                    best_score = -9999; best_idx = -1
                    for i, item in enumerate(available):
                        cap = item['caption'].lower(); score = 0; has_tag = False
                        for tag in ordered_tags:
                            if re.search(r'\b' + re.escape(tag) + r'\b', cap):
                                has_tag = True
                                if tag in needs: score += (10 * needs[tag]) if needs[tag] > 0 else -5
                        if has_tag and score > best_score: best_score = score; best_idx = i
                    if best_idx == -1: break
                    chosen = available.pop(best_idx)
                    to_export.append(chosen)
                    for tag in ordered_tags:
                        if re.search(r'\b' + re.escape(tag) + r'\b', chosen['caption'].lower()) and tag in needs: needs[tag] -= 1
        else: to_export = relevant[:lim]

    sim_stats = {t: 0 for t in ordered_tags}
    for item in to_export:
        cap = item['caption'].lower()
        for t in ordered_tags:
            if re.search(r'\b' + re.escape(t) + r'\b', cap): sim_stats[t] += 1
            
    pie_data = {k: v for k, v in sim_stats.items() if v > 0}
    if not pie_data:
        p_fig = px.pie(names=[MSG[lang].get("none", "None")], values=[1], title=MSG[lang].get("sim_no_tag", "No tag"))
        b_fig = px.bar(x=[MSG[lang].get("none", "None")], y=[0], title=MSG[lang].get("sim_no_tag", "No tag"))
    else:
        p_fig = px.pie(names=list(pie_data.keys()), values=list(pie_data.values()), title=MSG[lang].get("sim_dist", "Dist"))
        p_fig.update_traces(textposition='inside', textinfo='percent+label')
        b_fig = px.bar(x=list(pie_data.keys()), y=list(pie_data.values()), title=MSG[lang].get("sim_occ", "Occurrences"))

    gallery_preview = [item['img_path'] for item in to_export]
    
    if is_simulation:
        rep = MSG[lang].get("simul_res", "Simul: {count}").format(count=len(to_export))
        gr.Info("📊 Simulation terminée !")
        return rep, gallery_preview, p_fig, b_fig
    else:
        if not export_dir or str(export_dir).strip() == "": export_dir = os.path.join(os.getcwd(), "output", "dataset_final")
        if not os.path.exists(export_dir): os.makedirs(export_dir)
        for item in to_export:
            shutil.copy2(item['img_path'], os.path.join(export_dir, item['img_name']))
            shutil.copy2(item['txt_path'], os.path.join(export_dir, os.path.basename(item['txt_path'])))
        msg = MSG[lang].get("export_success", "Success").format(count=len(to_export), dest=export_dir)
        gr.Info(f"✅ Export réussi dans {export_dir}")
        return msg, gallery_preview, p_fig, b_fig

# ==========================================
# MODULE 1 PRO : PRÉ-TRAITEMENT & DOUBLONS
# ==========================================

def scan_duplicates_advanced(dataset, tolerance):
    if not HAS_IMAGEHASH:
        gr.Warning("Installez imagehash: pip install imagehash")
        return gr.update(choices=[], value=""), {}
    
    hashes = {}
    dups_pairs = []
    
    for item in dataset:
        try:
            img = Image.open(item['img_path'])
            h = imagehash.average_hash(img)
            
            found_dup = False
            for prev_h, prev_item in hashes.items():
                if abs(h - prev_h) <= int(tolerance):
                    pair_name = f"{prev_item['img_name']} VS {item['img_name']}"
                    dups_pairs.append({
                        "name": pair_name, 
                        "imgA": prev_item['img_path'], "imgB": item['img_path'],
                        "idA": prev_item['id'], "idB": item['id']
                    })
                    found_dup = True
                    break
            if not found_dup: hashes[h] = item
        except: pass
    
    if not dups_pairs:
        gr.Info("Aucun doublon visuel trouvé avec cette tolérance !")
        return gr.update(choices=[], value=""), {}
        
    choices = [p["name"] for p in dups_pairs]
    mapping = {p["name"]: p for p in dups_pairs}
    gr.Warning(f"{len(choices)} paires suspectes trouvées !")
    return gr.update(choices=choices, value=choices[0]), mapping

def load_duplicate_pair(pair_name, mapping):
    if not pair_name or pair_name not in mapping: return None, None, -1, -1
    data = mapping[pair_name]
    return data["imgA"], data["imgB"], data["idA"], data["idB"]

def delete_duplicate(dataset, filtered_dataset, id_to_delete, pair_name, mapping):
    if id_to_delete < 0: return dataset, filtered_dataset, gr.update(), mapping, "Erreur suppression"
    item_to_del = next((x for x in dataset if x['id'] == id_to_delete), None)
    if item_to_del:
        try:
            os.remove(item_to_del['img_path'])
            if os.path.exists(item_to_del['txt_path']): os.remove(item_to_del['txt_path'])
            dataset = [x for x in dataset if x['id'] != id_to_delete]
            filtered_dataset = [x for x in filtered_dataset if x['id'] != id_to_delete]
            gr.Info(f"Fichier {item_to_del['img_name']} supprimé.")
        except Exception as e:
            gr.Warning(f"Impossible de supprimer: {e}")
            
    if pair_name in mapping:
        del mapping[pair_name]
        
    choices = list(mapping.keys())
    val = choices[0] if choices else ""
    return dataset, filtered_dataset, gr.update(choices=choices, value=val), mapping, f"Supprimé. Reste {len(choices)} doublons."

def batch_rename_dataset(dataset, prefix):
    if not dataset or not prefix.strip(): return dataset, "Veuillez entrer un préfixe."
    prefix = prefix.strip()
    count = 1
    dir_path = os.path.dirname(dataset[0]['img_path'])
    
    for item in dataset:
        ext = os.path.splitext(item['img_name'])[1]
        new_img_name = f"{prefix}_{count:04d}{ext}"
        new_txt_name = f"{prefix}_{count:04d}.txt"
        new_img_path = os.path.join(dir_path, new_img_name)
        new_txt_path = os.path.join(dir_path, new_txt_name)
        
        try:
            os.rename(item['img_path'], new_img_path)
            if os.path.exists(item['txt_path']): os.rename(item['txt_path'], new_txt_path)
            item['img_name'] = new_img_name
            item['img_path'] = new_img_path
            item['txt_path'] = new_txt_path
        except: pass
        count += 1
        
    gr.Info("Renommage par lot effectué !")
    return dataset, "✅ Dataset renommé."

def batch_process_images(dataset, dest_folder, size, format_choice, crop_mode, handle_alpha):
    if not dataset: return "Aucun dataset."
    if not dest_folder: dest_folder = os.path.join(os.getcwd(), "processed_dataset")
    os.makedirs(dest_folder, exist_ok=True)
    
    count = 0
    target_size = int(size)
    for item in dataset:
        try:
            img = Image.open(item['img_path'])
            
            if handle_alpha and (img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P': img = img.convert('RGBA')
                bg.paste(img, (0,0), img)
                img = bg
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
                
            if crop_mode == "Smart Face Crop (OpenCV)" and HAS_CV2:
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    x, y, w_face, h_face = faces[0]
                    center_x, center_y = x + w_face//2, y + h_face//2
                    w, h = img.size
                    min_dim = min(w, h)
                    left = max(0, center_x - min_dim//2)
                    top = max(0, center_y - min_dim//2)
                    right = min(w, left + min_dim)
                    bottom = min(h, top + min_dim)
                    if right - left < min_dim: left = right - min_dim
                    if bottom - top < min_dim: top = bottom - min_dim
                    img = img.crop((left, top, right, bottom))
                else:
                    w, h = img.size
                    min_dim = min(w, h)
                    img = img.crop(((w-min_dim)/2, (h-min_dim)/2, (w+min_dim)/2, (h+min_dim)/2))
            elif crop_mode == "1:1 (Carré Centre)":
                w, h = img.size
                min_dim = min(w, h)
                img = img.crop(((w-min_dim)/2, (h-min_dim)/2, (w+min_dim)/2, (h+min_dim)/2))
            
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            ext = ".webp" if format_choice == "WebP" else ".jpg"
            new_name = os.path.splitext(item['img_name'])[0] + ext
            save_path = os.path.join(dest_folder, new_name)
            
            img.save(save_path, format="WEBP" if format_choice=="WebP" else "JPEG", quality=95)
            new_txt_name = os.path.splitext(item['img_name'])[0] + ".txt"
            shutil.copy2(item['txt_path'], os.path.join(dest_folder, new_txt_name))
            count += 1
        except Exception as e: print(f"Erreur pré-traitement sur {item['img_name']}: {e}")
        
    return f"✅ {count} images traitées avec succès !"

# ==========================================
# MODULE 2 PRO : IA (VLM & LLM via API)
# ==========================================

def load_ai_recipes():
    if os.path.exists(AI_RECIPES_FILE):
        with open(AI_RECIPES_FILE, 'r') as f: return json.load(f)
    return {"Default Flux Style": "Réécris ces tags en une phrase naturelle parfaite pour le modèle Flux : {tags}"}

def save_ai_recipe(name, prompt):
    if not name: return gr.update()
    recipes = load_ai_recipes()
    recipes[name] = prompt
    with open(AI_RECIPES_FILE, 'w') as f: json.dump(recipes, f)
    gr.Info("Template IA sauvegardé !")
    return gr.update(choices=list(recipes.keys()), value=name)

def apply_ai_recipe(name): return load_ai_recipes().get(name, "")

AI_ACTION_DESCRIPTIONS = {
    "Auto-Taggage / Super OCR (VLM)": "**Vision :** Analyse complète de l'image et extraction du texte.",
    "Reality Check & Hallucinations (VLM)": "**Vision :** Supprime les tags inexistants dans l'image réelle.",
    "Concept Isolator (Spécial LoRA)": "**Vision :** Décrit tout SAUF le sujet central.",
    "Traducteur Visuel (Booru ↔ Phrase Naturelle)": "**Texte :** Convertit des tags bruts en une belle phrase.",
    "Tag Sorting & Standardisation": "**Texte :** Ordonne l'importance des tags et corrige l'orthographe.",
    "Traduction Automatique (Vers Anglais)": "**Texte :** Traduit proprement vers l'anglais.",
    "✨ Prompt Personnalisé (Texte/Vision)": "**Custom :** Utilisez le champ 'Prompt Personnalisé' ci-dessous."
}

def update_ai_action_desc(action):
    show_custom = action == "✨ Prompt Personnalisé (Texte/Vision)"
    desc = AI_ACTION_DESCRIPTIONS.get(action, "")
    return f"<div class='ai-desc-box'>ℹ️ {desc}</div>", gr.update(visible=show_custom), gr.update(visible=show_custom)

def call_ai_api(prompt, model, image_path, api_backend, api_url, temp, ctx, sys_prompt):
    api_url = str(api_url).strip()
    if not api_url.startswith("http"): api_url = "http://" + api_url
    
    b64 = None
    if image_path:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            
    if api_backend == "Ollama":
        if not api_url.endswith("/api/generate") and not api_url.endswith("/api/chat"):
            api_url = api_url.rstrip("/") + "/api/generate"
            
        payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": float(temp), "num_ctx": int(ctx)}}
        if sys_prompt: payload["system"] = str(sys_prompt).strip()
        if b64: payload["images"] = [b64]
        
        try:
            response = requests.post(api_url, json=payload, timeout=180)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return f"Erreur API: Connexion impossible à {api_url}. Ollama est-il lancé ?"
        except Exception as e: return f"Erreur API Ollama: {e}"
        
    else:
        if api_url.endswith("/"): api_url = api_url[:-1]
        if not api_url.endswith("/v1/chat/completions"):
            api_url = api_url + "/v1/chat/completions"
            
        messages = []
        if sys_prompt: messages.append({"role": "system", "content": str(sys_prompt).strip()})
        
        if b64:
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})
            
        payload = {"model": model, "messages": messages, "temperature": float(temp), "max_tokens": int(ctx)}
        
        try:
            response = requests.post(api_url, json=payload, timeout=180)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except requests.exceptions.ConnectionError:
            return f"Erreur API: Connexion impossible à {api_url}. Le serveur LM Studio/Kobold est-il lancé ?"
        except Exception as e: return f"Erreur API OpenAI Compatible: {e}"

def process_ai_action(dataset, selected_ids, search_text, action, custom_prompt, injection_mode, use_vision_for_custom, vlm_model, llm_model, api_backend, api_url, temp, ctx, sys_prompt, lang):
    if not dataset: return dataset, dataset, dataset, "Dataset vide.", extract_all_tags(dataset)
    history = copy.deepcopy(dataset)
    count = 0
    errors = []
    
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        current_cap = item['caption']
        new_cap = current_cap
        res = ""
        
        try:
            if action == "Auto-Taggage / Super OCR (VLM)":
                res = call_ai_api("Décris cette image en détail (virgules). Ajoute le texte lu sous la forme text: \"le texte\".", vlm_model, item['img_path'], api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "Reality Check & Hallucinations (VLM)":
                res = call_ai_api(f"Tags actuels: '{current_cap}'. Ne renvoie QUE les tags réellement présents.", vlm_model, item['img_path'], api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "Concept Isolator (Spécial LoRA)":
                res = call_ai_api("Décris l'arrière-plan et le style, NE DÉCRIS PAS le sujet principal.", vlm_model, item['img_path'], api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "Traducteur Visuel (Booru ↔ Phrase Naturelle)":
                res = call_ai_api(f"Transforme en phrase anglaise fluide pour Flux : {current_cap}", llm_model, None, api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "Traduction Automatique (Vers Anglais)":
                res = call_ai_api(f"Translate into English, keep comma format: {current_cap}", llm_model, None, api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "Tag Sorting & Standardisation":
                res = call_ai_api(f"Ordonne (Sujet, Vêtements, Fond) et corrige: {current_cap}", llm_model, None, api_backend, api_url, temp, ctx, sys_prompt)
            elif action == "✨ Prompt Personnalisé (Texte/Vision)":
                model_to_use = vlm_model if use_vision_for_custom else llm_model
                img_path_to_use = item['img_path'] if use_vision_for_custom else None
                prompt_to_use = custom_prompt.replace("{tags}", current_cap)
                res = call_ai_api(prompt_to_use, model_to_use, img_path_to_use, api_backend, api_url, temp, ctx, sys_prompt)
            
            if res.startswith("Erreur API"):
                errors.append(item['img_name'])
                gr.Warning(res)
                continue
                
            if injection_mode == "Remplacer tout" or action != "✨ Prompt Personnalisé (Texte/Vision)": new_cap = res
            elif injection_mode == "Ajouter au début": new_cap = res + ", " + current_cap if current_cap else res
            elif injection_mode == "Ajouter à la fin": new_cap = current_cap + ", " + res if current_cap else res
            
            if new_cap != current_cap:
                item['caption'] = new_cap
                count += 1
        except:
            errors.append(item['img_name'])
            
    save_all_captions(dataset)
    
    msg = f"✅ IA Appliquée ({count} modifiés)."
    if errors: msg += f" ⚠️ Échecs sur {len(errors)} fichiers (Timeout/Erreur)."
    gr.Info(msg)
    
    filtered_dataset = [item for item in dataset if search_text.lower() in item['caption'].lower()] if search_text else dataset
    return dataset, filtered_dataset, history, msg, extract_all_tags(dataset)

def analyze_bias(dataset, llm_model, api_backend, api_url, temp, ctx, sys_prompt):
    if not dataset: return "Aucun dataset."
    all_caps = " | ".join([it['caption'] for it in dataset[:50]]) 
    prompt = f"Tu es un expert en entraînement de modèles IA (LoRA, SDXL). Voici un échantillon des captions de mon dataset : {all_caps}. Fais-moi un bref rapport des biais potentiels (ex: poses répétitives, manques de diversité) et propose des conseils."
    return call_ai_api(prompt, llm_model, None, api_backend, api_url, temp, ctx, sys_prompt)

# ==========================================
# MODULE STATS AVANCÉES PRO (Points 4, 5, 6)
# ==========================================

def update_advanced_stats(dataset):
    if not dataset: return None, None, "Aucun dataset", "Aucune contradiction"
    
    pairs = defaultdict(int)
    tag_counts = defaultdict(int)
    for item in dataset:
        tags = [t.strip().lower() for t in item['caption'].split(',') if t.strip()]
        for i in range(len(tags)):
            tag_counts[tags[i]] += 1
            for j in range(i+1, len(tags)):
                pairs[tuple(sorted([tags[i], tags[j]]))] += 1
                
    top_tags = [t for t, _ in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]]
    
    z_data = []
    for t1 in top_tags:
        row = []
        for t2 in top_tags:
            if t1 == t2: row.append(0)
            else: row.append(pairs.get(tuple(sorted([t1, t2])), 0))
        z_data.append(row)
    fig_heatmap = px.imshow(z_data, x=top_tags, y=top_tags, color_continuous_scale='Viridis', title="Matrice de Co-occurrence")
    
    widths, heights, names = [], [], []
    for item in dataset:
        try:
            w, h = Image.open(item['img_path']).size
            widths.append(w); heights.append(h); names.append(item['img_name'])
        except: pass
    df_bucket = pd.DataFrame({'Largeur': widths, 'Hauteur': heights, 'Nom': names})
    fig_scatter = px.scatter(df_bucket, x='Largeur', y='Hauteur', hover_data=['Nom'], title="Distribution des Résolutions")
    fig_scatter.add_vline(x=1024, line_dash="dash", line_color="red"); fig_scatter.add_hline(y=1024, line_dash="dash", line_color="red")
    
    anti_pairs = []
    for i in range(len(top_tags)):
        for j in range(i+1, len(top_tags)):
            if pairs.get(tuple(sorted([top_tags[i], top_tags[j]])), 0) == 0:
                anti_pairs.append(f"[{top_tags[i]}] ❌ [{top_tags[j]}]")
    anti_txt = "\n".join(anti_pairs[:15]) if anti_pairs else "Tous les tops tags sont interconnectés."
    
    contradictions_found = []
    for item in dataset:
        cap = item['caption'].lower()
        for (a, b) in CONTRADICTIONS_LOGIQUES:
            if re.search(r'\b' + re.escape(a) + r'\b', cap) and re.search(r'\b' + re.escape(b) + r'\b', cap):
                contradictions_found.append(f"Image {item['img_name']} : Contient '{a}' ET '{b}'")
    contra_txt = "\n".join(contradictions_found) if contradictions_found else "✅ Aucune contradiction logique détectée."
    
    return fig_heatmap, fig_scatter, anti_txt, contra_txt

# ==========================================
# INTERFACE GRADIO & TRADUCTION UI V3.0 PRO
# ==========================================

def change_language(lang, stats_df, config_df):
    t = UI_T.get(lang, UI_T.get("FR", {})) 
    m = MSG.get(lang, MSG.get("FR", {}))
    new_stats = stats_df
    new_config = config_df
    kw = m.get("df_kw", "Mot-clé" if lang == "FR" else "Keyword")
    tgt = m.get("df_tgt", "Cible %" if lang == "FR" else "Target %")
    prio = m.get("df_prio", "Priorité" if lang == "FR" else "Priority")
    if isinstance(stats_df, pd.DataFrame) and not stats_df.empty:
        new_stats = stats_df.rename(columns={
            "Mot-clé": kw, "Keyword": kw,
            "Compte": "Count" if lang=="EN" else "Compte", "Count": "Compte" if lang=="FR" else "Count",
            "Actuel %": "Current %" if lang=="EN" else "Actuel %", "Current %": "Actuel %" if lang=="FR" else "Current %",
            "Cible %": tgt, "Target %": tgt,
            "Écart": "Diff" if lang=="EN" else "Écart", "Diff": "Écart" if lang=="FR" else "Diff"
        })
    if isinstance(config_df, pd.DataFrame) and not config_df.empty:
        new_config = config_df.rename(columns={
            "Priorité": prio, "Priority": prio, "Mot-clé": kw, "Keyword": kw, "Cible %": tgt, "Target %": tgt
        })
    lbl_pie = "Graphique (Répartition)" if lang == "FR" else "Chart (Distribution)"
    lbl_bar = "Graphique (Occurrences)" if lang == "FR" else "Chart (Occurrences)"
    lbl_exp = "Graphique (Export)" if lang == "FR" else "Chart (Export)"
    shortcuts_text = "🎹 **Actions :** `[←/→]` Naviguer | `[Ctrl+S]` Sauver caption | `[Alt+S]` Suivre/Retirer mot-clé (Stats)<br>🖱️ **Sélection :** `[Ctrl+Clic]` Multi-sélection | `[Maj+Clic]` Plage d'images | `[Ctrl+A]` Tout | `[Alt+C]` Vider" if lang == "FR" else "🎹 **Actions:** `[←/→]` Navigate | `[Ctrl+S]` Save caption | `[Alt+S]` Track/Untrack keyword (Stats)<br>🖱️ **Selection:** `[Ctrl+Click]` Multi-select | `[Shift+Click]` Select range | `[Ctrl+A]` Select All | `[Alt+C]` Clear"

    return (
        # Section V2 Originale (57 updates)
        gr.update(value=t.get("title", "")), gr.update(value=t.get("browse", "")), gr.update(value=t.get("load", "")),
        gr.update(value=t.get("status_wait", "")), gr.update(value=t.get("recipe_global", "")), gr.update(label=t.get("recipes_dd", "")),
        gr.update(label=t.get("recipe_name", "")), gr.update(value=t.get("save_recipe", "")), gr.update(placeholder=t.get("tracked_ph", "")),
        gr.update(value=t.get("gallery_title", "")), gr.update(label=t.get("search", ""), placeholder=t.get("search_ph", "")),
        gr.update(label=t.get("multi_cb", "")), gr.update(value=t.get("clear_sel", "")), gr.update(label=t.get("cols", "")),
        gr.update(value=t.get("hide_gal", "")), gr.update(label=t.get("tab_view", "")), gr.update(value=t.get("btn_prev", "")),
        gr.update(value=t.get("btn_next", "")), gr.update(value=shortcuts_text), gr.update(value=t.get("toggle_stat", "")),
        gr.update(value=t.get("save_cap", "")), gr.update(label=t.get("tab_batch", "")), gr.update(value=t.get("btn_undo", "")),
        gr.update(label=t.get("target_rep", "")), gr.update(label=t.get("synonyms", "")), gr.update(value=t.get("btn_rep_syn", "")),
        gr.update(label=t.get("rep_this", "")), gr.update(label=t.get("rep_that", "")), gr.update(label=t.get("use_regex", "")),
        gr.update(value=t.get("btn_apply", "")), gr.update(label=t.get("add_text", "")), 
        gr.update(choices=t.get("add_pos_choices", [""]), value=t.get("add_pos_choices", [""])[0] if t.get("add_pos_choices") else ""),
        gr.update(value=t.get("btn_add", "")), gr.update(value=t.get("btn_clean_com", "")), gr.update(value=t.get("btn_clean_dup", "")),
        gr.update(label=t.get("df_preview", "")), gr.update(label=t.get("tab_export", "")), gr.update(value=t.get("exp_desc", "")),
        gr.update(value=t.get("exp_edit", "")), gr.update(value=new_config, headers=t.get("exp_df_headers", [])), 
        gr.update(label=t.get("strat", ""), choices=t.get("strat_choices", ["", ""]), value=t.get("strat_choices", ["", ""])[1] if len(t.get("strat_choices", []))>1 else ""),
        gr.update(label=t.get("max_img", "")), gr.update(label=t.get("dest_folder", ""), placeholder=t.get("dest_ph", "")),
        gr.update(value=t.get("btn_simul", "")), gr.update(value=t.get("btn_exp", "")), gr.update(value=t.get("res_simul", "")),
        gr.update(value=t.get("exp_gal", "")), gr.update(label=t.get("tab_stats", "")), gr.update(value=t.get("stat_edit", "")), 
        gr.update(value=new_stats, headers=t.get("stat_df_headers", [])), gr.update(value=t.get("btn_top20", "")),
        gr.update(value=t.get("btn_orph", "")), gr.update(label=t.get("txt_orph", "")),
        gr.update(label=lbl_pie), gr.update(label=lbl_bar), gr.update(label=lbl_exp),
        
        # Section V3.0 Pro (50 updates)
        gr.update(label=t.get("guide_title", "")), gr.update(value=t.get("guide_text", "")),
        gr.update(label=t.get("tab_prep", "")), gr.update(value=t.get("prep_info", "")), gr.update(value=t.get("dup_title", "")), 
        gr.update(label=t.get("hash_tol", "")), gr.update(value=t.get("btn_scan_dups", "")), gr.update(label=t.get("dup_dd", "")), 
        gr.update(value=t.get("btn_del_A", "")), gr.update(value=t.get("btn_del_B", "")), gr.update(value=t.get("rename_title", "")), 
        gr.update(label=t.get("rename_prefix", "")), gr.update(value=t.get("btn_rename", "")), gr.update(value=t.get("resize_title", "")), 
        gr.update(label=t.get("prep_size", "")), gr.update(label=t.get("prep_format", "")), gr.update(label=t.get("prep_crop", "")), 
        gr.update(label=t.get("prep_alpha", "")), gr.update(label=t.get("prep_dest", "")), gr.update(value=t.get("btn_prep", "")),
        
        gr.update(label=t.get("tab_ai", "")), gr.update(value=t.get("ai_info", "")), gr.update(value=t.get("ai_conf_title", "")), 
        gr.update(label=t.get("api_backend", "")), gr.update(label=t.get("vlm_model", "")), gr.update(label=t.get("llm_model", "")), 
        gr.update(label=t.get("ai_adv_acc", "")), gr.update(label=t.get("api_url_input", "")), gr.update(label=t.get("ai_temp", "")), 
        gr.update(label=t.get("ai_ctx", "")), gr.update(label=t.get("ai_sys", "")), gr.update(value=t.get("ai_act_title", "")), 
        gr.update(label=t.get("ai_action_dd", "")), gr.update(label=t.get("ai_tpl_dd", "")), gr.update(label=t.get("ai_tpl_name", "")), 
        gr.update(value=t.get("btn_save_tpl", "")), gr.update(label=t.get("custom_prompt_input", "")), gr.update(label=t.get("use_vision_custom", "")),
        gr.update(label=t.get("injection_mode", "")), gr.update(value=t.get("btn_run_ai", "")), gr.update(value=t.get("btn_undo_ai", "")), 
        
        gr.update(value=t.get("bias_title", "")), gr.update(value=t.get("btn_bias", "")), gr.update(label=t.get("txt_bias", "")),
        gr.update(value=t.get("adv_stats_title", "")), gr.update(value=t.get("btn_calc_adv", "")), gr.update(label=t.get("plot_heatmap", "")), 
        gr.update(label=t.get("plot_bucket", "")), gr.update(value=t.get("anti_title", "")), gr.update(value=t.get("contra_title", ""))
    )

with gr.Blocks(title="IMG Dataset Refiner v3.0 Pro", css=css_code) as app:
    
    dataset_state = gr.State([])
    filtered_state = gr.State([])
    history_state = gr.State([])
    current_idx_state = gr.State(0)
    selected_indices_state = gr.State([]) 
    config_df_state = gr.State("{}") 
    stats_df_state = gr.State("{}")
    recipe_selected_row = gr.State(-1)
    
    dup_mapping_state = gr.State({})
    dup_idA = gr.State(-1)
    dup_idB = gr.State(-1)
    
    dummy_selection = gr.Textbox(visible=False, elem_id="dummy_selection")
    ui_hidden_sync_input = gr.Textbox(value="{}", elem_id="hidden_sync_input")
    ui_hidden_sync_btn = gr.Button(elem_id="hidden_sync_btn")
    ui_hidden_calc_btn = gr.Button(elem_id="hidden_calc_btn")
    ui_hidden_dnd_input = gr.Textbox(elem_id="hidden_dnd_input")
    ui_hidden_dnd_btn = gr.Button(elem_id="hidden_dnd_btn")
    ui_hidden_tags_input = gr.Textbox(elem_id="hidden_tags_input")
    
    t_init = UI_T.get("FR", {})

    with gr.Row():
        with gr.Column(scale=2):
            lang_radio = gr.Radio(["FR", "EN"], value="FR", label="Language / Langue")
            ui_title = gr.Markdown(t_init.get("title", "# 📊 IMG Dataset Refiner v3.0 Pro\n*Gère, visualise, et équilibre ton dataset.*"))
            
            ui_guide_acc = gr.Accordion(t_init.get("guide_title", "📖 Guide de Démarrage Rapide (Nouveau ? Cliquez ici)"), open=False)
            with ui_guide_acc:
                ui_guide_text = gr.Markdown(t_init.get("guide_text", "**Bienvenue dans IMG Dataset Refiner v3.0 Pro ! Voici comment utiliser cet outil :**\n1. **📂 Charger :** Entrez le chemin de votre dossier (contenant images et `.txt`) et cliquez sur *Charger*.\n2. **🖱️ Sélectionner :** Cliquez sur une image dans la galerie à gauche. Utilisez `[Ctrl+Clic]` ou `[Maj+Clic]` pour en sélectionner plusieurs.\n3. **✍️ Éditer :** Modifiez les tags dans l'onglet *Vue*. **C'est sauvegardé automatiquement !**\n4. **⚡ Actions par lots :** Utilisez l'onglet *Édition Batch* ou *Assistant IA* pour modifier toutes vos images sélectionnées d'un coup."))
            
            with gr.Row():
                dir_input = gr.Textbox(placeholder="C:\\mon\\dataset", show_label=False, scale=4)
                ui_browse_btn = gr.Button(t_init.get("browse", "📂 Parcourir"), scale=1)
            ui_load_btn = gr.Button(t_init.get("load", "🚀 Charger le Dataset"), variant="primary")
            ui_status_text = gr.Markdown(t_init.get("status_wait", "*En attente de chargement...*"))
            
        with gr.Column(scale=3):
            ui_recipe_global = gr.Markdown(t_init.get("recipe_global", "**Recette Globale (Synchronisée)**"))
            with gr.Row():
                ui_recipes_dropdown = gr.Dropdown(choices=list(load_recipes().keys()), label=t_init.get("recipes_dd", "Charger Recette"), scale=2)
                ui_recipe_name = gr.Textbox(label=t_init.get("recipe_name", "Nom pour sauver"), scale=1)
                ui_save_recipe_btn = gr.Button(t_init.get("save_recipe", "💾 Sauver"), scale=1)
            ui_tracked_words = gr.Textbox(show_label=False, placeholder=t_init.get("tracked_ph", "ex: p0se-s1:50, man:20"), lines=2, elem_id="tracked_words_input")

    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=0, elem_id="left_panel") as left_panel:
            ui_gallery_title = gr.Markdown(t_init.get("gallery_title", "### 🖼️ Galerie & Sélection"))
            ui_search_box = gr.Textbox(label=t_init.get("search", "🔍 Filtrer les images"), placeholder=t_init.get("search_ph", "Tapez un mot..."))
            with gr.Group():
                ui_multi_select_cb = gr.Checkbox(label=t_init.get("multi_cb", "✅ Mode Sélection Multiple"), value=False, interactive=True, elem_id="multi_cb")
                ui_clear_sel_btn = gr.Button(t_init.get("clear_sel", "🧹 Effacer la sélection"), elem_id="clear_sel_btn")
                ui_selection_status = gr.Markdown("**...**")
            ui_gallery_cols = gr.Slider(minimum=1, maximum=6, step=1, value=2, label=t_init.get("cols", "Colonnes"))
            gallery = gr.Gallery(label="Dataset", columns=2, rows=6, height=750, object_fit="contain", allow_preview=False, elem_id="main_gallery")
            
        with gr.Column(scale=1):
            ui_toggle_panel_btn = gr.Button(t_init.get("hide_gal", "◀ Masquer la Galerie"), elem_id="toggle_gallery_btn", variant="secondary", size="sm")
            
            with gr.Tabs():
                # --- ONGLET 1 : VUE ORIGINALE ---
                ui_tab_view = gr.Tab(t_init.get("tab_view", "👁️ Visualiseur & Édition"))
                with ui_tab_view:
                    gr.HTML("<div class='info-box'>💡 <b>Astuce Édition :</b> Cliquez sur une image à gauche pour la voir. Tapez vos mots-clés ci-dessous. Le texte est <b>sauvegardé automatiquement</b> !</div>")
                    with gr.Row():
                        ui_btn_prev = gr.Button(t_init.get("btn_prev", "⬅️ Précédent"), elem_id="prev_btn")
                        ui_btn_next = gr.Button(t_init.get("btn_next", "➡️ Suivant"), elem_id="next_btn")
                    ui_viewer_status = gr.Markdown("**...**")
                    with gr.Row():
                        current_img = gr.Image(interactive=False, type="filepath", height=350, elem_id="viewer_area")
                        with gr.Column(elem_id="viewer_area_text"):
                            highlight_preview = gr.HTML()
                            word_counter = gr.HTML("<div style='color:green;'>0</div>")
                            ui_viewer_shortcuts = gr.Markdown(t_init.get("shortcuts", "🎹 **Actions :** `[←/→]` Naviguer | `[Ctrl+S]` Sauver caption | `[Alt+S]` Suivre mot-clé"))
                            ui_toggle_tag_btn = gr.Button(t_init.get("toggle_stat", "🪄 Suivre/Retirer sélection (Stats)"), variant="secondary", elem_id="toggle_tag_btn")
                    current_caption = gr.Textbox(show_label=False, lines=4, elem_id="viewer_caption_area")
                    ui_save_single_btn = gr.Button(t_init.get("save_cap", "💾 Sauvegarder la Caption"), variant="primary", elem_id="save_single_btn")
                    ui_single_save_status = gr.Markdown()

                # --- ONGLET 2 : EDITION BATCH ORIGINALE ---
                ui_tab_batch = gr.Tab(t_init.get("tab_batch", "⚡ Édition en Batch"))
                with ui_tab_batch:
                    gr.HTML("<div class='info-box'>⚠️ <b>Cible :</b> Les actions ci-dessous s'appliqueront <b>uniquement aux images sélectionnées</b> (ou à toutes si aucune n'est sélectionnée).</div>")
                    ui_btn_undo = gr.Button(t_init.get("btn_undo", "↩️ ANNULER LA DERNIÈRE ACTION"), variant="stop")
                    ui_batch_status = gr.Markdown()
                    with gr.Row():
                        with gr.Group():
                            ui_target_rep = gr.Textbox(label=t_init.get("target_rep", "Tag répétitif (ex: 1girl)"))
                            ui_synonyms = gr.Textbox(label=t_init.get("synonyms", "Synonymes (séparés par des virgules)"))
                            ui_btn_rep_syn = gr.Button(t_init.get("btn_rep_syn", "Remplacer doublons par synonymes"))
                        with gr.Group():
                            ui_old_text = gr.Textbox(label=t_init.get("rep_this", "Remplacer ceci..."))
                            ui_new_text = gr.Textbox(label=t_init.get("rep_that", "... Par cela"))
                            ui_use_regex = gr.Checkbox(label=t_init.get("use_regex", "Regex"))
                            ui_btn_apply = gr.Button(t_init.get("btn_apply", "Appliquer"))
                    with gr.Row():
                        with gr.Group():
                            ui_add_text = gr.Textbox(label=t_init.get("add_text", "Texte à Ajouter"))
                            ui_add_pos = gr.Radio(t_init.get("add_pos_choices", ["Début", "Fin"]), value=t_init.get("add_pos_choices", ["Début", "Fin"])[0], show_label=False)
                            ui_btn_add = gr.Button(t_init.get("btn_add", "Ajouter"))
                        with gr.Group():
                            ui_btn_clean_com = gr.Button(t_init.get("btn_clean_com", "Nettoyer virgules et espaces"))
                            ui_btn_clean_dup = gr.Button(t_init.get("btn_clean_dup", "Retirer tags identiques purs"))
                    ui_preview_table = gr.Dataframe(label=t_init.get("df_preview", "Aperçu des changements"), interactive=False)

                # --- ONGLET 3 : PRE-TRAITEMENT (PRO) ---
                ui_tab_prep = gr.Tab(t_init.get("tab_prep", "🖼️ Pré-traitement & Doublons"))
                with ui_tab_prep:
                    ui_prep_info = gr.HTML(t_init.get("prep_info", "<div class='info-box'>ℹ️ <b>Astuce :</b> Avant de tagger vos images, utilisez cet onglet pour standardiser leur résolution ou repérer les images quasi-identiques (Doublons) qui pourraient fausser votre entraînement.</div>"))
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_dup_title = gr.Markdown(t_init.get("dup_title", "### 🔍 Traque aux Doublons Visuels"))
                            ui_hash_tol = gr.Slider(0, 20, 5, step=1, label=t_init.get("hash_tol", "Tolérance (0 = Clone exact, 10+ = Recadrage)"))
                            btn_scan_dups = gr.Button(t_init.get("btn_scan_dups", "Scanner le dossier"))
                            
                            dup_dropdown = gr.Dropdown(label=t_init.get("dup_dd", "Paires Suspectes"), interactive=True)
                            with gr.Row():
                                dup_img_A = gr.Image(label="Image A", interactive=False, height=200)
                                dup_img_B = gr.Image(label="Image B", interactive=False, height=200)
                            with gr.Row():
                                btn_del_A = gr.Button(t_init.get("btn_del_A", "🗑️ Supprimer A"), variant="stop")
                                btn_del_B = gr.Button(t_init.get("btn_del_B", "🗑️ Supprimer B"), variant="stop")
                            dup_status = gr.Markdown()
                            
                        with gr.Column(scale=1):
                            ui_rename_title = gr.Markdown(t_init.get("rename_title", "### 🚀 Renommage par lot"))
                            ui_rename_prefix = gr.Textbox(label=t_init.get("rename_prefix", "Préfixe (ex: mon_concept)"), placeholder="concept")
                            btn_rename = gr.Button(t_init.get("btn_rename", "Renommer tout le dataset"))
                            
                            gr.Markdown("---")
                            ui_resize_title = gr.Markdown(t_init.get("resize_title", "### 📐 Redimensionnement & Formatage"))
                            prep_size = gr.Dropdown(["512", "768", "1024", "1536"], value="1024", label=t_init.get("prep_size", "Résolution Max"))
                            prep_format = gr.Dropdown(["WebP", "JPEG"], value="WebP", label=t_init.get("prep_format", "Format"))
                            prep_crop = gr.Dropdown(["Conserver Ratio", "1:1 (Carré Centre)", "Smart Face Crop (OpenCV)"], value="Conserver Ratio", label=t_init.get("prep_crop", "Recadrage"))
                            prep_alpha = gr.Checkbox(value=True, label=t_init.get("prep_alpha", "Convertir fond transparent en Blanc (Recommandé)"))
                            prep_dest = gr.Textbox(label=t_init.get("prep_dest", "Dossier de destination (Laissez vide pour dossier auto)"), placeholder="ex: C:\\mon_dataset\\processed")
                            btn_prep = gr.Button(t_init.get("btn_prep", "Lancer le Traitement"), variant="primary")
                            prep_status = gr.Markdown()

                # --- ONGLET 4 : ASSISTANT IA (PRO) ---
                ui_tab_ai = gr.Tab(t_init.get("tab_ai", "🤖 Assistant IA Local"))
                with ui_tab_ai:
                    ui_ai_info = gr.HTML(t_init.get("ai_info", "<div class='info-box' style='border-color: #f59e0b; background-color: rgba(245, 158, 11, 0.1);'>💡 <b>Vous avez déjà vos fichiers <code>.gguf</code> téléchargés ?</b><br>Pour éviter de télécharger les modèles en double via Ollama, ouvrez simplement vos modèles dans <b>LM Studio</b> ou <b>KoboldCPP</b>, démarrez leur serveur local (souvent port 1234), et choisissez <i>API OpenAI / LM Studio</i> ci-dessous !</div>"))
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_ai_conf_title = gr.Markdown(t_init.get("ai_conf_title", "### ⚙️ Serveur et Modèles Locaux"))
                            api_backend = gr.Radio(["Ollama", "API OpenAI / LM Studio (GGUF locaux)"], label=t_init.get("api_backend", "Moteur IA (Backend)"), value="Ollama")
                            vlm_model = gr.Textbox(value="llava", label=t_init.get("vlm_model", "Modèle Vision (ex: llava, qwen2.5-vl, local-model)"))
                            llm_model = gr.Textbox(value="llama3.1", label=t_init.get("llm_model", "Modèle Texte (ex: llama3.1, local-model)"))
                            
                            ui_ai_adv_acc = gr.Accordion(t_init.get("ai_adv_acc", "🛠️ Paramètres Avancés API"), open=False)
                            with ui_ai_adv_acc:
                                api_url_input = gr.Textbox(value=DEFAULT_OLLAMA_URL, label=t_init.get("api_url_input", "URL du Serveur Local"), placeholder="http://127.0.0.1:11434")
                                ai_temp = gr.Slider(minimum=0.0, maximum=2.0, value=0.7, step=0.1, label=t_init.get("ai_temp", "Température (Créativité)"))
                                ai_ctx = gr.Number(value=4096, label=t_init.get("ai_ctx", "Contexte Max (Tokens)"))
                                ai_sys = gr.Textbox(label=t_init.get("ai_sys", "System Prompt"), lines=2)
                        
                        with gr.Column(scale=2):
                            ui_ai_act_title = gr.Markdown(t_init.get("ai_act_title", "### 🚀 Actions sur la sélection"))
                            default_action = "Auto-Taggage / Super OCR (VLM)"
                            ai_action_dropdown = gr.Dropdown([
                                "Auto-Taggage / Super OCR (VLM)",
                                "Reality Check & Hallucinations (VLM)",
                                "Concept Isolator (Spécial LoRA)",
                                "Traducteur Visuel (Booru ↔ Phrase Naturelle)",
                                "Tag Sorting & Standardisation",
                                "Traduction Automatique (Vers Anglais)",
                                "✨ Prompt Personnalisé (Texte/Vision)"
                            ], label=t_init.get("ai_action_dd", "Action IA"), value=default_action)
                            
                            ai_action_desc = gr.HTML()
                            
                            with gr.Group(visible=False) as custom_prompt_group:
                                with gr.Row():
                                    ai_template_dd = gr.Dropdown(choices=list(load_ai_recipes().keys()), label=t_init.get("ai_tpl_dd", "📚 Vos Templates"))
                                    ai_template_name = gr.Textbox(label=t_init.get("ai_tpl_name", "Nom du nouveau template"))
                                    btn_save_template = gr.Button(t_init.get("btn_save_tpl", "💾 Sauver Template"))
                                custom_prompt_input = gr.Textbox(label=t_init.get("custom_prompt_input", "Votre Prompt"), placeholder="Utilisez {tags} pour injecter les mots-clés actuels...", lines=3)
                                use_vision_for_custom = gr.Checkbox(label=t_init.get("use_vision_custom", "Fournir l'image au modèle (Utilisera le VLM)"))
                            
                            with gr.Group(visible=False) as injection_group:
                                injection_mode = gr.Radio(["Remplacer tout", "Ajouter au début", "Ajouter à la fin"], label=t_init.get("injection_mode", "Mode d'injection"), value="Remplacer tout")
                                
                            with gr.Row():
                                btn_run_ai = gr.Button(t_init.get("btn_run_ai", "✨ Lancer l'IA sur la Sélection"), variant="primary")
                                btn_undo_ai = gr.Button(t_init.get("btn_undo_ai", "↩️ Annuler (Undo)"), variant="stop")
                            ai_status = gr.Markdown()
                    
                    gr.Markdown("---")
                    ui_bias_title = gr.Markdown(t_init.get("bias_title", "### 🤖 Profiling de Dataset par l'IA"))
                    btn_bias = gr.Button(t_init.get("btn_bias", "Générer le rapport de Biais Sémantique (LLM)"), variant="secondary")
                    txt_bias = gr.Textbox(label=t_init.get("txt_bias", "Rapport IA"), lines=5, interactive=False)

                # --- ONGLET 5 : EXPORT ORIGINAL ---
                ui_tab_export = gr.Tab(t_init.get("tab_export", "📁 Assistant d'Export & Recette"))
                with ui_tab_export:
                    ui_exp_desc = gr.Markdown(t_init.get("exp_desc", "Configurez ici votre recette..."))
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_exp_edit = gr.Markdown(t_init.get("exp_edit", "### ⚙️ Éditeur de Recette..."))
                            with gr.Row():
                                ui_btn_up = gr.Button("⬆️ Monter (Alt+Haut)", variant="secondary", size="sm", elem_id="btn_move_up")
                                ui_btn_down = gr.Button("⬇️ Descendre (Alt+Bas)", variant="secondary", size="sm", elem_id="btn_move_down")
                                ui_btn_del = gr.Button("🗑️ Supprimer", variant="stop", size="sm")
                            with gr.Row():
                                ui_quick_prio = gr.Dropdown(label="N° Priorité", choices=[str(i) for i in range(1, 101)], allow_custom_value=True, scale=1)
                                ui_quick_target = gr.Number(label="Cible %", scale=1)
                            ui_export_config_df = gr.Dataframe(headers=t_init.get("exp_df_headers", ["Priorité", "Mot-clé", "Cible %"]), interactive=True, type="pandas", row_count=("dynamic"), column_count=(3, "fixed"))
                            ui_strategy_radio = gr.Radio(t_init.get("strat_choices", ["", "Filtre Classique"]), value=t_init.get("strat_choices", ["", "Filtre Classique"])[1] if len(t_init.get("strat_choices", [""])) > 1 else "", label=t_init.get("strat", "🤖 Stratégie"))
                            ui_max_img_input = gr.Number(label=t_init.get("max_img", "Limite d'images (0 = Infini)"), value=0, precision=0)
                            ui_export_dir = gr.Textbox(label=t_init.get("dest_folder", "Dossier de Destination"), placeholder=t_init.get("dest_ph", "Laisser vide..."))
                            with gr.Row():
                                ui_btn_simul = gr.Button(t_init.get("btn_simul", "🔍 Simuler"), variant="secondary")
                                ui_btn_exp = gr.Button(t_init.get("btn_exp", "🚀 Exporter le Dataset"), variant="primary")
                        with gr.Column(scale=1):
                            ui_res_simul = gr.Markdown(t_init.get("res_simul", "### 📊 Résultat de la Simulation"))
                            ui_export_status = gr.Markdown()
                            export_pie = gr.Plot(label="Graphique (Export)")
                    ui_exp_gal = gr.Markdown(t_init.get("exp_gal", "### 🖼️ Miniature du Dataset Final"))
                    export_gallery = gr.Gallery(columns=8, rows=2, height=250, object_fit="contain", allow_preview=False)

                # --- ONGLET 6 : STATS ORIGINALES + ANALYTIQUES PRO ---
                ui_tab_stats = gr.Tab(t_init.get("tab_stats", "📈 Statistiques Générales"))
                with ui_tab_stats:
                    ui_stats_status = gr.Markdown()
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_stat_edit = gr.Markdown(t_init.get("stat_edit", "### 📊 Données (Calcul Instantané)..."))
                            ui_stats_table = gr.Dataframe(headers=t_init.get("stat_df_headers", []), interactive=True, type="pandas", row_count=("dynamic"))
                            ui_btn_civitai = gr.Button("📋 Générer tableau format CivitAI/Markdown", variant="secondary")
                            ui_civitai_output = gr.Textbox(label="Format CivitAI", interactive=False, lines=5)
                            with gr.Row():
                                ui_btn_top20 = gr.Button(t_init.get("btn_top20", "🪄 Remplir avec le Top 20"))
                                ui_btn_orph = gr.Button(t_init.get("btn_orph", "🕵️ Tags Orphelins"))
                            ui_txt_orph = gr.Textbox(label=t_init.get("txt_orph", "Orphelins"), lines=4)
                            
                        with gr.Column(scale=2):
                            pie_chart = gr.Plot(label="Graphique (Répartition)")
                            bar_chart = gr.Plot(label="Graphique (Occurrences)")
                            gr.Markdown("---")
                            ui_adv_stats_title = gr.Markdown(t_init.get("adv_stats_title", "### 🧬 Analytiques Avancées (v3.0 Pro)"))
                            btn_calc_adv = gr.Button(t_init.get("btn_calc_adv", "Générer/Rafraîchir les Audits de Co-occurrence"), variant="primary")
                            with gr.Row():
                                plot_heatmap = gr.Plot(label="Matrice de Co-occurrence")
                                plot_bucket = gr.Plot(label="Résolutions")
                            with gr.Row():
                                with gr.Column():
                                    ui_anti_title = gr.Markdown(t_init.get("anti_title", "### 🛡️ Matrice d'Exclusion (Anti-Heatmap)"))
                                    txt_anti = gr.Textbox(show_label=False, lines=6, interactive=False)
                                with gr.Column():
                                    ui_contra_title = gr.Markdown(t_init.get("contra_title", "### ⚠️ Chasseur de Contradictions Logiques"))
                                    txt_contra = gr.Textbox(show_label=False, lines=6, interactive=False)

# ==========================================
# CÂBLAGE DES ÉVÉNEMENTS (Version Définitive)
# ==========================================

    def auto_switch_api_url(backend):
        if backend == "Ollama": return "http://127.0.0.1:11434"
        else: return "http://127.0.0.1:1234"
        
    api_backend.change(fn=auto_switch_api_url, inputs=[api_backend], outputs=[api_url_input])

    ai_action_dropdown.change(fn=update_ai_action_desc, inputs=[ai_action_dropdown], outputs=[ai_action_desc, custom_prompt_group, injection_group])

    js_toggle = """function() {
        const panel = document.getElementById('left_panel'); const btn = document.getElementById('toggle_gallery_btn');
        if (panel.classList.contains('collapsed')) { panel.classList.remove('collapsed'); btn.innerText = "◀"; } 
        else { panel.classList.add('collapsed'); btn.innerText = "▶"; }
        return [];
    }"""
    ui_toggle_panel_btn.click(fn=None, js=js_toggle)
    ui_browse_btn.click(fn=browse_folder, inputs=[], outputs=[dir_input])
    ui_gallery_cols.change(fn=lambda x: gr.update(columns=x), inputs=[ui_gallery_cols], outputs=[gallery])

    # Core V2 Navigation Bindings
    ui_load_btn.click(
        fn=load_dataset, inputs=[dir_input, lang_radio], 
        outputs=[dataset_state, filtered_state, history_state, ui_status_text, gallery, selected_indices_state, ui_selection_status, ui_hidden_sync_input, ui_hidden_tags_input]
    )
    ui_search_box.change(fn=filter_gallery, inputs=[dataset_state, ui_search_box, lang_radio], outputs=[filtered_state, gallery, selected_indices_state, ui_selection_status, ui_hidden_sync_input])
    
    ui_hidden_sync_btn.click(
        fn=handle_sync, inputs=[ui_hidden_sync_input, dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], 
        outputs=[dataset_state, filtered_state, selected_indices_state, ui_selection_status, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status, ui_hidden_tags_input]
    )
    
    ui_btn_prev.click(fn=nav_prev, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], outputs=[dataset_state, filtered_state, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status])
    ui_btn_next.click(fn=nav_next, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], outputs=[dataset_state, filtered_state, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status])
    ui_save_single_btn.click(fn=save_single_caption, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, lang_radio], outputs=[dataset_state, filtered_state, ui_single_save_status])
    ui_clear_sel_btn.click(fn=clear_selection, inputs=[lang_radio], outputs=[selected_indices_state, ui_selection_status, ui_hidden_sync_input])

    # Stats Live V2
    js_get_sel = "function(tracker, dummy) { let sel = window.getSelection().toString().trim(); if(!sel) { let ae = document.activeElement; if(ae && (ae.tagName === 'TEXTAREA' || ae.tagName === 'INPUT')) sel = ae.value.substring(ae.selectionStart, ae.selectionEnd).trim(); } return [tracker, sel || \"\"]; }"
    ui_hidden_calc_btn.click(fn=analyze_dataset, inputs=[dataset_state, ui_tracked_words, lang_radio], outputs=[pie_chart, bar_chart, ui_stats_table, stats_df_state, ui_export_config_df, config_df_state, ui_stats_status])
    ui_tracked_words.change(fn=update_viewer, inputs=[filtered_state, current_idx_state, ui_tracked_words, lang_radio], outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status])
    ui_toggle_tag_btn.click(fn=toggle_tracked_word, inputs=[ui_tracked_words, dummy_selection], outputs=[ui_tracked_words], js=js_get_sel).success(fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }")
    current_caption.change(fn=update_word_count, inputs=[current_caption, lang_radio], outputs=[word_counter])
    
    # Tableaux & Recettes
    ui_recipes_dropdown.change(fn=apply_recipe, inputs=[ui_recipes_dropdown], outputs=[ui_tracked_words])
    ui_save_recipe_btn.click(fn=save_recipe, inputs=[ui_recipe_name, ui_tracked_words], outputs=[ui_recipes_dropdown, ui_status_text])
    
    ui_export_config_df.select(fn=get_row_index, inputs=[config_df_state], outputs=[recipe_selected_row, ui_quick_prio, ui_quick_target])
    ui_quick_prio.change(fn=apply_quick_prio, inputs=[ui_quick_prio, recipe_selected_row, config_df_state], outputs=[ui_export_config_df, config_df_state, ui_tracked_words, recipe_selected_row])
    ui_quick_target.change(fn=apply_quick_target, inputs=[ui_quick_target, recipe_selected_row, config_df_state], outputs=[ui_export_config_df, config_df_state, ui_tracked_words])
    ui_btn_up.click(fn=df_move_up, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_btn_down.click(fn=df_move_down, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_btn_del.click(fn=df_delete_row, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_hidden_dnd_btn.click(fn=handle_drag_and_drop, inputs=[ui_hidden_dnd_input, ui_export_config_df], outputs=[ui_export_config_df, ui_tracked_words])
    ui_export_config_df.change(fn=handle_recipe_df_safe, inputs=[ui_export_config_df, config_df_state, ui_tracked_words], outputs=[ui_export_config_df, config_df_state, ui_tracked_words])
    
    ui_btn_top20.click(fn=auto_fill_top_tags, inputs=[dataset_state], outputs=[ui_tracked_words]).success(fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }")
    ui_btn_orph.click(fn=find_orphans, inputs=[dataset_state, lang_radio], outputs=[ui_txt_orph])
    ui_btn_civitai.click(fn=generate_civitai_format, inputs=[ui_stats_table], outputs=[ui_civitai_output])
    ui_stats_table.change(fn=handle_stats_df_safe, inputs=[ui_stats_table, stats_df_state, ui_tracked_words], outputs=[ui_stats_table, stats_df_state, ui_tracked_words]).success(fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }")

    # Batch Original
    js_confirm = "function() { if (!confirm('⚠️ Appliquer cette modification en masse ? / Apply this mass modification?')) throw new Error('Annulé.'); }"
    ui_btn_undo.click(fn=None, js="function(){ if(!confirm('⚠️ Annuler ?')) throw new Error('Annulé'); }").success(fn=undo_last_action, inputs=[dataset_state, history_state, lang_radio], outputs=[dataset_state, filtered_state, ui_batch_status])
    ui_btn_add.click(fn=None, js=js_confirm).success(fn=batch_add, inputs=[dataset_state, ui_add_text, ui_add_pos, selected_indices_state, ui_search_box, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_apply.click(fn=None, js=js_confirm).success(fn=batch_replace, inputs=[dataset_state, ui_old_text, ui_new_text, ui_use_regex, selected_indices_state, ui_search_box, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_clean_com.click(fn=None, js=js_confirm).success(fn=batch_clean_commas, inputs=[dataset_state, selected_indices_state, ui_search_box, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_clean_dup.click(fn=None, js=js_confirm).success(fn=batch_remove_duplicates, inputs=[dataset_state, selected_indices_state, ui_search_box, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_rep_syn.click(fn=None, js=js_confirm).success(fn=batch_synonyms, inputs=[dataset_state, ui_target_rep, ui_synonyms, selected_indices_state, ui_search_box, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])

    # Export
    ui_btn_simul.click(fn=simulate_and_export, inputs=[dataset_state, ui_export_dir, ui_export_config_df, gr.State(True), selected_indices_state, ui_strategy_radio, ui_max_img_input, lang_radio], outputs=[ui_export_status, export_gallery, export_pie, bar_chart])
    ui_btn_exp.click(fn=simulate_and_export, inputs=[dataset_state, ui_export_dir, ui_export_config_df, gr.State(False), selected_indices_state, ui_strategy_radio, ui_max_img_input, lang_radio], outputs=[ui_export_status, export_gallery, export_pie, bar_chart])

    # --- PRO: Pré-traitement & Doublons ---
    btn_scan_dups.click(fn=scan_duplicates_advanced, inputs=[dataset_state, ui_hash_tol], outputs=[dup_dropdown, dup_mapping_state])
    dup_dropdown.change(fn=load_duplicate_pair, inputs=[dup_dropdown, dup_mapping_state], outputs=[dup_img_A, dup_img_B, dup_idA, dup_idB])
    btn_del_A.click(fn=delete_duplicate, inputs=[dataset_state, filtered_state, dup_idA, dup_dropdown, dup_mapping_state], outputs=[dataset_state, filtered_state, dup_dropdown, dup_mapping_state, dup_status])
    btn_del_B.click(fn=delete_duplicate, inputs=[dataset_state, filtered_state, dup_idB, dup_dropdown, dup_mapping_state], outputs=[dataset_state, filtered_state, dup_dropdown, dup_mapping_state, dup_status])
    btn_rename.click(fn=batch_rename_dataset, inputs=[dataset_state, ui_rename_prefix], outputs=[dataset_state, prep_status])
    btn_prep.click(fn=batch_process_images, inputs=[dataset_state, prep_dest, prep_size, prep_format, prep_crop, prep_alpha], outputs=[prep_status])

    # --- PRO: IA & Paramètres ---
    ai_template_dd.change(fn=apply_ai_recipe, inputs=[ai_template_dd], outputs=[custom_prompt_input])
    btn_save_template.click(fn=save_ai_recipe, inputs=[ai_template_name, custom_prompt_input], outputs=[ai_template_dd])
    btn_run_ai.click(
        fn=process_ai_action, 
        inputs=[dataset_state, selected_indices_state, ui_search_box, ai_action_dropdown, custom_prompt_input, injection_mode, use_vision_for_custom, vlm_model, llm_model, api_backend, api_url_input, ai_temp, ai_ctx, ai_sys, lang_radio],
        outputs=[dataset_state, filtered_state, history_state, ai_status, ui_hidden_tags_input]
    )
    btn_undo_ai.click(fn=None, js="function(){ if(!confirm('⚠️ Annuler la dernière action IA ?')) throw new Error('Annulé'); }").success(fn=undo_last_action, inputs=[dataset_state, history_state, lang_radio], outputs=[dataset_state, filtered_state, ai_status])
    btn_bias.click(fn=analyze_bias, inputs=[dataset_state, llm_model, api_backend, api_url_input, ai_temp, ai_ctx, ai_sys], outputs=[txt_bias])

    # --- PRO: Stats Avancées ---
    btn_calc_adv.click(fn=update_advanced_stats, inputs=[dataset_state], outputs=[plot_heatmap, plot_bucket, txt_anti, txt_contra])

    # Changement de langue dynamique
    lang_radio.change(
        fn=change_language, inputs=[lang_radio, ui_stats_table, ui_export_config_df],
        outputs=[
            ui_title, ui_browse_btn, ui_load_btn, ui_status_text, ui_recipe_global, ui_recipes_dropdown, ui_recipe_name, ui_save_recipe_btn, ui_tracked_words,
            ui_gallery_title, ui_search_box, ui_multi_select_cb, ui_clear_sel_btn, ui_gallery_cols, ui_toggle_panel_btn, ui_tab_view, ui_btn_prev, ui_btn_next,
            ui_viewer_shortcuts, ui_toggle_tag_btn, ui_save_single_btn, ui_tab_batch, ui_btn_undo, ui_target_rep, ui_synonyms, ui_btn_rep_syn,
            ui_old_text, ui_new_text, ui_use_regex, ui_btn_apply, ui_add_text, ui_add_pos, ui_btn_add, ui_btn_clean_com, ui_btn_clean_dup, ui_preview_table,
            ui_tab_export, ui_exp_desc, ui_exp_edit, ui_export_config_df, ui_strategy_radio, ui_max_img_input, ui_export_dir, ui_btn_simul, ui_btn_exp, ui_res_simul,
            ui_exp_gal, ui_tab_stats, ui_stat_edit, ui_stats_table, ui_btn_top20, ui_btn_orph, ui_txt_orph, pie_chart, bar_chart, export_pie,
            # Nouveaux champs Pro
            ui_guide_acc, ui_guide_text,
            ui_tab_prep, ui_prep_info, ui_dup_title, ui_hash_tol, btn_scan_dups, dup_dropdown, btn_del_A, btn_del_B,
            ui_rename_title, ui_rename_prefix, btn_rename, ui_resize_title, prep_size, prep_format, prep_crop, prep_alpha, prep_dest, btn_prep,
            ui_tab_ai, ui_ai_info, ui_ai_conf_title, api_backend, vlm_model, llm_model, ui_ai_adv_acc, api_url_input, ai_temp, ai_ctx, ai_sys,
            ui_ai_act_title, ai_action_dropdown, ai_template_dd, ai_template_name, btn_save_template, custom_prompt_input, use_vision_for_custom,
            injection_mode, btn_run_ai, btn_undo_ai, ui_bias_title, btn_bias, txt_bias,
            ui_adv_stats_title, btn_calc_adv, plot_heatmap, plot_bucket, ui_anti_title, ui_contra_title
        ]
    )

    app.load(fn=lambda: None, inputs=None, outputs=None, js=custom_js)

if __name__ == "__main__":
    try:
        app.launch(inbrowser=True, server_name="127.0.0.1", css=css_code)
    except TypeError:
        # Fallback de sécurité Gradio 4
        app.launch(inbrowser=True, server_name="127.0.0.1")