# Derived from threads.scad: https://github.com/rcolyer/threads-scad.git
# Created 2016-2017 by Ryan A. Colyer.
# This work is released with CC0 into the public domain.
# https://creativecommons.org/publicdomain/zero/1.0/
#
# https://www.thingiverse.com/thing:1686322
#
# v2.1

def lookup(key: float, table: List[(float, float)]):
    high_k = high_v = low_k = low_v = 0.0
    for k, v in table:
        if k <= key and (k > low_k or low_k > key):
            low_k = k
            low_v = v
        if k >= key and (k < high_k or low_k < key):
            high_k = k
            high_v = v

    if key > high_k or key < low_k:
        raise ValueError

    # Linear interpolation
    f = (k - low_k) / (high_k - low_k)
    return (high_v * f) + (low_v * (1 - f))

screw_resolution = 0.2  # in mm


# Provides standard metric thread pitches.
def ThreadPitch(diameter: float):
    if diameter > 64:
        return diameter * 6.0 / 64
    return lookup(diameter, (
      (2, 0.4),
      (2.5, 0.45),
      (3, 0.5),
      (4, 0.7),
      (5, 0.8),
      (6, 1.0),
      (7, 1.0),
      (8, 1.25),
      (10, 1.5),
      (12, 1.75),
      (14, 2.0),
      (16, 2.0),
      (18, 2.5),
      (20, 2.5),
      (22, 2.5),
      (24, 3.0),
      (27, 3.0),
      (30, 3.5),
      (33, 3.5),
      (36, 4.0),
      (39, 4.0),
      (42, 4.5),
      (48, 5.0),
      (52, 5.0),
      (56, 5.5),
      (60, 5.5),
      (64, 6.0)
    ))

# This generates a closed polyhedron from an array of arrays of points,
# with each inner array tracing out one loop outlining the polyhedron.
# pointarrays should contain an array of N arrays each of size P outlining a
# closed manifold.  The points must obey the right-hand rule.  For example,
# looking down, the P points in the inner arrays are counter-clockwise in a
# loop, while the N point arrays increase in height.  Points in each inner
# array do not need to be equal height, but they usually should not meet or
# cross the line segments from the adjacent points in the other arrays.
# (N>=2, P>=3)
# Core triangles:
#   [j][i], [j+1][i], [j+1][(i+1)%P]
#   [j][i], [j+1][(i+1)%P], [j][(i+1)%P]
#   Then triangles are formed in a loop with the middle point of the first
#   and last array.
def ClosePoints(pointarrays) :
    def recurse_avg(arr, n=0, p=[0,0,0]):
        if  (n>=len(arr)):
            return p
        else:
            return recurse_avg(arr, n+1, p+(arr[n]-p)/(n+1))

    N = len(pointarrays)
    P = len(pointarrays[0])
    NP = N*P
    lastarr = pointarrays[N-1]
    midbot = recurse_avg(pointarrays[0])
    midtop = recurse_avg(pointarrays[N-1])

    faces_bot = (
        [0,i+1,1+(i+1)%len(pointarrays[0])] for i in range(P)
       )

    loop_offset = 1
    bot_len = loop_offset + P

    faces_loop = []
    for j in range(N-1):
        for i in range(P):
            for t in range(2):
                if t == 0:
                    faces_loop.append(
                         [j*P+i+loop_offset, (j+1)*P+i+loop_offset, (j+1)*P+(i+1)%P+loop_offset])
                else:
                    faces_loop.append(
                        [j*P+i+loop_offset, (j+1)*P+(i+1)%P+loop_offset, j*P+(i+1)%P+loop_offset])

    top_offset = loop_offset + NP - P
    midtop_offset = top_offset + P

    faces_top = (
        (midtop_offset,top_offset+(i+1)%P,top_offset+i)  for i in range(P)
    )

    points = []
    for i in range(-1, NP+1):
        if i<0: 
            points.append(midbot)
        elif i==NP:
            points.append(midtop)
        else:
            points.append(pointarrays[floor(i/P)][i%P])

    faces = concat(faces_bot, faces_loop, faces_top)

    polyhedron(points=points, faces=faces)



