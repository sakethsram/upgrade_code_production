def extract_junos_versions(self, text):
    """
    Extract Junos versions for re0 and re1 from show version invoke-on all-routing-engines output.
    Looks up to 4 lines after "re0:" / "re1:" for a line starting with "Junos:".
    Returns dict: {"re0": version_string_or_None, "re1": version_string_or_None}
    """
    lines  = text.splitlines()
    result = {"re0": None, "re1": None}

    for re_label in ["re0:", "re1:"]:
        for i, line in enumerate(lines):
            if line.strip() == re_label:
                for look_ahead in range(1, 5):   # check up to 4 lines ahead
                    if i + look_ahead < len(lines):
                        candidate = lines[i + look_ahead].strip()
                        if candidate.lower().startswith("junos:"):
                            version = candidate.split(":", 1)[1].strip()
                            result[re_label[:-1]] = version
                            break
                break

a="""
"""