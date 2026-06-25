#!/usr/bin/env python3
"""
find_hairpins.py

Find possible hairpins in a DNA or RNA sequence and optionally visualize them
in an RTF file and/or via a GUI.

Hairpin definition:
- Single sequence (DNA or RNA).
- A hairpin has a stem (>= min_stem bp) and a loop (>= min_loop nt).
- Allowed base pairs: A–T, A–U, G–C (Watson–Crick) and wobble G–T, G–U.
- Stem 2 is antiparallel to stem 1, as in a normal hairpin.
- We enumerate *all* contiguous stems that satisfy the constraints, not just
  maximal stems.

Outputs:
- CLI mode:
    * Prints a list of hairpin dictionaries (JSON) to stdout.
    * Writes an RTF file where each hairpin is one line of the sequence, with
      stem nucleotides red, wobble nucleotides underlined, and hairpins with
      maximal stem length in bold.
- GUI mode (default if no args, or `--gui` is used):
    * Lets you enter sequence and parameters.
    * Displays hairpins in a colored / formatted view similar to the RTF.
    * Optional checkbox controls whether to write an RTF output file.
    * Positions of stem starts and wobble positions can be reported as 0-based
      or 1-based indices (default 1-based).
"""

import json
import sys
from typing import List, Dict, Set


# Watson–Crick + wobble base pairs
BASE_PAIRS = {
    "AT", "TA",
    "AU", "UA",
    "GC", "CG",
    "GT", "TG",
    "GU", "UG",
}

# Wobble-only
WOBBLE_PAIRS = {
    "GT", "TG",
    "GU", "UG",
}


