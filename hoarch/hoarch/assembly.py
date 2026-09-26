"""Assembly and print notes for every building in the collection: the text of each kit's
PRINT_NOTES.txt and build guide. ``NOTES[key]`` (the houses) and ``SHOPS[key]`` (the Main
Street shops) are (title, assembly steps, optional extra notes); the shared paragraphs are
COMMON_TOP (printer settings), DECK (planked porch decks) and CORNICE_NOTE (built-up
cornices)."""

COMMON_TOP = """Printer settings (all plates): 0.4 mm nozzle, PLA, 0.20 mm layers (0.16 is the finest these
were designed for). These 3MF files carry geometry only, so Bambu Studio uses your current
process preset:
  SUPPORTS OFF for every plate except the Windows_Doors plate.
  SUPPORTS ON for the Windows_Doors plate only: tree(auto), "On build plate only". Each window
  and door is ONE part: a plug with the glass and sash that pushes into the wall opening, and
  the carved frame on top; the frame prints face-up on supports that touch only its back.
Brim ON (Bambu 'Auto' is fine) for the tall or thin parts: wall shells, roof, porch frames
(posts and railings stand up in one piece), arcades (they print on their top edge), chimneys,
finials, and the flat gable ornaments. Windows and doors are one colour: paint the glass,
sashes and doors after (or colour-paint them in Bambu Studio).
Optional dark glass: on the Windows_Doors plate the first 0.4 mm (two layers) of every window
is its glass. Start that plate in a dark grey or black and change filament once to the frame
colour on the first layer above 0.4 mm (the slider's 0.6 mm layer at 0.20 mm layers: Bambu
Studio swaps before the layer you pick). The glass comes out dark, two layers thick, and
everything above it (sash, frame) in the frame colour. On the doors those two layers are the
back of the leaves, inside the house.
"""

WALLS = """  1. FOUNDATION.
  2. WALLS-1 (the whole first floor) onto the foundation's locating lip.
  3. BELT onto the lip at the top of WALLS-1, then WALLS-2 onto the belt's lip.
  4. Windows and doors: clip off the supports and push each plug into its opening from
     outside; the frame drops into the flat landing cut in the siding."""

DECK = """PORCH-deck is the floor planks, frame, skirt and piers in one piece, on its own PorchDeck
plate. It prints upside down: its first 1.2 mm (6 layers at 0.20) are the planks. Load a wood
brown, and change filament once to the trim colour on the first layer above 1.2 mm (Bambu
Studio: right-click the slider's 1.4 mm layer > Add color change). The hairline cracks between the planks are meant
to be there; they print as dark lines between the boards."""

PORCH = """  - Porch: PORCH-deck (planks, frame, skirt and piers in one piece); the porch frames
    (posts and railings in one piece) drop into the sockets in its planks; arcades on the post
    tops (their tabs drop into the post slots); PORCH-roof, then its tin top; the steps at
    the front."""

