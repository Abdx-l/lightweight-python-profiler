"""Call-stack timing profiler and SVG flame renderer."""
import argparse
import html
import runpy
import sys
import time
from collections import defaultdict
from pathlib import Path


class Profiler:
    def __init__(self, clock=time.perf_counter_ns):
        self.clock = clock
        self.stacks = defaultdict(int)
        self.frames = []

    def callback(self, frame, event, arg):
        if event == "call":
            self.frames.append((frame, self.clock(), frame.f_code.co_name))
        elif event == "return" and self.frames:
            top, start, name = self.frames[-1]
            if top is frame:
                elapsed = max(0, self.clock() - start)
                self.stacks[";".join(item[2] for item in self.frames)] += elapsed
                self.frames.pop()

    def run(self, function, *args, **kwargs):
        previous = sys.getprofile()
        sys.setprofile(self.callback)
        try:
            return function(*args, **kwargs)
        finally:
            sys.setprofile(previous)
            self.frames.clear()


def folded(stacks):
    return "\n".join(f"{name} {value}" for name, value in sorted(stacks.items())) + "\n"


def svg(stacks):
    # Leaf timings may overlap their ancestors. Layout each depth by call path.
    totals = defaultdict(int)
    for path, duration in stacks.items():
        parts = path.split(";")
        for depth in range(1, len(parts) + 1):
            totals[tuple(parts[:depth])] += duration if depth == len(parts) else 0
    for path in sorted(totals, key=len, reverse=True):
        if len(path) > 1:
            totals[path[:-1]] += totals[path]
    roots = sorted((p for p in totals if len(p) == 1), key=str)
    total = sum(totals[p] for p in roots) or 1
    height = (max(map(len, totals), default=1) + 1) * 28
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">', '<rect width="100%" height="100%" fill="#111827"/>']

    def draw(path, x, width):
        depth = len(path) - 1
        label = html.escape(path[-1], quote=True)
        duration = totals[path]
        color = ["#f59e0b", "#38bdf8", "#34d399", "#a78bfa"][depth % 4]
        chunks.append(f'<g><title>{label}: {duration} ns</title><rect x="{x:.2f}" y="{depth * 28 + 4}" width="{max(0,width-1):.2f}" height="24" fill="{color}"/><text x="{x+4:.2f}" y="{depth * 28 + 20}" font-size="12" font-family="sans-serif">{label[:30]}</text></g>')
        offset = x
        for child in sorted((p for p in totals if len(p) == len(path)+1 and p[:-1] == path), key=str):
            share = width * totals[child] / duration if duration else 0
            draw(child, offset, share)
            offset += share

    x = 0.0
    for root in roots:
        width = 1000 * totals[root] / total
        draw(root, x, width)
        x += width
    chunks.append("</svg>")
    return "\n".join(chunks) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("script")
    p.add_argument("--folded", default="trace.folded")
    p.add_argument("--svg", default="flame.svg")
    a = p.parse_args()
    profiler = Profiler()
    profiler.run(runpy.run_path, a.script, run_name="__main__")
    Path(a.folded).write_text(folded(profiler.stacks), encoding="utf-8")
    Path(a.svg).write_text(svg(profiler.stacks), encoding="utf-8")
    print(f"Wrote {len(profiler.stacks)} call stacks")


if __name__ == "__main__":
    main()

