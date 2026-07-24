"""Write an agent-resolution response.

Usage:
  python respond.py <seq> '<json-mapping>'
Example (map the label "Rename" to the live UIA name "Rename (F2)", and mark
"budget.xlsx" absent):
  python respond.py 1 "{\"Rename\": \"Rename (F2)\", \"budget.xlsx\": null}"

The mapping keys are the model's expected labels; values are the exact live UIA
element NAME to use (or null if the label is not on screen yet). The resolver
prefers an element inside the model's search region (x<960) when several share
a name, and persists your non-null choices to <task>.map.json for future runs.
"""
import os, sys, json

RES = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent_resolution"))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    seq = int(sys.argv[1])
    mapping = json.loads(sys.argv[2])
    out = os.path.join(RES, "response_%d.json" % seq)
    json.dump({"seq": seq, "mapping": mapping}, open(out, "w", encoding="utf-8"))
    print("WROTE", out, "->", {"seq": seq, "mapping": mapping})


if __name__ == "__main__":
    main()
