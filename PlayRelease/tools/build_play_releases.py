"""Build Play-Store-ready signed .aab bundles & store graphic kits for all 4 E3M Corp watch faces."""
from pathlib import Path
import getpass
import io
import os
import re
import shutil
import subprocess
import zipfile
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
import xmlschema

WATCH_PROJECTS = Path(r'C:\WatchProjects')
PLAY_ROOT = WATCH_PROJECTS / 'PlayRelease'
SDK = Path(r'C:\AndroidSdk')
BUILD_TOOLS = SDK / 'build-tools' / '36.0.0'
AAPT2 = BUILD_TOOLS / 'aapt2.exe'
ANDROID_JAR = SDK / 'platforms' / 'android-35' / 'android.jar'
BUNDLETOOL = PLAY_ROOT / 'tools' / 'bundletool-all.jar'
KEYSTORE = PLAY_ROOT / 'e3mcorp-upload.keystore'
KS_ALIAS = 'e3mcorp-upload'
KS_PASS = os.environ.get('PLAY_KEYSTORE_PASS', '')
JARSIGNER = Path(r'C:\Java\bin\jarsigner.exe')
FONT_VAR = WATCH_PROJECTS / 'WatchFaceNixie' / 'design' / 'teko_variable.ttf'

SCHEMA_DIR = WATCH_PROJECTS / 'WatchFaceNixie' / 'tools' / 'wff-schema-2'
SCHEMA = xmlschema.XMLSchema11(str(SCHEMA_DIR / 'watchface.xsd'))

