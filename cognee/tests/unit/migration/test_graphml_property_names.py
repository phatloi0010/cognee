"""GraphML property names must survive XML attribute quoting."""

import xml.etree.ElementTree as ET

import networkx as nx
import pytest

from cognee.modules.migration.formats import write_graphml

_NS = "{http://graphml.graphdrawing.org/xmlns}"
_KEYS = ['display"name', "both'\"quotes", "a&b", "a<b", "ordinary_name"]


@pytest.mark.parametrize("key", _KEYS)
@pytest.mark.parametrize("scope", ["node", "edge"])
def test_graphml_property_names_roundtrip(key, scope, tmp_path):
    nodes = [("n1", {key: "Alice"} if scope == "node" else {}), ("n2", {})]
    # Supplying relationship_name avoids the separate, already-reported missing-key bug.
    edges = [("n1", "n2", "knows", {"relationship_name": "knows", key: "Alice"})]
    destination = tmp_path / "graph.graphml"
    write_graphml(nodes, edges if scope == "edge" else [], destination)

    root = ET.parse(destination).getroot()
    declaration = next(
        element
        for element in root.findall(f"{_NS}key")
        if element.get("for") == scope and element.get("attr.name") == key
    )
    data = root.find(f"{_NS}graph/{_NS}{scope}/{_NS}data")
    if scope == "edge":
        data = next(
            item
            for item in root.findall(f"{_NS}graph/{_NS}edge/{_NS}data")
            if item.get("key") == declaration.get("id")
        )
    assert data.get("key") == declaration.get("id")
    assert data.text == "Alice"


def test_networkx_reads_node_with_quoted_property_name(tmp_path):
    destination = tmp_path / "graph.graphml"
    write_graphml([("n1", {'display"name': "Alice"})], [], destination)
    graph = nx.read_graphml(destination)
    assert graph.nodes["n1"]['display"name'] == "Alice"
