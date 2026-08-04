# HONEYLIGHT MARBLE QUIPU — Complete Prototype Parts List
## 4 ft tall × 8 ft wide · 16 lanes · 16 hammers · Golf balls · Solar powered

> **⚠️ INSTRUMENT CONFIRMED 2026-08-04:** Mark's chosen instrument is the
> **ALIENPAN handpan — D Minor Kurd, 440 Hz, 10 notes, AISI 430 stainless
> steel, 22×22×10", bronze finish, with bag + wooden stand** (photo verified).
> This is a handpan (10 tone fields on a convex shell), NOT a steel tongue
> drum. Adjustments vs. the BOM below:
> - Solenoid arch carries **10 hammers**, not 16 (one per tone field)
> - Arch diameter ~26" to clear the 22" shell + stand
> - Contact pickup mounts under the shell base, not on tongues
> - Sim (honeylight_full.py → marble-quipu-sim.html) already retuned to 10 lanes D Kurd
> - The 16-lane lane/ramp hardware below remains valid for the V2 canon build

> **Vision:** 16 parallel golf ball lanes (quipu runners) drop balls onto a handpan tongue drum actuated by solenoid hammers, triggered by IR sensors, driven by a Raspberry Pi, displayed on an RGB LED quipu bar, amplified through barn speakers, powered by solar.

---

## 1. INSTRUMENT  — $325.00
*The heart of the system — pre-owned, verified mint*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **"Handpan" Tongue Drum — Used Mint** | D Kurd Natural Minor · D A Bb C D E F G A · 9 notes · ~14" dia · dome-top steel · incl. mallets + backpack case | 1 | $325.00 | $325.00 | [Reverb.com #86815164](https://reverb.com/item/86815164) — Anthony's Gear Emporium, Brooklyn NY |

---

## 2. FRAME (4 ft tall × 8 ft wide × 8 in deep) — $209.17
*Dimensional lumber skeleton; holds lanes, ball loader, and drum*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| 2×4 pine stud, 8 ft | Vertical side uprights (×4) + cross-bracing | 6 | $5.48 | $32.88 | Home Depot |
| 2×4 pine stud, 6 ft | Horizontal top/bottom rails | 4 | $4.28 | $17.12 | Home Depot |
| 3/4" plywood sheet, 4×8 ft | Back panel — ball guides, lane walls mount to this | 1 | $42.00 | $42.00 | Home Depot |
| 1/4" plywood sheet, 4×8 ft | Lane divider strips, cut into 16 × 4 ft strips | 1 | $28.00 | $28.00 | Home Depot |
| 1×2 pine, 8 ft | Lane channel lips, ball guide rails | 8 | $3.18 | $25.44 | Home Depot |
| 3" wood screws, 1 lb box | Frame assembly | 1 | $8.97 | $8.97 | Home Depot |
| 1-5/8" wood screws, 1 lb box | Plywood/thin stock fastening | 1 | $7.48 | $7.48 | Home Depot |
| Corner brackets, L-steel 3" | Frame rigidity at corners + mid-spans | 8 | $1.98 | $15.84 | Home Depot |
| Rubber leveling feet, 2" | Floor contact — adjustable for barn floor | 4 | $3.50 | $14.00 | Amazon |
| Wood glue, 8 oz | Lane divider bonding | 1 | $5.48 | $5.48 | Home Depot |
| Black spray paint, flat, 12 oz | Frame finish — shows off LEDs and ball colors | 2 | $5.98 | $11.96 | Home Depot |

---

## 3. PLEXIGLASS FRONT CASE — $362.49
*Clear front lets visitors watch every ball fall — the quipu is visible*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **1/4" clear acrylic sheet, 4×8 ft** | Main front viewing panel — full frame coverage | 1 | $189.00 | $189.00 | TAP Plastics / Amazon |
| 1/8" clear acrylic sheet, 4×2 ft | Side panels (2) — enclose ball channels | 2 | $48.00 | $96.00 | TAP Plastics / Amazon |
| Acrylic cement (Weld-On 3) | Panel bonding at seams | 1 | $14.50 | $14.50 | Amazon |
| Acrylic edge tape, 1/4" × 25 ft | Polish raw cut edges, safety finish | 1 | $12.00 | $12.00 | Amazon |
| Piano hinge, 24" stainless | Hinged front panel — opens for ball loading/service | 2 | $11.50 | $23.00 | Amazon |
| Magnetic catch, heavy duty | Holds front panel closed during play | 4 | $3.25 | $13.00 | Amazon |
| Drill bit set, acrylic-safe | Sharp brad-point bits for clean acrylic holes | 1 | $14.99 | $14.99 | Amazon |

