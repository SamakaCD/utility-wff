#!/usr/bin/env python3
"""Generate the Watch Face Format sources for a rebuild of the Pixel Watch
'Utility' (numerique) watch face, Modular II layout.

Geometry is taken from the decompiled res/xml/watch_face_numerique.xml, whose
complication bounds live in a 192x192 space (complicationScaleX/Y="192.0").
WFF uses a 450x450 canvas, so every coordinate is scaled by 450/192.
"""
import os
import shutil

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wff")
CANVAS = 450
SCALE = CANVAS / 192.0


def s(v):
    """Scale a 192-space coordinate onto the 450 canvas."""
    return round(v * SCALE)


# --- geometry, straight from the Modular II ComplicationSlotsOption -----------
# bulbs:     left 18.5..61.5, centre 74.5..117.5, right 130.5..173.5, y 62..105
# long text: 26..166 x, 114..164 y
# Adding a date row on top left the stack crowded upwards: measured margins were
# 14 units at the top against 50 at the bottom, with the ink centroid 56 units
# above the face centre. Dropping the two lower groups evens that out and buys
# back the clock's original size. Modular I -- the layout the original ships a
# date in -- likewise sits its bulbs much lower, so this moves toward it.
LOWER_SHIFT = 23
BULB_Y, BULB_SIZE = s(62) + LOWER_SHIFT, s(105 - 62)
BULBS = [s(18.5), s(74.5), s(130.5)]
LT_X, LT_Y = s(26), s(114) + LOWER_SHIFT
LT_W, LT_H = s(166 - 26), s(164 - 114)

# Modular II has no gap above the clock -- the bulbs start at y=145 -- so making
# room for a date row means giving the clock a smaller box. (The original only
# carries a date in Modular I, where the bulbs sit at y=254 instead.)
DATE_Y, DATE_H, DATE_SIZE = 32, 26, 21
TIME_Y, TIME_H, TIME_SIZE = 60, 104, 100

RING = 10  # measured off the original: stroke is 0.098 of the bulb diameter

# --- colourways, in the exact order and naming of res/xml/four_colorway.xml --
COLORWAYS = [
    ("a02", "#949494", "Graphite"), ("a03", "#e4e4e4", "Cloud"),
    ("a04", "#fcf7eb", "Almond"), ("a05", "#ff7b78", "Watermelon"),
    ("a23", "#f99586", "Coral"), ("a06", "#ffa49f", "Pomelo"),
    ("a36", "#ffc1bd", "Guava"), ("a24", "#fdb78f", "Peach"),
    ("a07", "#ffd4b6", "Champagne"), ("a25", "#d8ab77", "Chai"),
    ("a26", "#c4b575", "Sand"), ("a27", "#f8c67c", "Honey"),
    ("a28", "#ffd88a", "Melon"), ("a08", "#ffe9b9", "Wheat"),
    ("a29", "#fffa86", "Dandelion"), ("a09", "#fcffb6", "Limoncello"),
    ("a37", "#ebffc3", "Lemongrass"), ("a10", "#e6ff7b", "Lime"),
    ("a11", "#c7ff81", "Pear"), ("a16", "#9ff7ad", "Spearmint"),
    ("a31", "#5dd996", "Fern"), ("a15", "#759a8c", "Forest"),
    ("a12", "#abffdf", "Mint"), ("a13", "#beecdb", "Jade"),
    ("a14", "#cce4df", "Sage"), ("a32", "#b0e4ec", "Stream"),
    ("a33", "#8ef1ff", "Aqua"), ("a17", "#c7e9ff", "Sky"),
    ("a18", "#a2c2f7", "Ocean"), ("a19", "#81acf4", "Sapphire"),
    ("a20", "#aeb4ff", "Amethyst"), ("a34", "#d6c3ff", "Lilac"),
    ("a35", "#e4b0fd", "Lavender"), ("a21", "#fabbff", "Flamingo"),
    ("a22", "#ffcaed", "Bubble Gum"),
]
DEFAULT_COLORWAY = [c[0] for c in COLORWAYS].index("a22")

