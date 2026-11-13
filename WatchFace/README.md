# Palette Meteo — versione 4.0

Quadrante nativo Wear OS in Watch Face Format 2, pacchetto `com.local.watchface.syshud`. Ripristina la disposizione verticale richiesta: ore sopra i minuti a sinistra, secondi e salute a destra, previsioni e comandi in basso.

## Aspetto e comportamento

- Quattro palette grafite, ore avorio e minuti lime. Il colore di minuti, indicatori e pulsante segue l'accento selezionato: lime, ambra, ghiaccio, rosso o bianco.
- Solo le cifre che cambiano si ribaltano dall'alto. La metà superiore precedente ruota verso la cerniera e la nuova metà inferiore si apre in 600 ms. Gestiti anche 23:59 → 00:00 e i cambi delle decine.
- Sessanta tacche sul bordo. Il secondo corrente ha una tacca luminosa più lunga e quattro tacche di scia attenuata; avanza di una posizione al secondo. Il numero piccolo a destra non ha un altro anello.
- Battito con etichetta BPM, passi con etichetta PASSI e batteria con percentuale. Nessuna corona laterale ripetuta. Sotto il 20% la percentuale della batteria diventa rossa.
- Previsioni per i prossimi tre giorni con giorno, simbolo, massima e minima. La legenda MAX / MIN esplicita l'ordine delle temperature. Il tocco sulla previsione apre Meteo Samsung, dove consultare anche il dettaglio attuale.
- I dati provengono dalle sorgenti native `WEATHER.*`. Se mancano, il quadrante mostra trattini. Un aggiornamento fallito conserva i dati disponibili e mostra l'orario dell'ultimo aggiornamento. Gestite tutte le 16 condizioni del formato.
- Registratore Samsung al centro in basso; calendario e notifiche nelle due complicazioni modificabili. Restano le scorciatoie per cuore, passi e batteria. Un aggiornamento conserva le assegnazioni delle complicazioni scelte dall'utente.
- Always-on: stessa disposizione delle cifre, solo contorni e data attenuata, senza secondi, animazioni, meteo o pulsanti. Non cambia l'impostazione AOD del Watch.
- Orario accessibile al lettore schermo anche se le cifre sono immagini.

## Consegne

- `build/PaletteMeteo.apk`: versione 4.0 firmata con la stessa chiave locale delle versioni precedenti.
- `res/raw/watchface.xml`: sorgente WFF generato.
- `design/vertical/mockup.png`: proposta grafica prodotta con Imagegen prima dell'implementazione.
- `design/vertical/preview-illustrative-weather.png`: rendering del sorgente con dati dimostrativi.
- `design/vertical/flip-preview.gif`: animazione locale 13:59 → 14:00, compreso il passaggio dei secondi lungo il bordo.
- `design/vertical/flip-contact-sheet.jpg`: fotogrammi intermedi del ribaltamento.
- `design/vertical/preview-always-on.png`: rendering locale della modalità ambient.
- `design/vertical/device-active.png` e `device-always-on.png`: acquisizioni reali della versione 4.0 sul Galaxy Watch.
- `design/vertical/device-minute-change.mp4` e `device-motion-contact.jpg`: registrazione reale e fotogrammi del passaggio 07:20 → 07:21.
- `design/vertical/device-verification.json`: riscontro delle verifiche sul dispositivo e delle impostazioni ambient conservate.
- `design/vertical/preview-weather-unavailable.png`, `preview-one-day-unavailable.png`, `preview-stale-weather.png`: stati di assenza o aggiornamento fallito.
- `backups/palette-v3-before-vertical/`: risorse, strumenti, documentazione e APK della versione 3.0 precedente.
- `backups/apex-v2-before-flip/` e `backups/syshud-original-20261112/`: versioni precedenti preservate.

I file `preview-*` e `flip-preview.gif` sono rendering locali; i loro numeri meteo sono illustrativi e non sono inclusi nelle espressioni del quadrante. I file `device-*` e `tap-*` sono acquisizioni dal Watch, con dati reali. La miniatura dell'APK usa trattini al posto delle previsioni per non presentare valori inventati.

