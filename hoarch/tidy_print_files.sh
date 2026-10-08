#!/bin/bash
# Tidy the HO model print files in your Downloads folder (or another folder you name).
#
# Keeps the newest zip and the newest Bambu Studio project (..._P2S_v1.x.3mf) of each building and
# moves the rest to the Trash (a zip sent in parts, ..._v1.2_part1of2.zip, keeps all its parts):
#   - older versions (Fowler v1.1 when you have Fowler v1.2, or the old zips with no version),
#   - extra copies your browser saved as "(1)", " 2" or "-1",
#   - the old combined zip of the first 40 buildings, which holds old versions.
# It shows you the list first and moves nothing until you type y. Everything goes to the
# Trash, so you can put anything back from there. Other files are not touched.
#
# Run it from Terminal:
#   bash ~/Downloads/tidy_print_files.sh
#   bash ~/Downloads/tidy_print_files.sh ~/Desktop/Models      (a different folder)

DIR="${1:-$HOME/Downloads}"
cd "$DIR" 2>/dev/null || { echo "Can't open the folder $DIR"; exit 1; }
if ! ls . > /dev/null 2>&1; then
  echo "macOS didn't let Terminal look in $DIR. Allow it in System Settings > Privacy & Security >"
  echo "Files and Folders (turn on Downloads Folder under Terminal), then run this again."
  exit 1
fi

# The latest version of each building when this script was made, for the "not the latest"
# note at the end. Zips that come out later are handled anyway: the newest one you have is kept.
LATEST="
  Alvarado 1.2 Ardmore 1.1 Arroyo 1.2 Ashby_Villa 1.2 Ashcombe 1.3 Bakery 1.2 Bank 1.3 Barber 1.1
  Beaumont_Queen_Anne 1.2 Beauvais 1.2 Beaver_Run_Trestle 1.0 Belcourt 1.1 Bellerive 1.2
  Blackwater_Coaling_Tower 1.2 Blackwater_Engine_House 1.2 Blackwater_Sand_House 1.1
  Blackwater_Yard_Office 1.2 Brenton 1.2 Camellia 1.4 Capistrano 1.1 Carrow 1.4 Chatham 1.2
  Chevalier 1.1 Crossing_Shanty_Oil_House 1.1 Delacroix 1.1 Delancey 1.2 Drugstore 1.3 Ellsworth 1.4
  Engine_Company_No3 1.1 Fairhaven 1.3 Fontaine 1.2 Fowler 1.3 General 1.2 Greenfield_Bandstand 1.0
  Harcourt_Second_Empire 1.3 Hardware 1.4 Harmon_Town_Hall 1.1 Hathaway 1.3 Hawthorn 1.4 Hollis 1.4
  Hollister 1.4 Hotel 1.4 Jeweler 1.3 Juniper 1.3 Kiln_Ridge_Tunnel_Portals 1.0 Kittredge 1.3
  Lafayette 1.2 Lakeshore_Freight_House 1.1 Larkspur 1.3 Lindenwald 1.3 Magnolia 1.3 Marchand 1.2
  Marigold 1.3 Merritt 1.1 Mill_Creek_Bridge 1.0 Millbrook_Depot 1.2 Millinery 1.2 Montclair 1.3
  MX_Tower 1.1 Oakhurst 1.5 Pemberton 1.2 Pennock 1.2 Pinckney 1.3 Pingree 1.4
  Pleasant_Valley_School 1.1 Porter 1.3 Prescott 1.2 Primrose 1.3 Pullman 1.3 Randolph 1.3
  Ridgely 1.3 Rochambeau 1.1 Rosecroft 1.3 Sandoval 1.1 Section_House_No4 1.0 St_Brendans_Church 1.3
  Stauffer 1.1 Stickley 1.4 Stonehaven_Tunnel_Portals 1.0 Thorne_Livery 1.1 Twins 1.4 Valcour 1.2
  Vantassel 1.4 Water_Tank_No12 1.0 Westbrook 1.3 Whitby 1.3 Whitmore 1.3 Winthrop 1.3 Wisteria 1.3
  Wrightwood 1.2
