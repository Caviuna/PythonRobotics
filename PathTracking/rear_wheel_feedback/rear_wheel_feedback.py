#! /usr/bin/python
"""

Path tracking simulation with rear wheel feedback steering control and PID speed control.

author: Atsushi Sakai

"""
import math
import matplotlib.pyplot as plt
import unicycle_model
from pycubicspline import pycubicspline

Kp = 1.0  # speed propotional gain
animation = True
#  animation = False


def PIDControl(target, current):
    a = Kp * (target - current)

    return a


def pi_2_pi(angle):
    while(angle > math.pi):
        angle = angle - 2.0 * math.pi

    while(angle < -math.pi):
        angle = angle + 2.0 * math.pi

    return angle


def rear_wheel_feedback_control(state, cx, cy, cyaw, ck, preind):
    KTH = 1.0
    KE = 0.5

    ind, e = calc_nearest_index(state, cx, cy, cyaw)

    k = ck[ind]
    v = state.v
    th_e = pi_2_pi(state.yaw - cyaw[ind])

    omega = v * k * math.cos(th_e) / (1.0 - k * e) - \
        KTH * abs(v) * th_e - KE * v * math.sin(th_e) * e / th_e
    #  pass

    if th_e == 0.0 or omega == 0.0:
        return 0.0, ind

    delta = math.atan2(unicycle_model.L * omega / v, 1.0)

    #  print(k, v, e, th_e, omega, delta)

    return delta, ind


def calc_nearest_index(state, cx, cy, cyaw):
    dx = [state.x - icx for icx in cx]
    dy = [state.y - icy for icy in cy]

    d = [abs(math.sqrt(idx ** 2 + idy ** 2)) for (idx, idy) in zip(dx, dy)]

    mind = min(d)

    ind = d.index(mind)

    dxl = cx[ind] - state.x
    dyl = cy[ind] - state.y

    angle = pi_2_pi(cyaw[ind] - math.atan2(dyl, dxl))
    if angle < 0:
        mind *= -1

    return ind, mind


def closed_loop_prediction(cx, cy, cyaw, ck, speed_profile, goal):

    T = 500.0  # max simulation time
    goal_dis = 0.3
    stop_speed = 0.05

    state = unicycle_model.State(x=-0.0, y=-0.0, yaw=0.0, v=0.0)

    time = 0.0
    x = [state.x]
    y = [state.y]
    yaw = [state.yaw]
    v = [state.v]
    t = [0.0]
    target_ind = calc_nearest_index(state, cx, cy, cyaw)

    while T >= time:
        di, target_ind = rear_wheel_feedback_control(
            state, cx, cy, cyaw, ck, target_ind)
        ai = PIDControl(speed_profile[target_ind], state.v)
        state = unicycle_model.update(state, ai, di)

        if abs(state.v) <= stop_speed:
            target_ind += 1

        time = time + unicycle_model.dt

        # check goal
        dx = state.x - goal[0]
        dy = state.y - goal[1]
        if math.sqrt(dx ** 2 + dy ** 2) <= goal_dis:
            print("Goal")
            break

        x.append(state.x)
        y.append(state.y)
        yaw.append(state.yaw)
        v.append(state.v)
        t.append(time)

        if target_ind % 1 == 0 and animation:
            plt.cla()
            plt.plot(cx, cy, "-r", label="course")
            plt.plot(x, y, "ob", label="trajectory")
            plt.plot(cx[target_ind], cy[target_ind], "xg", label="target")
            plt.axis("equal")
            plt.grid(True)
            plt.title("speed:" + str(round(state.v, 2)) +
                      "tind:" + str(target_ind))
            plt.pause(0.0001)

    return t, x, y, yaw, v


def set_stop_point(target_speed, cx, cy, cyaw):
    speed_profile = [target_speed] * len(cx)

    d = []
    direction = 1.0

    # Set stop point
    for i in range(len(cx) - 1):
        dx = cx[i + 1] - cx[i]
        dy = cy[i + 1] - cy[i]
        td = math.sqrt(dx ** 2.0 + dy ** 2.0)
        d.append(td)
        dyaw = cyaw[i + 1] - cyaw[i]
        switch = math.pi / 4.0 <= dyaw < math.pi / 2.0

        if switch:
            direction *= -1

        if direction != 1.0:
            speed_profile[i] = - target_speed
        else:
            speed_profile[i] = target_speed

        if switch:
            speed_profile[i] = 0.0

    speed_profile[-1] = 0.0

    d.append(d[-1])

    return speed_profile, d


def calc_speed_profile(cx, cy, cyaw, target_speed):

    speed_profile, d = set_stop_point(target_speed, cx, cy, cyaw)

    #  flg, ax = plt.subplots(1)
    #  plt.plot(speed_profile, "-r")
    #  plt.show()

    return speed_profile


def main():
    print("rear wheel feedback tracking start!!")
    ax = [0.0, 6.0, 12.5, 5.0, 7.5, 3.0, -1.0]
    ay = [0.0, 0.0, 5.0, 6.5, 3.0, 5.0, -2.0]
    goal = [ax[-1], ay[-1]]

    cx, cy, cyaw, ck, s = pycubicspline.calc_spline_course(ax, ay, ds=0.1)
    target_speed = 10.0 / 3.6

    sp = calc_speed_profile(cx, cy, cyaw, target_speed)

    t, x, y, yaw, v = closed_loop_prediction(cx, cy, cyaw, ck, sp, goal)

    flg, _ = plt.subplots(1)
    print(len(ax), len(ay))
    plt.plot(ax, ay, "xb", label="input")
    plt.plot(cx, cy, "-r", label="spline")
    plt.plot(x, y, "-g", label="tracking")
    plt.grid(True)
    plt.axis("equal")
    plt.xlabel("x[m]")
    plt.ylabel("y[m]")
    plt.legend()

    flg, ax = plt.subplots(1)
    plt.plot(s, [math.degrees(iyaw) for iyaw in cyaw], "-r", label="yaw")
    plt.grid(True)
    plt.legend()
    plt.xlabel("line length[m]")
    plt.ylabel("yaw angle[deg]")

    flg, ax = plt.subplots(1)
    plt.plot(s, ck, "-r", label="curvature")
    plt.grid(True)
    plt.legend()
    plt.xlabel("line length[m]")
    plt.ylabel("curvature [1/m]")

    plt.show()


if __name__ == '__main__':
    main()