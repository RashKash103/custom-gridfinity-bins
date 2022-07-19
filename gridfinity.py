import math
import cadquery2 as cq
import warnings
from cadquery2 import Workplane, Vector, Location
from typing import List, Union, Optional, Literal
from dataclasses import dataclass


BOTTOM_THICKNESS = 2


class IncorrectNumberOfRowsError(Exception):
    pass


class InvalidPropertyError(Exception):
    pass


class SmallDimensionsWarning(Warning):
    pass


class CannotDrawLabelLedgesWarning(Warning):
    pass


@dataclass
class Properties:
    units_wide: int
    units_long: int
    units_high: int
    divisions: List[Union[List[float], int]]

    draw_finger_scoop: bool
    draw_label_ledge: bool
    make_magnet_hole: bool
    make_screw_hole: bool

    @property
    def height(self) -> float:
        return self.units_high * 7 - 5.6

    @property
    def length(self) -> float:
        return self.units_long * 42

    @property
    def width(self) -> float:
        return self.units_wide * 42

    def __post_init__(self):
        if self.units_wide < 1 or self.units_long < 1:
            raise InvalidPropertyError(
                "Width or length cannot be less than 1."
            )
        if self.units_high < 2:
            raise InvalidPropertyError(
                "Units high cannot be less than 2."
            )
        if len(self.divisions) != self.units_long:
            raise IncorrectNumberOfRowsError(
                "Number of rows in divisions array must be equal to the number of units long."
            )


def draw_base(
    self: Workplane
) -> Workplane:
    return (
        self
        .box(37.2, 37.2, 2.6, (True, True, False))
        .edges("|Z").fillet(1.6)
        .faces("<Z").chamfer(0.8)
        .faces(">Z")
        .box(42, 42, 2.4, (True, True, False))
        .edges("|Z and (>Y or <Y)").fillet(4)
        .faces(">>Z[-2]").edges("<Z").chamfer(2.39999999)
    )


def draw_bases(
    self: Workplane,
    prop: Properties
) -> Workplane:
    return (
        self
        .rarray(42, 42, prop.units_wide, prop.units_long)
        .eachpoint(lambda loc: (
            cq.Workplane()
            .drawBase()
            .val().located(loc)
        ))
    )


def draw_buckets(
    self: Workplane,
    prop: Properties
) -> Workplane:

    is_drawer_too_small = False
    small_drawer_width = 15

    sketches = []
    x_origin, y_origin = (1, 1)
    for row in prop.divisions:
        if isinstance(row, int):
            row = [1] * row
        widths = [round(ratio / sum(row) * (prop.width - (len(row) + 1)), 2)
                  for ratio in row]
        height = (prop.length - (prop.units_long + 1)) / prop.units_long

        for width in widths:
            if width < small_drawer_width:
                is_drawer_too_small = True
            sketch = (
                cq.Sketch()
                .rect(width, height)
                .vertices()
                .fillet(3)
                .edges()
                .moved(Location(Vector(
                    width / 2,
                    -height / 2
                )))
                .moved(Location(Vector(
                    -prop.width / 2 + x_origin,
                    prop.length / 2 - y_origin
                )))
            )
            x_origin = x_origin + width + 1
            sketches.append(sketch)
        x_origin = 1
        y_origin = y_origin + height + 1

    if is_drawer_too_small:
        warnings.warn(
            f"Drawer width is less than or equal to {small_drawer_width}mm",
            SmallDimensionsWarning
        )

    return (
        self
        .faces("<Z[0]").workplane(centerOption="CenterOfBoundBox").tag("base")
        .box(prop.width, prop.length, prop.height, (True, True, False))
        .edges("|Z").fillet(4)
        .faces(">Z")
        .workplane()
        .placeSketch(*sketches)
        .extrude(BOTTOM_THICKNESS - prop.height, "cut")
    )


