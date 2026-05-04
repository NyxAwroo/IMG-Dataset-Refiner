# **📊 Datasets Images EditSelect (v2.0)**

**Un gestionnaire et équilibreur de datasets local avancé pour la préparation d'entraînements de modèles IA**  
[Installation](#bookmark=id.f3jo4a1xx81u) • [Nouveautés v2](#bookmark=id.mdvcmfrrldb) • [Fonctionnalités](#bookmark=id.rjtteofu34gs) • [Workflow](#bookmark=id.vy394u6k1s7v)

## **🎯 À propos**

Un gestionnaire et équilibreur de datasets avancé pour la préparation d'entraînements de modèles IA **(Flux, Qwen, SDXL, LoRA)**. Conçu avec **Gradio** et propulsé par des injections JavaScript natives pour des performances optimales, cet outil permet de **visualiser, nettoyer, analyser et exporter** vos datasets d'images avec une ergonomie digne d'un logiciel de bureau.

## **🚀 Nouveautés de la v2.0**

Cette version majeure transforme l'outil en une véritable application "desktop-like" :

* **Sélection "Façon Windows" :** Support natif de \[Ctrl+Clic\], \[Maj+Clic\] et \[Ctrl+A\] dans la galerie, avec un rendu visuel 100% JavaScript (zéro temps de chargement ou clignotement).  
* **Éditeur de Tableau "Excel-like" :** Cliquez sur une case et tapez votre chiffre pour écraser instantanément la valeur, sans effacer au préalable.  
* **Auto-Save Silencieux :** Vos modifications de texte sont sauvegardées automatiquement en arrière-plan lorsque vous naviguez entre les images.  
* **Smart Swap & Drag & Drop :** Réorganisez vos recettes en glissant-déposant les lignes, ou utilisez \[Alt+Flèches\]. L'algorithme prévient les doublons de priorité de manière intelligente.  
* **Calcul Instantané :** Les statistiques se mettent à jour en temps réel lors de votre saisie, sans besoin d'actualiser manuellement.  
* **Export CivitAI :** Génération en un clic d'un tableau Markdown de vos statistiques, prêt à être collé sur CivitAI ou GitHub.

## **📸 Galerie & Aperçu**

### **🎬 Interface Principale**

### **🖼️ Galerie Complète**

#### **1️⃣ Vue Gestion des Tags et Édition**

Interface de gestion des tags avec sélection multiple et édition batch

#### **2️⃣ Vue Statistiques et Analyse**

Visualisation des statistiques avec graphiques Plotly et distribution des tags

#### **3️⃣ Vue Assistant d'Export**

Assistant d'export intelligent avec simulation et stratégies d'équilibrage

#### **4️⃣ Vue Galerie Détaillée**

Galerie avancée avec navigation et actions contextuelles

## **🌟 Fonctionnalités Principales**

### **🖼️ Galerie et Ergonomie (Interface Avancée)**

| Fonctionnalité | Description |
| :---- | :---- |
| **Design UI/UX Optimisé** | Panneau latéral redimensionnable et repliable pour maximiser l'espace de travail. Mode sombre natif. |
| **Sélection Ultra-Rapide** | \[Ctrl+Clic\], \[Maj+Clic\], \[Ctrl+A\] avec surbrillance dynamique gérée côté client. |
| **Raccourcis Claviers Complets** | Navigation (←/→), Recherche (Ctrl+F), Sauvegarde (Ctrl+S), Stats (Alt+S), Vider (Alt+C). |
| **Menu Contextuel Custom** | Clic droit sur l'image pour un accès rapide aux actions essentielles sans déplacer la souris. |

### **👁️ Visualiseur & Édition**

| Fonctionnalité | Description |
| :---- | :---- |
| **Surlignage Robuste** | Les mots-clés suivis s'illuminent en jaune dans vos captions via un moteur Regex optimisé. |
| **Auto-Save Silencieux** | Sauvegarde transparente de vos textes lors de la navigation (avec création de .bak). |
| **Compteur de Tokens CLIP** | Avertissement visuel en rouge si votre caption dépasse la limite habituelle (ex: \> 225 tokens). |

### **⚡ Édition en Batch (Masse)**

💡 **Note** : Les actions s'appliquent à tout le dataset ou uniquement à votre sélection multiple.

* **Gestion des Synonymes (Expert LoRA)** : Remplacement intelligent de tags répétitifs par une liste de synonymes tournants.  
* **Chercher/Remplacer (avec Regex)** : Support des expressions régulières pour un nettoyage en profondeur.  
* **Nettoyage Automatique** : Suppression des virgules multiples, espaces en trop et tags en doublons.  
* **Aperçu Avant/Après & Undo** : Visualisez les changements avec possibilité d'annuler (Undo).

### **📈 Statistiques & Équilibrage**

* 🎯 **Calcul Instantané** : Mises à jour des graphiques et données en temps réel lors de la saisie des mots-clés.  
* 📊 **Visualisation Plotly** : Génération de camemberts et d'histogrammes dynamiques.  
* 📋 **Export CivitAI / Markdown** : Bouton dédié pour copier vos statistiques proprement.  
* 🔍 **Chasseur de Tags Orphelins** : Détecte les fautes de frappe (tags uniques).

### **📁 Assistant d'Export Intelligent**

Trois stratégies d'export pour tous les besoins :

| Stratégie | Description |
| :---- | :---- |
| **Équilibrage Auto** | L'algorithme "Greedy" sélectionne la combinaison d'images qui se rapproche le plus de vos cibles %. |
| **Priorité** | Remplit le dataset dans l'ordre de priorité de vos tags. |
| **Filtre Classique** | Ne garde que les images contenant certains tags. |

**Bonus** : Interface de tableau Drag & Drop, Saisie express, Boutons Monter/Descendre, et Simulation visuelle d'export.

## **🚀 Installation & Lancement**

### **Prérequis**

* **Python 3.10+**  
* Git

### **Étapes**

1. **Clonez le dépôt**  
   git clone \[https://github.com/BC8069EA84/Datasets-Images-EditSelect.git\](https://github.com/BC8069EA84/Datasets-Images-EditSelect.git)  
   cd Datasets-Images-EditSelect

2. **Installez les dépendances**  
   pip install gradio pandas plotly

3. **Lancez l'outil**  
   python lora\_manager.py

4. **Accédez l'interface**  
   * L'interface s'ouvrira automatiquement dans votre navigateur par défaut (127.0.0.1).

## **💡 Comment ça marche ? (Workflow recommandé)**

1️⃣  Chargez votre dossier  
    └─ Contenant vos paires image \+ .txt

2️⃣  Analysez vos données  
    └─ Onglet Statistiques → "Remplir avec le Top 20"

3️⃣  Définissez vos cibles  
    └─ Assistant d'Export → Ajustez les priorités et pourcentages

4️⃣  Nettoyez & Éditez  
    └─ Galerie → Utilisez le Mode Multi-sélection et l'Éditeur Batch

5️⃣  Exportez votre dataset  
    └─ Assistant d'Export → Simuler → Exporter

## **📦 Structure du Projet**

Datasets-Images-EditSelect/  
├── lora\_manager.py          \# Point d'entrée principal (Le code métier et UI)  
├── Changelog.md             \# Historique des mises à jour (v2.0)  
├── en.json                  \# Dictionnaire de langue Anglaise  
├── fr.json                  \# Dictionnaire de langue Française  
├── readme.md                \# Cette documentation  
├── requirements.txt         \# Dépendances Python  
└── screenshots demo/        \# Démonstration visuelle

## **🎓 Cas d'Usage**

✅ Préparation de datasets pour **LoRA fine-tuning** ✅ Équilibrage de datasets **multi-concepts** ✅ Nettoyage et correction de captions en **masse** ✅ Analyse statistique de la distribution d'un dataset  
✅ Export intelligent avec contraintes précises

## **📄 Licence**

Libre d'utilisation et de modification pour vos workflows d'IA.

## **🤝 Contribution**

Les contributions sont bienvenues \! N'hésitez pas à :

* Signaler des bugs via les Issues  
* Proposer des améliorations  
* Soumettre des Pull Requests

**Fait avec ❤️ pour la communauté IA**  
[⬆️ Retour au sommet](#bookmark=id.24dv3z72fojd)