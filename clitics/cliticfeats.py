"""Block CliticFeats extracts features for Czech clitic 'se'."""
from udapi.core.block import Block


# Dependency relations that introduce a subordinate (dependent) clause.
# xcomp is intentionally excluded: in Czech it marks the infinitive complement
# of modal/phase verbs (musí, začal, nechal, …) which together form a complex
# predicate, NOT a separate dependent clause.
_SUBORDINATING_DEPRELS = {"ccomp", "advcl", "acl", "csubj"}


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
        print("sent_id\tord\tpredicate_form\tclause_type")

    def process_node(self, node):
        if node.form.lower() != "se" or node.upos == "ADP":
            return
        predicate = node.parent
        predicate_form = self._predicate_form(predicate)
        clause_type = self._clause_type(predicate)
        sent_id = node.root.sent_id or ""
        print(f"{sent_id}\t{node.ord}\t{predicate_form}\t{clause_type}")
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