# This creates a vertical rod at the origin with external threads.  It uses
# metric standards by default.
def ScrewThread(outer_diam, height, pitch=0, tooth_angle=30, tolerance=0.4, tip_height=0, tooth_height=0, tip_min_fract=0):

    if pitch == 0:
        pitch = ThreadPitch(outer_diam)
    if tooth_height == 0: 
        tooth_height = pitch
    if tip_min_fract < 0:
        tip_min_fract =  0
    elif tip_min_fract > 0.9999:
        tip_min_fract = 0.9999

    outer_diam_cor = outer_diam + 0.25*tolerance # Plastic shrinkage correction
    inner_diam = outer_diam - tooth_height/tan(tooth_angle)
    if outer_diam_cor < screw_resolution:
        o_r = screw_resolution/2
    else:
        o_r = outer_diam_cor / 2
    if inner_diam < screw_resolution:
        ir = screw_resolution/2
    else:
        ir =inner_diam / 2
    if height < screw_resolution:
        height = screw_resolution

    steps_per_loop_try = ceil(2*3.14159265359*o_r / screw_resolution)
    if steps_per_loop_try < 4:
        steps_per_loop = 4
    else:
        steps_per_loop = steps_per_loop_try
    hs_ext = 3
    hsteps = ceil(3 * height / pitch) + 2*hs_ext

    extent = o_r - ir

    tip_start = height-tip_height
    tip_height_sc = tip_height / (1-tip_min_fract)

    if tip_height_sc > tooth_height/2:
        tip_height_ir = tip_height_sc - tooth_height/2
    else:
        tip_height_ir = tip_height_sc

    if tip_height_sc > tooth_height:
        tip_height_w = tooth_height
    else:
        tip_height_w = tip_height_sc
    tip_wstart = height + tip_height_sc - tip_height - tip_height_w

    def tooth_width(a, h, pitch, tooth_height, extent):
        ang_full = h*360.0/pitch-a,
        ang_pn = atan2(sin(ang_full), cos(ang_full)),
        if ang_pn < 0:
            ang = ang_pn+360
        else:
            ang = ang_pn
        frac = ang/360,
        tfrac_half = tooth_height / (2*pitch),
        tfrac_cut = 2*tfrac_half
        if frac > tfrac_cut:
            return 0
        elif frac <= tfrac_half:
            return (frac / tfrac_half) * extent
        else:
            return (1 - (frac - tfrac_half)/tfrac_half) * extent

      pointarrays = []
      for hs in range(hsteps+1):
          for s in range(steps_per_loop):
            ang_full = s*360.0/steps_per_loop,
            ang_pn = atan2(sin(ang_full), cos(ang_full)),
            ang = ang_pn < 0 ? ang_pn+360 : ang_pn,

            h_fudge = pitch*0.001,

            h_mod =
              (hs%3 == 2) ?
                ((s == steps_per_loop-1) ? tooth_height - h_fudge : (
                 (s == steps_per_loop-2) ? tooth_height/2 : 0)) : (
              (hs%3 == 0) ?
                ((s == steps_per_loop-1) ? pitch-tooth_height/2 : (
                 (s == steps_per_loop-2) ? pitch-tooth_height + h_fudge : 0)) :
                ((s == steps_per_loop-1) ? pitch-tooth_height/2 + h_fudge : (
                 (s == steps_per_loop-2) ? tooth_height/2 : 0))
              ),

            h_level =
              (hs%3 == 2) ? tooth_height - h_fudge : (
              (hs%3 == 0) ? 0 : tooth_height/2),

            h_ub = floor((hs-hs_ext)/3) * pitch
              + h_level + ang*pitch/360.0 - h_mod,
            h_max = height - (hsteps-hs) * h_fudge,
            h_min = hs * h_fudge,
            h = (h_ub < h_min) ? h_min : ((h_ub > h_max) ? h_max : h_ub),

            ht = h - tip_start,
            hf_ir = ht/tip_height_ir,
            ht_w = h - tip_wstart,
            hf_w_t = ht_w/tip_height_w,
            hf_w = (hf_w_t < 0) ? 0 : ((hf_w_t > 1) ? 1 : hf_w_t),

            ext_tip = (h <= tip_wstart) ? extent : (1-hf_w) * extent,
            wnormal = tooth_width(ang, h, pitch, tooth_height, ext_tip),
            w = (h <= tip_wstart) ? wnormal :
              (1-hf_w) * wnormal +
              hf_w * (0.1*screw_resolution + (wnormal * wnormal * wnormal /
                (ext_tip*ext_tip+0.1*screw_resolution))),
            r = (ht <= 0) ? ir + w :
              ( (ht < tip_height_ir ? ((2/(1+(hf_ir*hf_ir))-1) * ir) : 0) + w)
            pointarrays.append([r*cos(ang), r*sin(ang), h])

    ClosePoints(pointarrays)

# This creates a threaded hole in its children using metric standards by
# default.
def ScrewHole(child, outer_diam, height, position=[0,0,0], rotation=[0,0,0], pitch=0, tooth_angle=30, tolerance=0.4, tooth_height=0):
  extra_height = 0.001 * height

  return difference(
    child,
    translate(position)
      rotate(rotation)
      translate([0, 0, -extra_height/2])
      ScrewThread(1.01*outer_diam + 1.25*tolerance, height + extra_height,
        pitch, tooth_angle, tolerance, tooth_height=tooth_height)
  )

kid_circle = 34
kid_nut = 24
kid_height = 14
kid_screw_size = 12
kid_tolerance = 0.6

def KidBase():
    return union(
        cylinder(height=kid_height, radius=kid_nut/2.0, segments=6).translate([0,0,2]),
        cylinder(height=2, radius=kid_circle/2.0).translate([0,0,2])
    )
    

# Create a standard sized metric hex nut.
def KidMetricNut(diameter, thickness=0):
    return ScrewHole(KidBase(), kid_screw_size, kid_height, tolerance=kid_tolerance)

# Create a standard sized metric bolt with hex head and hex key.
def KidMetricBolt():
    obj = difference() {
        KidBase(),
        cube([kid_circle, 4, 4], center: True)
    )
    return ScrewHole(obj, kid_screw_size, kid_height-6, tolerance=kid_tolerance)


view(KidMetricBolt())
view(KidMetricNut())
