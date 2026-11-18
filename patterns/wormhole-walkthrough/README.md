# wormhole-walkthrough — one set of items, four views, and the jumps between them

## What it does

A presentation design system for explaining where information lives and how it travels. One page shows the
same twelve items four ways, and animates the move from one view to the next so the audience watches the
same things rearrange instead of being shown a new picture:

1. **Tree.** Every item has one home in a folder tree that crosses three stacked layers (a shared base, a
   group layer, a personal layer).
2. **Tags and wormholes.** Items also carry tags. Picking a tag links the matching items across branches and
   layers with a soft liquid tube, a "wormhole". A **gate** (the diamond on a tube) is the point where a
   person approves before anything crosses; the tube waits there until the gate is clicked.
3. **Map.** Riding a tube lands in a relationship map: each item is a node, a line joins two items that
   share a tag, and pulses show where one item's information goes.
4. **Systems.** Six generic system panels (grid sheet, document library, data pipeline, customer record,
   ticket queue, ledger). Items sit inside the systems they live in, and tubes join an item's copies across
   systems.

The picture is general: items can stand for records, files or whole modular systems, tubes for the
connectors between them, and the gate for a permission or approval check on a link.

## The failure it prevents

A diagram of folders says where things are filed; a diagram of connections says what touches what. Shown as
two separate slides, a non-technical audience reads them as two different systems and loses the thread.
Because the items never leave the screen here, "where it lives" and "what it connects to" read as two views
of one thing.

## What it retires

The second and third diagrams, and the spoken "this box is the same as that box on the last slide". It also
retires redrawing: the wording is one block of data, so a new audience needs new labels, not a new drawing.

## Files

| File | What it is |
|---|---|
| `files/walkthrough.html` | The page: all four views and nine numbered stops. One self-contained file with no network calls. |
| `files/plates/plate-1-overview.svg` to `plate-6-overview-dark.svg` | Six still plates with no text, for slides: overview, drill-down, wormhole, filter, component sheet, dark overview. |
| `files/tokens.json` | Colours (light and dark), line weight, corner radius, spacing unit and element sizes of the still plates. |
| `files/slots.json` | For each still plate, every element's position and label area as percentages of width and height, so code can place real labels on top. |
| `files/build_plates.py` | Standard-library Python that draws the six plates and writes both JSON files from one layout. |
| `files/image-plate-recipe/prompts.md` | The prompts and settings that produced a matching set of painted plates from an image-editing model. |

## Install

1. Open `files/walkthrough.html` in a browser. Nothing else is needed to present it.
2. Load your own wording: near the top of the script, edit the `CONTENT` object and nothing else. It holds
   the title, the three layer names, the twelve item labels (`b1`-`b4` base, `g1`-`g4` group, `u1`-`u4`
   personal), the five tag names, the nine stop captions and the `systems` block (the six panel names, which
   drawing each uses, which items live in which system, which system pairs are linked, which link carries
   the gate, and the ride that stop 9 plays).
3. Leave `LAYOUT` (positions, and which item carries which tags) and `TOKENS` (colours and sizes) alone
   unless you mean to change the drawing. `THEME` picks the starting skin: `"vital"` (dark, slow breathing
   motion) or `"calm"` (flat, light).
4. For slides, use the plates in `files/plates/` and place labels from `files/slots.json`. To redraw them,
   run `python3 build_plates.py`; it writes the six plates into `files/plates/` and both JSON files next to
   itself, so the plates and the label positions always describe the same drawing.

## How it is operated

Three interactions, by design, and no control panels: open an item, pick a tag, step through the stops.

- Click or tap an item, a tag chip, a numbered stop, a gate, a tube head or a system panel.
- Right, Left and Space step the stops; `1` to `9` jump to a stop.
- `j` or Enter rides the wormhole from an open item and back; Escape steps back one level.
- `t` switches the skin; `d` flips light and dark.

It is built for a 16:9 shared screen, scales to the window, and honours the reduced-motion setting.

## Prove it

1. Open the page and press `1` through `9`. Each stop must show its caption, and stops 7 to 9 must move the
   same twelve items into the map and into the system panels, not replace them.
2. Click a tag chip. Tubes must grow between the matching items, and one must stop at the diamond until the
   diamond is clicked.
3. Change one label in `CONTENT`, reload, and confirm it changed in the tree, the map and the system panels.
4. Run `python3 build_plates.py` in a scratch copy and confirm the six plates it writes contain no `text`
   elements (`grep -c "<text" plates/plate-*.svg` prints 0 for each).

## The image-plate recipe

`files/image-plate-recipe/prompts.md` records how a matching set of six painted, text-free plates was made
with an image-editing model. The method is the reusable part: render the overview plate once, then make
every other plate by editing that image in place, so the grid never moves and all six line up. The file
also records what did not work.

## Does not do

- It does not read any data source. Every word on the page is typed into `CONTENT`.
- It does not change its counts from `CONTENT`: 3 layers, 4 branches, 12 items, 5 tags and 6 systems are
  fixed. Changing them means editing `LAYOUT`.
- It does not guarantee text fit. The layouts were tuned with short placeholder labels and without a
  rendering tool in the loop; check every view after loading longer labels.
- It does not imitate any product. The six system panels are generic shapes with neutral names; relabel
  them, do not redraw them as a real screen.
- `tokens.json` and `slots.json` describe the still plates; the page carries its own copies in `TOKENS`
  and `LAYOUT`.
