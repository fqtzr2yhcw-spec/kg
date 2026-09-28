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
Brim ON (Bambu 'Auto' is fine) for the tall or thin parts: wall shells, roof, the porch tops
(they print upside down on the roof's flat top, the posts and railings standing up), chimneys,
finials, and the flat gable ornaments and lace. Windows and doors are one colour: paint the glass,
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

SHOPS = {
    "pemberton": ('THE PEMBERTON BLOCK - BRICK COMMERCIAL BLOCK WITH TWO CAST-IRON STOREFRONTS', """  1. FOUNDATION (the granite plinth, with a pad under each shop entry).
  2. WALLS-1 (the whole ground floor, with the brick posts that stand behind the storefronts'
     inner columns) onto the foundation's locating lip.
  3. VESTIBULE and VESTIBULE-2 (the recessed entries with their doors) drop in from above onto
     the pads, behind the entries. Then push each STOREFRONT's plug into its opening from
     outside: the V notches in its back slide over the brick posts.
  4. SIGN (DRY GOODS) and SIGN-2 (BOOTS & SHOES) over the storefronts, then CORNICE-store
     above them (the lower double cornice); each sits flat in the landing left in the brick.
  5. SILL-COURSE onto the lip at the top of WALLS-1, then WALLS-2 onto its lip.
  6. Windows and doors: push each plug into its opening from outside.
  7. ROOF drops inside the walls onto the ledge; the CHIMNEY stands in its pocket.
  8. FRIEZE, then CORNICE-top (the upper double cornice) on the front parapet; COPING on top of
     the walls; the TABLET stands on the coping at the centre of the front.
""", """Colour changes (optional, each on a plate of its own colour):
  SIGN and SIGN-2: print face-up. Black for the board, then at 1.0 mm change to gold: the
    letters and the frame come out gilt on black.
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
     the false front; RIDGE on top; the STOVEPIPE down into its socket in the roof jack on ROOF-R.
  7. BOARDWALK along the front; the barber POLE into its socket at the curb, left of the door.
""", """Colour changes (optional, each on a plate of its own colour):
  AWNING: prints on its side, so its stripes are bands of height. Start red and change
    filament every 2.2 mm (2.2, 4.4, 6.6 ... 52.8: 24 changes, red and white in turn). Or
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
     on the COLUMN, which stands in the recess in the steps platform (its head pegs up into
     the corbel).
  5. WALLS-2 onto the belt's lip; the TURRET stands on the belt and corbel at the corner,
     its back against the cut-away corner of WALLS-2. TURRET-roof (its finial printed on it) on top.
  6. Windows and doors: push each plug into its opening from outside.
  7. ROOF (gravel) drops inside onto the ledge; the CHIMNEY stands in its pocket.
  8. FRIEZE-front / -side and CORNICE-front / -side on the top of the walls (their ends die
     into the turret); COPING on top; the BLADE sign's tongue into its slot in the wall beside the
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
  5. SIGN, CAP and the CREST on the false front; the VSIGN's tongue into its slot and its wall plates on their
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
     BLADE (pretzel) sign's tongue into its slot in the wall beside the window.
  5. ROOF-L and ROOF-R on the walls' sloped tops against the back of the stepped gable;
     RIDGE on top (its underside fits the two slopes); the CHIMNEY goes down through its hole.
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
  4. The SHUTTERs beside the upstairs front windows; the HOIST's tongue into its slot over the loading
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
     front; the BLADE (hat) sign's tongue into its slot in the right-hand stile, upstairs.
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
     BLADE (pocket watch) sign's tongue into its slot in the right-hand pier beside the arch.
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

TURNED_PORCH = """PORCH-deck against the base (see the deck note); PORCH-top (the porch roof, beams, posts and
     railings in one piece, so no post is glued on its own) lowered onto the deck: the square
     peg under each post drops into its socket in the planks (a drop of glue in each socket, out
     of sight) and its back edge meets the wall under the eave; then its tin top; the
     PORCH-steps"""

LACE = """; the PORCH-lace pieces (the arches, flat) against the face of the beam and posts, each
     glued by its whole flat back (the mitred ends meet at the corner posts)"""


def top_porch(tin="", lace=False):
    """The one-piece porch-top steps: ``tin`` names the separate tin piece ("" when the tin is
    printed with the top, as its one colour change); ``lace`` adds the applied arches."""
    t = TURNED_PORCH.replace("; then its tin top", f"; {tin} on top of it, glued over its whole face" if tin else "")
    return t.replace("; the\n     PORCH-steps", (LACE if lace else "") + "; the\n     PORCH-steps")


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
            out.extend(textwrap.wrap(body, width, initial_indent=lead, subsequent_indent=" " * 5,
                                     break_on_hyphens=False))
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
     past); TOWER-SPIRE (its finial printed on it) on the band's lip.
  9. Porch (round the front and the west side, past the tower): """ + top_porch("PORCH-roof-cap (the standing-seam tin)") + """;
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
     round its top band, CUPOLA-roof (its finial printed on it) on the band's lip.
  9. Porch: """ + top_porch("PORCH-roof-tin (the seamed tin)") + """; STOOP-back at the
     back door of the ell.
"""),
    "harcourt": ("THE HARCOURT - SECOND EMPIRE", "  1. FOUNDATION (rock-faced granite).\n" + jointed(
        " (the first storey, the tower's first storey and the east bay)",
        " (the second storey and the whole tower above the joint)") + """
  5. Bay: the CORNICE-B parts round the bay's top band; BAY-roof (the deck) on them; the
     BAY-crest strips into the grooves along its edges.
  6. The CORNICE-E parts round the eave band (the piece round the tower slides on from the
     front).
  7. MANSARD (it prints upside down) down over the walls onto the eave's crown, hugging the
     tower; the DORMERs into their notches with their windows and DORMER-hoods; ROOF-curb
     (upside down) on the mansard's top, ROOF-deck into the curb; the CREST strips round the
     deck; the CHIMNEYs in their deck pockets.
  8. Tower: the CORNICE-T parts round its top band; TOWER-CAP (the concave mansard) on the
     band's lip; TOWER-curb and TOWER-deck (its finial printed on it); the TOWER-crest strips.
  9. Portico: """ + top_porch("PORCH-roof-tin (the seamed tin)") + """; STOOP-back at the
     back door.
"""),
    "fowler": ("THE FOWLER - OCTAGON HOUSE", "  1. FOUNDATION (brick).\n" + jointed() + """
  5. SHUTTERs: glue a pair beside each window.
  6. The CORNICE-E parts round the eave band; ROOF-main onto the lip at the wall tops; the
     two CHIMNEYs in their pockets.
  7. Cupola: CUPOLA-walls on the roof's flat top, its eight windows, the CORNICE-CUP parts
     round its top band, CUPOLA-roof (its finial printed on it) on the band's lip.
  8. Veranda: """ + top_porch() + """; STOOP-back at the
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
  8. Porch: """ + top_porch() + """; STOOP-back at the
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
     past); TOWER-roof (the cone, its finial printed on it) on the band's lip.
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
  8. Porch: """ + top_porch() + """; STOOP-back at the
     back door.
"""),
    "hollis": ("THE HOLLIS - FOLK VICTORIAN FARMHOUSE", "  1. FOUNDATION (block).\n" + jointed(
        " (the main block and the wing)", " (with the three gable walls and their chevron boarding)") + """
  5. SHUTTERs beside the windows that have room for them.
  6. The CORNICE-E parts round the eave band, along the eave walls and across the gable ends.
  7. ROOF onto the lip along the eave walls; the two CHIMNEYs in their pockets; a GABLE
     (the gingerbread) on each gable's rake end.
  8. Porch (in the corner of the L): """ + top_porch() + """.
  9. Back porch (along the back of the wing, its steps at the back door): the same with the BPORCH
     parts.
"""),
    "carrow": ("THE CARROW - QUEEN ANNE CASTLE", "  1. FOUNDATION (coursed stone).\n" + jointed(
        " (the Roman brick storey with the turret's first storey)",
        " (the half-timbered storey, the front gable and the whole turret above the joint)") + """
  5. The CORNICE-E parts round the eave band of the house and the turret (the pieces round the
     turret fit on from the side).
  6. ROOF onto the lip along the eave walls, round the turret; the CHIMNEY in its pocket;
     GABLE-truss (the arch-braced Tudor truss) on the front gable's rake end.
  7. Turret: the CORNICE-T parts round its top band (they stop where the main roof climbs
     past); TURRET-roof (its finial printed on it) on the band's lip.
  8. Porch (round the front and the west side): """ + top_porch() + """;
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
  7. Porch: """ + top_porch("PORCH-roof-tin (the flat tin sheet)", lace=True) + """;
     STOOP-back at the back door.
  8. Add-ons: the FLOWERBOXes under the front windows, the ROCKER on its mat on the porch.
""", """Colour changes (optional, each on a plate of its own colour):
  FLOWERBOX: turquoise box, then at 2.2 mm change to pink for the flowers.
  PORCH-top: prints upside down on its flat roof, the posts standing up. Gold for the roof
    and its scalloped fascia, then at 4.4 mm change to orange for the beams, posts and
    railings. The railings' hand rails are short bridges between the posts.
The bargeboards (2.2 mm thick, with 1.2 mm ties between every accent: blunt quatrefoils, a
solid apex round the medallion, thick scroll feet, the finial on a block) and the lace arches
print face-up, lying flat; the ROCKER on its side.
"""),
    "primrose": ("THE PRIMROSE - BUTTER-YELLOW EASTLAKE QUEEN ANNE", "  1. FOUNDATION (the pebble-dash base).\n" + jointed(
        "", " (with the wing's gable)") + """
     Each window has its own small transom of square lights above it.
  5. The CORNICE-E parts round the eave band, across the wing's gable foot too.
  6. ROOF onto the lip at the wall tops; CHIMNEY down through its pocket; the four WALK
     strips round the flat top (front and back first, the sides between them);
     GABLE-ornament on the wing's rake ends.
  7. Porch: """ + top_porch() + """; PORCH-pediment on the porch roof over the steps;
     STOOP-back at the back door.
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
     TOWER-spire (the finial printed on its tip) on top; TOWER-vane (the arrow on its stem): the
     stem plugs 5.5 mm down into the socket in the finial.
  8. Porch (round the tower): """ + top_porch("PORCH-roof-tin", lace=True) + """; PORCH-gable on the roof over
     the steps; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-top print upside down, the GABLE ornaments, the PORCH-gable, the
PORCH-lace and the vane (arrow and stem) face-up. The TOWER-gablets, TOWER-crown, lantern,
core and spire print upright; the gablet spikes are fine, so print them slowly.
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
  5. Porticoes: each house's COLUMNs in the recesses in the stoop landing either side of the
     door (the peg on each capital goes up into its pocket under the portico), its
     PORTICO over them against the wall; the M-PORTICO-rail on the Myrtle's portico.
  6. Each STOOP up to its door, each STOOP-back at its back door; the RAILINGs in front of
     the bays (the long run's end tongues into the stoop's cheek, the short return's into the
     basement).
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
  7. Tower: the CORNICE-T parts round its top band; TOWER-roof (the bell-cast cone, its
     finial printed on it) on the band's lip.
  8. Porch: """ + top_porch(lace=True) + """; PORCH-pediment on the roof over the steps;
     STOOP-back at the back door.
""", """The PORCH-deck and PORCH-top print upside down; the LOGGIA, the GABLE, the PORCH-pediment
and the PORCH-lace face-up (on their backs); the dormer, the tower
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
  6. Tower: the CORNICE-T parts round its top band; TOWER-roof (the swallowtail cone,
     its finial printed on it) on the band's lip.
  7. Porch: """ + top_porch(lace=True) + """; PORCH-gable on the roof over the steps;
     STOOP-back at the back door.
""", """The PORCH-deck and PORCH-top print upside down; the GABLEs, the PORCH-gable and the
PORCH-lace face-up (on their backs); the dormer, the tower roof and the finial
upright.
"""),
    "camellia": ("THE CAMELLIA - PINK QUEEN ANNE WITH A BELL-ROOFED TOWER", "  1. FOUNDATION (the diamond-point base).\n" + jointed(
        " (the round tower, the pavilion and the bay are part of it)",
        " (it carries the tower's top storey and both gables)") + """
  5. Bay: the CORNICE-B parts round the bay's top band; BAY-ROOF on them, under the joint.
  6. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; the two GABLEs on the
     rakes.
  7. Tower: the CORNICE-T parts round its top band; TOWER-roof (the bell, its spike
     finial printed on it) on the band's lip.
  8. Porch: """ + top_porch() + """; PORCH-pediment on the roof over the steps;
     STOOP-back at the back door.
  9. Forecourt: the FORECOURT in front of the steps. Each street lamp: drop its LAMP-glass
     into the lantern cage of the LAMP from above, press the LAMP-cap over the four post
     tops, and stand the lamp in its socket at a front corner of the forecourt.
""", """The PORCH-deck and PORCH-top (its frieze included) print upside down; the GABLEs and the
PORCH-pediment face-up (on their backs); the tower roof, the finial and the lamps
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
  7. Porch: """ + top_porch(lace=True) + """; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-top print upside down; the GABLEs and the PORCH-lace face-up (on
their backs); the dormers, their roofs and the chimney upright.
"""),
    "hawthorn": ("THE HAWTHORN - EASTLAKE HOUSE WITH A SQUARE TOWER", "  1. FOUNDATION (the ledge-stone base).\n" + jointed(
        " (the square tower's lower storeys are part of it)",
        " (it carries the tower's top storey and the front gable)") + """
  5. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip at
     the wall tops, round the tower; CHIMNEY down through its pocket; GABLE (the star
     ornament) on the front gable's rake.
  6. Tower: the CORNICE-T parts round its top band; TOWER-roof (the pyramid, its
     pineapple finial printed on it) on the band's lip.
  7. Porch: """ + top_porch(lace=True) + """; STOOP-back at the back door.
""", """The PORCH-deck and PORCH-top print upside down; the GABLE and the PORCH-lace face-up (on
their backs); the tower roof, the finial and the chimney upright.
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
     flat on the wall either side of the door; PORTICO-top (the entablature, deck and both
     columns in one piece, so no column is glued on its own) lowered onto the floor, each
     column's foot into its recess, its back against the wall and the pilasters; the three
     BALCONY-rail runs on its deck (the front, then the two returns); STEPS-front.
  6. The CORNICE-E parts round the eave band; PEDIMENT (the white tympanum with its raking
     cornices) on the gable wall round the oculus.
  7. ROOF onto the lip at the wall tops; a CHIMNEY into each end pocket; each DORMER-core into
     its DORMER, the DORMERs into their pockets on the front slope, a DORMER-roof on each.
  8. STOOP-back at the back door.
""", """The PORTICO-top (on its flat deck, the columns standing up; brim on) and the cornices' upper
parts print upside down; the pilasters, the balcony rails and the PEDIMENT flat on their backs; the dormers, the
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
  5. The portico: PORTICO-floor against the front (see the deck note); PORTICO-top (the curved
     entablature, deck and all six columns in one piece, so no column is glued on its own)
     lowered onto it, each column's foot into its recess in the planks, its ends against the
     wall; BALCONY-rail on its edge (its two straight ends run back to the wall); STEPS-front.
  6. The CORNICE-E parts round the eave band; ROOF onto the lip at the wall tops; a CHIMNEY
     into each pocket at the ridge; each DORMER-core into its DORMER, the DORMERs into their
     pockets, a DORMER-roof on each.
  7. STOOP-back at the back door.
""", """The PORTICO-top (on its flat deck, the columns standing up; brim on) and the PORTICO-floor
print upside down; the balustrade upright; the dormers, the chimneys and the roof upright.
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
  5. BALCONY on the joint cornice over the entrance; its three BALCONY-rail runs into the
     grooves along its edges.
  6. The CORNICE-E parts round the eave band (they stop at the portico).
  7. The portico: PORTICO-base against the basement, PORTICO-floor on it (see the deck note),
     STEPS-front; the four PORTICO-columns, each foot into its recess in the floor;
     PORTICO-beam on the columns (the peg on each capital goes up into its pocket), its ends
     against the wall; the CORNICE-P parts round the beam; PORTICO-ceiling up inside the beam.
  8. ROOF onto the lip at the wall tops (its front runs out over the portico as the
     pediment's roof); PEDIMENT on the beam under it; a CHIMNEY into each pocket; each
     DORMER-core into its DORMER, the DORMERs into their pockets on the end slopes, a
     DORMER-roof on each.
  9. CUPOLA into the pocket on the ridge, CUPOLA-dome (its finial printed on it) on it.
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
     PORCH-posts, each plinth into its recess in the deck; PORCH-beam on the posts under the
     kick (the peg on each post's cap goes up into its pocket); STEPS-front.
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
  5. The six DROPs (turned acorns) under the jetty's edge, each tongue up into its pocket: two
     at the corners, four between the windows.
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
     broken pediment, its tongue into the slot in the dormer's face.
  7. TOWER-roof (its finial printed on it) onto the tower's cornice.
  8. The porch: """ + top_porch(lace=True).replace("post", "column").replace("beams, columns", "beams, pedestals, columns") + """;
     PORCH-pediment over the steps.
  9. STOOP-back at the back door.
""", """The cornices' upper parts and the porch deck print upside down; the walls, the roofs, the tower
roof, the dormers, the urns and the chimney print upright; the PORCH-top
prints upside down on its flat roof, the columns standing up; the PORCH-lace pieces face-up.
"""),
    "fairhaven": ("THE FAIRHAVEN - COLONIAL REVIVAL WITH BAYS", """  1. FOUNDATION (snecked stone).
  2. WALLS-1 onto the foundation's lip: the whole first storey with both bays in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the second storey, the bays, both end gables
     and the front cross-gable in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (ogee-hooded windows below, consoled windows above, the Palladian window in the front
     gable, a lunette in each end gable, the double doors front and back).
  5. The CORNICE-J parts round the storey joint, the CORNICE-E parts round the eave (they wrap
     round the bays and across the gable ends).
  6. ROOF onto the lip at the wall tops; the two CHIMNEYs into their pockets; a BAY-roof on each
     bay's cornice, under the main eave.
  7. The veranda: """ + top_porch(lace=True) + """.
  8. STOOP-back at the back door.
""", """The cornices' upper parts, the porch deck and the PORCH-top print upside down (the top on its
flat roof, the posts standing up); the walls, the roofs and the chimneys print upright; the
PORCH-lace pieces face-up.
"""),
    "prescott": ("THE PRESCOTT - FEDERAL", """  1. FOUNDATION (brownstone, a band of vermiculated blocks along its top).
  2. WALLS-1 onto the foundation's lip: the whole first storey in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the whole second storey in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (blind-arched windows with carved fans below, tablet-capped windows above, the tripartite
     window over the entrance, the Adam doorway at the front and a plainer one at the back).
  5. The CORNICE-J parts round the storey joint, the CORNICE-E parts round the eave.
  6. ROOF onto the lip at the wall tops; the four CHIMNEYs into their pockets.
  7. The roof balustrade: BALUSTRADE-front and BALUSTRADE-back along the level curb at the roof's
     edge, then BALUSTRADE-west and BALUSTRADE-east between them (their end pedestals meet at the
     corners); each run is glued by its whole flat foot.
  8. STEPS-front (brownstone, fitted to the foundation) under the front door, STOOP-back at the
     back door.
""", """The cornices' upper parts print upside down; the walls, the roof, the chimneys and the steps
upright; the balustrade runs on their feet.
"""),
    "bellerive": ("THE BELLERIVE - FRENCH COLONIAL (LOUISIANA CREOLE)", """  1. FOUNDATION (a brick sill).
  2. WALLS-1 onto the foundation's lip: the raised ground storey (rose stucco, spalled to the
     brick here and there) in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the main storey (colombage: timber framing
     with brick between) in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (arched batten doors and windows below, the tall French doors of the main storey, casements
     of the same pattern across the back). A pair of SHUTTERs beside each French door and each
     back casement: the timbers stop at the shutters' edges, so each shutter's flat back glues
     to the brick.
  5. The CORNICE-J parts round the storey joint, the CORNICE-E parts round the eave.
  6. The gallery: GALLERY-deck (the planks, the frame, the joists and the stuccoed columns in
     one piece) stands on its columns across the front and down both ends of the house, its
     inner edge against the joint cornice. GALLERY-top (the colonnettes, the railings, the cutwork frieze
     and the flat top in one piece, so no post is glued on its own) lowered onto the deck: the
     peg under each colonnette drops into its socket in the planks. GALLERY-roof (the cypress
     skirt roof) on the top's flat, up against the wall under the eave cornice.
  7. STAIR up to the gallery at the front: its cheeks wrap the two columns either side.
  8. ROOF onto the lip at the wall tops; the two CHIMNEYs into their pockets; each DORMER-core
     into its DORMER, the two DORMERs into their pockets on the front slope, a DORMER-roof on
     each.
""", """The cornices' upper parts print upside down; the GALLERY-deck prints upside down (its first
1.2 mm are the planks: change to the Rose of the columns on the first layer above it); the
GALLERY-top prints upside down on its flat, the colonnettes standing up; the walls, the roofs,
the stair, the dormers and the chimneys print upright; the shutters on their backs.
"""),
    "pinckney": ("THE PINCKNEY - CHARLESTON SINGLE HOUSE", """  1. FOUNDATION (brick with iron-grilled vents).
  2. WALLS-1 onto the foundation's lip: the tuckpointed brick ground storey in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the weatherboard upper storey and both
     gables in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (crossette windows below, Gibbs windows above, the jib doors onto the upper piazza, the
     house door halfway down the piazza, the back door, a louvred demilune in each gable). A
     pair of SHUTTERs beside each window on the street front, the east side and the back.
  5. The CORNICE-J parts round the storey joint, the CORNICE-E parts round the eave (across both
     gables' feet, so each gable reads as a pediment).
  6. ROOF onto the lip at the wall tops; the two CHIMNEYs into their pockets on the ridge.
  7. The lower piazza: PIAZZA-deck (planks, piers and skirt) against the west wall; PIAZZA-top-1
     (the Tuscan columns, the railings, the crescent frieze and the planked floor of the upper
     piazza, all one piece) lowered onto it, the peg under each column into its socket; the
     PIAZZA-steps-0 against the deck's street end.
  8. PIAZZA-screen (the street screen wall) on the deck across the piazza's street end, between
     the corner column and the house, and the DOOR-piazza into it.
  9. The upper piazza: PIAZZA-2-top (the palmetto colonnettes, the cracked-ice railings and the
     frieze in one piece) onto the planked floor, each peg into its socket; PIAZZA-roof (the
     shed roof) on its flat top, up against the wall under the eave cornice.
 10. STOOP-back at the back door.
""", """The cornices' upper parts print upside down; so do the PIAZZA-deck and both piazza tops (on
their flat tops, the columns standing up). PIAZZA-top-1's first 1.2 mm are the upper piazza's
floor planks: load a wood brown and change to White on the first layer above 1.2 mm. The
walls, the roofs, the screen and the chimneys print upright; the shutters on their backs.
"""),
    "randolph": ("THE RANDOLPH - TIDEWATER VIRGINIA", """  1. FOUNDATION (English bond under a rubbed-brick water table).
  2. WALLS-1 onto the foundation's lip: the whole ground storey in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the upper storey and both clipped gables
     in one part (the gables' tops slope back to take the roof's clipped ends).
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (segmental-pediment windows below, rosette-capped windows above, two small lights in each
     gable, the Doric frontispiece and the back door).
  5. The CORNICE-J parts round the storey joint, the CORNICE-E parts round the eave (across the
     gable feet).
  6. ROOF onto the lip at the wall tops: its clipped ends settle on the sloping tops of the
     gables. The two CHIMNEYs (Stratford clusters) into their pockets on the ridge; each
     DORMER-core into its DORMER, the six DORMERs into their pockets, a DORMER-roof on each.
  7. The portico: PORTICO-deck against the front under the door; PORTICO-top (the Roman Doric
     columns, the railings and the triglyph entablature in one piece) onto it, each peg into
     its socket; PORTICO-roof on its flat top against the wall; PORTICO-steps-0 at the front.
  8. STOOP-back at the back door.
""", """The cornices' upper parts, the PORTICO-deck and the PORTICO-top print upside down (the top on
its flat roof, the columns standing up); the walls, the roofs, the chimney clusters and the
dormers print upright.
"""),
    "stauffer": ("THE STAUFFER - PENNSYLVANIA GERMAN", """  1. FOUNDATION (a sandstone plinth).
  2. WALLS-1 onto the foundation's lip: the whitewashed limestone storey in one part.
  3. FOREBAY (the forebay's floor, the joists' ends showing under it) against the front of
     WALLS-1, its top level with the lip.
  4. JOINT (the girt) onto WALLS-1's lip: at the front it runs out over the FOREBAY floor.
  5. WALLS-2 onto the joint's lip: the log storey and both boarded gables in one part; a
     HEXSIGN into the round pocket in each gable.
  6. Windows and doors: clip off the supports and push each plug into its opening from outside
     (pegged windows in the stone storey, pairs of casements in the log storey, the Dutch door
     under the forebay, the hooded side door, the back door). A pair of SHUTTERs beside each
     window of the stone storey.
  7. The CORNICE-J parts round the girt, the CORNICE-E parts round the eave (across the gable
     feet).
  8. ROOF onto the lip at the wall tops; CHIMNEY into its pocket.
  9. BAKEOVEN against the east gable between the two lower windows, BAKEOVEN-roof on it (the
     flue comes up through its hole).
 10. STOOP-0 under the front door, STOOP-2 at the back door, STOOP-3 at the side door.
""", """The cornices' upper parts and the FOREBAY print upside down; the hex signs and shutters on
their backs; the walls, the roofs, the chimney and the bake oven upright.
"""),
    "porter": ("THE PORTER - CONNECTICUT RIVER VALLEY", """  1. FOUNDATION (random rubble with ribbon pointing, under the house and the ell).
  2. WALLS-1 onto the foundation's lip: the whole ground storey and the one-storey kitchen ell
     in one part.
  3. JOINT onto WALLS-1, then WALLS-2 onto its lip: the upper storey and both gables in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (pedimented windows below, bull's-eye-capped windows above, a small light in each gable,
     the Connecticut Valley doorway, the back door; the ell's windows and its batten door).
  5. The CORNICE-J parts round the storey joint (they stop against the ell's roof), the
     CORNICE-E parts round the eave (across the gable feet), the CORNICE-ELL parts round the
     ell's eave (they stop against the house).
  6. ROOF onto the lip at the wall tops; the two CHIMNEYs into their pockets. ELL-roof onto the
     ell's lip, its back against the east gable.
  7. The ell's porch: PORCH-deck in the angle between the ell and the house; PORCH-top (the
     ringed posts, the sunburst railings and the frieze in one piece) onto it, each peg into
     its socket; PORCH-roof on its flat top against the ell's wall; PORCH-steps-0 at the front.
  8. STOOP-0 under the front door, STOOP-2 at the back door.
""", """The cornices' upper parts, the PORCH-deck and the PORCH-top print upside down (the top on its
flat roof, the posts standing up); the walls, the roofs and the chimneys print upright.
"""),
    "pingree": ("THE PINGREE - SALEM FEDERAL", """  1. FOUNDATION (bush-hammered granite).
  2. WALLS-1 onto the foundation's lip: the whole ground storey in one part.
  3. JOINT-1 onto WALLS-1, WALLS-2 onto its lip; JOINT-2 onto WALLS-2, WALLS-3 onto its lip:
     one part for each storey.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (splayed-lintel windows below, fluted-apron windows on the first floor, kneeled windows in
     the top storey, the elliptical-fanlight entrance, the balcony doors over it, the back door).
  5. The CORNICE-J1 parts round the first joint, the CORNICE-J2 parts round the second, the
     CORNICE-E parts round the eave.
  6. ROOF onto the lip at the wall tops; the two CHIMNEY pairs into their pockets at the ends.
  7. The belvedere: CUPOLA-walls on the roof's flat deck, a window in each face, the CORNICE-CUP
     parts round its top, CUPOLA-roof on them (the gilded eagle is printed with it: its one
     filament change).
  8. The portico: PORTICO-floor (the paving and the half-round steps) against the foundation
     under the door; PORTICO-top (the four columns, the curved entablature, the cornice and the
     roof, all one piece) lowered onto it, the peg under each column into its socket;
     PORTICO-balustrade on the roof, under the balcony doors.
  9. STOOP-back at the back door.
""", """The cornices' upper parts and the PORTICO-top print upside down (the top on its flat roof, the
columns standing up); the walls, the roofs, the belvedere, the chimneys, the portico floor and
the balustrade print upright.
"""),
    "alvarado": ("THE ALVARADO - SPANISH COLONIAL", """  1. FOUNDATION (coquina blocks).
  2. WALLS-1 onto the foundation's lip: the whole ground storey in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole upper storey in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the ground-floor casements behind their rejas, the upper casements under scalloped
     lintels, the three glazed plank doors onto the balcony, the studded portal in its alfiz,
     the back door).
  5. The CORNICE-J parts round the joint (they stop at the balcony, whose deck takes their
     place), then the CORNICE-E parts round the eave.
  6. ROOF onto the lip at the wall tops; the two CHIMNEY stacks into their pockets.
  7. The balcony: BALCONY-deck against the front wall under the glazed doors (its carved
     brackets flat on the wall); BALCONY-top (the posts with their zapatas, the spindle
     railings and the scalloped frieze in one piece) lowered onto it, each peg into its
     socket; BALCONY-roof on its flat top against the wall.
  8. The garden: GARDENWALL against the east end, its coping on top, the GATE into the arch.
  9. STOOP-0 under the portal, STOOP-2 at the back door.
""", """The cornices' upper parts, the BALCONY-deck and the BALCONY-top print upside down (the top on its
flat roof, the posts standing up); the walls, the roofs, the garden wall and the chimneys print
upright.
"""),
    "brenton": ("THE BRENTON - NEWPORT GEORGIAN", """  1. FOUNDATION (pillow-dressed granite).
  2. WALLS-1 onto the foundation's lip: the whole ground storey in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole upper storey in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (bolection windows below, arch-headed windows above, the shell-hood doorway with its
     pineapple at the front, the flat-hooded door at the back).
  5. The CORNICE-J parts round the joint, then the CORNICE-E parts round the eave.
  6. ROOF-lower (the steep slopes of the gambrel) onto the lip at the wall tops.
  7. The dormers: each DORMER-core into its DORMER, the DORMER into its pocket in the lower
     slope (standing on its seat), its DORMER-roof on top.
  8. ROOF-upper (the walk, its ring railing and the tin roof, one piece) onto the lower roof's
     top, the groove under the walk over the lip round the break.
  9. The two CHIMNEY stacks into their pockets in the upper roof, the crosses to the street.
 10. STOOP-0 under the front door, STOOP-2 at the back door.
""", """The cornices' upper parts print upside down; the walls, both roofs (the upper one standing on
its walk), the dormers and the chimneys print upright.
"""),
    "ridgely": ("THE RIDGELY - BALTIMORE FEDERAL ROW", """  1. FOUNDATION (boasted brownstone), open under the middle house for the carriage passage.
  2. PASSAGE-vault (the barrel vault and its two side walls, one piece) into the gap in the
     foundation, from front to back.
  3. WALLS-1 onto the foundation's lip, over the vault: the whole ground storey of the row in
     one part.
  4. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole upper storey and both gable ends.
  5. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the parlour windows under marble flat arches, the chamber windows under beaded lintels,
     the six fanlight doorways).
  6. PASSAGE-arch-S and PASSAGE-arch-N round the passage's mouths, on the bare patch of wall
     left for them.
  7. The CORNICE-J parts round the joint, then the CORNICE-E parts round the eave.
  8. ROOF between the gable walls onto the lip at the eave walls; the four CHIMNEY stacks into
     their pockets on the ridge.
  9. The dormers: each DORMER-core into its DORMER, the DORMER into its pocket in the roof
     (standing on its seat), its DORMER-roof on top.
 10. A white marble STOOP at every door.
""", """The cornices' upper parts print upside down; the passage vault prints standing on end, its
arches face-up; the walls, the roof, the dormers, the chimneys and the stoops print upright.
"""),
    "arroyo": ("THE ARROYO - CALIFORNIA CRAFTSMAN BUNGALOW", """  1. FOUNDATION (clinker brick).
  2. WALLS onto the foundation's lip: the whole storey and both gables in one part, the knee
     braces under the rakes printed with it.
  3. Windows, doors and the two gable vents: clip off the supports and push each plug into its
     opening from outside.
  4. The CORNICE-E parts round the eave (they stop at the porch roof and at the chimney).
  5. ROOF between the gable walls onto the lip on the eave walls.
  6. CHIMNEY against the bare patch of the east wall, up through the notch in the eave.
  7. The porch: PORCH-deck against the foundation; PORCH-top (the columns on their pedestals,
     the porch walls and the beams, one piece) onto it, each peg into its socket; PORCH-roof on
     its flat top against the front wall; PORCH-steps-0 at the front.
  8. STOOP-back at the kitchen door.
""", """The cornice's upper parts, the PORCH-deck and the PORCH-top print upside down; the walls, the
roofs and the chimney print upright.
"""),
    "hollister": ("THE HOLLISTER - AMERICAN FOURSQUARE", """  1. FOUNDATION (rock-faced concrete block), with the box bay's footing on the east side.
  2. WALLS-1 onto the foundation's lip: the whole ground storey and the box bay in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole upper storey in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside.
  5. The CORNICE-J parts round the joint, the CORNICE-BAY parts round the bay, the CORNICE-E
     parts round the eave.
  6. BAY-roof onto the bay's lip against the east wall.
  7. ROOF onto the lip at the wall tops; CHIMNEY into its pocket in the back slope.
  8. The dormers: each DORMER-core into its DORMER, the DORMER into its pocket (standing on its
     seat), its DORMER-roof on top.
  9. The porch: PORCH-deck against the foundation; PORCH-top (columns, railings and beams, one
     piece) onto it, each peg into its socket; PORCH-roof on its flat top against the front
     wall; PORCH-steps-0 at the door.
 10. STOOP-back at the back door.
""", """The cornices' upper parts, the PORCH-deck and the PORCH-top print upside down; the walls, the
roofs, the dormers and the chimney print upright.
"""),
    "wrightwood": ("THE WRIGHTWOOD - PRAIRIE SCHOOL", """  1. FOUNDATION (long limestone plinth blocks) under the centre block and both wings.
  2. WALLS-1 onto the foundation's lip: the whole ground storey and both wings in one part (Roman
     brick to the sill line, then stucco: one filament change).
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the centre block's upper storey in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside.
  5. The CORNICE-WINGW and CORNICE-WINGE parts round the wings, the CORNICE-J parts round the
     joint, the CORNICE-E parts round the main eave.
  6. WING-roof-W and WING-roof-E onto the wing lips against the centre block.
  7. ROOF onto the lip at the wall tops; CHIMNEY into its pocket on the ridge.
  8. The terrace: TERRACE (floor, parapet walls and piers) against the front wall;
     TERRACE-coping-W and -E (copings, pier caps and planter urns) on top; TERRACE-steps
     into the gap.
  9. STOOP-back at the back door.
""", """The cornices' upper parts print upside down; the walls, the roofs, the terrace and the chimney
print upright.
"""),
    "ashcombe": ("THE ASHCOMBE - TUDOR REVIVAL", """  1. FOUNDATION (squared rubble stone) under the house and the front gable.
  2. WALLS-1 onto the foundation's lip: the whole brick ground storey, the front gable included.
     Paint the raised diaper bricks a darker, over-burnt red.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole half-timbered upper storey with its three
     gables in one part. Paint the raised timbers oak, the render between them cream.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the stone-framed ones print oak, then stone from the wall face out).
  5. The CORNICE-J parts round the jetty, the CORNICE-E parts round the eave.
  6. CHIMNEY on the ground against the front wall beside the door, into its notch through both
     cornices.
  7. ROOF onto the lip at the wall tops; the three BARGE boards on the gable ends.
  8. STOOP-front at the door, STOOP-back at the back door.
""", """The cornices' upper parts print upside down; the walls, the roof and the chimney print upright
(the chimney stone to the plinth, then brick); the bargeboards print flat, face up.
"""),
    "capistrano": ("THE CAPISTRANO - MISSION REVIVAL", """  1. FOUNDATION (plaster plinth with grilled vents) under the house and the tower.
  2. WALLS-1 onto the foundation's lip: the whole ground storey and the tower's foot in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the upper storey, the mission parapet and the
     bell tower up to its belfry, in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the arched ground windows print timber, then iron for the rejas; the front door prints
     timber, then clay for its portal).
  5. The CORNICE-J parts round the joint, the CORNICE-E parts round the eave, the CORNICE-T
     parts round the tower top.
  6. BELFRY-floor down the tower onto its ledge; the BELL's bar into the slots in the front
     arch's jambs from inside.
  7. ROOF onto the lip at the wall tops (it notches round the parapet and the tower); CHIMNEY
     into its pocket; PARAPET-cap on the parapet's shaped top.
  8. TOWER-roof (with its finial) on the tower top.
  9. The porch: PORCH-deck against the foundation; PORCH-top (columns, arches, low walls and
     beams, one piece) onto it, each peg into its socket; PORCH-roof on its flat top against
     the front wall; PORCH-steps-0 at the door.
 10. STOOP-back at the back door.
""", """The cornices' upper parts, the PORCH-deck, the PORCH-top and the BELL print upside down; the
PARAPET-cap prints flat; the walls, the roofs and the chimney print upright.
"""),
    "kittredge": ("THE KITTREDGE - AIRPLANE BUNGALOW", """  1. FOUNDATION (tapestry brick).
  2. WALLS onto the foundation's lip: the whole storey, both gables and the four inner walls that
     carry the cockpit, in one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside.
  4. The CORNICE-E parts round the eave.
  5. ROOF onto the lip at the wall tops (the cockpit's walls rise through its opening); CHIMNEY
     into its pocket on the ridge.
  6. COCKPIT-foot down through the roof onto the lip on the inner walls; COCKPIT-joint on it; the
     CORNICE-B parts round it (the belt over the ridge).
  7. COCKPIT onto the joint's lip: the upper room with its gables; the CORNICE-C parts round its
     eave; COCKPIT-roof on top.
  8. The porch: PORCH-deck against the foundation; PORCH-top (twin columns, railings and beams,
     one piece) onto it, each peg into its socket; PORCH-roof on its flat top against the front
     wall; PORCH-steps-0 at the door.
  9. STOOP-back at the back door.
""", """The cornices' upper parts, the PORCH-deck and the PORCH-top print upside down; the walls, the
cockpit, the roofs and the chimney print upright.
"""),
    "pullman": ("THE PULLMAN - CHICAGO BUNGALOW", """  1. FOUNDATION (a raised brick basement; it prints brick, then limestone for the water table).
  2. WALLS onto the foundation's lip: the whole storey and the canted bay in one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside
     (they print green, then limestone from the wall face out).
  4. The CORNICE-E parts round the eave, the bay included.
  5. CHIMNEY on the ground against the east wall, into its notch through the cornice.
  6. ROOF onto the lip at the wall tops; each DORMER-core into its DORMER, the DORMER into its
     pocket (standing on its seat), its DORMER-roof on top.
  7. STOOP at the front door (paint its cheek walls brick), STOOP-back at the back door.
""", """The cornice's upper parts print upside down; the walls, the roof, the dormers and the chimney
print upright.
"""),
    "lindenwald": ("THE LINDENWALD - SWISS CHALET BUNGALOW", """  1. FOUNDATION (cyclopean stonework).
  2. WALLS-1 onto the foundation's lip: the whole rubble-stone ground storey in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole log upper storey with both gables, the
     crossing log ends at the corners and the purlins under the rakes, in one part.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside
     (they print cream, then red for the shutters, heads and window boxes).
  5. The CORNICE-J parts round the joint, the CORNICE-E parts round the eave.
  6. ROOF onto the lip at the wall tops; CHIMNEY into its pocket on the ridge; BARGE-0 and
     BARGE-1 on the two gable ends.
  7. The porch: PORCH-deck against the foundation; PORCH-top (posts, railings, beams and the
     balcony floor, one piece) onto it, each peg into its socket; BALCONY-rail on the
     balcony's floor; PORCH-steps-0 at the door.
  8. STOOP-back at the back door.
""", """The cornices' upper parts, the PORCH-deck and the PORCH-top print upside down; the bargeboards
print flat; the walls, the roof, the chimney and the balcony railing print upright.
"""),
    "stickley": ("THE STICKLEY - CRAFTSMAN WITH SLEEPING PORCH", """  1. FOUNDATION (board-formed concrete).
  2. WALLS-1 onto the foundation's lip: the whole lap-sided ground storey in one part.
  3. JOINT onto WALLS-1, WALLS-2 onto its lip: the whole shaked upper storey with both gables.
  4. Windows and doors: clip off the supports and push each plug into its opening from outside.
  5. The CORNICE-J parts round the joint, the CORNICE-E parts round the eave.
  6. ROOF onto the lip at the wall tops; CHIMNEY into its pocket on the ridge.
  7. The two-tier porch on the east gable: PORCH-deck against the foundation; PORCH-top (posts,
     railings, beams and the sleeping porch's floor, one piece) onto it, each peg into its
     socket; SLEEP-top (the sleeping porch's posts, shaked parapets and beams, one piece) onto
     the floor, its pegs into the sockets in PORCH-top; SLEEP-roof on its flat top against the
     gable; PORCH-steps-0 at the east steps.
  8. The pergola: TERRACE against the foundation at the front door, TERRACE-steps into its
     front; PERGOLA (posts, beams and rafters, one piece) onto the terrace, its pegs into the
     sockets, the beam ends against the wall.
  9. STOOP-back at the back door.
""", """The cornices' upper parts, the PORCH-deck, both porch tops and the PERGOLA print upside down;
the walls, the roofs, the terrace and the chimney print upright.
"""),
    "sandoval": ("THE SANDOVAL - PUEBLO REVIVAL", """  1. FOUNDATION (a plastered plinth).
  2. WALLS-1 onto the foundation's lip: the whole lower storey, with the inner walls that carry
     the upper storey, in one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside
     (they print turquoise, then wood for the lintels from the wall face out).
  4. The CORNICE-1 parts (the viga ends) round the lower storey's top.
  5. ROOF-1 (the lower roof: deck, parapet and canales in one) onto the lip; the upper storey's
     walls pass up through its opening. CHIMNEY (the kiva stack) into its socket on the deck.
  6. WALLS-2 onto the lip on the inner walls, up through the lower roof; the CORNICE-2 parts
     round its top; ROOF-2 on its lip.
  7. The portal: PORCH-deck against the foundation; PORCH-top (log posts, zapatas, bancos and
     beams, one piece) onto it, each peg into its socket; PORCH-roof on its flat top against the
     front wall; PORCH-steps-0 at the door.
  8. STOOP-back at the back door. The HORNO stands on its own in the yard.
""", """The cornices' upper parts, the PORCH-deck and the PORCH-top print upside down; the walls, the
roof trays, the chimney and the horno print upright.
"""),
    "millbrook": ("THE MILLBROOK DEPOT - RAILROAD STICK STATION", """  1. FOUNDATION (drafted-margin ashlar).
  2. WALLS onto the foundation's lip: the whole depot and the agent's bay in one part (it prints
     chocolate to the chair rail, then gold).
  3. Windows and doors: clip off the supports and push each plug into its opening from outside.
     The sliding freight doors' leaves, tracks and hangers lie on the plain fields left in the
     siding.
  4. The CORNICE-E parts round the eave band.
  5. The SIGN boards into the plain fields high on the end walls, each glued by its whole back.
  6. ROOF onto the lip at the wall tops; DORMER on its seat in the front slope with DORMER-core
     inside it and DORMER-roof over it; each FLUE down through its pocket.
  7. The platform: PLATFORM-deck against the foundation along the track side; PLATFORM-top (the
     canopy, beams and round columns in one piece) lowered onto it, each column's peg into its
     socket in the planks, its back edge against the wall and round the bay; PLATFORM-roof on
     its flat top against the wall; PLATFORM-steps-0 at the west end.
""", """The cornice's upper part, the PLATFORM-deck and the PLATFORM-top print upside down; the name
boards print face up; the walls, the roof, the dormer and the flues print upright.
"""),
    "brendan": ("ST. BRENDAN'S CHURCH - GOTHIC REVIVAL", """  1. FOUNDATION (snecked rubble, with plinths under the buttresses).
  2. WALLS-1 onto the foundation's lip: the nave with its gables and buttresses and the tower's
     lower stage, one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside
     (the rose into the west gable, the louvres into the belfry once WALLS-2 is on).
  4. The CORNICE-E parts round the nave's eave band (they stop at the tower).
  5. The CLOCKs into the round plain fields on the tower's front and west faces, each glued by
     its whole back.
  6. ROOF onto the lip at the nave's wall tops, between the gables.
  7. JOINT (the tower's string course) onto the tower top of WALLS-1; the CORNICE-J parts round
     it; WALLS-2 (the belfry stage) onto the joint's lip.
  8. The CORNICE-T parts round the tower top; SPIRE (the deck, pinnacles, spire and cross in one)
     onto the lip.
  9. STEPS-west and STEPS-tower at the doors.
""", """The cornices' upper parts print upside down; the clocks print face up; the walls, the roof and
the spire print upright (the spire changes to stone for its cross).
"""),
    "harmon": ("HARMON TOWN HALL - ITALIANATE CIVIC HALL", """  1. FOUNDATION (cushion-rusticated limestone).
  2. WALLS-1 onto the foundation's lip: the ground storey and the tower's foot, one part.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside.
  4. JOINT onto WALLS-1; the CORNICE-J parts round it; WALLS-2 (the upper storey with the tower
     rising through the roof) onto the joint's lip.
  5. The CORNICE-E parts round the eave band (they stop at the tower); ROOF onto the lip.
  6. The TABLET and the three CLOCKs into their plain fields on the tower, glued by their backs;
     the belfry louvres into their arches.
  7. The CORNICE-T parts round the tower top; TOWER-roof (with its flagstaff) onto the lip.
  8. STEPS at the front door, STEPS-back at the back.
""", """The cornices' upper parts print upside down; the tablet and clocks print face up; the walls,
the roofs and the steps print upright (the tower roof changes colour for its flagstaff).
"""),
    "engine3": ("ENGINE COMPANY No. 3 - VILLAGE ENGINE HOUSE", """  1. FOUNDATION (the bevelled granite water table).
  2. WALLS-1 onto the foundation's lip: the apparatus floor and the hose tower's foot.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside (the two engine doors into their arches).
  4. JOINT; the CORNICE-J parts round it; WALLS-2 (the upper storey, both gables and the hose
     tower) onto the joint's lip.
  5. The CORNICE-E parts round the eave band; the NAME-STONE into its field in the front gable.
  6. ROOF onto the lip; CHIMNEY down through its pocket.
  7. The CORNICE-T parts round the tower top; TOWER-roof (with its finial) onto the lip.
  8. APRON before the engine doors; STEP-back at the back door.
""", """The cornices' upper parts print upside down; the name stone prints face up; the walls, roofs,
chimney and apron print upright.
"""),
    "lakeshore": ("THE LAKESHORE FREIGHT HOUSE - RAILROAD FREIGHT SHED", """  1. FOUNDATION (the timber crib).
  2. WALLS onto the crib's lip, with both gable ends.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside. The sliding doors' leaves, tracks and hoods lie on the plain
     fields left in the shiplap.
  4. The CORNICE-E parts round the eave band; the SIGN into its field over the track-side doors.
  5. ROOF onto the lip; STOVEPIPE down through its hole.
  6. DOCK-S along the track side and DOCK-N along the street side against the crib, each with its
     steps at the west end.
""", """The cornice's upper part and the two docks print upside down; the sign prints face up; the
walls, roof and stovepipe print upright.
"""),
    "pleasant": ("PLEASANT VALLEY SCHOOL - ONE-ROOM SCHOOLHOUSE", """  1. FOUNDATION (brick piers with lattice between).
  2. WALLS onto the foundation's lip, with both gables.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside.
  4. The CORNICE-E parts round the eave band; the NAME-BOARD into its field in the front gable.
  5. ROOF onto the lip; BELFRY onto its flat seat at the front of the ridge; CHIMNEY down
     through its pocket at the back.
  6. STEPS at the door.
""", """The cornice's upper part prints upside down; the name board prints face up; the walls, the roof,
the belfry and the chimney print upright.
"""),
    "thorne": ("THE THORNE LIVERY - LIVERY AND FEED STABLE", """  1. FOUNDATION (river cobbles).
  2. WALLS onto the foundation's lip, with both gables.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside (the hay door into the front gable).
  4. The CORNICE-E parts round the eave band; the SIGN into its field over the big doors; the
     HAY-HOOD into its field at the peak, glued by its back.
  5. ROOF onto the lip; CUPOLA onto its flat seat in the ridge.
  6. RAMP-front and RAMP-back at the big doors.
""", """The cornice's upper part prints upside down; the sign and the hay hood print on their backs;
the walls, roof, cupola and ramps print upright.
"""),
    "mxtower": ("MX TOWER - INTERLOCKING TOWER", """  1. FOUNDATION (the scored concrete plinth).
  2. WALLS-1 (the brick relay room) onto the foundation's lip.
  3. Windows and doors: clip off the supports and push each plug into its opening from outside.
  4. JOINT; the CORNICE-J parts round it; WALLS-2 (the operating floor) onto the joint's lip.
  5. The CORNICE-E parts round the eave band; the SIGN into its field on the west end.
  6. ROOF onto the lip.
  7. STAIR against the back wall, its head at the operator's door.
""", """The cornices' upper parts print upside down; the sign prints face up; the stair prints lying on
its outer stringer; the walls and roof print upright.
"""),
    "tank12": ("WATER TANK No. 12 - RAILROAD WATER TANK", """  1. FOOTINGS (the pad and nine footing blocks) on the layout.
  2. TRESTLE onto the footings, each post's peg into its socket.
  3. TANK onto the trestle's deck, the spout toward the track.
  4. ROOF onto the tank's rim.
""", """The trestle prints upside down on its deck; the footings, tank and roof print upright.
"""),
    "greenfield": ("THE GREENFIELD BANDSTAND - OCTAGONAL PARK BANDSTAND", """  1. DECK (the planked floor on its lattice skirt).
  2. TOP-top (the columns, railings, arches and roof slab in one piece) lowered onto it, each
     column's peg into its socket in the planks.
  3. ROOF (with its finial) on the top's flat roof.
  4. STEPS-0 at the front face.
""", """The deck and the top print upside down; the roof prints upright (it changes colour for its
finial).
"""),
    "blackwater": ("THE BLACKWATER COALING TOWER - TIMBER COALING TOWER", """  1. FOOTINGS on the layout, the long side (with the ladder's pad at its west end) along the track the chutes serve.
  2. TRESTLE onto the footings, each post's peg into its socket, the walkway toward the track.
  3. WALLS onto the deck, the door onto the walkway; CORNICE-B-lower (the strapped sill) round their foot.
  4. The windows and the walkway door into the bin house; SIGN on the plain field under the eave.
  5. CORNICE-E-lower onto the ledge under the eave, then CORNICE-E-upper on top of it.
  6. SHAFT onto its footing at the east end, its plain face against the bin house; its windows; CORNICE-S-lower, then CORNICE-S-upper, onto the ledge at its top.
  7. ROOF onto the bin house, notched round the shaft, the spout toward the shaft.
  8. HEAD-WALLS onto the shaft's cornice, the plain patch on the west face against the spout's end; its windows; CORNICE-H-course, then CORNICE-H-crown; HEAD-ROOF.
  9. HOIST-FOUNDATION beside the shaft, HOIST-WALLS onto it (the door toward the track); its windows and door; CORNICE-K-frieze, then CORNICE-K-crown; HOIST-ROOF; STACK down through the hole in the roof.
  10. CHUTE-1 and CHUTE-2 onto the two plain fields either side of the walkway door, the aprons out over the track; RAILING along the walkway's edge; LADDER at the walkway's west end, its tab flat on the deck.
""", """The trestle prints upside down on its deck; the walls, shaft (about 190 mm) and hoist house upright; the chutes and the sign on their backs; the ladder on its face; windows and doors face up with supports under their frames only.
"""),
    "stonehaven": ("THE STONEHAVEN TUNNEL PORTALS - SINGLE-TRACK STONE PORTALS (PAIR)", """  1. Lay the track first. Stand each PORTAL square across it, the date tablet up, the arch centred on the track (60 mm wide, 82 mm to the crown).
  2. LINER against the back of each portal, lined up with the arch; it glues by its whole end ring.
  3. WING-L and WING-R against the portal's sides, their angled ends flat on the portal's side faces, the walls splaying forward along the approach.
  4. Build the hillside behind and over the linings (foam, plaster cloth or a cardboard web), up to the cornice and the wing walls' copings. The kit has two of each part, one set for each end of the tunnel.
""", """Every part prints face up, flat on its back, with no supports; the linings stand on end.
"""),
    "sandhouse": ("THE BLACKWATER SAND HOUSE - LOCOMOTIVE SANDING PLANT", """  1. FOUNDATION on the layout, the long side with three windows toward the track.
  2. WALLS onto the foundation's lip; the windows and doors into their openings.
  3. CORNICE-E-lower onto the ledge under the eave, then CORNICE-E-upper on top of it.
  4. ROOF onto the walls; CHIMNEY onto its flat seat on the back slope.
  5. TOWER-FOOTINGS between the house and the track; TOWER-LEGS onto them, each peg into its socket, the open upper bay toward the track.
  6. TOWER-BIN down through the hole in the legs' plate, its flat bottom on the plate; TOWER-CAP on its top; SPOUTS under the outlet, raking out over the track.
  7. WET-BIN at the west end by the wet-sand doors, its open side toward the track; SAND-HEAP into it.
""", """The tower's legs print upside down on their plate and the bin on its top; the walls, roof, cap, spouts and bins upright. Windows and doors print face up with supports under their frames only.
"""),
    "enginehouse": ("THE BLACKWATER ENGINE HOUSE - TWO-STALL BRICK ENGINE HOUSE", """  1. Lay the two stall tracks first, 58 mm apart. FOUNDATION over them, its gaps at the stall doorways.
  2. WALLS onto the foundation; the side and back windows and the two gable oculi into their openings.
  3. DOOR-stall1 and DOOR-stall2 (the arched heads with their fanlights) into the stall doorways.
  4. CORNICE-E-lower onto the ledge under the eave, then CORNICE-E-upper on top of it.
  5. ROOF onto the walls; MONITOR onto the flat seat along the ridge; SMOKEJACK-1 and SMOKEJACK-2 onto their seats over the stalls.
  6. The door leaves (LEAF-L and LEAF-R, two of each): glue them into a doorway to shut the stall, or stand them open at right angles, the hinge edge against the jamb band.
""", """The walls (116 x 230 mm) fill the P1S/P2S bed; walls, roof and monitor print upright, the leaves flat. Windows and doors print face up with supports under their frames only.
"""),
    "yardoffice": ("THE BLACKWATER YARD OFFICE - TWO-STOREY YARD OFFICE", """  1. FOUNDATION on the layout, the bay toward the tracks.
  2. WALLS-1 (with the bay) onto the foundation; its windows and the door; JOINT onto WALLS-1.
  3. CORNICE-B-course round the bay's top, then CORNICE-B-crown; BAY-ROOF onto the bay, under the joint.
  4. CORNICE-J-lower round the joint, then CORNICE-J-crown; WALLS-2 onto the joint; its windows; SIGN on the plain field on the front.
  5. CORNICE-E-lower onto the ledge under the eave, then CORNICE-E-upper on top of it.
  6. ROOF onto the walls; LOOKOUT onto the flat seat at the top of the hip; CHIMNEY onto its seat on the back slope.
  7. STOOP under the door.
""", """Walls, roofs, lookout and chimney print upright. Windows and doors print face up with supports under their frames only.
"""),
    "section4": ("SECTION HOUSE No. 4 - TOOL HOUSE AND SPEEDER SHED", """  1. TOOL-FOUNDATION on the layout, the door side toward the track; TOOL-WALLS onto it; the door and windows; TOOL-CORNICE-frieze, then TOOL-CORNICE-crown; TOOL-ROOF; STOVEPIPE down into the hole in the back slope.
  2. SPEEDER-FOUNDATION with its gable end to the speeder's spur; SPEEDER-WALLS onto it; the doors and window; SPEEDER-CORNICE-course, then SPEEDER-CORNICE-crown; SPEEDER-ROOF.
""", """Walls and roofs print upright. Windows and doors print face up with supports under their frames only.
"""),
    "shanty": ("THE CROSSING SHANTY AND OIL HOUSE - WATCHMAN'S SHANTY, OIL HOUSE AND CROSSBUCK", """  1. SHANTY-CRIB by the crossing; SHANTY-WALLS onto it, the door toward the road; its windows and door; SHANTY-CORNICE-course, then SHANTY-CORNICE-crown; SHANTY-ROOF; STOVEPIPE down into its hole.
  2. OIL-FOUNDATION; OIL-WALLS onto it; the door and the two vents; OIL-CORNICE-frieze, then OIL-CORNICE-crown; OIL-ROOF.
  3. CROSSBUCK beside the road, its foot flat on the ground.
""", """Walls and roofs print upright, the crossbuck flat on its back. Windows and doors print face up with supports under their frames only.
"""),
    "kilnridge": ("THE KILN RIDGE TUNNEL PORTALS - DOUBLE-TRACK BRICK PORTALS (PAIR)", """  1. Lay the two tracks first, 51 mm apart. Stand each PORTAL square across them, the keystone up, the arch (112 mm wide, 80 mm to the crown) centred between the tracks.
  2. LINER against the back of each portal, lined up with the arch; it glues by its whole end ring.
  3. WING-L and WING-R against the portal's sides, their angled ends flat on the portal's side faces, the walls stepping down along the approach.
  4. Build the hillside behind and over the linings, up to the cornice and the wing walls' copings. The kit has two of each part, one set for each end of the tunnel.
""", """Every part prints face up, flat on its back, with no supports; the linings stand on end. For stone dressings in a second colour, change filament at 5.0 mm on the portals and wing walls (one change).
"""),
    "millcreek": ("THE MILL CREEK BRIDGE - CONCRETE ABUTMENTS, PIER AND TWO GIRDER SPANS", """  1. Set the two ABUTMENTs facing each other, their breasts 226 mm apart, each backwall top level with the track's subgrade on its bank.
  2. PIER midway, 113 mm from each breast, its cutwaters up and down stream, its top level with the abutments' seats.
  3. SPAN-1 and SPAN-2 onto the bearing pads, each from its abutment's seat to the pier.
  4. Lay the track in its ballast on the decks, level with the approaches.
""", """Abutments, pier and spans print upright (the spans on their bottom flanges), with no supports.
"""),
    "beaverrun": ("THE BEAVER RUN TRESTLE - TIMBER TRESTLE BRIDGE", """  1. Shape the valley so each bent's sill sits at the depth its length gives below the cap line (35, 60, 75, 60 and 35 mm), the bents 50 mm apart; the two BULKHEADs at the banks, 300 mm apart, their caps at the same level.
  2. The BENTs upright in order, square across the line, their caps level.
  3. The SPANs from cap to cap, each resting on half a cap at each end.
  4. Rail on the ties, or flex track on the stringers.
""", """Bents and bulkheads print flat on their faces, the spans upside down on their guard timbers; no supports.
"""),
}

ZIPNAME = {"villa": "Ashby_Villa", "beaumont": "Beaumont_Queen_Anne", "harcourt": "Harcourt_Second_Empire",
           "millbrook": "Millbrook_Depot", "brendan": "St_Brendans_Church", "harmon": "Harmon_Town_Hall",
           "engine3": "Engine_Company_No3", "lakeshore": "Lakeshore_Freight_House", "pleasant": "Pleasant_Valley_School",
           "thorne": "Thorne_Livery", "mxtower": "MX_Tower", "tank12": "Water_Tank_No12", "greenfield": "Greenfield_Bandstand",
           "blackwater": "Blackwater_Coaling_Tower", "stonehaven": "Stonehaven_Tunnel_Portals",
           "sandhouse": "Blackwater_Sand_House", "enginehouse": "Blackwater_Engine_House", "yardoffice": "Blackwater_Yard_Office", "section4": "Section_House_No4", "shanty": "Crossing_Shanty_Oil_House", "kilnridge": "Kiln_Ridge_Tunnel_Portals", "millcreek": "Mill_Creek_Bridge", "beaverrun": "Beaver_Run_Trestle"}

NOTES = {k: (v[0], _rewrap(v[1])) + tuple(v[2:]) for k, v in NOTES.items()}
SHOPS = {k: (v[0], _rewrap(v[1])) + tuple(v[2:]) for k, v in SHOPS.items()}