# Fonts lifted from the original APK's assets/.
#
# The clock uses GoogleSansFlexTimeOnly (12 glyphs: digits + colon). That file
# is still a VARIABLE font pinned at wght 300, so the Font element must request
# LIGHT explicitly: WFF otherwise defaults to NORMAL (400) and interpolating
# away from the pinned instance visibly deforms the outlines at clock sizes.
#
# Text uses the static wght-700 instance (the reference shows all
# complication text bold), so no interpolation is possible.
# Its weight is pinned too, to rule out synthetic emboldening. Neither original
# font carries Cyrillic, but the renderer falls back per glyph (verified on
# device), so non-Latin complication text still shows.
TIME_FONT = "google_sans_flex_time"
TIME_FONT_BOLD = "google_sans_flex_time_bold"  # the original's BOLDTIME variant
TEXT_FONT = "google_sans_flex"

# each TimeOnly file is pinned at its own weight, so the Font element has to ask
# for exactly that weight or the outlines deform (see the note above)
TIME_WEIGHTS = {TIME_FONT: "LIGHT", TIME_FONT_BOLD: "SEMI_BOLD"}

# the original defaults BOLDTIME off; --boldtime flips it, to exercise that branch
BOLD_TIME_DEFAULT = "TRUE" if "--boldtime" in __import__("sys").argv else "FALSE"

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
HAVE_FONTS = all(os.path.exists(os.path.join(FONT_DIR, f + ".ttf"))
                 for f in (TIME_FONT, TIME_FONT_BOLD, TEXT_FONT))

# The original's fonts are Google's proprietary typefaces and are not part of
# this repository: run scripts/extract_assets.py against your own copy of the
# Pixel Watch faces APK to place them in fonts/. Without them the watch face
# falls back to the device font, which on a Pixel Watch is Google Sans anyway --
# only the pinned weights and the digits-only clock instance are lost.
if not HAVE_FONTS or "--sysfont" in __import__("sys").argv:
    TIME_FONT = TIME_FONT_BOLD = TEXT_FONT = "SYNC_TO_DEVICE"
    TIME_WEIGHTS = {"SYNC_TO_DEVICE": "NORMAL"}

NEUTRAL = "#ffffff"  # complication text
TRACK_FACTOR = 0.12  # the original's unfilled arc is the accent at 12% value
PLATE = "#1f1f1f"  # filled bulb background


def darken(hexcolor, factor=TRACK_FACTOR):
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


ACCENT = "[CONFIGURATION.accent.0]"
TEXT = "[CONFIGURATION.accent.1]"
TRACK_C = "[CONFIGURATION.accent.2]"

# progress sweep shared by RANGED_VALUE and GOAL_PROGRESS
ARC_START, ARC_SWEEP = -150, 300


def sweep(value, low, high):
    return (
        f"{ARC_START} + (((clamp(({value}), ({low}), ({high})) - ({low}))"
        f" / (({high}) - ({low}))) * ({ARC_SWEEP}))"
    )


def text_part(x, y, w, h, size, expr, color=TEXT, align="CENTER"):
    return ambient(f"""<PartText x="{x}" y="{y}" width="{w}" height="{h}">
  <Text align="{align}" ellipsis="TRUE">
    <Font family="{TEXT_FONT}" size="{size}" weight="BOLD" color="{color}">
      <Template><![CDATA[%s]]><Parameter expression="{expr}"/></Template>
    </Font>
  </Text>
</PartText>""", AMBIENT_ALPHA)


def image_part(x, y, w, h, expr):
    """Plain image, no recolouring -- for SMALL_IMAGE, which is a photo."""
    return (f'<PartImage x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<Image resource="{expr}"/></PartImage>')


