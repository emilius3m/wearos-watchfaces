# Palette Meteo — versione 5.0, variante A

Quadrante nativo Wear OS in Watch Face Format 2, pacchetto `com.local.watchface.syshud`. Ripristina la disposizione verticale richiesta: ore sopra i minuti a sinistra, secondi e salute a destra, previsioni e comandi in basso.

La versione 5.0 realizza il mockup A scelto dall'utente: tre grandi pulsanti rotondi lungo un arco, con icona e nome **Agenda**, **Voce**, **Avvisi**. I cerchi misurano 100 unità WFF: sul display misurato da 480 px e 340 dpi corrispondono a circa 106,67 px, cioè **50,20 dp**. Voce ha un'area sensibile più ampia (112 unità) per compensare le dimensioni non scalate dei Group riportate dall'accessibilità del runtime Samsung. Le aree sono separate, interamente nel display e non intercettate dalla scorciatoia meteo. Le due complicazioni laterali mantengono gli ID 0 e 1, così come la scorciatoia meteo configurabile mantiene l'ID 3.

Per fare spazio ai tasti, le palette sono leggermente più compatte e ogni previsione presenta il simbolo accanto alle temperature. Restano disposizione verticale, animazione al cambio cifra, secondi sul bordo, tre giorni di previsioni e always-on a contorno.

## Aspetto e comportamento

- Quattro palette grafite, ore avorio e minuti lime. Il colore di minuti, indicatori e pulsante segue l'accento selezionato: lime, ambra, ghiaccio, rosso o bianco.
- Solo le cifre che cambiano si ribaltano dall'alto. La metà superiore precedente ruota verso la cerniera e la nuova metà inferiore si apre in 600 ms. Gestiti anche 23:59 → 00:00 e i cambi delle decine.
- Sessanta tacche sul bordo. Il secondo corrente ha una tacca luminosa più lunga e quattro tacche di scia attenuata; avanza di una posizione al secondo. Il numero piccolo a destra non ha un altro anello.
- Battito con etichetta BPM, passi con etichetta PASSI e batteria con percentuale. Nessuna corona laterale ripetuta. Sotto il 20% la percentuale della batteria diventa rossa.
- Previsioni per i prossimi tre giorni con giorno, simbolo, massima e minima. La legenda MAX / MIN esplicita l'ordine delle temperature. Il tocco mantiene la scorciatoia Meteo configurabile del progetto; se lo slot non è assegnato, è previsto l'avvio di Meteo Samsung come destinazione predefinita.
- I dati provengono dalle sorgenti native `WEATHER.*`. Se mancano, il quadrante mostra trattini. Un aggiornamento fallito conserva i dati disponibili e mostra l'orario dell'ultimo aggiornamento. Gestite tutte le 16 condizioni del formato.
- Registratore Samsung al centro in basso; calendario e notifiche nelle due complicazioni modificabili. Restano le scorciatoie per cuore, passi e batteria. Un aggiornamento conserva le assegnazioni delle complicazioni scelte dall'utente.
- Always-on: stessa disposizione delle cifre, solo contorni e data attenuata, senza secondi, animazioni, meteo o pulsanti. Non cambia l'impostazione AOD del Watch.
- Orario accessibile al lettore schermo anche se le cifre sono immagini.

## Consegne

- `build/PaletteMeteo.apk`: versione 5.0 firmata con la stessa chiave locale delle versioni precedenti.
- `design/round-buttons/preview-illustrative-weather.png`, `preview-always-on.png`, `flip-preview.gif`: anteprime della variante A realizzata, con meteo illustrativo.
- `design/round-buttons/touch-geometry.json`: misure delle tre aree di tocco sul display 480 px / 340 dpi.
- `design/mockups-touch-20261114/A-tre-tasti-grandi.png`: mockup selezionato dall'utente.
- `backups/palette-v4-before-round-buttons/`: sorgenti e APK preservati prima della variante A, compresa la scorciatoia meteo configurabile.
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

## Verifiche della versione 5.0

Il 14 novembre 2026: controlli di schema, risorse, firma e compilazione superati; verificati i sei cambi di cifra, la posizione dei secondi, l'AOD statico e i casi meteo. Ispezionate le anteprime. Il controllo `validate_touch.py` verifica le dimensioni minime di 48 dp, la separazione dei tasti, il margine circolare e l'assenza di sovrapposizione della scorciatoia meteo.

La variante A 5.0 è stata installata e visualizzata il 14 novembre 2026: `device-initial-install.png` documenta la disposizione reale e i dati meteo disponibili. Il successivo APK, con padding aggiuntivo per Voce e destinazione meteo predefinita, resta da installare e verificare perché il collegamento si è nuovamente interrotto. Le impostazioni rilevate erano `ambient_enabled=0` e `ambient_force_when_docked=0`; non sono state modificate. Il Watch mostrava il risparmio energetico attivo.

## Verifiche storiche della versione 4.0

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

La compilazione rigenera XML e immagini delle palette, esegue i controlli locali e geometrici, aggiorna la miniatura, valida e firma. `verify_device.py` acquisisce il quadrante e controlla le scorciatoie della disposizione 5.0. Usarlo dopo l'installazione, con il Watch sbloccato e senza altre interazioni in corso. Non cambia impostazioni di sistema. Usare `ANDROID_SERIAL` se ADB vede sia il dispositivo per IP sia l'alias mDNS. `validate_touch.py --pixels 480 --density 340` permette di ricontrollare le misure per il dispositivo effettivo.

## Riferimenti

- Teko, SIL Open Font License 1.1: `licenses/Teko-OFL.txt`; https://github.com/google/fonts/tree/main/ofl/teko
- Previsioni native: https://developer.android.com/training/wearables/wff/weather
- Fonti temporali: https://developer.android.com/reference/wear-os/wff/common/attributes/source-type
- Avvio delle app: https://developer.android.com/reference/wear-os/wff/common/launch
- Dimensioni di tocco: https://developer.android.com/training/wearables/accessibility
- Schema ufficiale locale in `tools/wff-schema-2`: https://github.com/google/watchface/tree/main/third_party/wff/specification/documents/2