SHOPS = {
    "pemberton": ("THE PEMBERTON BLOCK - BRICK COMMERCIAL BLOCK WITH A CAST-IRON STOREFRONT", """  1. FOUNDATION (the granite plinth, with a pad under the shop entry).
  2. WALLS-1 (the whole ground floor, with the brick posts that stand behind the storefront's
     inner columns) onto the foundation's locating lip.
  3. VESTIBULE (the recessed entry with its doors) drops in from above onto the pad, behind
     the entry. Then push the STOREFRONT's plug into the big opening from outside: the V
     notches in its back slide over the brick posts.
  4. SIGN over the storefront, then CORNICE-store above it (the lower double cornice); each
     sits flat in the landing left in the brick.
  5. SILL-COURSE onto the lip at the top of WALLS-1, then WALLS-2 onto its lip.
  6. Windows and doors: push each plug into its opening from outside.
  7. ROOF drops inside the walls onto the ledge; the CHIMNEY stands in its pocket.
  8. FRIEZE, then CORNICE-top (the upper double cornice) on the front parapet; COPING on top of
     the walls; the TABLET stands on the coping at the centre of the front.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN: prints face-up. Black for the board, then at 1.0 mm change to gold: the letters and
    the frame come out gilt on black.
  TABLET (on the Cream plate with the FRIEZE, which is finished by then): at 3.6 mm change to
    gold or a dark colour for the name, date and rim.
"""),
    "barber": ("KELLER'S BARBER SHOP - FALSE-FRONT SHOP ON A BOARDWALK", """  1. FOUNDATION (the timber sill, with a pad under the shop entry).
  2. WALLS (the whole shop in one piece: false front, sides, rear gable and the posts behind
     the storefront's inner columns) onto the sill's locating lip.
  3. VESTIBULE drops in from above onto the pad behind the entry; then push the STOREFRONT's
     plug into its opening from outside (its V notches slide over the posts).
  4. AWNING rail on the flat landing right above the storefront; SIGN above it; FRIEZE (the
     sawn brackets hang from it) and CORNICE on top of the false front; COPING over the top;
     the TABLET stands on the coping.
  5. Windows and doors: push each plug into its opening from outside.
  6. ROOF-L and ROOF-R rest on the walls' sloped tops, their front ends against the back of
     the false front; RIDGE on top; the STOVEPIPE goes down through the hole in ROOF-R.
  7. BOARDWALK along the front; the barber POLE at its curb, left of the door.
""", """Colour changes (optional, each on a plate of its own colour):
  AWNING: prints on its side, so its stripes are bands of height. Start red and change
    filament every 2.2 mm (2.2, 4.4, 6.6 ... 30.8: 14 changes, red and white in turn). Or
    print it in one colour.
  SIGN: red for the board, then at 1.0 mm change to white for the letters and frame.
  TABLET: white, then at 3.6 mm change to navy for the date and rim.
  BOARDWALK: prints upside down. Plank brown for the first 1.2 mm, then change to the frame
    colour (as the porch decks).
  POLE: white with raised helical stripes: paint them red (and blue), or colour-paint them in
    Bambu Studio.
"""),
    "bank": ("THE MERCHANTS BANK - STONE CORNER BANK", """  1. FOUNDATION (the polished granite base); the STEPS stand at the cut corner.
  2. WALLS-1 (the banking hall) onto the foundation's locating lip.
  3. BELT onto the lip at the top of WALLS-1, then WALLS-2 onto the belt's lip (the parapet
     walls on the party wall and the rear are part of it).
  4. Windows and doors: push each plug into its opening from outside; the corner door's temple
     front (pilasters, BANK entablature, pediment) is part of the door.
  5. ROOF drops inside the walls onto the ledge; the SKYLIGHT and the CHIMNEY stand in their
     pockets.
  6. Round the two street fronts and the cut corner: the FRIEZE pieces (lettered), then the
     CORNICE pieces on them (their ends are mitred to meet at the corners), then the
     BALUSTRADE pieces on the wall tops (mitred the same way).
""", """Colour changes (optional):
  FRIEZE plate: prints face-up. Cream for the boards, then at 1.2 mm change to gold: the
    letters (MERCHANTS BANK, 1882, SAVINGS) come out gilt.
"""),
    "general": ("HARTLEY'S GENERAL STORE - FALSE-FRONT STORE WITH A TWO-STOREY GALLERY", """  1. FOUNDATION (stone piers with board skirting, a pad under the shop entry).
  2. WALLS-1 (with the posts behind the storefront's inner columns) onto the foundation's lip.
  3. VESTIBULE drops in from above onto the pad; push the STOREFRONT's plug into its opening
     from outside (its V notches slide over the posts).
  4. BELT onto the lip at the top of WALLS-1, then WALLS-2 (with the false front) onto it.
  5. Windows and doors: push each plug into its opening from outside.
  6. ROOF (corrugated) on the walls' sloped tops, its front end against the back of the false
     front; the CHIMNEY goes down through its hole.
  7. On the false front: SIGN, FRIEZE (dogtooth), CORNICE, and the ARCH board on top.
  8. The gallery: SIDEWALK along the front; GALLERY-lower (posts and beam) stands on it;
     GALLERY-deck on the beam against the belt (it prints upside down); GALLERY-upper (posts
     and railing) on the deck's edge, the two GALLERY-rail ends back to the wall; GALLERY-roof
     from the upper beam up to the flat landing on the wall.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN: green for the board, then at 1.0 mm change to cream for the letters and frame.
  ARCH: cream for the board, then at 0.8 mm change to green for the rim and the date.
  GALLERY-deck: prints upside down. Plank brown for the first 1.2 mm, then change to the
    frame colour (as the porch decks).
"""),
    "drugstore": ("WHITCOMB'S PHARMACY - CORNER DRUGSTORE WITH A TURRET", """  1. FOUNDATION (the bossed stone base) and the STEPS platform at the cut corner.
  2. WALLS-1 (with the brick posts behind the storefronts' middle columns) onto the
     foundation's locating lip.
  3. Push the two storefronts (STORE-FRONT, STORE-SIDE) into their openings from outside
     (their V notches slide over the posts); SIGN-front and SIGN-side above them.
  4. BELT onto the lip at the top of WALLS-1; the CORBEL goes under the belt at the corner,
     on the COLUMN, which stands on the steps platform.
  5. WALLS-2 onto the belt's lip; the TURRET stands on the belt and corbel at the corner,
     its back against the cut-away corner of WALLS-2. TURRET-roof on top, FINIAL in it.
  6. Windows and doors: push each plug into its opening from outside.
  7. ROOF (gravel) drops inside onto the ledge; the CHIMNEY stands in its pocket.
  8. FRIEZE-front / -side and CORNICE-front / -side on the top of the walls (their ends die
     into the turret); COPING on top; the BLADE sign's wall plate on its landing beside the
     turret.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN plate: plum boards, then at 1.0 mm change to cream for the letters and frames.
  BLADE: prints lying flat. Black for the arm and plate, then at 0.8 mm change to gold: the
    mortar and pestle and its Rx come out gold on black.
"""),
    "hotel": ("THE PALACE HOTEL - HOTEL AND SALOON WITH A BRACKETED BALCONY", """  1. FOUNDATION (cobbles).
  2. WALLS-1 onto the foundation's lip; BELT-1; WALLS-2; BELT-2; WALLS-3 (with the false
     front and the rear gable), each onto the lip of the one below.
  3. Windows and doors: push each plug into its opening from outside (the saloon's batwing
     doorway is one part with its SALOON head board).
  4. The BRACKETs on their landings under the second floor; the BALCONY deck on them (it
     prints upside down); RAIL-front along its edge and the two RAIL-end pieces back to the
     wall (they print flat: stand them up).
  5. SIGN, CAP and the CREST on the false front; the VSIGN's two wall plates on their
     landings at the right-hand end.
  6. ROOF-L and ROOF-R on the walls' sloped tops against the back of the false front; RIDGE
     on top; the CHIMNEYs go down through their holes.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN and VSIGN: maroon boards, then at 1.0 mm change to gold for the letters and frames.
  BALCONY: prints upside down. Plank brown for the first 1.2 mm, then change to the frame
    colour (as the porch decks).
"""),
    "bakery": ("VOGEL'S BAKERY - BRICK BAKERY WITH A CROW-STEPPED GABLE", """  1. FOUNDATION (the herringbone brick base).
  2. WALLS (the whole bakery in one piece, with the stepped front gable and the rear gable)
     onto the foundation's locating lip.
  3. Windows and doors: push each plug into its opening from outside.
  4. The COPING caps on the crow steps (the numbers match the steps from the bottom, L and
     R), the crown cap on top; the DATE stone under it; the SIGN over the shop window; the
     BLADE (pretzel) sign's wall plate on its landing beside the window.
  5. ROOF-L and ROOF-R on the walls' sloped tops against the back of the stepped gable;
     RIDGE on top; the CHIMNEY goes down through its hole.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN: green board, then at 1.0 mm change to gold for the letters and frame.
  BLADE: prints lying flat. Black for the arm and plate, then at 0.8 mm change to gold for the
    pretzel.
"""),
    "hardware": ("BASSETT HARDWARE & FEED - STONE STORE WITH A LOADING HOIST", """  1. FOUNDATION (the battered base).
  2. WALLS-1 onto the foundation's lip; BELT (the string course); WALLS-2 (with the front
     parapet and the stepped side parapets) onto the belt's lip.
  3. Windows and doors: push each plug into its opening from outside (the fanlight goes over
     the front doors).
  4. The SHUTTERs beside the upstairs front windows; the HOIST's wall plate over the loading
     door; FRIEZE, CAP and the date PANEL on the front parapet.
  5. ROOF between the side parapets, its front end on the ledge behind the frieze and its
     back on the rear wall.
""", """Colour change (optional):
  FRIEZE: green board, then at 1.0 mm change to cream for the letters and frame.
"""),
    "millinery": ("MADAME DUFRESNE'S MILLINERY - PRESSED-METAL FRONT WITH A FALSE MANSARD", """  1. FOUNDATION (the moulded stone base, with the plinth for the bay and the door steps).
  2. WALLS-1 (the brick sides and rear, open at the front) onto the foundation's lip, then
     FRONT-1 (the lower pressed-metal front) across the open end: it covers the ends of the
     side walls and stands on the base. Glue it to the side walls' ends.
  3. BELT (the ovolo course) onto the lips; WALLS-2 onto the belt's lip; FRONT-2 on the belt
     across the front, glued to the side walls' ends.
  4. BAY: push its back into the big ground-floor opening; it stands on the stone plinth.
     Windows and doors: push each plug into its opening from outside.
  5. SIGN between the stiles over the bay and the door; FRIEZE and CAP at the top of the
     front; the BLADE (hat) sign's wall plate on the right-hand stile, upstairs.
  6. ROOF on the ledge inside the walls; MONITOR on the deck (it sits over the middle);
     CHIMNEY down through its pocket at the back; COPING on the side and rear walls.
  7. MANSARD on the front wall and the cap, its flat back flush with the inside of the
     front wall; DORMER into the notch in the mansard.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN and FRIEZE (one plate): plum board, then at 1.0 mm change to gold for the letters,
    frames and bracket tails.
  BLADE: prints lying flat. Black for the arm and plate, then at 0.8 mm change to gold for the
    hat.
The FRONT parts print face-up (the pressed-metal panels on top), the MANSARD and DORMER on
their flat backs, the BAY standing on its floor.
"""),
    "jeweler": ("ASHWORTH & SONS, JEWELERS - TERRA-COTTA SHOP WITH A STREET CLOCK", """  1. FOUNDATION (the tooled granite base).
  2. WALLS-1 (the brick sides and rear, open at the front) onto the foundation's lip, then
     FRONT-1 (the lower terra-cotta front with the great arch) across the open end: it covers
     the ends of the side walls and stands on the base. Glue it to the side walls' ends.
  3. BELT (the cyma course) onto the lips; WALLS-2 onto the belt's lip; FRONT-2 (with the
     parapet and the oriel's opening) on the belt across the front, glued to the side walls.
  4. SHOPFRONT into the arch from outside; the other windows and doors the same way. ORIEL:
     push its flat back into its opening upstairs; ORIEL-roof on the oriel's cornice against
     the wall.
  5. FRIEZE and CAP at the top of the front; the date PANEL on the parapet over the cap; the
     BLADE (pocket watch) sign's wall plate on the right-hand pier beside the arch.
  6. ROOF on the ledge inside the walls; CHIMNEY down through its pocket at the back; COPING
     on the side and rear walls.
  7. SIDEWALK against the base (the step goes in front of the door); CLOCK on the sidewalk
     near the curb, left of the arch; a DIAL into the round seat on each face of its head.
""", """Colour changes (optional, each on a plate of its own colour):
  FRIEZE: green board, then at 1.0 mm change to gold for the eggs, darts, frame and letters.
  BLADE: prints lying flat. Black for the arm and plate, then at 0.8 mm change to gold for the
    watch.
  DIALs: white discs, then at 0.6 mm change to black for the hands and quarter marks.
The FRONT parts print face-up (the terra cotta on top), the ORIEL and its roof on their flat
backs, the CLOCK standing up (brim on).
"""),
}


