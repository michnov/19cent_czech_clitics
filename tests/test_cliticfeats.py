import sys
import types
import unittest


if "udapi" not in sys.modules:
    udapi = types.ModuleType("udapi")
    core = types.ModuleType("udapi.core")
    block_mod = types.ModuleType("udapi.core.block")

    class Block:  # pragma: no cover
        pass

    block_mod.Block = Block
    core.block = block_mod
    udapi.core = core
    sys.modules["udapi"] = udapi
    sys.modules["udapi.core"] = core
    sys.modules["udapi.core.block"] = block_mod

from clitics.cliticfeats import CliticFeats


class FakeNode:
    def __init__(
        self, form, ord_, upos="X", deprel="", lemma=None, feats="_", is_root=False
    ):
        self.form = form
        self.lemma = lemma if lemma is not None else form.lower()
        self.ord = ord_
        self.upos = upos
        self.deprel = deprel
        self.feats = feats
        self.parent = None
        self.children = []
        self._is_root = is_root

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def is_root(self):
        return self._is_root

    def __hash__(self):
        return id(self)


class CliticFeatsTests(unittest.TestCase):
    def test_clause_position_uses_full_clitic_group(self):
        root = FakeNode("<root>", 0, is_root=True)
        pred = root.add_child(
            FakeNode("četl", 1, upos="VERB", deprel="root", lemma="číst")
        )
        pred.add_child(
            FakeNode(
                "ho",
                2,
                upos="PRON",
                deprel="obj",
                lemma="on",
                feats="Case=Acc|Variant=Short",
            )
        )
        se = pred.add_child(
            FakeNode(
                "se",
                3,
                upos="PRON",
                deprel="expl:pv",
                lemma="se",
                feats="PronType=Prs|Reflex=Yes|Variant=Short",
            )
        )

        group = CliticFeats._clitic_group(se, pred)
        self.assertEqual([n.form for n in group], ["ho", "se"])
        self.assertEqual(CliticFeats._clause_position(pred, group), "postiniciální")

    def test_relation_to_regent_uses_full_clitic_group(self):
        root = FakeNode("<root>", 0, is_root=True)
        pred = root.add_child(
            FakeNode("četl", 4, upos="VERB", deprel="root", lemma="číst")
        )
        pred.add_child(FakeNode("on", 1, upos="PRON", deprel="nsubj", lemma="on"))
        se = pred.add_child(
            FakeNode(
                "si",
                2,
                upos="PRON",
                deprel="expl:pv",
                lemma="se",
                feats="Case=Dat|PronType=Prs|Reflex=Yes|Variant=Short",
            )
        )
        pred.add_child(
            FakeNode(
                "jsem",
                3,
                upos="AUX",
                deprel="aux",
                lemma="být",
                feats="Mood=Ind|Person=1|Tense=Pres|VerbForm=Fin",
            )
        )

        group = CliticFeats._clitic_group(se, pred)
        self.assertEqual([n.form for n in group], ["si", "jsem"])
        self.assertEqual(CliticFeats._relation_to_regent(pred, group), "kontaktní preverbální")

    def test_group_accepts_inflected_pronoun_clitic(self):
        root = FakeNode("<root>", 0, is_root=True)
        pred = root.add_child(
            FakeNode("četl", 3, upos="VERB", deprel="root", lemma="číst")
        )
        pred.add_child(
            FakeNode(
                "mi",
                1,
                upos="PRON",
                deprel="iobj",
                lemma="já",
                feats="Case=Dat|Variant=Short",
            )
        )
        se = pred.add_child(
            FakeNode(
                "se",
                2,
                upos="PRON",
                deprel="expl:pv",
                lemma="se",
                feats="Case=Acc|PronType=Prs|Reflex=Yes|Variant=Short",
            )
        )

        group = CliticFeats._clitic_group(se, pred)
        self.assertEqual([n.form for n in group], ["mi", "se"])


if __name__ == "__main__":
    unittest.main()