---

## 4. GOLF BALL LANES + BALL LOADER — $259.03
*16 parallel vertical channels · golf balls are the quipu knots*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| Golf balls, white, 12-pack | 1.68" dia, 45.9g — 8 packs = 96 balls (6 per lane reserve) | 8 | $11.99 | $95.92 | Amazon |
| 1.75" PVC square channel, 4 ft | One per lane — snug golf ball guide (1.75" ID = ball + 0.07" clearance) | 16 | $3.48 | $55.68 | Home Depot |
| PVC cement + primer | Channel-to-base bonding | 1 | $8.99 | $8.99 | Home Depot |
| Ball gate servo mount brackets | 3D-printed — holds gate servo at top of each channel | 16 | $1.50 | $24.00 | Print/cut |
| Ball return tray, aluminum, 8 ft | Angled trough at bottom catches balls after strike | 1 | $28.00 | $28.00 | Metal shop |
| Ball elevator motor, DC 12V geared | Worm-gear motor lifts balls from return tray to loader — 5 RPM | 1 | $14.99 | $14.99 | Amazon |
| Ball magazine tube, 2" PVC, 8 ft | Top horizontal reservoir — holds balls waiting for gate dispatch | 1 | $6.48 | $6.48 | Home Depot |
| Magazine deflector servo | Routes balls from magazine into correct lane | 1 | $8.99 | $8.99 | Amazon |
| Felt strip, 1" × 10 ft roll | Lines channel interiors — quiets rolling, cushions pre-strike | 2 | $7.99 | $15.98 | Amazon |

---

## 5. SOLENOID HAMMERS (1 per lane × 16) — $180.51
*Each hammer fires when ball arrives at bottom of lane — no moving arm in prototype*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **JF-0530B push solenoid, 12V** | 10mm stroke, spring return, 9N force — 16 + 2 spare | 18 | $3.20 | $57.60 | Amazon |
| Solenoid mount plate, 1/8" aluminum | Pre-drilled angle bracket, aimed at drum tongue at 40° | 16 | $2.50 | $40.00 | Amazon |
| M3 × 16mm bolts + nuts, 50-pack | Solenoid-to-bracket, bracket-to-frame | 2 | $6.99 | $13.98 | Amazon |
| M3 nylon washers, 50-pack | Isolation between solenoid body and mount (reduces buzz) | 1 | $4.99 | $4.99 | Amazon |
| **Rubber mallet tips, 8mm, 20-pack** | Press-fit onto plunger — warm attack tone on steel | 1 | $8.99 | $8.99 | Amazon |
| 1/2" aluminum crown arch tube, 4 ft | Bent into crown arch over drum — 9 solenoids mount to arch | 2 | $8.49 | $16.98 | Home Depot |
| Tube bender, 1/2" EMT | Bend arch to correct radius | 1 | $15.00 | $15.00 | Harbor Freight |
| U-bolt clamps, 1/2" × 10-pack | Attach solenoid brackets to arch tube | 2 | $7.99 | $15.98 | Amazon |
| Shrink tubing assortment | Insulate solenoid wiring at hammer end | 1 | $6.99 | $6.99 | Amazon |

---