CORNICE_NOTE = """Cornices: every storey joint and every eave (and the tower, bay, cupola and ell tops) has a
built-up cornice of at most two parts:
  -lower = the frieze and the course over it, printed upright;
  -upper = the bracketed soffit and the crown, printed upside down (turn it over to fit).
A level with one ring in a pose keeps that ring's name (-frieze, -crown). The prefixes say
where each goes: CORNICE-J between the storeys, CORNICE-E the eave, CORNICE-T the tower or
turret top, CORNICE-B the bay, CORNICE-CUP the cupola, CORNICE-ELL the kitchen ell.
Two-colour parts have ONE filament change, and sit on plates of their own named for it
("..._then_White_at_6.0mm"): load the first colour; the second starts at that height. Bambu
Studio swaps filament before the layer you pick, so pick the first layer above the height (at
0.20 mm layers the slider's 6.2 mm layer for 6.0 mm), right-click > Add color change. The
kits are laid out for 0.20 mm layers; at 0.16 mm pick the layer nearest the height.
Fit each lower part over its plain wall band from above onto the ledge, then the upper part
on it (its brackets hang in front of the frieze); a drop of glue holds each. So fit the
CORNICE-J parts before the storey above goes on, the CORNICE-E parts before the roof, and a
tower's before its roof. A part that wraps a tower comes in pieces (-0, -1, ...) that fit on
from the side; a part cut short by a tower or a lower roof simply stops against it.
"""

JOINTED = """  2. WALLS-1 onto the foundation's lip{w1}.
  3. JOINT (the plain band between the storeys, with the ledge the cornice stands on) onto
     WALLS-1's lip; the CORNICE-J parts round it; then WALLS-2 onto the joint's lip{w2}.
  4. Windows and doors: clip off the supports and push each plug into its opening from
     outside; the frame drops into the flat landing cut in the siding."""

TURNED_PORCH = """PORCH-deck against the base (see the deck note); the PORCH-frames (posts and railings in
     one piece) into the sockets in the planks; the PORCH-arcades on the post tops (their tabs
     drop into the posts' slots); PORCH-roof on them against the walls, then its tin top;
     the PORCH-steps"""

FRIEZE_PORCH = """PORCH-deck against the base (see the deck note); the PORCH-frames (posts and railings in
     one piece) into the sockets in the planks; the PORCH-friezes on the post tops (their tabs
     drop into the posts' slots); PORCH-roof on them against the walls, then PORCH-roof-top;
     the PORCH-steps"""


def _rewrap(text, width=94):
    """Re-flow each numbered step so no line runs past ``width`` (continuations indented 5)."""
    import re
    import textwrap
    out, step = [], []

    def flush():
        if step:
            first = step[0]
            lead = re.match(r"^(\s*)", first).group(1)
            body = " ".join(x.strip() for x in step)
            out.extend(textwrap.wrap(body, width, initial_indent=lead, subsequent_indent=" " * 5))
            step.clear()
    for line in text.split("\n"):
        if re.match(r"^\s*\d+\. ", line) or not line.strip():
            flush()
        if line.strip():
            step.append(line)
        else:
            out.append("")
    flush()
    return "\n".join(out)


