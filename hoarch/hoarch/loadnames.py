"""Zip names of the second series of flatcar loads (hoarch.flatloads2, registered in hoarch.loads2).
Plain data, so hoarch.assembly can read it without building any geometry."""

ZIPNAMES = {
    "girders": "Concrete_Bridge_Girder_Load",
    "lumber": "Lumber_Load",
    "wrapped": "Wrapped_Lumber_Load",
    "tires": "Mining_Truck_Tire_Load",
    "logs": "Sawlog_Load",
    "panels": "Track_Panel_Load",
    "concties": "Concrete_Crosstie_Load",
    "woodties": "Wood_Crosstie_Bundle_Load",
    "granite": "Granite_Block_Load",
    "bricks": "Brick_Cube_Load",
    "ingotmolds": "Ingot_Mold_Load",
    "cablereels": "HV_Cable_Reel_Load",
    "trailers": "Piggyback_Trailer_Load",
    "containers": "ISO_Container_Load",
    "crates": "Machinery_Crate_Load",
    "chillers": "Air_Cooled_Chiller_Load",
    "propane": "Propane_Tank_Load",
    "culverts": "Precast_Box_Culvert_Load",
    "conpipe": "Concrete_Pipe_Load",
    "barriers": "Jersey_Barrier_Load",
    "manholes": "Precast_Manhole_Load",
    "doubletees": "Precast_Double_Tee_Load",
    "rebar": "Rebar_Bundle_Load",
    "sheetpile": "Steel_Sheet_Piling_Load",
    "poles": "Utility_Pole_Load",
    "crushed": "Crushed_Car_Scrap_Load",
    "giantlog": "Giant_Log_Load",
    "pulpwood": "Pulpwood_Load",
    "truss": "Pony_Truss_Bridge_Load",
    "rotor": "Generator_Rotor_Load",
    "stator": "Generator_Stator_Load",
    "tubebundle": "Heat_Exchanger_Tube_Bundle_Load",
    "column": "Distillation_Column_Load",
    "gear": "Girth_Gear_Load",
    "genset": "Diesel_Genset_Load",
    "boiler": "Package_Boiler_Load",
    "locoboiler": "Locomotive_Boiler_Load",
    "wheelsets": "Freight_Car_Wheelset_Load",
    "girderspan": "Plate_Girder_Span_Load",
    "windblade": "Wind_Turbine_Blade_Load",
    "minecars": "Mine_Car_Load",
    "joists": "Steel_Joist_Load",
    "copper": "Copper_Cathode_Load",
    "farmtractors": "Steel_Wheel_Tractor_Load",
    "buckets": "Excavator_Bucket_Load",
    "primemover": "Locomotive_Diesel_Engine_Load",
    "radiators": "Transformer_Radiator_Load",
    "anchor": "Ship_Anchor_and_Chain_Load",
    "hydraulics": "Hydraulic_Cylinder_Load",
    "turnout": "Turnout_Frog_and_Switch_Point_Load",
    "locoengine": "Locomotive_Engine_and_Generator_Load",
    "drivers": "Steam_Locomotive_Driver_Load",                 # third series (hoarch.flatloads3), 0.2 mm nozzle
    "castings": "Truck_Side_Frame_and_Bolster_Load",
    "bop": "Blowout_Preventer_Load",
}

# Loads made for the 0.2 mm nozzle (0.10 mm layers): finer detail than a 0.4 nozzle can draw.
# hoarch.packs slices them with slicer/bambu_like_0.2.ini and hoarch.bambu writes their projects
# with the P2S 0.2 nozzle presets (bambu/p2s_profiles_0.2.json).
FINE = ("locoengine", "drivers", "castings", "bop")
NOZZLE = {k: 0.2 for k in FINE}
LAYER = {k: 0.1 for k in FINE}
