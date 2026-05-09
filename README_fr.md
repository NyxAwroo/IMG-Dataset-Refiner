# **📊 IMG Dataset Refiner (v4.0 Pro)**

**L'outil ultime de gestion, d'équilibrage, de pré-traitement, d'édition par lots et d'assistance IA (VLM/LLM) pour la préparation d'entraînements de modèles (LoRA, SDXL, Flux)** [Installation](#bookmark=id.15wxvz2309y4) • [Nouveautés v4.0](#bookmark=id.h4oh5540alo4) • [Fonctionnalités](#bookmark=id.tm4b60nt4exp) • [Workflow](#bookmark=id.pleyekjljsnv)

## **🎯 À propos**

**IMG Dataset Refiner** est une suite logicielle "desktop-like" conçue pour les créateurs de modèles IA. Propulsé par **Gradio** avec des injections JavaScript natives et CSS sur mesure pour des performances optimales, cet outil permet de **visualiser, éditer massivement, pré-traiter, nettoyer, analyser par l'IA et exporter** vos datasets d'images avec une précision chirurgicale.

## **🚀 Nouveautés de la v4.0 Pro**

Cette version apporte une fluidité sans précédent dans l'édition manuelle de votre dataset :

* **📚 Bibliothèque de mots (Mass Batch Custom) :** Un nouveau module interactif unique pour garder sous la main une liste de tags. Cochez-les pour les Ajouter, Retirer ou Remplacer massivement sur une sélection d'images d'un seul clic.  
* **🌍 Assistant de Traduction Live :** Traduisez vos captions en temps réel, injectez des mots traduits à la volée, ou convertissez un fichier .txt entier en anglais instantanément grâce à l'intégration de deep-translator. L'aperçu s'affiche en direct sous votre zone de frappe.  
* **⌨️ Productivité Absolue :** Naviguez d'image en image avec PageUp/PageDown sans même avoir à cliquer en dehors de la zone de texte. Sauvegardez à la volée avec Ctrl+S.  
* **🗂️ Tri Dynamique et UI Repensée :** Triez vos images de A à Z ou Z à A, profitez d'une interface débarrassée des menus distrayants, et basculez toute l'application entre Français et Anglais d'un simple clic.

## **⚙️ Fonctionnalités Clés**

### **🤖 Capacités IA (Assistant Local via API)**

* **Intégration Ollama / LM Studio :** Support natif pour exécuter des modèles de langage (LLM) et de vision (VLM) directement sur le dataset via API locale.  
* **Auto-Taggage / Super OCR (VLM) :** Génération complète de captions ou extraction précise de textes incrustés dans l'image.  
* **Reality Check & Chasseur d'Hallucinations (VLM) :** L'IA compare le texte à l'image et supprime automatiquement les tags qui décrivent des éléments invisibles.  
* **Concept Isolator (VLM) :** L'IA décrit l'environnement et ignore le sujet central, idéal pour préparer les données d'entraînement de LoRAs de personnages.  
* **Traducteur Visuel (Booru ↔ Naturel) :** Conversion intelligente des listes de tags en phrases complètes fluides (optimisé pour Flux et SD3).

### **🖼️ Traque aux Doublons & Pré-traitement**

* **Doublons (ImageHash) :** Scanner visuel paramétrable détectant les images similaires (clones exacts ou recadrages) avec interface de suppression rapide A/B.  
* **Smart Face Crop (OpenCV) :** Recadrage automatique centré sur les visages détectés pour optimiser les portraits.  
* **Redimensionnement de Masse :** Downscaling haute qualité (Lanczos) vers 512, 768, 1024 ou 1536px, avec gestion automatique des PNG transparents (fond blanc).  
* **Batch Renaming :** Renommage propre et incrémental (prefix\_0001.jpg) de toutes les images et de leurs .txt associés en un clic.

### **🧬 Analytiques Avancées & Qualité**

