import sys
from pathlib import Path

path = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("runs/dqn_experiment/events.out.tfevents.1764687876.cocoa.47312.0")
)
out = path.parent / "events_summary.txt"
try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    ea = EventAccumulator(str(path), size_guidance={"scalars": 0})
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    with open(out, "w", encoding="utf-8") as f:
        f.write("Found scalar tags: " + str(tags) + "\n")
        for tag in tags:
            events = ea.Scalars(tag)
            f.write(f"\nTag: {tag}  (total events: {len(events)})\n")
            head = events[:5]
            tail = events[-5:]
            f.write("  first:\n")
            for e in head:
                f.write(f"    step={e.step} time={e.wall_time:.3f} value={e.value}\n")
            f.write("  last:\n")
            for e in tail:
                f.write(f"    step={e.step} time={e.wall_time:.3f} value={e.value}\n")
    print("Wrote summary to", out)
except Exception as ex:
    with open(out, "w", encoding="utf-8") as f:
        f.write("EventAccumulator failed: " + str(ex) + "\n")
        f.write("Falling back to summary_iterator\n")
    try:
        try:
            from tensorflow.compat.v1.train import summary_iterator
        except Exception:
            from tensorflow.python.summary.summary_iterator import summary_iterator
        tag_vals = {}
        for e in summary_iterator(str(path)):
            for v in e.summary.value:
                tag = v.tag
                if hasattr(v, "simple_value"):
                    val = v.simple_value
                elif hasattr(v, "tensor") and v.tensor:
                    try:
                        from tensorflow.python.framework import tensor_util

                        val = float(tensor_util.MakeNdarray(v.tensor))
                    except Exception:
                        continue
                else:
                    continue
                tag_vals.setdefault(tag, []).append((e.step, e.wall_time, val))
        with open(out, "a", encoding="utf-8") as f:
            if not tag_vals:
                f.write("No scalar values found by summary_iterator.\n")
            else:
                f.write("Found scalar tags: " + str(list(tag_vals.keys())) + "\n")
                for tag, evs in tag_vals.items():
                    f.write(f"\nTag: {tag} (total events: {len(evs)})\n")
                    for s, t, v in evs[:5]:
                        f.write(f"    first: step={s} time={t:.3f} value={v}\n")
                    for s, t, v in evs[-5:]:
                        f.write(f"    last: step={s} time={t:.3f} value={v}\n")
        print("Wrote summary to", out)
    except Exception as ex2:
        with open(out, "a", encoding="utf-8") as f:
            f.write("Fallback also failed: " + str(ex2) + "\n")
        print("Failed to write summary, see file", out)
