# **📝 Changelog \- IMG Dataset Refiner**

## **v4.0 Pro (Mise à jour d'Ergonomie et de Productivité)**

Cette mise à jour se concentre sur l'accélération radicale du flux de travail manuel et la fiabilisation de l'interface face aux limitations strictes de Gradio 4\.

### **📚 Nouveau : Bibliothèque de mots (Mass Batch Custom)**

* **Module 100% sur mesure :** Remplacement de l'ancien tableau par une liste cliquable personnalisée (HTML/JS) immunisée contre les blocages de Gradio.  
* **Sélection visuelle :** Les mots cochés s'illuminent en orange instantanément.  
* **Édition de masse :** Nouveaux modes pour **Ajouter**, **Retirer** ou **Remplacer** des mots spécifiques sur toute une sélection d'images d'un seul clic.  
* **Mise à jour en temps réel :** L'application de la bibliothèque rafraîchit immédiatement l'éditeur de texte et la galerie visuelle.

### **🌍 Traduction Avancée & Live**

* **Aperçu Live Natif :** Le visualiseur de traduction en temps réel utilise désormais un composant natif stylisé en CSS (vert) pour une stabilité parfaite.  
* **Traduction Globale :** Nouveau bouton permettant de traduire l'intégralité du caption actuel vers l'anglais et de le sauvegarder automatiquement.  
* **Analyse contextuelle :** Le traducteur lit désormais la phrase entière au lieu de la découper mot à mot, garantissant une meilleure détection de la langue de départ (ex: *lumière* traduit correctement en *light*).

### **✨ UI, UX & Navigation**

* **Navigation "Mains sur le clavier" :** Ajout des raccourcis PageUp et PageDown pour passer à l'image précédente/suivante sans jamais perdre le focus de frappe dans la zone de texte.  
* **Tri Dynamique :** Ajout d'une option au-dessus de la galerie pour trier les images par ordre alphabétique croissant (A-Z) ou décroissant (Z-A).  
* **Interface "Desktop" :** Suppression forcée par CSS des en-têtes et pieds de page natifs de Gradio (menu hamburger) pour une interface plus propre et immersive. La barre "Recette Globale" a été rapatriée en haut de l'écran.

### **🛠️ Correctifs & Optimisations (Gradio 4\)**

* **Backups Intelligents :** Le script ne génère plus de fichiers .bak inutiles si le fichier .txt d'origine est complètement vide.  
* **Contournement de Sécurité JS :** Les événements onclick bloqués par Gradio ont été remplacés par un système global d'attributs data-idx couplé à un horodatage (Date.now()), garantissant une réactivité parfaite aux clics.  
* **Fenêtres de confirmation :** Réparation des pop-ups JavaScript de confirmation (Batch & Undo) qui faisaient perdre les données en mémoire sous Gradio 4\.  
* **Internationalisation (100%) :** Tous les nouveaux modules, alertes Javascript et messages système sont désormais liés aux fichiers fr.json et en.json pour une bascule linguistique instantanée et totale.

## **v3.0 Pro**

Cette mise à jour majeure transforme l'outil en une véritable suite professionnelle d'ingénierie de données (Data Engineering) pour les modèles IA. Elle apporte des capacités d'analyse visuelle, de traitement d'images automatisé et d'assistance par Intelligence Artificielle locale.

### **🤖 Nouveautés IA (Assistant Local via API)**

* **Intégration Ollama / LM Studio :** Support natif pour exécuter des modèles de langage (LLM) et de vision (VLM) directement sur le dataset via API locale.  
* **Auto-Taggage / Super OCR (VLM) :** Génération complète de captions ou extraction précise de textes incrustés dans l'image.  
* **Reality Check & Chasseur d'Hallucinations (VLM) :** L'IA compare le texte à l'image et supprime automatiquement les tags qui décrivent des éléments invisibles.  
* **Concept Isolator (VLM) :** L'IA décrit l'environnement et ignore le sujet central, idéal pour préparer les données d'entraînement de LoRAs de personnages.  
* **Traducteur Visuel (Booru ↔ Naturel) :** Conversion intelligente des listes de tags en phrases complètes fluides (optimisé pour Flux et SD3).  
* **Tag Sorting & Standardisation :** Restructuration des tags par ordre d'importance et correction automatique des erreurs sémantiques.  
* **Prompt Personnalisé & Templates :** Possibilité de créer ses propres requêtes IA (avec la variable {tags}), de choisir le mode d'injection (Remplacer, Ajouter) et de sauvegarder ses propres recettes IA.

