from piecad import *

inch = 25.4
thk = 2
iota = 1
post = 0.75 * inch
off = 0.25 * inch

hook_l = 5 * inch
hook_h = 5
hook_w = post
slider_l= 3.0*inch
slider_h = hook_h+2*thk+2*iota
slider_w = hook_w+2*thk+2*iota
slider_r = post/2
hook_r = slider_r-thk-iota
ring_r = slider_r*2

def ring(h):
    return difference(
        cylinder(radius = ring_r, height=h),
        cylinder(radius = slider_r, height=h),
    ).translate([ring_r/2, ring_r/2, 0])

tiny = thk+iota
slider = union(
    ring(slider_h),
    difference(
        rectangle([slider_l, slider_w]).extrude(slider_h).translate([0, -tiny, 0]),
        rectangle([hook_l+iota, hook_w+iota]).extrude(hook_h+2*iota).translate([0, 0, thk]),
    ).translate([ring_r, 0, 0])
)

view(slider)

hook = union(
    ring(hook_h),
    rounded_rectangle([hook_l, hook_w], hook_r).extrude(hook_h).translate([ring_r, 0, 0]),
    cylinder(radius=slider_r, height=40).translate([ring_r+hook_l-hook_r-thk-iota, hook_w/2, hook_h]),
    rounded_rectangle([slider_l, hook_w], hook_r).extrude(hook_h).translate([-slider_l, 0, 0]),
)

view(hook)

save("/tmp/head_rest_purse_hanger_slider.obj", slider)
save("/tmp/head_rest_purse_hanger_hook.obj", hook)