def icon(x, y, w, h, expr, color=None):
    """Recolour a complication icon to the colourway.

    tintColor alone cannot do this: it composites multiplicatively, so a light
    accent over a saturated provider icon (Fitbit's green shoe, a red heart)
    leaves it unchanged -- verified on device. Painting a solid accent fill and
    using the icon as a MASK gives a flat silhouette in the accent colour,
    which is what the original does.
    """
    color = color or ACCENT
    return ambient(f"""<Group x="{x}" y="{y}" width="{w}" height="{h}" name="icon">
  <PartDraw x="0" y="0" width="{w}" height="{h}" renderMode="SOURCE">
    <Rectangle x="0" y="0" width="{w}" height="{h}">
      <Fill color="{color}"/>
    </Rectangle>
  </PartDraw>
  <PartImage x="0" y="0" width="{w}" height="{h}" renderMode="MASK">
    <Image resource="{expr}"/>
  </PartImage>
</Group>""", AMBIENT_ALPHA)


# Always-on keeps the whole composition -- same weights, icons in place -- and
# only dims it. The panel dims itself on top of this, and OPR stays far under
# the 15% cap either way, so nothing needs to be dropped.
AMBIENT_ALPHA = 200

# --aod-preview renders the ambient composition in interactive mode, so it can
# be screenshotted and measured -- screencap returns a stale frame while dozing.
AOD_PREVIEW = "--aod-preview" in __import__("sys").argv


def ambient(block, value, base=255):
    """Give a Part*/Group element an alpha that changes in always-on mode.

    Every element built here has an explicit closing tag, so this only has to
    add the attribute and slip a Variant in as the first child.
    """
    if AOD_PREVIEW:
        base, value = value, base
    open_end = block.index(">") + 1
    head = block[:open_end - 1] + f' alpha="{base}">'
    variant = f'\n  <Variant mode="AMBIENT" target="alpha" value="{value}"/>'
    return head + variant + block[open_end:]


def indent(block, spaces):
    pad = " " * spaces
    return "\n".join(pad + line for line in block.splitlines())


def only_if_present(expr, block):
    """Draw block only when expr has data.

    The renderer walks every Complication branch when it builds the highlight
    layer, so an unguarded PartImage whose resource is absent makes
    DWF:ResourceManager log 'Path is empty or null' on every frame.
    """
    return f"""<Condition>
  <Expressions>
    <Expression name="present"><![CDATA[{expr} != null]]></Expression>
  </Expressions>
  <Compare expression="present">
{indent(block, 4)}
  </Compare>
</Condition>"""


# --- bulb slot ---------------------------------------------------------------
B = BULB_SIZE
# PartDraw CLIPS its children to its own bounds (measured on device: a ring
# stroked along an oval that filled the PartDraw lost the outer half of its
# stroke). So every PartDraw here spans the whole bulb, and the oval the ring is
# stroked along is inset by half the stroke instead, which also puts the ring's
# outer edge flush with the bulb bounds as in the original.
# Marker metrics, measured off the original by scanning tangentially through it:
# the white dot is 13 units across, separated from the arc by a 4-unit dark gap
# on each side, which keeps it legible where it overlaps the fill.
DOT = 13
DOT_HALO = 4

# The marker dot is wider than the ring and is centred on the ring's path, so
# it overhangs the bulb bounds and would be clipped flat on its outer side
# (measured: radial extent 9.9px vs 11.2px tangential). Pull the whole ring in
# by that overhang plus a pixel of margin so the dot stays round.
IC = B / 2.0   # centre of the bulb, in PartDraw coordinates
INSET = RING / 2.0 + max(0.0, (DOT - RING) / 2.0 + 1)
IB = B - 2 * INSET  # bounding oval of the ring