def draw_mate(
    self: Workplane,
    prop: Properties
) -> Workplane:

    width = prop.width - 0.5
    length = prop.length - 0.5
    outer_fillet = 3.75

    s1 = (
        cq.Sketch()
        .rect(width, length)
        .vertices().fillet(outer_fillet)
    )

    s2 = (
        cq.Sketch()
        .rect(width - 1.9 * 2, length - 1.9 * 2)
        .vertices().fillet(outer_fillet - 1.9)
    )

    s3 = (
        cq.Sketch()
        .rect(width - 2.6 * 2, length - 2.6 * 2)
        .vertices().fillet(outer_fillet - 2.6)
    )

    s4 = (
        cq.Sketch()
        .rect(width - 1 * 2, length - 1 * 2)
        .vertices().fillet(outer_fillet - 1)
    )

    top = (
        cq.Workplane().copyWorkplane(
            self.workplaneFromTagged("base").workplane(offset=prop.height - 2.84)
        )
        .box(width, length, 7.24, (True, True, False))
        .edges("|Z").fillet(outer_fillet)
        .faces(">Z")
        .placeSketch(
            s1,
            s2.moved(Location(Vector(0, 0, -1.9))),
            s2.moved(Location(Vector(0, 0, -3.7))),
            s3.moved(Location(Vector(0, 0, -4.4))),
            s3.moved(Location(Vector(0, 0, -5.6))),
            s4.moved(Location(Vector(0, 0, -7.24)))
        )
        .loft(True, "s")
    )

    return self.union(top)


def draw_front_surface(
    self: Workplane,
    prop: Properties
) -> Workplane:
    return (
        self.faces(">Z[3]")
        .workplane()
        .transformed(offset=(0, -prop.length / 2 + 1))
        .box(prop.width, 1.85, prop.height - 2, (True, False, False))
    )


def draw_finger_scoops(
    self: Workplane,
    prop: Properties
) -> Workplane:

    if not prop.draw_finger_scoop:
        return self

    bucket_length = (prop.length - (prop.units_long + 1)) / prop.units_long
    scoop_radius = min(prop.height * 0.6, bucket_length * 0.9)

    sketches = []
    for i in range(0, prop.units_long):
        sketch = (
            cq.Sketch()
            .rect(scoop_radius, scoop_radius)
            .vertices(">X and >Y")
            .circle(scoop_radius, mode="s")
            .moved(Location(Vector(
                scoop_radius / 2 -
                0.5 * bucket_length * prop.units_long -
                math.floor(prop.units_long / 2) +
                (0.5 if prop.units_long % 2 == 0 else 0),
                scoop_radius / 2 - (prop.height - BOTTOM_THICKNESS) / 2)))
            .moved(Location(Vector(
                i * (bucket_length + 1) + (1.6 if i == 0 else 0),
                0
            )))
        )
        sketches.append(sketch)

    return (
        self.faces(">X[1]")
        .workplane(centerOption="CenterOfBoundBox")
        .placeSketch(*sketches)
        .extrude(prop.width - 1)
    )


def draw_label_ledge(
    self: Workplane,
    prop: Properties
) -> Workplane:

    if not prop.draw_label_ledge:
        return self
    

    bucket_length = (prop.length - (prop.units_long + 1)) / prop.units_long
    ledge_length = 12 + 0.75

    if prop.height < ledge_length + 0.5:
        warnings.warn(
            "Label ledges cannot be drawn as the specified unit height is too low.",
            CannotDrawLabelLedgesWarning
        )
        return self

    sketches = []
    for i in range(0, prop.units_long):
        last_offset = 3 if i == prop.units_long - 1 else 0

        sketch = (
            cq.Sketch()
            .segment((last_offset, 0), (-ledge_length, 0))
            .segment((last_offset, -ledge_length - last_offset))
            .close()
            .assemble()
            .vertices("<X")
            .fillet(0.6)
            .moved(Location(Vector(
                - 0.5 - (0.5 * prop.units_long - 1) * (bucket_length + 1),
                (prop.height - BOTTOM_THICKNESS) / 2)))
            .moved(Location(Vector(
                i * (bucket_length + 1)
                - last_offset,
                0
            )))
        )
        sketches.append(sketch)

    return (
        self.faces(">X[1]")
        .workplane(centerOption="CenterOfBoundBox")
        .placeSketch(*sketches)
        .extrude(prop.width - 1.5)
    )