FACES = [
    dict(
        slug='nixie',
        src=WATCH_PROJECTS / 'WatchFaceNixie',
        package='it.e3mcorp.watchface.nixie',
        version_code='2',
        version_name='1.1',
        title_en='NIXIE',
        title_it='NIXIE',
        tagline='60s IN-18 Tube Chronograph',
        strings_en={
            'watch_face_name': 'NIXIE',
            'case_finish_name': 'Case & Bezel',
            'case_titanium': 'Brushed Titanium & Copper',
            'case_brass': 'Brass & Gunmetal',
            'tube_color_name': 'Tube Color',
            'color_ambra': 'Neon Amber',
            'color_vfd': 'VFD Phosphor Green',
            'color_cobalto': 'Ionic Cobalt',
            'color_rubino': 'Warm Ruby',
            'slot_notif_name': 'Bottom Left Complication',
            'slot_shortcut_name': 'Bottom Right Shortcut',
            'slot_weather_name': 'Weather Shortcut',
        },
        strings_it={
            'watch_face_name': 'NIXIE',
            'case_finish_name': 'Cassa e Lunetta',
            'case_titanium': 'Titanio e Rame',
            'case_brass': 'Ottone e Gunmetal',
            'tube_color_name': 'Colore Valvole',
            'color_ambra': 'Ambra Neon',
            'color_vfd': 'VFD Verde Fosforo',
            'color_cobalto': 'Cobalto Ionico',
            'color_rubino': 'Rubino Caldo',
            'slot_notif_name': 'Complicazione in basso a sinistra',
            'slot_shortcut_name': 'Scorciatoia in basso a destra',
            'slot_weather_name': 'Scorciatoia Meteo',
        },
    ),
    dict(
        slug='solari',
        src=WATCH_PROJECTS / 'WatchFaceSolari',
        package='it.e3mcorp.watchface.solari',
        version_code='2',
        version_name='1.1',
        title_en='SOLARI',
        title_it='SOLARI',
        tagline='Mechanical Split-Flap & Seconds Crown',
        strings_en={
            'watch_face_name': 'SOLARI',
            'theme_color_name': 'Crown & Minutes',
            'color_ambra': 'Solari · Amber',
            'color_corallo': 'Coral · Warm',
            'color_giada': 'Jade · Green',
            'color_cobalto': 'Cobalt · Blue',
            'color_avorio': 'Ivory · Mono',
            'slot_left_name': 'Bottom Left Complication',
            'slot_shortcut_name': 'Bottom Right Shortcut',
            'slot_weather_name': 'Weather Shortcut',
        },
        strings_it={
            'watch_face_name': 'SOLARI',
            'theme_color_name': 'Corona e Minuti',
            'color_ambra': 'Solari · Ambra',
            'color_corallo': 'Corallo · Caldo',
            'color_giada': 'Giada · Verde',
            'color_cobalto': 'Cobalto · Blu',
            'color_avorio': 'Avorio · Mono',
            'slot_left_name': 'Complicazione in basso',
            'slot_shortcut_name': 'Scorciatoia rapida',
            'slot_weather_name': 'Scorciatoia Meteo',
        },
    ),
    dict(
        slug='palette',
        src=WATCH_PROJECTS / 'WatchFacePalette',
        package='it.e3mcorp.watchface.palette',
        version_code='3',
        version_name='1.2',
        title_en='PALETTE',
        title_it='PALETTE',
        tagline='Split-Flap Tiles & Live Weather',
        strings_en={
            'watch_face_name': 'PALETTE',
            'accent_name': 'Accent Color',
            'color_arancio': 'Orange',
            'color_ottone': 'Brass',
            'color_rosso': 'Red',
            'color_verde': 'Green',
            'color_azzurro': 'Sky Blue',
            'slot_shortcut_name': 'Top Right Shortcut',
            'slot_weather_name': 'Weather Shortcut',
        },
        strings_it={
            'watch_face_name': 'PALETTE',
            'accent_name': 'Colore',
            'color_arancio': 'Arancio',
            'color_ottone': 'Ottone',
            'color_rosso': 'Rosso',
            'color_verde': 'Verde',
            'color_azzurro': 'Azzurro',
            'slot_shortcut_name': 'Scorciatoia rapida',
            'slot_weather_name': 'Scorciatoia Meteo',
        },
    ),
    dict(
        slug='syshud',
        src=WATCH_PROJECTS / 'WatchFace',
        package='it.e3mcorp.watchface.syshud',
        version_code='5',
        version_name='4.1',
        title_en='APEX METEO',
        title_it='Palette Meteo',
        tagline='Vertical Split-Flap & 3-Day Forecast',
        strings_en={
            'watch_face_name': 'APEX METEO',
            'a11y_time': '%1$s hours %2$s minutes',
            'color_warm': 'Amber · Classic',
            'theme_color_name': 'Accent',
            'color_volt': 'Volt · Lime',
            'color_ice': 'Ice · Frost',
            'color_ember': 'Ember · Orange',
            'color_white': 'Titanium · White',
            'color_red': 'Pulse · Red',
            'slot_left_name': 'Left Complication',
            'slot_right_name': 'Right Complication',
            'slot_shortcut_name': 'Bottom Shortcut',
            'slot_weather_name': 'Weather Shortcut',
        },
        strings_it={
            'watch_face_name': 'Palette Meteo',
            'a11y_time': 'Ore %1$s e %2$s minuti',
            'color_warm': 'Ambra · Classico',
            'theme_color_name': 'Accento',
            'color_volt': 'Volt · Lime',
            'color_ice': 'Ice · Ghiaccio',
            'color_ember': 'Ember · Arancio',
            'color_white': 'Titanium · Bianco',
            'color_red': 'Pulse · Rosso',
            'slot_left_name': 'Scorciatoia sinistra',
            'slot_right_name': 'Scorciatoia destra',
            'slot_shortcut_name': 'Scorciatoia centrale',
            'slot_weather_name': 'Scorciatoia Meteo',
        },
    ),
]


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(str(c) for c in cmd)}\n{res.stdout}\n{res.stderr}")
    return res.stdout.strip()