def find_hairpins(seq: str,
                  min_stem: int = 3,
                  min_loop: int = 3,
                  index_base: int = 1) -> List[Dict]:
    """
    Find all hairpins in a DNA/RNA sequence.

    Hairpin is defined by:
    - stem1: positions i .. i+L-1
    - stem2: positions j-L+1 .. j
    - with L >= min_stem and loop_len >= min_loop
    - for all k in 0..L-1, (i+k, j-k) must be an allowed base pair.

    Positions in returned dictionaries are reported using `index_base`
    (0-based or 1-based; default 1-based).
    """
    if index_base not in (0, 1):
        raise ValueError("index_base must be 0 or 1")

    seq = seq.upper()
    n = len(seq)
    if n == 0:
        return []

    # Precompute which positions can pair (including wobble)
    pair = [[False] * n for _ in range(n)]
    wobble = [[False] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            code = seq[i] + seq[j]
            if code in BASE_PAIRS:
                pair[i][j] = True
                if code in WOBBLE_PAIRS:
                    wobble[i][j] = True

    hairpins: List[Dict] = []

    # Enumerate outer base pairs (i, j) that are far enough apart
    # to support *some* stem length >= min_stem and loop length >= min_loop.
    for i in range(n):
        # Minimal j such that with stem length = min_stem, loop_len >= min_loop:
        # loop_len = j - i - 2*L + 1 >= min_loop => j >= i + 2*L + min_loop - 1
        j_min = i + 2 * min_stem + min_loop - 1
        if j_min >= n:
            continue

        for j in range(j_min, n):
            if not pair[i][j]:
                continue

            # Compute maximal contiguous stem length (L_max) starting from outer pair (i, j).
            wobble_flags = []
            pair_codes = []
            L = 0
            while True:
                left = i + L
                right = j - L

                # Stop if arms would cross or touch
                if left >= right:
                    break

                if not pair[left][right]:
                    break

                wobble_flags.append(wobble[left][right])
                pair_codes.append(seq[left] + seq[right])
                L += 1

            L_max = L

            if L_max < min_stem:
                continue

            # Now enumerate all possible stem lengths L_sub from min_stem to L_max
            # that still give loop_len >= min_loop.
            for L_sub in range(min_stem, L_max + 1):
                loop_len = j - i - 2 * L_sub + 1
                if loop_len < min_loop:
                    continue

                stem1_start = i
                stem2_start = j - L_sub + 1

                stem1_seq = seq[stem1_start:stem1_start + L_sub]
                stem2_seq = seq[stem2_start:stem2_start + L_sub]

                # Count wobble pairs and collect positions, plus GC and AT/AU pairs
                wobble_pairs = 0
                wobble_positions: Set[int] = set()
                gc_pairs = 0
                at_au_pairs = 0

                for k in range(L_sub):
                    if wobble_flags[k]:
                        wobble_pairs += 1
                        wobble_positions.add(stem1_start + k)
                        wobble_positions.add(stem2_start + (L_sub - 1 - k))

                    code = pair_codes[k]
                    if code in ("GC", "CG"):
                        gc_pairs += 1
                    elif code in ("AT", "TA", "AU", "UA"):
                        at_au_pairs += 1

                hairpins.append(
                    {
                        "stem_length": L_sub,
                        "loop_length": loop_len,
                        "stem1_start": stem1_start + index_base,
                        "stem1_seq": stem1_seq,
                        "stem2_start": stem2_start + index_base,
                        "stem2_seq": stem2_seq,
                        "wobble_pairs": wobble_pairs,
                        "gc_pairs": gc_pairs,
                        "at_au_pairs": at_au_pairs,
                        # Positions of wobble nucleotides reported using index_base
                        "wobble_positions": sorted(
                            pos + index_base for pos in wobble_positions
                        ),
                    }
                )

    return hairpins


def write_hairpins_rtf(seq: str,
                       hairpins: List[Dict],
                       filename: str,
                       index_base: int = 1) -> None:
    """
    Write an RTF file where each hairpin is one line of the sequence, formatted as:

    - Full sequence on its own line (no extra descriptive text).
    - Stem nucleotides are red.
    - Nucleotides in wobble pairs are underlined.
    - Hairpins with maximal stem length are bold.

    `index_base` must match the base used in the hairpin dictionaries
    (0-based or 1-based; default 1-based).
    """
    if index_base not in (0, 1):
        raise ValueError("index_base must be 0 or 1")

    seq = seq.upper()
    n = len(seq)

    with open(filename, "w") as f:
        # Basic RTF header
        f.write(r"{\rtf1\ansi" + "\n")
        # Color table: index 1 = black (default), index 2 = red
        f.write(r"{\colortbl ;\red0\green0\blue0;\red255\green0\blue0;}" + "\n")

        if not hairpins:
            f.write(r"\cf1 No hairpins found for sequence: " + seq + r"\line" + "\n")
            f.write("}")
            return

        max_stem = max(hp["stem_length"] for hp in hairpins)

        for hp in hairpins:
            is_max = hp["stem_length"] == max_stem
            line = ""

            # Always start in black
            line += r"\cf1 "
            if is_max:
                line += r"\b "

            current_color = "black"
            underline = False

            # Convert to 0-based indices
            s1_start0 = hp["stem1_start"] - index_base
            s2_start0 = hp["stem2_start"] - index_base
            stem_len = hp["stem_length"]

            # Positions that belong to the stem
            stem_positions = set(range(s1_start0, s1_start0 + stem_len)) | set(
                range(s2_start0, s2_start0 + stem_len)
            )

            wobble_positions_list = hp.get("wobble_positions", [])
            if index_base == 1:
                wobble_positions0 = {p - 1 for p in wobble_positions_list}
            else:
                wobble_positions0 = set(wobble_positions_list)

            for pos in range(n):
                base = seq[pos]

                is_stem = pos in stem_positions
                is_wobble = pos in wobble_positions0

                # Switch color when entering/leaving stem
                if is_stem and current_color != "red":
                    line += r"\cf2 "
                    current_color = "red"
                elif not is_stem and current_color != "black":
                    line += r"\cf1 "
                    current_color = "black"

                # Toggle underline for wobble positions
                if is_wobble and not underline:
                    line += r"\ul "
                    underline = True
                elif not is_wobble and underline:
                    line += r"\ulnone "
                    underline = False

                line += base

            # Make sure underline is off at end of line
            if underline:
                line += r"\ulnone "

            # Turn off bold if this was a max-stem hairpin
            if is_max:
                line += r"\b0 "

            # End the line (sequence only on this line)
            line += r"\line"
            f.write(line + "\n")

        # End of RTF document
        f.write("}")


# ------------------------ GUI MODE ------------------------ #

def gui_main() -> None:
    """
    Launch a simple Tkinter GUI for hairpin finding.

    - Sequence input (multiline).
    - min_stem and min_loop inputs (default values).
    - Output RTF filename entry with a checkbox to enable/disable writing.
    - Radio buttons to choose 0-based or 1-based indexing for positions.
    - Results shown in a text box with color / formatting similar to the RTF.
    """
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    root = tk.Tk()
    root.title("Hairpin Finder")

    # ---------- Layout containers ----------
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    # Input frame
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(fill="x", expand=False)

    # Sequence label + text
    seq_label = ttk.Label(input_frame, text="Sequence:")
    seq_label.grid(row=0, column=0, sticky="w")

    seq_text = tk.Text(input_frame, height=4, width=60, wrap="word")
    seq_text.grid(row=1, column=0, columnspan=4, sticky="we", pady=(2, 6))

    # Parameters: min_stem, min_loop, output filename, checkbox, index base
    min_stem_var = tk.StringVar(value="3")
    min_loop_var = tk.StringVar(value="3")
    out_name_var = tk.StringVar(value="hairpins_output.rtf")
    write_rtf_var = tk.BooleanVar(value=True)
    index_base_var = tk.IntVar(value=1)

    ttk.Label(input_frame, text="Min stem length:").grid(row=2, column=0, sticky="e")
    min_stem_entry = ttk.Entry(input_frame, textvariable=min_stem_var, width=6)
    min_stem_entry.grid(row=2, column=1, sticky="w", padx=(4, 12))

    ttk.Label(input_frame, text="Min loop length:").grid(row=2, column=2, sticky="e")
    min_loop_entry = ttk.Entry(input_frame, textvariable=min_loop_var, width=6)
    min_loop_entry.grid(row=2, column=3, sticky="w", padx=(4, 0))

    ttk.Label(input_frame, text="Output RTF filename:").grid(
        row=3, column=0, sticky="e", pady=(4, 0)
    )
    out_name_entry = ttk.Entry(input_frame, textvariable=out_name_var, width=30)
    out_name_entry.grid(
        row=3, column=1, columnspan=3, sticky="w", padx=(4, 0), pady=(4, 0)
    )

    # Index base selection
    index_label = ttk.Label(input_frame, text="Index positions as:")
    index_label.grid(row=4, column=0, sticky="e", pady=(4, 0))

    index_1_radio = ttk.Radiobutton(
        input_frame, text="1-based", variable=index_base_var, value=1
    )
    index_1_radio.grid(row=4, column=1, sticky="w", padx=(4, 0), pady=(4, 0))

    index_0_radio = ttk.Radiobutton(
        input_frame, text="0-based", variable=index_base_var, value=0
    )
    index_0_radio.grid(row=4, column=2, sticky="w", padx=(4, 0), pady=(4, 0))

    write_rtf_check = ttk.Checkbutton(
        input_frame,
        text="Write RTF file",
        variable=write_rtf_var,
        onvalue=True,
        offvalue=False,
    )
    write_rtf_check.grid(row=5, column=0, columnspan=4, sticky="w", pady=(4, 0))

    # Run button
    run_button = ttk.Button(input_frame, text="Find hairpins")
    run_button.grid(row=6, column=0, columnspan=4, pady=(8, 4))

    # Results frame
    results_frame = ttk.Frame(main_frame)
    results_frame.pack(fill="both", expand=True, pady=(8, 0))

    ttk.Label(results_frame, text="Results:").pack(anchor="w")

    results_text = tk.Text(results_frame, height=15, wrap="none")
    results_text.pack(side="left", fill="both", expand=True)

    scroll_y = ttk.Scrollbar(results_frame, orient="vertical", command=results_text.yview)
    scroll_y.pack(side="right", fill="y")
    results_text.configure(yscrollcommand=scroll_y.set)

    # Configure tags for coloring and formatting
    results_text.tag_configure("stem", foreground="red")
    results_text.tag_configure("wobble", underline=1)
    results_text.tag_configure("maxstem", font=("TkDefaultFont", 10, "bold"))

    def render_results(seq: str, hairpins: List[Dict], index_base: int) -> None:
        """Render RTF-style colored results into the Text widget."""
        results_text.delete("1.0", "end")

        if not hairpins:
            results_text.insert("1.0", "No hairpins found with these parameters.\n")
            return

        seq = seq.upper()
        n = len(seq)
        max_stem = max(hp["stem_length"] for hp in hairpins)

        first_line = True
        for hp in hairpins:
            if not first_line:
                results_text.insert("end", "\n")
            first_line = False

            is_max = hp["stem_length"] == max_stem

            s1_start0 = hp["stem1_start"] - index_base
            s2_start0 = hp["stem2_start"] - index_base
            stem_len = hp["stem_length"]

            stem_positions = set(range(s1_start0, s1_start0 + stem_len)) | set(
                range(s2_start0, s2_start0 + stem_len)
            )

            wobble_positions_list = hp.get("wobble_positions", [])
            if index_base == 1:
                wobble_positions0 = {p - 1 for p in wobble_positions_list}
            else:
                wobble_positions0 = set(wobble_positions_list)

            for pos in range(n):
                base = seq[pos]
                is_stem = pos in stem_positions
                is_wobble = pos in wobble_positions0

                tags = []
                if is_stem:
                    tags.append("stem")
                if is_wobble:
                    tags.append("wobble")
                if is_max:
                    tags.append("maxstem")

                results_text.insert("end", base, tuple(tags))

    def on_run():
        # Get sequence (strip whitespace/newlines)
        raw_seq = seq_text.get("1.0", "end").strip().upper()
        seq = "".join(ch for ch in raw_seq if not ch.isspace())

        if not seq:
            messagebox.showerror("Input error", "Please enter a sequence.")
            return

        # Get numeric parameters
        try:
            min_stem = int(min_stem_var.get())
            min_loop = int(min_loop_var.get())
            if min_stem <= 0 or min_loop <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Input error",
                "Min stem and min loop must be positive integers."
            )
            return

        index_base = index_base_var.get()
        if index_base not in (0, 1):
            messagebox.showerror(
                "Input error",
                "Index base must be 0 or 1."
            )
            return

        # Run hairpin search
        hairpins = find_hairpins(seq, min_stem=min_stem, min_loop=min_loop,
                                 index_base=index_base)

        # Render results in the GUI
        render_results(seq, hairpins, index_base=index_base)

        if not hairpins:
            messagebox.showinfo("No hairpins", "No hairpins found with these parameters.")
            return

        # Optionally write RTF
        if write_rtf_var.get():
            default_out = out_name_var.get().strip() or "hairpins_output.rtf"
            out_name_var.set(default_out)

            filename = filedialog.asksaveasfilename(
                title="Save RTF file",
                initialfile=default_out,
                defaultextension=".rtf",
                filetypes=[("RTF files", "*.rtf"), ("All files", "*.*")]
            )
            if filename:
                try:
                    write_hairpins_rtf(seq, hairpins, filename, index_base=index_base)
                    messagebox.showinfo(
                        "Saved",
                        f"Wrote {len(hairpins)} hairpins to:\n{filename}"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error saving RTF",
                        f"An error occurred while writing the RTF file:\n{e}"
                    )

    run_button.configure(command=on_run)

    root.mainloop()


