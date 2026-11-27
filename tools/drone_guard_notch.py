"""Reference-derived guard notch in the existing side mounting plane."""
import FreeCAD as App
import Part

# Back-projected from fixed frame 180 at X=108 mm. Appearance assumptions;
# fitted-view observations are not independent accuracy or manufacturing data.
GUARD_NOTCH_YZ = ((197.89647630384934, 151.07348882695686), (221.49489304090787, 152.19817679589505), (218.2397193570609, 146.52082000684726), (214.9740253089069, 140.8251146233702), (208.86309486557406, 134.49928009033835), (202.2447762411569, 128.58048942248126), (197.96309903498235, 127.88333987413347))


def trim_guard_notch(shape, side):
    points = [App.Vector(side*103, y, z) for y,z in GUARD_NOTCH_YZ]
    cutter = Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(side*18,0,0))
    result = shape.cut(cutter).removeSplitter()
    result.check(True)
    if not result.isValid() or not result.isClosed() or len(result.Solids)!=1:
        raise ValueError('Invalid continuous guard notch')
    return result
