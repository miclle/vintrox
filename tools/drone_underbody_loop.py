"""Build the mirrored decorative loops in final assembly coordinates."""

import FreeCAD as App
import Part


LOOP_RADIUS = 2.2
LOOP_PARAMETERS = (
    0.0, 0.10000995443738048, 0.2057098257661289, 0.321459638593329,
    0.4338601671604783, 0.5393807011390678, 0.6348829144468303,
    0.7248050580073706, 0.8279803378564432, 0.9281997215595998, 1.0,
)
RIGHT_LOOP_POINTS = (
    (44.5, 72.8, 57.0),
    (45.05255527685936, 74.83731297688911, 39.869170519396846),
    (45.20372764930619, 75.9462343071762, 23.787948462743604),
    (44.90288669051388, 81.21741881307405, 10.418541805360665),
    (44.79191481031275, 91.43072248919596, 2.711494940061688),
    (45.362266911001, 105.60386724424727, 4.353514553059756),
    (46.30846392172454, 118.38631254004237, 8.35600159604193),
    (47.040557093125585, 126.23862789441503, 17.08370315706601),
    (46.995737962631054, 128.3927026554097, 30.620109832830565),
    (45.80455849503019, 127.29552740199324, 45.564878781119994),
    (44.5, 126.6, 57.0),
)


def loop_loft(points, parameters=None, radius=LOOP_RADIUS):
    curve = Part.BSplineCurve()
    interpolation = {"Parameters": parameters} if parameters is not None else {}
    curve.interpolate([App.Vector(*point) for point in points], **interpolation)
    # Circular normal sections produce a smooth loft where the pipe shell
    # reported GeomAbs_C0 despite the smooth centreline.
    first, last = curve.FirstParameter, curve.LastParameter
    step = (last - first) / 39
    stations = [first + index * step for index in range(39)] + [last]
    sections = [
        Part.Wire([Part.makeCircle(radius, curve.value(station), curve.tangent(station)[0])])
        for station in stations
    ]
    return Part.makeLoft(sections, True, False)