def write_strings_xml(path: Path, mapping: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    root = etree.Element('resources')
    for k, v in mapping.items():
        el = etree.SubElement(root, 'string', name=k)
        el.text = v
    etree.ElementTree(root).write(str(path), encoding='utf-8', xml_declaration=True, pretty_print=True)


def make_shortcut_slot(slot_id, x, y, w, h, display_name, accent_color, circle=False,
                       bg_fill=None, bg_stroke=None, stroke_w='1.4',
                       icon_color='#FFFFFFFF', fallback_res='ic_mic', fallback_sz=22,
                       draw_vector_mic_color=None):
    """Build a schema-valid WFF 2 ComplicationSlot (direct Scene child) for universal Wear OS shortcuts."""
    slot = etree.Element(
        'ComplicationSlot',
        x=str(x), y=str(y), width=str(w), height=str(h),
        slotId=str(slot_id),
        displayName=display_name,
        isCustomizable='TRUE',
        supportedTypes='MONOCHROMATIC_IMAGE SMALL_IMAGE SHORT_TEXT EMPTY',
    )
    etree.SubElement(slot, 'Variant', mode='AMBIENT', target='alpha', value='0')
    if circle:
        etree.SubElement(slot, 'BoundingOval', x='0', y='0', width=str(w), height=str(h))
    else:
        etree.SubElement(slot, 'BoundingRoundBox', x='0', y='0', width=str(w), height=str(h), cornerRadius='13')

    etree.SubElement(
        slot, 'DefaultProviderPolicy',
        defaultSystemProvider='APP_SHORTCUT',
        defaultSystemProviderType='MONOCHROMATIC_IMAGE',
    )

    def paint_bg(parent):
        if bg_fill or bg_stroke:
            pd = etree.SubElement(parent, 'PartDraw', x='0', y='0', width=str(w), height=str(h))
            if circle:
                sh = etree.SubElement(pd, 'Ellipse', x='0', y='0', width=str(w), height=str(h))
            else:
                sh = etree.SubElement(pd, 'RoundRectangle', x='0', y='0', width=str(w), height=str(h),
                                      cornerRadiusX='13', cornerRadiusY='13')
            if bg_fill:
                etree.SubElement(sh, 'Fill', color=bg_fill)
            if bg_stroke:
                etree.SubElement(sh, 'Stroke', color=bg_stroke, thickness=stroke_w)

    ic_x = str(round((w - fallback_sz) / 2))
    ic_y = str(round((h - fallback_sz) / 2))

    # MONOCHROMATIC_IMAGE
    c_mono = etree.SubElement(slot, 'Complication', type='MONOCHROMATIC_IMAGE')
    paint_bg(c_mono)
    pi = etree.SubElement(c_mono, 'PartImage', x=ic_x, y=ic_y, width=str(fallback_sz), height=str(fallback_sz),
                          tintColor=icon_color)
    etree.SubElement(pi, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')

    # SMALL_IMAGE
    c_small = etree.SubElement(slot, 'Complication', type='SMALL_IMAGE')
    paint_bg(c_small)
    sm_sz = round(min(w, h) * 0.62)
    sm_x = str(round((w - sm_sz) / 2))
    sm_y = str(round((h - sm_sz) / 2))
    pis = etree.SubElement(c_small, 'PartImage', x=sm_x, y=sm_y, width=str(sm_sz), height=str(sm_sz))
    etree.SubElement(pis, 'Image', resource='[COMPLICATION.SMALL_IMAGE]')

    # SHORT_TEXT
    c_txt = etree.SubElement(slot, 'Complication', type='SHORT_TEXT')
    paint_bg(c_txt)
    pt = etree.SubElement(c_txt, 'PartText', x='4', y='4', width=str(w - 8), height=str(h - 8))
    tx = etree.SubElement(pt, 'Text', align='CENTER', maxLines='1', ellipsis='TRUE')
    fn = etree.SubElement(tx, 'Font', family='teko_semibold', size='18', weight='SEMI_BOLD', color=icon_color)
    tpl = etree.SubElement(fn, 'Template')
    tpl.text = '%s'
    etree.SubElement(tpl, 'Parameter', expression='[COMPLICATION.TEXT]')

    # EMPTY fallback (crisp vector icon or drawable fallback so the tactile button stays whole before config)
    c_empty = etree.SubElement(slot, 'Complication', type='EMPTY')
    paint_bg(c_empty)
    if draw_vector_mic_color:
        # Clean universal '+' / shortcut badge in vector for syshud which lacks ic_mic png
        pd = etree.SubElement(c_empty, 'PartDraw', x='0', y='0', width=str(w), height=str(h))
        cx, cy = w / 2, h / 2
        for x1, y1, x2, y2 in ((cx - 8, cy, cx + 8, cy), (cx, cy - 8, cx, cy + 8)):
            ln = etree.SubElement(pd, 'Line', startX=str(x1), startY=str(y1), endX=str(x2), endY=str(y2))
            etree.SubElement(ln, 'Stroke', color=draw_vector_mic_color, thickness='3', cap='ROUND')
    else:
        pie = etree.SubElement(c_empty, 'PartImage', x=ic_x, y=ic_y, width=str(fallback_sz), height=str(fallback_sz),
                               tintColor=icon_color)
        etree.SubElement(pie, 'Image', resource=fallback_res)

    return slot


def transform_watchface_xml(slug, xml_path: Path):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    scene = root.find('Scene')

    # 1. Replace Samsung Health explicit launches with official WFF 2 HEALTH_HEART_RATE
    for launch in root.xpath('//Launch'):
        tgt = launch.get('target', '')
        if 'shealth' in tgt:
            launch.set('target', 'HEALTH_HEART_RATE')
        elif 'watch.weather' in tgt:
            launch.getparent().remove(launch)

    # 2. Replace vendor/local recorder button with universal customizable APP_SHORTCUT ComplicationSlot
    if slug == 'nixie':
        for g in root.xpath('//Group[@name="recorder_btn"]'):
            g.getparent().remove(g)
        scene.append(make_shortcut_slot(
            slot_id=1, x=310, y=324, w=62, h=52,
            display_name='slot_shortcut_name',
            accent_color='[CONFIGURATION.theme.2]',
            circle=False, bg_fill=None, bg_stroke=None,
            icon_color='[CONFIGURATION.theme.2]', fallback_res='ic_mic', fallback_sz=22,
        ))
    elif slug == 'solari':
        for g in root.xpath('//Group[@name="recorder"]'):
            g.getparent().remove(g)
        scene.append(make_shortcut_slot(
            slot_id=1, x=322, y=332, w=54, h=54,
            display_name='slot_shortcut_name',
            accent_color='[CONFIGURATION.theme.0]',
            circle=True, bg_fill='[CONFIGURATION.theme.0]',
            icon_color='#FF12141A', fallback_res='ic_mic', fallback_sz=28,
        ))
    elif slug == 'palette':
        for g in root.xpath('//Group[@name="recorder"]'):
            g.getparent().remove(g)
        scene.append(make_shortcut_slot(
            slot_id=0, x=366, y=112, w=68, h=68,
            display_name='slot_shortcut_name',
            accent_color='[CONFIGURATION.accent.0]',
            circle=True, bg_fill='[CONFIGURATION.accent.0]',
            icon_color='#FF14100C', fallback_res='ic_mic', fallback_sz=38,
        ))
    elif slug == 'syshud':
        for g in root.xpath('//Group[@name="flip_group_296"]'):
            g.getparent().remove(g)
        scene.append(make_shortcut_slot(
            slot_id=2, x=199, y=383, w=52, h=52,
            display_name='slot_shortcut_name',
            accent_color='[CONFIGURATION.verticalPalette.0]',
            circle=True, bg_fill='[CONFIGURATION.verticalPalette.0]',
            draw_vector_mic_color='#FF13190A',
        ))
        # Localize hardcoded Italian text inside syshud watchface.xml for global Play Store
        repl = {
            'PASSI': 'STEPS',
            'METEO NON DISPONIBILE': 'WEATHER UNAVAILABLE',
            'PROSSIMI 3 GIORNI · MAX / MIN': '3-DAY FORECAST · MAX / MIN',
            'Da aggiornare · %s · MAX / MIN': 'Updated · %s · MAX / MIN',
            'Domani': '+1 DAY',
            'Tra 2 giorni': '+2 DAYS',
            'Tra 3 giorni': '+3 DAYS',
        }
        for node in root.iter():
            if node.text and node.text.strip() in repl:
                node.text = repl[node.text.strip()]

    etree.indent(root, space='    ')
    for node in root.iter():
        if node.tag in ('Font', 'BitmapFont', 'Upper', 'Template') and len(node):
            if node.tag != 'Template':
                node.text = None
            for inner in node:
                inner.tail = None
    tree.write(str(xml_path), encoding='utf-8', xml_declaration=True)


def validate_app(app_dir: Path):
    face_path = app_dir / 'res/raw/watchface.xml'
    errors = list(SCHEMA.iter_errors(str(face_path)))
    if errors:
        msg = '\n'.join(f'SCHEMA: {e.path}: {e.reason}' for e in errors[:10])
        raise RuntimeError(f'XSD validation failed for {app_dir.name}:\n{msg}')
    face = etree.parse(str(face_path))
    strings = {e.get('name') for e in etree.parse(str(app_dir / 'res/values/strings.xml')).getroot()}
    strings_it = {e.get('name') for e in etree.parse(str(app_dir / 'res/values-it/strings.xml')).getroot()}
    for node in face.xpath('//*[@displayName]'):
        dn = node.get('displayName')
        assert dn in strings, f"missing en string {dn}"
        assert dn in strings_it, f"missing it string {dn}"
    for node in face.xpath('//Font'):
        fam = node.get('family')
        if fam != 'SYNC_TO_DEVICE':
            assert (app_dir / f"res/font/{fam}.ttf").exists(), f"missing font {fam}"
    drawables = {p.stem for p in (app_dir / 'res').glob('drawable*/*') if p.is_file()}
    for node in face.xpath('//*[@resource]'):
        r = node.get('resource')
        if not r.startswith('['):
            assert r in drawables, f"missing drawable {r}"
    groups = [g.get('name') for g in face.xpath('//Group') if g.get('name')]
    assert len(groups) == len(set(groups)), 'duplicate group names'
    return len(face.xpath('//*'))


def build_aab(spec, stage_dir: Path):
    app_dir = stage_dir / 'app'
    build_dir = stage_dir / 'build'
    build_dir.mkdir(parents=True, exist_ok=True)
    res_zip = build_dir / 'compiled_res.zip'
    proto_apk = build_dir / 'proto.apk'
    base_zip = build_dir / 'base.zip'
    aab_out = PLAY_ROOT / f"{spec['package']}.aab"
    if aab_out.exists():
        aab_out.unlink()

    run([str(AAPT2), 'compile', '--dir', str(app_dir / 'res'), '-o', str(res_zip)])
    run([
        str(AAPT2), 'link', '--proto-format',
        '-o', str(proto_apk),
        '--manifest', str(app_dir / 'AndroidManifest.xml'),
        '-I', str(ANDROID_JAR),
        '--min-sdk-version', '34',
        '--target-sdk-version', '35',
        str(res_zip),
    ])

    # Repackage proto.apk into bundle module zip: manifest/AndroidManifest.xml, resources.pb, res/...
    with zipfile.ZipFile(proto_apk, 'r') as zin, zipfile.ZipFile(base_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            target_name = 'manifest/AndroidManifest.xml' if item.filename == 'AndroidManifest.xml' else item.filename
            zout.writestr(target_name, data)

    run([
        'java', '-jar', str(BUNDLETOOL), 'build-bundle',
        f'--modules={base_zip}',
        f'--output={aab_out}',
    ])
    run([
        str(JARSIGNER),
        '-keystore', str(KEYSTORE),
        '-storepass', KS_PASS,
        '-keypass', KS_PASS,
        str(aab_out),
        KS_ALIAS,
    ])
    val_out = run(['java', '-jar', str(BUNDLETOOL), 'validate', f'--bundle={aab_out}'])
    return aab_out, val_out


def _load_square_watch(path: Path):
    return Image.open(path).convert('RGBA')


def _round_crop(im: Image.Image, size: int):
    im = im.resize((size, size), Image.LANCZOS).convert('RGBA')
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 255))
    out.paste(im, (0, 0), mask)
    return out.convert('RGB')


def generate_store_assets(spec, stage_dir: Path):
    assets_dir = stage_dir / 'store_assets'
    assets_dir.mkdir(parents=True, exist_ok=True)
    src = spec['src']
    slug = spec['slug']

    # Pick high-res source previews for each face
    if slug == 'nixie':
        main_im = _load_square_watch(src / 'design/preview-titanium-ambra.png')
        alt_im = _load_square_watch(src / 'design/preview-brass-ambra.png')
        alt2_im = _load_square_watch(src / 'design/preview-titanium-vfd.png')
        aod_im = _load_square_watch(src / 'design/preview-ambient.png')
    elif slug == 'solari':
        main_im = _load_square_watch(src / 'design/preview-ambra.png')
        alt_im = _load_square_watch(src / 'design/preview-corallo.png')
        alt2_im = _load_square_watch(src / 'design/preview-giada.png')
        aod_im = _load_square_watch(src / 'design/preview-ambient.png')
    elif slug == 'palette':
        main_im = _load_square_watch(src / 'design/preview-arancio.png')
        strip = Image.open(src / 'design/preview-themes.png').convert('RGBA')
        w_s = strip.height
        alt_im = strip.crop((w_s, 0, 2 * w_s, w_s))
        alt2_im = strip.crop((3 * w_s, 0, 4 * w_s, w_s))
        aod_im = _load_square_watch(src / 'design/preview-ambient.png')
    else:  # syshud: generate live forecast previews via preview_flip.Renderer!
        import sys
        from datetime import datetime
        sys.path.insert(0, str(src / 'tools'))
        import preview_flip as PF
        now = datetime(2026, 11, 13, 9, 27, 36)
        r_main = PF.Renderer(now, ambient=False, weather=True)
        r_main.data['CONFIGURATION.verticalPalette.0'] = '#FFD5FF45'
        main_im = r_main.render()
        r_warm = PF.Renderer(now, ambient=False, weather=True)
        r_warm.data['CONFIGURATION.verticalPalette.0'] = '#FFFFBE78'
        alt_im = r_warm.render()
        r_ice = PF.Renderer(now, ambient=False, weather=True)
        r_ice.data['CONFIGURATION.verticalPalette.0'] = '#FF9CDCF0'
        alt2_im = r_ice.render()
        aod_im = PF.Renderer(now, ambient=True, weather=False).render()
        sys.path.pop(0)

    # 1. Play Store 512 x 512 App Icon (dark studio tile + centered watch face)
    icon = Image.new('RGB', (512, 512), (10, 11, 14))
    dial_460 = _round_crop(main_im, 468)
    mask_460 = Image.new('L', (468, 468), 0)
    ImageDraw.Draw(mask_460).ellipse([0, 0, 467, 467], fill=255)
    icon.paste(dial_460, (22, 22), mask_460)
    icon.save(assets_dir / 'icon_512.png', optimize=True)

    # 2. Play Store 1024 x 500 Feature Graphic
    feat = Image.new('RGB', (1024, 500), (14, 15, 19))
    d = ImageDraw.Draw(feat)
    # Subtle studio glow behind watch dials
    d.ellipse([26, 20, 474, 468], fill=(24, 26, 32))
    dial_f1 = _round_crop(main_im, 412)
    mask_f1 = Image.new('L', (412, 412), 0)
    ImageDraw.Draw(mask_f1).ellipse([0, 0, 411, 411], fill=255)
    feat.paste(dial_f1, (56, 44), mask_f1)

    dial_f2 = _round_crop(alt_im, 248)
    mask_f2 = Image.new('L', (248, 248), 0)
    ImageDraw.Draw(mask_f2).ellipse([0, 0, 247, 247], fill=255)
    feat.paste(dial_f2, (326, 206), mask_f2)

    def fit_font(text, start_sz, weight, max_w=390):
        sz = start_sz
        while sz >= 16:
            f = ImageFont.truetype(str(FONT_VAR), sz)
            f.set_variation_by_axes([weight])
            if f.getlength(text) <= max_w:
                return f
            sz -= 2
        return f

    tf_title = fit_font(spec['title_en'], 90, 700)
    tf_sub = fit_font(spec['tagline'], 34, 500)
    tf_tag = fit_font('WEAR OS · WATCH FACE FORMAT 2', 24, 500)

    d.text((602, 178), spec['title_en'], font=tf_title, fill=(248, 244, 236), anchor='lm')
    d.text((602, 248), spec['tagline'], font=tf_sub, fill=(196, 198, 206), anchor='lm')
    d.text((602, 302), 'WEAR OS · WATCH FACE FORMAT 2', font=tf_tag, fill=(138, 144, 158), anchor='lm')
    feat.save(assets_dir / 'feature_graphic_1024x500.png', optimize=True)

    # 3. Clean 1080 x 1080 Wear OS round screenshots on pure #000000
    for idx, (lbl, im) in enumerate((('main', main_im), ('theme1', alt_im), ('theme2', alt2_im), ('aod', aod_im)), 1):
        _round_crop(im, 1080).save(assets_dir / f'screenshot_{idx}_{lbl}_1080.png', optimize=True)

    return assets_dir


def stage_project(spec):
    stage_dir = PLAY_ROOT / spec['slug']
    app_dir = stage_dir / 'app'
    if app_dir.exists():
        shutil.rmtree(app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(spec['src'] / 'res', app_dir / 'res')
    # Rewrite AndroidManifest.xml with official it.e3mcorp package
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{spec['package']}"
    android:versionCode="{spec['version_code']}"
    android:versionName="{spec['version_name']}">

    <uses-sdk
        android:minSdkVersion="34"
        android:targetSdkVersion="35" />

    <uses-feature android:name="android.hardware.type.watch" />

    <application
        android:allowBackup="false"
        android:hasCode="false"
        android:icon="@drawable/preview"
        android:label="@string/watch_face_name">

        <property
            android:name="com.google.wear.watchface.format.version"
            android:value="2" />

    </application>
</manifest>
'''
    (app_dir / 'AndroidManifest.xml').write_text(manifest, encoding='utf-8')
    write_strings_xml(app_dir / 'res/values/strings.xml', spec['strings_en'])
    write_strings_xml(app_dir / 'res/values-it/strings.xml', spec['strings_it'])
    transform_watchface_xml(spec['slug'], app_dir / 'res/raw/watchface.xml')
    elem_count = validate_app(app_dir)
    aab_path, val_out = build_aab(spec, stage_dir)
    assets_dir = generate_store_assets(spec, stage_dir)
    print(f"[OK] {spec['package']} -> {aab_path.name} ({aab_path.stat().st_size} bytes, {elem_count} XML elems)")
    return aab_path, assets_dir


if __name__ == '__main__':
    if not KS_PASS:
        KS_PASS = getpass.getpass('Upload keystore password: ')
    for spec in FACES:
        stage_project(spec)
    print('All 4 Play Store AAB bundles built, signed, and validated cleanly.')
