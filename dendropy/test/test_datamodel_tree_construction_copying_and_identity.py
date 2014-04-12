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
Tests basic Tree copying etc.
"""

import unittest
import dendropy
import copy
from dendropy.test.support import datagen_curated_test_tree
from dendropy.test.support import compare_and_validate

class TestTreeIdentity(unittest.TestCase):

    def setUp(self):
        self.t1 = dendropy.Tree()
        self.t2 = dendropy.Tree()

    def test_equal(self):
        self.assertNotEqual(self.t1, self.t2)

    def test_hash_dict_membership(self):
        k = {}
        k[self.t1] = 1
        k[self.t2] = 2
        self.assertEqual(len(k), 2)
        self.assertEqual(k[self.t1], 1)
        self.assertEqual(k[self.t2], 2)
        self.assertIn(self.t1, k)
        self.assertIn(self.t2, k)
        del k[self.t1]
        self.assertNotIn(self.t1, k)
        self.assertIn(self.t2, k)
        self.assertEqual(len(k), 1)
        k1 = {self.t1: 1}
        k2 = {self.t2: 1}
        self.assertIn(self.t1, k1)
        self.assertIn(self.t2, k2)
        self.assertNotIn(self.t2, k1)
        self.assertNotIn(self.t1, k2)

    def test_hash_set_membership(self):
        k = set()
        k.add(self.t1)
        k.add(self.t2)
        self.assertEqual(len(k), 2)
        self.assertIn(self.t1, k)
        self.assertIn(self.t2, k)
        k.discard(self.t1)
        self.assertNotIn(self.t1, k)
        self.assertIn(self.t2, k)
        self.assertEqual(len(k), 1)
        k1 = {self.t1: 1}
        k2 = {self.t2: 1}
        self.assertIn(self.t1, k1)
        self.assertIn(self.t2, k2)
        self.assertNotIn(self.t2, k1)
        self.assertNotIn(self.t1, k2)

class TestTreeCopying(
        datagen_curated_test_tree.CuratedTestTree,
        compare_and_validate.Comparator,
        unittest.TestCase):

    def add_annotations(self, tree):
        for idx, nd in enumerate(tree):
            if idx % 2 == 0:
                nd.edge.label = "E{}".format(idx)
                nd.edge.length = idx
            an1 = nd.annotations.add_new("a{}".format(idx),
                    "{}{}{}".format(nd.label, nd.taxon, idx))
            an2 = nd.annotations.add_bound_attribute("label")
            an3 = an1.annotations.add_bound_attribute("name")
            ae1 = nd.edge.annotations.add_new("a{}".format(idx),
                    "{}{}".format(nd.edge.label, idx))
            ae2 = nd.edge.annotations.add_bound_attribute("label")
            ae3 = ae1.annotations.add_bound_attribute("name")
        tree.annotations.add_new("a", 0)
        tree.label = "hello"
        b = tree.annotations.add_bound_attribute("label")
        b.annotations.add_new("c", 3)

    def test_copy(self):
        tree1, anodes1, lnodes1, inodes1 = self.get_tree(suppress_internal_node_taxa=False,
                suppress_external_node_taxa=False)
        self.add_annotations(tree1)
        for tree2 in (
                # tree1.clone(0),
                # copy.copy(tree1),
                # tree1.clone(1),
                # tree1.taxon_namespace_scoped_copy(),
                dendropy.Tree(tree1),
                ):
            self.compare_distinct_trees(tree1, tree2,
                    taxon_namespace_scoped=True,
                    compare_annotations=True)
            # Redundant, given the above
            # But for sanity's sake ...
            nodes1 = [nd for nd in tree1]
            nodes2 = [nd for nd in tree2]
            self.assertEqual(len(nodes1), len(nodes2))
            for nd1, nd2 in zip(nodes1, nodes2):
                self.assertIsNot(nd1, nd2)
                self.assertEqual(nd1.label, nd2.label)
                self.assertIs(nd1.taxon, nd2.taxon)

    def test_deepcopy(self):
        tree1, anodes1, lnodes1, inodes1 = self.get_tree(suppress_internal_node_taxa=False,
                suppress_external_node_taxa=False)
        self.add_annotations(tree1)
        for tree2 in (
                tree1.clone(2),
                copy.deepcopy(tree1),
                dendropy.Tree(tree1, taxon_namespace=dendropy.TaxonNamespace()),
                ):
            self.compare_distinct_trees(tree1, tree2,
                    taxon_namespace_scoped=False,
                    compare_annotations=True)
            # Redundant, given the above
            # But for sanity's sake ...
            nodes1 = [nd for nd in tree1]
            nodes2 = [nd for nd in tree2]
            self.assertEqual(len(nodes1), len(nodes2))
            for nd1, nd2 in zip(nodes1, nodes2):
                self.assertIsNot(nd1, nd2)
                self.assertEqual(nd1.label, nd2.label)
                self.assertIsNot(nd1.taxon, nd2.taxon)
                self.assertEqual(nd1.taxon.label, nd2.taxon.label)

class TestSpecialTreeConstruction(
        datagen_curated_test_tree.CuratedTestTree,
        compare_and_validate.Comparator,
        unittest.TestCase):

    def test_construction_from_another_tree_different_label(self):
        pass

    def test_construction_from_given_seed_node(self):
        pass

if __name__ == "__main__":
    unittest.main()