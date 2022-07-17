from gridfinity import Properties, make_box, export_box, export_svg

UNITS_WIDE = 4 # The number of Gridfinity units wide (left to right)
UNITS_LONG = 3 # The number of Gridfinity units long (front to back)
UNITS_HIGH = 4 # The number of Gridfinity units high (in 7mm increments)

# This define how each row is divided. The number of entries in this list
# must be equal to the number of UNITS_LONG defined above.
DIVISIONS = [
    [1, 2, 1], # If defined as a list, it will make n number of drawers
               # where n is the number of items in the list. Each of the
               # drawers will have the relative width defined.
               # For example, this entry will create 3 drawers, the left
               # and right ones will be half the size of the center one.

    3,         # If entered as a single integer, it will make n drawers,
               # each of them an equal size. This entry will make 3
               # equally sized drawers. 
    
    [10, 90]   # You can treat them like percentages too if you wanted to. 
               # The numbers are ratio'd dynamically.
]

# Draw the rounded finger scoop on the front of each drawer.
DRAW_FINGER_SCOOP = True
# Draws a 12mm label ledge on each row.
DRAW_LABEL_LEDGE = True

# Make holes on the bottom for magnets.
MAKE_MAGNET_HOLE = False
# Make holes on the bottom for screws.
MAKE_SCREW_HOLE = False



# Make the properties object to be passed to the make_box method.
properties = Properties(
    UNITS_WIDE,
    UNITS_LONG,
    UNITS_HIGH,
    DIVISIONS,
    DRAW_FINGER_SCOOP,
    DRAW_LABEL_LEDGE,
    MAKE_MAGNET_HOLE,
    MAKE_SCREW_HOLE)


# This makes the box, writes it to an output STL, and returns it.
# If no filename is provided, it will not output it to a file.
result = make_box(properties, "output.stl")


# If you did not output to a file when making the box, you may use
# the export_box function to export it.
export_box(result, "output2.stl")


# Or if you want a nicely rendered SVG, use export_svg
export_svg(result, "output.svg")