def bulb_ring(track_only=False):
    """Full circle track, used by the non-progress complication types.

    Pure decoration, so it drops out entirely in always-on.
    """
    return ambient(f"""<PartDraw x="0" y="0" width="{B}" height="{B}">
  <Ellipse x="{INSET}" y="{INSET}" width="{IB}" height="{IB}">
    <Stroke thickness="{RING}" color="{PLATE if track_only else TRACK_C}"/>
  </Ellipse>
</PartDraw>""", AMBIENT_ALPHA)


def _arc(color, end_expr=None):
    transform = (f'\n    <Transform target="endAngle" value="{end_expr}"/>'
                 if end_expr else "")
    return (f'  <Arc centerX="{IC}" centerY="{IC}" width="{IB}" height="{IB}"'
            f' startAngle="{ARC_START}" endAngle="{ARC_START + ARC_SWEEP}">\n'
            f'    <Stroke thickness="{RING}" color="{color}" cap="ROUND"/>'
            f'{transform}\n  </Arc>')


def bulb_gauge(value, low, high):
    """RANGED_VALUE: proportional fill over the darkened track, plus a marker
    dot at the head of the fill."""
    track = ambient(f'<PartDraw x="0" y="0" width="{B}" height="{B}">\n'
                    f'{_arc(TRACK_C)}\n</PartDraw>', AMBIENT_ALPHA)
    fill = ambient(f'<PartDraw x="0" y="0" width="{B}" height="{B}">\n'
                   f'{_arc(ACCENT, sweep(value, low, high))}\n</PartDraw>',
                   AMBIENT_ALPHA)
    marker = ambient(f"""<PartDraw x="0" y="0" width="{B}" height="{B}">
  <Ellipse x="{IC - DOT / 2 - DOT_HALO}" y="{INSET - DOT / 2 - DOT_HALO}" width="{DOT + 2 * DOT_HALO}" height="{DOT + 2 * DOT_HALO}">
    <Fill color="#ff000000"/>
  </Ellipse>
  <Ellipse x="{IC - DOT / 2}" y="{INSET - DOT / 2}" width="{DOT}" height="{DOT}">
    <Fill color="#ffffffff"/>
  </Ellipse>
  <Transform target="angle" value="{sweep(value, low, high)}"/>
</PartDraw>""", AMBIENT_ALPHA)
    return track + "\n" + fill + "\n" + marker


def bulb_progress(value, low, high):
    """GOAL_PROGRESS: darkened track with the accent filling it, and no marker."""
    track = ambient(f'<PartDraw x="0" y="0" width="{B}" height="{B}">\n'
                    f'{_arc(TRACK_C)}\n</PartDraw>', AMBIENT_ALPHA)
    fill = ambient(f'<PartDraw x="0" y="0" width="{B}" height="{B}">\n'
                   f'{_arc(ACCENT, sweep(value, low, high))}\n</PartDraw>',
                   AMBIENT_ALPHA)
    return track + "\n" + fill


# text + optional icon inside a bulb
TW, TX = B - 26, 13
ICON = 21
VALUE_SIZE = 25


def bulb_content():
    """Value text with the icon below it when the data source supplies one."""
    with_icon = text_part(TX, 33, TW, 30, VALUE_SIZE, "[COMPLICATION.TEXT]") + "\n" + icon(
        round((B - ICON) / 2), 70, ICON, ICON, "[COMPLICATION.MONOCHROMATIC_IMAGE]"
    )
    return f"""<Condition>
  <Expressions>
    <Expression name="hasIcon"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null]]></Expression>
  </Expressions>
  <Compare expression="hasIcon">
{indent(with_icon, 4)}
  </Compare>
  <Default>
{indent(text_part(TX, 36, TW, 30, VALUE_SIZE, "[COMPLICATION.TEXT]"), 4)}
  </Default>
</Condition>"""


