#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: Ist wurst...

import re
import sys
import json
from graphviz import Digraph


def digraph_creator(data):

    unit_separator_file = 'C:\\temp\\osmc-rol\\L2\\library\\Cisco\\unit_separator.txt'
    with open(unit_separator_file, 'r') as file:
        unit_separator = file.read()

    unit_header_file = 'C:\\temp\\osmc-rol\\L2\\library\\Cisco\\ws-c2960x_unit_header.txt'
    with open(unit_header_file, 'r') as file:
        unit_header = file.read()

    unit_48_file = 'C:\\temp\\osmc-rol\\L2\\library\\Cisco\\ws-c2960x_unit_48.txt'
    with open(unit_48_file, 'r') as file:
        unit_48 = file.read()

    unit_24_file = 'C:\\temp\\osmc-rol\\L2\\library\\Cisco\\ws-c2960x_unit_24.txt'
    with open(unit_24_file, 'r') as file:
        unit_24 = file.read()

    intersw_conns = 2

    g = Digraph(
        name='L2_topology',
        filename='l2_topology.gv',
        graph_attr={'rankdir': 'LR', 'splines': 'line', 'overlap': 'false', 'imagepath': 'C:/Users/akdaniel/Downloads/nw_topo/', 'label': 'Layer 2 Topology - Beta'}
    )
    g.format = 'svg'
    g.attr('node', shape='plaintext')
    g.attr('edge', arrowhead='none', arrowtail='none', penwidth='3', minlen='3')

    # create nodes for stacked switches
    c_elements = 0
    for group in data['groups']:
        c_elements += len(data['groups'][group])
        for element in data['groups'][group]:
            switch_node = ''
            table = '<table border="1" cellborder="0" bgcolor="#15495d" color="grey">'
            platform = element['platform']
            hostname = element['hostname']
            for i in range(1, element['units']+1):
                platform_new = platform + ' - U' + str(i)
                unit_header_new = re.sub('PLATFORM_V',platform_new, unit_header)
                unit_header_new = re.sub('HOSTNAME_V', hostname, unit_header_new)
                switch_node += unit_header_new
                if "24" in element['platform']:
                    switch_node += re.sub('TYP_V_UID_V', 'XX' + str(i), unit_24)
                if "48" in element['platform']:
                    switch_node += re.sub('TYP_V_UID_V', 'XX' + str(i), unit_48)
                if i == element['units']:
                    unit_separator_new = ""
                else:
                    unit_separator_new = unit_separator

                switch_node += unit_separator_new

            table += switch_node
            table += '</table>'
            label = '<\n' + table + '\n>'
            g.node(hostname, penwidth='0', fontname='Arial', label=label)

    # create dummy right and dummy top nodes for groups
    dummy_horizontals = []
    s = {}
    for group in data['groups']:
        dummy_verticals = []
        nametop = "dummy" + group + "top"
        g.node(nametop, style='invis')

        nameright = "dummy" + group + "right"
        table = '<table border="1" cellborder="0" bgcolor="#15495d" color="grey">\n'
        max_conns = c_elements * intersw_conns
        for i in range(max_conns):
            table += '<tr><td port="' + str(i) + '"></td></tr>\n'
        table += '</table>'
        label = '<' + table + '>'
        g.node(nameright, label=label, style='invis')

        dummy_horizontals.append(nametop)
        dummy_horizontals.append(nameright)
        dummy_verticals.append(nameright)
        for element in data['groups'][group]:
            hostname = element['hostname']
            dummy_r_hname = nameright + hostname

            table = '<table border="1" cellborder="0" bgcolor="#15495d" color="grey">\n'
            max_conns = c_elements * intersw_conns
            for i in range(max_conns):
                table += '<tr><td port="' + str(i) + '"></td></tr>\n'
            table += '</table>'
            label = '<' + table + '>'
            g.node(dummy_r_hname, label=label, style='invis')

            dummy_verticals.append(dummy_r_hname)
            g.edge(hostname, dummy_r_hname, style="invis")

        for i in range(len(dummy_verticals) - 1):
            pair = dummy_verticals[i:i + 2]
            g.edge(pair[0], pair[1], style="invis", constraint='false')
        with g.subgraph() as s[group]:
            s[group].attr(rank='same')
            for element in dummy_verticals:
                s[group].node(element)

    # create edges with sliding window for dummy nodes
    for i in range(len(dummy_horizontals)-1):
        pair = dummy_horizontals[i:i+2]
        g.edge(pair[0], pair[1], style="invis")

    # edge from top to all group member nodes downstairs
    for group in data['groups']:
        h_list = []
        name_top = "dummy" + group + "top"
        hostname = data['groups'][group][0]['hostname']
        g.edge(name_top, hostname, style="invis")
        for element in data['groups'][group]:
            hostname = element['hostname']
            h_list.append(hostname)
            if len(h_list) > 1:
                cur_pos = len(h_list) - 1
                prev_pos = len(h_list) - 2
                g.edge(h_list[prev_pos], h_list[cur_pos], style="invis")

    # subgraph for ranksame with dummy group top node and with all member nodes in group
    s = {}
    for group in data['groups']:
        name_top = "dummy" + group + "top"
        with g.subgraph() as s[group]:
            s[group].attr(rank='same')
            s[group].node(name_top)
            for element in data['groups'][group]:
                hostname = element['hostname']
                s[group].node(hostname)

    # edges between interfaces and ports for dummy nodes
    colors = ["#0080ff", "#80ff00", "#00FF00", "#00FF80", "#00FFFF"]
    color_dict = {}
    i = 0
    id = 0
    if 'edges' in data:
        for edge in data['edges']:
            from_hostname = edge['from'].split(':')[0]
            to_hostname = edge['to'].split(':')[0]
            key = from_hostname + to_hostname
            if key in color_dict:
                hex_color = color_dict[key]
            else:
                hex_color = colors[i]
                if i+1 < len(colors):
                    i += 1
                else:
                    i = 0
                color_dict[key] = hex_color
            label = edge['from'] + " - " + edge['to']
            for group in data['groups']:
                for element in data['groups'][group]:
                    if from_hostname == element['hostname']:
                        from_nameright = "dummy" + group + "right"
                        from_group = group
                        from_d_nameright  = from_nameright + from_hostname
                    if to_hostname == element['hostname']:
                        to_nameright = "dummy" + group + "right"
                        to_group = group
                        to_d_nameright = to_nameright + to_hostname

            from_nameright_port = from_nameright + ":" + str(id)
            from_d_nameright_port = from_d_nameright + ":" + str(id)
            to_nameright_port = to_nameright + ":" + str(id)
            to_d_nameright_port = to_d_nameright + ":" + str(id)

            if from_group != to_group:
                g.edge(edge['from'], from_nameright_port, dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
                g.edge(from_nameright_port, to_nameright_port, dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
                g.edge(to_nameright_port, to_d_nameright_port, dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
                g.edge(to_d_nameright_port, edge['to'], dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
            else:
                g.edge(edge['from'], from_d_nameright_port, dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
                g.edge(from_d_nameright_port, to_d_nameright_port, dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
                g.edge(to_d_nameright_port, edge['to'], dir='both', color=hex_color, constraint='false', headclip='false', tailclip='false', tooltip=label)
            id += 1

    g.view()
    g.render()
    print(g.source)


def main(argv):

    input_filename = 'C:\\temp\\osmc-rol\\L2\\L2_topo_input_sw_24p.json'
    input_json = open(input_filename)
    input_data = json.load(input_json)

    digraph_creator(input_data)

if __name__ == "__main__":
    main(sys.argv[1:])
