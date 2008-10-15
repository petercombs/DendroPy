#! /usr/bin/env python

############################################################################
##  splits.py
##
##  Part of the DendroPy library for phylogenetic computing.
##
##  Copyright 2008 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Split calculation and management.
"""

from dendropy import taxa
from dendropy import trees
from dendropy import treegen

def is_non_singleton_split(split):
    """
    Returns True if a split is NOT between a leaf and the rest of the taxa.
    """
    # ((split-1) & split) is True (non-zero) only
    # if split is not a power of 2, i.e., if split
    # has more than one bit turned on, i.e., if it
    # is a non-trivial split.    
    return ((split-1) & split)

def number_to_bitstring(num):
    """
    Returns a representation of a number as a bit string.
    """
    return num>0 and number_to_bitstring(num>>1)+str(num&1) or ''
    
def split_as_string(split_mask, taxa_block, symbol1='.', symbol2='*'):
    """
    Returns a 'pretty' split representation.
    """
    s = number_to_bitstring(split_mask).rjust(len(taxa_block), '0')
    return s.replace('0', symbol1).replace('1', symbol2)
    
def split_as_string_rev(split_mask, taxa_block, symbol1='.', symbol2='*'):
    """
    Returns a 'pretty' split representation, reversed, with first taxon
    on the left (as given by PAUP*)
    """
    return split_as_string(split_mask=split_mask, 
                           taxa_block=taxa_block, 
                           symbol1=symbol1,
                           symbol2=symbol2)[::-1]
    
def split_taxa_list(split_mask, taxa_block, index=0):
    """
    Returns list of taxa represented by split.
    """
    taxa = []
    while split_mask:
        if split_mask & 1:
            taxa.append(taxa_block[index])
        split_mask = split_mask >> 1
        index += 1
    return taxa

def encode_splits(tree, 
                  taxa_block=None, 
                  edge_split_mask='split_mask', 
                  tree_split_edges_map="split_edges",
                  tree_split_taxa_map="split_taxa",
                  tree_splits_list="splits",
                  tree_complemented_splits='complemented_splits',
                  tree_complemented_split_edges_map="complemented_split_edges"):
    """
    Processes splits on a tree, encoding them as bitmask on each edge. 
    Returns a dictionary where the keys are splits and the values are edges.
    If `tree_split_edges_map` is given, then the dictionary is embedded as an attribute
    of the tree.
    If `tree_split_taxa_map` is given, then an additional tree attribute is set---
    a dictionary of splits to list of taxa represented by the split.
    If `tree_splits_list` is given, a set of all splits is added to the tree as an attribute
    If `tree_complemented_split_edges_maps` is  gvien, a dictionary of all complements of the splits 
    is also added, with the complemented splits as keys and the corresponding edges as values
    """
    if taxa_block is None:
        taxa_block = tree.infer_taxa_block()
    split_map = {}
    for edge in tree.postorder_edge_iter():
        children = edge.head_node.children()
        if children:
            setattr(edge, edge_split_mask, 0)
            for child in children:
                setattr(edge, edge_split_mask, getattr(edge, edge_split_mask) | getattr(child.edge, edge_split_mask))
        else:
            if edge.head_node.taxon:
                setattr(edge, edge_split_mask, taxa_block.taxon_bitmask(edge.head_node.taxon))
            else:
                setattr(edge, edge_split_mask, 0)
        split_map[getattr(edge, edge_split_mask)] = edge
    if tree_split_edges_map:
        setattr(tree, tree_split_edges_map, split_map)
    if tree_split_taxa_map:
        split_taxa = {}
        for split in split_map:
            split_taxa[split] = split_taxa_list(split, taxa_block)
        setattr(tree, tree_split_taxa_map, split_taxa)
    if tree_splits_list:
        setattr(tree, tree_splits_list, set(split_map.keys()))
    if tree_complemented_splits or tree_complemented_split_edges_map:
        taxa_mask = taxa_block.all_taxa_bitmask()
        csplit_edges = {}
        for split in split_map.keys():
            csplit = split ^ taxa_mask
            csplit_edges[csplit] = split_map[split]
        if tree_complemented_splits:
            setattr(tree, tree_complemented_splits, set(csplit_edges.keys()))
        if tree_complemented_split_edges_map:            
            setattr(tree, tree_complemented_split_edges_map, csplit_edges)        
    return split_map
                
############################################################################        
## SplitDistribution

class SplitDistribution(object):
    """
    Collects information regarding splits over multiple trees.
    """
    
    def __init__(self, taxa_block=None):
        """
        What else?
        """
        self.total_trees_counted = 0
        if taxa_block is not None:
            self.taxa_block = taxa_block            
        else:
            self.taxa_block = taxa.TaxaBlock()
        self.splits = []
        self.complemented_splits = []
        self.split_counts = {}
        self.complemented_split_counts = {}
        self.split_edge_lengths = {}
        self.split_node_ages = {}
        self.ignore_edge_lengths = False
        self.ignore_node_ages = False
        self.__split_freqs = None
        self.__complemented_split_freqs = None
        self.__trees_counted_for_freqs = 0
        
    def splits_considered(self):
        """
        Returns 4 values:
            total number of splits counted
            total number of unique splits counted
            total number of non-trivial splits counted
            total number of unique non-trivial splits counted
        """
        num_splits = 0
        num_unique_splits = 0
        num_nt_splits = 0
        num_nt_unique_splits = 0
        for s in self.split_counts:
            num_unique_splits += 1 
            num_splits += self.split_counts[s]
            if is_non_singleton_split(s):
                num_nt_unique_splits += 1
                num_nt_splits += self.split_counts[s]
        return num_splits, num_unique_splits, num_nt_splits, num_nt_unique_splits                                                        
        
    def calc_freqs(self):
        """
        Forces recalculation of frequencies.
        """
        self.__split_freqs = {}
        self.__complemented_split_freqs = {}
        if self.total_trees_counted == 0:
            total = 1
        else:
            total = self.total_trees_counted
        for split in self.split_counts:
            self.__split_freqs[split] = float(self.split_counts[split]) / total
        for split in self.complemented_split_counts:
            self.__complemented_split_freqs[split] = float(self.complemented_split_counts[split]) / total
        self.__trees_counted_for_freqs = self.total_trees_counted            
        return self.__split_freqs, self.__complemented_split_freqs                
        
    def _get_split_frequencies(self):
        """
        Returns dictionary of splits : split frequencies.
        """
        if self.__split_freqs is None or self.__trees_counted_for_freqs != self.total_trees_counted:
            self.calc_freqs()
        return self.__split_freqs   
        
    split_frequencies = property(_get_split_frequencies)     
    
    def _get_complemented_split_frequencies(self):
        """
        Returns dictionary of complemented splits : split frequencies.
        """
        if self.__complemented_split_freqs is None or self.__trees_counted_for_freqs != self.total_trees_counted:
            self.calc_freqs()
        return self.__complemented_split_freqs   
        
    complemented_split_frequencies = property(_get_complemented_split_frequencies)      

    def count_splits_on_tree(self, tree):
        """
        Counts splits in this tree and add to totals.
        """
        self.total_trees_counted += 1
        tree.normalize_taxa(taxa_block=self.taxa_block)
        tree.deroot()
        encode_splits(tree, 
                     self.taxa_block, 
                     tree_split_taxa_map=None)        
        for split in tree.splits:
            if split not in self.split_counts:
                self.splits.append(split)
                self.split_counts[split] = 1
            else:
                self.split_counts[split] += 1     
            if not self.ignore_edge_lengths:                
                if split not in self.split_edge_lengths:
                    self.split_edge_lengths[split] = []    
                if tree.split_edges[split].length is not None: 
                    self.split_edge_lengths[split].append(tree.split_edges[split].length)
                else:
                    self.split_edge_lengths[split].append(0.0)
            if not self.ignore_node_ages:  
                if split not in self.split_node_ages:
                    self.split_node_ages[split] = []
                edge = tree.split_edges[split]
                if edge.head_node is not None:
                    self.split_node_ages[split].append(edge.head_node.distance_from_tip())
        for split in tree.complemented_splits:
            if split not in self.complemented_split_counts:
                self.complemented_splits.append(split)            
                self.complemented_split_counts[split] = 1
            else:
                self.complemented_split_counts[split] += 1    

                         