def bulb_slot(slot_id, x, name, policy):
    types = ("RANGED_VALUE GOAL_PROGRESS SHORT_TEXT "
             "MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY")
    plate = ambient(f'<PartDraw x="0" y="0" width="{B}" height="{B}">'
                    f'<Ellipse x="0" y="0" width="{B}" height="{B}">'
                    f'<Fill color="{PLATE}"/></Ellipse></PartDraw>', AMBIENT_ALPHA)
    body = "\n".join([
        f'<Complication type="RANGED_VALUE">',
        indent(bulb_gauge("[COMPLICATION.RANGED_VALUE_VALUE]",
                          "[COMPLICATION.RANGED_VALUE_MIN]",
                          "[COMPLICATION.RANGED_VALUE_MAX]"), 2),
        indent(bulb_content(), 2),
        "</Complication>",
        f'<Complication type="GOAL_PROGRESS">',
        indent(bulb_progress("[COMPLICATION.GOAL_PROGRESS_VALUE]", "0",
                             "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]"), 2),
        indent(bulb_content(), 2),
        "</Complication>",
        f'<Complication type="SHORT_TEXT">',
        indent(bulb_ring(), 2),
        indent(bulb_content(), 2),
        "</Complication>",
        f'<Complication type="MONOCHROMATIC_IMAGE">',
        indent(plate, 2),
        indent(only_if_present(
            "[COMPLICATION.MONOCHROMATIC_IMAGE]",
            icon(round((B - 41) / 2), round((B - 41) / 2), 41, 41,
                 "[COMPLICATION.MONOCHROMATIC_IMAGE]")), 2),
        "</Complication>",
        f'<Complication type="SMALL_IMAGE">',
        indent(plate, 2),
        indent(only_if_present(
            "[COMPLICATION.SMALL_IMAGE]",
            image_part(round((B - 61) / 2), round((B - 61) / 2), 61, 61,
                       "[COMPLICATION.SMALL_IMAGE]")), 2),
        "</Complication>",
        f'<Complication type="EMPTY">',
        indent(bulb_ring(track_only=True), 2),
        "</Complication>",
    ])
    return f"""<ComplicationSlot slotId="{slot_id}" x="{x}" y="{BULB_Y}" width="{B}" height="{B}" displayName="{name}" supportedTypes="{types}">
  <BoundingOval x="0" y="0" width="{B}" height="{B}" outlinePadding="2.0"/>
  {policy}
{indent(body, 2)}
</ComplicationSlot>"""


FITBIT = "com.fitbit.FitbitMobile/com.fitbit.complications"
STEPS_POLICY = (
    '<DefaultProviderPolicy'
    f' primaryProvider="{FITBIT}.offloadable.steps.OffloadableStepsComplicationDataSourceService"'
    ' primaryProviderType="GOAL_PROGRESS"'
    ' defaultSystemProvider="STEP_COUNT" defaultSystemProviderType="SHORT_TEXT"/>'
)
HEART_POLICY = (
    '<DefaultProviderPolicy'
    f' primaryProvider="{FITBIT}.offloadable.heartrate.OffloadableHeartRateComplicationDataSourceService"'
    ' primaryProviderType="RANGED_VALUE"'
    ' defaultSystemProvider="HEART_RATE" defaultSystemProviderType="SHORT_TEXT"/>'
)
BATTERY_POLICY = ('<DefaultProviderPolicy defaultSystemProvider="WATCH_BATTERY"'
                  ' defaultSystemProviderType="RANGED_VALUE"/>')


# --- long text slot ----------------------------------------------------------
LT_ICON = 32
LT_PAD = 14
LT_TEXT_X = LT_PAD + LT_ICON + 8
LT_LINE_H = 32
LT_SIZE = 24
LT_TOP = round(LT_H / 2 - LT_LINE_H)  # two stacked lines, centred


