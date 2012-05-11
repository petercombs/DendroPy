#! /usr/bin/env python

##############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2010 Jeet Sukumaran and Mark T. Holder.
##  All rights reserved.
##
##  See "LICENSE.txt" for terms and conditions of usage.
##
##  If you use this work or any portion thereof in published work,
##  please cite it as:
##
##     Sukumaran, J. and M. T. Holder. 2010. DendroPy: a Python library
##     for phylogenetic computing. Bioinformatics 26: 1569-1571.
##
##############################################################################

"""
Tests of split counting on trees with incomplete leaf sets.
"""

import unittest

import dendropy
from dendropy.test.support import pathmap
from dendropy.utility import messaging
_LOG = messaging.get_logger(__name__)

class IncompleteLeafSetSplitTest(unittest.TestCase):

    def testUnrooted(self):
        src_prefix = "incomplete_leaves_unrooted"
        input_ds = dendropy.DataSet.get_from_path(
                src=pathmap.tree_source_path(src_prefix + ".dendropy-pruned.nex"),
                schema='nexus',
                attached_taxon_set=True)
        input_taxa = input_ds.taxon_sets[0]
        output_ds = dendropy.DataSet.get_from_path(
                src=pathmap.tree_source_path(src_prefix + ".paup-pruned.nex"),
                schema='nexus',
                attached_taxon_set=True,
                taxon_set=input_taxa)
        for set_idx, src_trees in enumerate(input_ds.tree_lists):
            src_trees = input_ds.tree_lists[set_idx]
            ref_trees = output_ds.tree_lists[set_idx]
            for tree_idx, src_tree in enumerate(src_trees):
                _LOG.debug("Set %d/%d, Tree %d/%d" % (set_idx+1, len(input_ds.tree_lists), tree_idx+1, len(src_trees)))
                ref_tree = ref_trees[tree_idx]
                self.assertEqual(src_tree.symmetric_difference(ref_tree), 0)

if __name__ == "__main__":
    unittest.main()