## 6. GATE SERVOS (ball release — 1 per lane) — $80.58
*Holds each ball at top of lane; Pi releases at exact millisecond — gravity does the rest*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **SG90 micro servo, 9g** | 180° rotation, 4.8V, 2.5 kg·cm — 16 lane gates + 2 spare + 2 magazine | 20 | $2.49 | $49.80 | Amazon |
| Servo gate arm, 3D printed | Swings across lane opening to hold/release ball on command | 16 | $0.80 | $12.80 | 3D print |
| **PCA9685 16-ch PWM servo driver** | One I²C board drives all 16 servos from Pi — required | 1 | $8.99 | $8.99 | Amazon |
| Second PCA9685 board | Chained for solenoid PWM hold control | 1 | $8.99 | $8.99 | Amazon |

---

## 7. ELECTRONICS — BRAIN — $84.26
*Raspberry Pi Zero 2W is the quipucamayoc — reads the score, fires the hammers*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **Raspberry Pi Zero 2W** | Quad-core 1GHz, 512MB RAM, WiFi/BT — runs pi_marble_quipu.py | 1 | $15.00 | $15.00 | Adafruit |
| Pi Zero 2W GPIO header | 2×20 pin solder-on — required for GPIO | 1 | $0.99 | $0.99 | Adafruit |
| 32GB microSD, Class 10 | OS + song data + Python scripts | 1 | $8.99 | $8.99 | Amazon |
| Pi Zero case with GPIO cutout | Dust/insect resistant for barn environment | 1 | $7.99 | $7.99 | Amazon |
| ULN2803A Darlington array IC | Drives 8 solenoids per chip from 3.3V GPIO — need 2 + 1 spare | 3 | $0.95 | $2.85 | Amazon |
| 1N4007 flyback diodes, 50-pack | One per solenoid — prevents back-EMF destroying Pi | 1 | $5.99 | $5.99 | Amazon |
| 330Ω resistors, 100-pack | GPIO current limiting to ULN2803 inputs | 1 | $4.99 | $4.99 | Amazon |
| 10kΩ resistors, 100-pack | Sensor pull-ups | 1 | $4.99 | $4.99 | Amazon |
| Half-size breadboard | Prototype wiring — replace with PCB in V2 | 2 | $4.99 | $9.98 | Amazon |
| PCB screw terminal block, 2-pos | Clean power connections to solenoid harness | 10 | $0.55 | $5.50 | Amazon |
| DIN rail mount enclosure, 8" | Houses Pi + driver boards — mounts inside frame | 1 | $16.99 | $16.99 | Amazon |

---

## 8. BALL SENSORS (1 per lane) — $29.40
*Detects ball arrival at hammer zone — triggers solenoid AND logs the note event*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **IR break-beam sensor pair, TCRT5000** | 3.3V-compatible, 1ms response — 16 + 4 spare | 20 | $0.85 | $17.00 | Amazon |
| Sensor mount bracket, 3D printed | Positions IR beam exactly across lane at strike height | 16 | $0.40 | $6.40 | 3D print |
| Piezo disc sensor, 27mm | Backup: contact detection on hammer plate | 4 | $0.75 | $3.00 | Amazon |
| LM393 comparator board, 2-ch | Cleans piezo signal to 3.3V logic for Pi GPIO | 2 | $1.50 | $3.00 | Amazon |

---

## 9. POWER SYSTEM — $133.87
*Two separate rails — 5V for Pi/logic, 12V for solenoids — never mix them*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **12V 10A DC power supply** | Solenoid rail — 16 solenoids × 500mA peak = 8A max draw | 1 | $24.99 | $24.99 | Amazon |
| 5V 3A USB-C power supply | Pi + servo logic rail | 1 | $9.99 | $9.99 | Amazon |
| DC barrel jack panel mount, 5-pk | Clean power entry into enclosure | 1 | $7.99 | $7.99 | Amazon |
| 12V → 5V buck converter, 3A | Optional: run everything off one 12V supply | 1 | $6.99 | $6.99 | Amazon |
| Power switch, 15A rocker, illuminated | Main on/off — panel mount | 1 | $4.99 | $4.99 | Amazon |
| 18 AWG hookup wire, red, 25 ft | 12V solenoid positive runs | 1 | $8.99 | $8.99 | Amazon |
| 18 AWG hookup wire, black, 25 ft | 12V ground runs | 1 | $8.99 | $8.99 | Amazon |
| 22 AWG hookup wire, 6-color, 25 ft | Signal wiring, sensor leads, GPIO connections | 2 | $11.99 | $23.98 | Amazon |
| Ferrule crimp kit + crimper | Professional wire terminations into screw terminals | 1 | $17.99 | $17.99 | Amazon |
| Cable management spiral wrap, 3/8" | Bundle and route wiring harnesses along frame | 1 | $8.99 | $8.99 | Amazon |
| Zip ties, 6" 100-pack | Wire routing and strain relief throughout | 2 | $4.99 | $9.98 | Amazon |

