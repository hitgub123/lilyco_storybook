import sys

if len(sys.argv) < 2:
    print("Usage: python inspect_events.py <path-to-event-file-or-dir>")
    sys.exit(1)

path = sys.argv[1]

# Try tensorboard EventAccumulator first
try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    ea = EventAccumulator(path, size_guidance={"scalars": 0})
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    print("Found scalar tags:", tags)
    for tag in tags:
        events = ea.Scalars(tag)
        print(f"\nTag: {tag}  (total events: {len(events)})")
        head = events[:5]
        tail = events[-5:]
        print("  first:")
        for e in head:
            print(f"    step={e.step} time={e.wall_time:.3f} value={e.value}")
        print("  last:")
        for e in tail:
            print(f"    step={e.step} time={e.wall_time:.3f} value={e.value}")
except Exception as ex:
    print("EventAccumulator import failed or could not read with it:", ex)
    print("Falling back to tensorflow summary_iterator if available...")
    try:
        try:
            # TensorFlow 2.x compatibility
            from tensorflow.compat.v1.train import summary_iterator
        except Exception:
            from tensorflow.python.summary.summary_iterator import summary_iterator
        tag_vals = {}
        for e in summary_iterator(path):
            for v in e.summary.value:
                tag = v.tag
                if hasattr(v, "simple_value"):
                    val = v.simple_value
                elif v.tensor:
                    # attempt to parse tensor proto for single-value
                    try:
                        import numpy as _np
                        from tensorflow.python.framework import tensor_util

                        val = float(tensor_util.MakeNdarray(v.tensor))
                    except Exception:
                        continue
                else:
                    continue
                tag_vals.setdefault(tag, []).append((e.step, e.wall_time, val))
        if not tag_vals:
            print("No scalar values found by summary_iterator.")
        else:
            print("Found scalar tags:", list(tag_vals.keys()))
            for tag, evs in tag_vals.items():
                print(f"\nTag: {tag} (total events: {len(evs)})")
                for s, t, v in evs[:5]:
                    print(f"    first: step={s} time={t:.3f} value={v}")
                for s, t, v in evs[-5:]:
                    print(f"    last: step={s} time={t:.3f} value={v}")
    except Exception as ex2:
        print("Fallback also failed:", ex2)
        sys.exit(2)
