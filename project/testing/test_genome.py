
import os
import pytest
import sys
viz_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(viz_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
from neat.genome import NodeGene

@pytest.fixture
def node_gene():
    return NodeGene(
        node_id=1,
        node_type="HIDDEN",
        bias=0.5,
        activation_func="sigmoid",
    )

def test_node_gene_representation(node_gene):
    assert node_gene.__repr__() == f"NodeGene(id={node_gene.id}, type={node_gene.type}, " \
                f"bias={node_gene.bias:.3f}, act='{node_gene.activation_function_name}')"

def test_node_gene_dict(node_gene):
    expected_dict = {
        "id": node_gene.id,
        "type": node_gene.type,
        "bias": node_gene.bias,
        "activation_function_name": node_gene.activation_function_name,
    }
    assert node_gene.to_dict() == expected_dict
