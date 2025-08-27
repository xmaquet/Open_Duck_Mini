# Open Duck Mini

Mini-version (~42 cm) du BDX Droid, pensée pour être reproductible par les makers et la communauté robotique, avec un coût cible inférieur à 400 €.  
Le projet regroupe modèles 3D, schémas électroniques, documentation, code de simulation et scripts de pilotage.

---

## Contenus du dépôt

### 📂 Racine
- `README.md` : présentation originale du projet.
- `LICENSE` : licence libre.
- `thanks.md` : remerciements aux contributeurs.
- `pyproject.toml`, `setup.cfg` : configuration du paquet Python **mini-bdx** (dépendances et build).
- `BEST_WALK_ONNX.onnx`, `BEST_WALK_ONNX_2.onnx` : politiques de marche exportées au format ONNX.

---

### 📂 Documentation (`docs/`)
- **Assemblage & impression** :  
  - `assembly_guide.md` : guide d’assemblage.  
  - `print_guide.md` : recommandations pour l’impression 3D.
- **Câblage & électronique** :  
  - `open_duck_mini_v1_wiring_diagram.png`  
  - `open_duck_mini_v2_wiring_diagram.(drawio|png)`  
  - `wiring.(drawio|png)`  
  - `head_schematic.xcf`
- **Calibration & configuration des servos** :  
  - `CONFIGURE_MOTORS_FR.md`  
  - `configure_motors.md`  
  - `CALIBRATION_SERVOS_FEETECH_FR.md`  
  - `feetech_identification.md`
- **Préparation & simulation** :  
  - `prepare_robot.md` (préparer le robot physique).  
  - `sim2real.md` (transfert simulation → réel).

---

### 📂 Bibliothèque Python (`mini_bdx/`)
Code principal du projet.

- **Moteur de marche**  
  - `placo_walk_engine/placo_walk_engine.py` : moteur de marche basé sur la librairie **placo**.  
  - `old_walk_engine/` : version historique du moteur de marche.

- **Utilitaires** (`utils/`) :  
  Fonctions pour la simulation Mujoco, les splines, l’apprentissage par renforcement, etc.

- **Modèles robotiques**  
  - `robots/` : définitions URDF/XML, STL et PART pour le robot v2 et ses variantes.  
  - `mujoco_models/` : modèles et scènes Mujoco pour la simulation.  
  - Assets graphiques et textures.

---

### 📂 Expérimentations (`experiments/`)
Scripts de test, simulation et apprentissage.

- **v2/**  
  - `placo_walk_real_robot.py` : pilotage du robot réel (via Feetech/pypot, option manette Xbox, option visualisation).  
  - `mujoco_placo_walk.py` : simulation de la marche sous Mujoco.  
  - `onnx_AWD_mujoco*.py` : exécution de politiques ONNX.  
  - `placo_defaults.json`, `params_m6.json` : paramètres par défaut.

- **RL/** et **RL/new/**  
  - Environnements Gym/Mujoco.  
  - Scripts d’imitation (BC, GAIL), apprentissage, enregistrement et replay d’épisodes.  
  - `play_policy.py` pour exécuter une politique entraînée.

- **LeRobot/**  
  - Scripts d’enregistrement HDF5 (essais de collecte de données).

---

### 📂 Pièces à imprimer (`print/`)
Toutes les pièces nécessaires en **.stl** et **.part** :  
tête, tronc, jambes, supports moteurs, antennes, oeil, adaptateurs…  
Correspond aux fichiers mécaniques utilisés dans les modèles URDF.

---

## Points d’entrée du projet

- **Simulation** :  
  `experiments/v2/mujoco_placo_walk.py`  
  → lance une marche simulée avec Mujoco et Placo.

- **Robot réel** :  
  `experiments/v2/placo_walk_real_robot.py`  
  → exécute le moteur de marche avec interface Feetech/pypot, manette Xbox optionnelle, visualisation optionnelle.  
  ⚠️ Nécessite le dépôt **[Open_Duck_Mini_Runtime](https://github.com/antoine-pi/Open_Duck_Mini_Runtime)** sur la machine embarquée (Raspberry Pi Zero 2 W).

---

## Premiers pas

1. **Impression 3D** : consulter `docs/print_guide.md` puis imprimer les pièces du dossier `print/`.  
2. **Assemblage** : suivre `docs/assembly_guide.md`.  
3. **Câblage** : se référer aux schémas de `docs/`.  
4. **Configuration des servos** : lire `docs/CONFIGURE_MOTORS_FR.md` et `docs/CALIBRATION_SERVOS_FEETECH_FR.md`.  
5. **Simulation** : exécuter `experiments/v2/mujoco_placo_walk.py`.  
6. **Robot réel** : installer le runtime dédié, puis lancer `experiments/v2/placo_walk_real_robot.py`.

---

## Ressources complémentaires
- [Projet d’origine : BDX Open Duck](https://github.com/antoine-pi/Open_Duck_Mini)  
- [Runtime embarqué : Open_Duck_Mini_Runtime](https://github.com/antoine-pi/Open_Duck_Mini_Runtime)  
