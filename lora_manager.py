import gradio as gr
import os
import re
import shutil
import json
import io
import copy
import plotly.express as px
import pandas as pd
from collections import Counter

# ==========================================
# CONFIGURATION & DICTIONNAIRES DE LANGUE
# ==========================================

RECIPES_FILE = "lora_recipes.json"

MSG = {"FR": {}, "EN": {}}
UI_T = {"FR": {}, "EN": {}}

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
# STYLES CSS NATIFS
# ==========================================
css_code = """
#left_panel {
    resize: horizontal; overflow-x: hidden; overflow-y: auto; width: 380px; min-width: 250px; max-width: 70vw;
    flex: none !important; border-right: 2px solid #374151; padding-right: 15px;
    transition: min-width 0.3s ease, width 0.3s ease, padding 0.3s ease, opacity 0.3s ease;
}
#left_panel.collapsed { width: 0px !important; min-width: 0px !important; padding: 0px !important; margin: 0px !important; border: none !important; opacity: 0; pointer-events: none; }
.caption-label { font-size: 14px !important; font-weight: bold !important; color: #4ade80 !important; display: none !important; }

/* Highlight CSS 100% JS pour la Sélection Instantanée */
.custom-selected {
    outline: 4px solid #ff8800 !important;
    outline-offset: -4px !important;
    box-shadow: inset 0 0 20px rgba(255, 136, 0, 0.9) !important;
    border-radius: 8px !important;
}
.custom-selected img {
    filter: sepia(0.8) hue-rotate(330deg) saturate(3) !important;
    opacity: 0.8 !important;
}

/* Cache les inputs techniques de synchro Gradio sans les détruire du DOM ! */
#hidden_sync_input, #hidden_sync_btn, #hidden_calc_btn, #hidden_dnd_input, #hidden_dnd_btn { 
    display: none !important; 
}

/* CSS Drag & Drop Table Avancé */
.gradio-dataframe tbody tr { transition: background-color 0.2s, opacity 0.2s; }
.gradio-dataframe tbody tr[draggable="true"] { cursor: grab !important; }
.gradio-dataframe tbody tr[draggable="true"]:active { cursor: grabbing !important; }
.gradio-dataframe tbody tr.dragging { opacity: 0.4; background-color: rgba(255, 136, 0, 0.3) !important; outline: 2px dashed #ff8800; outline-offset: -2px;}

/* Custom Context Menu */
#customContextMenu {
    position: absolute; z-index: 99999; background: #2A2B32; border: 1px solid #4ade80; 
    border-radius: 8px; padding: 6px; box-shadow: 0px 8px 16px rgba(0,0,0,0.6); min-width: 180px;
}
.menu-item {
    padding: 8px 12px; cursor: pointer; color: #e5e7eb; font-size: 14px; 
    border-radius: 4px; transition: background 0.1s, color 0.1s; font-weight: 500;
}
.menu-item:hover { background: #4ade80; color: #111827; }
"""

