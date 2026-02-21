"""Block CliticFeats extracts features for Czech clitic 'se'."""
from udapi.core.block import Block


# Dependency relations that introduce a subordinate (dependent) clause.
# xcomp is intentionally excluded: in Czech it marks the infinitive complement
# of modal/phase verbs (musí, začal, nechal, …) which together form a complex
# predicate, NOT a separate dependent clause.
_SUBORDINATING_DEPRELS = {"ccomp", "advcl", "acl", "csubj"}
_CLITIC_GROUP_FORMS = {"se", "mu", "ho", "bych", "jsem"}


class CliticFeats(Block):
    """Extract features for the Czech clitic *se* (not a preposition).

    For every token whose lowercased form is *se* and whose UPOS tag is not
    ``ADP`` (i.e. it is not a preposition) the block prints one TSV line with
    the following columns:

    * ``sent_id``       – identifier of the sentence
    * ``ord``           – 1-based position of the *se* token in the sentence
    * ``predicate_form`` – space-joined forms of the governing predicate and
                           all its auxiliary/copular dependents, in sentence
                           order (represents the full complex predicate).
                           When the governing verb is itself an ``xcomp``
                           complement (e.g. modal/phase verb construction),
                           the chain of ``xcomp`` heads and their own
                           auxiliaries is also included.
    * ``clause_type``   – ``HV`` if the predicate is part of the main clause,
                           ``VV`` if it is part of a dependent/subordinate
                           clause

    A header line is printed at the beginning of the output.
    """

    def process_start(self):
        print(
            "sent_id\tord\tpredicate_form\tclause_type\tclause_position\trelation_to_regent"
        )

    def process_node(self, node):
        if node.form.lower() != "se" or node.upos == "ADP":
            return
        predicate = node.parent
        predicate_form = self._predicate_form(predicate)
        clause_type = self._clause_type(predicate)
        clitic_group = self._clitic_group(node, predicate)
        clause_position = self._clause_position(predicate, clitic_group)
        relation_to_regent = self._relation_to_regent(predicate, clitic_group)
        sent_id = node.root.sent_id or ""
        print(
            f"{sent_id}\t{node.ord}\t{predicate_form}\t{clause_type}\t"
            f"{clause_position}\t{relation_to_regent}"
        )
        print(node.root.get_sentence())

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _predicate_form(predicate):
        """Return space-joined forms of the complex predicate in sentence order.

        The complex predicate consists of:
        * the governing verb (``predicate``) and all its ``aux``/``cop``
          dependents, and
        * the chain of ``xcomp`` heads above it (modal/phase verbs like
          *musí*, *začal*, *nechal*) together with *their* ``aux``/``cop``
          dependents.
        """
        if predicate is None or predicate.is_root():
            return "_"
        parts = [predicate]
        for child in predicate.children:
            base_deprel = child.deprel.split(":")[0] if child.deprel else ""
            if base_deprel in ("aux", "cop"):
                parts.append(child)

        # Climb through xcomp chain: each xcomp head is part of the complex
        # predicate (e.g. "musí se opírat" → forms: musí opírat).
        visited = {predicate}
        node = predicate
        while True:
            base_deprel = node.deprel.split(":")[0] if node.deprel else ""
            if base_deprel != "xcomp" or node.parent is None or node.parent.is_root():
                break
            head = node.parent
            if head in visited:
                break
            visited.add(head)
            parts.append(head)
            for child in head.children:
                base_ch = child.deprel.split(":")[0] if child.deprel else ""
                if base_ch in ("aux", "cop"):
                    parts.append(child)
            node = head

        parts.sort(key=lambda n: n.ord)
        return " ".join(part.form for part in parts)

    @staticmethod
    def _clause_type(predicate):
        """Return ``HV`` (main clause) or ``VV`` (dependent clause).

        Starting at *predicate*, the method walks up the dependency tree.
        The first node whose base dependency relation is either ``root``
        (→ main clause, ``HV``) or a member of ``_SUBORDINATING_DEPRELS``
        (→ dependent clause, ``VV``) determines the result.

        ``xcomp`` relations are transparent: the method passes through them
        because in Czech they connect the infinitive complement to its
        modal/phase verb head within the same predicate cluster, not across
        clause boundaries.
        """
        if predicate is None or predicate.is_root():
            return "_"
        visited = set()
        node = predicate
        while True:
            if node in visited:
                return "HV"  # cycle guard – treat as main clause
            visited.add(node)
            base_deprel = node.deprel.split(":")[0] if node.deprel else ""
            if base_deprel == "root":
                return "HV"
            if base_deprel in _SUBORDINATING_DEPRELS:
                return "VV"
            if node.parent is None or node.parent.is_root():
                return "HV"
            node = node.parent

    @staticmethod
    def _clitic_group(node, predicate):
        """Return contiguous clitic-group nodes containing *node* (incl. se)."""
        if node is None:
            return []
        clause_nodes = CliticFeats._clause_nodes(predicate)
        if not clause_nodes:
            return [node]
        non_punct = [n for n in clause_nodes if getattr(n, "upos", "") != "PUNCT"]
        try:
            idx = non_punct.index(node)
        except ValueError:
            return [node]

        start = idx
        while start > 0 and CliticFeats._is_group_clitic(non_punct[start - 1]):
            start -= 1
        end = idx
        while end + 1 < len(non_punct) and CliticFeats._is_group_clitic(non_punct[end + 1]):
            end += 1
        return non_punct[start:end + 1]

    @staticmethod
    def _clause_position(predicate, clitic_group):
        """Return position of the whole clitic group in clause."""
        clause_nodes = CliticFeats._clause_nodes(predicate)
        units, group_idx = CliticFeats._clause_units(clause_nodes, clitic_group)
        if group_idx is None:
            return "_"
        if group_idx == 0:
            return "iniciální"
        if group_idx == 1:
            return "postiniciální"
        if group_idx == len(units) - 1 and group_idx > 0 and units[group_idx - 1] == predicate:
            return "finální"
        if group_idx == len(units) - 2 and group_idx + 1 < len(units) and units[group_idx + 1] == predicate:
            return "prefinální"
        return "mediální"

    @staticmethod
    def _relation_to_regent(predicate, clitic_group):
        """Return relation of the whole clitic group to governing predicate."""
        clause_nodes = CliticFeats._clause_nodes(predicate)
        units, group_idx = CliticFeats._clause_units(clause_nodes, clitic_group)
        if group_idx is None or predicate is None or predicate not in units:
            return "_"
        pred_idx = units.index(predicate)
        if group_idx + 1 == pred_idx:
            return "kontaktní preverbální"
        if group_idx == pred_idx + 1:
            return "kontaktní postverbální"

        complex_predicate = set(CliticFeats._predicate_nodes(predicate))
        left = units[group_idx - 1] if group_idx > 0 else None
        right = units[group_idx + 1] if group_idx + 1 < len(units) else None
        if left in complex_predicate and right in complex_predicate:
            return "kontaktní interverbální"
        if group_idx < pred_idx:
            return "izolovaná"
        return "jiné"

    @staticmethod
    def _is_group_clitic(node):
        if node is None:
            return False
        form = (node.form or "").lower()
        if form not in _CLITIC_GROUP_FORMS:
            return False
        if form == "se" and getattr(node, "upos", "") == "ADP":
            return False
        return True

    @staticmethod
    def _predicate_nodes(predicate):
        if predicate is None or predicate.is_root():
            return []
        parts = [predicate]
        for child in predicate.children:
            base_deprel = child.deprel.split(":")[0] if child.deprel else ""
            if base_deprel in ("aux", "cop"):
                parts.append(child)
        visited = {predicate}
        node = predicate
        while True:
            base_deprel = node.deprel.split(":")[0] if node.deprel else ""
            if base_deprel != "xcomp" or node.parent is None or node.parent.is_root():
                break
            head = node.parent
            if head in visited:
                break
            visited.add(head)
            parts.append(head)
            for child in head.children:
                base_ch = child.deprel.split(":")[0] if child.deprel else ""
                if base_ch in ("aux", "cop"):
                    parts.append(child)
            node = head
        return sorted(parts, key=lambda n: n.ord)

    @staticmethod
    def _clause_nodes(predicate):
        clause_root = CliticFeats._clause_root(predicate)
        if clause_root is None or clause_root.is_root():
            return []
        return sorted(CliticFeats._collect_subtree_nodes(clause_root), key=lambda n: n.ord)

    @staticmethod
    def _clause_root(predicate):
        if predicate is None or predicate.is_root():
            return None
        node = predicate
        visited = set()
        while node is not None and not node.is_root():
            if node in visited:
                break
            visited.add(node)
            base_deprel = node.deprel.split(":")[0] if node.deprel else ""
            if base_deprel != "xcomp" or node.parent is None or node.parent.is_root():
                return node
            node = node.parent
        return predicate

    @staticmethod
    def _collect_subtree_nodes(root):
        nodes = []
        stack = [root]
        seen = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            nodes.append(node)
            stack.extend(reversed(list(node.children)))
        return nodes

    @staticmethod
    def _clause_units(clause_nodes, clitic_group):
        non_punct = [n for n in clause_nodes if getattr(n, "upos", "") != "PUNCT"]
        group_set = set(clitic_group or [])
        units = []
        group_idx = None
        i = 0
        while i < len(non_punct):
            node = non_punct[i]
            if node in group_set:
                if group_idx is None:
                    group_idx = len(units)
                    units.append("__CLITIC_GROUP__")
                i += 1
                while i < len(non_punct) and non_punct[i] in group_set:
                    i += 1
                continue
            units.append(node)
            i += 1
        return units, group_idx
