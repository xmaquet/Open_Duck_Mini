# Feetech STS3215 Calibration GUI

IHM légère (Tkinter) pour scanner, bouger, définir un zéro logiciel et changer ID/baud des servos Feetech STS3215 via `pypot`.

## Setup rapide
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
