import networkx as nx


def get_asin_inventory_in_network(G, asin):
    total_asin_inventory = 0
    for _, node_data in G.nodes(data=True):
        total_asin_inventory += node_data.get('inventory', {}).get(asin, 0)

    return total_asin_inventory


def get_asin_inventory_on_all_inbound_arcs(G, asin):
    amazon_fcs = set()
    for node, node_data in G.nodes(data=True):
        if node_data.get('node_type') not in ['customer', 'vendor']:
            amazon_fcs.add(node)

    total_arc_inventory = 0
    for origin, destination, edge_data in G.edges(data=True):
        if destination in amazon_fcs:
            for shipment in edge_data['shipments']:
                total_arc_inventory += shipment['quantity']

    return total_arc_inventory


def get_asin_inventory_on_inbound_arcs_to_node(G, asin, node):
    total_arc_inbound_to_node = 0
    for origin, destination, edge_data in G.edges(data=True):
        if destination == node:
            for shipment in edge_data['shipments']:
                total_arc_inbound_to_node += shipment['quantity']
    return total_arc_inbound_to_node


def get_asin_inventory_on_inbound_arcs_to_node_by_arrival_time(
        G, asin, node, max_arrival_time=3):
    total_arc_inbound_to_node = [0 for _ in range(max_arrival_time)]
    for origin, destination, edge_data in G.edges(data=True):
        if destination == node:
            for shipment in edge_data['shipments']:
                arrival_time = shipment['time_until_arrival']
                if arrival_time > 0:
                    total_arc_inbound_to_node[arrival_time -
                                              1] += shipment['quantity']

    return total_arc_inbound_to_node


def get_asin_inventory_in_node(node_data, asin):
    return node_data.get('inventory', {}).get(asin, 0)


def set_asin_inventory_in_node(node_data, asin, quantity):
    node_data.get('inventory', {})[asin] = quantity
