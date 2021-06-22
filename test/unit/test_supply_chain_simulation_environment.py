import pytest
import networkx as nx
import scse.controller.miniscot as miniSCOT
from scse.main.cli import MiniSCOTDebuggerApp

_HORIZON = 10

def _create_miniscot():
    return miniSCOT.SupplyChainEnvironment(time_horizon = _HORIZON,
                                           asin_selection = 1)


def test_importable():
    env = _create_miniscot()
    final_state = env.run()

    assert final_state['clock'] == _HORIZON


def test_fulfilled():
    env = _create_miniscot()
    final_state = env.run()

    G = final_state['network']

    # TODO remove the 'CUST1' hard-coding
    cust_node_data = G.nodes['Customer']
    total_delivered_to_customer = cust_node_data['delivered']

    assert total_delivered_to_customer > 0


def test_profiles():
    env = miniSCOT.SupplyChainEnvironment(time_horizon = _HORIZON,
                                          asin_selection = 1,
                                          profile = 'newsvendor_demo_profile')

    final_state = env.run()

    assert final_state['clock'] == _HORIZON


def test_cli_transcript():
    app = MiniSCOTDebuggerApp()
    app.do_start("-seed 12345 -horizon 1")
    #app._start(horizon = 10, seed = 12345, asin_list_size = 1)
    app.do_next("")
    app.do_run("")

    # We just need to reach the end...
    assert True