---

## 10. LED QUIPU BAR (the visual score) — $52.14
*16 RGB LEDs across top — one per lane — encodes pitch as color — this IS the quipu*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **WS2812B addressable RGB LED strip, 30/m, 1m** | 16 LEDs used — individually addressable, 5V | 1 | $9.99 | $9.99 | Amazon |
| WS2812B LED panel, 8×8 matrix | Optional full note matrix display above drum | 1 | $14.99 | $14.99 | Amazon |
| Frosted white acrylic diffuser strip, 1"×8" | Mounted in front of LED strip — softens individual dots | 1 | $8.00 | $8.00 | TAP Plastics |
| Aluminum LED channel, U-profile, 8 ft | Houses LED strip + diffuser — professional finish | 1 | $12.99 | $12.99 | Amazon |
| Level shifter 3.3V → 5V, 4-ch | WS2812B needs 5V data signal — Pi GPIO is 3.3V | 1 | $3.99 | $3.99 | Amazon |
| 1000µF 6.3V capacitor | Across LED strip power — prevents first-LED burnout | 2 | $0.99 | $1.98 | Amazon |
| 470Ω resistor | On WS2812B data line — prevents signal ringing | 2 | $0.10 | $0.20 | Amazon |

---

## 11. AUDIO SYSTEM (pickup + mic + amp + speakers) — $248.86
*Capture the drum acoustically + spatial reinforcement for the outdoor barn*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **Contact pickup / piezo transducer, 35mm** | Adheres to drum body — captures vibration directly, no bleed | 2 | $8.99 | $17.98 | Amazon |
| Condenser microphone, cardioid, USB | e.g. FIFINE K678 — captures room resonance + ball roll + barn ambience | 1 | $39.99 | $39.99 | Amazon |
| USB audio interface, 2-in stereo | e.g. Behringer UMC22 — connects pickups + mic to Pi | 1 | $39.99 | $39.99 | Amazon |
| XLR cable, 10 ft, balanced | Mic to interface | 1 | $8.99 | $8.99 | Amazon |
| 1/4" TS cable, 6 ft | Contact pickup to interface input | 2 | $5.99 | $11.98 | Amazon |
| **Class D stereo amplifier, 30W+30W** | e.g. SMSL SA-98E — drives barn speakers from Pi audio | 1 | $44.99 | $44.99 | Amazon |
| **Passive bookshelf speakers, 5", pair** | Mount at top corners of frame — project sound into barn | 1 | $49.99 | $49.99 | Amazon |
| Speaker wire, 16 AWG, 25 ft | Amplifier to speakers | 1 | $9.99 | $9.99 | Amazon |
| Speaker mount brackets, adjustable | Corner-mount to frame top — angle outward 15° | 2 | $6.99 | $13.98 | Amazon |
| RCA to 3.5mm stereo cable, 6 ft | Pi headphone out → amplifier RCA in | 1 | $5.99 | $5.99 | Amazon |
| Foam weatherstripping tape, 1/4" | Isolates drum from frame — prevents vibration coupling | 1 | $4.99 | $4.99 | Home Depot |

---

