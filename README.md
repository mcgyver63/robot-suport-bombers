# 🤖 WSOL-NOSOL-SAH – Robot de Suport per a Bombers

Sistema robòtic autònom dissenyat per explorar entorns perillosos, detectar víctimes, i proporcionar suport en operacions de rescat i extinció d'incendis.

## 🎯 Objectiu del projecte
Reduir el risc per als bombers humans mitjançant:
- Exploració remota d'espais perillosos
- Monitoratge ambiental en temps real
- Detecció de víctimes
- Navegació autònoma i evasió d'obstacles

> ⚠️ Aquest projecte ha estat desenvolupat amb hardware limitat, dins les possibilitats econòmiques disponibles, com a prova de concepte per validar el software. La idea original contemplava una arquitectura més ambiciosa.

---

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

---

## 🖥️ Interfície d'Usuari

- Mapa dinàmic del LiDAR
- Stream de vídeo normal/tèrmic
- Lectures de sensors en temps real
- Control manual i missions automàtiques
- Alertes visuals/sonores i registre d'esdeveniments

---

## 📁 Estructura del Projecte

