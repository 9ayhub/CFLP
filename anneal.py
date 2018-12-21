# coding:utf-8

from random import choice
import numpy as np
import time

# ---------------------------------------------------#
#  globals                                           #
#                                                    #
# ---------------------------------------------------#

# greedy ---------------------------

fac_num = 0
cus_num = 0
assign_cost = [[]]

total_cost = -1
facilities = []
customers = []
assign = [[]]

# anneal ---------------------------

t = 99.0

# tabu ---------------------------

history_min_cost = 0
tabu_list = []
tabu_facilities = facilities
tabu_customers = customers

# ---------------------------------------------------#
#  classes                                           #
#                                                    #
# ---------------------------------------------------#

class Customer:
    def __init__(self, id, demond, assign):
        self.id = id
        self.demond = demond
        self.assign = assign

class Facility:
    def __init__(self, id, capacity, open_cost, open):
        self.id = id
        self.capacity = capacity
        self.open_cost = open_cost
        self.open = open

class tabu_entry:
    def __init__(self, fac_from, fac_to, cus):
        self.fac_from = fac_from
        self.fac_to = fac_to
        self.cus = cus

# ---------------------------------------------------#
#  functions                                         #
#                                                    #
# ---------------------------------------------------#

# greedy ---------------------------

def readFile():
    global fac_num, cus_num, fac_capacity, fac_open_cost, cus_demond, assign_cost, assign
    f = open('Instances/p4')

    read_nums = f.readline().strip().split()
    fac_num = int(read_nums[0])
    cus_num = int(read_nums[1])

    for i in range(fac_num):
        read_cap_and_cost = f.readline().strip().split()
        facility = Facility(i, float(read_cap_and_cost[0]), float(read_cap_and_cost[1]), 0)
        facilities.append(facility)

    
    for i in range(cus_num / 10):
        read_cus_demond = f.readline().strip().split()
        for j in range(10):
            # cus_demond.append(int(read_cus_demond[j]))
            customer = Customer(i * 10 + j, float(read_cus_demond[j]), -1)
            customers.append(customer)

    assign_cost = [[0 for i in range(cus_num)] for i in range(fac_num)]
    for i in range(fac_num):
        assign_cost_temp = []
        for j in range(cus_num / 10):
            read_assign_cost = f.readline().strip().split()
            for k in range(10):
                assign_cost[i][j * 10 + k] = float(read_assign_cost[k])
    
    assign = [[0 for _ in range(cus_num)] for _ in range(fac_num)]

    f.close()

def greedy():
    global total_cost
    for i in range(len(assign[0])):
        min_cost = -1
        fac = -1
        cus = -1
        for j in range(len(assign)):
            if get_fac_cap(j) < customers[i].demond:
                continue

            temp_cost = assign_cost[j][i]
            # temp_cost = temp_cost + facilities[j].open_cost

            if min_cost == -1 or temp_cost < min_cost:
                fac = j
                cus = i
                min_cost = temp_cost

        if min_cost == -1:
            print "false!"
            return 
        else:
            facilities[fac].open = 1
            assign[fac][cus] = 1
            customers[cus].assign = fac

def get_fac_cap(j):
    cost = 0
    for i in range(cus_num):
        cost = cost + assign[j][i] * customers[i].demond
    return facilities[j].capacity - cost

def get_total_cost():
    cost = 0
    for i in range(cus_num):
        cost = cost + assign_cost[customers[i].assign][i]
    for i in range(fac_num):
        cost = cost + facilities[i].open_cost * facilities[i].open
    return cost

def print_result():
    print total_cost
    for i in range(fac_num):
        print facilities[i].open, 
    print ''
    for i in range(cus_num):
        print customers[i].assign, 

# anneal ---------------------------

def random_choice():
    customer = choice(customers)
    facility_from = facilities[customer.assign]
    while True:
        facility_to = choice(facilities)
        if customer.assign != facility_to.id and get_fac_cap(facility_to.id) >= customer.demond:
            break
    return customer, facility_from, facility_to

