"""Show the next UNANSWERED agent-resolution request (if any).

Usage:  python show_pending.py
Prints the request seq, the labels the model needs resolved, and the candidate
UIA elements (name | control_type | x,y), unicode-safe. You (the agent) then
call respond.py with your chosen mapping.
"""
import os, json, glob, sys

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent_resolution")
RES = os.path.abspath(RES)


def _asc(s):
    return str(s).encode("ascii", "replace").decode()


def main():
    reqs = sorted(glob.glob(os.path.join(RES, "request_*.json")),
                  key=lambda p: int(os.path.basename(p).split("_")[1].split(".")[0]))
    pending = [p for p in reqs
               if not os.path.isfile(os.path.join(RES, "response_%s.json" %
                                                   os.path.basename(p).split("_")[1].split(".")[0]))]
    if not pending:
        print("NO PENDING REQUEST")
        return
    p = pending[0]
    r = json.load(open(p, encoding="utf-8"))
    print("PENDING REQUEST seq=%s task=%s" % (r["seq"], r["task"]))
    print("labels to resolve:", r["unresolved_labels"])
    print("already resolved:", r.get("already_resolved"))
    print("--- candidate UIA elements (in the model's left region x<960 are usable) ---")
    labs = [l.lower() for l in r["unresolved_labels"]]
    for e in r["uia_elements"]:
        nm = (e.get("name") or "")
        if not nm.strip() or len(nm) > 60:
            continue
        toks = set("".join(c if c.isalnum() else " " for c in nm.lower()).split())
        rel = any(any(t in nm.lower() for t in lab.split()) or (set(lab.split()) & toks) for lab in labs)
        x = e.get("x")
        region = "  <-usable" if isinstance(x, (int, float)) and x < 960 else ""
        if rel:
            print("   %-38s | %-12s | (%s,%s)%s" % (_asc(nm)[:38], _asc(e.get("control_type")), x, e.get("y"), region))


if __name__ == "__main__":
    main()