"

DUP='( ?\([0-9]+\)| [0-9]+|-[0-9]+)?'      # a browser's extra-copy mark: " (1)", "(1)", " 2", "-1"
PRINT_RE="^(.+)_Print_Files(_v([0-9]+)\.([0-9]+))?(_part[0-9]+of[0-9]+)?${DUP}\.zip\$"
HO_RE="^(HO_[A-Za-z0-9_]+)${DUP}\.(zip|pdf|md)\$"
KIT_RE="^Beaumont_HO_Kit_RevB${DUP}\.zip\$"
P2S_RE="^(.+)_P2S_v([0-9]+)\.([0-9]+)${DUP}\.3mf\$"

TAB=$(printf '\t')
LIST=$(mktemp "${TMPDIR:-/tmp}/tidy.XXXXXX") || exit 1
PLAN=$(mktemp "${TMPDIR:-/tmp}/tidy.XXXXXX") || exit 1
trap 'rm -f "$LIST" "$PLAN"' EXIT

mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1"; }
row() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$(mtime "$4")" "$4" "$3" >> "$LIST"; }   # group ver clean file

# 1. Find the print zips and the collection files (certificates, guides, listings).
for f in *; do
  [ -f "$f" ] || continue
  if [[ $f =~ $PRINT_RE ]]; then
    name=${BASH_REMATCH[1]}
    if [ -n "${BASH_REMATCH[2]}" ]; then
      maj=$((10#${BASH_REMATCH[3]})); min=$((10#${BASH_REMATCH[4]}))
      row "P $name" $((maj * 1000 + min)) "${name}_Print_Files_v${maj}.${min}${BASH_REMATCH[5]}.zip" "$f"
    else
      row "P $name" 0 "${name}_Print_Files.zip" "$f"            # from before the zips had versions
    fi
  elif [[ $f =~ $P2S_RE ]]; then
    name=${BASH_REMATCH[1]}
    maj=$((10#${BASH_REMATCH[2]})); min=$((10#${BASH_REMATCH[3]}))
    row "S $name" $((maj * 1000 + min)) "${name}_P2S_v${maj}.${min}.3mf" "$f"
  elif [[ $f =~ $KIT_RE ]]; then
    row "KIT" 0 "Beaumont_HO_Kit_RevB.zip" "$f"
  elif [[ $f =~ $HO_RE ]]; then
    clean="${BASH_REMATCH[1]}.${BASH_REMATCH[3]}"
    if [ "${BASH_REMATCH[1]}" = "HO_Victorian_Collection_All_40" ]; then
      row "ALL40" 0 "$clean" "$f"
    else
      row "H $clean" 0 "$clean" "$f"
    fi
  fi
done

# 2. Per building: keep the newest version (the latest-saved copy of it, or every part of it), drop the rest.
HAS_BEAUMONT=0
grep -q "^P Beaumont_Queen_Anne${TAB}" "$LIST" && HAS_BEAUMONT=1
sort -t "$TAB" -k1,1 -k2,2nr -k3,3nr "$LIST" | awk -F'\t' -v OFS='\t' -v beau=$HAS_BEAUMONT '
  $1 == "ALL40"            { print "ALL40", $0; next }
  $1 == "KIT" && beau      { print "KIT", $0; next }
  $1 != g                  { g = $1; top = $2 + 0; seen[g SUBSEP $5] = 1; print "KEEP", $0; next }
  $2 + 0 < top             { print "OLD", $0; next }
  (g SUBSEP $5) in seen    { print "COPY", $0; next }
                           { seen[g SUBSEP $5] = 1; print "KEEP", $0 }' > "$PLAN"

# 3. Show the plan.
DROP=(); KEEP=0; KB=0; OUTDATED=""
echo
echo "Looking in $PWD"
echo
while IFS="$TAB" read -r act grp ver mt f clean; do
  case $act in
    KEEP)
      KEEP=$((KEEP + 1))
      case $grp in
        "P "*)
          name=${grp#P }
          want=$(printf '%s\n' $LATEST | awk -v n="$name" 'p == n { print; exit } { p = $0 }')
          if [ -n "$want" ]; then
            w=$(( ${want%%.*} * 1000 + ${want#*.} ))
            if [ "$ver" -lt "$w" ]; then
              have="v$((ver / 1000)).$((ver % 1000))"; [ "$ver" -eq 0 ] && have="the zip with no version"
              OUTDATED="$OUTDATED  $name: you have $have, the latest is v$want
"
            fi
          fi ;;
      esac ;;
    *)
      case $act in
        OLD)   why="older version" ;;
        COPY)  why="extra copy" ;;
        ALL40) why="old combined zip (holds old versions)" ;;
        KIT)   why="early Beaumont kit (replaced by the Beaumont Queen Anne zip)" ;;
      esac
      [ ${#DROP[@]} -eq 0 ] && echo "Moving to the Trash:"
      printf '  %-52s %s\n' "$f" "$why"
      DROP+=("$PWD/$f")
      KB=$((KB + $(du -sk "$f" | cut -f1))) ;;
  esac
done < "$PLAN"

[ ${#DROP[@]} -gt 0 ] && echo
echo "Keeping $KEEP file(s): the newest of each building, and one copy of each certificate, guide and listing file."

if [ -n "$OUTDATED" ]; then
  echo
  echo "Not the latest version (download the newer zip from our chat):"
  printf '%s' "$OUTDATED"
fi

PKG=""
for d in *_pkg*; do [ -d "$d" ] && PKG="$PKG  $d
"; done
if [ -n "$PKG" ]; then
  echo
  echo "Unzipped folders (left alone, because they don't show a version; delete old ones by hand):"
  printf '%s' "$PKG"
fi

echo
if [ ${#DROP[@]} -eq 0 ]; then
  echo "Nothing to tidy: there's only one copy of each building's newest zip."
  exit 0
fi
SIZE=$(awk -v kb=$KB 'BEGIN { if (kb >= 1048576) printf "%.1f GB", kb / 1048576; else printf "%.0f MB", kb / 1024 }')
read -r -p "Move these ${#DROP[@]} file(s) to the Trash (about $SIZE)? Type y and press Return: " ans
case $ans in
  y|Y|yes|Yes|YES) ;;
  *) echo "Nothing moved."; exit 0 ;;
esac

# 4. Move them to the Trash through Finder (macOS may ask once to let Terminal control Finder).
osascript -e 'on run argv' \
          -e 'set theItems to {}' \
          -e 'repeat with p in argv' \
          -e 'set end of theItems to ((POSIX file (contents of p)) as alias)' \
          -e 'end repeat' \
          -e 'tell application "Finder" to delete theItems' \
          -e 'end run' "${DROP[@]}" > /dev/null
LEFT=0
for p in "${DROP[@]}"; do [ -e "$p" ] && LEFT=$((LEFT + 1)); done
if [ $LEFT -gt 0 ]; then
  echo "$LEFT file(s) couldn't be moved to the Trash. If macOS asked to let Terminal control Finder,"
  echo "click OK (or allow it in System Settings > Privacy & Security > Automation) and run this again."
  exit 1
fi

# 5. A kept copy saved as "... (1).zip" gets its plain name back once the plain name is free.
while IFS="$TAB" read -r act grp ver mt f clean; do
  [ "$act" = KEEP ] && [ "$f" != "$clean" ] && [ ! -e "$clean" ] && mv -n "$f" "$clean" && echo "Renamed $f to $clean"
done < "$PLAN"
echo "Done: moved ${#DROP[@]} file(s) to the Trash."
