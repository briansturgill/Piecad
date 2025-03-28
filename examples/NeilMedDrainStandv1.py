$fn=50;

wall=2;
r=5;
x=120;
y=70;
z=10;
sh = 150;
sr = 25/2;
bh=35;
br=32/2;
pw=wall*8;
pd=wall*2;

module round_rect(dim, radius) {
    hull() {
        translate([radius, radius, 0]) circle(radius);
        translate([dim.x-radius, radius, 0]) circle(radius);
        translate([radius, dim.y-radius, 0]) circle(radius);
        translate([dim.x-radius, dim.y-radius, 0]) circle(radius);
    }
}
 
module rcube(dim, radius) {
    linear_extrude(dim.z) {
        round_rect([dim.x, dim.y], radius);
    }   
}

module DrainBase() {
    difference() {
        translate([-wall, -wall, -wall]) rcube([x+2*wall, y+2*wall, z+wall], r);
        rcube([x, y, z+wall], r);
    }
}

module DrainBottom(h) {
    translate([wall, pw, 1])
    rotate([0, 0, -180]) {
        translate([-pw+wall, 0, 0]) rcube([pw, pw, pd], 2);
        rcube([pd, pw, h], 2);
    }
 }

module DrainTop(cylr) {
    thk = 15*wall;
    difference() {
        union() {
            cylinder(h=wall*3, r=cylr+wall);
            translate([-(cylr+pd+4*wall), -(cylr+4*wall)/2, 0]) rcube([pd+4*wall, pw+3*wall, thk], 2);
        }
        translate([0, 0,-1]) cylinder(h=wall*2*2, r=cylr);
        translate([-(cylr+pd+3*wall), -(cylr+1*wall)/2, 1]) rcube([pd+1, pw, thk], 2);
    }
}

module DrainTops() {
    translate([0, y+30, 0]) rotate([0, 0, 0]) DrainTop(br);
    
    translate([0, y*2+10, 0]) rotate([0, 0, 0]) DrainTop(sr);
}

module DrainStand() {
    DrainBase();
    translate([x/6, y/2-4*wall, -wall])
        DrainBottom(sh);
    translate([(x - 2.5*(x/6)), y/2-4*wall, -wall])
        DrainBottom(bh);
}

//translate([0, 0, wall]) DrainStand();
DrainTops();

