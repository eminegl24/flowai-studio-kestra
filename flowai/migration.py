"""Inventory supported SAP export declarations without translating their semantics."""
import json
import re
from pathlib import PurePosixPath

from defusedxml.ElementTree import fromstring

KINDS = {"job", "workflow", "dataflow"}
ATL_DECLARATION = re.compile(
    r"""^\s*(?:CREATE\s+)?(?:AL_)?(JOB|WORKFLOW|DATAFLOW)\s+(?:"([^"]+)"|([\w.\-]+))""",
    re.IGNORECASE | re.ASCII,
)


def inventory(filename, source):
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == ".atl":
        objects = [
            (match[1].lower(), match[2] or match[3])
            for line in source.splitlines()
            if (match := ATL_DECLARATION.match(line))
        ]
    elif suffix == ".xml":
        root = fromstring(source, forbid_dtd=True)
        objects = []
        for node in root.iter():
            kind = node.tag.rsplit("}", 1)[-1].lower().removeprefix("al_")
            name = node.get("name") or node.get("NAME")
            if kind in KINDS and name:
                objects.append((kind, name))
    else:
        raise ValueError("Use an .atl or .xml export.")
    objects = list(dict.fromkeys(objects))
    if not objects:
        raise ValueError("No supported declarations found in this export.")
    # A disabled draft deliberately performs no source operations.
    yaml = (
        "id: sap_migration_draft\nnamespace: migration.sap\ndisabled: true\ntasks:\n"
        "  - id: review_required\n    type: io.kestra.plugin.core.log.Log\n"
        f"    message: {json.dumps(f'Review {len(objects)} inventoried SAP objects before implementing this flow.')}\n"
    )
    return {
        "objects": [{"kind": kind, "name": name} for kind, name in objects],
        "draft": yaml,
        "warnings": ["Inventory only. Review mappings, transformations and dependencies manually."],
    }
