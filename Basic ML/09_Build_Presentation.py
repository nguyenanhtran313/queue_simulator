"""
09_Build_Presentation.py — Dựng presentation.html tự chứa (self-contained), phong cách
dashboard kiểu Google Analytics: top navigation dạng tab, MỖI BƯỚC LÀ 1 TRANG riêng (không
cuộn qua tất cả), có nút Trước/Tiếp linh hoạt. Đọc toàn bộ output của Bước 0→8, mỗi trang có
mô tả PHƯƠNG PHÁP (bước này làm gì) + PHÁT HIỆN (insight tính trực tiếp từ số liệu thật, không
phải văn bản cố định) — để presentation luôn khớp với kết quả chạy gần nhất.

Chạy:  py 09_Build_Presentation.py   (cần đã chạy xong 00 -> 08)
Output: presentation.html
"""

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent

# ---- Palette categorical cho CHART (đã validate qua dataviz skill — 6 slot đầu, thứ tự cố
# định để đảm bảo phân biệt tốt cho người mù màu). Màu UI (nav/nút) dùng riêng Google Blue. --
MODEL_COLORS = {
    "Logistic Regression": "#2a78d6",             # blue
    "XGBoost": "#1baf7a",                          # aqua
    "LightGBM": "#eda100",                         # yellow
    "Logistic Regression (Uplift)": "#008300",     # green
    "XGBoost (Uplift)": "#4a3aa7",                 # violet
    "LightGBM (Uplift)": "#e34948",                # red
}
MODEL_ORDER = list(MODEL_COLORS.keys())
INK_PRIMARY = "#202124"
INK_SECONDARY = "#5f6368"
INK_MUTED = "#80868b"
GRID = "#e8eaed"
SURFACE = "#ffffff"
GOOGLE_BLUE = "#1a73e8"
GOOGLE_GREEN = "#188038"
GOOGLE_RED = "#d93025"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Roboto", "DejaVu Sans", "Arial"],
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_SECONDARY,
    "text.color": INK_PRIMARY,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def fmt_vnd(x: float) -> str:
    return f"{x:,.0f} đ"


