from . import entity, game_map, geom
from hlt.entity import Position, Ship
from .geom import Point, Seg, min_dist, ps_dist, pp_dist
from .constants import *
import math
import logging
from collections import OrderedDict

def to_turns(dist, speed = MAX_SPEED):
    return dist/speed

def nav(ship, targ, gmap, obs, move_table={}, speed=MAX_SPEED, max_deviation=90):
    dist = ship.dist_to(targ)
    angle = round(ship.angle_to(targ))
    speed = speed if (dist >= speed) else int(dist)

    if obs == None:
        obs = [e for e in gmap.all_planets() + gmap.my_dships()
                if ship.dist_to(e)-ship.radius-e.radius <= dist]
        obs.extend([e for e in gmap.my_uships() if e != ship
                        and ship.dist_to(e)-ship.radius-e.radius<=MAX_SPEED*2])


    obs = sorted(obs,key=lambda t:ship.dist_to(t))
    angs = [int(n/2) if n%2==0 else -int(n/2) for n in range(1,max_deviation*2+2)]

    for d_ang in angs:

        move_ang = (angle+d_ang)%360
        d = Point.polar(speed, move_ang)
        move = Seg(ship.loc,ship.loc+d)

        d = Point.polar(dist,move_ang)
        full_move = Seg(ship.loc,ship.loc+d)
        
        if not gmap.contains_pt(move.p2):
            continue

        for e in obs:
            collide_dist = ship.radius+e.radius+.000001
            if e in move_table and min_dist(move,move_table[e]) <= collide_dist:
                break
            elif not e in move_table:
                if type(e) == Ship and e.can_atk():
                    if ps_dist(e.loc,move)<=collide_dist:
                        break
                elif ps_dist(e.loc,full_move) <=collide_dist:
                    break
        else:
            return ship.thrust(speed,move_ang), move

    return None, None

def harass_nav(ship, targ, gmap,obs,move_table={}, speed=MAX_SPEED,max_deviation=180, enemies = []):
    dist = ship.dist_to(targ)
    angle = round(ship.angle_to(targ))

    if obs == None:
        obs = [e for e in gmap.all_planets() + gmap.my_dships()
                if ship.dist_to(e)-ship.radius-e.radius <= max(MAX_SPEED,dist)]
        obs.extend([e for e in gmap.my_uships() if e != ship
                        and ship.dist_to(e)-ship.radius-e.radius<=MAX_SPEED*2])


    obs = sorted(obs,key=lambda t:ship.dist_to(t))
    angs = [int(n/2) if n%2==0 else -int(n/2) for n in range(1,max_deviation*2+2)]


    obs.extend(enemies)
    obs.extend([t for t in gmap.all_dships() if ship.dist_to(t)<= MAX_SPEED+WEAPON_RADIUS])

    for d_ang in angs:
        move_ang = (angle+d_ang)%360
        d = Point.polar(speed, move_ang)
        move = Seg(ship.loc,ship.loc+d)

        full_d = Point.polar(max(MAX_SPEED,dist),move_ang)
        full_move = Seg(ship.loc,ship.loc+full_d)
        if not gmap.contains_pt(move.p2):
            continue

        for e in obs:
            collide_dist = ship.radius+e.radius+.000001
            if e in enemies:
                en_speed = pp_dist(e.loc,move.p2) if pp_dist(e.loc,move.p2) < MAX_SPEED else MAX_SPEED
                en_move = Seg(e.loc,e.loc+Point.polar(en_speed,e.angle_to(Position(move.p2))))
                if ship.dist_to(e) <= collide_dist+WEAPON_RADIUS:
                    pass
                elif min_dist(move,en_move) <= collide_dist + WEAPON_RADIUS:
                    break
            elif e == targ:
                if ps_dist(e.loc,move)<=collide_dist:
                    break
            elif e in move_table and min_dist(move,move_table[e]) <= collide_dist:
                break
            elif not e in move_table:
                if type(e) == Ship and e.can_atk():
                    if ps_dist(e.loc,move)<=collide_dist:
                        break
                elif ps_dist(e.loc,full_move) <=collide_dist:
                    break
        else:
            return ship.thrust(speed,move_ang), move

    return None, None

def num_hits(ship):
    return math.ceil(ship.hp/WEAPON_DAMAGE)

def cent_of_mass(entities):
    return Position(geom.cent_of_mass([e.loc for e in entities]))