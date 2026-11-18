# Final prompts and settings

## Model

Nano Banana Pro (`nano_banana_pro`), chosen from the 52 entries in Higgsfield's image catalog on 2026-11-17.

1. Higgsfield's catalog tags it for diagrams, and its recommender ranked it first for this brief.
2. Tested: first render had no characters anywhere and the exact counts asked for (3 layers, 4 folders, 10 items, 6 stops).
3. It edits a reference image in place. Measured against plate 1, the grid in plates 2, 3, 4 and 6 moved by at most 0.04 percent of the canvas width, which is what makes the plates match.

Not used: Nano Banana 2.1 (the one test was rejected by Higgsfield's safety filter, a false positive), OpenAI Hazel (no 16:9), Recraft V4.1 (no reference images), GPT Image 2.6 (not tested, the free queue allowed one job per hour).

## Settings, all plates

| Setting | Value |
|---|---|
| Model | `nano_banana_pro` |
| Aspect ratio | 16:9 |
| Resolution | 2K. Native output is 2752 x 1536. Delivered files are cropped to exact 16:9 at 2720 x 1530 (16 px off each side, 3 px off top and bottom, same crop on every plate). |
| Negative prompt | This model has no separate field. The last paragraph of each prompt is the negative prompt. |
| Seed | Not exposed by this model. |
| Reference images | Passed as `image_references`, in the order listed under each plate. |
| Cost | 0 credits. Run on the free unlimited allowance, which caps at 2K. 4K is 4 credits per plate. |

## Plate 1: overview, light

Three passes.

Pass 1, no reference:

```
A clean flat vector diagram for a presentation slide, 16:9, light theme, viewed straight on with no perspective. Modern minimalist, calm, lots of empty space. Thin precise lines of one weight, rounded rectangles with one corner radius, flat solid fills.

Palette: cool greys only. Off-white background #F6F7F9, very light grey panels, white cards with a hairline grey outline, mid-grey lines #AEB6C2, slate-grey folder icons #7F8A9B. No other colour.

Composition:
- The upper-left corner of the canvas stays empty.
- Header row: a small slate-grey dot at upper centre. A thin line descends from it to a thin horizontal line, which connects down to exactly four small slate-grey folder icons spaced evenly in one row. Each folder icon is a solid rounded rectangle with a short tab.
- Below the header: exactly three wide horizontal panels of identical size, arranged one above another with equal small gaps, edges aligned. The upper panel is the lightest grey, the middle panel slightly darker, the lower panel slightly darker again. The left fifth of each panel stays empty.
- From each folder icon a thin straight vertical line runs down across all three panels: four parallel vertical lines.
- Cards: small white rounded rectangles, all the same size, each centred on a vertical line within a panel. Exactly ten cards: the lower panel has four (one on every vertical line); the middle panel has three (on the first, second and fourth lines); the upper panel has three (on the first, third and fourth lines). Each card is plain white and empty, except for one or two tiny tag chips (small light-grey lozenges with fully rounded ends) along its lower edge.
- At the far right, beside the panels, one narrow vertical bar with fully rounded ends in mid grey, as tall as the three panels together.
- One faint thin dashed light-grey line winds gently across the whole diagram from the upper left to the lower right, crossing all three panels, with exactly six small empty circles spaced evenly along it (white fill, thin grey outline).

The image has no text: no letters, no numerals, no labels, no symbols, no placeholder lines. No gradients, no shadows, no glow, no 3D, no charts, no buttons, no toolbars.
```

Pass 2, reference: pass 1. Fixes the connector band, which had rendered two-tone like a scrollbar.

```
Edit the reference image. Keep the canvas, the straight-on view, and the size, position, colour and line weight of every shape exactly as they are. Make only these four changes:

1. The tall narrow bar at the far right becomes one single flat shape: a capsule filled entirely with one solid mid grey #AEB6C2 from its upper end to its lower end, same size, position and outline as now. No lighter section, no darker section, no inner shape, no gradient. It must not look like a scrollbar.
2. The six small circles on the dashed line become about twice as large in diameter, each staying centred where it is now. They remain empty: white fill, thin grey outline, nothing inside.
3. The dashed line begins a little inside the left edge of the canvas instead of running off the edge, and ends just before the bar.
4. In the upper panel, the left cell gets exactly the same fill colour as the rest of that panel.

Everything else is untouched. The image has no text: no letters, no numerals, no labels, no symbols.
```

Pass 3, reference: pass 2. Restores the light-to-dark layer steps and enlarges the stop circles.

```
Edit the reference image. Keep the canvas, the straight-on view, and the size, position, colour and line weight of every shape exactly as they are. Make only these two changes:

1. The upper panel (the first of the three large panels) becomes lighter: fill the whole panel, both its left cell and its main area, with one flat very light grey #E9EAEE. It must be clearly lighter than the middle panel. Its outline, its divider line and everything drawn on it stay as they are.
2. Each of the six circles on the dashed line becomes larger: its diameter about half the height of a card. Centres stay where they are. They remain empty: white fill, thin grey outline, nothing inside.

Everything else is untouched, including the solid grey bar on the right. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Plate 2: drill-down

Reference: plate 1 final.

```
Edit the reference image. Keep the canvas, the straight-on view, the grid, and the size and position of every shape exactly as they are. Keep the three panels, the bar on the right and all grey colours unchanged.

Changes:
1. Remove the dashed line and its six white circles completely, restoring the panels, lines and cards behind them.
2. The second folder from the left is open: recolour that folder icon solid amber #F2994A. Its vertical line and the header line joining it to the dot at the top stay dark and crisp.
3. The two cards on that second vertical line (one in the middle panel, one in the lower panel) stay crisp white with their tag chips. The one in the middle panel is selected: give it a solid amber #F2994A outline about twice the normal outline weight. Its fill stays white.
4. Everything on the other three vertical lines recedes: those three folder icons, their vertical lines, their cards and their tag chips fade to a very pale version, about a quarter of normal contrast, as if at 25 percent opacity. The parts of the header line that lead only to those folders fade the same way.

Amber is the only colour added. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Plate 3: wormhole

Reference: plate 1 final.

```
Edit the reference image. Keep the canvas, the straight-on view, the grid, and the size and position of every shape exactly as they are. Keep all grey colours unchanged. Nothing is dimmed.

Changes:
1. Remove the dashed line and its six white circles completely, restoring the panels, lines and cards behind them.
2. One tag is active. On exactly four cards, one tag chip turns solid teal #0F8587: the card on the first vertical line in the upper panel, the card on the second vertical line in the middle panel, the card on the third vertical line in the lower panel, and the card on the fourth vertical line in the upper panel. All other tag chips stay light grey.
3. Join these four cards in that order with exactly three links. Each link is a soft, translucent, water-like tube in teal: a smooth ribbon of even width, about one and a half times as thick as a tag chip is tall, filled with flat teal #0F8587 at roughly 40 percent opacity, so the panels, lines and card outlines beneath stay visible through it. Each tube flows out of the right-hand edge of the card it starts from, like liquid leaving the card, bends in one smooth gentle curve, and ends at the next card in a rounded drop-shaped tip, slightly wider than the tube, that just touches that card's edge. The liquid feel comes only from the shape. Flat fill, soft edges, no outline, no highlights, no gloss, no glow, no shadow.
4. On the third tube (the long one that rises from the lower panel to the upper panel), at its midpoint, place one gate marker on top of the tube: a small diamond (a square turned 45 degrees, corners slightly rounded), about one third as tall as a card, white fill, dark slate #3B4350 outline about twice the normal line weight, empty inside.
5. The tall bar at the far right turns solid teal #0F8587, still one flat shape.

Teal and the dark slate outline of the diamond are the only additions. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Plate 4: filter

References, in order: plate 1 final, plate 3.

```
Edit the first reference image. Use the second reference image only to match the teal accent colour and the look of a teal tag chip.

Changes:
1. Remove the dashed line and its six white circles completely.
2. Ghost the whole diagram: every panel, line, folder icon, card, tag chip, the dot at the top and the tall bar on the right fades to a barely visible pale version, about 15 percent of normal contrast, as if seen through a sheet of frosted white. Positions do not change.
3. In front, centred on the canvas at mid height, add one tidy row: a white rounded-rectangle tray with a thin dark outline, holding exactly four white cards side by side, evenly spaced. These four cards are in the same style as the cards in the diagram (plain white, thin dark outline, rounded corners, tag chips along the lower edge) and about one and a half times their size. On each of the four cards one tag chip is solid teal, the same teal as in the second reference; any other chip on it stays light grey. The tray and its four cards are crisp and at full contrast.
4. Just above the upper-left corner of the tray, one solid teal capsule-shaped chip, a little larger than the chips on the cards, empty: the chosen tag.

No tubes, no diamond, no other additions. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Plate 5: component sheet

Two passes.

Pass 1, references in order: plate 1 final, plate 2, plate 3.

```
Create a component sheet in exactly the visual style of the reference images: same colours, same thin dark outlines, same corner radius, same flat fills. Plain background in the same off-white as the references. Ten separate elements arranged in a tidy grid of five columns and two rows, evenly spaced. Each element sits alone, centred in its own cell, with generous empty space around it and an empty area beneath it. No frames, boxes or divider lines around the cells.

First row, left to right:
1. One slate-grey folder icon, as in the references.
2. One white card with a thin dark outline and two light-grey capsule-shaped tag chips along its lower edge.
3. One short wide rounded-rectangle panel in very light grey with a thin dark outline.
4. One light-grey capsule-shaped tag chip, enlarged enough to see clearly.
5. One narrow vertical bar with fully rounded ends in mid grey.

Second row, left to right:
6. One short translucent teal tube exactly like the tubes in the reference: a smooth gently curved ribbon of translucent teal ending in a rounded drop-shaped tip at one end.
7. One white diamond with a thick dark slate outline, empty, like the one in the reference.
8. One white circle with a thin grey outline, empty.
9. One white card with a thick solid amber outline, like the selected card in the reference, with a tag chip along its lower edge.
10. One card with tag chips, faded to a very pale version, like the receded cards in the reference.

Nothing else on the sheet. The image has no text: no letters, no numerals, no labels, no symbols.
```

Pass 2, reference: pass 1 only. Flattens the tag chip, redraws the connector band and outlines the layer plane. A try with two references (pass 1 plus plate 1) merged the two images, so pass one reference.

```
Edit the reference image, which is a sheet of ten separate elements in two rows of five. Keep the canvas, the background, and the size, position and look of all ten elements exactly as they are. Do not add, remove or move anything. Make only these three small corrections, all in the first row:

1. Fourth element (the large capsule shape): make it perfectly flat. One solid light grey fill #DDDBE3, with no outline, no dark edge, no shading, no bevel and no highlight.
2. Fifth element (the narrow vertical bar): redraw it in the same place as one clean capsule with crisp, sharp edges, filled with one solid mid grey #B3B5C2. No blur, no smear, no double edge, no gradient.
3. Third element (the pale rounded rectangle): give it a thin dark slate outline #5E5E6E, the same weight as the outline of the white card next to it, and a flat very light grey fill #E8E9ED.

The second row stays exactly as it is: the teal tube, the diamond, the circle, the card with the amber outline and the pale card. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Plate 6: overview, dark

Reference: plate 1 final.

```
Recolour the reference image into a dark theme. Keep every shape, size, position and line exactly identical: same canvas, same straight-on view, same grid, same panels with their divider lines, same cards and tag chips, same folder icons, same bar, same dashed line and the same six circles. Change colours only.

New colours:
- Background: deep charcoal slate #14171C.
- The three panels: three close dark greys, upper #1C2129, middle #222831, lower #282F39, each with a thin mid-grey outline #6B7686.
- Cards: dark slate #323A46 with a thin light-grey outline #8A94A3. Tag chips on the cards: mid slate #55606F.
- All tree lines (the vertical lines and the header lines): thin mid grey #6B7686.
- Folder icons and the dot at the top: light slate #9AA5B5.
- The tall bar on the right: one flat mid grey #6B7686.
- The dashed line: faint grey #4A5361.
- The six circles: filled with the background colour #14171C, with a thin light-grey outline #9AA5B5, empty inside.

Flat colours only. No glow, no gradients, no shadows, no highlights. The image has no text: no letters, no numerals, no labels, no symbols.
```

## Optional video: one tube grows, pauses at the diamond, then finishes

| Setting | Value |
|---|---|
| Model | Seedance 2.5 (`seedance_2_5`), mode `omni_reference` |
| Start frame | `video-start-frame.png`: plate 3 with the gated tube removed and the diamond left in place, passed as `start_image` |
| End frame | Plate 3 (`plate-3-wormhole.png`), passed as `end_image` |
| Duration | 7 seconds |
| Aspect ratio, resolution | 16:9, 720p on the free allowance, 1080p with credits |
| Audio | Off (`generate_audio: false`) |
| Cost | 0 credits |

The start frame was made by editing the pixels of plate 3 directly, so everything except the removed tube is identical to the end frame. To make it inside Higgsfield instead, use this prompt with plate 3 as the reference (not used here):

```
Edit the reference image. Remove only the long tube that carries the diamond (the one rising from the lower panel to the upper panel), completely, including its drop-shaped tip, restoring the panels, lines and cards behind it. Keep the white diamond exactly where it is. Keep the other two tubes, the teal tag chips, the teal bar and everything else identical. The image has no text.
```

Video prompt:

```
Static locked-off shot of this flat diagram. Nothing moves except one translucent teal tube, identical in colour, width and softness to the two tubes already in the picture. It wells out of the right-hand edge of the card on the third vertical line in the lower panel like calm liquid and grows forward along one smooth path, led by a rounded drop-shaped tip. When the tip reaches the white diamond it stops and holds still for about two seconds. Then it flows on past the diamond and finishes when its tip touches the card on the fourth vertical line in the upper panel. The diamond stays in place on top of the tube. The motion is slow, even and calm, like liquid in a flat animation. No camera movement, no zoom, no parallax, no glow, no splashes, no ripples, no bubbles, no lighting change, no new elements, no text.
```

Timing: 0 to 2.5 seconds grow to the diamond, 2.5 to 4.5 hold, 4.5 to 6.5 flow on to the far card, 6.5 to 7 rest.
