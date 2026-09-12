// Empire State Building — parametric model (OpenSCAD)
// An editable alternative to the Python generator. Adjust the parameters,
// then Render (F6) and Export STL, or headless:
//     openscad -o esb.stl empire_state_building.scad
//
// Units are mm. Massing + facade come from the real building (Shreve, Lamb &
// Harmon, 1931): full-block base, slab tower with vertical piers and per-floor
// reveals, stepped setbacks, tiered mooring-mast crown, tapering spire.

mm = 0.40;            // millimetres per foot  (roof 1250ft -> 500mm)
$fn = 48;

// ---- facade parameters ----
pier_pitch  = 16;     // ft between window bands
win_frac    = 0.55;   // window width / pitch
win_depth   = 3;      // window recess depth (ft)
corner_pier = 22;     // solid corner pier width (ft)
floor_ft    = 12.25;  // storey height (ft)
spandrel    = 1.4;    // per-floor reveal depth/height (ft)

module boxft(x, y, z0, z1)
    translate([0, 0, z0*mm])
        linear_extrude(height=(z1-z0)*mm)
            square([x*mm, y*mm], center=true);

module drum(r0, r1, z0, z1)
    translate([0, 0, z0*mm]) cylinder(h=(z1-z0)*mm, r1=r0*mm, r2=r1*mm);

// slab tower with punched facade (vertical piers + floor reveals)
module shaft(x, y, z0, z1) {
    zc = (z0+z1)/2; zh = (z1-z0-2);
    difference() {
        boxft(x, y, z0, z1);
        nY = floor((y-2*corner_pier)/pier_pitch);
        for (i=[0:nY-1]) let(p=(i-(nY-1)/2)*pier_pitch)
            for (sx=[1,-1])
                translate([sx*x/2*mm, p*mm, zc*mm])
                    cube([2*win_depth*mm, pier_pitch*win_frac*mm, zh*mm], center=true);
        nX = floor((x-2*corner_pier)/pier_pitch);
        for (i=[0:nX-1]) let(p=(i-(nX-1)/2)*pier_pitch)
            for (sy=[1,-1])
                translate([p*mm, sy*y/2*mm, zc*mm])
                    cube([pier_pitch*win_frac*mm, 2*win_depth*mm, zh*mm], center=true);
        for (z=[z0+floor_ft : floor_ft : z1-2]) {
            for (sx=[1,-1]) translate([sx*x/2*mm, 0, z*mm])
                cube([2*spandrel*mm, (y-2*corner_pier)*mm, spandrel*mm], center=true);
            for (sy=[1,-1]) translate([0, sy*y/2*mm, z*mm])
                cube([(x-2*corner_pier)*mm, 2*spandrel*mm, spandrel*mm], center=true);
        }
    }
}

module empire_state() {
    // base (floors 1-5) + 5th-floor cornice + lower massing
    boxft(197, 425, 0, 60);
    boxft(205, 433, 58, 62);
    boxft(165, 340, 62, 120);
    // tower shaft
    shaft(132, 210, 120, 1000);
    // stepped setbacks + 86th-floor deck
    boxft(140, 218, 1000, 1004); boxft(118, 180, 1004, 1024);
    boxft(124, 186, 1024, 1028); boxft(104, 150, 1028, 1046);
    boxft(110, 156, 1046, 1050); boxft( 92, 124, 1050, 1062);
    // tiered mooring-mast crown
    drum(46, 44, 1062, 1110); drum(41, 39, 1110, 1152);
    drum(37, 35, 1152, 1200); drum(33, 31, 1200, 1228);
    drum(30, 18, 1228, 1246); drum(16, 10, 1246, 1258);
    // spire + antenna
    drum(10, 7, 1258, 1300); drum(6.5, 4.5, 1300, 1360); drum(4, 2, 1360, 1454);
}

empire_state();
