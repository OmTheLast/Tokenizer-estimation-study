"""Paired, descriptive tokenizer comparisons from frozen numeric measurements."""
import argparse
import hashlib
import json
import math
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pyarrow
import pyarrow.parquet as pq


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(a, b):
    ratio = np.asarray(a, dtype=float) / np.asarray(b, dtype=float)
    assert np.all(np.isfinite(ratio)) and np.all(ratio > 0)
    q = np.quantile(ratio, [.1, .5, .9], method="linear")
    return {"n": len(ratio), "geometric_mean_ratio": float(np.exp(np.mean(np.log(ratio)))),
            "median_ratio": float(q[1]), "p10_ratio": float(q[0]), "p90_ratio": float(q[2]),
            "min_ratio": float(np.min(ratio)), "max_ratio": float(np.max(ratio)),
            "fraction_less": float(np.mean(ratio < 1)), "fraction_equal": float(np.mean(ratio == 1)),
            "fraction_more": float(np.mean(ratio > 1))}


def save_figure(fig, output, name):
    for ext in ("png", "svg", "pdf"):
        path = output / f"{name}.{ext}"
        fig.savefig(path, dpi=180, facecolor="white")
        if ext == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def heatmap(ax, values, xlabels, ylabels):
    logged = np.log2(values)
    extent = max(float(np.max(np.abs(logged))), .01)
    im = ax.imshow(logged, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-extent, vcenter=0, vmax=extent), aspect="auto")
    ax.set_xticks(range(len(xlabels)), xlabels)
    ax.set_yticks(range(len(ylabels)), ylabels)
    for i in range(len(ylabels)):
        for j in range(len(xlabels)):
            ax.text(j, i, f"{values[i,j]:.2f}", ha="center", va="center", fontsize=10,
                    color="white" if abs(logged[i,j]) > .65 * extent else "#151515")
    return im, extent


def ratio_colorbar(fig, im, ax, extent):
    ticks = [x for x in range(math.ceil(-extent), math.floor(extent) + 1)]
    bar = fig.colorbar(im, ax=ax, fraction=.035, pad=.025, ticks=ticks)
    bar.ax.set_yticklabels([f"{2**x:g}×" for x in ticks])
    bar.set_label("Count ratio (logarithmic color scale)")


