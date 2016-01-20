import math

def perspectiveGL(fovY, aspect, zNear, zFar):
    pi = 3.1415926535897932384626433832795;
    # GLdouble fW, fH;

    #fH = tan( (fovY / 2) / 180 * pi ) * zNear;
    fH = math.tan((fovY/360) * pi) * zNear
    fW = fH * aspect

    #glFrustum( -fW, fW, -fH, fH, zNear, zFar );
    print("left, right, bottom, top = %f, %f, %f, %f" % (-fW, fW, -fH, fH))
    print("zNear, zFar = %f, %f" % (zNear, zFar))

perspectiveGL(60, 1000 / 700, 0.1, 1000.0)


# http://arstechnica.com/civis/viewtopic.php?t=147154
http://stackoverflow.com/questions/12943164/replacement-for-gluperspective-with-glfrustrum