## 12. SOLAR + BATTERY (outdoor barn operation) — $342.90
*Runs indefinitely in daylight — charges while playing — Potomac MD latitude 39°N*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| **100W monocrystalline solar panel** | ~33V open circuit, 8.3A peak — barn roof mount | 1 | $89.99 | $89.99 | Amazon |
| **MPPT solar charge controller, 20A** | e.g. Victron SmartSolar MPPT 75/15 — temp-compensated | 1 | $49.99 | $49.99 | Amazon |
| **12V 50Ah LiFePO4 battery** | Deep cycle — 2+ days runtime without sun, 2000+ cycles | 1 | $119.99 | $119.99 | Amazon |
| Solar panel mounting bracket kit | Roof/rafter mount — adjustable tilt for 39°N latitude | 1 | $28.99 | $28.99 | Amazon |
| 10 AWG solar panel cable, 20 ft | Panel to charge controller run | 1 | $14.99 | $14.99 | Amazon |
| MC4 connector pairs, 5-pack | Solar panel cable connections — weatherproof | 1 | $7.99 | $7.99 | Amazon |
| Battery to controller cable, 6 ft | 10 AWG, with 30A inline fuse | 1 | $9.99 | $9.99 | Amazon |
| 30A blade fuse + holder | Battery protection | 2 | $3.99 | $7.98 | Amazon |
| Waterproof junction box, 6"×4" | Houses charge controller + fuses — IP65 barn exterior | 1 | $12.99 | $12.99 | Amazon |

---

## 13. TOOLS + CONSUMABLES (one-time build cost) — $122.91
*Project-specific tools — assume you have basic hand tools already*

| Item | Spec | Qty | Unit | Total | Source |
|---|---|---|---|---|---|
| Soldering iron + solder, 60/40 | For PCB headers, solenoid leads, LED connections | 1 | $22.99 | $22.99 | Amazon |
| Helping hands / PCB vise | Hold boards while soldering | 1 | $11.99 | $11.99 | Amazon |
| Digital multimeter | Continuity, voltage, resistance checks throughout | 1 | $14.99 | $14.99 | Amazon |
| Wire stripper, 22-18 AWG | Precision wire prep | 1 | $12.99 | $12.99 | Amazon |
| Heat gun, 300W mini | Shrink tubing on all connections | 1 | $19.99 | $19.99 | Amazon |
| Label maker tape, 1/2" | Label every wire harness — essential for 16-lane debugging | 1 | $9.99 | $9.99 | Amazon |
| Electrical tape, 3-pack | Temp insulation + cable marking | 1 | $6.99 | $6.99 | Home Depot |
| Tung oil finish, 1 qt | Weatherproof any exposed wood — barn humidity protection | 1 | $14.99 | $14.99 | Home Depot |
| Sandpaper assortment 80/120/220 | Frame smoothing before paint | 1 | $7.99 | $7.99 | Home Depot |

---

## BUDGET SUMMARY

| Section | Total |
|---|---|
| 1. Instrument (handpan tongue drum) | $325.00 |
| 2. Frame (4 ft × 8 ft lumber) | $209.17 |
| 3. Plexiglass front case | $362.49 |
| 4. Golf ball lanes + loader | $259.03 |
| 5. Solenoid hammers (×16) | $180.51 |
| 6. Gate servos (×16) | $80.58 |
| 7. Electronics — brain (Pi) | $84.26 |
| 8. Ball sensors (×16) | $29.40 |
| 9. Power system | $133.87 |
| 10. LED Quipu bar | $52.14 |
| 11. Audio (pickup + mic + amp + speakers) | $248.86 |
| 12. Solar + battery | $342.90 |
| 13. Tools + consumables (one-time) | $122.91 |
| **GRAND TOTAL** | **$2,431.12** |
| *Ex-tools (recurring build cost)* | *$2,308.21* |
| *Tools only (one-time)* | *$122.91* |

---

## BUILD SEQUENCE (Recommended Order)

```
WEEK 1:  Order instrument (Reverb) + all Amazon/Adafruit electronics
WEEK 2:  Build frame (Home Depot run) + cut plexiglass
WEEK 3:  Install lanes + wire sensors + breadboard Pi circuit
WEEK 4:  Mount solenoids + arch + tune strike angles
WEEK 5:  Wire LEDs + audio system + power system
WEEK 6:  Solar install on barn roof + full system test
WEEK 7:  Load first songs in golf balls. Play for the goats. 🐐
```

---

*Honeylight Marble Quipu · Prototype v1.0 · Honeylight Farm · Potomac MD 20854*
*"The runners run in parallel."*