* **Matrice de Co-occurrence (Heatmap) :** Graphique interactif Plotly analysant les liens entre vos 20 tags principaux pour détecter le "Concept Bleeding" (fuite de concepts).  
* **Résolution Bucketing :** Graphique en nuage de points pour visualiser la répartition des résolutions de vos images brutes.  
* **Chasseur de Contradictions :** Détection automatique d'aberrations logiques dans vos captions (ex: "day" \+ "night" sur la même image).  
* **Tags Orphelins :** Détection des mots-clés uniques (souvent révélateurs de fautes de frappe).

### **📁 Export Stratégique**

* **Équilibrage Auto (Pourcentages) :** Fixez des cibles d'apparition pour vos concepts (ex: 50% homme, 50% femme) et l'algorithme "Greedy" piochera les images parfaites pour atteindre ce ratio.  
* **Génération de Tableaux CivitAI :** Exportez vos statistiques d'un clic pour les coller directement sur votre page modèle.

## **🔄 Workflow Recommandé**

1️⃣ **Pré-traitement (Onglet 🖼️)** └─ Nettoyez les doublons visuels, renommez vos fichiers proprement et redimensionnez vos images si nécessaire.  
2️⃣ **Auto-Captioning IA (Onglet 🤖)** └─ Laissez votre modèle Vision local (ex: LLaVA ou Qwen) générer une première base de tags solides sur l'ensemble de votre sélection.  
3️⃣ **Édition Rapide & Traduction (Onglet 👁️)** └─ Naviguez rapidement au clavier (PageUp/PageDown). Utilisez l'aperçu de **Traduction Live** pour écrire vos idées en français et les insérer instantanément en anglais.  
4️⃣ **Édition de Masse (Onglet ⚡ & Bibliothèque 📚)** └─ Remplissez votre Bibliothèque Custom de mots-clés. Sélectionnez plusieurs images (Ctrl+Clic), puis ajoutez ou retirez ces concepts en un clic pour standardiser votre dataset.  
5️⃣ **Audits & Export Stratégique (Onglets 📈 & 📁)** └─ Vérifiez qu'il n'y a pas de biais grâce à la *Heatmap* de co-occurrence. Entrez vos cibles %, simulez l'équilibre, et exportez un dataset parfait et prêt à l'entraînement \!

## **⚙️ Installation**

1. Clonez ce dépôt ou téléchargez les fichiers.  
2. Installez les dépendances requises via votre terminal :  
   pip install gradio pandas plotly imagehash opencv-python deep-translator

3. Lancez le script :  
   python lora\_manager.py

## **📦 Structure du Projet**

IMG-Dataset-Refiner/      
├── lora\_manager.py          \# Point d'entrée principal (Le code métier et UI)      
├── Changelog.md             \# Historique des mises à jour (v4.0 Pro)      
├── en.json                  \# Dictionnaire de langue Anglaise      
├── fr.json                  \# Dictionnaire de langue Française      
├── lora\_recipes.json        \# Sauvegardes de vos configurations d'export    
├── ai\_recipes.json          \# Sauvegardes de vos prompts Custom IA    
├── README\_fr.md             \# Cette documentation      
└── requirements.txt         \# Dépendances Python

## **🎓 Cas d'Usage**

✅ Préparation de datasets exigeants pour **LoRA fine-tuning** (SD 1.5, SDXL, Flux)  
✅ **Auto-captioning local** respectueux de la vie privée (100% hors-ligne)  
✅ Équilibrage mathématique de datasets **multi-concepts** ✅ Annotation de masse ultra-rapide via la **Bibliothèque Custom** ✅ Identification et résolution de problèmes d'**overfitting** via audits visuels

## **📄 Licence**

Libre d'utilisation et de modification pour vos workflows personnels et professionnels d'IA.

## **🤝 Contribution**

Les contributions sont bienvenues \! N'hésitez pas à :

* Signaler des bugs via les Issues  
* Proposer des améliorations  
* Soumettre des Pull Requests

**Forgé avec ❤️ pour la communauté de l'IA Générative.**