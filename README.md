
# 🤖 WSOL-NOSOL-SAH – Robot de Suport per a Bombers

Sistema robòtic autònom dissenyat per explorar entorns perillosos, detectar víctimes, i proporcionar suport en operacions de rescat i extinció d'incendis.

## 🎯 Objectiu del projecte
Reduir el risc per als bombers humans mitjançant:
- Exploració remota d'espais perillosos
- Monitoratge ambiental en temps real
- Detecció de víctimes
- Navegació autònoma i evasió d'obstacles

> ⚠️ Aquest projecte ha estat desenvolupat amb hardware limitat, dins les possibilitats econòmiques disponibles, com a prova de concepte per validar el software. La idea original contemplava una arquitectura més ambiciosa.

## 🧱 Arquitectura del Sistema

### Nivell 1 – Arduino
- Control de motors i actuadors
- Gestió de sensors (gasos, ultrasònics, temperatura)

### Nivell 2 – Raspberry Pi
- Bridge entre Arduino i PC
- Lectura de LiDAR i càmera
- Comunicació TCP/IP
- Heartbeat + Watchdog

### Nivell 3 – PC (Windows)
- Interfície gràfica amb PyQt
- Processament de dades en temps real
- Navegació i control manual/autònom

## 🖥️ Interfície d'Usuari

- Mapa dinàmic del LiDAR
- Stream de vídeo normal/tèrmic
- Lectures de sensors en temps real
- Control manual i missions automàtiques
- Alertes visuals/sonores i registre d'esdeveniments

## 📁 Estructura del Projecte

```
robot_control_system/
├── Main.py
├── modules/
├── ui/
├── config/
├── resources/
├── raspberry/
├── arduino/
├── logs/
├── db/
├── requirements.txt
└── README.md
```

## 📡 Comunicacions

- Protocol JSON sobre TCP/IP (PC ↔ Raspberry)
- Serial USB (Raspberry ↔ Arduino)
- Reconnexió automàtica i gestió d’errors

## 🔬 IA prevista (no implementada per ara)

Funcions planificades però no actives per incompatibilitat entre TensorFlow i Python 3.13:
- Predicció de propagació d’incendis
- Detecció de víctimes (visió + àudio + CO₂)
- Navegació amb SLAM
- Avaluació estructural
- Coordinació multi-robot

## 📦 Requisits

Instal·lació de dependències:
```bash
pip install -r requirements.txt
```

Entorns:
- Windows 11 (PC de control)
- Raspberry Pi OS (bridge)
- Arduino IDE (per carregar l'sketch)

## 🛠️ Execució

**PC (GUI + control):**
```bash
python Main.py
```

**Raspberry Pi (bridge):**
```bash
python raspberry/complete_bridge.py
```

**Arduino:**
Càrrega de `arduino/Arduino_motors_sensors.ino` amb l’IDE d’Arduino.

## 📜 Llicència

Distribuït sota la [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)  
El programari és lliure, però qualsevol versió modificada ha de mantenir la mateixa llicència.

## 🙏 Agraïments

Aquest projecte no hauria estat possible sense el suport dels meus companys d'intel·ligència artificial.  
**Gràcies a ChatGPT i Claude**, que han desenvolupat la major part del codi, demostrant que, junts, **ho podem tot**.

També vull agrair al meu fill **Josep**, que ha suportat els meus crits i eufòries durant tot aquest projecte amb una paciència heroica.
