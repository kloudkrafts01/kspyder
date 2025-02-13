#!python

from Engines.restExtractorEngine import ElementGraph

SAMPLE_GRAPH_NODES = [
    {
        'level': 0,
        'parent': None,
        'display_name': 'example.com',
        'name': '237459',
        'described': True,
        'children': 2
    },
    {
        'level': 1,
        'parent': '237459',
        'display_name': 'prd',
        'name': 'prod999990',
        'described': True,
        'children': 3
    },
    {
        'level': 2,
        'parent': 'prod999990',
        'display_name': 'ShopInDior-PRD',
        'name': 'SIDprd',
        'described': True,
        'children': 0
    }
]

SAMPLE_GRAPH = ElementGraph('sample_graph')
SAMPLE_GRAPH.depth = 2
SAMPLE_GRAPH.node_count = 3
SAMPLE_GRAPH.leaf_count = 1
SAMPLE_GRAPH.nodes = SAMPLE_GRAPH_NODES

SAMPLE_PILE = [
    {
        'level': 1,
        'parent': '237459',
        'disaply_name': 'non-prd',
        'name': 'nonprd909876'
    },
    {
        'level': 2,
        'parent': 'prod999990',
        'display_name': 'Bespoke-PRD',
        'name': 'BSPKprod'
    },
    {
        'level': 2,
        'parent': 'prod999990',
        'disaply_name': 'Dataiku-PRD',
        'name': 'DTKprod'
    }
]

SAMPLE_CHILDREN = [
    {
        'parent': 'DTKprod',
        'display_name': 'DataikuStudio-PRD',
        'name': 'DTKstudioPRD'
    },
    {
        'parent': 'nonprd909876',
        'display_name': 'Bespoke-NONPRD',
        'name': 'bspkNONPRD'
    },
    {
        'parent': 'nonprd909876',
        'display_name': 'Dataiku-NONPRD',
        'name': 'DTKnonPRD'
    }
]