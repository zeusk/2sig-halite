import hlt
from hlt import helper
import logging
import time
import math
from hlt.geom import Point, Seg, cent_of_mass
from collections import OrderedDict
from hlt.constants import *
from hlt.entity import Position

# GAME START
game = hlt.Game("HunterKiller")
turn = 0
rush_policy = False
rush_policy_num_players_max = 2
rush_policy_dis_players_max = 16 * hlt.constants.MAX_SPEED

while True:
    start_time = time.process_time()
    gmap = game.update_map()

    logging.info("TURN {}".format(turn))

    # Pre-process stage, decide if we want to rush or execute our default policy
    if turn == 0:
        nplayers = len(gmap.all_players())
        e_cent = geom.cent_of_mass([e.loc for e in gmap.en_ships()])
        m_cent = geom.cent_of_mass([m.loc for m in gmap.my_ships()])
        dplayers = geom.pp_dist2(e_cent, m_cent)
        rush_policy = nplayers <= rush_policy_num_players_max && dplayers <= rush_policy_dis_players_max

    # Execute out strategy
    #HANDLE ATKS AT T=0
    has_atked = set()
    for s in gmap.all_uships():
        atks = []
        for t in gmap.all_ships():
            if s.owner != t.owner and s.dist_to(t) < WEAPON_RADIUS:
                atks.append(t)

        if atks:
            has_atked.add(s)
            for t in atks:
                t.hp -= WEAPON_DAMAGE/len(atks)
                if t.hp <= 0:
                    gmap.remove_ship(t)

    #THREAT LEVEL CODE
    threat_level = {}
    if gmap.my_dships():
        for e in gmap.en_uships():
            min_turns = helper.to_turns(min(map(lambda t:e.dist_to(s),gmap.my_dships()))-WEAPON_RADIUS)
            min_turns = max([0,min_turns])
            if min_turns < 1:
                threat_level[e] = 1

    #OTHER INFO
    rem_dock = {p:p.rem_spots() for p in gmap.unowned_planets() + gmap.my_uplanets()}
    en_ship_assigned = {s:math.ceil(s.hp/WEAPON_DAMAGE) for s in gmap.en_ships()}

    #MOVE LIST WITH PRIORITIES
    move_list = {}
    b = [e for e in gmap.unowned_planets() + gmap.my_uplanets() if e.remaining_resources > 0]
    for s in gmap.my_uships():
        for e in b + gmap.en_ships():
            if type(e) == hlt.entity.Planet:
                if rush_policy == True:
                    continue
                d = helper.to_turns(s.dist_to(s.closest_pt_to(e))) + 2
                if e.owner != gmap.get_me():
                    d += .5
            elif type(e) == hlt.entity.Ship:
                d = helper.to_turns(s.dist_to(e) - WEAPON_RADIUS)
                if e in threat_level:
                    d -= threat_level[e]
                elif not e.can_atk():
                    d -= 1

            move_list[(s,e)] = d

    move_list = OrderedDict(sorted(move_list.items(), key=lambda t:t[1]))

    #ITERATE THROUGH MOVES
    move_table = {}
    first_targ = OrderedDict()
    unassigned = set(gmap.my_uships())

    logging.info("HALFWAY TIME: {}".format(time.process_time() - start_time))

    cmds = []
    for (s,e), d in move_list.items():
        if time.process_time() - start_time > 1.9:
            logging.info("TOOK WAY TOO MUCH TIME")
            break

        nav_cmd = None
        move = None

        if s not in unassigned or len(unassigned) == 0:
            continue

        if s not in first_targ:
            first_targ[s] = e

        if type(e) == hlt.entity.Planet and rem_dock[e] > 0:
            if s.can_dock(e):
                nav_cmd = s.dock(e)
                rem_dock[e] -= 1
                cmds.append(nav_cmd)
            else:
                nav_cmd, move = helper.nav(s,s.closest_pt_to(e), gmap, None,move_table)
                if nav_cmd:
                    rem_dock[e] -= 1
                    cmds.append(nav_cmd)
                if move:
                    move_table[s] = move
            unassigned.discard(s)
        elif type(e) == hlt.entity.Ship:

            # WITHIN POTENTIAL ATTACK RANGE
            if s.dist_to(e) <= WEAPON_RADIUS + 2*MAX_SPEED:
                # ATTACK
                if s in has_atked:
                    nav_cmd, move = helper.nav(s,s.closest_pt_to(e,6),gmap,None,move_table)
                else:
                    nav_cmd, move = helper.nav(s,s.closest_pt_to(e),gmap,None,move_table)
                if move:
                    atk_pos = Position(move.p2)
                else:
                    atk_pos = Position(s.loc, s.loc + Point.polar(MAX_SPEED,s.angle_to(e)))
                atk_ens = [t for t in gmap.en_uships() if t.dist_to(atk_pos) <= WEAPON_RADIUS + MAX_SPEED]
                atk_frs = [t for t in gmap.my_uships() if t.dist_to(atk_pos) <= MAX_SPEED+2]
                if len(atk_frs) > len(atk_ens):
                    if nav_cmd:
                        en_ship_assigned[e] -= 1
                        cmds.append(nav_cmd)
                    if move:
                        move_table[s] = move
                    unassigned.discard(s)
                    continue

                # OTHER OPTIONS
                en_dships = sorted(gmap.en_dships(),key=lambda t:s.dist_to(t))
                my_dships = sorted(gmap.my_dships(),key=lambda t:e.dist_to(t))
                my_dship = my_dships[0] if my_dships else None
                en_dship = en_dships[0] if en_dships else None

                if time.process_time() - start_time > 1.9:
                    logging.info("TOOK WAY TOO MUCH TIME")
                    break

                # HARASS
                if en_dship != None and (my_dship == None or s.dist_to(en_dship)+7*(len(gmap.all_players()) - 1) < e.dist_to(my_dship)) and en_ship_assigned[en_dship] > 0:
                    chasers = [t for t in gmap.en_uships() if s.dist_to(t) <= 2*MAX_SPEED+WEAPON_RADIUS]
                    nav_cmd, move = helper.harass_nav(s,en_dship,gmap,None,move_table,enemies=chasers)
                    if nav_cmd:
                        cmds.append(nav_cmd)
                        if move:
                            move_table[s] = move
                        unassigned.discard(s)
                        #logging.info("{} harass {}".format(s,en_dship))
                        continue

                if time.process_time() - start_time > 1.9:
                    logging.info("TOOK WAY TOO MUCH TIME")
                    break

                # DEFEND
                if my_dship != None:
                    def_frns = [t for t in gmap.my_uships() if t.dist_to(my_dship) <= MAX_SPEED + 3]
                    def_ens = [t for t in gmap.en_uships() if t.dist_to(my_dship) <= MAX_SPEED + WEAPON_RADIUS]
                    def_dfrns = [t for t in gmap.my_dships() if t.dist_to(my_dship) <= 3]
                    if e.dist_to(my_dship) <= WEAPON_RADIUS + MAX_SPEED and len(def_frns+def_dfrns) >= len(def_ens):
                        #logging.info("{} defend {}".format(s,my_dship))
                        pos = Position(my_dship.loc + Point.polar(.500001, my_dship.angle_to(e)+90))
                        nav_cmd, move = helper.nav(s,pos,gmap,None,move_table)
                    else:
                        enemies = [t for t in gmap.en_uships() if s.dist_to(t)<= MAX_SPEED*2 + WEAPON_RADIUS]
                        enemies = sorted(enemies,key=lambda t:s.dist_to(t))
                        en_cent = helper.cent_of_mass(enemies)
                        if len(enemies) == 0:
                            logging.info("{} defend {}".format(s,e))
                        d = WEAPON_RADIUS+len(gmap.all_players())-2 - (s.dist_to(enemies[0]) - MAX_SPEED)
                        dv = Point.polar(d, s.angle_to(en_cent))
                        pos = Position(s.loc - dv)
                        nav_cmd, move = helper.nav(s,pos,gmap,None,move_table)

                    if nav_cmd:
                        cmds.append(nav_cmd)
                    if move:
                        move_table[s] = move
                    unassigned.discard(s)
                    continue

                if time.process_time() - start_time > 1.9:
                    logging.info("TOOK WAY TOO MUCH TIME")
                    break

                #FLEE
                enemies = [t for t in gmap.en_uships() if s.dist_to(t)<= MAX_SPEED*2 + WEAPON_RADIUS]
                enemies = sorted(enemies,key=lambda t:s.dist_to(t))
                en_cent = helper.cent_of_mass(enemies)
                dv = Point.polar(MAX_SPEED, s.angle_to(en_cent))
                pos = Position(s.loc - dv)
                nav_cmd, move = helper.nav(s,pos,gmap,None,move_table)
                if nav_cmd:
                    cmds.append(nav_cmd)
                if move:
                    move_table[s] = move
                unassigned.discard(s)

            # OUTSIDE POTENTIAL ATTACK RANGE
            elif en_ship_assigned[e] > 0:
                if time.process_time() - start_time > 1.9:
                    logging.info("TOOK WAY TOO MUCH TIME")
                    break
                nav_cmd, move = helper.nav(s,e,gmap,None,move_table)
                if nav_cmd:
                    en_ship_assigned[e] -= 1
                    cmds.append(nav_cmd)
                if move:
                    move_table[s] = move
                unassigned.discard(s)

    for s in first_targ:
        if time.process_time() - start_time > 1.9:
            logging.info("TOOK WAY TOO MUCH TIME")
            break
        if s in unassigned:
            nav_cmd, move = helper.nav(s,s.closest_pt_to(first_targ[s]),gmap, None, move_table)
            if nav_cmd:
                cmds.append(nav_cmd)
            if move:
                move_table[s] = move

    # Send out game commands
    game.send_command_queue(cmds)

    turn = turn + 1
    elapsed_time = time.process_time() - start_time
    if elapsed_time >= .5:
        logging.info("Time Elapsed CRITICAL: {}".format(elapsed_time))
    else:
        logging.info("Time Elapsed: {}".format(elapsed_time))
    # TURN END
# GAME END
