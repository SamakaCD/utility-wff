# Notes

## Things worth knowing about Watch Face Format

Collected while building this face; each one cost a debugging round trip.

| | |
|---|---|
| `align="LEFT"` is not valid | Use `START` / `CENTER` / `END`. An invalid value silently falls back to `CENTER`. |
| `PartDraw` clips its children | A ring stroked along an oval that fills the `PartDraw` loses the outer half of its stroke. Give the `PartDraw` the full slot and inset the oval instead. |
| `tintColor` needs format version ≥ 3 for expressions | With `version=2` a literal colour tints but `[CONFIGURATION.x.0]` is silently ignored. |
| `tintColor` composites multiplicatively | It cannot recolour a saturated provider icon. Paint a solid fill and use the icon as a `renderMode="MASK"` sibling instead. |
| `blendMode` is element-vs-canvas | `SRC_IN` there clips the whole complication away; it is not a tint mode. |
| `TimeText` formats time only | Dates come from `[DAY_OF_WEEK_S]`, `[DAY]`, `[MONTH_S]` inside a `PartText` template. |
| One `Text` may hold several `Font` runs | The way to mix colours in one centred line. Two side-by-side `PartText` boxes drift off centre by half the difference of their widths. |
| `BooleanConfiguration` can wrap scene content | `BooleanOption` children may contain a `DigitalClock`; `Condition` accepts only `Part*` elements. |
| Partially-instanced variable fonts deform | `GoogleSansFlexTimeOnly_wght_300…ttf` still carries `fvar`/`gvar`. WFF asks for `NORMAL` (400) by default, and interpolating away from the pinned instance visibly wrecks the outlines. Pin `weight` to the file's own value. |
| Favourites remember slot bindings | Changing a `DefaultProviderPolicy` has no effect until the favourite is recreated; a full uninstall is the reliable reset. |
| `screencap` is stale while dozing | It returns the last composited frame. Force a redraw first, or read the always-on composition with `gen_wff.py --aod-preview`. |
| A WFF face is set by package, not component | `--es watchFaceId <package>`; the `--ecn component` form used for legacy faces fails with `FavoriteOperationException: Watch face package is not installed`. |

## Why the original cannot simply be sideloaded

`WatchFacesBlockingManagerImpl.isBlockedWatchFace()` in WearServices:

```java
if (watchFaceId.getClassName() != null) {         // legacy watch face
    if (checkPermission("com.google.wear.permission.BYPASS_COMPLICATIONS_RESTRICTION", pkg) == 0)
        return false;
    if (!allowlist.contains(sha256(signingPublicKey)))
        return true;                              // blocked
}
return false;
```

The signature allowlist is only consulted for faces identified by a service
class name. Watch Face Format faces have none, so the check never runs.

## Complication data sources

Steps and heart rate default to Fitbit's `GOAL_PROGRESS` and `RANGED_VALUE`
sources, which is what gives those rings an arc. The system `STEP_COUNT` and
`HEART_RATE` sources only offer `SHORT_TEXT`, which renders a plain ring — so
without Fitbit installed the arcs disappear.

The two ring styles differ deliberately, matching the original: `GOAL_PROGRESS`
is a two-tone fill with no marker, `RANGED_VALUE` adds a dot at the head of the
fill. The unfilled part of a ring is the accent colour at 12 % value, not a
neutral grey.

## Always-on

Every part carries a `Variant mode="AMBIENT" target="alpha"`, so always-on is the
same composition at a lower alpha — nothing is removed and the clock keeps its
configured weight. On-pixel ratio measured on device: 6.4 % interactive against
4.7 % ambient, well under the 15 % ceiling.

Content is dimmed only modestly on purpose. The panel already dims itself and
does so *adaptively* via the ambient light sensor, so a fixed low alpha would
make always-on unreadable in daylight. `AMBIENT_ALPHA` in `gen_wff.py` is the
knob.

Sideloaded packages cannot hold `com.google.wear.permission.DISPLAY_OFFLOAD`, so
always-on is drawn by the normal renderer rather than the hardware offload path.
The log lines about it on entering ambient are expected.

## Tools

None of these need image libraries.

| | |
|---|---|
| `tools/opr.py` | on-pixel ratio of a frame, against the 15 % always-on ceiling |
| `tools/balance.py` | vertical centroid of the lit pixels and its distribution |
| `tools/stroke.py` | stroke thickness normalised by digit height |
| `tools/crop.py` | crop and upscale a region for inspection |
| `tools/pair.py` | two frames side by side with centre and centroid guides |
| `scripts/watch.sh` | activate the face on a watch and pull a screenshot |
| `scripts/ab.sh` | capture an interactive/always-on pair, recording wakefulness |
| `scripts/shot.sh` | capture a frame that is guaranteed to be interactive |

The adb scripts take the watch's serial from `WATCH`.