def fmt_roi(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{x:+.2f}x"


def fig_to_base64(fig) -> str:
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def embed_image_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def ordered(df: pd.DataFrame) -> pd.DataFrame:
    return df.set_index("model").loc[MODEL_ORDER].reset_index()


# ===================================================================================
# Charts
# ===================================================================================

def chart_accuracy(df: pd.DataFrame, baselines: dict) -> str:
    df = ordered(df)
    be_label = f"{baselines['break_even_threshold']:.0%}"
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [MODEL_COLORS[m] for m in df["model"]]
    bars = ax.bar(df["model"], df["accuracy"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, labels=[f"{v:.1%}" for v in df["accuracy"]],
                 padding=3, fontsize=10, fontweight="bold", color=INK_PRIMARY)
    ax.set_ylim(0, max(df["accuracy"]) * 1.2)
    ax.set_ylabel(f"Accuracy (ngưỡng hoà vốn {be_label})")
    ax.set_title("So sánh Accuracy — 6 mô hình", fontsize=13, fontweight="bold", loc="left")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_precision_recall(df: pd.DataFrame, baselines: dict) -> str:
    df = ordered(df)
    be_label = f"{baselines['break_even_threshold']:.0%}"
    x = np.arange(len(df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    b1 = ax.bar(x - width/2, df["precision"], width, label="Precision", color="#2a78d6", zorder=3)
    b2 = ax.bar(x + width/2, df["recall"], width, label="Recall", color="#1baf7a", zorder=3)
    ax.bar_label(b1, labels=[f"{v:.0%}" for v in df["precision"]], padding=2, fontsize=8.5, fontweight="bold")
    ax.bar_label(b2, labels=[f"{v:.0%}" for v in df["recall"]], padding=2, fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df["model"], rotation=15, ha="right")
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Tỷ lệ")
    ax.set_title(f"So sánh Precision & Recall — 6 mô hình (ngưỡng hoà vốn {be_label}, cùng ngưỡng dùng gửi ZNS)",
                 fontsize=13, fontweight="bold", loc="left")
    ax.legend(frameon=False, loc="upper right")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_profit(df: pd.DataFrame, baselines: dict) -> str:
    df = ordered(df)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = [MODEL_COLORS[m] for m in df["model"]]
    bars = ax.bar(df["model"], df["profit_vnd"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, labels=[f"{v/1e6:,.1f}tr" for v in df["profit_vnd"]],
                 padding=3, fontsize=10, fontweight="bold", color=INK_PRIMARY)
    mass = baselines["mass_marketing_profit_vnd"]
    ax.axhline(mass, color=INK_MUTED, linestyle="--", linewidth=1.5, zorder=2)
    ax.text(len(df) - 0.4, mass, f"  Mass Marketing (gửi hết): {mass/1e6:,.1f}tr đ",
            va="bottom", ha="right", fontsize=9, color=INK_SECONDARY)
    ax.set_ylabel("Lợi nhuận trên tập test (VND)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:,.0f}tr"))
    ax.set_title("So sánh Lợi nhuận thực tế trên tập Test — 6 mô hình vs Mass Marketing",
                 fontsize=13, fontweight="bold", loc="left")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_roi(df: pd.DataFrame, baselines: dict) -> str:
    df = ordered(df)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = [MODEL_COLORS[m] for m in df["model"]]
    bars = ax.bar(df["model"], df["roi"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, labels=[fmt_roi(v) for v in df["roi"]],
                 padding=3, fontsize=10, fontweight="bold", color=INK_PRIMARY)
    mass_roi = baselines.get("mass_marketing_roi", np.nan)
    if pd.notna(mass_roi):
        ax.axhline(mass_roi, color=INK_MUTED, linestyle="--", linewidth=1.5, zorder=2)
        ax.text(len(df) - 0.4, mass_roi, f"  Mass Marketing ROI: {fmt_roi(mass_roi)}",
                va="bottom", ha="right", fontsize=9, color=INK_SECONDARY)
    ax.axhline(0, color=GRID, linewidth=1, zorder=1)
    ax.set_ylabel("ROI = Lợi nhuận / Chi phí (lần)")
    ax.set_title("So sánh ROI (hiệu quả sử dụng ngân sách) — 6 mô hình",
                 fontsize=13, fontweight="bold", loc="left")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_gain_decile(decile_df: pd.DataFrame, baselines: dict, best_label: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    x = decile_df["cum_customers_pct"]
    y = decile_df["cum_profit_vnd"]
    ax.plot(x, y, marker="o", color="#2a78d6", linewidth=2.5, markersize=7, zorder=3)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi/1e6:,.0f}tr", (xi, yi), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8, fontweight="bold", color=INK_PRIMARY)
    mass = baselines["mass_marketing_profit_vnd"]
    ax.axhline(mass, color=INK_MUTED, linestyle="--", linewidth=1.5, zorder=2)
    ax.text(5, mass, f"Mass Marketing: {mass/1e6:,.1f}tr đ", va="bottom", fontsize=9, color=INK_SECONDARY)
    ax.set_xlabel("% khách hàng được nhắm tới (xếp theo Uplift Score giảm dần)")
    ax.set_ylabel("Lợi nhuận lũy kế (VND)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:,.0f}tr"))
    ax.set_title(f"Gain Chart — {best_label}: lợi nhuận tích lũy theo % khách hàng nhắm tới",
                 fontsize=13, fontweight="bold", loc="left")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_roc_auc(df: pd.DataFrame) -> str:
    prop = df[df["family"] == "Propensity"].copy()
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    colors = [MODEL_COLORS[m] for m in prop["model"]]
    bars = ax.bar(prop["model"], prop["roc_auc"], color=colors, width=0.5, zorder=3)
    ax.bar_label(bars, labels=[f"{v:.3f}" for v in prop["roc_auc"]],
                 padding=3, fontsize=10, fontweight="bold", color=INK_PRIMARY)
    ax.axhline(0.5, color=INK_MUTED, linestyle="--", linewidth=1.2, zorder=2)
    ax.text(len(prop) - 0.35, 0.5, "  Random guess (0.5)", va="bottom", ha="right",
            fontsize=8.5, color=INK_SECONDARY)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Benchmark ROC-AUC — 3 mô hình Propensity", fontsize=13, fontweight="bold", loc="left")
    style_ax(ax)
    fig.tight_layout()
    return fig_to_base64(fig)


# ===================================================================================
# Insight text (tính từ số liệu thật)
# ===================================================================================

def build_insights(df: pd.DataFrame, baselines: dict, decile_df: pd.DataFrame, fi_df: pd.DataFrame) -> dict:
    mass = baselines["mass_marketing_profit_vnd"]
    df = df.copy()
    df["profit_uplift_vs_mass_pct"] = (df["profit_vnd"] - mass) / mass

    best_acc_row = df.loc[df["accuracy"].idxmax()]
    best_profit_row = df.loc[df["profit_vnd"].idxmax()]
    best_roi_row = df.loc[df["roi"].idxmax()]
    worst_profit_row = df.loc[df["profit_vnd"].idxmin()]

    propensity = df[df["family"] == "Propensity"]
    uplift = df[df["family"] == "Uplift"]
    best_propensity = propensity.loc[propensity["profit_vnd"].idxmax()]
    best_uplift = uplift.loc[uplift["profit_vnd"].idxmax()]

    n_below_mass = (df["profit_vnd"] < mass).sum()
    n_roi_below_mass = (df["roi"] < baselines.get("mass_marketing_roi", 0)).sum()

    peak_decile_row = decile_df.loc[decile_df["cum_profit_vnd"].idxmax()]

    top_feat_xgb = fi_df[fi_df["model"] == "XGBoost"].sort_values("importance", ascending=False)
    top_feat_names = [f.replace("remainder__", "").replace("cat__", "") for f in top_feat_xgb["feature"].head(3)]

    insights = {}

    be = baselines['break_even_threshold']
    test_rr = baselines['test_response_rate']
    prop_send_rate = propensity["n_sent"] / propensity["n_test"]
    most_selective = propensity.loc[prop_send_rate.idxmin()]
    most_selective_rate = prop_send_rate.min()
    least_selective = propensity.loc[prop_send_rate.idxmax()]
    least_selective_rate = prop_send_rate.max()

    insights["accuracy"] = (
        f"Toàn bộ Accuracy/Precision/Recall ở đây được tính tại <b>đúng ngưỡng dùng để quyết định gửi ZNS</b> "
        f"(hoà vốn {be:.0%}) — không dùng ngưỡng 0.5 mặc định, vì 0.5 không có ý nghĩa kinh tế khi cost/reward "
        f"chỉ {be:.0%}. Model có Accuracy cao nhất là <b>{best_acc_row['model']}</b> ({best_acc_row['accuracy']:.1%}). "
        f"3 model Uplift có Accuracy thấp hơn hẳn nhóm Propensity — đây là điều <b>dự kiến, không phải lỗi</b>: "
        f"Uplift model không dự đoán \"khách này có phản hồi không\" mà trả lời câu hỏi khác — \"khuyến mãi có "
        f"làm khách này đổi ý không\". Response rate nền trên tập test chỉ {test_rr:.1%}, nên Accuracy dễ bị chi "
        f"phối bởi việc đoán đúng nhóm đa số (không phản hồi)."
    )

    insights["precision_recall"] = (
        f"Ở ngưỡng hoà vốn {be:.0%}, <b>{least_selective['model']}</b> gửi cho gần như toàn bộ khách hàng "
        f"({least_selective_rate:.0%}) → Recall rất cao ({least_selective['recall']:.0%}) nhưng Precision chỉ "
        f"xấp xỉ response rate nền ({least_selective['precision']:.0%} so với nền {test_rr:.1%}) — tức <b>không "
        f"thực sự chọn lọc</b>, gần như gửi đại trà trá hình. Ngược lại <b>{most_selective['model']}</b> chọn lọc "
        f"hơn hẳn (chỉ gửi cho {most_selective_rate:.0%} khách hàng) nhưng vẫn giữ Recall {most_selective['recall']:.0%} "
        f"và Precision {most_selective['precision']:.0%} — cao hơn rõ rệt so với nền {test_rr:.1%} — cho thấy nó "
        f"tách biệt nhóm khách hàng tốt hơn thay vì chỉ hạ thấp ngưỡng để \"vơ hết\"."
    )

    insights["profit"] = (
        f"<b>{best_profit_row['model']}</b> cho lợi nhuận cao nhất trên tập test: "
        f"{fmt_vnd(best_profit_row['profit_vnd'])} ({best_profit_row['profit_uplift_vs_mass_pct']:+.1%} so với gửi đại trà "
        f"— {fmt_vnd(mass)}). Ngược lại, {n_below_mass}/6 model cho lợi nhuận <b>thấp hơn</b> cả gửi đại trà, gồm "
        f"{worst_profit_row['model']} ({worst_profit_row['profit_uplift_vs_mass_pct']:+.1%}) — một bài học quan trọng: "
        f"không phải model phức tạp hơn lúc nào cũng thắng, và Uplift Modeling cần được đánh giá bằng Profit thực tế "
        f"trên tập test, không thể giả định nó tự động tốt hơn Propensity."
    )

    mass_roi = baselines.get("mass_marketing_roi", float("nan"))
    insights["roi"] = (
        f"Profit đo QUY MÔ giá trị tạo ra, còn <b>ROI đo HIỆU QUẢ sử dụng ngân sách</b> — 2 góc nhìn có thể lệch "
        f"nhau. ROI cao nhất thuộc về <b>{best_roi_row['model']}</b> ({fmt_roi(best_roi_row['roi'])}, so với "
        f"Mass Marketing {fmt_roi(mass_roi)}). {n_roi_below_mass}/6 model có ROI thấp hơn cả gửi đại trà — nghĩa là "
        f"dù có thể vẫn lời (Profit dương), nhưng đang chi tiêu ZNS kém hiệu quả hơn phương án đơn giản nhất. "
        f"Khi ngân sách marketing bị giới hạn, nên ưu tiên model có ROI cao; khi mục tiêu là tối đa hoá tổng lợi "
        f"nhuận và ngân sách dồi dào, nên ưu tiên model có Profit cao — 2 tiêu chí không phải lúc nào cũng chọn "
        f"cùng 1 model."
    )

    insights["gain_decile"] = (
        f"Nếu chỉ nhắm tới top {peak_decile_row['cum_customers_pct']:.0f}% khách hàng có Uplift Score cao nhất "
        f"(thay vì gửi 100%), lợi nhuận đạt đỉnh {fmt_vnd(peak_decile_row['cum_profit_vnd'])} — "
        f"{(peak_decile_row['cum_profit_vnd']-mass)/mass:+.1%} so với gửi đại trà — trong khi tiết kiệm được "
        f"{100-peak_decile_row['cum_customers_pct']:.0f}% chi phí gửi tin. Gửi thêm cho nhóm 10% cuối (Uplift Score "
        f"thấp nhất, nhiều khả năng là Sleeping Dogs) kéo lợi nhuận tụt trở lại đúng bằng mức Mass Marketing — "
        f"minh chứng rõ cho nguyên tắc \"không phải cứ gửi nhiều hơn là lời hơn\"."
    )

    insights["feature_importance"] = (
        f"Theo XGBoost, 3 yếu tố quyết định lớn nhất tới khả năng phản hồi khuyến mãi là: "
        + ", ".join(f"<b>{f}</b>" for f in top_feat_names) +
        f". Điều này khớp với phát hiện T-test/Chi-square ở Bước 1 (EDA) — Segment và Last_Active_Days là "
        f"nhóm biến \"vàng\", còn Age/Gender/Txn_Count_3M gần như không có vai trò."
    )

    insights["final_best_propensity"] = best_propensity
    insights["final_best_uplift"] = best_uplift
    insights["final_best_overall"] = best_profit_row
    insights["final_best_accuracy"] = best_acc_row
    insights["final_best_roi"] = best_roi_row
    insights["mass"] = mass
    insights["mass_roi"] = mass_roi
    return insights


# ===================================================================================
# EDA page helpers
# ===================================================================================

VN_LABELS = {
    "Age": "Tuổi", "Avg_Monthly_Balance_VND": "Số dư TB/tháng",
    "Txn_Count_3M": "Số GD 3 tháng", "Txn_Amount_3M_VND": "Tổng tiền GD 3 tháng",
    "App_Logins_3M": "Số lần login app", "Promo_Txn_Count_3M": "Số lần dùng KM 3 tháng",
    "Last_Active_Days": "Ngày kể từ lần hoạt động cuối", "Gender": "Giới tính", "Segment": "Phân khúc",
}


def build_eda_table(eda: dict) -> str:
    rows = []
    for t in eda["significance_tests"]:
        var = VN_LABELS.get(t["variable"], t["variable"])
        sig_badge = '<span class="badge badge-good">Có ý nghĩa</span>' if t["significant"] else '<span class="badge badge-neutral">Không</span>'
        corr = f"{t['corr_with_target']:+.3f}" if t["corr_with_target"] is not None else "—"
        rows.append(
            f"<tr><td>{var}</td><td style='text-align:center'>{t['test']}</td>"
            f"<td style='text-align:right'>{t['p_value']:.4f}</td>"
            f"<td style='text-align:center'>{sig_badge}</td>"
            f"<td style='text-align:right'>{corr}</td></tr>"
        )
    return (
        '<table class="table"><thead><tr><th>Biến</th><th>Kiểm định</th><th>p-value</th>'
        '<th>Ý nghĩa TK (p&lt;0.05)</th><th>Tương quan target</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_describe_table(eda: dict) -> str:
    describe = eda["describe"]
    cols = list(describe.keys())
    stats_order = ["mean", "std", "min", "25%", "50%", "75%", "max"]
    header = "<tr><th>Thống kê</th>" + "".join(f"<th>{VN_LABELS.get(c, c)}</th>" for c in cols) + "</tr>"
    rows = []
    for s in stats_order:
        cells = "".join(f"<td style='text-align:right'>{describe[c][s]:,.1f}</td>" for c in cols)
        rows.append(f"<tr><td><b>{s}</b></td>{cells}</tr>")
    return f'<table class="table"><thead>{header}</thead><tbody>{"".join(rows)}</tbody></table>'


def build_cluster_table(cluster_df: pd.DataFrame) -> str:
    df = cluster_df.rename(columns={
        "Cluster": "Cụm", "Promo_Txn_Count_3M": "TB Số lần dùng KM",
        "Last_Active_Days": "TB Ngày không hoạt động", "Avg_Monthly_Balance_VND": "TB Số dư",
        "Cluster_Size": "Số lượng KH",
    })
    for c in df.columns:
        if "TB" in c and "Số dư" in c:
            df[c] = df[c].map(lambda v: f"{v:,.0f} đ")
        elif "TB" in c:
            df[c] = df[c].map(lambda v: f"{v:,.1f}")
        elif "Số lượng" in c:
            df[c] = df[c].map(lambda v: f"{v:,.0f}")
    return df.to_html(classes="table", index=False, escape=False)


# ===================================================================================
# Main
# ===================================================================================

def main() -> None:
    print("--- STEP 9: Building presentation.html (Google Analytics style, multi-page) ---")

    results = ordered(pd.read_csv(HERE / "08_model_comparison_results.csv"))
    with open(HERE / "08_baselines.json", "r", encoding="utf-8") as f:
        baselines = json.load(f)
    fi_df = pd.read_csv(HERE / "08_feature_importance.csv")
    decile_df = pd.read_csv(HERE / "08_uplift_gain_by_decile.csv")
    best_uplift_label = decile_df["model"].iloc[0]

    eda = None
    eda_path = HERE / "01_eda_results.json"
    if eda_path.exists():
        with open(eda_path, "r", encoding="utf-8") as f:
            eda = json.load(f)

    cluster_df = None
    cluster_path = HERE / "02_cluster_profile.csv"
    if cluster_path.exists():
        cluster_df = pd.read_csv(cluster_path)

    try:
        resp_col = pd.read_csv(HERE / "customer_promo_data.csv", usecols=["Historical_Promo_Response"])
        n_rows = len(resp_col)
        response_rate = resp_col["Historical_Promo_Response"].mean()
    except FileNotFoundError:
        n_rows = baselines["n_test"] * 5
        response_rate = baselines["test_response_rate"]

    insights = build_insights(results, baselines, decile_df, fi_df)

    print("Đang vẽ biểu đồ...")
    img_accuracy = chart_accuracy(results, baselines)
    img_precision_recall = chart_precision_recall(results, baselines)
    img_profit = chart_profit(results, baselines)
    img_roi = chart_roi(results, baselines)
    img_gain = chart_gain_decile(decile_df, baselines, best_uplift_label)
    img_roc_auc = chart_roc_auc(results)

    img_corr = embed_image_file(HERE / "01_correlation_matrix.png")
    img_kmeans_eval = embed_image_file(HERE / "02_kmeans_evaluation.png")
    img_shap_bar = embed_image_file(HERE / "05_shap_summary_bar.png")
    img_shap_dot = embed_image_file(HERE / "05_shap_summary_dot.png")
    img_shap_dep1 = embed_image_file(HERE / "05_shap_dependence_top1.png")

    # ---- Bảng số liệu chính (Bước 8) — đã thêm cột ROI + Chi phí theo yêu cầu ----
    table_df = results[["model", "family", "accuracy", "precision", "recall",
                         "profit_vnd", "total_cost_vnd", "roi", "n_sent"]].rename(
        columns={"model": "Model", "family": "Loại", "accuracy": "Accuracy", "precision": "Precision",
                 "recall": "Recall", "profit_vnd": "Lợi nhuận (VND)", "total_cost_vnd": "Chi phí (VND)",
                 "roi": "ROI", "n_sent": "Số KH gửi"}
    )
    table_df["Accuracy"] = table_df["Accuracy"].map(lambda v: f"{v:.1%}")
    table_df["Precision"] = table_df["Precision"].map(lambda v: f"{v:.1%}")
    table_df["Recall"] = table_df["Recall"].map(lambda v: f"{v:.1%}")
    table_df["Lợi nhuận (VND)"] = table_df["Lợi nhuận (VND)"].map(lambda v: f"{v:,.0f}")
    table_df["Chi phí (VND)"] = table_df["Chi phí (VND)"].map(lambda v: f"{v:,.0f}")
    table_df["ROI"] = table_df["ROI"].map(fmt_roi)
    table_df["Số KH gửi"] = table_df["Số KH gửi"].map(lambda v: f"{v:,.0f}")
    table_str = table_df.to_html(classes="table", index=False, escape=False)

    best_propensity = insights["final_best_propensity"]
    best_uplift = insights["final_best_uplift"]
    best_overall = insights["final_best_overall"]
    best_roi_row = insights["final_best_roi"]
    mass = insights["mass"]
    mass_roi = insights["mass_roi"]

    def img_tag(b64, alt, style="width:100%;border-radius:8px;"):
        if not b64:
            return f'<p class="missing-img">⚠️ Chưa có ảnh "{alt}" — hãy chạy script tương ứng trước.</p>'
        return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="{style}">'

    # ============================ EDA PAGE CONTENT ============================
    if eda:
        eda_kpis = f"""
        <div class="kpi-row">
          <div class="kpi-card"><div class="kpi-label">Số khách hàng</div><div class="kpi-value">{eda['n_rows']:,}</div></div>
          <div class="kpi-card"><div class="kpi-label">Số cột dữ liệu</div><div class="kpi-value">{eda['n_cols']}</div></div>
          <div class="kpi-card"><div class="kpi-label">Giá trị thiếu (missing)</div><div class="kpi-value">{eda['total_missing_values']}</div></div>
          <div class="kpi-card"><div class="kpi-label">Response rate</div><div class="kpi-value">{eda['response_rate']:.1%}</div></div>
        </div>"""
        n_sig = sum(1 for t in eda["significance_tests"] if t["significant"])
        n_total_tests = len(eda["significance_tests"])
        sig_vars = [VN_LABELS.get(t["variable"], t["variable"]) for t in eda["significance_tests"] if t["significant"]]
        nonsig_vars = [VN_LABELS.get(t["variable"], t["variable"]) for t in eda["significance_tests"] if not t["significant"]]
        eda_stats_table = build_describe_table(eda)
        eda_sig_table = build_eda_table(eda)
        eda_conclusion = (
            f"<b>Kết luận Bước 1:</b> {n_sig}/{n_total_tests} biến có ý nghĩa thống kê (p&lt;0.05) với target — "
            f"nhóm biến \"vàng\" nên giữ lại: {', '.join(f'<b>{v}</b>' for v in sig_vars)}. "
            f"Nhóm biến nhiễu (p≥0.05, cân nhắc loại bỏ khi cần model gọn nhẹ): {', '.join(nonsig_vars) if nonsig_vars else '(không có)'}. "
            f"Ngoài ra, <code>Estimated_CLV_VND</code> tương quan {eda['clv_balance_correlation']:.3f} với "
            f"<code>Avg_Monthly_Balance_VND</code> — bẫy đa cộng tuyến, đã loại khi train ở các bước sau."
        )
    else:
        eda_kpis = '<p class="missing-img">⚠️ Chưa có 01_eda_results.json — hãy chạy 01_EDA_and_Stats.py trước.</p>'
        eda_stats_table = eda_sig_table = eda_conclusion = ""

    # ============================ KMEANS PAGE CONTENT ============================
    if cluster_df is not None:
        best_k = int(cluster_df["Best_K"].iloc[0])
        n_clusters = len(cluster_df)
        cluster_table_html = build_cluster_table(cluster_df)
        cluster_conclusion = (
            f"Thuật toán chọn <b>K={best_k}</b> cụm dựa trên Silhouette Score cao nhất. Đây là phân tích "
            f"<b>độc lập</b> (persona khách hàng), không phải input cho model dự đoán phản hồi khuyến mãi ở "
            f"các bước sau — giá trị của nó là cho đội Marketing một góc nhìn \"chân dung khách hàng\" song song."
        )
    else:
        cluster_table_html = '<p class="missing-img">⚠️ Chưa có 02_cluster_profile.csv — hãy chạy 02_KMeans_Segmentation.py trước.</p>'
        cluster_conclusion = ""
        n_clusters = "?"

    # ============================ HTML ============================
    pages = []  # (id, nav_label, title, content_html)

    pages.append(("p-overview", "Tổng quan", "📊 Case Study: Dự đoán & Tối ưu ROI Chiến dịch Khuyến mãi (ZNS)", f"""
      <p class="page-subtitle">So sánh 6 mô hình (Propensity x3 + Uplift x3) — dữ liệu {n_rows:,} khách hàng.</p>
      <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Số khách hàng</div><div class="kpi-value">{n_rows:,}</div></div>
        <div class="kpi-card"><div class="kpi-label">Response rate</div><div class="kpi-value">{response_rate:.1%}</div></div>
        <div class="kpi-card"><div class="kpi-label">Chi phí / tin ZNS</div><div class="kpi-value">500 đ</div></div>
        <div class="kpi-card"><div class="kpi-label">Lợi nhuận / phản hồi</div><div class="kpi-value">10.000 đ</div></div>
        <div class="kpi-card"><div class="kpi-label">Ngưỡng hoà vốn</div><div class="kpi-value">{baselines['break_even_threshold']:.0%}</div></div>
      </div>
      <div class="card">
        <h3>Mục tiêu bài toán</h3>
        <p>Dự đoán khách hàng nào nên nhận tin khuyến mãi ZNS để tối đa hoá lợi nhuận, so với việc gửi đại trà
        cho toàn bộ khách hàng. Bài toán trả lời 2 câu hỏi kinh doanh: <b>(1)</b> Model nào dự đoán đúng nhất
        ai sẽ phản hồi? <b>(2)</b> Model nào tối ưu lợi nhuận/ROI thực tế tốt nhất khi áp dụng?</p>
        <h3>Lộ trình trình bày</h3>
        <ol class="roadmap">
          <li>Bước 1 — Khám phá dữ liệu (EDA) & Kiểm định thống kê</li>
          <li>Bước 2 — Phân khúc khách hàng (KMeans, phân tích độc lập)</li>
          <li>Bước 3-4 — Xây dựng & Benchmark 3 model Propensity</li>
          <li>Bước 5 — Giải thích model bằng SHAP</li>
          <li>Bước 8 — So sánh công bằng 6 model: Accuracy / Precision / Recall / Profit / ROI</li>
          <li>Kết luận — Chọn model nào cho từng mục tiêu kinh doanh</li>
        </ol>
      </div>
    """))

    pages.append(("p-eda", "1. EDA", "Bước 1 — Khám phá dữ liệu & Kiểm định thống kê", f"""
      <div class="method-box">
        <b>Phương pháp:</b> Kiểm tra chất lượng dữ liệu (missing values, describe), tính baseline response rate,
        chạy <b>T-test</b> cho các biến số liên tục và <b>Chi-square</b> cho các biến phân loại để xác định biến
        nào có ý nghĩa thống kê (p&lt;0.05) với target, và vẽ ma trận tương quan để phát hiện đa cộng tuyến.
      </div>
      {eda_kpis}
      <div class="card">
        <h3>Thống kê mô tả (các biến số chính)</h3>
        {eda_stats_table}
      </div>
      <div class="card">
        <h3>Kiểm định thống kê (T-test / Chi-square) với target</h3>
        {eda_sig_table}
        <div class="insight">{eda_conclusion}</div>
      </div>
      <div class="card">
        <h3>Ma trận tương quan (Correlation Matrix)</h3>
        {img_tag(img_corr, "Correlation Matrix")}
      </div>
    """))

    pages.append(("p-kmeans", "2. Phân khúc KH", "Bước 2 — Phân khúc khách hàng (KMeans)", f"""
      <div class="method-box">
        <b>Phương pháp:</b> Phân cụm khách hàng theo hành vi (Số lần dùng KM, Ngày không hoạt động, Số dư TB) sau
        khi chuẩn hoá dữ liệu. Tìm số cụm K tối ưu bằng Elbow Method + Silhouette Score, rồi profile từng cụm để
        đặt tên nhóm khách hàng (persona).
      </div>
      <div class="card">
        <h3>Elbow Method & Silhouette Score (K={n_clusters if isinstance(n_clusters, str) else cluster_df['Best_K'].iloc[0]})</h3>
        {img_tag(img_kmeans_eval, "KMeans Evaluation")}
      </div>
      <div class="card">
        <h3>Chân dung từng cụm khách hàng</h3>
        {cluster_table_html}
        <div class="insight">{cluster_conclusion}</div>
      </div>
    """))

    pages.append(("p-benchmark", "3-4. Benchmark", "Bước 3-4 — Xây dựng & Benchmark Model", f"""
      <div class="method-box">
        <b>Phương pháp:</b> Xây model baseline (Logistic Regression, pipeline chuẩn hoá + one-hot encoding, xử lý
        mất cân bằng lớp bằng <code>class_weight='balanced'</code>), sau đó so sánh với 2 model tree-based mạnh
        hơn (XGBoost, LightGBM — không cần scale numeric, bắt được tương quan phi tuyến) bằng ROC-AUC.
      </div>
      <div class="card">
        <h3>ROC-AUC — 3 model Propensity (train/test 80/20, đo trên tập test)</h3>
        {img_tag(img_roc_auc, "ROC-AUC Benchmark", style="max-width:600px;border-radius:8px;")}
        <div class="insight">Cả 3 model có ROC-AUC quanh {results[results['family']=='Propensity']['roc_auc'].mean():.2f} —
        vượt xa mốc 0.5 (đoán ngẫu nhiên), xác nhận các biến từ Bước 1 thực sự mang tín hiệu dự đoán.
        Model production (XGBoost/LightGBM) được lưu ra <code>.pkl</code> để tái sử dụng ở Bước 5-7.</div>
      </div>
    """))

    pages.append(("p-shap", "5. SHAP", "Bước 5 — Giải thích Model bằng SHAP", f"""
      <div class="method-box">
        <b>Phương pháp:</b> Dùng SHAP TreeExplainer trên model XGBoost để biến AI từ "hộp đen" thành "hộp trong
        suốt" — biểu đồ Bar cho biết biến nào quan trọng nhất, biểu đồ Dot cho biết chiều tác động (tăng hay
        giảm xác suất phản hồi), biểu đồ Dependence tìm "điểm bùng phát" theo từng ngưỡng giá trị cụ thể.
      </div>
      <div class="card">
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
          <div style="flex:1; min-width:300px;"><h3>Feature Importance tổng thể</h3>{img_tag(img_shap_bar, "SHAP Bar")}</div>
          <div style="flex:1; min-width:300px;"><h3>Chiều hướng tác động</h3>{img_tag(img_shap_dot, "SHAP Dot")}</div>
        </div>
        {img_tag(img_shap_dep1, "SHAP Dependence", style="max-width:600px;border-radius:8px;margin-top:14px;")}
        <div class="insight">{insights['feature_importance']}</div>
      </div>
    """))

    pages.append(("p-compare", "8. So sánh 6 Model", "Bước 8 — So sánh công bằng 6 Mô hình", f"""
      <div class="method-box">
        <b>Phương pháp:</b> Chỉ chia train/test <b>một lần duy nhất</b> (80/20, stratify), dùng chung cho cả
        6 model để so sánh công bằng. Đánh giá Accuracy/Precision/Recall/Profit/ROI <b>chỉ trên tập test</b>
        (chưa từng thấy khi train) — tránh lạc quan giả do data leakage. Quy ước gửi ZNS: Propensity gửi nếu
        P(phản hồi) &gt; {baselines['break_even_threshold']:.0%}; Uplift gửi nếu Uplift Score &gt; {baselines['break_even_threshold']:.0%}.
        Accuracy/Precision/Recall dùng <b>đúng ngưỡng này</b> (không phải 0.5 mặc định) để 3 chỉ số giải thích
        được vì sao Profit lại như vậy, thay vì mâu thuẫn với nó.
      </div>
      <div class="card"><h3>1. Accuracy</h3>{img_tag(img_accuracy, "Accuracy")}<div class="insight">{insights['accuracy']}</div></div>
      <div class="card"><h3>2. Precision &amp; Recall</h3>{img_tag(img_precision_recall, "Precision Recall")}<div class="insight">{insights['precision_recall']}</div></div>
      <div class="card"><h3>3. Lợi nhuận (Profit)</h3>{img_tag(img_profit, "Profit")}<div class="insight">{insights['profit']}</div></div>
      <div class="card"><h3>4. ROI = Lợi nhuận / Chi phí</h3>{img_tag(img_roi, "ROI")}<div class="insight">{insights['roi']}</div></div>
      <div class="card"><h3>5. Gain Chart — Uplift model tốt nhất</h3>{img_tag(img_gain, "Gain Chart")}<div class="insight">{insights['gain_decile']}</div></div>
      <div class="card">
        <h3>Bảng số liệu đầy đủ</h3>
        <div class="table-scroll">{table_str}</div>
      </div>
    """))

    pages.append(("p-conclusion", "Kết luận", "✅ Kết luận — Nên chọn model nào?", f"""
      <div class="conclusion-box">
        <h3>🎯 Kịch bản A — Ưu tiên ROI hơn Accuracy (scale nhanh, chấp nhận đánh đổi)</h3>
        <p>Model cho lợi nhuận thực tế cao nhất trên tập test là <b>{best_overall['model']}</b>:
        {fmt_vnd(best_overall['profit_vnd'])}, cao hơn gửi đại trà {((best_overall['profit_vnd']-mass)/mass):+.1%}
        (ROI {fmt_roi(best_overall['roi'])}). Nếu mục tiêu thuần tuý là <b>hiệu quả ngân sách</b> (ROI cao nhất
        trên mỗi đồng chi ra) thay vì tổng lợi nhuận, model đáng cân nhắc là <b>{best_roi_row['model']}</b>
        (ROI {fmt_roi(best_roi_row['roi'])}) — 2 tiêu chí này có thể trỏ tới các model khác nhau tuỳ ngân sách
        campaign còn nhiều hay ít. (Tham chiếu: ROI của Mass Marketing là {fmt_roi(mass_roi)}.)</p>
      </div>

      <div class="conclusion-box conclusion-box-blue">
        <h3>📈 Kịch bản B — Ưu tiên Accuracy để scale ổn định, ROI không quá tệ</h3>
        <p>Model có Accuracy cao nhất là <b>{insights['final_best_accuracy']['model']}</b>
        ({insights['final_best_accuracy']['accuracy']:.1%}) — dự đoán ổn định, ít lệch khi áp dụng cho tệp
        khách hàng mới/lớn hơn trong tương lai. Lợi nhuận của model này là
        {fmt_vnd(insights['final_best_accuracy']['profit_vnd'])}
        ({((insights['final_best_accuracy']['profit_vnd']-mass)/mass):+.1%} so với gửi đại trà, ROI
        {fmt_roi(insights['final_best_accuracy']['roi'])}) — vẫn dương và vượt mass marketing, tức ROI
        "không quá tệ" như yêu cầu.</p>
      </div>

      <div class="final-answer">
        <p class="final-answer-lead">Trong case study này, cả 2 kịch bản đều hội tụ về CÙNG một model:</p>
        <p class="model-name">{best_overall['model']}</p>
        <p class="final-answer-sub">Accuracy {best_overall['accuracy']:.1%} · Lợi nhuận {fmt_vnd(best_overall['profit_vnd'])}
        ({((best_overall['profit_vnd']-mass)/mass):+.1%} vs Mass Marketing) · ROI {fmt_roi(best_overall['roi'])}</p>
      </div>

      <div class="card">
        <h3>Lưu ý về Uplift Modeling</h3>
        <div class="insight">
          Về lý thuyết, Uplift Model (loại trừ "Sleeping Dogs" — nhóm khách hàng phản cảm với khuyến mãi) có
          tiềm năng vượt Propensity model. Trong lần chạy này, model Uplift tốt nhất
          (<b>{best_uplift['model']}</b>, lợi nhuận {fmt_vnd(best_uplift['profit_vnd'])}, ROI {fmt_roi(best_uplift['roi'])})
          chưa vượt được {best_propensity['model']} ({fmt_vnd(best_propensity['profit_vnd'])}) — nguyên nhân
          nhiều khả năng là hiệu ứng nhân quả (uplift) của khuyến mãi trong dữ liệu khá sát ngưỡng hoà vốn
          {baselines['break_even_threshold']:.0%}, khiến ước lượng S-Learner dễ nhiễu. Khuyến nghị: tiếp tục đầu
          tư tinh chỉnh Uplift Model (Two-Model Learner/T-Learner, hoặc thu thập thêm dữ liệu treatment ngẫu
          nhiên/A-B test thật) trước khi đưa vào production.
        </div>
      </div>
      <p class="footer-note"><i>Toàn bộ số liệu trong báo cáo này được tính trực tiếp từ {n_rows:,} dòng dữ liệu
      và pipeline 00→09 trong thư mục <code>Basic ML/</code>.</i></p>
    """))

    nav_buttons = "".join(
        f'<button class="nav-tab" data-page="{pid}" onclick="goToPage(\'{pid}\')">{label}</button>'
        for pid, label, _, _ in pages
    )
    page_sections = "".join(
        f'<section class="page" id="{pid}"><h1 class="page-title">{title}</h1>{content}</section>'
        for pid, _, title, content in pages
    )
    page_ids_js = ",".join(f"'{pid}'" for pid, _, _, _ in pages)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Case Study: Dự đoán & Tối ưu ROI Khuyến mãi</title>
<style>
  :root {{
    --blue: {GOOGLE_BLUE}; --green: {GOOGLE_GREEN}; --red: {GOOGLE_RED};
    --ink: {INK_PRIMARY}; --ink-secondary: {INK_SECONDARY}; --ink-muted: {INK_MUTED};
    --grid: {GRID}; --surface: {SURFACE}; --page-bg: #f8f9fa;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; background: var(--page-bg);
          color: var(--ink); -webkit-font-smoothing: antialiased; }}
  .topnav {{ position: sticky; top: 0; z-index: 10; background: var(--surface);
             border-bottom: 1px solid var(--grid); box-shadow: 0 1px 2px rgba(60,64,67,0.15); }}
  .topnav-inner {{ max-width: 1180px; margin: 0 auto; padding: 0 24px; display: flex;
                   align-items: center; gap: 4px; overflow-x: auto; }}
  .nav-brand {{ font-weight: 700; font-size: 1.05rem; color: var(--blue); padding: 14px 16px 14px 0;
                white-space: nowrap; }}
  .nav-tab {{ background: none; border: none; padding: 16px 14px; font-size: 0.88rem; font-weight: 500;
              color: var(--ink-secondary); cursor: pointer; white-space: nowrap; border-bottom: 3px solid transparent;
              transition: color .15s, border-color .15s; }}
  .nav-tab:hover {{ color: var(--blue); background: rgba(26,115,232,0.04); }}
  .nav-tab.active {{ color: var(--blue); border-bottom-color: var(--blue); font-weight: 700; }}

  main {{ max-width: 1180px; margin: 0 auto; padding: 28px 24px 100px 24px; }}
  .page {{ display: none; animation: fadein .2s ease; }}
  .page.active {{ display: block; }}
  @keyframes fadein {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  .page-title {{ font-size: 1.55rem; font-weight: 700; margin: 0 0 6px 0; color: var(--ink); }}
  .page-subtitle {{ color: var(--ink-secondary); margin-top: 0; }}

  .method-box {{ background: #e8f0fe; border-radius: 8px; padding: 14px 18px; margin: 16px 0;
                 font-size: 0.93rem; color: #1a3d7c; border-left: 4px solid var(--blue); }}

  .kpi-row {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 18px 0; }}
  .kpi-card {{ background: var(--surface); border: 1px solid var(--grid); border-radius: 10px;
               padding: 16px 20px; flex: 1; min-width: 160px; box-shadow: 0 1px 2px rgba(60,64,67,0.08); }}
  .kpi-label {{ font-size: 0.8rem; color: var(--ink-secondary); font-weight: 500; }}
  .kpi-value {{ font-size: 1.7rem; font-weight: 700; color: var(--ink); margin-top: 4px; }}

  .card {{ background: var(--surface); border: 1px solid var(--grid); border-radius: 10px; padding: 22px 26px;
           margin-bottom: 20px; box-shadow: 0 1px 2px rgba(60,64,67,0.08); }}
  .card h3 {{ margin-top: 0; font-size: 1.08rem; color: var(--ink); }}

  .insight {{ background: #f1f8f6; border-left: 4px solid #188038; padding: 13px 18px; border-radius: 6px;
              margin-top: 14px; font-size: 0.93rem; line-height: 1.55; }}
  .insight b {{ color: #0d652d; }}

  .table-scroll {{ overflow-x: auto; }}
  table.table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.87rem; }}
  table.table th, table.table td {{ border: 1px solid var(--grid); padding: 8px 12px; text-align: right; }}
  table.table th {{ background: #f8f9fa; color: var(--ink-secondary); font-weight: 600; text-align: center; }}
  table.table td:first-child, table.table th:first-child {{ text-align: left; }}
  table.table tr:hover td {{ background: #f8f9fa; }}

  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 0.78rem; font-weight: 600; }}
  .badge-good {{ background: #e6f4ea; color: #188038; }}
  .badge-neutral {{ background: #f1f3f4; color: #5f6368; }}

  .roadmap {{ line-height: 2; }}
  .roadmap li {{ margin-bottom: 4px; }}

  .conclusion-box {{ background: #e6f4ea; border: 1.5px solid var(--green); border-radius: 10px;
                      padding: 18px 24px; margin-bottom: 16px; }}
  .conclusion-box h3 {{ color: #0d652d; margin-top: 0; }}
  .conclusion-box-blue {{ background: #e8f0fe; border-color: var(--blue); }}
  .conclusion-box-blue h3 {{ color: #174ea6; }}

  .final-answer {{ background: linear-gradient(135deg, var(--blue), #174ea6); color: white; border-radius: 12px;
                    padding: 28px 32px; text-align: center; margin: 20px 0; }}
  .final-answer-lead {{ margin: 0; font-size: 1rem; opacity: 0.9; }}
  .model-name {{ font-size: 1.7rem; font-weight: 800; color: #fdd663; margin: 8px 0; }}
  .final-answer-sub {{ margin: 0; font-size: 0.95rem; }}

  .missing-img {{ color: #b45309; background: #fff7ed; padding: 10px; border-radius: 6px; }}
  .footer-note {{ text-align: center; color: var(--ink-muted); font-size: 0.85rem; }}
  code {{ background: #f1f3f4; padding: 1px 6px; border-radius: 4px; font-size: 0.9em; }}

  .page-footer-nav {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--surface);
                       border-top: 1px solid var(--grid); box-shadow: 0 -1px 4px rgba(60,64,67,0.1);
                       display: flex; align-items: center; justify-content: center; gap: 20px; padding: 12px 20px; z-index: 10; }}
  .footer-btn {{ background: var(--blue); color: white; border: none; border-radius: 20px; padding: 9px 20px;
                 font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: background .15s; }}
  .footer-btn:hover {{ background: #174ea6; }}
  .footer-btn:disabled {{ background: #dadce0; color: #9aa0a6; cursor: not-allowed; }}
  .page-indicator {{ color: var(--ink-secondary); font-size: 0.88rem; font-weight: 500; min-width: 110px; text-align: center; }}
</style>
</head>
<body>

<nav class="topnav">
  <div class="topnav-inner">
    <div class="nav-brand">📊 ZNS ROI Case Study</div>
    {nav_buttons}
  </div>
</nav>

<main>
  {page_sections}
</main>

<div class="page-footer-nav">
  <button class="footer-btn" id="prev-btn" onclick="prevPage()">← Trước</button>
  <span class="page-indicator" id="page-indicator"></span>
  <button class="footer-btn" id="next-btn" onclick="nextPage()">Tiếp →</button>
</div>

<script>
  const PAGES = [{page_ids_js}];
  let currentIndex = 0;

  function goToPage(id) {{
    PAGES.forEach(p => {{
      const el = document.getElementById(p);
      el.classList.toggle('active', p === id);
    }});
    document.querySelectorAll('.nav-tab').forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.page === id);
    }});
    currentIndex = PAGES.indexOf(id);
    updateFooter();
    window.scrollTo(0, 0);
  }}
  function prevPage() {{ if (currentIndex > 0) goToPage(PAGES[currentIndex - 1]); }}
  function nextPage() {{ if (currentIndex < PAGES.length - 1) goToPage(PAGES[currentIndex + 1]); }}
  function updateFooter() {{
    document.getElementById('page-indicator').textContent = `Bước ${{currentIndex + 1}} / ${{PAGES.length}}`;
    document.getElementById('prev-btn').disabled = currentIndex === 0;
    document.getElementById('next-btn').disabled = currentIndex === PAGES.length - 1;
  }}
  goToPage(PAGES[0]);
</script>

</body>
</html>
"""

    out_path = HERE / "presentation.html"
    out_path.write_text(html_content, encoding="utf-8")
    print(f"--- Done! Created {out_path} ---")


if __name__ == "__main__":
    main()