def main(output):
    plan_path = ROOT / "config/comparative-pilot-v1.json"
    plan = json.loads(plan_path.read_text())
    source = ROOT / plan["input"]
    assert sha(source) == plan["input_sha256"]
    assert sha(ROOT / plan["pilot_config"]) == plan["pilot_config_sha256"]
    pilot = json.loads((ROOT / plan["pilot_config"]).read_text())
    locks = {}
    for filename, digest in plan["tokenizer_locks"].items():
        p = ROOT / "config" / filename
        assert sha(p) == digest
        lock = json.loads(p.read_text())
        locks[lock["model_key"]] = lock
    rows = pq.read_table(source).to_pylist()
    models, labels = plan["models"], plan["labels"]
    languages = [v["code"] for v in pilot["languages"]]
    language_labels = [v["label"] for v in pilot["languages"]]
    ids = sorted({r["sentence_id"] for r in rows})
    assert len(rows) == 9000 and len(ids) == 100 and len(languages) == 18 and len(models) == 5
    by_key = {(r["model_key"], r["language"], r["sentence_id"]): r for r in rows}
    assert len(by_key) == len(rows)
    counts = np.empty((5, 18, 100), dtype=np.int64)
    for mi, model in enumerate(models):
        for li, language in enumerate(languages):
            for si, sid in enumerate(ids):
                row = by_key[model, language, sid]
                reference = by_key[models[0], language, sid]
                assert row["text_sha256"] == reference["text_sha256"]
                assert row["tokenizer_revision"] == locks[model]["revision"]
                assert row["dataset_revision"] == pilot["revision"] and row["split"] == "dev"
                assert row["token_count"] > 0
                counts[mi, li, si] = row["token_count"]
    paired = []
    lookup = {}
    for ai, a in enumerate(models):
        for bi, b in enumerate(models):
            for li, language in enumerate(languages + ["ALL"]):
                aa, bb = (counts[ai].ravel(), counts[bi].ravel()) if language == "ALL" else (counts[ai, li], counts[bi, li])
                record = {"numerator": a, "denominator": b, "language": language, **summarize(aa, bb)}
                paired.append(record)
                lookup[a, b, language] = record
    translated = []
    english_index = languages.index(plan["language_reference"])
    for mi, model in enumerate(models):
        for li, language in enumerate(languages):
            translated.append({"tokenizer": model, "numerator_language": language,
                               "denominator_language": plan["language_reference"],
                               **summarize(counts[mi, li], counts[mi, english_index])})
    for a in models:
        for b in models:
            for lang in languages + ["ALL"]:
                assert np.isclose(lookup[a,b,lang]["geometric_mean_ratio"] * lookup[b,a,lang]["geometric_mean_ratio"], 1)
    output.mkdir(parents=True, exist_ok=False)
    summary = {"paired_tokenizers": paired, "aligned_translations": translated}
    (output / "comparisons.json").write_text(json.dumps(summary, indent=2) + "\n")
    data = {"axis_order": ["tokenizer", "language", "aligned_sentence_id"], "models": models,
            "languages": languages, "aligned_sentence_ids": ids, "content_counts": counts.tolist()}
    (output / "count-data.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"})

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=.16, right=.88, bottom=.24, top=.83)
    values = np.array([[lookup[a,b,"ALL"]["geometric_mean_ratio"] for b in models] for a in models])
    im, extent = heatmap(ax, values, labels, labels)
    ratio_colorbar(fig, im, ax, extent)
    ax.set_xlabel("Denominator tokenizer", labelpad=12)
    ax.set_ylabel("Numerator tokenizer", labelpad=12)
    fig.suptitle("Same text, different tokenizer: count ratios", fontsize=18, y=.96)
    fig.text(.16,.885,"Read each cell as row count ÷ column count.",fontsize=12)
    fig.text(.09,.15,"1 = equal counts; 2 = twice as many tokens; 0.5 = half as many.",fontsize=11)
    fig.text(.09,.105,"Geometric mean of 1,800 paired ratios per cell; all 18 varieties weighted equally.",fontsize=10)
    fig.text(.09,.065,"FLORES+ dev • 100 related translation sets • Content tokens only • No model-quality ranking",fontsize=9)
    fig.text(.09,.025,"Five pinned BPE profiles, not five proven families. *MiniCPM: HF JSON; browser/GGUF unverified.",fontsize=9)
    save_figure(fig, output, "01-pairwise-count-ratios")

    reference = plan["tokenizer_reference"]
    others = [m for m in models if m != reference]
    all_records = [lookup[m,reference,l] for m in others for l in languages]
    low = 2 ** math.floor(math.log2(min(r["p10_ratio"] for r in all_records)))
    high = 2 ** math.ceil(math.log2(max(r["p90_ratio"] for r in all_records)))
    ticks = [2**x for x in range(round(math.log2(low)), round(math.log2(high)) + 1)]
    fig, axes = plt.subplots(1,4,figsize=(17,10),sharey=True)
    fig.subplots_adjust(left=.16,right=.98,bottom=.20,top=.85,wspace=.17)
    for ax, model in zip(axes, others):
        rr = [lookup[model,reference,l] for l in languages]
        med = np.array([r["median_ratio"] for r in rr])
        p10 = np.array([r["p10_ratio"] for r in rr])
        p90 = np.array([r["p90_ratio"] for r in rr])
        ax.errorbar(med, np.arange(18), xerr=[med-p10,p90-med], fmt="o",markersize=4,color="#007f86",capsize=2,lw=1.3)
        ax.axvline(1,color="#555555",ls="--",lw=1)
        ax.set_xscale("log",base=2)
        ax.set(xlim=(low*.90,high*1.10),yticks=range(18),yticklabels=language_labels,
               xlabel="Count ÷ Qwen count",title=labels[models.index(model)])
        ax.set_xticks(ticks,[f"{x:g}×" for x in ticks]);ax.grid(axis="x",alpha=.2)
        ax.spines[["right","top"]].set_visible(False)
    axes[0].invert_yaxis()
    fig.suptitle("Tokenizer differences depend on the language",fontsize=20,y=.965)
    fig.text(.16,.905,"Same text in each pair • Dot: median ratio • Line: 10th–90th percentile of observed ratios",fontsize=12)
    fig.text(.16,.12,"100 paired texts per row. Lines show sample variation, not confidence intervals. Same logarithmic scale in all panels.",fontsize=10)
    fig.text(.16,.075,"Qwen is a fixed reference, not a quality standard. All tokenizer pairs are retained in the numeric results.",fontsize=10)
    fig.text(.16,.03,"FLORES+ dev • Content tokens only • Five BPE profiles • *MiniCPM uses its HF JSON tokenizer.",fontsize=10)
    save_figure(fig,output,"02-language-ratios-versus-qwen")

    fig,ax=plt.subplots(figsize=(18,7))
    fig.subplots_adjust(left=.08,right=.93,bottom=.36,top=.82)
    values=np.array([r["geometric_mean_ratio"] for r in translated]).reshape(5,18)
    im,extent=heatmap(ax,values,language_labels,labels)
    plt.setp(ax.get_xticklabels(),rotation=45,ha="right",fontsize=10)
    ratio_colorbar(fig,im,ax,extent)
    fig.suptitle("Aligned translations: token count relative to English",fontsize=20,y=.96)
    fig.text(.08,.875,"Each cell: language count ÷ English count, using the same tokenizer and aligned sentence IDs.",fontsize=12)
    fig.text(.08,.16,"Geometric mean of 100 paired ratios per cell. English = 1 by definition. Color scale is logarithmic.",fontsize=11)
    fig.text(.08,.10,"Translations differ in length and wording: these ratios do not isolate a language effect or measure model intelligence.",fontsize=11)
    fig.text(.08,.04,"FLORES+ dev • Related translation sets • Content tokens only • *MiniCPM: HF JSON, browser/GGUF unverified.",fontsize=10)
    save_figure(fig,output,"03-aligned-language-ratios")

    lines=["# Direct tokenizer-count comparison", "", "Exploratory analysis of the already-measured FLORES+ dev pilot, 2026-10-18.",
           "No new tokenization, fitting, devtest access or model inference.", "", "## Same-text comparison", "",
           "Each cell is the geometric mean of per-text row/column count ratios over 1,800 matched texts.",
           "A value of 2 means twice as many tokens on this multiplicative average, not twice the cost",
           "or half the useful context in an actual application. No universal winner is implied.", "",
           "| Numerator / denominator | " + " | ".join(labels) + " |", "| --- | " + " | ".join(["---:"]*5) + " |"]
    for a,label in zip(models,labels):
        lines.append("| " + label + " | " + " | ".join(f"{lookup[a,b,'ALL']['geometric_mean_ratio']:.3f}" for b in models) + " |")
    lines += ["", "![Pairwise count ratios](01-pairwise-count-ratios.png)", "", "## Differences within each language", "",
              "![Language distributions](02-language-ratios-versus-qwen.png)", "",
              "Dots are median per-text ratios; horizontal lines cover the 10th–90th percentile.",
              "Intervals describe the sample spread, not confidence intervals. Reference choice is fixed",
              "in the plan. Every other ordered pair and its language cells remains in comparisons.json.", "",
              "For a concrete cross-language contrast, LFM/Gemma geometric mean ratios are:"]
    for lang in ["eng_Latn","tam_Taml","kor_Hang"]:
        r=lookup["lfm2-1.2b","gemma4-e2b",lang]
        lines.append(f"- {language_labels[languages.index(lang)]}: {r['geometric_mean_ratio']:.3f}×; median {r['median_ratio']:.3f}, p10–p90 {r['p10_ratio']:.3f}–{r['p90_ratio']:.3f} (100 texts).")
    lines += ["", "These examples illustrate variation; they do not establish its cause. They are geometric",
              "means of ratios, so they need not equal earlier ratios of summed token counts.", "", "## Aligned translations", "",
              "![Language relative to English](03-aligned-language-ratios.png)", "",
              "English is a reference only. Translation length, wording and writing systems vary together.",
              "These results are not a controlled test isolating language or a measure of language quality.", "",
              "## Evidence and limits", "", "- [comparisons.json](comparisons.json): 475 tokenizer-pair summaries and 90 translation summaries, including self-comparisons.",
              "- [count-data.json](count-data.json): numeric count cube and alignment IDs; no source text or token-ID sequences.",
              "- [validation.json](validation.json): pairing checks, hashes and versions.",
              "- [Inventory](../inventory-01/REPORT.md): all five assets use BPE but have distinct pipeline fingerprints.",
              "- [Specification](../../../config/comparative-pilot-v1.json) and [protocol](../../../docs/COMPARATIVE_STUDY_V2.md).", "",
              "The 9,000 counts cover 1,800 texts and 100 related translation sets, not independent draws.",
              "Five selected profiles do not represent all BPE tokenizers or other algorithm classes.",
              "Content-only counts omit full chat templates and response reserves. Browser speed/memory",
              "and model answer quality were not measured. MiniCPM is HF JSON, not verified GGUF parity.",
              "All three figures have PNG/SVG/PDF exports. See the independent verification output after validation.", ""]
    (output/"REPORT.md").write_text("\n".join(lines))
    validation={"input_sha256":sha(source),"plan_sha256":sha(plan_path),"script_sha256":sha(Path(__file__)),
                "versions":{"python":platform.python_version(),"numpy":np.__version__,"pyarrow":pyarrow.__version__,"matplotlib":matplotlib.__version__},
                "checks":{"rows":9000,"unique_keys":len(by_key),"aligned_ids":100,"languages":18,"tokenizers":5,
                          "paired_text_hashes_match":True,"tokenizer_and_dataset_revisions_match":True,
                          "positive_counts":True,"summary_groups":len(paired)+len(translated),"geometric_mean_reciprocals_match":True},
                "visual_inspection":"pending","independent_verification":"pending"}
    (output/"validation.json").write_text(json.dumps(validation,indent=2)+"\n")
    print("Verified 9,000 row keys/revisions and paired text hashes; generated 565 ratio summaries and three figures.")
    for lang in ["eng_Latn","tam_Taml","kor_Hang"]:
        print(lang,"LFM/Gemma geometric mean ratio:",lookup["lfm2-1.2b","gemma4-e2b",lang]["geometric_mean_ratio"])


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/"results"):
        parser.error("Output must be inside results/")
    main(output)
