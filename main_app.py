import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash import dash_table
from utils import load_config, parse_contents, generate_csv

import base64


config = load_config("config.json")

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    [
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=False,
        ),
        html.Div("CSV Separator: "),
        dcc.Input(
            id="csv-separator",
            type="text",
            placeholder="Enter CSV separator",
            value=",",
            style={"margin": "10px"},
        ),
        html.Button(
            "Preview and Map", id="preview-and-map-button", style={"margin": "10px"}
        ),
        html.Div(id="file-preview"),
        html.Div(id="column-mapper"),
        html.Div(id="mapping-result"),
        html.Div(id="generated-csv"),
        html.Button("Generate CSV", id="generate-csv-button", style={"margin": "10px"}),
    ]
)


@app.callback(
    Output("file-preview", "children"),
    Output("column-mapper", "children"),
    Input("preview-and-map-button", "n_clicks"),
    State("upload-data", "contents"),
    State("csv-separator", "value"),
    State("upload-data", "filename"),
)
def update_preview_and_mapper(n_clicks, contents, separator, filename):
    if contents is None or n_clicks is None:
        return [html.Div()], [html.Div()]

    try:
        df = parse_contents(contents, filename, separator)
    except Exception:
        return [html.Div(["Error processing file"])], [html.Div()]

    expected_columns = config["expected_columns"]
    mapper = [
        html.Div(
            [
                html.P(f"Map {column}:"),
                dcc.Dropdown(
                    id={"type": "dropdown", "index": i},
                    options=[{"label": col, "value": col} for col in df.columns],
                ),
            ],
            style={"display": "inline-block", "width": "30%", "margin": "5px"},
        )
        for i, column in enumerate(expected_columns)
    ]

    return (
        dash_table.DataTable(
            data=df.head().to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_cell={"textAlign": "left"},
        ),
        mapper,
    )


@app.callback(
    Output("mapping-result", "children"),
    [Input(f"dropdown-{i}", "value") for i in range(len(config["expected_columns"]))],
)
def display_mapping(*column_mappings):
    mapped_columns = zip(config["expected_columns"], column_mappings)
    return html.Div(
        [
            html.P(f"Mapped columns:"),
            html.Ul(
                [
                    html.Li(f"{expected_col}: {mapped_col}")
                    for expected_col, mapped_col in mapped_columns
                ]
            ),
        ]
    )


def dropdowns_exist(layout):
    ids_in_layout = [
        child.id for child in layout.children if hasattr(child, "id") and child.id
    ]
    return all(
        [
            f"dropdown-{i}" in ids_in_layout
            for i in range(len(config["expected_columns"]))
        ]
    )


@app.callback(
    Output("generated-csv", "children"),
    Input("generate-csv-button", "n_clicks"),
    State("upload-data", "contents"),
    State("csv-separator", "value"),
    State("upload-data", "filename"),
    State({"type": "dropdown", "index": ALL}, "value"),
)
def generate_new_csv(n_clicks, contents, separator, filename, column_mappings):
    if contents is None or n_clicks is None:
        return html.Div()

    try:
        df = parse_contents(contents, filename, separator)
    except Exception:
        return html.Div(["Error processing file"])

    if None in column_mappings:
        return html.Div(["Please map all columns before generating the CSV file"])

    column_mapping_dict = dict(zip(config["expected_columns"], column_mappings))
    new_csv = generate_csv(df, column_mapping_dict, separator)
    encoded_csv = base64.b64encode(new_csv.encode()).decode()

    return html.Div(
        [
            html.H5("Download your new CSV file:"),
            html.A(
                "Download CSV",
                href=f"data:text/csv;base64,{encoded_csv}",
                download="new_csv_file.csv",
            ),
        ]
    )
