"""Offline tests for finding the model Google served a reply with (scan_served / pick_served)."""

from gemini_webapi.types import AvailableModel, ModelOutput, ServedModel, pick_served, scan_served


def _model(model_id: str, display: str, name: str | None = None) -> AvailableModel:
    return AvailableModel(model_id=model_id, model_name=name or display.lower(), display_name=display, description="", capacity=1)


REGISTRY = {
    m.model_id: m
    for m in (
        _model("fbb127bbb056c959", "4 Hydrogen", "gemini-4-hydrogen"),
        _model("5bf011840784117a", "Hydrogen Thinking", "gemini-hydrogen-thinking"),
        _model("9d8ca3786ebdfbea", "Pro", "gemini-pro"),
        _model("cf41b0e0dd7d53e5", "Auto", "gemini-auto"),
    )
}


def _run(chunks: list[str]) -> ServedModel | None:
    state: dict = {}
    for c in chunks:
        scan_served(state, c, REGISTRY)
    return pick_served(state, REGISTRY)


def test_served_by_id_quoted_and_escaped():
    got = _run(['xx"fbb127bbb056c959",null,null,"4 Hydrogen"yy'])
    assert got == ServedModel(model_id="fbb127bbb056c959", display_name="4 Hydrogen", via="id")
    got = _run(['[\\"cf41b0e0dd7d53e5\\",null,null,\\"Auto\\"]'])
    assert got is not None and got.model_id == "cf41b0e0dd7d53e5" and got.via == "id"


def test_id_split_across_chunks_still_matches():
    got = _run(['junk "9d8ca37', '86ebdfbea" more'])
    assert got is not None and got.model_id == "9d8ca3786ebdfbea"


def test_two_distinct_ids_is_ambiguous():
    assert _run(['"fbb127bbb056c959" and "9d8ca3786ebdfbea"']) is None


def test_name_only_used_when_no_id_matched():
    got = _run(['label "Hydrogen Thinking" alone'])
    assert got == ServedModel(model_id="5bf011840784117a", display_name="Hydrogen Thinking", via="name")


def test_id_wins_over_a_name_mention():
    got = _run(['"Hydrogen Thinking" ... "fbb127bbb056c959"'])
    assert got is not None and got.model_id == "fbb127bbb056c959" and got.via == "id"


def test_two_names_without_id_is_ambiguous():
    assert _run(['"Pro" and "Hydrogen Thinking"']) is None


def test_nothing_matched_is_none():
    assert _run(["plain reply with no model names"]) is None


def test_unknown_id_is_ignored():
    assert _run(['"0000000000000000"']) is None


def test_model_output_carries_served_field():
    out = ModelOutput(metadata=["c", "r"], candidates=[])
    assert out.served is None
    out.served = ServedModel(model_id="x", display_name="X", via="id")
    assert out.served.via == "id"


def test_served_name_is_the_status_name_not_the_tagline():
    # A real RPC model: display_name is the tagline, status_name the name field.
    real = AvailableModel(
        model_id="fbb127bbb056c959", model_name="gemini-4-hydrogen", display_name="Everyday help",
        description="", capacity=1, status_name="4 Hydrogen",
    )
    registry = {real.model_id: real}
    state: dict = {}
    scan_served(state, 'x "fbb127bbb056c959" y', registry)
    got = pick_served(state, registry)
    assert got is not None and got.display_name == "4 Hydrogen" and got.via == "id"
    # The tagline appearing in ordinary text must not be taken as a served-name match.
    state2: dict = {}
    scan_served(state2, "This is Everyday help for you", registry)
    assert pick_served(state2, registry) is None
