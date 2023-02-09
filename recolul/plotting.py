import plotly.graph_objects as go

from recolul.duration import Duration


def plot_overtime_balance_history(days: list[str], overtime_history: list[Duration]) -> None:
    cumulative_overtime_history = []
    for overtime in overtime_history:
        last_cumulative_overtime = (
            cumulative_overtime_history[-1] if cumulative_overtime_history
            else Duration()
        )
        cumulative_overtime_history.append(last_cumulative_overtime + overtime)

    fig = go.Figure(
            data=go.Scatter(
                x=days,
                y=[duration.minutes for duration in cumulative_overtime_history],
                text=[str(duration) for duration in cumulative_overtime_history],
                hovertemplate="%{x} %{text}<extra></extra>",
                mode="lines+markers"
            )
    )
    fig.update_layout(
        yaxis_title="Overtime balance (minutes)"
    )
    fig.show()