def cal_new_cost(fac_from, fac_to, cus):
    global total_cost
    new_cost = total_cost - assign_cost[fac_from.id][cus.id] + assign_cost[fac_to.id][cus.id]
    if get_fac_cap(fac_from.id) == fac_from.capacity - cus.demond:
        new_cost = new_cost - fac_from.open_cost
    if fac_to.open == 0:
        new_cost = new_cost + fac_to.open_cost
    return new_cost

def accept(facility_from, facility_to, customer):
    global total_cost
    if get_fac_cap(facility_from.id) == facility_from.capacity - customer.demond:
        facility_from.open = 0
    facility_to.open = 1
    assign[facility_from.id][customer.id] = 0
    assign[facility_to.id][customer.id] = 1
    customer.assign = facility_to.id

def anneal():
    global t, total_cost
    min_cost = total_cost
    while t > 1:
        for i in range(200):
            customer, facility_from, facility_to = random_choice()
            
            new_cost = cal_new_cost(facility_from, facility_to, customer)
            
            if new_cost < min_cost or np.random.rand() < np.exp(-(new_cost-min_cost)/t):
                accept(facility_from, facility_to, customer)
                if new_cost < total_cost:
                    min_cost = new_cost

        t = t * 0.9
    total_cost = min_cost
    
# tabu ---------------------------

def tabu():
    global total_cost, history_min_cost, tabu_customers, tabu_facilities
    history_min_cost = total_cost

    for n in range(400):
        now_min_cost = 0
        fac_from = facilities[0]
        fac_to = facilities[0]
        cus = customers[0]

        # 在当前最优解的基础上，在候选集中寻找cost更低，且不在禁忌表中的exchange
        now_min_cost, fac_from, fac_to, cus = find_best_change(now_min_cost, fac_from, fac_to, cus)
        update_tabu_list(fac_from, fac_to, cus)
        accept(fac_from, fac_to, cus)

        if now_min_cost < history_min_cost:
            history_min_cost = now_min_cost
            tabu_facilities = facilities
            tabu_customers = customers


def find_best_change(now_min_cost, fac_from, fac_to, cus):
    for i in range(10):# 候选集
        customer, facility_from, facility_to = random_choice()
        new_cost = cal_new_cost(facility_from, facility_to, customer)
        if new_cost < now_min_cost or i == 0:
            entry = tabu_entry(facility_from, facility_to, customer)
            if entry not in tabu_list or new_cost < history_min_cost:
                now_min_cost = new_cost
                fac_from = facility_from
                fac_to = facility_to
                cus = customer
    return now_min_cost, fac_from, fac_to, cus

def update_tabu_list(fac_from, fac_to, cus):
    entry = tabu_entry(fac_from, fac_to, cus)
    if entry in tabu_list:
        print "remove"
        tabu_list.remove(entry)

    tabu_list.append(entry)
    if len(tabu_list) > 300:
        tabu_list.pop(0)


def print_tabu():
    global history_min_cost
    print history_min_cost
    for i in range(len(tabu_facilities)):
        print tabu_facilities[i].open, 
    print ''
    for i in range(len(tabu_customers)):
        print tabu_customers[i].assign, 
    
# ---------------------------------------------------#
#  "api"                                             #
#                                                    #
# ---------------------------------------------------#

def run_greedy():
    global total_cost
    print "\n-----\ngreedy\n-----"
    readFile()
    greedy()
    cost = get_total_cost()
    print_result()

def run_anneal():
    global total_cost
    print "\n-----\nanneal\n-----"
    readFile()
    greedy()
    total_cost = get_total_cost()
    anneal()
    print_result()

def run_tabu():
    global total_cost
    readFile()
    greedy()
    total_cost = get_total_cost()
    print "-----\ngreedy\n-----"
    print_result()
    tabu()
    print "\n-----\ntabu\n-----"
    print_tabu()

# ---------------------------------------------------#
#  run                                               #
#                                                    #
# ---------------------------------------------------#

run_anneal()
# run_tabu()