def long_text_slot(slot_id, diagnostic=False):
    """The bottom row.

    `diagnostic` swaps the slot over to SHORT_TEXT/STEP_COUNT, which is the only
    data source on the Wear emulator that supplies a title, a text and an icon
    at once. It renders through the same geometry and the same [COMPLICATION.*]
    bindings, so it verifies the row on an image that has no calendar provider.
    """
    ctype = "SHORT_TEXT" if diagnostic else "LONG_TEXT"
    provider = "STEP_COUNT" if diagnostic else "NEXT_EVENT"
    lt_icon = icon(LT_PAD - 8, round((LT_H - LT_ICON) / 2), LT_ICON, LT_ICON,
                   "[COMPLICATION.MONOCHROMATIC_IMAGE]")
    wide = LT_W - LT_PAD * 2
    narrow = LT_W - LT_TEXT_X - LT_PAD

    def two_lines(x, w):
        return (text_part(x, LT_TOP, w, LT_LINE_H, LT_SIZE, "[COMPLICATION.TITLE]",
                          align="START") + "\n" +
                text_part(x, LT_TOP + LT_LINE_H, w, LT_LINE_H, LT_SIZE,
                          "[COMPLICATION.TEXT]", align="START"))

    def one_line(x, w):
        return text_part(x, round((LT_H - LT_LINE_H) / 2), w, LT_LINE_H, LT_SIZE,
                         "[COMPLICATION.TEXT]", align="START")

    body = f"""<Condition>
  <Expressions>
    <Expression name="iconAndTitle"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null && [COMPLICATION.TITLE] != null]]></Expression>
    <Expression name="iconOnly"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null]]></Expression>
    <Expression name="titleOnly"><![CDATA[[COMPLICATION.TITLE] != null]]></Expression>
  </Expressions>
  <Compare expression="iconAndTitle">
{indent(two_lines(LT_TEXT_X, narrow), 4)}
{indent(lt_icon, 4)}
  </Compare>
  <Compare expression="iconOnly">
{indent(one_line(LT_TEXT_X, narrow), 4)}
{indent(lt_icon, 4)}
  </Compare>
  <Compare expression="titleOnly">
{indent(two_lines(LT_PAD, wide), 4)}
  </Compare>
  <Default>
{indent(one_line(LT_PAD, wide), 4)}
  </Default>
</Condition>"""
    empty = (f'<PartDraw x="0" y="0" width="{LT_W}" height="{LT_H}">'
             f'<RoundRectangle x="2" y="2" width="{LT_W - 4}" height="{LT_H - 4}"'
             f' cornerRadiusX="24" cornerRadiusY="24">'
             f'<Stroke thickness="2" color="{PLATE}"/></RoundRectangle></PartDraw>')
    return f"""<ComplicationSlot slotId="{slot_id}" x="{LT_X}" y="{LT_Y}" width="{LT_W}" height="{LT_H}" displayName="complication_bottom" supportedTypes="{ctype} EMPTY">
  <BoundingRoundBox x="0" y="0" width="{LT_W}" height="{LT_H}" outlinePadding="2.0" cornerRadius="24"/>
  <DefaultProviderPolicy defaultSystemProvider="{provider}" defaultSystemProviderType="{ctype}"/>
  <Complication type="{ctype}">
{indent(body, 4)}
  </Complication>
  <Complication type="EMPTY">
{indent(empty, 4)}
  </Complication>
</ComplicationSlot>"""


# --- assembly ----------------------------------------------------------------
def date_row():
    """Day name plus day of month, e.g. "Mon 27".

    TimeText only formats times, so this goes through PartText with the
    [DAY_OF_WEEK_S] / [DAY] sources. The two colours are inline Font runs inside
    one Text, not two PartTexts meeting at the centre -- with separate boxes the
    pair drifts off centre by half the difference of the two widths (measured
    -11 units), whereas a single text flow centres exactly.
    """
    return f"""<PartText x="0" y="{DATE_Y}" width="{CANVAS}" height="{DATE_H}">
  <Text align="CENTER">
    <Font family="{TEXT_FONT}" size="{DATE_SIZE}" weight="BOLD" color="{ACCENT}">
      <Template><![CDATA[%s ]]><Parameter expression="[DAY_OF_WEEK_S]"/></Template>
    </Font>
    <Font family="{TEXT_FONT}" size="{DATE_SIZE}" weight="BOLD" color="{TEXT}">
      <Template><![CDATA[%d]]><Parameter expression="[DAY]"/></Template>
    </Font>
  </Text>
</PartText>"""


