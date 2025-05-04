
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

## 🔬 IA prevista (no implementada per ara)

Funcions planificades però no actives per incompatibilitat entre TensorFlow i Python 3.13:
- Predicció de propagació d’incendis
- Detecció de víctimes (visió + àudio + CO₂)
- Navegació amb SLAM
- Avaluació estructural
- Coordinació multi-robot

## 📦 Requisits

```bash
pip install -r requirements.txt
```

- Windows 11 (PC de control)
- Raspberry Pi OS (bridge)
- Arduino IDE

## 🛠️ Execució

```bash
python Main.py
python raspberry/complete_bridge.py
```

Càrrega de `arduino/Arduino_motors_sensors.ino` amb l’IDE d’Arduino.

## 📜 Llicència

Distribuït sota la [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)

## 🙏 Agraïments

Aquest projecte no hauria estat possible sense el suport dels meus companys d'intel·ligència artificial.  
**Gràcies a ChatGPT i Claude**, que han desenvolupat la major part del codi, demostrant que, junts, **ho podem tot**.  
També vull agrair al meu fill **Josep**, que ha suportat els meus crits i eufòries durant tot aquest projecte amb una paciència heroica.

---

# 🇬🇧 WSOL-NOSOL-SAH – Firefighter Support Robot

An autonomous robotic system designed to explore hazardous environments, detect victims, and assist in rescue and firefighting operations.

## 🎯 Project Goal
Reduce risks to human firefighters through:
- Remote exploration of dangerous areas
- Real-time environmental monitoring
- Victim detection
- Autonomous navigation and obstacle avoidance

> ⚠️ This project was developed with limited hardware resources, adapted to available economic means, as a proof of concept to validate the software. The original idea contemplated a more ambitious architecture.

## 🧱 System Architecture

### Level 1 – Arduino
- Motor and actuator control
- Sensor management (gas, ultrasonic, temperature)

### Level 2 – Raspberry Pi
- Bridge between Arduino and PC
- LiDAR and camera data reading
- TCP/IP communication
- Heartbeat + Watchdog

### Level 3 – PC (Windows)
- GUI with PyQt
- Real-time data processing
- Manual and autonomous navigation

## 🖥️ User Interface

- Real-time LiDAR mapping
- Normal and thermal video stream
- Live sensor readings
- Manual control and mission handling
- Visual/audio alerts and event log

## 🔬 Planned AI Features (not yet implemented)

Not implemented due to incompatibility between TensorFlow and Python 3.13:
- Fire spread prediction
- Victim detection (vision + audio + CO₂)
- Navigation with SLAM
- Structural risk analysis
- Multi-robot coordination

## 📦 Requirements

```bash
pip install -r requirements.txt
```

- Windows 11 (control PC)
- Raspberry Pi OS (bridge)
- Arduino IDE

## 🛠️ Running

```bash
python Main.py
python raspberry/complete_bridge.py
```

Upload `arduino/Arduino_motors_sensors.ino` using the Arduino IDE.

## 📜 License

Distributed under [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)

## 🙏 Acknowledgements

This project would not have been possible without the support of my AI companions.  
**Thanks to ChatGPT and Claude**, who developed most of the code and proved that together, **everything is possible**.  
Also, special thanks to my son **Josep**, who patiently endured my shouting and emotional outbursts throughout this entire project.