# ==========================================
# JAVASCRIPT GLOBAL ULTIME
# ==========================================
custom_js = """
function() {
    if (window.__DIES_INJECTED) return;
    window.__DIES_INJECTED = true;

    document.body.classList.add('dark');
    
    window.gallerySelectedIndices = new Set();
    window.lastClickedIndex = -1;

    function updateGalleryVisuals() {
        document.querySelectorAll('#main_gallery button').forEach((btn, idx) => {
            btn.classList.toggle('custom-selected', window.gallerySelectedIndices.has(idx));
        });
    }

    // Synchro unifiée : Envoie Sélection + Demande d'affichage en UNE seule fois
    function syncWithPython(viewIndex) {
        const payload = {
            selected: Array.from(window.gallerySelectedIndices),
            viewIndex: viewIndex
        };
        const wrapper = document.getElementById('hidden_sync_input');
        const inputEl = wrapper ? wrapper.querySelector('textarea, input') : null;
        if (inputEl) {
            inputEl.value = JSON.stringify(payload);
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(() => {
                const btn = document.getElementById('hidden_sync_btn');
                if (btn) btn.click();
            }, 30);
        }
    }

    const observer = new MutationObserver(() => { 
        updateGalleryVisuals(); 
        
        // Listener intelligent sur la zone de mots clés pour éviter la boucle infinie
        const trackedWrapper = document.getElementById('tracked_words_input');
        const trackedInput = trackedWrapper ? trackedWrapper.querySelector('textarea') : null;
        if (trackedInput && !trackedInput.dataset.commaListener) {
            trackedInput.dataset.commaListener = "true";
            
            trackedInput.addEventListener('keyup', function(e) {
                // Déclenche le calcul uniquement sur Virgule ou Entrée
                if (e.key === ',' || e.key === 'Enter') {
                    setTimeout(() => document.getElementById('hidden_calc_btn')?.click(), 50);
                }
            });
            trackedInput.addEventListener('blur', function(e) {
                setTimeout(() => document.getElementById('hidden_calc_btn')?.click(), 50);
            });
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // ================= SÉLECTION EXCEL-LIKE (Option Double Clic Svelte) =================
    // Observe l'apparition des champs de saisie pour sélectionner leur texte automatiquement
    const svelteInputObserver = new MutationObserver((mutations) => {
        mutations.forEach(m => {
            m.addedNodes.forEach(node => {
                if (node.nodeType === 1) {
                    const input = node.tagName === 'INPUT' ? node : node.querySelector('input');
                    if (input && input.closest('.gradio-dataframe')) {
                        let tries = 0;
                        const selectInterval = setInterval(() => {
                            input.select(); // Surligne tout (Excel-like !)
                            if (tries++ > 15) clearInterval(selectInterval);
                        }, 20);
                    }
                }
            });
        });
    });
    svelteInputObserver.observe(document.body, { childList: true, subtree: true });

    // ================= DRAG & DROP TABLEAU =================
    let dragStartIndex = -1;
    document.addEventListener('mousedown', function(e) {
        const tr = e.target.closest('.gradio-dataframe tbody tr');
        if (!tr) return;
        if (e.target.closest('input') || e.target.closest('textarea')) {
            tr.removeAttribute('draggable');
        } else {
            tr.setAttribute('draggable', 'true');
        }
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
            if (e.clientY < mid) { tr.before(draggingTr); } 
            else { tr.after(draggingTr); }
        }
    });

    document.addEventListener('dragend', function(e) {
        const tr = e.target.closest('tbody tr');
        if (tr) {
            tr.classList.remove('dragging');
            tr.removeAttribute('draggable');
        }
    });

    document.addEventListener('drop', function(e) {
        const tr = e.target.closest('tbody tr');
        if (tr) {
            e.preventDefault();
            const draggingTr = document.querySelector('.dragging');
            if(draggingTr) {
                draggingTr.classList.remove('dragging');
                draggingTr.removeAttribute('draggable');
            }
            
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

    // ================= RACCOURCIS CLAVIERS =================
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

    // ================= GESTION DU CLIC GALERIE =================
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
            // Clic simple normal
            window.gallerySelectedIndices.clear();
            window.gallerySelectedIndices.add(index); 
        }

        window.lastClickedIndex = index;
        updateGalleryVisuals();
        syncWithPython(index);
    }, true);

    // ================= MENU CONTEXTUEL CLIC DROIT =================
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
# FONCTIONS LOGIQUES PYTHON
# ==========================================

def norm_tracked_words(s):
    if not s or not isinstance(s, str): return ""
    return ",".join(sorted([x.strip().lower() for x in s.split(',') if x.strip()]))

def get_gallery_items(filtered_dataset, lang):
    return [(item['img_path'], "") for item in filtered_dataset]

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
    msg_no_sel = MSG[lang].get("no_sel_all", "No selection")
    if not os.path.isdir(directory): 
        return [], [], [], MSG[lang].get("folder_not_found", "Folder not found"), [], [], msg_no_sel, "{}"
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
    success_msg = MSG[lang].get("images_loaded", "{count} images loaded.").format(count=len(dataset))
    gr.Info(success_msg)
    return dataset, dataset, [], success_msg, gal_items, [], msg_no_sel, "{}"

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
    
    gr.Info(MSG[lang].get("saved", "Saved: {name}").format(name=item_filtered['img_name']))

# === FONCTION UNIFIÉE ===
def handle_sync(payload_str, dataset, filtered_dataset, old_idx, old_caption, tracked_words, lang):
    silent_save(dataset, filtered_dataset, old_idx, old_caption, lang)
    
    try:
        data = json.loads(payload_str)
        sel_js = data.get("selected", [])
        view_idx = int(data.get("viewIndex", 0))
    except:
        sel_js = []
        view_idx = 0
        
    real_ids = []
    if filtered_dataset:
        for i in sel_js:
            if 0 <= i < len(filtered_dataset): real_ids.append(filtered_dataset[i]['id'])
    
    sel_text = MSG[lang].get("selected_multi", "{count} selected").format(count=len(real_ids)) if real_ids else MSG[lang].get("no_sel_batch", "")
    
    img_path, hl_html, cap, wc, c_idx, v_status = update_viewer(filtered_dataset, view_idx, tracked_words, lang)
    return dataset, filtered_dataset, real_ids, sel_text, img_path, hl_html, cap, wc, c_idx, v_status

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

def safe_df_to_tracked_words(df, current_str):
    new_str = df_to_tracked_words(df)
    if norm_tracked_words(new_str) == norm_tracked_words(current_str):
        return gr.update()
    return new_str

# ==========================================
# GESTION DU TABLEAU & MENU "SAISIE RAPIDE"
# ==========================================

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
        except Exception:
            pass
            
    try:
        new_df[prio_col] = pd.to_numeric(new_df[prio_col], errors='coerce').fillna(999).astype(int)
        new_df = new_df.sort_values(by=prio_col).reset_index(drop=True)
        new_df[prio_col] = range(1, len(new_df) + 1)
    except:
        pass
    
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
        if old_idx < 0 or old_idx >= len(current_df) or new_idx < 0 or new_idx >= len(current_df):
            return current_df, gr.update()
            
        df_list = current_df.to_dict('records')
        item = df_list.pop(old_idx)
        df_list.insert(new_idx, item)
        new_df = pd.DataFrame(df_list)
        
        prio_col = "Priorité" if "Priorité" in new_df.columns else "Priority"
        new_df[prio_col] = range(1, len(new_df) + 1)
        return new_df, df_to_tracked_words(new_df)
    except:
        return current_df, gr.update()

def generate_civitai_format(df):
    if df is None or df.empty: return ""
    md = "| " + " | ".join(df.columns) + " |\n"
    md += "|" + "|".join(["---" for _ in df.columns]) + "|\n"
    for _, row in df.iterrows():
        md += "| " + " | ".join(str(x) for x in row.values) + " |\n"
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

# BATCH FUNCTIONS
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

def batch_add(dataset, text, pos, selected_ids, lang):
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
    return dataset, dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_replace(dataset, old_text, new_text, use_regex, selected_ids, lang):
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
    return dataset, dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_clean_commas(dataset, selected_ids, lang):
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
    return dataset, dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_remove_duplicates(dataset, selected_ids, lang):
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
    return dataset, dataset, history, msg, create_preview_df(history, dataset, lang)

def batch_synonyms(dataset, target_tag, synonyms_str, selected_ids, lang):
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
    return dataset, dataset, history, msg, create_preview_df(history, dataset, lang)

def simulate_and_export(dataset, export_dir, config_df, is_simulation, selected_ids, strategy, max_images, lang):
    if not dataset: 
        return MSG[lang].get("no_dataset", ""), [], None, None
        
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
            if sum(needs.values()) == 0:
                 to_export = relevant[:lim]
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
                        if re.search(r'\b' + re.escape(tag) + r'\b', chosen['caption'].lower()) and tag in needs:
                            needs[tag] -= 1
        else:
            to_export = relevant[:lim]

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
        if not export_dir or str(export_dir).strip() == "":
            export_dir = os.path.join(os.getcwd(), "output", "dataset_final")
            
        if not os.path.exists(export_dir): 
            os.makedirs(export_dir)
            
        for item in to_export:
            shutil.copy2(item['img_path'], os.path.join(export_dir, item['img_name']))
            shutil.copy2(item['txt_path'], os.path.join(export_dir, os.path.basename(item['txt_path'])))
            
        msg = MSG[lang].get("export_success", "Success").format(count=len(to_export), dest=export_dir)
        gr.Info(f"✅ Export réussi dans {export_dir}")
        return msg, gallery_preview, p_fig, b_fig

# ==========================================
# INTERFACE GRADIO
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
            "Priorité": prio, "Priority": prio,
            "Mot-clé": kw, "Keyword": kw,
            "Cible %": tgt, "Target %": tgt
        })
    
    lbl_pie = "Graphique (Répartition)" if lang == "FR" else "Chart (Distribution)"
    lbl_bar = "Graphique (Occurrences)" if lang == "FR" else "Chart (Occurrences)"
    lbl_exp = "Graphique (Export)" if lang == "FR" else "Chart (Export)"

    shortcuts_text = "🎹 **Actions :** `[←/→]` Naviguer | `[Ctrl+S]` Sauver caption | `[Alt+S]` Suivre/Retirer mot-clé (Stats)<br>🖱️ **Sélection :** `[Ctrl+Clic]` Multi-sélection | `[Maj+Clic]` Plage d'images | `[Ctrl+A]` Tout | `[Alt+C]` Vider" if lang == "FR" else "🎹 **Actions:** `[←/→]` Navigate | `[Ctrl+S]` Save caption | `[Alt+S]` Track/Untrack keyword (Stats)<br>🖱️ **Selection:** `[Ctrl+Click]` Multi-select | `[Shift+Click]` Select range | `[Ctrl+A]` Select All | `[Alt+C]` Clear"

    # Attention: Doit correspondre EXACTEMENT au outputs=[...]
    return (
        gr.update(value=t.get("title", "")), 
        gr.update(value=t.get("browse", "")), 
        gr.update(value=t.get("load", "")),
        gr.update(value=t.get("status_wait", "")), 
        gr.update(value=t.get("recipe_global", "")), 
        gr.update(label=t.get("recipes_dd", "")),
        gr.update(label=t.get("recipe_name", "")), 
        gr.update(value=t.get("save_recipe", "")), 
        gr.update(placeholder=t.get("tracked_ph", "")),
        gr.update(value=t.get("gallery_title", "")), 
        gr.update(label=t.get("search", ""), placeholder=t.get("search_ph", "")),
        gr.update(label=t.get("multi_cb", "")), 
        gr.update(value=t.get("clear_sel", "")), 
        gr.update(label=t.get("cols", "")),
        gr.update(value=t.get("hide_gal", "")), 
        gr.update(label=t.get("tab_view", "")), 
        gr.update(value=t.get("btn_prev", "")),
        gr.update(value=t.get("btn_next", "")), 
        gr.update(value=shortcuts_text), 
        gr.update(value=t.get("toggle_stat", "")),
        gr.update(value=t.get("save_cap", "")), 
        gr.update(label=t.get("tab_batch", "")), 
        gr.update(value=t.get("btn_undo", "")),
        gr.update(label=t.get("target_rep", "")), 
        gr.update(label=t.get("synonyms", "")), 
        gr.update(value=t.get("btn_rep_syn", "")),
        gr.update(label=t.get("rep_this", "")), 
        gr.update(label=t.get("rep_that", "")), 
        gr.update(label=t.get("use_regex", "")),
        gr.update(value=t.get("btn_apply", "")), 
        gr.update(label=t.get("add_text", "")), 
        gr.update(choices=t.get("add_pos_choices", [""]), value=t.get("add_pos_choices", [""])[0] if t.get("add_pos_choices") else ""),
        gr.update(value=t.get("btn_add", "")), 
        gr.update(value=t.get("btn_clean_com", "")), 
        gr.update(value=t.get("btn_clean_dup", "")),
        gr.update(label=t.get("df_preview", "")), 
        gr.update(label=t.get("tab_export", "")), 
        gr.update(value=t.get("exp_desc", "")),
        gr.update(value=t.get("exp_edit", "")), 
        gr.update(value=new_config, headers=t.get("exp_df_headers", [])), 
        gr.update(label=t.get("strat", ""), choices=t.get("strat_choices", ["", ""]), value=t.get("strat_choices", ["", ""])[1] if len(t.get("strat_choices", []))>1 else ""),
        gr.update(label=t.get("max_img", "")), 
        gr.update(label=t.get("dest_folder", ""), placeholder=t.get("dest_ph", "")),
        gr.update(value=t.get("btn_simul", "")), 
        gr.update(value=t.get("btn_exp", "")), 
        gr.update(value=t.get("res_simul", "")),
        gr.update(value=t.get("exp_gal", "")), 
        gr.update(label=t.get("tab_stats", "")), 
        gr.update(value=t.get("stat_edit", "")), 
        gr.update(value=new_stats, headers=t.get("stat_df_headers", [])), 
        gr.update(value=t.get("btn_top20", "")),
        gr.update(value=t.get("btn_orph", "")), 
        gr.update(label=t.get("txt_orph", "")),
        gr.update(label=lbl_pie), 
        gr.update(label=lbl_bar), 
        gr.update(label=lbl_exp)
    )

with gr.Blocks(title="Datasets Images EditSelect", css=css_code) as app:
    
    dataset_state = gr.State([])
    filtered_state = gr.State([])
    history_state = gr.State([])
    current_idx_state = gr.State(0)
    selected_indices_state = gr.State([]) 
    config_df_state = gr.State("{}") 
    stats_df_state = gr.State("{}")
    recipe_selected_row = gr.State(-1)
    
    dummy_selection = gr.Textbox(visible=False, elem_id="dummy_selection")
    
    # Boutons de synchro cachés via CSS UNIQUEMENT (Important pour Gradio 4)
    ui_hidden_sync_input = gr.Textbox(value="{}", elem_id="hidden_sync_input")
    ui_hidden_sync_btn = gr.Button(elem_id="hidden_sync_btn")
    ui_hidden_calc_btn = gr.Button(elem_id="hidden_calc_btn")
    ui_hidden_dnd_input = gr.Textbox(elem_id="hidden_dnd_input")
    ui_hidden_dnd_btn = gr.Button(elem_id="hidden_dnd_btn")
    
    t_init = UI_T.get("FR", {})

    with gr.Row():
        with gr.Column(scale=2):
            lang_radio = gr.Radio(["FR", "EN"], value="FR", label="Language / Langue")
            ui_title = gr.Markdown(t_init.get("title", ""))
            with gr.Row():
                dir_input = gr.Textbox(placeholder="C:\\mon\\dataset", show_label=False, scale=4)
                ui_browse_btn = gr.Button(t_init.get("browse", ""), scale=1)
            ui_load_btn = gr.Button(t_init.get("load", ""), variant="primary")
            ui_status_text = gr.Markdown(t_init.get("status_wait", ""))
            
        with gr.Column(scale=3):
            ui_recipe_global = gr.Markdown(t_init.get("recipe_global", ""))
            with gr.Row():
                ui_recipes_dropdown = gr.Dropdown(choices=list(load_recipes().keys()), label=t_init.get("recipes_dd", ""), scale=2)
                ui_recipe_name = gr.Textbox(label=t_init.get("recipe_name", ""), scale=1)
                ui_save_recipe_btn = gr.Button(t_init.get("save_recipe", ""), scale=1)
            ui_tracked_words = gr.Textbox(show_label=False, placeholder=t_init.get("tracked_ph", ""), lines=2, elem_id="tracked_words_input")

    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=0, elem_id="left_panel") as left_panel:
            ui_gallery_title = gr.Markdown(t_init.get("gallery_title", ""))
            ui_search_box = gr.Textbox(label=t_init.get("search", ""), placeholder=t_init.get("search_ph", ""))
            with gr.Group():
                ui_multi_select_cb = gr.Checkbox(label=t_init.get("multi_cb", ""), value=False, interactive=True, elem_id="multi_cb")
                ui_clear_sel_btn = gr.Button(t_init.get("clear_sel", ""), elem_id="clear_sel_btn")
                ui_selection_status = gr.Markdown("**...**")
            ui_gallery_cols = gr.Slider(minimum=1, maximum=6, step=1, value=2, label=t_init.get("cols", ""))
            gallery = gr.Gallery(label="Dataset", columns=2, rows=6, height=750, object_fit="contain", allow_preview=False, elem_id="main_gallery")
            
        with gr.Column(scale=1):
            ui_toggle_panel_btn = gr.Button(t_init.get("hide_gal", ""), elem_id="toggle_gallery_btn", variant="secondary", size="sm")
            
            with gr.Tabs():
                with gr.Tab(t_init.get("tab_view", "")) as ui_tab_view:
                    with gr.Row():
                        ui_btn_prev = gr.Button(t_init.get("btn_prev", ""), elem_id="prev_btn")
                        ui_btn_next = gr.Button(t_init.get("btn_next", ""), elem_id="next_btn")
                    ui_viewer_status = gr.Markdown("**...**")
                    with gr.Row():
                        current_img = gr.Image(interactive=False, type="filepath", height=350, elem_id="viewer_area")
                        with gr.Column(elem_id="viewer_area_text"):
                            highlight_preview = gr.HTML()
                            word_counter = gr.HTML("<div style='color:green;'>0</div>")
                            ui_viewer_shortcuts = gr.Markdown("🎹 **Actions :** `[←/→]` Naviguer | `[Ctrl+S]` Sauver caption | `[Alt+S]` Suivre/Retirer mot-clé (Stats)<br>🖱️ **Sélection :** `[Ctrl+Clic]` Multi-sélection | `[Maj+Clic]` Plage d'images | `[Ctrl+A]` Tout | `[Alt+C]` Vider")
                            ui_toggle_tag_btn = gr.Button(t_init.get("toggle_stat", ""), variant="secondary", elem_id="toggle_tag_btn")
                    current_caption = gr.Textbox(show_label=False, lines=4)
                    ui_save_single_btn = gr.Button(t_init.get("save_cap", ""), variant="primary", elem_id="save_single_btn")
                    ui_single_save_status = gr.Markdown()

                with gr.Tab(t_init.get("tab_batch", "")) as ui_tab_batch:
                    ui_btn_undo = gr.Button(t_init.get("btn_undo", ""), variant="stop")
                    ui_batch_status = gr.Markdown()
                    with gr.Row():
                        with gr.Group():
                            ui_target_rep = gr.Textbox(label=t_init.get("target_rep", ""))
                            ui_synonyms = gr.Textbox(label=t_init.get("synonyms", ""))
                            ui_btn_rep_syn = gr.Button(t_init.get("btn_rep_syn", ""))
                        with gr.Group():
                            ui_old_text = gr.Textbox(label=t_init.get("rep_this", ""))
                            ui_new_text = gr.Textbox(label=t_init.get("rep_that", ""))
                            ui_use_regex = gr.Checkbox(label=t_init.get("use_regex", ""))
                            ui_btn_apply = gr.Button(t_init.get("btn_apply", ""))
                    with gr.Row():
                        with gr.Group():
                            ui_add_text = gr.Textbox(label=t_init.get("add_text", ""))
                            ui_add_pos = gr.Radio(t_init.get("add_pos_choices", ["Début", "Fin"]), value="Début", show_label=False)
                            ui_btn_add = gr.Button(t_init.get("btn_add", ""))
                        with gr.Group():
                            ui_btn_clean_com = gr.Button(t_init.get("btn_clean_com", ""))
                            ui_btn_clean_dup = gr.Button(t_init.get("btn_clean_dup", ""))
                    ui_preview_table = gr.Dataframe(label=t_init.get("df_preview", ""), interactive=False)

                with gr.Tab(t_init.get("tab_export", "")) as ui_tab_export:
                    ui_exp_desc = gr.Markdown(t_init.get("exp_desc", ""))
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_exp_edit = gr.Markdown("### ⚙️ Éditeur de Recette\n*Sélectionnez une ligne et utilisez les outils ci-dessous pour une **édition ultra-rapide**, ou glissez-déposez dans le tableau.*")
                            
                            with gr.Row():
                                ui_btn_up = gr.Button("⬆️ Monter (Alt+Haut)", variant="secondary", size="sm", elem_id="btn_move_up")
                                ui_btn_down = gr.Button("⬇️ Descendre (Alt+Bas)", variant="secondary", size="sm", elem_id="btn_move_down")
                                ui_btn_del = gr.Button("🗑️ Supprimer", variant="stop", size="sm")
                                
                            gr.Markdown("#### ⚡ Saisie Rapide (Ligne sélectionnée)")
                            with gr.Row():
                                ui_quick_prio = gr.Dropdown(label="N° Priorité (Sélectionnez pour déplacer)", choices=[str(i) for i in range(1, 101)], allow_custom_value=True, scale=1)
                                ui_quick_target = gr.Number(label="Cible % (Appliquer instantanément)", scale=1)
                            
                            ui_export_config_df = gr.Dataframe(
                                headers=t_init.get("exp_df_headers", ["Priorité", "Mot-clé", "Cible %"]), 
                                interactive=True, type="pandas", row_count=("dynamic"), column_count=(3, "fixed")
                            )
                            
                            ui_strategy_radio = gr.Radio(t_init.get("strat_choices", ["", "Filtre Classique"]), value="Filtre Classique", label=t_init.get("strat", ""))
                            ui_max_img_input = gr.Number(label=t_init.get("max_img", ""), value=0, precision=0)
                            ui_export_dir = gr.Textbox(label=t_init.get("dest_folder", ""), placeholder=t_init.get("dest_ph", ""))
                            with gr.Row():
                                ui_btn_simul = gr.Button(t_init.get("btn_simul", ""), variant="secondary")
                                ui_btn_exp = gr.Button(t_init.get("btn_exp", ""), variant="primary")
                        with gr.Column(scale=1):
                            ui_res_simul = gr.Markdown(t_init.get("res_simul", ""))
                            ui_export_status = gr.Markdown()
                            export_pie = gr.Plot(label="Graphique (Export)")
                    ui_exp_gal = gr.Markdown(t_init.get("exp_gal", ""))
                    export_gallery = gr.Gallery(columns=8, rows=2, height=250, object_fit="contain", allow_preview=False)

                with gr.Tab(t_init.get("tab_stats", "")) as ui_tab_stats:
                    ui_stats_status = gr.Markdown()
                    with gr.Row():
                        with gr.Column(scale=1):
                            ui_stat_edit = gr.Markdown("### 📊 Données (Calcul Instantané)\n*Se met à jour dès que vous tapez une virgule `,` ou sortez de la case. Supprimez une ligne avec `Suppr`.*")
                            ui_stats_table = gr.Dataframe(headers=t_init.get("stat_df_headers", []), interactive=True, type="pandas", row_count=("dynamic"))
                            
                            gr.Markdown("---")
                            ui_btn_civitai = gr.Button("📋 Générer tableau format CivitAI/Markdown", variant="secondary")
                            ui_civitai_output = gr.Textbox(label="Format CivitAI (Sélectionnez et copiez le texte ci-dessous)", interactive=False, lines=5)
                            gr.Markdown("---")
                            
                            with gr.Row():
                                ui_btn_top20 = gr.Button(t_init.get("btn_top20", ""))
                                ui_btn_orph = gr.Button(t_init.get("btn_orph", ""))
                            ui_txt_orph = gr.Textbox(label=t_init.get("txt_orph", ""), lines=4)
                        with gr.Column(scale=2):
                            pie_chart = gr.Plot(label="Graphique (Répartition)")
                            bar_chart = gr.Plot(label="Graphique (Occurrences)")

# ==========================================
# LOGIQUE D'INTERFACE ET EVENEMENTS
# ==========================================

    lang_radio.change(
        fn=change_language,
        inputs=[lang_radio, ui_stats_table, ui_export_config_df],
        outputs=[
            ui_title, ui_browse_btn, ui_load_btn, ui_status_text, ui_recipe_global,
            ui_recipes_dropdown, ui_recipe_name, ui_save_recipe_btn, ui_tracked_words,
            ui_gallery_title, ui_search_box, ui_multi_select_cb, ui_clear_sel_btn,
            ui_gallery_cols, ui_toggle_panel_btn, ui_tab_view, ui_btn_prev, ui_btn_next,
            ui_viewer_shortcuts, ui_toggle_tag_btn, ui_save_single_btn,
            ui_tab_batch, ui_btn_undo, ui_target_rep, ui_synonyms, ui_btn_rep_syn,
            ui_old_text, ui_new_text, ui_use_regex, ui_btn_apply, ui_add_text,
            ui_add_pos, ui_btn_add, ui_btn_clean_com, ui_btn_clean_dup, ui_preview_table,
            ui_tab_export, ui_exp_desc, ui_exp_edit, ui_export_config_df, ui_strategy_radio,
            ui_max_img_input, ui_export_dir, ui_btn_simul, ui_btn_exp, ui_res_simul,
            ui_exp_gal, ui_tab_stats, ui_stat_edit, ui_stats_table,
            ui_btn_top20, ui_btn_orph, ui_txt_orph,
            pie_chart, bar_chart, export_pie
        ]
    )

    js_toggle = """
    function() {
        const panel = document.getElementById('left_panel');
        const btn = document.getElementById('toggle_gallery_btn');
        if (panel.classList.contains('collapsed')) {
            panel.classList.remove('collapsed');
            btn.innerText = "◀ Hide Gallery";
        } else {
            panel.classList.add('collapsed');
            btn.innerText = "▶ Show Gallery";
        }
        return [];
    }
    """
    ui_toggle_panel_btn.click(fn=None, js=js_toggle)
    ui_browse_btn.click(fn=browse_folder, inputs=[], outputs=[dir_input])
    ui_gallery_cols.change(fn=lambda x: gr.update(columns=x), inputs=[ui_gallery_cols], outputs=[gallery])

    ui_load_btn.click(fn=load_dataset, inputs=[dir_input, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_status_text, gallery, selected_indices_state, ui_selection_status, ui_hidden_sync_input])
    ui_search_box.change(fn=filter_gallery, inputs=[dataset_state, ui_search_box, lang_radio], outputs=[filtered_state, gallery, selected_indices_state, ui_selection_status, ui_hidden_sync_input])
    
    # SYNC UNIFIÉE
    ui_hidden_sync_btn.click(
        fn=handle_sync, 
        inputs=[ui_hidden_sync_input, dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], 
        outputs=[dataset_state, filtered_state, selected_indices_state, ui_selection_status, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status]
    )
    
    ui_btn_prev.click(fn=nav_prev, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], outputs=[dataset_state, filtered_state, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status])
    ui_btn_next.click(fn=nav_next, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, ui_tracked_words, lang_radio], outputs=[dataset_state, filtered_state, current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status])
    
    ui_clear_sel_btn.click(fn=clear_selection, inputs=[lang_radio], outputs=[selected_indices_state, ui_selection_status, ui_hidden_sync_input])
    
    js_get_sel = """function(tracker, dummy) {
        let sel = window.getSelection().toString().trim();
        if(!sel) {
            let ae = document.activeElement;
            if(ae && (ae.tagName === 'TEXTAREA' || ae.tagName === 'INPUT')) sel = ae.value.substring(ae.selectionStart, ae.selectionEnd).trim();
        }
        return [tracker, sel || ""];
    }"""
    
    ui_hidden_calc_btn.click(
        fn=analyze_dataset, 
        inputs=[dataset_state, ui_tracked_words, lang_radio], 
        outputs=[pie_chart, bar_chart, ui_stats_table, stats_df_state, ui_export_config_df, config_df_state, ui_stats_status]
    )
    
    ui_tracked_words.change(
        fn=update_viewer, 
        inputs=[filtered_state, current_idx_state, ui_tracked_words, lang_radio], 
        outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, ui_viewer_status]
    )
    
    ui_toggle_tag_btn.click(fn=toggle_tracked_word, inputs=[ui_tracked_words, dummy_selection], outputs=[ui_tracked_words], js=js_get_sel).success(
        fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }"
    )
    
    current_caption.change(fn=update_word_count, inputs=[current_caption, lang_radio], outputs=[word_counter])
    ui_save_single_btn.click(fn=save_single_caption, inputs=[dataset_state, filtered_state, current_idx_state, current_caption, lang_radio], outputs=[dataset_state, filtered_state, ui_single_save_status])

    # === INTERACTIONS DU TABLEAU RECETTE & MENU RAPIDE ===
    ui_export_config_df.select(fn=get_row_index, inputs=[config_df_state], outputs=[recipe_selected_row, ui_quick_prio, ui_quick_target])
    
    ui_quick_prio.change(fn=apply_quick_prio, inputs=[ui_quick_prio, recipe_selected_row, config_df_state], outputs=[ui_export_config_df, config_df_state, ui_tracked_words, recipe_selected_row])
    ui_quick_target.change(fn=apply_quick_target, inputs=[ui_quick_target, recipe_selected_row, config_df_state], outputs=[ui_export_config_df, config_df_state, ui_tracked_words])

    ui_btn_up.click(fn=df_move_up, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_btn_down.click(fn=df_move_down, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_btn_del.click(fn=df_delete_row, inputs=[ui_export_config_df, recipe_selected_row], outputs=[ui_export_config_df, recipe_selected_row, ui_tracked_words])
    ui_hidden_dnd_btn.click(fn=handle_drag_and_drop, inputs=[ui_hidden_dnd_input, ui_export_config_df], outputs=[ui_export_config_df, ui_tracked_words])
    
    ui_export_config_df.change(fn=handle_recipe_df_safe, inputs=[ui_export_config_df, config_df_state, ui_tracked_words], outputs=[ui_export_config_df, config_df_state, ui_tracked_words])

    ui_btn_top20.click(fn=auto_fill_top_tags, inputs=[dataset_state], outputs=[ui_tracked_words]).success(
        fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }"
    )
    ui_btn_orph.click(fn=find_orphans, inputs=[dataset_state, lang_radio], outputs=[ui_txt_orph])
    ui_btn_civitai.click(fn=generate_civitai_format, inputs=[ui_stats_table], outputs=[ui_civitai_output])
    
    ui_stats_table.change(fn=handle_stats_df_safe, inputs=[ui_stats_table, stats_df_state, ui_tracked_words], outputs=[ui_stats_table, stats_df_state, ui_tracked_words]).success(
        fn=None, js="function(){ setTimeout(()=>document.getElementById('hidden_calc_btn')?.click(), 100); }"
    )
    
    # Batch Editions
    js_confirm = "function() { if (!confirm('⚠️ Appliquer cette modification en masse ? / Apply this mass modification?')) throw new Error('Annulé.'); }"
    ui_btn_undo.click(fn=None, js="function(){ if(!confirm('⚠️ Annuler ?')) throw new Error('Annulé'); }").success(fn=undo_last_action, inputs=[dataset_state, history_state, lang_radio], outputs=[dataset_state, filtered_state, ui_batch_status])
    ui_btn_add.click(fn=None, js=js_confirm).success(fn=batch_add, inputs=[dataset_state, ui_add_text, ui_add_pos, selected_indices_state, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_apply.click(fn=None, js=js_confirm).success(fn=batch_replace, inputs=[dataset_state, ui_old_text, ui_new_text, ui_use_regex, selected_indices_state, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_clean_com.click(fn=None, js=js_confirm).success(fn=batch_clean_commas, inputs=[dataset_state, selected_indices_state, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_clean_dup.click(fn=None, js=js_confirm).success(fn=batch_remove_duplicates, inputs=[dataset_state, selected_indices_state, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])
    ui_btn_rep_syn.click(fn=None, js=js_confirm).success(fn=batch_synonyms, inputs=[dataset_state, ui_target_rep, ui_synonyms, selected_indices_state, lang_radio], outputs=[dataset_state, filtered_state, history_state, ui_batch_status, ui_preview_table])

    ui_btn_simul.click(
        fn=simulate_and_export, 
        inputs=[dataset_state, ui_export_dir, ui_export_config_df, gr.State(True), selected_indices_state, ui_strategy_radio, ui_max_img_input, lang_radio], 
        outputs=[ui_export_status, export_gallery, export_pie, bar_chart]
    )
    ui_btn_exp.click(
        fn=simulate_and_export, 
        inputs=[dataset_state, ui_export_dir, ui_export_config_df, gr.State(False), selected_indices_state, ui_strategy_radio, ui_max_img_input, lang_radio], 
        outputs=[ui_export_status, export_gallery, export_pie, bar_chart]
    )

    app.load(fn=lambda: None, inputs=None, outputs=None, js=custom_js)

if __name__ == "__main__":
    app.launch(inbrowser=True, server_name="127.0.0.1")