def clock(font):
    """The clock, dimmed in always-on but keeping its configured weight."""
    text = ambient(f"""<TimeText format="h:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="0" width="{CANVAS}" height="{TIME_H}">
  <Font family="{font}" size="{TIME_SIZE}" weight="{TIME_WEIGHTS[font]}" width="NORMAL" color="{ACCENT}"/>
</TimeText>""", AMBIENT_ALPHA)
    return (f'<DigitalClock x="0" y="{TIME_Y}" width="{CANVAS}" height="{TIME_H}">\n'
            + indent(text, 2) + '\n</DigitalClock>')


def bold_time_switch():
    """The original's BOLDTIME setting: the same clock in two pinned weights.

    A BooleanConfiguration wraps scene content directly, which is what lets a
    DigitalClock live in each branch -- Condition only accepts Part* children.
    """
    return f"""<BooleanConfiguration id="boldTime">
  <BooleanOption id="TRUE">
{indent(clock(TIME_FONT_BOLD), 4)}
  </BooleanOption>
  <BooleanOption id="FALSE">
{indent(clock(TIME_FONT), 4)}
  </BooleanOption>
</BooleanConfiguration>"""
    return switch


CYR = "Зустріч 14:30"


def cyrillic_probe():
    """Two identical Cyrillic strings, one in the Latin-only original text font
    and one in the device font, to see whether the renderer falls back."""
    def line(y, family, label):
        return f"""<PartText x="0" y="{y}" width="{CANVAS}" height="34">
  <Text align="CENTER">
    <Font family="{family}" size="26" color="#ffffffff">
      <Template><![CDATA[{label}: {CYR}]]></Template>
    </Font>
  </Text>
</PartText>"""
    return ("<Group x=\"0\" y=\"0\" width=\"450\" height=\"450\" name=\"cyr_probe\">\n"
            + indent(line(268, TEXT_FONT, "orig"), 2) + "\n"
            + indent(line(308, "SYNC_TO_DEVICE", "dev"), 2) + "\n"
            + "</Group>")


def watchface_xml(diagnostic=False, cyr=False):
    options = "\n".join(
        f'      <ColorOption id="{i}" displayName="color_{cid}"'
        f' colors="{col} {NEUTRAL} {darken(col)}"/>'
        for i, (cid, col, _) in enumerate(COLORWAYS)
    )
    slots = "\n".join([
        bulb_slot(1, BULBS[0], "complication_left", STEPS_POLICY),
        bulb_slot(2, BULBS[1], "complication_center", BATTERY_POLICY),
        bulb_slot(3, BULBS[2], "complication_right", HEART_POLICY),
        long_text_slot(4, diagnostic),
    ])
    if cyr:
        slots += "\n" + cyrillic_probe()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<WatchFace width="{CANVAS}" height="{CANVAS}" clipShape="CIRCLE">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="10:09:00"/>
  <UserConfigurations>
    <ColorConfiguration id="accent" displayName="accent_label" screenReaderText="accent_label" defaultValue="{DEFAULT_COLORWAY}">
{options}
    </ColorConfiguration>
    <BooleanConfiguration id="boldTime" displayName="bold_time_label" screenReaderText="bold_time_label" defaultValue="{BOLD_TIME_DEFAULT}"/>
  </UserConfigurations>
  <Scene backgroundColor="#ff000000">
{indent(date_row(), 4)}
{indent(bold_time_switch(), 4)}
{indent(slots, 4)}
  </Scene>