### **🖼️ Pré-traitement & Gestion de Fichiers**

* **Traque aux Doublons (ImageHash) :** Scanner visuel paramétrable détectant les images similaires (clones exacts ou recadrages) avec interface de suppression rapide A/B.  
* **Smart Face Crop (OpenCV) :** Recadrage automatique centré sur les visages détectés pour optimiser les portraits.  
* **Auto-Formatage 1:1 :** Recadrage carré parfait depuis le centre.  
* **Redimensionnement de Masse :** Downscaling haute qualité (Lanczos) vers 512, 768, 1024 ou 1536px, avec conversion au format WebP ou JPEG.  
* **Gestion Alpha/Transparence :** Les images avec fond transparent (ex: PNG détourés) sont automatiquement aplaties sur fond blanc avant le redimensionnement pour éviter les artefacts noirs.  
* **Batch Renaming :** Renommage propre et incrémental (prefix\_0001.jpg) de toutes les images et de leurs .txt associés en un clic.

### **UI / UX**

* Ajout d'onglets pour une meilleure catégorisation (Vue, Batch, Pré-traitement, IA, Export, Stats).  
* Ajout de panneaux d'information "Astuce" interactifs avec encodage HTML/CSS direct.

### **Stats**

* **Matrice de Co-occurrence (Heatmap) :** Graphique interactif Plotly analysant les liens entre vos 20 tags principaux pour détecter le "Concept Bleeding".  
* **Résolution Bucketing :** Graphique en nuage de points pour visualiser la répartition des résolutions de vos images brutes.  
* **Chasseur de Contradictions :** Détection automatique d'aberrations logiques dans vos captions (ex: "day" \+ "night", ou "solo" \+ "multiple girls").  
* **Matrice d'Exclusion :** Liste les combinaisons de mots qui n'apparaissent *jamais* ensemble pour vérifier la diversité de votre concept.

### **Bugs (Gradio 4+ fixes)**

* **Boucle infinie des mots-clés :** Le calcul des statistiques ne se déclenche plus à chaque lettre tapée, mais uniquement lors de la frappe d'une virgule ,, de la touche Entrée, ou en quittant la case. Fin des effacements intempestifs \!  
* **Bug de surlignage HTML ("Background") :** Correction d'une faille où les mots-clés (comme "background" ou "color") corrompaient la balise HTML \<mark\> utilisée pour le surlignage. Le moteur Regex traite désormais les mots les plus longs en premier et en une seule passe.  
* **Boutons fantômes (Gradio 4\) :** Remplacement de visible=False par du CSS display: none \!important pour les boutons de synchronisation Python/JS, car Gradio 4 détruisait complètement les éléments du DOM, rendant les scripts inopérants.  
* **Bouton de copie CivitAI :** Suppression du paramètre obsolète show\_copy\_button=True qui causait des crashs au lancement, et génération d'un tableau purement Markdown formaté.  
* **Avertissement col\_count :** Mise à jour du paramètre déprécié col\_count vers column\_count pour un terminal propre.  
* **Bug de démarrage :** Sécurisation des fonctions d'interface (MSG\[lang\].get) pour éviter les crashs KeyError: None si l'initialisation de Gradio se fait avant le chargement complet des langues.

## **🌍 Internationalisation**

* Mise à jour complète des fichiers fr.json et en.json pour intégrer toutes les nouveautés IA, Pré-traitement, Batch Custom et UI de la version 4.0.