def jointed(w1="", w2=""):
    return _rewrap(JOINTED.format(w1=w1, w2=w2))


NOTES = {
    "beaumont": ("THE BEAUMONT - QUEEN ANNE", "  1. FOUNDATION (fieldstone).\n" + jointed(
        " (the first storey, the tower's lower storeys and the bay on the wing)",
        " (the upper storey, the wing gable and the whole tower above the joint)") + """
  5. Bay: the CORNICE-B parts round the bay's top band (they stop at the wing wall); BAY-ROOF
     on them, under the joint.
  6. The CORNICE-E parts round the eave band of the house and the tower (the pieces round the
     tower fit on from the side).
  7. ROOF-main onto the lip at the wall tops, round the tower; ROOF-crest on the ridge cap;
     the CHIMNEYs down into their pockets; the DORMER into its pocket on the west slope (it
     sits flat on its seat), WIN-dormer into its face, DORMER-roof on top; GABLE-trim (the
     sunburst and collar) on the wing gable's shingles over the attic window.
  8. Tower: the CORNICE-T parts round its top band (they stop where the main roof climbs
     past); TOWER-SPIRE on the band's lip; TOWER-FINIAL in its seat at the tip.
  9. Porch (round the front and the west side, past the tower): """ + TURNED_PORCH + """;
     STOOP-back at the back door.
"""),
    "villa": ("THE ASHBY - ITALIANATE VILLA", "  1. FOUNDATION (limestone).\n" + jointed(
        " (the first storey and the kitchen ell)", "") + """
  5. SHUTTERs: glue a pair beside each window (the short pairs upstairs).
  6. Kitchen ell: the CORNICE-ELL parts round the ell's top band; ROOF-ell on the ell's lip,
     up against the house (it runs under the joint cornice, which stops against it).
  7. The CORNICE-E parts round the eave band; ROOF-main onto the lip at the wall tops; the
     CHIMNEYs down into their pockets.
  8. Cupola: CUPOLA-walls on the roof's flat top, its four twin windows, the CORNICE-CUP parts
     round its top band, CUPOLA-roof on the band's lip and the CUPOLA-finial in its seat.
  9. Porch: """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """; STOOP-back at the
     back door of the ell.
"""),
    "harcourt": ("THE HARCOURT - SECOND EMPIRE", "  1. FOUNDATION (rock-faced granite).\n" + jointed(
        " (the first storey, the tower's first storey and the east bay)",
        " (the second storey and the whole tower above the joint)") + """
  5. Bay: the CORNICE-B parts round the bay's top band; BAY-roof (the deck) on them; the
     BAY-crest strips along its edges.
  6. The CORNICE-E parts round the eave band (the piece round the tower slides on from the
     front).
  7. MANSARD (it prints upside down) down over the walls onto the eave's crown, hugging the
     tower; the DORMERs into their notches with their windows and DORMER-hoods; ROOF-curb
     (upside down) on the mansard's top, ROOF-deck into the curb; the CREST strips round the
     deck; the CHIMNEYs in their deck pockets.
  8. Tower: the CORNICE-T parts round its top band; TOWER-CAP (the concave mansard) on the
     band's lip; TOWER-curb and TOWER-deck; the TOWER-crest strips; TOWER-finial.
  9. Portico: """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """; STOOP-back at the
     back door.
"""),
    "fowler": ("THE FOWLER - OCTAGON HOUSE", "  1. FOUNDATION (brick).\n" + jointed() + """
  5. SHUTTERs: glue a pair beside each window.
  6. The CORNICE-E parts round the eave band; ROOF-main onto the lip at the wall tops; the
     two CHIMNEYs in their pockets.
  7. Cupola: CUPOLA-walls on the roof's flat top, its eight windows, the CORNICE-CUP parts
     round its top band, CUPOLA-roof on the band's lip and the CUPOLA-finial in its seat.
  8. Veranda: """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """; STOOP-back at the
     back door.
"""),
    "whitby": ("THE WHITBY - CARPENTER GOTHIC COTTAGE", "  1. FOUNDATION (rubble stone).\n" + jointed(
        "", " (the knee wall and the four gable walls)") + """
  5. The CORNICE-E parts round the eave band, along the eave walls and across the gable ends
     (they stop at the front and back cross gables, whose walls run up through the eave).
  6. ROOF drops between the gable walls onto the lip along the eave walls (it is hollow and
     prints upright); the CHIMNEYs in their ridge pockets.
  7. BARGE boards: glue one to the end of each rake (the two longer boards on the side
     gables, the two steeper ones front and back); the drop and finial sit at the apex.
  8. Porch: """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """; STOOP-back at the
     back door.
"""),
    "delancey": ("THE DELANCEY - SAN FRANCISCO ITALIANATE ROW HOUSE", "  1. FOUNDATION (the rusticated raised basement); the basement windows push into it.\n" + jointed(
        " (the bay with its colonettes is part of it)", "") + """
  5. The CORNICE-E parts round the eave band, round the bay too.
  6. ROOF-deck onto the lip at the wall tops (it covers the crown); the CHIMNEYs in their
     deck pockets; the PARAPET (printed on its back) stands on the deck along the street.
  7. STOOP up to the front door.
"""),
    "ardmore": ("THE ARDMORE - RICHARDSONIAN ROMANESQUE", "  1. FOUNDATION (boulder courses).\n" + jointed(
        " (the first storey, the tower's first storey and the loggia walls)",
        " (the second storey, the front gable and the whole tower above the joint)") + """
  5. The CORNICE-E parts round the eave band of the house and the tower (the pieces round the
     tower fit on from the side).
  6. ROOF onto the lip along the eave walls, round the tower; the CHIMNEYs in their ridge
     pockets.
  7. Tower: the CORNICE-T parts round its top band (they stop where the main roof climbs
     past); TOWER-roof (the cone) on the band's lip; TOWER-finial in its seat.
  8. Entrance loggia: PORCH-floor into the loggia; PORTAL (the great arch, printed on its
     back) round the loggia's arched opening; PORCH-deck on the loggia walls (it prints
     upside down), PORCH-parapet on the deck; STEPS-front and STEPS-back.
"""),
    "merritt": ("THE MERRITT - STICK STYLE", "  1. FOUNDATION (parged).\n" + jointed(
        " (the main block and the wing)", " (with the three gable walls)") + """
  5. The CORNICE-E parts round the eave band, along the eave walls and across the gable ends.
  6. ROOF onto the lip along the eave walls, between the gable walls; the CHIMNEY in its
     pocket.
  7. TRUSSes: glue one to the end of each rake (two for the main gables, the shorter one for
     the wing).
  8. Porch: """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """; STOOP-back at the
     back door.
"""),
    "hollis": ("THE HOLLIS - FOLK VICTORIAN FARMHOUSE", "  1. FOUNDATION (block).\n" + jointed(
        " (the main block and the wing)", " (with the three gable walls and their chevron boarding)") + """
  5. SHUTTERs beside the windows that have room for them.
  6. The CORNICE-E parts round the eave band, along the eave walls and across the gable ends.
  7. ROOF onto the lip along the eave walls; the two CHIMNEYs in their pockets; a GABLE
     (the gingerbread) on each gable's rake end.
  8. Porch (in the corner of the L): """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """;
     STOOP-back at the back door.
"""),
    "carrow": ("THE CARROW - QUEEN ANNE CASTLE", "  1. FOUNDATION (coursed stone).\n" + jointed(
        " (the Roman brick storey with the turret's first storey)",
        " (the half-timbered storey, the front gable and the whole turret above the joint)") + """
  5. The CORNICE-E parts round the eave band of the house and the turret (the pieces round the
     turret fit on from the side).
  6. ROOF onto the lip along the eave walls, round the turret; the CHIMNEY in its pocket;
     GABLE-truss (the arch-braced Tudor truss) on the front gable's rake end.
  7. Turret: the CORNICE-T parts round its top band (they stop where the main roof climbs
     past); TURRET-roof on the band's lip; TURRET-finial in its seat.
  8. Porch (round the front and the west side): """ + TURNED_PORCH.replace("its tin top", "PORCH-roof-tin") + """;
     STOOP-back at the back door.
"""),
    "marigold": ("THE MARIGOLD - TURQUOISE GINGERBREAD COTTAGE", """  1. FOUNDATION (the coquina-stone base).
  2. WALLS (the whole cottage in one piece, with both gables) onto the foundation's lip.
  3. Windows and doors: push each plug into its opening from outside.
  4. The CORNICE-E parts round the eave band (frieze, course, bed, crown), across the gable feet
     too.
  5. GABLE-screen (the lace band) across the foot of the front gable, in its landing;
     GABLE-hood over the gable window.
  6. ROOF onto the lip at the wall tops; CHIMNEY down through its pocket; a BARGE board on
     each gable's rake ends (the medallion under the apex).
  7. Porch: PORCH-deck against the front of the base (see the deck note); a PORCH-post into
     each socket in the planks; the PORCH-rails between the posts (the gap in the middle is
     for the steps); the PORCH-arcades on the post tops; PORCH-roof on the arcades against
     the wall, then PORCH-roof-top; the PORCH-steps at the front, STOOP-back at the back door.
  8. Add-ons: the FLOWERBOXes under the front windows, the ROCKER on the porch.
""", """Colour changes (optional, each on a plate of its own colour):
  FLOWERBOX: turquoise box, then at 2.2 mm change to pink for the flowers.
The bargeboards print face-up, the ROCKER on its side, the arcades on their top edge.
"""),
    "primrose": ("THE PRIMROSE - BUTTER-YELLOW EASTLAKE QUEEN ANNE", "  1. FOUNDATION (the pebble-dash base).\n" + jointed(
        "", " (with the wing's gable)") + """
     Each window has its own small transom of square lights above it.
  5. The CORNICE-E parts round the eave band, across the wing's gable foot too.
  6. ROOF onto the lip at the wall tops; CHIMNEY down through its pocket; the four WALK
     strips round the flat top (front and back first, the sides between them);
     GABLE-ornament on the wing's rake ends.
  7. Porch: PORCH-deck against the base (see the deck note); the PORCH-frames into the
     sockets in the planks; the PORCH-arcades on the post tops; PORCH-roof on them against
     the wall, then PORCH-roof-top; PORCH-pediment on the porch roof over the steps; the
     PORCH-steps; STOOP-back at the back door.
""", """The ROOF prints upright; its flat top is carried on a 45 degree fill inside, so no
supports. The WALK strips and the GABLE-ornament print face-up.
"""),
    "rosecroft": ("THE ROSECROFT - CORAL STICK-STYLE TOWER HOUSE", "  1. FOUNDATION (the banded stone base).\n" + jointed(
        " (the tower and the canted bay are part of it)", "") + """
  5. The bay's roof (BAY-roof) on the bay top, against the wall.
  6. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; a GABLE ornament on the
     rake of each front gable.
  7. Tower: the CORNICE-T parts round its top band; TOWER-gablets (the ring of eight pointed
     gables) on the band's lip; TOWER-crown down into the ring; TOWER-lantern-core (the dark
     octagon) on the crown's flat top and the TOWER-lantern (the teal sleeve) down over it;
     TOWER-spire on top; TOWER-finial on the flat at the spire's tip; TOWER-vane (the arrow)
     on the top of the finial's rod.
  8. Porch (round the tower): """ + FRIEZE_PORCH + """; PORCH-gable on the roof over
     the steps; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-roof print upside down, the GABLE ornaments, the PORCH-gable and
the vane arrow face-up, the friezes on their top edge. The TOWER-gablets, TOWER-crown, lantern,
core and spire print upright; the finial's rod and the gablet spikes are fine, so print them
slowly or glue them with a drop of CA.
"""),
    "twins": ("LAUREL & MYRTLE - SAN FRANCISCO ITALIANATE PAIR", """  1. FOUNDATION (the panelled raised basement under both houses).
  2. Each house (L = the cream Laurel, M = the sage Myrtle): its WALLS-1 onto the foundation's
     lip (the bay with its colonnettes is part of it); its JOINT onto WALLS-1's lip, its
     CORNICE-J parts round it, then its WALLS-2 onto the joint's lip. The two houses meet back
     to back at the party wall.
  3. Windows and doors: push each plug into its opening from outside.
  4. Each house's CORNICE-F part (the frieze and course under the main cornice, in one piece)
     round its top band; each EAVE-roof (the bracketed cornice with the flat roof deck) onto the lip at
     its wall top; each CHIMNEY into the pocket in its deck. The L-PEDIMENT stands on the
     Laurel's cornice over the bay; the M-CRESTING strips stand just inside the Myrtle's
     fascia along the front.
  5. Porticoes: each house's COLUMNs on the stoop landing either side of the door, its
     PORTICO over them against the wall; the M-PORTICO-rail on the Myrtle's portico.
  6. Each STOOP up to its door, each STOOP-back at its back door; the RAILINGs in front of
     the bays.
""", """The EAVE-roofs print upside down: the first 0.8 mm are the roof deck and the fascia's top
fillet, so a filament change there (a dark grey, then the trim colour) gives a dark roof over
a coloured cornice. The PORTICOs print on their backs, the PEDIMENT, CRESTING and RAILINGs
face-up (flat); the columns, the portico rail and the stoops upright.
"""),
    "larkspur": ("THE LARKSPUR - TURQUOISE QUEEN ANNE WITH A LOGGIA", "  1. FOUNDATION (the drafted stone base).\n" + jointed(
        " (the wing and the round tower are part of it)", " (the loggia's floor is in the joint)") + """
  5. LOGGIA (the arcade screen) into the front of the loggia, on its floor, under the eave.
  6. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; GABLE (the pediment
     with the fan) on the wing's rake; DORMER-core into the back of the DORMER, the DORMER
     down into its pocket on the front slope (it sits flat on its seat), DORMER-roof on top.
  7. Tower: the CORNICE-T parts round its top band; TOWER-roof (the bell-cast cone) on the
     band's lip; TOWER-finial on the flat at the tip.
  8. Porch: """ + FRIEZE_PORCH + """; PORCH-pediment on the roof over the steps;
     STOOP-back at the back door.
""", """The PORCH-deck and PORCH-roof print upside down; the LOGGIA, the GABLE and the
PORCH-pediment face-up (on their backs); the friezes on their top edge; the dormer, the tower
roof and the finial upright.
"""),
    "juniper": ("THE JUNIPER - GREEN QUEEN ANNE WITH A ROUND TOWER", "  1. FOUNDATION (the tuckpointed brick base).\n" + jointed(
        " (the round tower's lower storeys are part of it)", " (it carries the tower's top storey)") + """
     WIN-oval (the oval window in its lavender surround) goes into the oval opening beside
     the front doors.
  5. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; the two GABLEs on the
     front and side gable rakes; DORMER-core into the back of the DORMER, the DORMER down
     into its pocket on the front slope, DORMER-roof on top.
  6. Tower: the CORNICE-T parts round its top band; TOWER-roof (the swallowtail cone) on the
     band's lip; TOWER-finial on the flat at the tip.
  7. Porch: """ + FRIEZE_PORCH + """; PORCH-gable on the roof over the steps;
     STOOP-back at the back door.
""", """The PORCH-deck and PORCH-roof print upside down; the GABLEs and the PORCH-gable face-up
(on their backs); the friezes on their top edge; the dormer, the tower roof and the finial
upright.
"""),
    "camellia": ("THE CAMELLIA - PINK QUEEN ANNE WITH A BELL-ROOFED TOWER", "  1. FOUNDATION (the diamond-point base).\n" + jointed(
        " (the round tower, the pavilion and the bay are part of it)",
        " (it carries the tower's top storey and both gables)") + """
  5. Bay: the CORNICE-B parts round the bay's top band; BAY-ROOF on them, under the joint.
  6. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; the two GABLEs on the
     rakes.
  7. Tower: the CORNICE-T parts round its top band; TOWER-roof (the bell) on the band's lip;
     TOWER-finial (the spike) on the flat at the tip.
  8. Porch: """ + FRIEZE_PORCH + """; PORCH-pediment on the roof over the steps;
     STOOP-back at the back door.
  9. Forecourt: the FORECOURT in front of the steps. Each street lamp: drop its LAMP-glass
     into the lantern cage of the LAMP from above, press the LAMP-cap over the four post
     tops, and stand the lamp in its socket at a front corner of the forecourt.
""", """The PORCH-deck and PORCH-roof print upside down; the GABLEs and the PORCH-pediment face-up
(on their backs); the friezes on their top edge; the tower roof, the finial and the lamps
(standard, glass and cap) upright; the forecourt face-up. Print the lamp standards with a brim.
"""),
    "wisteria": ("THE WISTERIA - LAVENDER COTTAGE WITH A CURVED PORCH", """  1. FOUNDATION (the river-stone base).
  2. WALLS onto the foundation's lip (one piece: the cottage, the front wing and all three
     gable walls).
  3. Windows and doors: push each plug into its opening from outside.
  4. The CORNICE-E parts round the eave band, across the gable feet too.
  5. ROOF onto the lip at the wall tops; CHIMNEY down through its pocket at the ridge; the
     three GABLEs (crescent ornaments) on the rakes.
  6. Dormers: DORMER-core into the back of each DORMER, the DORMER down into its pocket on the
     front slope (it sits flat on its seat), then its DORMER-roof on top.
  7. Porch: """ + FRIEZE_PORCH + """; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-roof print upside down; the GABLEs face-up (on their backs); the
friezes on their top edge; the dormers, their roofs and the chimney upright.
"""),
    "hawthorn": ("THE HAWTHORN - EASTLAKE HOUSE WITH A SQUARE TOWER", "  1. FOUNDATION (the ledge-stone base).\n" + jointed(
        " (the square tower's lower storeys are part of it)",
        " (it carries the tower's top storey and the front gable)") + """
  5. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; GABLE (the star
     ornament) on the front gable's rake.
  6. Tower: the CORNICE-T parts round its top band; TOWER-roof (the pyramid) on the band's
     lip; TOWER-finial (the pineapple) on the flat at the tip.
  7. Porch: """ + FRIEZE_PORCH + """; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-roof print upside down; the GABLE face-up (on its back); the
friezes on their top edge; the tower roof, the finial and the chimney upright.
"""),
    "magnolia": ("THE MAGNOLIA - TWIN-GABLED HOUSE WITH AN ENTRY LOGGIA", """  1. FOUNDATION (the V-jointed ashlar base, with the loggia's floor).
  2. WALLS-1 onto the foundation's lip (the brick ground storey, with the loggia sunk into
     its front).
  3. JOINT (the band between the storeys, with the loggia's ceiling) onto WALLS-1's lip; the
     CORNICE-J parts round it (they run on over the loggia); then WALLS-2 onto the joint's lip
     (the shingled upper storey and both front gables).
  4. LOGGIA (the arcade screen) into the front of the loggia, on its floor, under the joint.
  5. Windows and doors: push each plug into its opening from outside (the front doors are
     in the back wall of the loggia).
  6. The CORNICE-E parts round the eave band; ROOF onto the lip at the wall tops; CHIMNEY
     down through its pocket; the two GABLEs (arcade ornaments) on the front gables' rakes.
  7. STEPS up to the loggia at the front, STOOP-back at the back door.
""", """The LOGGIA and the GABLEs print face-up (on their backs); the walls, the joint, the roof and
the chimney upright.
"""),
    # ---- the third batch: Colonial
    "whitmore": ("THE WHITMORE - GEORGIAN COLONIAL", """  1. FOUNDATION (English-bond brick under a moulded water table).
  2. WALLS-1 onto the foundation's lip (the two box bays are part of it). Round each bay's top
     the CORNICE-B parts (the reeded frieze, then the copper crown); a BAY-roof on each, against
     the wall under the joint.
  3. JOINT onto WALLS-1's lip; the CORNICE-J parts round it (they stop either side of the
     portico); then WALLS-2 onto the joint's lip (the pediment's gable wall is part of it).
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the round-headed French window over the portico and the oculus in the pediment too); a
     pair of SHUTTERs beside each shuttered window.
  5. The portico: PORTICO-floor against the front of the pavilion; the two PORTICO-pilasters
     flat on the wall either side of the door; the two PORTICO-columns on the floor;
     PORTICO-roof on the columns and pilasters against the wall; the three BALCONY-rail runs on
     its deck (the front, then the two returns); STEPS-front.
  6. The CORNICE-E parts round the eave band; PEDIMENT (the white tympanum with its raking
     cornices) on the gable wall round the oculus.
  7. ROOF onto the lip at the wall tops; a CHIMNEY into each end pocket; each DORMER-core into
     its DORMER, the DORMERs into their pockets on the front slope, a DORMER-roof on each.
  8. STOOP-back at the back door.
""", """The PORTICO-roof and the cornices' upper parts print upside down; the columns upright (brim
on); the pilasters, the balcony rails and the PEDIMENT flat on their backs; the dormers, the
chimneys and the roof upright.
"""),
    "westbrook": ("THE WESTBROOK - COLONIAL REVIVAL WITH A BOWED PORTICO", """  1. FOUNDATION (rubble under a dressed cap).
  2. WALLS-1 onto the foundation's lip (the west wing is part of it); the CORNICE-W parts round
     the wing's top; ROOF-wing on it, against the main wall under the joint.
  3. JOINT onto WALLS-1's lip; the CORNICE-J parts round it (they stop at the wing's roof and
     behind the portico); then WALLS-2 onto the joint's lip.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the fanlit entrance and the French doors under the portico, the pair onto the balcony);
     a pair of SHUTTERs beside each shuttered window.
  5. The portico: PORTICO-floor against the front (see the deck note); the six PORTICO-columns
     on it; PORTICO-roof on the columns against the wall; BALCONY-rail on its edge (its two
     straight ends run back to the wall); STEPS-front.
  6. The CORNICE-E parts round the eave band; ROOF onto the lip at the wall tops; a CHIMNEY
     into each pocket at the ridge; each DORMER-core into its DORMER, the DORMERs into their
     pockets, a DORMER-roof on each.
  7. STOOP-back at the back door.
""", """The PORTICO-roof and the PORTICO-floor print upside down; the columns and the balustrade
upright (brim on); the dormers, the chimneys and the roof upright.
"""),
    "pennock": ("THE PENNOCK - PENNSYLVANIA FIELDSTONE COLONIAL", """  1. FOUNDATION (dry-laid ledgestone).
  2. WALLS-1 onto the foundation's lip (the kitchen ell at the back is part of it). Round the
     ell's top the CORNICE-ELL parts (the whirl frieze, then the white crown); ELL-gable on
     the ell's north wall top, between the cornice ends.
  3. JOINT onto WALLS-1's lip; the CORNICE-J parts round it (they stop either side of the
     ell's roof); then WALLS-2 onto the joint's lip (both gable walls are part of it).
  4. PENT-S, the pent roof, across the front on the joint cornice, its back against WALLS-2.
  5. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the front door's hood and consoles are part of it); a pair of SHUTTERs beside each
     shuttered window, their strap hinges on the outer sides.
  6. The CORNICE-E parts round the eave band (across the gable feet too); PENT-E and PENT-W
     on the cornice across each gable foot.
  7. ROOF onto the lip at the wall tops; a CHIMNEY into each end pocket; each DORMER-core into
     its DORMER, the DORMERs into their pockets on the front slope, a DORMER-roof (tin) on each.
  8. ELL-roof onto the ell's lip, against the back wall; ELL-chimney into its pocket.
  9. STOOP against the front under the door, STEPS-front in front of it, a SETTLE either side
     of the door on the stoop; STOOP-back and STOOP-ell at the back doors.
""", """The cornices' upper parts print upside down; the pents print as they sit (the soffit on the
bed); the DORMER-roofs stand on their front ends; the settles, the dormers, the chimneys,
the stoop and the roofs upright. The datestone (J P 1768) is carved in the west gable.
"""),
    "oakhurst": ("THE OAKHURST - SOUTHERN COLONIAL WITH A GIANT PORTICO", """  1. FOUNDATION (the raised red-brick basement with its arched vents).
  2. WALLS-1 onto the foundation's lip (the east wing is part of it). Round the wing's top the
     CORNICE-W parts (the lotus frieze, then the white crown); TERRACE-deck onto the wing's
     lip (see the deck note); the three TERRACE-rail runs on its edge (the long sides first).
  3. JOINT onto WALLS-1's lip; the CORNICE-J parts round it (they stop either side of the
     terrace); then WALLS-2 onto the joint's lip.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the entrance, the French doors onto the balcony and the terrace); a pair of SHUTTERs
     beside each shuttered window.
  5. BALCONY on the joint cornice over the entrance; its three BALCONY-rail runs on it.
  6. The CORNICE-E parts round the eave band (they stop at the portico).
  7. The portico: PORTICO-base against the basement, PORTICO-floor on it (see the deck note),
     STEPS-front; the four PORTICO-columns on the floor; PORTICO-beam on the columns, its ends
     against the wall; the CORNICE-P parts round the beam; PORTICO-ceiling up inside the beam.
  8. ROOF onto the lip at the wall tops (its front runs out over the portico as the
     pediment's roof); PEDIMENT on the beam under it; a CHIMNEY into each pocket; each
     DORMER-core into its DORMER, the DORMERs into their pockets on the end slopes, a
     DORMER-roof on each.
  9. CUPOLA into the pocket on the ridge, CUPOLA-dome on it, CUPOLA-finial on top.
 10. STOOP-back at the back door.
""", """The PORTICO-floor, the TERRACE-deck and the PORTICO-ceiling print upside down; the columns
upright (brim on); the railings, the balustrade runs and the PEDIMENT flat on their backs;
the beam, the cupola, the dome, the dormers, the chimneys and the roof upright.
"""),
    "vantassel": ("THE VAN TASSEL - DUTCH COLONIAL WITH A GAMBREL ROOF", """  1. FOUNDATION (field boulders under a sandstone sill).
  2. WALLS onto the foundation's lip: the whole storey of sandstone and both shingled gable
     ends in one part (two colours: see its plate name).
  3. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the quarter-round lights in the gables too); a pair of SHUTTERs beside each shuttered
     window.
  4. The CORNICE-E parts round the eave band (across the gable feet too).
  5. ROOF onto the lip at the wall tops: the gable walls slip up inside its ends, the kick
     sweeps out over the porch. A CHIMNEY into each pocket at the ends of the ridge.
  6. DORMER-core into the DORMER, the DORMER into its pocket on the back slope, DORMER-roof on it.
  7. The porch: PORCH-base against the front, PORCH-deck on it (see the deck note), the six
     PORCH-posts on the deck, PORCH-beam on the posts under the kick; STEPS-front.
  8. STOOP-back at the back door.
""", """The ROOF prints standing on its west end (its section is the same all along, so the kick
and the eaves need no support); the PORCH-deck upside down; the DORMER-roof lying on its
underside; the posts, the walls, the dormer and the chimneys upright.
"""),
    "hathaway": ("THE HATHAWAY - NEW ENGLAND SALTBOX", """  1. FOUNDATION (split granite).
  2. WALLS-1 onto the foundation's lip (the lean-to behind is part of it); the CORNICE-L parts
     round the lean-to's eave (three sides).
  3. JOINT onto WALLS-1's lip at the front block; the CORNICE-J parts round it; WALLS-2 onto the
     joint's lip (both front gables are part of it).
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the swan-neck doorway at the front, the attic lights in the gables).
  5. The CORNICE-E parts round the front eave band (across the gable feet too).
  6. A LEAN-gable on the top of each of the lean-to's end walls, against the front block.
  7. ROOF onto the lips at the wall tops (it runs from the front eave over the ridge and all the
     way down the catslide to the lean-to's eave); CHIMNEY into the pocket at the ridge.
  8. STOOP-front and STOOP-back (granite steps) at the doors.
""", """The ROOF prints standing on its west end; the cornices' upper parts upside down; the walls,
the lean-to's gables and the chimney upright.
"""),
    "chatham": ("THE CHATHAM - CAPE COD", """  1. FOUNDATION (tabby: lime and oyster shell).
  2. WALLS onto the foundation's lip: the whole storey, both gables and the east wing in one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the hooded windows, the cross-and-bible doors, the lights in the gables); a pair of
     SHUTTERs beside each shuttered window.
  4. The CORNICE-E parts round the main eave band (across the west gable's foot; they stop where
     the wing meets the house); the CORNICE-W parts round the wing's eave.
  5. ROOF onto the lip at the wall tops; CHIMNEY into the pocket at the ridge; each DORMER-core
     into its DORMER, the three DORMERs into their pockets on the front slope, a DORMER-roof on
     each.
  6. WING-roof onto the wing's lip, against the east gable.
  7. STOOP-front (the millstone) under the front door, STOOP-back at the back door.
""", """The cornices' upper parts print upside down; the walls, the roofs, the dormers, the chimney
and the millstone step upright.
"""),
    "winthrop": ("THE WINTHROP - GARRISON COLONIAL", """  1. FOUNDATION (galleted stone: chips of flint pressed into the joints).
  2. WALLS-1 onto the foundation's lip: the brick lower storey (rat-trap bond) in one part.
  3. JOINT onto WALLS-1: the girt. At the front it runs out 5 mm past the brick wall; that
     overhang (the jetty) carries the upper storey.
  4. WALLS-2 onto the JOINT's lip: the clapboard upper storey and both gables in one part.
  5. The six DROPs (turned acorns) under the jetty's edge: two at the corners, four between the
     windows.
  6. Windows and doors: clip off the supports and push each plug into its opening from outside
     (segmental-arched lights below, key-capped lights above, small lights in the gables, a
     Tudor-arched door front and back).
  7. The CORNICE-J parts round the joint, the CORNICE-E parts round the eave band; each ring is in
     two halves that meet the chimneys at the gable ends.
  8. ROOF onto the lip at the wall tops.
  9. The two CHIMNEYs stand on the ground against the gables, up through the notches in the rakes.
 10. STOOP-front and STOOP-back (stone steps) at the doors.
""", """The cornices' upper parts and the acorn drops print upside down; the walls, the roof and the
chimneys print upright.
"""),
    "ellsworth": ("THE ELLSWORTH - COLONIAL REVIVAL WITH A TOWER", """  1. FOUNDATION (cobblestones in rows).
  2. WALLS-1 onto the foundation's lip: the whole first storey and the tower's first storey in one
     part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the second storey and the tower's upper two
     stages in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (divided-sash windows below, six-over-one windows above, round-headed lights in the tower,
     the leaded doorway front and back). The two TOWER-panels go on the bare fields of the
     tower's top stage.
  5. The CORNICE-J parts round the storey joint (tower included), the CORNICE-E parts round the
     eave (they stop against the tower), the CORNICE-T parts round the tower's top.
  6. ROOF onto the lip at the wall tops; CHIMNEY into its pocket; each DORMER-core into its DORMER,
     the DORMERs into their pockets, a DORMER-roof on each and a DORMER-urn in the gap of each
     broken pediment.
  7. TOWER-roof onto the tower's cornice, the TOWER-finial on its neck.
  8. The porch: PORCH-deck against the foundation; the PORCH-frames (pedestals, columns and
     railings) into the sockets in the deck; the PORCH-friezes into the slots at the column
     tops; PORCH-roof on top, PORCH-roof-top on it; PORCH-pediment over the steps; the steps.
  9. STOOP-back at the back door.
""", """The cornices' upper parts, the porch deck and the porch roof print upside down; the walls,
the roofs, the tower roof, the dormers, the urns, the chimney and the porch frames print
upright; the porch friezes print on their top edges.
"""),
}

ZIPNAME = {"villa": "Ashby_Villa", "beaumont": "Beaumont_Queen_Anne", "harcourt": "Harcourt_Second_Empire"}

NOTES = {k: (v[0], _rewrap(v[1])) + tuple(v[2:]) for k, v in NOTES.items()}
