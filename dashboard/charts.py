import pandas as pd  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]


# Why: Decoupling chart generation into pure functions allows headless unit testing without running Streamlit.


def create_gender_pie(data: dict) -> go.Figure:
    """Create a donut chart for user gender ratio."""
    ratio = data.get("gender_ratio", {})
    labels = [k.title() for k in ratio.keys()]
    values = list(ratio.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=["#3b82f6", "#ec4899"]),
            )
        ]
    )
    fig.update_layout(title="Gender Breakdown", margin=dict(t=40, b=20, l=20, r=20))
    return fig


def create_bmi_pie(data: dict) -> go.Figure:
    """Create a pie chart for user BMI category percentages."""
    bmi_pct = data.get("bmi_categories_pct", {})
    labels = [k.title() for k in bmi_pct.keys()]
    values = list(bmi_pct.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=["#10b981", "#f59e0b", "#ef4444", "#6366f1"]),
            )
        ]
    )
    fig.update_layout(title="BMI Categories (%)", margin=dict(t=40, b=20, l=20, r=20))
    return fig


def create_activity_pie(data: dict) -> go.Figure:
    """Create a pie chart for user activity level distribution."""
    activity = data.get("activity_level_ratio", {})
    labels = [k.replace("_", " ").title() for k in activity.keys()]
    values = list(activity.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
            )
        ]
    )
    fig.update_layout(title="Activity Levels", margin=dict(t=40, b=20, l=20, r=20))
    return fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create a correlation heatmap matrix from numeric health metrics."""
    # Why: texttemplate forces Plotly to display rounded values directly inside each heatmap cell.
    fig = go.Figure(
        data=go.Heatmap(
            z=df.values,
            x=df.columns.tolist(),
            y=df.index.tolist(),
            colorscale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            text=df.round(2).values,
            texttemplate="%{text}",
        )
    )
    fig.update_layout(
        title="Metrics Correlation Heatmap",
        xaxis=dict(tickangle=-30),
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


def create_popular_exercises_bar(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create a horizontal bar chart of the most logged exercises."""
    top_df = df.sort_values(by="interaction_count", ascending=True).tail(top_n)

    fig = go.Figure(
        data=[
            go.Bar(
                x=top_df["interaction_count"],
                y=top_df["name"],
                orientation="h",
                marker=dict(color="#2563eb"),
                hovertemplate="%{y}: %{x} logs<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=f"Top {top_n} Most Popular Exercises",
        xaxis_title="Interaction Count",
        yaxis_title="Exercise",
        margin=dict(t=40, b=40, l=150, r=20),
    )
    return fig


def create_macro_comparison_bar(df: pd.DataFrame) -> go.Figure:
    """Create a grouped bar chart comparing macros between veg and non-veg foods."""
    macros = [
        ("avg_protein_g", "Protein (g)"),
        ("avg_carbs_g", "Carbs (g)"),
        ("avg_fat_g", "Fat (g)"),
        ("avg_fiber_g", "Fiber (g)"),
    ]

    fig = go.Figure()
    for _, row in df.iterrows():
        diet_label = "Vegetarian" if row["diet_type"] == "veg" else "Non-Vegetarian"
        values = [row[col] for col, _ in macros]
        fig.add_trace(
            go.Bar(
                name=diet_label,
                x=[label for _, label in macros],
                y=values,
            )
        )

    fig.update_layout(
        barmode="group",
        title="Macronutrient Comparison per 100g (Veg vs Non-Veg)",
        yaxis_title="Grams (g)",
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


def create_daily_metrics_chart(data: dict) -> go.Figure:
    """Create side-by-side benchmark bars for daily sleep and water intake."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Sleep Hours Benchmark", "Daily Water Intake (mL)"),
    )

    sleep = data.get("sleep_hours", {})
    water = data.get("water_ml", {})

    fig.add_trace(
        go.Bar(
            name="Sleep (hrs)",
            x=["Q25", "Mean", "Q70"],
            y=[sleep.get("q25", 0), sleep.get("mean", 0), sleep.get("q70", 0)],
            marker=dict(color="#8b5cf6"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            name="Water (mL)",
            x=["Mean", "Median"],
            y=[water.get("mean", 0), water.get("median", 0)],
            marker=dict(color="#06b6d4"),
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        title="Daily Health Habits Benchmarks",
        showlegend=False,
        margin=dict(t=60, b=40, l=40, r=20),
    )
    return fig


def create_weight_history_chart(weight_history: list[dict]) -> go.Figure:
    """Create a line chart showing personal user weight progression over time."""
    dates = [entry.get("date", "") for entry in weight_history]
    weights = [entry.get("weight_kg", 0.0) for entry in weight_history]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=weights,
                mode="lines+markers",
                name="Weight (kg)",
                line=dict(color="#10b981", width=3),
                marker=dict(size=8, color="#059669"),
                hovertemplate="%{x}: %{y} kg<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Weight History Progress",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        margin=dict(t=40, b=40, l=50, r=20),
    )
    return fig


def create_user_calorie_balance_chart(kcal_in: float, kcal_out: float) -> go.Figure:
    """Create a bar chart comparing user total caloric intake vs expenditure."""
    fig = go.Figure(
        data=[
            go.Bar(
                x=["Calorie Intake (In)", "Calorie Burned (Out)"],
                y=[kcal_in, kcal_out],
                marker=dict(color=["#f97316", "#3b82f6"]),
                text=[f"{kcal_in:,.0f} kcal", f"{kcal_out:,.0f} kcal"],
                textposition="auto",
            )
        ]
    )
    deficit = kcal_out - kcal_in
    deficit_text = f"Net Deficit: {deficit:,.0f} kcal" if deficit >= 0 else f"Net Surplus: {-deficit:,.0f} kcal"
    fig.update_layout(
        title=f"Total Calorie Balance ({deficit_text})",
        yaxis_title="Calories (kcal)",
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


def create_population_clusters_bar(clusters: list[dict]) -> go.Figure:
    """Create a bar chart showing user counts across KMeans demographic clusters."""
    names = [c.get("name", f"Cluster {c.get('cluster_id')}") for c in clusters]
    counts = [c.get("user_count", 0) for c in clusters]

    fig = go.Figure(
        data=[
            go.Bar(
                x=names,
                y=counts,
                marker=dict(color="#8b5cf6"),
                text=[f"{count} users" for count in counts],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Population Clusters Breakdown",
        xaxis_title="Cluster Archetype",
        yaxis_title="User Count",
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig

