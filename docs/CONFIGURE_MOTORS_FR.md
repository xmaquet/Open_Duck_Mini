# ⚙️ Configuration initiale des moteurs Feetech (Open Duck Mini)

## 🎯 Objectif
Configurer chaque moteur Feetech avec son **ID** et sa position zéro avant utilisation du robot Open Duck Mini.

💡 Cette procédure peut être réalisée :
- **Avant montage** (recommandé pour précision maximale)
- **Après montage** (possible avec précautions)

---

## 1️⃣ Pré-requis

**Matériel :**
- Raspberry Pi (ou PC) avec Python 3
- Alimentation stable pour les servos (batterie ou bloc d’alimentation adapté)
- Câble USB-série pour la carte de contrôle moteur
- Script `configure_motor.py` disponible dans le dépôt `Open_Duck_Mini_Runtime` (branche `v2`)

**Logiciel :**
- Cloner et installer le runtime :
```bash
git clone https://github.com/apirrone/Open_Duck_Mini_Runtime
cd Open_Duck_Mini_Runtime
git checkout v2
pip install -e .
```

---

## 2️⃣ Précautions de sécurité

- **Toujours** soutenir le robot ou isoler le servo à calibrer pour éviter qu’il ne force contre une surface.
- **Ne pas** forcer mécaniquement un servo avec le couple activé.
- En cas de calibration après montage : désactiver le couple (`io.disable_torque([id])`) avant tout ajustement mécanique.

---

## 3️⃣ Lancement de la configuration

Pour chaque servo, exécuter :
```bash
python configure_motor.py --id <id>
```

Ce que fait le script :
1. Scan du servo connecté
2. Attribution de l’ID choisi
3. Réglage du baudrate
4. Positionnement à zéro mécanique
5. Attente de l’installation du horn (bras) le plus aligné possible

📌 **Note** : Le zéro mécanique n’a pas besoin d’être parfait. Les écarts seront compensés lors de la calibration d’offset.

---

## 4️⃣ Liste des IDs des servos

| Articulation        | ID  |
|---------------------|-----|
| Hanche gauche yaw   | 20  |
| Hanche gauche roll  | 21  |
| Hanche gauche pitch | 22  |
| Genou gauche        | 23  |
| Cheville gauche     | 24  |
| Cou pitch           | 30  |
| Tête pitch          | 31  |
| Tête yaw            | 32  |
| Tête roll           | 33  |
| Hanche droite yaw   | 10  |
| Hanche droite roll  | 11  |
| Hanche droite pitch | 12  |
| Genou droit         | 13  |
| Cheville droite     | 14  |

---

## 5️⃣ Calibration de l’offset

Après cette configuration, il est recommandé de réaliser la **calibration des offsets** pour chaque articulation.  
➡️ Voir le guide : `CALIBRATION_SERVOS_FEETECH_FR.md`

---

## 📷 Alignement du horn

Positionner le horn comme sur la photo ci-dessous lors de la mise à zéro :

![Alignement du horn](https://github.com/user-attachments/assets/e3c4aefa-5e0a-4d4e-89f4-82df9bf30e29)

---

## ✅ Résumé du processus

1. Brancher et alimenter le servo
2. Lancer `configure_motor.py --id <id>`
3. Aligner le horn au mieux
4. Répéter pour chaque servo selon la liste d’IDs
5. Effectuer la calibration d’offset

---

🛠 **Prêt pour l’étape suivante** : calibration d’offsets et intégration dans `duck_config.json` ou EEPROM.