def draw_magnet_bore_holes(
    self: Workplane,
    prop: Properties
) -> Workplane:

    self.plane.zDir = Vector(0, 0, -1)
    if not (prop.make_magnet_hole or prop.make_screw_hole):
        return self

    self = (
        self
        .faces("<Z[-1]")
        .faces(cq.selectors.AreaNthSelector(-1))
        .rect(26, 26, forConstruction=True)
        .vertices()
    )

    if prop.make_screw_hole is True:
        self = self.cboreHole(3, 6.5, 2.4, 6)
    elif prop.make_magnet_hole is True:
        self = self.hole(6.5, 2.4)

    return self

def shave_outer_shell(
    self: Workplane,
    prop: Properties
) -> Workplane:
    return (
        self
        .faces("<Z[-1]")
        .faces(cq.selectors.AreaNthSelector(-1))
        .workplane(centerOption="CenterOfBoundBox")
        .sketch()
        .rect(prop.width, prop.length, tag="outer")
        .rect(prop.width - 0.5, prop.length - 0.5, mode="s", tag="inner")
        .vertices(tag="outer")
        .vertices(tag="inner").fillet(3.75)
        .finalize()
        .cutThruAll()
    )


Workplane.drawBase = draw_base
Workplane.drawBases = draw_bases
Workplane.drawBuckets = draw_buckets
Workplane.drawMate = draw_mate
Workplane.drawFrontSurface = draw_front_surface
Workplane.drawFingerScoops = draw_finger_scoops
Workplane.drawLabelLedge = draw_label_ledge
Workplane.drawMagnetBoreHoles = draw_magnet_bore_holes
Workplane.shaveOuterShell = shave_outer_shell


def make_box(
    prop: Properties,
    out_file: Union[str, None] = None,
    export_type: Optional[Literal["STL", "STEP", "AMF", "SVG", "TJS", "DXF", "VRML", "VTP"]] = None,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.1,
    opt = None
) -> Workplane:
    box = (
        cq.Workplane()
        .drawBases(prop)
        .drawBuckets(prop)
        .drawFrontSurface(prop)
        .drawFingerScoops(prop)
        .drawLabelLedge(prop)
        .drawMate(prop)
        .drawMagnetBoreHoles(prop)
        .shaveOuterShell(prop)
    )

    if out_file:
        export_box(
            box,
            out_file=out_file,
            export_type=export_type,
            tolerance=tolerance,
            angular_tolerance=angular_tolerance,
            opt=opt
        )
    return box


def export_box(
    box: Workplane,
    out_file: Union[str, None] = None,
    export_type: Optional[Literal["STL", "STEP", "AMF", "SVG", "TJS", "DXF", "VRML", "VTP"]] = None,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.1,
    opt = None
) -> Workplane:
    cq.exporters.export(
        box,
        out_file,
        exportType=export_type,
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
        opt=opt
    )
    return box


def export_svg(
    box: Workplane,
    out_file: Union[str, None] = None,
    opt = None
) -> Workplane:

    settings = {
        "showAxes": False,
        "marginLeft": 10,
        "marginTop": 10,
        "projectionDir": (2.75, -2.6, 2),
        "showHidden": False,
        "focus": 500
    }
    if opt:
        settings.update(opt)

    export_box(
        box,
        out_file=out_file,
        export_type="SVG",
        opt=settings
    )

    return box