# ------------------------ CLI MODE ------------------------ #

def cli_main(args: List[str]) -> None:
    """
    Command-line interface:

    Usage:
        python find_hairpins.py SEQUENCE [OUTPUT_RTF] [MIN_STEM] [MIN_LOOP] [INDEX_BASE]

    INDEX_BASE: 0 for 0-based positions, 1 for 1-based positions (default 1).
    """
    if not args or "-h" in args or "--help" in args:
        print("Usage: python find_hairpins.py SEQUENCE [OUTPUT_RTF] [MIN_STEM] [MIN_LOOP] [INDEX_BASE]")
        print("       python find_hairpins.py --gui")
        print("If no arguments or --gui is given, a GUI will be launched.")
        print("INDEX_BASE: 0 for 0-based positions, 1 for 1-based positions (default 1).")
        return

    seq = args[0].strip()
    out_rtf = args[1] if len(args) >= 2 else "hairpins_output.rtf"
    min_stem = int(args[2]) if len(args) >= 3 else 3
    min_loop = int(args[3]) if len(args) >= 4 else 3
    index_base = 1
    if len(args) >= 5:
        try:
            index_base = int(args[4])
            if index_base not in (0, 1):
                raise ValueError
        except ValueError:
            print("Warning: INDEX_BASE must be 0 or 1; defaulting to 1.", file=sys.stderr)
            index_base = 1

    hairpins = find_hairpins(seq, min_stem=min_stem, min_loop=min_loop,
                             index_base=index_base)

    # Print hairpin list as JSON to stdout
    print(json.dumps(hairpins, indent=2))

    # Write the RTF visualization
    write_hairpins_rtf(seq, hairpins, out_rtf, index_base=index_base)
    print(f"Wrote {len(hairpins)} hairpins to {out_rtf}")


def main():
    args = sys.argv[1:]

    # GUI mode if no args or explicit --gui
    if not args or "--gui" in args:
        gui_main()
        return

    cli_main(args)


if __name__ == "__main__":
    main()
