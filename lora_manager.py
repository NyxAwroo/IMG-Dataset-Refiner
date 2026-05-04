import gradio as gr
import os
import re
import shutil
import json
import copy
import plotly.express as px
import pandas as pd
from collections import Counter

# ==========================================
# CONFIGURATION ET VARIABLES GLOBALES
# ==========================================

RECIPES_FILE = "lora_recipes.json"

# Injection Javascript forte et CSS pour le redimensionnement
head_html = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 1. Thème Sombre Forcé
    document.body.classList.add('dark');
    
    // 2. Raccourcis Claviers "Forcés" (Utilisation de la phase de capture "true" pour court-circuiter Gradio)
    window.addEventListener('keydown', function(e) {
        const tag = e.target.tagName.toLowerCase();
        
        // Raccourci Alt + S : Autorisé partout, même en écrivant !
        if (e.altKey && e.key.toLowerCase() === 's') {
            e.preventDefault();
            e.stopPropagation();
            const btn = document.getElementById('toggle_tag_btn');
            if(btn) btn.click();
            return;
        }
        
        // Bloquer les flèches SEULEMENT si on est dans un champ texte
        if (tag === 'input' || tag === 'textarea') return;
        
        if (e.key === 'ArrowLeft') { 
            const btn = document.getElementById('prev_btn');
            if(btn) btn.click(); 
        }
        if (e.key === 'ArrowRight') { 
            const btn = document.getElementById('next_btn');
            if(btn) btn.click(); 
        }
    }, true); 

    // 3. Observer Magique pour la Surbrillance Orange (Regarde si Gradio a mis le ✅)
    const observer = new MutationObserver(() => {
        const galleryBtns = document.querySelectorAll('#main_gallery button');
        galleryBtns.forEach(btn => {
            const label = btn.querySelector('.caption-label');
            const img = btn.querySelector('img');
            
            if (label && label.innerText.includes('✅')) {
                // Style quand sélectionné
                btn.style.outline = '4px solid #ff8800';
                btn.style.outlineOffset = '-4px';
                btn.style.boxShadow = 'inset 0 0 20px rgba(255, 136, 0, 0.9)';
                btn.style.borderRadius = '8px';
                if (img) {
                    img.style.filter = 'sepia(0.8) hue-rotate(330deg) saturate(3)';
                    img.style.opacity = '0.8';
                }
            } else {
                // Style normal
                btn.style.outline = 'none';
                btn.style.boxShadow = 'none';
                if (img) {
                    img.style.filter = 'none';
                    img.style.opacity = '1';
                }
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

// Récupération de la sélection de texte (Outil Alt+S)
function getSelectedText(tracker, dummy) {
    let sel = window.getSelection().toString().trim();
    if (!sel) {
        let activeEl = document.activeElement;
        if (activeEl && (activeEl.tagName === 'TEXTAREA' || activeEl.tagName === 'INPUT')) {
            sel = activeEl.value.substring(activeEl.selectionStart, activeEl.selectionEnd).trim();
        }
    }
    if(!sel) return [tracker, ""];
    return [tracker, sel];
}

// Fonction de Pliage/Dépliage de la colonne gauche
function toggleGallery() {
    const panel = document.getElementById('left_panel');
    const btn = document.getElementById('toggle_gallery_btn');
    if (panel.classList.contains('collapsed')) {
        panel.classList.remove('collapsed');
        btn.innerText = "◀ Masquer la Galerie";
    } else {
        panel.classList.add('collapsed');
        btn.innerText = "▶ Afficher la Galerie";
    }
    return []; // Requis par Gradio
}

function confirmAction() {
    if (!confirm('⚠️ Appliquer cette modification ?')) throw new Error('Annulé.');
}
</script>

<style>
    /* 4. CSS pour le Redimensionnement et le Pliage (Slide vers la gauche) */
    #left_panel {
        resize: horizontal; /* La poignée magique ! */
        overflow-x: hidden;
        overflow-y: auto;
        width: 380px; /* Largeur de base */
        min-width: 250px;
        max-width: 70vw; /* Maximum 70% de l'écran */
        flex: none !important; /* Empêche Gradio d'annuler le resize */
        border-right: 2px solid #374151;
        padding-right: 15px;
        transition: min-width 0.3s ease, width 0.3s ease, padding 0.3s ease, opacity 0.3s ease;
    }
    
    #left_panel.collapsed {
        width: 0px !important;
        min-width: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        opacity: 0;
        pointer-events: none;
    }
    
    /* Couleur du tag natif de sélection */
    .caption-label { font-size: 14px !important; font-weight: bold !important; color: #4ade80 !important; }
</style>
"""

# ==========================================
# FONCTIONS DE GESTION DU DATASET
# ==========================================

def get_gallery_items(filtered_dataset, selected_ids):
    return [(item['img_path'], "✅ SÉLECTIONNÉE" if item['id'] in selected_ids else "") for item in filtered_dataset]

def browse_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        folder_path = filedialog.askdirectory(title="Sélectionnez le dossier")
        root.destroy()
        return folder_path if folder_path else ""
    except Exception as e: return ""

def load_dataset(directory):
    if not os.path.isdir(directory): return [], [], [], "❌ Dossier introuvable.", [], [], "Aucune sélection active."
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
            
    gal_items = get_gallery_items(dataset, [])
    return dataset, dataset, [], f"✅ {len(dataset)} images chargées.", gal_items, [], "Aucune sélection active."

def filter_gallery(dataset, search_text, selected_ids):
    if not dataset: return [], []
    if not search_text: 
        return dataset, get_gallery_items(dataset, selected_ids)
    filtered = [item for item in dataset if search_text.lower() in item['caption'].lower()]
    return filtered, get_gallery_items(filtered, selected_ids)

# ==========================================
# FONCTIONS DU VISUALISEUR
# ==========================================

def get_highlighted_html(caption, tracked_words_str):
    if not caption: return "<div style='padding:10px; background:var(--bg-color); border-radius:5px;'></div>"
    html_caption = caption
    if tracked_words_str:
        tracked_words = [w.split(':')[0].strip() for w in tracked_words_str.split(',') if w.strip()]
        for word in tracked_words:
            pattern = re.compile(r'(\b' + re.escape(word) + r'\b)', re.IGNORECASE)
            html_caption = pattern.sub(r'<mark style="background-color: #ffcc00; color: #000; font-weight: bold; padding: 2px 4px; border-radius: 4px; box-shadow: 0 0 5px rgba(255, 204, 0, 0.5);">\1</mark>', html_caption)
    return f"<div style='padding:15px; border:1px solid #555; background-color: #222; border-radius:8px; line-height:1.6; font-size:1.1em;'>{html_caption}</div>"

def update_word_count(text):
    if not text: return "0 mots"
    words = len(text.split())
    tokens = int(words * 1.3)
    color = "#ff4444" if tokens > 225 else "#44ff44"
    warning = "<br>⚠️ <i>Risque de troncature (CLIP > 225)</i>" if tokens > 225 else ""
    return f"<div style='color:{color}; font-weight:bold;'>{words} mots (~{tokens} tokens){warning}</div>"

def update_viewer(filtered_dataset, idx, tracked_words):
    if not filtered_dataset or idx < 0 or idx >= len(filtered_dataset): return None, "", "", "0 mots", 0, "Aucune sélection."
    item = filtered_dataset[idx]
    return item['img_path'], get_highlighted_html(item['caption'], tracked_words), item['caption'], update_word_count(item['caption']), idx, f"Image vue : {item['img_name']}"

def gallery_click(evt: gr.SelectData, filtered_dataset, selected_indices, multi_mode, tracked_words):
    idx = evt.index
    item = filtered_dataset[idx]
    real_id = item['id']
    if multi_mode:
        if real_id in selected_indices: selected_indices.remove(real_id)
        else: selected_indices.append(real_id)
    else: selected_indices = [real_id]
    
    sel_text = f"✅ **{len(selected_indices)}** image(s) sélectionnée(s)." if selected_indices else "Aucune sélection (Le Batch impactera tout)."
    gal_items = get_gallery_items(filtered_dataset, selected_indices)
    
    return item['img_path'], get_highlighted_html(item['caption'], tracked_words), item['caption'], update_word_count(item['caption']), idx, f"Image vue : {item['img_name']}", selected_indices, sel_text, gal_items

def nav_prev(filtered_dataset, idx, tracked_words):
    if not filtered_dataset: return None, "", "", "0 mots", 0, ""
    idx = (idx - 1) % len(filtered_dataset)
    return update_viewer(filtered_dataset, idx, tracked_words)

def nav_next(filtered_dataset, idx, tracked_words):
    if not filtered_dataset: return None, "", "", "0 mots", 0, ""
    idx = (idx + 1) % len(filtered_dataset)
    return update_viewer(filtered_dataset, idx, tracked_words)

def save_single_caption(dataset, filtered_dataset, idx, new_caption):
    if not filtered_dataset or idx < 0 or idx >= len(filtered_dataset): return dataset, filtered_dataset, "❌ Erreur."
    item_filtered = filtered_dataset[idx]
    real_id = item_filtered['id']
    if os.path.exists(item_filtered['txt_path']): shutil.copy2(item_filtered['txt_path'], item_filtered['txt_path'] + ".bak")
    item_filtered['caption'] = new_caption
    dataset[real_id]['caption'] = new_caption
    with open(item_filtered['txt_path'], 'w', encoding='utf-8') as f: f.write(new_caption)
    return dataset, filtered_dataset, f"✅ Sauvegardé : {item_filtered['img_name']}"

def clear_selection(filtered_dataset): 
    return [], "Aucune sélection (Le Batch impactera **TOUT** le dataset).", get_gallery_items(filtered_dataset, [])

# ==========================================
# STATS, DF & TOGGLE
# ==========================================

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
        mot = str(row.get("Mot-clé", "")).strip()
        if not mot or mot.lower() == "aucun": continue
        cible = str(row.get("Cible %", "")).replace('%', '').strip()
        if cible and cible != "-" and cible != "0.0" and cible != "0": words.append(f"{mot}:{cible}")
        else: words.append(mot)
    return ", ".join(words)

def analyze_dataset(dataset, tracked_words_str):
    if not dataset: return None, None, pd.DataFrame(), pd.DataFrame(), "Aucun dataset."
    if not tracked_words_str: return None, None, pd.DataFrame([{"Mot-clé": "", "Cible %": ""}]), pd.DataFrame([{"Priorité": 1, "Mot-clé": "", "Cible %": 0}]), "Entrez des mots-clés."
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
        row = {"Mot-clé": word, "Compte": count, "Actuel %": f"{pct:.1f}%"}
        if word in targets:
            row["Cible %"] = f"{targets[word]}%"
            row["Écart"] = f"{'+' if (pct - targets[word])>0 else ''}{pct - targets[word]:.1f}%"
        else:
            row["Cible %"] = "-"; row["Écart"] = "-"
        df_stats.append(row)
        
    df = pd.DataFrame(df_stats).sort_values(by="Compte", ascending=False)
    
    df_config = []
    for i, word in enumerate(stats.keys()):
        cible = targets.get(word, 0)
        df_config.append({"Priorité": i+1, "Mot-clé": word, "Cible %": cible})
    df_conf = pd.DataFrame(df_config)

    pie_data = {k: v for k, v in stats.items() if v > 0}
    if not pie_data:
        fig_pie = px.pie(names=["Aucun"], values=[1], title="Aucun tag trouvé")
        fig_bar = px.bar(x=["Aucun"], y=[0], title="Aucun tag trouvé")
    else:
        fig_pie = px.pie(names=list(pie_data.keys()), values=list(pie_data.values()), title="Répartition Globale")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_bar = px.bar(x=list(pie_data.keys()), y=list(pie_data.values()), title="Occurrences par Mot-clé")
    
    return fig_pie, fig_bar, df, df_conf, "✅ Statistiques à jour."

def find_orphans(dataset):
    if not dataset: return "Aucun dataset."
    all_words = []
    for item in dataset:
        tags = [t.strip().lower() for t in item['caption'].split(',')]
        all_words.extend(tags)
    counts = Counter(all_words)
    orphans = [tag for tag, count in counts.items() if count == 1 and len(tag) > 2]
    if not orphans: return "✅ Aucun tag orphelin trouvé."
    return "Tags uniques (potentiellement des fautes) :\n" + ", ".join(sorted(orphans))

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
    return {"Défaut": "1girl, solo, looking at viewer"}

def save_recipe(name, words):
    if not name: return gr.update(), "Nom vide."
    recipes = load_recipes()
    recipes[name] = words
    with open(RECIPES_FILE, 'w') as f: json.dump(recipes, f)
    return gr.update(choices=list(recipes.keys()), value=name), "✅ Recette sauvegardée."

def apply_recipe(name): return load_recipes().get(name, "")

# ==========================================
# FONCTIONS BATCH
# ==========================================
def save_all_captions(dataset):
    for item in dataset:
        with open(item['txt_path'], 'w', encoding='utf-8') as f: f.write(item['caption'])

def undo_last_action(dataset, history):
    if not history: return dataset, dataset, "Rien à annuler."
    dataset = copy.deepcopy(history)
    save_all_captions(dataset)
    return dataset, dataset, "✅ Dernière action annulée."

def create_preview_df(old_dataset, new_dataset):
    changes = []
    for old, new in zip(old_dataset, new_dataset):
        if old['caption'] != new['caption']:
            changes.append({"Fichier": old['img_name'], "Avant": old['caption'], "Après": new['caption']})
            if len(changes) >= 10: break
    if not changes: return pd.DataFrame([{"Message": "Aucun changement."}])
    return pd.DataFrame(changes)

def batch_add(dataset, text, pos, selected_ids):
    if not text: return dataset, dataset, dataset, "Texte vide.", pd.DataFrame()
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        if pos == "Début":
            sep = ", " if item['caption'] else ""
            item['caption'] = text + sep + item['caption']
        else:
            sep = ", " if item['caption'] and not item['caption'].endswith(", ") else ""
            item['caption'] = item['caption'] + sep + text
        count += 1
    save_all_captions(dataset)
    return dataset, dataset, history, f"✅ Ajouté à {count} fichiers.", create_preview_df(history, dataset)

def batch_replace(dataset, old_text, new_text, use_regex, selected_ids):
    history = copy.deepcopy(dataset)
    count = 0
    for item in dataset:
        if selected_ids and item['id'] not in selected_ids: continue
        if use_regex:
            try:
                new_cap = re.sub(old_text, new_text, item['caption'])
                if new_cap != item['caption']: item['caption'] = new_cap; count += 1
            except: return dataset, dataset, history, "❌ Erreur Regex.", pd.DataFrame()
        else:
            if old_text in item['caption']: item['caption'] = item['caption'].replace(old_text, new_text); count += 1
    save_all_captions(dataset)
    return dataset, dataset, history, f"✅ Remplacement dans {count} fichiers.", create_preview_df(history, dataset)

def batch_clean_commas(dataset, selected_ids):
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
    return dataset, dataset, history, f"✅ Nettoyé dans {count} fichiers.", create_preview_df(history, dataset)

def batch_remove_duplicates(dataset, selected_ids):
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
    return dataset, dataset, history, f"✅ Doublons retirés dans {count} fichiers.", create_preview_df(history, dataset)

def batch_synonyms(dataset, target_tag, synonyms_str, selected_ids):
    if not target_tag: return dataset, dataset, dataset, "Tag cible vide.", pd.DataFrame()
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
    return dataset, dataset, history, f"✅ Remplacement de doublons par des synonymes dans {count} fichiers.", create_preview_df(history, dataset)

# ==========================================
# EXPORT INTELLIGENT
# ==========================================

def simulate_and_export(dataset, export_dir, config_df, is_simulation, selected_ids, strategy, max_images, filtered_dataset):
    if not dataset: 
        return "❌ Aucun dataset chargé.", [], None, None, selected_ids, get_gallery_items(filtered_dataset, selected_ids)
        
    if config_df is None or config_df.empty: 
        config_df = pd.DataFrame([{"Priorité": 1, "Mot-clé": "", "Cible %": 0}])
    else:
        config_df["Priorité"] = pd.to_numeric(config_df["Priorité"], errors='coerce').fillna(999).astype(int)
        
    config_df = config_df.sort_values(by="Priorité")
    
    targets = {}; ordered_tags = []
    for _, row in config_df.iterrows():
        tag = str(row.get("Mot-clé", "")).strip().lower()
        if tag and tag != "aucun":
            try: c = float(str(row.get("Cible %", 0)).replace('%', '').strip())
            except: c = 0.0
            targets[tag] = c
            ordered_tags.append(tag)

    base_pool = [item for item in dataset if not selected_ids or item['id'] in selected_ids]
    to_export = []
    limit = int(max_images)

    if strategy == "Filtre Classique (Contient au moins un tag)":
        for item in base_pool:
            if not ordered_tags or any(re.search(r'\b' + re.escape(t) + r'\b', item['caption'].lower()) for t in ordered_tags):
                to_export.append(item)
        if limit > 0: to_export = to_export[:limit]

    elif strategy == "Priorité (Ordre du tableau)":
        seen = set()
        lim = limit if limit > 0 else len(base_pool)
        for tag in ordered_tags:
            for item in base_pool:
                if len(to_export) >= lim: break
                if item['id'] not in seen and re.search(r'\b' + re.escape(tag) + r'\b', item['caption'].lower()):
                    to_export.append(item); seen.add(item['id'])
            if len(to_export) >= lim: break

    elif strategy == "Équilibrage Auto (Pourcentages)":
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
        p_fig = px.pie(names=["Aucun"], values=[1], title="Simulé : Aucun tag")
        b_fig = px.bar(x=["Aucun"], y=[0], title="Simulé : Aucun tag")
    else:
        p_fig = px.pie(names=list(pie_data.keys()), values=list(pie_data.values()), title="Répartition du Futur Export")
        p_fig.update_traces(textposition='inside', textinfo='percent+label')
        b_fig = px.bar(x=list(pie_data.keys()), y=list(pie_data.values()), title="Occurrences (Export)")

    gallery_preview = [item['img_path'] for item in to_export]
    new_selected_ids = [item['id'] for item in to_export]
    
    # Générer la nouvelle vue de la galerie native
    gal_items = get_gallery_items(filtered_dataset, new_selected_ids)
    
    if is_simulation:
        rep = f"🔍 **SIMULATION : {len(to_export)} images sélectionnées.** Elles sont maintenant en surbrillance orange dans la galerie !"
        return rep, gallery_preview, p_fig, b_fig, new_selected_ids, gal_items
    else:
        if not export_dir or str(export_dir).strip() == "":
            export_dir = os.path.join(os.getcwd(), "output", "dataset_final")
            
        if not os.path.exists(export_dir): 
            os.makedirs(export_dir)
            
        for item in to_export:
            shutil.copy2(item['img_path'], os.path.join(export_dir, item['img_name']))
            shutil.copy2(item['txt_path'], os.path.join(export_dir, os.path.basename(item['txt_path'])))
            
        return f"✅ **EXPORT RÉUSSI !** {len(to_export)} fichiers copiés dans : \n`{export_dir}`", gallery_preview, p_fig, b_fig, new_selected_ids, gal_items

# ==========================================
# INTERFACE GRADIO
# ==========================================

with gr.Blocks(title="Datasets Images EditSelect", head=head_html) as app:
    dataset_state = gr.State([])
    filtered_state = gr.State([])
    history_state = gr.State([])
    current_idx_state = gr.State(0)
    selected_indices_state = gr.State([]) 
    dummy_selection = gr.Textbox(visible=False, elem_id="dummy_selection")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("# 📊 Datasets Images EditSelect\n*Gère, visualise, et équilibre ton dataset.*")
            with gr.Row():
                dir_input = gr.Textbox(placeholder="C:\\mon\\dataset", show_label=False, scale=4)
                browse_btn = gr.Button("📂 Parcourir", scale=1)
            load_btn = gr.Button("🚀 Charger le Dataset", variant="primary")
            status_text = gr.Markdown("*En attente de chargement...*")
            
        with gr.Column(scale=3):
            gr.Markdown("**Recette Globale (Synchronisée)**")
            tracked_words = gr.Textbox(show_label=False, placeholder="ex: p0se-s1:50, man:20", lines=2)

    gr.Markdown("---")
    
    with gr.Row():
        
        # --- COLONNE DE GAUCHE : ID 'left_panel' POUR CSS (Redimensionnement / Pliage) ---
        with gr.Column(scale=0, elem_id="left_panel") as left_panel:
            gr.Markdown("### 🖼️ Galerie & Sélection")
            search_box = gr.Textbox(label="🔍 Filtrer les images", placeholder="Tapez un mot...")
            with gr.Group():
                multi_select_cb = gr.Checkbox(label="✅ Mode Sélection Multiple", value=False)
                clear_sel_btn = gr.Button("🧹 Effacer la sélection")
                selection_status = gr.Markdown("**Aucune sélection (Les actions impacteront tout).**")
            gallery_cols = gr.Slider(minimum=1, maximum=6, step=1, value=2, label="Colonnes")
            gallery = gr.Gallery(label="Dataset", columns=2, rows=6, height=750, object_fit="contain", allow_preview=False, elem_id="main_gallery")
            
        # --- COLONNE DE DROITE : S'ÉTEND GRÂCE À SCALE=1 ---
        with gr.Column(scale=1):
            
            # BOUTON MAGIQUE POUR PLIER/DÉPLIER LA COLONNE GAUCHE
            toggle_panel_btn = gr.Button("◀ Masquer la Galerie", elem_id="toggle_gallery_btn", variant="secondary", size="sm")
            
            with gr.Tabs():
                
                with gr.Tab("👁️ Visualiseur & Édition"):
                    with gr.Row():
                        prev_btn = gr.Button("⬅️ Précédent", elem_id="prev_btn")
                        next_btn = gr.Button("➡️ Suivant", elem_id="next_btn")
                    viewer_status = gr.Markdown("**Aucune image sélectionnée.**")
                    with gr.Row():
                        current_img = gr.Image(interactive=False, type="filepath", height=350, elem_id="viewer_area")
                        with gr.Column(elem_id="viewer_area_text"):
                            highlight_preview = gr.HTML()
                            word_counter = gr.HTML("<div style='color:green;'>0 mots</div>")
                            gr.Markdown("🎹 `[Flèches]` = Naviguer | `[Alt+S]` = Toggle Stat")
                            toggle_tag_btn = gr.Button("🪄 Suivre/Retirer sélection (Stats)", variant="secondary", elem_id="toggle_tag_btn")
                    current_caption = gr.Textbox(show_label=False, lines=4)
                    save_single_btn = gr.Button("💾 Sauvegarder la Caption", variant="primary", elem_id="save_single_btn")
                    single_save_status = gr.Markdown()

                with gr.Tab("⚡ Édition en Batch"):
                    undo_btn = gr.Button("↩️ ANNULER LA DERNIÈRE ACTION", variant="stop")
                    batch_status = gr.Markdown()
                    with gr.Row():
                        with gr.Group():
                            target_tag = gr.Textbox(label="Tag répétitif (ex: 1girl)")
                            synonyms_input = gr.Textbox(label="Synonymes (séparés par des virgules)")
                            apply_syn_btn = gr.Button("Remplacer doublons par synonymes")
                        with gr.Group():
                            old_text = gr.Textbox(label="Remplacer ceci...")
                            new_text = gr.Textbox(label="... Par cela")
                            use_regex = gr.Checkbox(label="Regex")
                            replace_btn = gr.Button("Appliquer")
                    with gr.Row():
                        with gr.Group():
                            add_text = gr.Textbox(label="Texte à Ajouter")
                            add_pos = gr.Radio(["Début", "Fin"], value="Début", show_label=False)
                            add_btn = gr.Button("Ajouter")
                        with gr.Group():
                            clean_commas_btn = gr.Button("Nettoyer virgules et espaces")
                            clean_dup_btn = gr.Button("Retirer tags identiques purs")
                    preview_table = gr.Dataframe(label="Aperçu des changements", interactive=False)

                with gr.Tab("📁 Assistant d'Export & Recette"):
                    gr.Markdown("Configurez ici votre recette (priorité et %). Cliquez sur Simuler pour pré-sélectionner les images !")
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### ⚙️ Éditeur de Recette\n*Éditez les cases. Surveillez l'icône 🗑️ à gauche pour supprimer une ligne.*")
                            export_config_df = gr.Dataframe(headers=["Priorité", "Mot-clé", "Cible %"], interactive=True, type="pandas")
                            
                            strategy_radio = gr.Radio(["Filtre Classique (Contient au moins un tag)", "Équilibrage Auto (Pourcentages)", "Priorité (Ordre du tableau)"], value="Équilibrage Auto (Pourcentages)", label="🤖 Stratégie")
                            max_img_input = gr.Number(label="Limite d'images (0 = Infini)", value=0, precision=0)
                            export_dir = gr.Textbox(label="Dossier de Destination", placeholder="Laisser vide pour créer : ./output/dataset_final")
                            
                            with gr.Row():
                                simul_btn = gr.Button("🔍 Simuler (Met à jour la sélection)", variant="secondary")
                                export_btn = gr.Button("🚀 Exporter le Dataset", variant="primary")
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 📊 Résultat de la Simulation")
                            export_status = gr.Markdown("*En attente d'une simulation...*")
                            export_pie = gr.Plot()
                    
                    gr.Markdown("### 🖼️ Miniature du Dataset Final")
                    export_gallery = gr.Gallery(columns=8, rows=2, height=250, object_fit="contain", allow_preview=False)

                with gr.Tab("📈 Statistiques Générales"):
                    refresh_stats_btn = gr.Button("🔄 Calculer sur TOUT le dataset", variant="primary")
                    stats_status = gr.Markdown()
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("*Tableau éditable. Survolez l'index à gauche pour supprimer (🗑️).*")
                            stats_table = gr.Dataframe(headers=["Mot-clé", "Compte", "Actuel %", "Cible %", "Écart"], interactive=True, type="pandas")
                            auto_fill_btn = gr.Button("🪄 Remplir avec le Top 20")
                            find_orphans_btn = gr.Button("🕵️ Tags Orphelins")
                            orphans_text = gr.Textbox(label="Orphelins", lines=4)
                        with gr.Column(scale=2):
                            pie_chart = gr.Plot()
                            bar_chart = gr.Plot()

    # ==========================================
    # LOGIQUE D'INTERFACE ET EVENEMENTS
    # ==========================================

    # Événement Javascript pur pour plier/déplier la galerie !
    toggle_panel_btn.click(fn=None, js="toggleGallery")

    browse_btn.click(fn=browse_folder, inputs=[], outputs=[dir_input])
    gallery_cols.change(fn=lambda x: gr.update(columns=x), inputs=[gallery_cols], outputs=[gallery])

    load_btn.click(fn=load_dataset, inputs=[dir_input], outputs=[dataset_state, filtered_state, history_state, status_text, gallery, selected_indices_state, selection_status])
    
    search_box.change(fn=filter_gallery, inputs=[dataset_state, search_box, selected_indices_state], outputs=[filtered_state, gallery])
    
    gallery.select(fn=gallery_click, inputs=[filtered_state, selected_indices_state, multi_select_cb, tracked_words], outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, viewer_status, selected_indices_state, selection_status, gallery])
    
    prev_btn.click(fn=nav_prev, inputs=[filtered_state, current_idx_state, tracked_words], outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, viewer_status])
    next_btn.click(fn=nav_next, inputs=[filtered_state, current_idx_state, tracked_words], outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, viewer_status])
    
    clear_sel_btn.click(fn=clear_selection, inputs=[filtered_state], outputs=[selected_indices_state, selection_status, gallery])
    multi_select_cb.change(fn=clear_selection, inputs=[filtered_state], outputs=[selected_indices_state, selection_status, gallery])
    
    toggle_tag_btn.click(fn=toggle_tracked_word, inputs=[tracked_words, dummy_selection], outputs=[tracked_words], js="getSelectedText")
    tracked_words.change(fn=update_viewer, inputs=[filtered_state, current_idx_state, tracked_words], outputs=[current_img, highlight_preview, current_caption, word_counter, current_idx_state, viewer_status])
    
    current_caption.change(fn=update_word_count, inputs=[current_caption], outputs=[word_counter])
    save_single_btn.click(fn=save_single_caption, inputs=[dataset_state, filtered_state, current_idx_state, current_caption], outputs=[dataset_state, filtered_state, single_save_status])

    refresh_stats_btn.click(fn=analyze_dataset, inputs=[dataset_state, tracked_words], outputs=[pie_chart, bar_chart, stats_table, export_config_df, stats_status])
    auto_fill_btn.click(fn=auto_fill_top_tags, inputs=[dataset_state], outputs=[tracked_words])
    find_orphans_btn.click(fn=find_orphans, inputs=[dataset_state], outputs=[orphans_text])
    
    stats_table.change(fn=df_to_tracked_words, inputs=[stats_table], outputs=[tracked_words])
    export_config_df.change(fn=df_to_tracked_words, inputs=[export_config_df], outputs=[tracked_words])
    
    undo_btn.click(fn=None, js="confirmAction").success(fn=undo_last_action, inputs=[dataset_state, history_state], outputs=[dataset_state, filtered_state, batch_status])
    add_btn.click(fn=None, js="confirmAction").success(fn=batch_add, inputs=[dataset_state, add_text, add_pos, selected_indices_state], outputs=[dataset_state, filtered_state, history_state, batch_status, preview_table])
    replace_btn.click(fn=None, js="confirmAction").success(fn=batch_replace, inputs=[dataset_state, old_text, new_text, use_regex, selected_indices_state], outputs=[dataset_state, filtered_state, history_state, batch_status, preview_table])
    clean_commas_btn.click(fn=None, js="confirmAction").success(fn=batch_clean_commas, inputs=[dataset_state, selected_indices_state], outputs=[dataset_state, filtered_state, history_state, batch_status, preview_table])
    clean_dup_btn.click(fn=None, js="confirmAction").success(fn=batch_remove_duplicates, inputs=[dataset_state, selected_indices_state], outputs=[dataset_state, filtered_state, history_state, batch_status, preview_table])
    apply_syn_btn.click(fn=None, js="confirmAction").success(fn=batch_synonyms, inputs=[dataset_state, target_tag, synonyms_input, selected_indices_state], outputs=[dataset_state, filtered_state, history_state, batch_status, preview_table])

    # --- CONNEXION EXPORT INTELLIGENT ---
    simul_btn.click(
        fn=simulate_and_export, 
        inputs=[dataset_state, export_dir, export_config_df, gr.State(True), selected_indices_state, strategy_radio, max_img_input, filtered_state], 
        outputs=[export_status, export_gallery, export_pie, bar_chart, selected_indices_state, gallery]
    )
    
    export_btn.click(
        fn=simulate_and_export, 
        inputs=[dataset_state, export_dir, export_config_df, gr.State(False), selected_indices_state, strategy_radio, max_img_input, filtered_state], 
        outputs=[export_status, export_gallery, export_pie, bar_chart, selected_indices_state, gallery]
    )

if __name__ == "__main__":
    app.launch(inbrowser=True, server_name="127.0.0.1")