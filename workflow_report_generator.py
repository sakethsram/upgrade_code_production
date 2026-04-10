#!/usr/bin/env python3
"""
workflow_report_generator.py
Pre + Upgrade + Post driven by actual JSON data.
"""

from datetime import datetime
import json
import os
import difflib as _dl


PRE_TASK_TITLES = {
    "connect":                   "Connect to Device",
    "execute_show_commands":     "Collect Show Outputs",
    "show_version":              "Show Version",
    "check_storage":             "Check Storage",
    "backup_running_config":     "Backup Running Config",
    "transfer_image":            "Transfer Image",
    "verify_checksum":           "Verify Checksum",
}

UPGRADE_TASK_TITLES = {
    "status"   :            "Upgrade status",
    "connect":              "Connect to Device",
    "hops"     :            "Image Details",
}

POST_TASK_TITLES = {
    "connect":               "Connect to Device",
    "show_version":          "Show Version (Post-Upgrade)",
    "execute_show_commands": "Collect Show Outputs (Post-Upgrade)",
}

PHASE_META = {
    "pre":     {"label": "Pre-Checks",  "color": "#38bdf8"},
    "upgrade": {"label": "Upgrade",     "color": "#a78bfa"},
    "post":    {"label": "Post-Checks", "color": "#34d399"},
    # "report" card is intentionally removed — it was misleading
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _esc(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _norm_status(raw) -> str:
    if raw is True:  return "ok"
    if raw is False: return "failed"
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("success", "true", "completed", "ok", "passed",
                 "skipped", "generated", "low_space_cleaned", "already_upgraded"):
            return "ok"
        if s in ("failed", "false", "error", "rollback_failed"):
            return "failed"
        if s == "not_started":               return "not_started"
        if s in ("in_progress", "rolled_back"): return s
        if s == "":                          return ""
        return raw
    return str(raw) if raw is not None else ""


def _badge(status: str) -> str:
    m = {
        "ok":             '<span class="badge b-ok">OK</span>',
        "failed":         '<span class="badge b-fail">Failed</span>',
        "rollback_failed":'<span class="badge b-fail">Failed</span>',
        "not_started":    '<span class="badge b-ns">—</span>',
        "":               '<span class="badge b-ns">—</span>',
        "rolled_back":    '<span class="badge b-warn">Rolled Back</span>',
        "in_progress":    '<span class="badge b-ip">In Progress</span>',
        "low_space_cleaned": '<span class="badge b-warn">Cleaned</span>',
    }
    return m.get(status, f'<span class="badge b-ns">{_esc(status)}</span>')


def _remark(exc: str) -> str:
    return (f'<span class="remark-err">{_esc(exc)}</span>'
            if exc else '<span class="remark-na">—</span>')


# ─── command output drawer ────────────────────────────────────────────────────

def _cmd_drawer(cmds: list, prefix: str, phase: str) -> str:
    did = f"cmds-{prefix}-{phase}"
    if not cmds:
        return (f'<div class="cmd-drawer" hidden id="{did}">'
                f'<div class="cmd-empty">No commands collected.</div></div>')
    items = []
    for i, e in enumerate(cmds):
        lbl    = _esc(e.get("cmd", ""))
        raw    = _esc(e.get("output", "") or "(empty)")
        jobj   = e.get("json", {})
        jstr   = _esc(json.dumps(jobj, indent=2)) if jobj else "(not parsed)"
        exc    = _esc(e.get("exception", "") or "")
        ok     = exc == ""
        rid, jid, eid = (f"raw-{prefix}-{phase}-{i}",
                         f"jsn-{prefix}-{phase}-{i}",
                         f"exc-{prefix}-{phase}-{i}")
        err_btn = (f'<button class="mini-btn mini-err" onclick="tgl(\'{eid}\')">Why?</button>'
                   if not ok else "")
        items.append(f"""<div class="{'cmd-row ok' if ok else 'cmd-row fail'}">
  <div class="cm-hd">
    <span class="dot {'dot-ok' if ok else 'dot-fail'}"></span>
    <code class="cm-cmd">{lbl}</code>
    <div class="cm-btns">
      <button class="mini-btn" onclick="tgl('{rid}')">Raw</button>
      <button class="mini-btn" onclick="tgl('{jid}')">JSON</button>
      {err_btn}
    </div>
  </div>
  <div id="{rid}" class="log-box" hidden><pre>{raw}</pre></div>
  <div id="{jid}" class="log-box" hidden><pre>{jstr}</pre></div>
  {"" if ok else f'<div id="{eid}" class="log-box err-box" hidden><pre>{exc}</pre></div>'}
</div>""")
    return (f'<div class="cmd-drawer" hidden id="{did}">'
            f'<div class="cmd-list">{"".join(items)}</div></div>')

# ─── image transfer list ─────────────────────────────────────────────────────
def _image_drawer(entries: list, prefix: str):
    if not entries:
        return "", ""

    rows = []
    for i, e in enumerate(entries):
        status = _norm_status(e.get("status", "not_started"))
        image = _esc(e.get("image", "—"))
        exc = _esc(e.get("exception", "") or "")
        destination = _esc(e.get("destination", "") or "")

        rows.append(
            f'<tr class="task-row">'
            f'<td class="subtask-cell mono">{i+1}</td>'
            f'<td class="subtask-cell mono" style="word-break:break-all;font-size:.65rem;">{image}</td>'
            f'<td class="status-cell">{_badge(status)}</td>'
            f'<td class="subtask-cell mono" style="font-size:.63rem;line-height:1.7;">'
            f'<span style="color:var(--muted2);">path:</span> {destination}</td>'
            f'<td class="remark-cell mono">'
            f'{("<span class=remark-err>" + exc + "</span>") if exc else "<span class=remark-na>—</span>"}'
            f'</td></tr>'
        )

    cid = f"chk-image-{prefix}"
    toggle = f'<button class="mini-btn" onclick="tgl(\'{cid}\')">Images ({len(entries)})</button>'

    drawer = (
        f'<div class="drawer-slot">'
        f'<div class="cmd-drawer overlay" hidden id="{cid}">'
        f'<table class="hop-table"><tbody>{"".join(rows)}</tbody></table>'
        f'</div></div>'
    )
    return toggle, drawer

# ─── verify_checksum list ─────────────────────────────────────────────────────
def _checksum_drawer(entries: list, prefix: str):
    if not entries:
        return "", ""

    rows = []
    for i, e in enumerate(entries):
        image = _esc(e.get("image", "—"))
        status = _norm_status(e.get("status", "not_started"))
        match = e.get("match")
        expected = _esc(e.get("expected", "—"))
        computed = _esc(e.get("computed", "—") or "—")
        exc = _esc(e.get("exception", "") or "")

        match_html = (
            '<span class="badge b-ok">✓ Match</span>' if match is True else
            '<span class="badge b-fail">✗ Mismatch</span>' if match is False else
            '<span class="badge b-ns">—</span>'
        )

        rows.append(
            f'<tr class="task-row">'
            f'<td class="subtask-cell mono">{i+1}</td>'
            f'<td class="subtask-cell mono" style="word-break:break-all;font-size:.65rem;">{image}</td>'
            f'<td class="status-cell">{_badge(status)}</td>'
            f'<td class="status-cell">{match_html}</td>'
            f'<td class="remark-cell mono" style="font-size:.63rem;">'
            f'<span style="color:var(--muted2);">exp:</span> {expected}<br>'
            f'<span style="color:var(--muted2);">got:</span> {computed}'
            f'{("<br><span class=remark-err>" + exc + "</span>") if exc else ""}'
            f'</td></tr>'
        )

    cid = f"chk-checksum-{prefix}"
    toggle = f'<button class="mini-btn" onclick="tgl(\'{cid}\')">Checksums ({len(entries)})</button>'

    drawer = (
        f'<div class="drawer-slot">'
        f'<div class="cmd-drawer overlay" hidden id="{cid}">'
        f'<table class="hop-table"><tbody>{"".join(rows)}</tbody></table>'
        f'</div></div>'
    )
    return toggle, drawer

# ─── upgrade hops ─────────────────────────────────────────────────────────────

def _hops_rows(hops: list, pre_versions: dict) -> str:
    """
    Render hop rows. pre_versions is the dict captured before any upgrade
    ({"re0": "21.2R3", "re1": "21.2R3"}) stored at upgrade["pre_versions"].
    Each hop may also carry post_versions, switchover_1, switchover_2.
    """
    rows = []
    for i, hop in enumerate(hops):
        image  = hop.get("image", "—")
        status = _norm_status(hop.get("status", "not_started"))
        exc    = _esc(hop.get("exception", "") or "")
        md5    = hop.get("md5_match", None)
        conn   = hop.get("connect") if isinstance(hop.get("connect"), dict) else {}
        conn_st = _norm_status(conn.get("status", "not_started")) if conn else "not_started"
        conn_at = conn.get("attempt", "") if conn else ""
        conn_html = (f'<span class="badge b-ok">✓{" att "+str(conn_at) if conn_at else ""}</span>'
                     if conn_st == "ok" else _badge(conn_st))
        md5_html = ('<span class="badge b-ok">✓</span>'    if md5 is True  else
                    '<span class="badge b-fail">✗</span>'  if md5 is False else
                    '<span class="badge b-ns">—</span>')

        # ── RE0 / RE1 sub-status (dual-RE devices) ────────────────────────────
        re0 = hop.get("re0")
        re1 = hop.get("re1")
        re_html = ""
        if re0 is not None or re1 is not None:
            def _re_cell(label, re_data, pre_ver):
                if not re_data:
                    return f'<span class="re-chip re-ns">{label} —</span>'
                st  = _norm_status(re_data.get("status", "not_started"))
                ver = _esc(re_data.get("version", "") or "")
                cls = "re-ok" if st == "ok" else ("re-fail" if st == "failed" else "re-ns")
                # Show pre→post version arrow if we have both
                if pre_ver and ver and pre_ver != ver:
                    ver_part = (
                        f' <span class="re-ver" style="color:var(--muted2);">{_esc(pre_ver)}</span>'
                        f'<span class="re-arrow">→</span>'
                        f'<span class="re-ver">{ver}</span>'
                    )
                elif ver:
                    ver_part = f' <span class="re-ver">{ver}</span>'
                else:
                    ver_part = ""
                return f'<span class="re-chip {cls}">{label}{ver_part}</span>'

            pre_re0 = (pre_versions or {}).get("re0") or ""
            pre_re1 = (pre_versions or {}).get("re1") or ""

            # ── Switchover arrows (ACT2 and ACT4) ────────────────────────────
            sw1 = hop.get("switchover_1", "")   # e.g. "RE0(M)→RE1(M)"
            sw2 = hop.get("switchover_2", "")   # e.g. "RE1(M)→RE0(M)"
            sw_html = ""
            if sw1 or sw2:
                sw_parts = []
                if sw1:
                    sw_parts.append(f'<span class="sw-chip">{_esc(sw1)}</span>')
                if sw2:
                    sw_parts.append(f'<span class="sw-chip">{_esc(sw2)}</span>')
                sw_html = f'<div class="sw-row">{"".join(sw_parts)}</div>'

            # ── Post-hop versions ─────────────────────────────────────────────
            post_ver = hop.get("post_versions") or {}

            re_html = (
                f'<div class="re-chips">'
                f'{_re_cell("RE0", re0, pre_re0)}'
                f'{_re_cell("RE1", re1, pre_re1)}'
                f'</div>'
                f'{sw_html}'
            )

        if isinstance(image, (list, set)):
            nested_rows = []
            for j, img in enumerate(image):
                nested_rows.append(
                    f"<tr><td class='subtask-cell mono'>{i + 1}.{j}</td>"
                    f"<td class='subtask-cell mono' style='word-break:break-all;font-size:.65rem;'>{_esc(img)}</td></tr>"
                )
            image_html = (
                f'<table class="hop-table nested"><thead><tr>'
                f'<th>#</th><th>SMU Image</th>'
                f'</tr></thead><tbody>{"".join(nested_rows)}</tbody></table>'
            )
        else:
            image_html = _esc(image)

        rows.append(
            f'<tr class="task-row{"" if status in ("ok","not_started","") else " failed-row"}">'
            f'<td class="hop-num-cell">{i+1}</td>'
            f'<td class="hop-image-cell">{image_html}{re_html}</td>'
            f'<td class="hop-status-cell">{_badge(status)}</td>'
            f'<td class="hop-status-cell">{md5_html}</td>'
            f'<td class="hop-status-cell">{conn_html}</td>'
            f'<td class="hop-remark-cell">{"<span class=remark-err>" + exc + "</span>" if exc else "<span class=remark-na>—</span>"}</td>'
            f'</tr>'
        )
    return "\n".join(rows)


# ─── pre-phase rows ───────────────────────────────────────────────────────────

def _pre_rows(tasks: dict, prefix: str) -> tuple:
    color = PHASE_META["pre"]["color"]
    label = PHASE_META["pre"]["label"]
    items = [(n, d) for n, d in tasks.items() if isinstance(d, (dict, list))]
    count = len(items)
    rows  = []
    total = success = failed = 0
    first = True

    for name, data in items:
        # ── image details is a LIST ─────────────────────────────────────────
        if name == "transfer_image" and isinstance(data, list):
            if not data:
                agg = "not_started"
            elif all(_norm_status(e.get("status","")) == "ok" for e in data):
                agg = "ok"
            elif any(_norm_status(e.get("status","")) == "failed" for e in data):
                agg = "failed"
            else:
                agg = _norm_status(data[0].get("status", "not_started"))

            is_blank = agg in ("", "not_started")
            # CHANGE: only count toward total if actually started
            if not is_blank:
                total += 1
                if agg == "ok":   success += 1
                else:             failed += 1

            toggle, drawer = _image_drawer(data, prefix)
            pc = (f'<td class="phase-cell" rowspan="{count}" '
                  f'style="border-left:3px solid {color};">'
                  f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
                  ) if first else ""
            first = False
            rows.append(
                f'<tr class="task-row{"" if (agg == "ok" or is_blank) else " failed-row"}">'
                f'{pc}'
                f'<td class="subtask-cell"><span class="mono">'
                f'{PRE_TASK_TITLES.get(name, name)}</span> {toggle}{drawer}</td>'
                f'<td class="status-cell">{_badge(agg)}</td>'
                f'<td class="remark-cell"><span class="remark-na">—</span></td>'
                f'</tr>'
            )
            continue

        # ── verify_checksum is a LIST ─────────────────────────────────────────
        if name == "verify_checksum" and isinstance(data, list):
            if not data:
                agg = "not_started"
            elif all(_norm_status(e.get("status","")) == "ok" for e in data):
                agg = "ok"
            elif any(_norm_status(e.get("status","")) == "failed" for e in data):
                agg = "failed"
            else:
                agg = _norm_status(data[0].get("status", "not_started"))

            is_blank = agg in ("", "not_started")
            # CHANGE: only count toward total if actually started
            if not is_blank:
                total += 1
                if agg == "ok":   success += 1
                else:             failed += 1

            toggle, drawer = _checksum_drawer(data, prefix)
            pc = (f'<td class="phase-cell" rowspan="{count}" '
                  f'style="border-left:3px solid {color};">'
                  f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
                 ) if first else ""
            first = False
            rows.append(
                    f'<tr class="task-row{"" if (agg == "ok" or is_blank) else " failed-row"}">'
                    f'{pc}'
                    f'<td class="subtask-cell"><span class="mono">'
                    f'{PRE_TASK_TITLES.get(name, name)}</span> {toggle}{drawer}</td>'
                    f'<td class="status-cell">{_badge(agg)}</td>'
                    f'<td class="remark-cell"><span class="remark-na">—</span></td>'
                    f'</tr>'
            )
            continue

        # ── standard dict task ────────────────────────────────────────────────
        status   = _norm_status(data.get("status", ""))
        is_blank = status in ("", "not_started")
        exc      = data.get("exception", "") or ""
        display  = PRE_TASK_TITLES.get(name, name.replace("_", " ").title())

        # CHANGE: only count toward total if actually started
        if not is_blank:
            total += 1
            if status == "ok":   success += 1
            else:                failed  += 1

        pc = (f'<td class="phase-cell" rowspan="{count}" '
              f'style="border-left:3px solid {color};">'
              f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
              ) if first else ""
        first = False

        toggle = drawer = ""
        if name == "execute_show_commands":
            cmds   = data.get("commands", [])
            bid    = f"cmds-{prefix}-pre"
            toggle = f'<button class="mini-btn" onclick="tgl(\'{bid}\')">Outputs ({len(cmds)})</button>'
            drawer = _cmd_drawer(cmds, prefix, "pre")

        # task-specific remarks
        if name == "connect":
            ping = data.get("ping", None)
            parts = []
            if ping is not None:
                p = str(ping).lower()
                parts.append(f'<span class="remark-ok">ping: {_esc(p)}</span>'
                              if p in ("up","true")
                              else f'<span class="remark-err">ping: {_esc(p)}</span>')
            if exc: parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'

        elif name == "check_storage":
            parts = []
            deleted = data.get("deleted_files", [])
            if deleted: parts.append('<span class="remark-ok">files cleaned</span>')
            if data.get("sufficient") is False and status != "ok":
                parts.append('<span class="remark-err">insufficient space</span>')
            if exc: parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'

        elif name == "backup_active_filesystem":
            dc = data.get("disk_count", "")
            parts = []
            if dc: parts.append(f'<span class="mono" style="color:var(--muted2);">disks: {_esc(dc)}</span>')
            if exc: parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'

        elif name == "backup_running_config":
            cfg  = data.get("config_file","") or data.get("log_file","")
            dest = data.get("destination","")
            parts = []
            if cfg:  parts.append(f'<span class="mono" style="color:var(--muted2);">{_esc(cfg)}</span>')
            if dest: parts.append(f'<span class="mono" style="color:var(--muted2);">&#8594; {_esc(dest)}</span>')
            if exc:  parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " ".join(parts) or '<span class="remark-na">—</span>'

        elif name == "show_version":
            ver  = data.get("version","")
            plat = data.get("platform","")
            hn   = data.get("hostname","")
            parts = []
            if hn:   parts.append(f'<span class="mono" style="color:var(--accent);">{_esc(hn)}</span>')
            if plat: parts.append(f'<span class="mono" style="color:var(--muted2);">{_esc(plat)}</span>')
            if ver:  parts.append(f'<span class="mono" style="color:var(--muted2);">v{_esc(ver)}</span>')
            if exc:  parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'

        else:
            remark = _remark(exc)

        row_cls = "" if (status == "ok" or is_blank) else " failed-row"
        rows.append(
            f'<tr class="task-row{row_cls}">'
            f'{pc}'
            f'<td class="subtask-cell"><span class="mono">{_esc(display)}</span>'
            f' {toggle}{drawer}</td>'
            f'<td class="status-cell">{_badge(status)}</td>'
            f'<td class="remark-cell">{remark}</td>'
            f'</tr>'
        )

    return "\n".join(rows), total, success, failed


# ─── upgrade rows ─────────────────────────────────────────────────────────────

def _upgrade_rows(upg: dict, prefix: str) -> tuple:
    color      = PHASE_META["upgrade"]["color"]
    label      = PHASE_META["upgrade"]["label"]
    rows       = []
    total   = success = failed = 0
    items = [(n, d) for n, d in upg.items()]
    count = len(items)
    first = True

    # Pull pre_versions once — passed down to _hops_rows
    pre_versions = upg.get("pre_versions") or {}

    for name, data in items:

        # Skip internal tracking keys — not rendered as rows
        if name in ("pre_versions",):
            continue

        # ── hops is a LIST ───────────────────────────────────────────────
        if name == "hops" and isinstance(data, list):
            if not data:
                agg = "not_started"
            elif all(_norm_status(e.get("status","")) == "ok" for e in data):
                agg = "ok"
            elif any(_norm_status(e.get("status","")) == "failed" for e in data):
                agg = "failed"
            else:
                agg = _norm_status(data[0].get("status", "not_started"))

            is_blank = agg in ("", "not_started")
            # CHANGE: only count if started
            if not is_blank:
                total += 1
                if agg == "ok": success += 1
                else:           failed += 1

            toggle = (f'<button class="mini-btn" onclick="tglHops(\'hops-{prefix}\')">'
                      f'Hops ({len(data)})</button>')
            drawer = (f'<div class="hops-slot">'
                      f'<div class="hops-inline" hidden id="hops-{prefix}">'
                      f'<div class="hop-table-wrap">'
                      f'<table class="hop-table"><thead><tr>'
                      f'<th>#</th><th>Image / RE Versions</th><th>Status</th><th>MD5</th>'
                      f'<th>Reconnect</th><th>Remark</th>'
                      f'</tr></thead><tbody>{_hops_rows(data, pre_versions)}</tbody></table>'
                      f'</div></div></div>')

            pc = (f'<td class="phase-cell" rowspan="{count}" '
                  f'style="border-left:3px solid {color};">'
                  f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
                  ) if first else ""
            first = False

            rows.append(
                f'<tr class="task-row{"" if (agg == "ok" or is_blank) else " failed-row"}">'
                f'{pc}'
                f'<td class="subtask-cell"><span class="mono">'
                f'{UPGRADE_TASK_TITLES.get(name, name)}</span> {toggle}{drawer}</td>'
                f'<td class="status-cell">{_badge(agg)}</td>'
                f'<td class="remark-cell"><span class="remark-na">—</span></td>'
                f'</tr>'
            )
            continue

        pc = (f'<td class="phase-cell" rowspan="{count}" '
              f'style="border-left:3px solid {color};">'
              f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
              ) if first else ""
        first = False

        toggle = drawer = ""

        # ── handle strings ───────────────────────────────
        if isinstance(data, str):

            if name.lower() == "initial_os":
                initial_os = _esc(upg.get("initial_os", "—") or "—")
                target_os  = _esc(upg.get("target_os",  "—") or "—")
                rows.append(
                    f'<tr class="task-row">'
                    f'{pc}'
                    f'<td class="subtask-cell"><span class="mono">OS Path</span></td>'
                    f'<td class="status-cell"></td>'
                    f'<td class="remark-cell mono" style="color:var(--muted2);">'
                    f'{initial_os} &#8594; {target_os}</td>'
                    f'</tr>'
                )
                continue

            if name.lower() == "target_os" or name.lower() == "exception":
                continue

            display = UPGRADE_TASK_TITLES.get(name, name.replace("_", " ").title())
            status  = _norm_status(data)
            exc     = _esc(upg.get("exception", "") or "")
            is_blank = status in ("", "not_started")
            # CHANGE: only count if started
            if not is_blank:
                total += 1
                if status == "ok": success += 1
                else:              failed += 1
            row_cls = "" if status in ("ok", "", "not_started") else " failed-row"
            rows.append(
                f'<tr class="task-row{row_cls}">'
                f'{pc}'
                f'<td class="subtask-cell"><span class="mono">{_esc(display)}</span></td>'
                f'<td class="status-cell">{_badge(status)}</td>'
                f'<td class="remark-cell">{_remark(exc)}</td>'
                f'</tr>'
            )
            continue

        # ── standard dict task ────────────────────────────────────────────────
        if isinstance(data, dict):
            status   = _norm_status(data.get("status", ""))
            is_blank = status in ("", "not_started")
            exc      = data.get("exception", "") or ""
            display  = UPGRADE_TASK_TITLES.get(name, name.replace("_", " ").title())

            # CHANGE: only count if started
            if not is_blank:
                total += 1
                if status == "ok":   success += 1
                else:                failed  += 1

            row_cls = "" if (status == "ok" or is_blank) else " failed-row"
            rows.append(
                f'<tr class="task-row{row_cls}">'
                f'{pc}'
                f'<td class="subtask-cell"><span class="mono">{_esc(display)}</span></td>'
                f'<td class="status-cell">{_badge(status)}</td>'
                f'<td class="remark-cell">{_remark(exc)}</td>'
                f'</tr>'
            )

    rows.append('<tr class="phase-sep"><td colspan="4"></td></tr>')
    return "\n".join(rows), total, success, failed


# ─── post rows ────────────────────────────────────────────────────────────────

def _post_rows(post: dict, prefix: str) -> tuple:
    color = PHASE_META["post"]["color"]
    label = PHASE_META["post"]["label"]

    items = [(n, d) for n, d in post.items()]
    count = len(items)
    rows   = []
    total  = success = failed = 0
    first  = True

    for name, data in items:

        status   = _norm_status(data.get("status", ""))
        is_blank = status in ("", "not_started")
        exc      = data.get("exception", "") or ""
        display  = POST_TASK_TITLES.get(name, name.replace("_", " ").title())

        # CHANGE: only count if started
        if not is_blank:
            total += 1
            if status == "ok":   success += 1
            else:                failed  += 1

        pc = (f'<td class="phase-cell" rowspan="{count}" '
              f'style="border-left:3px solid {color};">'
              f'<span class="phase-lbl" style="color:{color};">{label}</span></td>'
              ) if first else ""
        first = False

        toggle = drawer = ""

        if name == "execute_show_commands":
            cmds   = data.get("commands", [])
            bid    = f"cmds-{prefix}-post"
            toggle = f'<button class="mini-btn" onclick="tgl(\'{bid}\')">Outputs ({len(cmds)})</button>'
            drawer = _cmd_drawer(cmds, prefix, "post")

        if name == "connect":
            ping = data.get("ping", None)
            parts = []
            if ping is not None:
                p = str(ping).lower()
                parts.append(f'<span class="remark-ok">ping: {_esc(p)}</span>'
                              if p in ("up","true")
                              else f'<span class="remark-err">ping: {_esc(p)}</span>')
            if exc: parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'

        elif name == "show_version":
            ver  = data.get("version","")
            plat = data.get("platform","")
            hn   = data.get("hostname","")
            parts = []
            if hn:   parts.append(f'<span class="mono" style="color:var(--accent);">{_esc(hn)}</span>')
            if plat: parts.append(f'<span class="mono" style="color:var(--muted2);">{_esc(plat)}</span>')
            if ver:  parts.append(f'<span class="mono" style="color:#86efac;">v{_esc(ver)}</span>')
            if exc:  parts.append(f'<span class="remark-err">{_esc(exc)}</span>')
            remark = " &nbsp;·&nbsp; ".join(parts) or '<span class="remark-na">—</span>'
        else:
            remark = _remark(exc)

        row_cls = "" if (status == "ok" or is_blank) else " failed-row"
        rows.append(
            f'<tr class="task-row{row_cls}">'
            f'{pc}'
            f'<td class="subtask-cell"><span class="mono">{_esc(display)}</span>'
            f' {toggle}{drawer}</td>'
            f'<td class="status-cell">{_badge(status)}</td>'
            f'<td class="remark-cell">{remark}</td>'
            f'</tr>'
        )

    rows.append('<tr class="phase-sep"><td colspan="4"></td></tr>')
    return "\n".join(rows), total, success, failed


# ─── report / diff phase ──────────────────────────────────────────────────────

import difflib as _difflib


def _inline_diff_html(pre_out: str, post_out: str) -> tuple:
    pre_lines  = pre_out.splitlines() if pre_out else []
    post_lines = post_out.splitlines() if post_out else []
    matcher    = _difflib.SequenceMatcher(None, pre_lines, post_lines, autojunk=False)

    pre_col  = []
    post_col = []

    def _mark_line_diff(a: str, b: str):
        sm     = _difflib.SequenceMatcher(None, a, b, autojunk=False)
        ha, hb = [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                ha.append(_esc(a[i1:i2]))
                hb.append(_esc(b[j1:j2]))
            elif tag == "replace":
                ha.append(f'<mark class="diff-del">{_esc(a[i1:i2])}</mark>')
                hb.append(f'<mark class="diff-ins">{_esc(b[j1:j2])}</mark>')
            elif tag == "delete":
                ha.append(f'<mark class="diff-del">{_esc(a[i1:i2])}</mark>')
            elif tag == "insert":
                hb.append(f'<mark class="diff-ins">{_esc(b[j1:j2])}</mark>')
        return "".join(ha), "".join(hb)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for ln in pre_lines[i1:i2]:
                pre_col.append(f'<span class="diff-eq">{_esc(ln)}</span>')
                post_col.append(f'<span class="diff-eq">{_esc(ln)}</span>')
        elif tag == "replace":
            a_blk = pre_lines[i1:i2]
            b_blk = post_lines[j1:j2]
            pairs = min(len(a_blk), len(b_blk))
            for k in range(pairs):
                ha, hb = _mark_line_diff(a_blk[k], b_blk[k])
                pre_col.append(f'<span class="diff-line-del">{ha}</span>')
                post_col.append(f'<span class="diff-line-ins">{hb}</span>')
            for k in range(pairs, len(a_blk)):
                pre_col.append(f'<span class="diff-line-del">{_esc(a_blk[k])}</span>')
                post_col.append(f'<span class="diff-na">N/A</span>')
            for k in range(pairs, len(b_blk)):
                pre_col.append(f'<span class="diff-na">N/A</span>')
                post_col.append(f'<span class="diff-line-ins">{_esc(b_blk[k])}</span>')
        elif tag == "delete":
            for ln in pre_lines[i1:i2]:
                pre_col.append(f'<span class="diff-line-del">{_esc(ln)}</span>')
                post_col.append(f'<span class="diff-na">N/A</span>')
        elif tag == "insert":
            for ln in post_lines[j1:j2]:
                pre_col.append(f'<span class="diff-na">N/A</span>')
                post_col.append(f'<span class="diff-line-ins">{_esc(ln)}</span>')

    pre_html  = "\n".join(pre_col)  or "<span class='diff-na'>(empty)</span>"
    post_html = "\n".join(post_col) or "<span class='diff-na'>(empty)</span>"
    return pre_html, post_html


def _report_rows(diff: dict, device_data: dict, prefix: str) -> str:
    color = "#fb923c"   # report phase colour kept for the diff section only

    if not diff:
        rows = [
            (f'<tr class="task-row">'
             f'<td class="phase-cell" rowspan="2" style="border-left:3px solid {color};">'
             f'<span class="phase-lbl" style="color:{color};">Report</span></td>'
             f'<td class="subtask-cell"><span class="mono">Diff Status</span></td>'
             f'<td class="status-cell"><span class="badge b-ns">Pending</span></td>'
             f'<td class="remark-cell"><span class="remark-na">—</span></td>'
             f'</tr>'),
            (f'<tr class="task-row">'
             f'<td class="subtask-cell" colspan="3">'
             f'<div class="diff-none">Diff will be available after post-checks complete.</div>'
             f'</td></tr>'),
            '<tr class="phase-sep"><td colspan="4"></td></tr>',
        ]
        return "\n".join(rows)

    changed_cmds = sorted(diff.keys())
    total_cmds   = len(changed_cmds)

    pre_cmds  = device_data.get("pre",  {}).get("execute_show_commands", {}).get("commands", [])
    post_cmds = device_data.get("post", {}).get("execute_show_commands", {}).get("commands", [])
    pre_map   = {c["cmd"]: c.get("output", "") for c in pre_cmds}
    post_map  = {c["cmd"]: c.get("output", "") for c in post_cmds}
    total_compared = len(set(pre_map) | set(post_map))

    diff_buttons = " ".join(
        f'<button class="mini-btn" style="font-size:.5rem;" onclick="tglDiff(\'diff-{prefix}-{abs(hash(cmd)) % 999999}\')">'
        f'{_esc(cmd)}</button>'
        for cmd in changed_cmds
    )

    rows = [
        (f'<tr class="task-row">'
         f'<td class="phase-cell" rowspan="2" style="border-left:3px solid {color};">'
         f'<span class="phase-lbl" style="color:{color};">Report</span></td>'
         f'<td class="subtask-cell"><span class="mono">Diff Status</span></td>'
         f'<td class="status-cell"><span class="badge b-ok">Complete</span></td>'
         f'<td class="remark-cell mono" style="color:var(--muted2);">'
         f'{total_cmds} changed &nbsp;·&nbsp; {total_compared} compared</td>'
         f'</tr>'),
        (f'<tr class="task-row">'
         f'<td class="subtask-cell" colspan="3">'
         f'<span class="mono" style="color:var(--muted2);font-size:.63rem;display:block;margin-bottom:.3rem;">Show diff:</span>'
         f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:.25rem;">{diff_buttons}</div>'
         f'</td></tr>'),
        '<tr class="phase-sep"><td colspan="4"></td></tr>',
    ]

    return "\n".join(rows)


def _diff_section(diff: dict, device_data: dict, prefix: str) -> str:
    if not diff:
        return ""

    pre_cmds  = device_data.get("pre",  {}).get("execute_show_commands", {}).get("commands", [])
    post_cmds = device_data.get("post", {}).get("execute_show_commands", {}).get("commands", [])
    pre_map   = {c["cmd"]: c.get("output", "") for c in pre_cmds}
    post_map  = {c["cmd"]: c.get("output", "") for c in post_cmds}

    blocks = []
    for cmd in sorted(diff.keys()):
        pre_out  = pre_map.get(cmd, "")
        post_out = post_map.get(cmd, "")
        pre_html, post_html = _inline_diff_html(pre_out, post_out)
        did = f"diff-{prefix}-{abs(hash(cmd)) % 999999}"

        blocks.append(f"""
<div class="diff-block" id="{did}" hidden>
  <div class="diff-block-hdr">
    <div class="diff-block-cmd">
      <code class="diff-block-cmdname">{_esc(cmd)}</code>
    </div>
    <button class="mini-btn mini-err" onclick="tglDiff('{did}')">Close</button>
  </div>
  <div class="diff-grid">
    <div class="diff-col-hdr">Pre-Upgrade</div>
    <div class="diff-col-hdr">Post-Upgrade</div>
    <div class="diff-pane"><pre>{pre_html}</pre></div>
    <div class="diff-pane"><pre>{post_html}</pre></div>
  </div>
</div>""")

    return f'<div class="diff-section" id="diffsec-{prefix}">{"".join(blocks)}</div>'


# ─── full tbody ───────────────────────────────────────────────────────────────

def build_tbody(device_data: dict, device_key: str) -> tuple:
    prefix   = device_key.replace(".", "_").replace("-", "_")
    all_rows = []
    total = success = failed = 0

    pre = device_data.get("pre", {})
    if pre:
        r, t, s, f = _pre_rows(pre, prefix)
        all_rows.append(r); total += t; success += s; failed += f
        all_rows.append('<tr class="phase-sep"><td colspan="4"></td></tr>')

    upg = device_data.get("upgrade", {})
    if upg:
        r, t, s, f = _upgrade_rows(upg, prefix)
        all_rows.append(r); total += t; success += s; failed += f
        all_rows.append('<tr class="phase-sep"><td colspan="4" style="border-top:2px solid #2a3044; height:8px;"></td></tr>')

    post = device_data.get("post", {})
    if post:
        r, t, s, f = _post_rows(post, prefix)
        all_rows.append(r); total += t; success += s; failed += f
        all_rows.append('<tr class="phase-sep"><td colspan="4" style="border-top:2px solid #2a3044; height:8px;"></td></tr>')

    diff = device_data.get("diff", {})
    all_rows.append(_report_rows(diff, device_data, prefix))

    return "\n".join(all_rows), total, success, failed


# ─── phase summary for cards ──────────────────────────────────────────────────

def _phase_summary(device_data: dict) -> dict:
    out = {}

    pre = device_data.get("pre", {})
    t = s = f = 0
    for name, td in pre.items():
        if isinstance(td, list):
            if not td: continue
            st = ("ok"     if all(_norm_status(e.get("status","")) == "ok" for e in td) else
                  "failed" if any(_norm_status(e.get("status","")) == "failed" for e in td) else
                  _norm_status(td[0].get("status","not_started")))
        elif isinstance(td, dict):
            st = _norm_status(td.get("status",""))
        else:
            continue
        # CHANGE: only count if actually started
        if st in ("","not_started"): continue
        t += 1
        if st == "ok": s += 1
        else: f += 1
    out["pre"] = (t, s, f)

    hops = device_data.get("upgrade", {}).get("hops", [])
    # CHANGE: only count hops that have been started
    started_hops = [h for h in hops if _norm_status(h.get("status","")) not in ("","not_started")]
    hok  = sum(1 for h in started_hops if _norm_status(h.get("status","")) == "ok")
    out["upgrade"] = (len(started_hops), hok, len(started_hops) - hok)

    post = device_data.get("post", {})
    pt = ps = pf = 0
    for name in ("connect", "show_version", "execute_show_commands"):
        td = post.get(name, {})
        if not td: continue
        st = _norm_status(td.get("status",""))
        # CHANGE: only count if actually started
        if st in ("","not_started"): continue
        pt += 1
        if st == "ok": ps += 1
        else: pf += 1
    out["post"] = (pt, ps, pf)

    return out


# ─── device panel ─────────────────────────────────────────────────────────────

def build_device_panel(device_key: str, device_data: dict, is_first: bool) -> str:
    dk = _esc(device_key)

    tbody, total, success, failed = build_tbody(device_data, device_key)
    summary = _phase_summary(device_data)
    prefix  = device_key.replace(".", "_").replace("-", "_")
    diff    = device_data.get("diff", {})
    diff_sec = _diff_section(diff, device_data, prefix)

    di = device_data.get("device_info", {})
    pre_ver  = device_data.get("pre",  {}).get("show_version", {}).get("version", "—") or "—"
    post_ver = device_data.get("post", {}).get("show_version", {}).get("version", "—") or "—"

    def phase_card(key):
        t, s, f = summary.get(key, (0, 0, 0))
        meta = PHASE_META[key]
        if t == 0:
            # Phase not started yet — render as dimmed/incomplete
            return (
                f'<div class="ph-card ph-card-inactive">'
                f'<div class="ph-top">'
                f'<span class="ph-lbl" style="color:var(--muted);">{meta["label"]}</span>'
                f'<span class="pill partial" style="font-size:.58rem;opacity:.45;">Not Started</span>'
                f'</div>'
                f'<div class="prog"><div class="progbar" style="width:0%;background:var(--border2);"></div></div>'
                f'</div>'
            )
        pct = round(s / t * 100) if t else 0
        cls = "ok" if f == 0 else ("fail" if s == 0 else "partial")
        label = "Hops" if key == "upgrade" else "Tasks"
        inner = f"{s}/{t} {label}"
        return (
            f'<div class="ph-card">'
            f'<div class="ph-top">'
            f'<span class="ph-lbl" style="color:{meta["color"]};">{meta["label"]}</span>'
            f'<span class="pill {cls}" style="font-size:.58rem;">{inner}</span>'
            f'</div>'
            f'<div class="prog"><div class="progbar" '
            f'style="width:{pct}%;background:{meta["color"]};"></div></div>'
            f'</div>'
        )

    # CHANGE: "report" card removed from phase_cards entirely
    phase_cards = "".join(phase_card(k) for k in ("pre", "upgrade", "post"))

    display = "block" if is_first else "none"
    return f"""
<div class="device-panel" id="panel-{dk}" style="display:{display};">
  <div class="dev-hdr">
    <div class="dev-meta">
      <div class="dev-title">
        <span class="dev-ip" id="di-host-{dk}">{_esc(di.get('host','—'))}</span>
        <span class="dev-sep">·</span>
        <span class="dev-vendor" id="di-vendor-{dk}">{_esc((di.get('vendor','') or '').upper())}</span>
        <span class="dev-sep">·</span>
        <span class="dev-model" id="di-model-{dk}">{_esc((di.get('model','') or '').upper())}</span>
      </div>
      <div class="dev-hn">
        <span class="mono" id="di-hostname-{dk}">{_esc(di.get('hostname','—'))}</span>
        <span class="ver-badge">
          <span style="color:var(--muted2);">pre</span>
          <span id="di-pre-version-{dk}">{_esc(pre_ver)}</span>
          <span style="color:var(--muted2);">→ post</span>
          <span id="di-post-version-{dk}" style="color:#86efac;">{_esc(post_ver)}</span>
        </span>
      </div>
    </div>
  </div>

  <div class="ph-cards">{phase_cards}</div>

  <div class="tbl-wrap">
    <table class="main-tbl">
      <thead>
        <tr>
          <th class="th-phase">Phase</th>
          <th class="th-task">Task</th>
          <th class="th-status">Status</th>
          <th class="th-remark">Remark</th>
        </tr>
      </thead>
      <tbody>
        {tbody}
      </tbody>
    </table>
  </div>

  {diff_sec}
</div>"""


# ─── overall stats ────────────────────────────────────────────────────────────

def _overall_stats(workflow_data: dict) -> tuple:
    total = success = failed = 0
    for dd in workflow_data.values():
        for name, td in dd.get("pre", {}).items():
            if isinstance(td, list):
                if not td: continue
                st = ("ok"     if all(_norm_status(e.get("status","")) == "ok" for e in td) else
                      "failed" if any(_norm_status(e.get("status","")) == "failed" for e in td) else
                      _norm_status(td[0].get("status","not_started")))
            elif isinstance(td, dict):
                st = _norm_status(td.get("status",""))
            else:
                continue
            if st in ("","not_started"): continue
            total += 1
            if st == "ok": success += 1
            else: failed += 1

        st = _norm_status(dd.get("upgrade",{}).get("status",""))
        if st not in ("","not_started"):
            total += 1
            if st == "ok": success += 1
            else: failed += 1

        for name in ("connect", "show_version", "execute_show_commands"):
            td = dd.get("post",{}).get(name, {})
            if not td: continue
            st = _norm_status(td.get("status",""))
            if st in ("","not_started"): continue
            total += 1
            if st == "ok": success += 1
            else: failed += 1

    return total, success, failed


def _device_info_json(workflow_data: dict) -> str:
    out = {}
    for dk, dd in workflow_data.items():
        pre_ver  = dd.get("pre",  {}).get("show_version", {}).get("version", "") or "—"
        post_ver = dd.get("post", {}).get("show_version", {}).get("version", "") or "—"
        out[dk] = {
            "host":         dd.get("device_info",{}).get("host","—") or "—",
            "vendor":       (dd.get("device_info",{}).get("vendor","—") or "—").upper(),
            "model":        (dd.get("device_info",{}).get("model","—") or "—").upper(),
            "hostname":     dd.get("device_info",{}).get("hostname","—") or "—",
            "pre_version":  pre_ver,
            "post_version": post_ver,
        }
    return json.dumps(out)


# ─── overall device-level pass/fail ──────────────────────────────────────────

def _count_device_states(workflow_data: dict) -> tuple:
    """
    Return (total_devices, passed, failed, in_progress).

    CHANGE: A device is only 'passed' when:
      - upgrade status == "success"  AND
      - at least one post check has completed OK
    A device is 'failed' when upgrade status == "failed" OR any pre task failed.
    Everything else is 'in_progress' (upgrade not yet started, or still running).
    """
    total       = len(workflow_data)
    passed      = 0
    failed      = 0
    in_progress = 0

    for dd in workflow_data.values():
        upg_st = _norm_status(dd.get("upgrade", {}).get("status", ""))

        # Check if any pre task explicitly failed
        pre_failed = any(
            _norm_status(
                td[0].get("status", "") if isinstance(td, list) and td and isinstance(td[0], dict)
                else td.get("status", "") if isinstance(td, dict)
                else ""
            ) == "failed"
            for td in dd.get("pre", {}).values()
            if isinstance(td, (dict, list))
        )

        # Post check completion: at least show_version or execute_show_commands done
        post_done = any(
            _norm_status(dd.get("post", {}).get(k, {}).get("status", "")) == "ok"
            for k in ("show_version", "execute_show_commands")
        )

        if pre_failed or upg_st == "failed":
            failed += 1
        elif upg_st == "success" and post_done:
            passed += 1
        else:
            in_progress += 1

    return total, passed, failed, in_progress


# ─── HTML generation ──────────────────────────────────────────────────────────

def generate_html_report(workflow_data: dict, output_dir: str = ".", stem: str = None) -> str:
    safe_data = {
        dk: {k: v for k, v in slot.items() if k not in ("conn","yaml")}
        for dk, slot in workflow_data.items()
    }
    device_keys = list(safe_data.keys())
    now         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_file     = datetime.now().strftime("%d_%m_%y_%H_%M_%S")

    # CHANGE: use the new 4-value counter for the top-right pill
    total_dev, passed_dev, failed_dev, inprog_dev = _count_device_states(safe_data)

    if failed_dev > 0 and passed_dev == 0:
        pill_cls = "fail"
        pill_txt = f"{failed_dev}/{total_dev} DEVICE(S) FAILED"
    elif failed_dev > 0:
        pill_cls = "partial"
        pill_txt = f"{passed_dev} PASSED · {failed_dev} FAILED · {inprog_dev} IN PROGRESS"
    elif inprog_dev > 0:
        pill_cls = "partial"
        pill_txt = f"{inprog_dev}/{total_dev} DEVICE(S) IN PROGRESS"
    else:
        pill_cls = "ok"
        pill_txt = f"ALL {total_dev} DEVICE(S) PASSED"

    dropdown_opts = "\n".join(
        f'<option value="{_esc(dk)}"{" selected" if i==0 else ""}>'
        f'{_esc(dk)} — {_esc(safe_data[dk].get("device_info",{}).get("host","—"))}'
        f'</option>'
        for i, dk in enumerate(device_keys)
    )
    device_panels = "\n".join(
        build_device_panel(dk, safe_data[dk], i==0)
        for i, dk in enumerate(device_keys)
    )
    di_json   = _device_info_json(safe_data)
    json_html = _esc(json.dumps(safe_data, indent=2, default=str))
    first_key = _esc(device_keys[0]) if device_keys else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Workflow Report — {len(device_keys)} Device(s)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
/* ── reset & root ────────────────────────────────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0a0c10;
  --surf:#111318;
  --surf2:#181c24;
  --surf3:#1e2330;
  --border:#1f2535;
  --border2:#2a3044;
  --text:#dde3f0;
  --muted:#4a5568;
  --muted2:#8896aa;
  --accent:#38bdf8;
  --ok:#22c55e;
  --err:#f43f5e;
  --warn:#f59e0b;
  --mono:"JetBrains Mono",monospace;
  --sans:"DM Sans",sans-serif;
  --r:6px;
}}
body{{
  font-family:var(--sans);
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  padding:2rem 1rem 4rem;
  font-size:14px;
}}
.wrap{{max-width:1160px;margin:0 auto}}

/* ── header ─────────────────────────────────────────────────────────────── */
.hdr{{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:1.5rem;
  padding-bottom:1rem;
  border-bottom:1px solid var(--border);
}}
.hdr h1{{
  font-size:1.4rem;
  font-weight:700;
  color:var(--text);
  letter-spacing:-.02em;
}}
.hdr h1 span{{color:var(--accent)}}
.sub{{font-size:.72rem;color:var(--muted2);margin-top:.25rem;font-family:var(--mono)}}

/* ── pills ───────────────────────────────────────────────────────────────── */
.pill{{
  display:inline-flex;
  align-items:center;
  padding:.25rem .65rem;
  border-radius:20px;
  font-size:.68rem;
  font-weight:700;
  letter-spacing:.04em;
  white-space:nowrap;
}}
.pill.ok{{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.3)}}
.pill.fail{{background:rgba(244,63,94,.15);color:#fb7185;border:1px solid rgba(244,63,94,.3)}}
.pill.partial{{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.3)}}

/* ── selector bar ────────────────────────────────────────────────────────── */
.sel-bar{{
  display:flex;
  align-items:center;
  gap:.75rem;
  margin-bottom:1.25rem;
  padding:.6rem .9rem;
  background:var(--surf);
  border:1px solid var(--border);
  border-radius:var(--r);
}}
.sel-bar label{{font-size:.72rem;color:var(--muted2);font-weight:600;letter-spacing:.05em;text-transform:uppercase}}
.dev-sel{{
  flex:1;
  background:var(--surf2);
  border:1px solid var(--border2);
  color:var(--text);
  border-radius:var(--r);
  padding:.3rem .6rem;
  font-size:.8rem;
  font-family:var(--mono);
}}
.dev-cnt{{font-size:.72rem;color:var(--muted2);margin-left:auto;font-family:var(--mono)}}

/* ── device panel ────────────────────────────────────────────────────────── */
.device-panel{{margin-bottom:2rem}}

.dev-hdr{{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  padding:.9rem 1rem;
  background:var(--surf);
  border:1px solid var(--border);
  border-radius:var(--r) var(--r) 0 0;
  border-bottom:none;
}}
.dev-meta{{display:flex;flex-direction:column;gap:.3rem}}
.dev-title{{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}}
.dev-ip{{font-family:var(--mono);font-size:.9rem;font-weight:600;color:var(--accent)}}
.dev-sep{{color:var(--muted)}}
.dev-vendor{{font-family:var(--mono);font-size:.75rem;color:var(--muted2);font-weight:600}}
.dev-model{{font-family:var(--mono);font-size:.75rem;color:var(--muted2)}}
.dev-hn{{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}}
.dev-hn .mono{{font-size:.75rem;color:var(--muted2)}}
.ver-badge{{
  display:inline-flex;
  align-items:center;
  gap:.3rem;
  font-family:var(--mono);
  font-size:.68rem;
  padding:.15rem .5rem;
  background:var(--surf2);
  border:1px solid var(--border2);
  border-radius:20px;
}}

/* ── phase cards ─────────────────────────────────────────────────────────── */
.ph-cards{{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:0;
  border:1px solid var(--border);
  border-top:none;
  border-bottom:none;
}}
.ph-card{{
  padding:.65rem .85rem;
  background:var(--surf2);
  border-right:1px solid var(--border);
}}
.ph-card:last-child{{border-right:none}}
.ph-card-inactive{{
  opacity:.45;
}}
.ph-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:.4rem}}
.ph-lbl{{font-size:.68rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
.prog{{height:3px;background:var(--border2);border-radius:2px;overflow:hidden}}
.progbar{{height:100%;border-radius:2px;transition:width .4s ease}}

/* ── main table ──────────────────────────────────────────────────────────── */
.tbl-wrap{{
  border:1px solid var(--border);
  border-radius:0 0 var(--r) var(--r);
  overflow:hidden;
  overflow-x:auto;
}}
.main-tbl{{
  width:100%;
  border-collapse:collapse;
  font-size:.78rem;
}}
.main-tbl thead tr{{background:var(--surf3)}}
.main-tbl th{{
  padding:.55rem .75rem;
  text-align:left;
  font-size:.65rem;
  font-weight:700;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:var(--muted2);
  border-bottom:1px solid var(--border2);
  white-space:nowrap;
}}
.th-phase{{width:90px}}
.th-task{{min-width:220px}}
.th-status{{width:90px}}
.th-remark{{min-width:160px}}

.task-row{{border-bottom:1px solid var(--border)}}
.task-row:last-child{{border-bottom:none}}
.task-row:hover{{background:rgba(255,255,255,.018)}}
.task-row td{{padding:.5rem .75rem;vertical-align:middle}}
.failed-row{{background:rgba(244,63,94,.04)}}
.failed-row:hover{{background:rgba(244,63,94,.07)}}

.phase-cell{{
  vertical-align:middle;
  text-align:center;
  padding:.4rem .5rem;
  white-space:nowrap;
  background:var(--surf2);
}}
.phase-lbl{{
  writing-mode:vertical-rl;
  text-orientation:mixed;
  transform:rotate(180deg);
  font-size:.6rem;
  font-weight:700;
  letter-spacing:.08em;
  text-transform:uppercase;
  display:inline-block;
}}
.phase-sep td{{
  padding:0;
  height:4px;
  background:var(--border2);
}}

.subtask-cell{{padding:.5rem .75rem;vertical-align:middle}}
.status-cell{{padding:.5rem .75rem;vertical-align:middle;white-space:nowrap}}
.remark-cell{{
  padding:.5rem .75rem;
  vertical-align:middle;
  font-size:.72rem;
  color:var(--muted2);
  line-height:1.5;
}}
.mono{{font-family:var(--mono);font-size:.72rem}}

/* ── badges ──────────────────────────────────────────────────────────────── */
.badge{{
  display:inline-flex;
  align-items:center;
  padding:.18rem .5rem;
  border-radius:4px;
  font-size:.62rem;
  font-weight:700;
  letter-spacing:.04em;
  white-space:nowrap;
  font-family:var(--mono);
}}
.b-ok{{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.25)}}
.b-fail{{background:rgba(244,63,94,.15);color:#fb7185;border:1px solid rgba(244,63,94,.25)}}
.b-warn{{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.25)}}
.b-ip{{background:rgba(56,189,248,.15);color:#7dd3fc;border:1px solid rgba(56,189,248,.25)}}
.b-ns{{background:var(--surf3);color:var(--muted2);border:1px solid var(--border2)}}

/* ── remark helpers ──────────────────────────────────────────────────────── */
.remark-ok{{color:#4ade80;font-family:var(--mono);font-size:.7rem}}
.remark-err{{color:#fb7185;font-family:var(--mono);font-size:.7rem;word-break:break-all}}
.remark-na{{color:var(--muted);font-family:var(--mono);font-size:.7rem}}

/* ── mini buttons ────────────────────────────────────────────────────────── */
.mini-btn{{
  display:inline-flex;
  align-items:center;
  padding:.18rem .45rem;
  border-radius:4px;
  font-size:.6rem;
  font-weight:600;
  font-family:var(--mono);
  cursor:pointer;
  border:1px solid rgba(56,189,248,.35);
  background:rgba(56,189,248,.08);
  color:#7dd3fc;
  transition:background .15s,color .15s,border-color .15s;
  margin-left:.25rem;
  white-space:nowrap;
}}
.mini-btn:hover{{background:rgba(56,189,248,.18);color:#e0f2fe;border-color:rgba(56,189,248,.6)}}
.mini-err{{border-color:rgba(244,63,94,.35);color:#fb7185;background:rgba(244,63,94,.06)}}
.mini-err:hover{{background:rgba(244,63,94,.14);border-color:#fb7185;color:#fca5a5}}

/* ── log/output boxes ────────────────────────────────────────────────────── */
.log-box{{
  margin:.5rem 0 .25rem;
  background:#080a0e;
  border:1px solid var(--border2);
  border-radius:var(--r);
  overflow:auto;
  max-height:340px;
}}
.log-box pre{{
  padding:.75rem 1rem;
  font-family:var(--mono);
  font-size:.65rem;
  line-height:1.65;
  color:#c8d3e6;
  white-space:pre-wrap;
  word-break:break-all;
}}
.err-box{{border-color:rgba(244,63,94,.3)}}
.err-box pre{{color:#fb7185}}

/* ── command drawer ──────────────────────────────────────────────────────── */
.cmd-drawer{{
  margin:.5rem 0;
  background:var(--surf2);
  border:1px solid var(--border2);
  border-radius:var(--r);
}}
.cmd-list{{padding:.5rem}}
.cmd-empty{{
  padding:.75rem 1rem;
  font-family:var(--mono);
  font-size:.68rem;
  color:var(--muted2);
}}
.cmd-row{{
  padding:.5rem .65rem;
  border-radius:4px;
  margin-bottom:.35rem;
  border:1px solid var(--border);
}}
.cmd-row.ok{{border-color:rgba(34,197,94,.15)}}
.cmd-row.fail{{border-color:rgba(244,63,94,.2)}}
.cm-hd{{
  display:flex;
  align-items:center;
  gap:.5rem;
  flex-wrap:wrap;
}}
.dot{{
  width:7px;height:7px;
  border-radius:50%;
  flex-shrink:0;
}}
.dot-ok{{background:var(--ok)}}
.dot-fail{{background:var(--err)}}
.cm-cmd{{
  font-family:var(--mono);
  font-size:.68rem;
  color:var(--accent);
  flex:1;
  min-width:0;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}}
.cm-btns{{display:flex;gap:.2rem;flex-shrink:0}}

/* ── overlay drawers (images / checksums) ────────────────────────────────── */
.drawer-slot{{
  position:relative;
  display:inline-block;
  vertical-align:top;
  margin-left:.4rem;
}}
.cmd-drawer.overlay{{
  position:absolute;
  top:0;
  left:100%;
  margin-left:.6rem;
  width:640px;
  max-width:70vw;
  background:var(--surf2);
  border:1px solid var(--border2);
  border-radius:var(--r);
  z-index:20;
  box-shadow:0 10px 25px rgba(0,0,0,.45);
}}

/* ── hops table ──────────────────────────────────────────────────────────── */
.hops-slot{{
  position:relative;
  display:inline-block;
  vertical-align:top;
  margin-left:.4rem;
}}
.hops-inline{{
  position:absolute;
  top:0;
  left:100%;
  margin-left:.6rem;
  width:700px;
  max-width:75vw;
  background:var(--surf2);
  border:1px solid var(--border2);
  border-radius:var(--r);
  z-index:20;
  box-shadow:0 10px 25px rgba(0,0,0,.45);
  overflow:hidden;
}}
.hop-table-wrap{{overflow-x:auto}}
.hop-table{{
  width:100%;
  border-collapse:collapse;
  font-size:.7rem;
}}
.hop-table th{{
  background:var(--surf3);
  padding:.4rem .65rem;
  text-align:left;
  font-size:.62rem;
  font-weight:700;
  letter-spacing:.05em;
  text-transform:uppercase;
  color:var(--muted2);
  border-bottom:1px solid var(--border2);
  white-space:nowrap;
}}
.hop-table td{{
  padding:.45rem .65rem;
  border-bottom:1px solid var(--border);
  vertical-align:middle;
}}
.hop-table tr:last-child td{{border-bottom:none}}
.hop-table tr:hover td{{background:rgba(255,255,255,.015)}}
.hop-table.nested{{margin:.3rem 0;background:var(--surf)}}
.hop-num-cell{{width:32px;color:var(--muted2);font-family:var(--mono);font-size:.65rem;text-align:center}}
.hop-image-cell{{font-family:var(--mono);font-size:.65rem;word-break:break-all;min-width:160px}}
.hop-status-cell{{width:80px;white-space:nowrap}}
.hop-remark-cell{{font-size:.65rem;color:var(--muted2);min-width:140px;word-break:break-all}}
.failed-row td{{background:rgba(244,63,94,.04)}}

/* ── RE chips (dual-RE) ──────────────────────────────────────────────────── */
.re-chips{{
  display:flex;
  gap:.3rem;
  flex-wrap:wrap;
  margin-top:.3rem;
}}
.re-chip{{
  display:inline-flex;
  align-items:center;
  gap:.25rem;
  padding:.12rem .4rem;
  border-radius:4px;
  font-family:var(--mono);
  font-size:.6rem;
  font-weight:600;
  border:1px solid transparent;
}}
.re-ok{{background:rgba(34,197,94,.12);color:#4ade80;border-color:rgba(34,197,94,.2)}}
.re-fail{{background:rgba(244,63,94,.12);color:#fb7185;border-color:rgba(244,63,94,.2)}}
.re-ns{{background:var(--surf3);color:var(--muted);border-color:var(--border2)}}
.re-ver{{font-weight:400;opacity:.8}}
.re-arrow{{
  color:var(--muted2);
  font-size:.55rem;
  margin:0 .1rem;
}}

/* ── switchover arrow chips ──────────────────────────────────────────────── */
.sw-row{{
  display:flex;
  align-items:center;
  gap:.35rem;
  margin-top:.3rem;
  flex-wrap:wrap;
}}
.sw-chip{{
  display:inline-flex;
  align-items:center;
  gap:.2rem;
  padding:.1rem .4rem;
  border-radius:4px;
  font-family:var(--mono);
  font-size:.58rem;
  font-weight:600;
  background:rgba(167,139,250,.1);
  color:#c4b5fd;
  border:1px solid rgba(167,139,250,.25);
  letter-spacing:.02em;
}}

/* ── diff section ────────────────────────────────────────────────────────── */
.diff-section{{margin-top:1rem}}
.diff-block{{
  margin-bottom:1rem;
  border:1px solid var(--border2);
  border-radius:var(--r);
  overflow:hidden;
}}
.diff-block-hdr{{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:.55rem .85rem;
  background:var(--surf3);
  border-bottom:1px solid var(--border2);
}}
.diff-block-cmd{{flex:1;min-width:0}}
.diff-block-cmdname{{
  font-family:var(--mono);
  font-size:.72rem;
  color:var(--accent);
}}
.diff-grid{{
  display:grid;
  grid-template-columns:1fr 1fr;
  grid-template-rows:auto 1fr;
}}
.diff-col-hdr{{
  padding:.4rem .75rem;
  background:var(--surf2);
  font-size:.62rem;
  font-weight:700;
  letter-spacing:.05em;
  text-transform:uppercase;
  color:var(--muted2);
  border-bottom:1px solid var(--border);
}}
.diff-col-hdr:first-of-type{{border-right:1px solid var(--border)}}
.diff-pane{{
  overflow:auto;
  max-height:420px;
  background:#080a0e;
}}
.diff-pane:first-of-type{{border-right:1px solid var(--border)}}
.diff-pane pre{{
  padding:.75rem 1rem;
  font-family:var(--mono);
  font-size:.63rem;
  line-height:1.7;
  white-space:pre-wrap;
  word-break:break-all;
}}
.diff-none{{
  padding:.6rem .75rem;
  font-size:.72rem;
  color:var(--muted2);
  font-family:var(--mono);
  font-style:italic;
}}

/* diff highlight tokens */
.diff-eq{{color:#8896aa}}
.diff-line-del{{color:#fca5a5;display:block;background:rgba(244,63,94,.08)}}
.diff-line-ins{{color:#86efac;display:block;background:rgba(34,197,94,.08)}}
.diff-na{{color:var(--muted);display:block;font-style:italic}}
mark.diff-del{{background:rgba(244,63,94,.3);color:#fca5a5;border-radius:2px;padding:0 1px}}
mark.diff-ins{{background:rgba(34,197,94,.3);color:#86efac;border-radius:2px;padding:0 1px}}

/* ── raw JSON section ────────────────────────────────────────────────────── */
.json-sec{{
  margin-top:2rem;
  border:1px solid var(--border);
  border-radius:var(--r);
  overflow:hidden;
}}
.json-sec summary{{
  padding:.65rem 1rem;
  background:var(--surf);
  cursor:pointer;
  font-size:.75rem;
  font-weight:600;
  color:var(--muted2);
  user-select:none;
}}
.json-sec summary:hover{{color:var(--text)}}
.jb{{
  padding:1rem;
  background:#080a0e;
  font-family:var(--mono);
  font-size:.62rem;
  line-height:1.65;
  color:#8896aa;
  overflow:auto;
  max-height:480px;
  white-space:pre;
}}

/* ── footer ──────────────────────────────────────────────────────────────── */
.ft{{
  margin-top:3rem;
  padding-top:1rem;
  border-top:1px solid var(--border);
  font-size:.68rem;
  color:var(--muted);
  font-family:var(--mono);
  text-align:center;
}}
</style>
</head>

<body>
<div class="wrap">

<header class="hdr">
  <div>
    <h1>Network Device <span>Workflow Report</span></h1>
    <p class="sub">Generated: {now} &nbsp;·&nbsp; {len(device_keys)} device(s)</p>
  </div>
  <span class="pill {pill_cls}">{_esc(pill_txt)}</span>
</header>

<div class="sel-bar">
  <label for="dev-sel">Device</label>
  <select id="dev-sel" class="dev-sel" onchange="selectDevice(this.value)">
    {dropdown_opts}
  </select>
  <span class="dev-cnt">{len(device_keys)} device(s)</span>
</div>

{device_panels}

<details class="json-sec">
  <summary>&#9658; Raw JSON (all devices)</summary>
  <pre class="jb">{json_html}</pre>
</details>

<footer class="ft">
  workflow_report_generator.py &nbsp;·&nbsp; {now}
</footer>
</div>

<script>
var DI = {di_json};

function updateInfo(key) {{
  var d = DI[key];
  if (!d) return;
  var set = function(id, v) {{
    var el = document.getElementById(id);
    if (el) el.textContent = v || '—';
  }};
  set('di-host-'         + key, d.host);
  set('di-vendor-'       + key, d.vendor);
  set('di-model-'        + key, d.model);
  set('di-hostname-'     + key, d.hostname);
  set('di-pre-version-'  + key, d.pre_version);
  set('di-post-version-' + key, d.post_version);
}}

function selectDevice(key) {{
  document.querySelectorAll('.device-panel').forEach(function(p) {{
    p.style.display = 'none';
  }});
  var p = document.getElementById('panel-' + key);
  if (p) p.style.display = 'block';
  updateInfo(key);
}}

function tgl(id) {{
  var el = document.getElementById(id);
  if (el) el.hidden = !el.hidden;
}}

function tglHops(id) {{
  var el = document.getElementById(id);
  if (el) el.hidden = !el.hidden;
}}

function tglDiff(id) {{
  var el = document.getElementById(id);
  if (!el) return;
  el.hidden = !el.hidden;
  if (!el.hidden) {{
    el.scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
  }}
}}

document.addEventListener('DOMContentLoaded', function() {{
  updateInfo('{first_key}');
}});
</script>
</body>
</html>
"""

    os.makedirs(output_dir, exist_ok=True)
    import glob
    for old in glob.glob(os.path.join(output_dir, "workflow_report_*.html")):
        os.remove(old)

    filename  = f"{stem}.html" if stem else f"workflow_report_{ts_file}.html"
    file_path = os.path.join(output_dir, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    return file_path


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: workflow_report_generator.py <input.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    single_device_keys = {"pre", "post", "upgrade", "diff", "device_info", "status", "conn", "yaml"}
    if set(data.keys()) <= single_device_keys | {"conn", "yaml"}:
        stem_key = input_path.stem
        workflow_data = {stem_key: data}
    else:
        workflow_data = data

    output_dir = str(input_path.parent)
    stem       = input_path.stem + "_report"

    out_path = generate_html_report(workflow_data, output_dir=output_dir, stem=stem)
    print(f"Report generated: {out_path}")