</WatchFace>
"""


def strings_xml():
    rows = [
        '  <string name="watch_face_name">Utility</string>',
        '  <string name="accent_label">Colour</string>',
        '  <string name="bold_time_label">Bold Time</string>',
        '  <string name="complication_left">Left</string>',
        '  <string name="complication_center">Centre</string>',
        '  <string name="complication_right">Right</string>',
        '  <string name="complication_bottom">Bottom</string>',
    ]
    rows += [f'  <string name="color_{cid}">{nm}</string>'
             for cid, _, nm in COLORWAYS]
    body = "\n".join(rows)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n{body}\n</resources>\n'


MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.ivan.watchface.utility">

  <uses-feature android:name="android.hardware.type.watch"/>

  <application
      android:label="@string/watch_face_name"
      android:hasCode="false">
    <meta-data
        android:name="com.google.android.wearable.standalone"
        android:value="true"/>
    <property
        android:name="com.google.wear.watchface.format.version"
        android:value="4"/>
  </application>
</manifest>
"""

INFO = """<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
  <Preview value="@drawable/preview"/>
  <Editable value="true"/>
  <MultipleInstancesAllowed value="true"/>
</WatchFaceInfo>
"""


def write_placeholder_preview(path, size=456):
    """A flat black square, enough to satisfy WatchFaceInfo/Preview.

    The original's preview art belongs to Google, so a fresh checkout renders
    its own rather than shipping theirs.
    """
    import struct
    import zlib

    row = bytes(3 * size)
    raw = b"".join(b"\x00" + row for _ in range(size))

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    open(path, "wb").write(png)


def main():
    import sys
    diagnostic = "--diag" in sys.argv
    cyr = "--cyr" in sys.argv
    for d in ("res/raw", "res/xml", "res/values", "res/drawable-nodpi",
              "res/font"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    write = lambda p, c: open(os.path.join(OUT, p), "w").write(c)
    write("AndroidManifest.xml", MANIFEST)
    write("res/raw/watchface.xml", watchface_xml(diagnostic, cyr))
    # Both fonts come straight out of the original APK's assets/.
    fonts = os.path.join(os.path.dirname(OUT), "fonts")
    for ttf in ("google_sans_flex_time.ttf", "google_sans_flex_time_bold.ttf",
                "google_sans_flex.ttf"):
        dst = os.path.join(OUT, "res/font", ttf)
        if not HAVE_FONTS or TIME_FONT == "SYNC_TO_DEVICE":
            if os.path.exists(dst):
                os.remove(dst)
        else:
            shutil.copy(os.path.join(fonts, ttf), dst)
    stale = os.path.join(OUT, "res/font/google_sans_flex_text.ttf")
    if os.path.exists(stale):
        os.remove(stale)
    if diagnostic:
        print("*** DIAGNOSTIC build: bottom slot is SHORT_TEXT/STEP_COUNT ***")
    write("res/xml/watch_face_info.xml", INFO)
    write("res/values/strings.xml", strings_xml())
    # preview_utility.png is the original's art, extracted locally and never
    # committed; assets/preview.png is this project's own render and ships with
    # the repository, so a fresh clone still gets a real preview.
    root = os.path.dirname(OUT)
    dst_preview = os.path.join(OUT, "res/drawable-nodpi/preview.png")
    for candidate in ("preview_utility.png", "assets/preview.png"):
        src = os.path.join(root, candidate)
        if os.path.exists(src):
            shutil.copy(src, dst_preview)
            break
    else:
        write_placeholder_preview(dst_preview)
        print("no preview image found -- wrote a plain placeholder")
    print(f"bulbs y={BULB_Y} size={B} x={BULBS}")
    print(f"long text x={LT_X} y={LT_Y} w={LT_W} h={LT_H}")
    print(f"colourways={len(COLORWAYS)} default={DEFAULT_COLORWAY}"
          f" ({COLORWAYS[DEFAULT_COLORWAY][2]})")
    lines = open(os.path.join(OUT, "res/raw/watchface.xml")).read().count("\n")
    print(f"watchface.xml: {lines} lines")


if __name__ == "__main__":
    main()
