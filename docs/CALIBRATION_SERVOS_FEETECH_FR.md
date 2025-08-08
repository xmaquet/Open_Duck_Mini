# 📘 Guide de calibration des servos Feetech (montés sur le robot)

## 🎯 Objectif
Ajuster le **zéro mécanique** des servos pour que la position neutre du robot corresponde à la commande `0` envoyée au moteur, en compensant les petits décalages liés au montage.

---

## 1️⃣ Préparatifs

**Matériel nécessaire :**
- Open Duck Mini entièrement assemblé.
- Alimentation stable.
- PC ou Raspberry Pi avec accès au script de calibration (`find_soft_offsets.py` ou version modifiée).
- Manette (facultatif, pour tests après calibration).

**Précautions :**
- Placer le robot sur un support stable **pattes décollées du sol**.
- Ne pas forcer à la main un servo sous tension (couple activé).
- Calibrer **une articulation à la fois**.

---

## 2️⃣ Lancement du script

```bash
cd scripts/
python find_soft_offsets.py
```

💡 Le script va :
1. Scanner les servos connectés.
2. Demander de **choisir l’articulation** à calibrer.
3. Envoyer le moteur à sa **position zéro logicielle**.

---

## 3️⃣ Positionner mécaniquement

1. Quand le servo atteint **zéro logiciel**, le couple reste activé.
2. **Désactiver le couple** pour libérer le mouvement (`io.disable_torque([id])`).
3. Ajuster **l’élément mécanique** fixé au servo (patte, cou, etc.) pour qu’il soit **dans la position neutre visée**.

---

## 4️⃣ Calcul et enregistrement de l’offset

- Le script lit la position actuelle (`new_pos`).
- Calcule l’offset :
  ```
  offset = zero_pos - new_pos
  ```
- Enregistre cet offset :
  - soit dans **`duck_config.json`** (méthode logicielle),
  - soit dans l’**EEPROM** du servo avec `io.set_offset()`.

---

## 5️⃣ Vérification

1. **Réactiver le couple** :
   ```python
   io.enable_torque([id])
   ```
2. Commander la position zéro :
   ```python
   io.set_goal_position({id: 0})
   ```
3. Vérifier que l’articulation revient **pile** à la position neutre.

---

## 6️⃣ Répéter pour chaque articulation

Ordre recommandé :
1. Hanche → genou → cheville (patte droite)
2. Hanche → genou → cheville (patte gauche)
3. Cou → tête

---

## 📊 Schéma visuel

```
[ Zéro logiciel ] ---> [ Ajustement mécanique ] ---> [ Offset calculé ]
```

```
┌───────────┐
│ Servo 0°  │ → Ajuster mécaniquement → Calcul offset → Enregistrer
└───────────┘
```

---

## ⚠️ Notes importantes

- Mode **EEPROM** : offset permanent, aucun besoin de corriger dans `duck_config.json`.
- Mode **logiciel** : offset appliqué à chaque démarrage par le runtime.
- **Monté en place** = possible, mais **désactiver le couple avant manipulation mécanique** pour éviter d’endommager les engrenages.