## Verifiche della versione 4.0

Il 13 novembre 2026 sono state completate:

- Validazione XSD 1.1 contro lo schema ufficiale WFF 2 e controllo dei riferimenti a risorse, stringhe, font e palette.
- Verifica dei fotogrammi iniziali e finali di sei cambi d'orario: 00:00, 10:00, 20:00, 14:00, 09:10 e 23:59.
- Controllo della posizione della tacca dei secondi ai quattro punti cardinali, a 16 secondi e a 59 secondi; confronto dell'AOD a secondi diversi per confermarne la staticità.
- Render delle 16 condizioni meteo, assenza totale, singolo giorno mancante e dati non aggiornati.
- Ispezione visiva delle modalità attiva e ambient e dei fotogrammi del ribaltamento.
- Compilazione Android, allineamento e verifica della firma APK riusciti.

**Versione 4.0 installata e verificata il 13 novembre 2026 sul Galaxy Watch SM-L310 (480 × 480, API 36).** Confermati dal gestore pacchetti versione e installazione; ispezionati quadrante attivo, previsioni native su tre giorni e always-on sul display. Il video del passaggio 07:20 → 07:21 mostra il ribaltamento intermedio e la cifra finale corretta. Verificate le cinque destinazioni al tocco: registratore, battito, passi, batteria e meteo. La scorciatoia meteo è stata corretta usando il nome completo della classe Android e verificata nuovamente dal quadrante.

Non sono state modificate impostazioni o simulate condizioni della batteria: `ambient_enabled=1` e `ambient_force_when_docked=0` sono rimasti invariati. L'AOD è confermato dall'acquisizione del display; il dump del servizio riportava `isAmbient=false` e non è stato usato come prova della modalità visualizzata. La durata della batteria non è stata misurata.

La versione 3.0 era stata installata e verificata sul Galaxy Watch SM-L310, display 480 × 480, API 36 il 12 novembre 2026, inclusi meteo nativo, animazione al cambio minuto, always-on e quattro scorciatoie. Le acquisizioni storiche `design/flip/device-*` appartengono a quella versione e non documentano la 4.0.

## Ricostruzione e installazione

Prerequisiti: Python con Pillow, `lxml` e `xmlschema`; Android SDK in `C:\AndroidSdk`, build-tools 36.0.0 e piattaforma 35; Java nel PATH. Font Teko Semibold incluso.

```powershell
.\tools\build.ps1
C:\AndroidSdk\platform-tools\adb.exe connect INDIRIZZO_IP:PORTA
$env:ANDROID_SERIAL = 'INDIRIZZO_IP:PORTA'
C:\AndroidSdk\platform-tools\adb.exe install -r .\build\PaletteMeteo.apk
python .\tools\verify_device.py
```

La compilazione rigenera XML e immagini delle palette, esegue i controlli locali, aggiorna la miniatura, valida e firma. `verify_device.py` acquisisce il quadrante e controlla le destinazioni dei tocchi nella disposizione 4.0. Usarlo dopo l'installazione, con il Watch sbloccato e senza altre interazioni in corso. Non cambia impostazioni di sistema. Usare `ANDROID_SERIAL` se ADB vede sia il dispositivo per IP sia l'alias mDNS.

## Riferimenti

- Teko, SIL Open Font License 1.1: `licenses/Teko-OFL.txt`; https://github.com/google/fonts/tree/main/ofl/teko
- Previsioni native: https://developer.android.com/training/wearables/wff/weather
- Fonti temporali: https://developer.android.com/reference/wear-os/wff/common/attributes/source-type
- Avvio delle app: https://developer.android.com/reference/wear-os/wff/common/launch
- Schema ufficiale locale in `tools/wff-schema-2`: https://github.com/google/watchface/tree/main/third_party/wff/specification/documents/2
