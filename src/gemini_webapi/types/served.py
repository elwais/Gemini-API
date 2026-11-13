from pydantic import BaseModel

from .availablemodel import AvailableModel


class ServedModel(BaseModel):
    """The model Google served a reply with, found in the raw response.

    Parameters
    ----------
    model_id: `str`
        The 16-hex id of the served model, as listed by `list_models()`.
    display_name: `str`
        The name Gemini shows for that model.
    via: `str`
        `"id"` when the id was found in the response, `"name"` when only the display name was.
    """

    model_id: str
    display_name: str
    via: str


# How much of the previous chunk to keep, so a name or id split across two chunks still matches.
_TAIL_CHARS = 300


def scan_served(state: dict, text: str, registry: dict[str, AvailableModel]) -> None:
    """Look for known model ids and display names in one decoded chunk of a raw stream.

    `state` is the per-generation dict the stream passes around; the matches are kept in it.
    A model id that appears quoted in the response is an id match; a display name that appears
    quoted is a name match, used only when no id matched (names can also occur in ordinary text).
    """
    buf = state.get("served_tail", "") + text
    state["served_tail"] = buf[-_TAIL_CHARS:]
    ids: set[str] = state.setdefault("served_ids", set())
    names: set[str] = state.setdefault("served_names", set())
    for model_id, model in registry.items():
        if model_id in ids:
            continue
        if any(q in buf for q in (f'"{model_id}"', f'\\"{model_id}\\"')):
            ids.add(model_id)
            continue
        if model_id in names:
            continue
        for label in (model.display_name, model.model_name):
            if label and any(q in buf for q in (f'"{label}"', f'\\"{label}\\"')):
                names.add(model_id)
                break


def pick_served(state: dict, registry: dict[str, AvailableModel]) -> ServedModel | None:
    """The served model, if the stream named exactly one known model by id, or else by name."""
    ids: set[str] = state.get("served_ids", set())
    names: set[str] = state.get("served_names", set())
    if len(ids) == 1:
        model_id, via = next(iter(ids)), "id"
    elif not ids and len(names) == 1:
        model_id, via = next(iter(names)), "name"
    else:
        return None
    model = registry.get(model_id)
    if model is None:
        return None
    return ServedModel(model_id=model_id, display_name=model.display_name or model.model_name, via=via)
