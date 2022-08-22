# -*- coding: utf-8 -*-
"""
Created on Mon Aug 22 10:42:07 2022

@author: poud579
"""


import copy
import networkx as nx
import opendssdirect as dss
import pandas as pd
from itertools import product
import json


dss.run_command('Redirect ../IEEE123_DSS/Run_IEEE123Bus.dss')
dss.run_command('solve')
node_order = dss.Circuit.YNodeOrder()

# Find the graph and iterate through all switch combinations to find the corresponding loss and rank them
lines_df = dss.utils.lines_to_dataframe()
xfrmr_df = dss.utils.transformers_to_dataframe()
G_original = nx.Graph()
check = dss.utils.lines_to_dataframe()

switches = {}
# switches_feeder = ['sw1', 'sw2', 'sw3', 'sw4', 'sw5', 'sw6', 'sw7', 'sw8']
switches_feeder = ['sw1', 'sw2', 'sw3', 'sw4', 'sw5', 'sw6', 'sw7', 'sw8', 'sw9', 'sw10', 'sw11']
sw_idx = 0
for index, row in lines_df.iterrows():
    bus1 = row['Bus1'].partition('.')[0]
    bus2 = row['Bus2'].partition('.')[0]
    G_original.add_edge(bus1, bus2)
    name = row['Name'].strip()
    if row['Name'] in switches_feeder:
        switches[sw_idx] = {}
        switches[sw_idx]['name'] = name
        switches[sw_idx]['bus1'] = bus1
        switches[sw_idx]['bus2'] = bus2
        sw_idx += 1

for xfmr in dss.Transformers.AllNames():
    dss.Circuit.SetActiveElement('Transformer.' + xfmr)
    bus1 = dss.CktElement.BusNames()[0].partition('.')[0]
    bus2 = dss.CktElement.BusNames()[1].partition('.')[0]
    G_original.add_edge(bus1, bus2)

print("Number of Buses:", G_original.number_of_nodes(), "\n", "Number of Edges:", G_original.number_of_edges())

sw_combs = list(product(range(2), repeat=len(switches)))
switch_combinations = {}
sw_comb_idx = 0
for sw_comb in sw_combs:
    flag = 0
    G = copy.deepcopy(G_original)
    # Open the switches in the combination that are "0"
    for idx, val in enumerate(sw_comb):
        if val == 0:
            G.remove_edge(switches[idx]['bus1'], switches[idx]['bus2'])

    # If G is disconnected and has a cycle, let's not include that for ranking;
    # Checking for purely radial network
    try:
        list_cycle = nx.find_cycle(G, source=None, orientation=None)
        flag = 1
    except:
        pass
    if nx.is_connected(G) and flag == 0:
        print(sw_comb)
        switch_combinations[sw_comb_idx] = sw_comb
        sw_comb_idx += 1

json_fp = open("switch_combinations.json", 'w')
json.dump(switch_combinations, json_fp, indent=2)
json_fp.close()


# For the time being, assume that the sensors are 3-phase
line_flow_sensors = ['l55', 'l114', 'l118']
voltage_sensors = ['57', '97', '76', '47']
csv_columns = ['t', 'load_profile']
for line in line_flow_sensors:
    csv_columns.append(line + '_A')
    csv_columns.append(line + '_B')
    csv_columns.append(line + '_C')
for bus in voltage_sensors:
    csv_columns.append(bus + '_A')
    csv_columns.append(bus + '_B')
    csv_columns.append(bus + '_C')

count = 0
load_mult = pd.read_csv('loadshape.csv')
for comb_idx, sw_comb in switch_combinations.items():
    print('Processing Topology: ', comb_idx, ': ', sw_comb)
    top_data_idx = []
    for t in range(len(load_mult)):
        topology_data = {'t': t, 'load_profile': load_mult.iloc[:, 0][t]}
        dss.run_command('Redirect ../IEEE123_DSS/Run_IEEE123Bus.dss')
        open_idxs = [idx for idx, val in enumerate(sw_comb) if val == 0]

        # Open the identified switches in OpenDSS
        for open_idx in open_idxs:
            dss.run_command('open Line.' + switches[open_idx]['name'])
        dss.run_command('set loadmult = ' + str(load_mult.iloc[:, 0][t]))
        dss.run_command('solve')

        # Grab sensor measurements from the solved power flow
        for line in line_flow_sensors:
            element = 'Line.' + line
            dss.Circuit.SetActiveElement(element)
            topology_data[line + '_A'] = complex(dss.CktElement.Powers()[0], dss.CktElement.Powers()[1])
            topology_data[line + '_B'] = complex(dss.CktElement.Powers()[2], dss.CktElement.Powers()[3])
            topology_data[line + '_C'] = complex(dss.CktElement.Powers()[4], dss.CktElement.Powers()[5])

        Vol = dss.Circuit.AllBusVMag()
        for bus in voltage_sensors:
            topology_data[bus + '_A'] = Vol[node_order.index(bus + '.1')]
            topology_data[bus + '_B'] = Vol[node_order.index(bus + '.2')]
            topology_data[bus + '_C'] = Vol[node_order.index(bus + '.3')]

        top_data_idx.append(topology_data)

    # Dump the time-series results to csv for a given switch combination
    csv_file = '../outputs/topology_' + str(comb_idx) + '.csv'
    df = pd.DataFrame(top_data_idx, columns=csv_columns)
    df.to_csv(csv_file, sep=',', index=False)
