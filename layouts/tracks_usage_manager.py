# layouts/tracks_usage_manager.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from utils.tracer import trace


def create_tracks_table(tracks, page_current=0, page_size=10):
    """
    Creates a table for track availability data with edit and delete action buttons
    """
    # Calculate indices for pagination
    start_idx = page_current * page_size
    end_idx = start_idx + page_size

    paged_tracks = tracks[start_idx:end_idx] if tracks else []

    # If no data, show message
    if not paged_tracks:
        return html.Div("No track availability data found.", className="text-center my-4")

    # Table headers
    headers = ["ID", "YEAR", "MONTH", "VALUE (%)", "ACTIONS"]

    # Create header row
    header_row = html.Tr([html.Th(h) for h in headers])

    # Create data rows
    data_rows = []
    for i, track in enumerate(paged_tracks):
        # Row ID - important for uniqueness
        row_id = track.get('id', str(i))

        # Create action buttons with unique IDs
        actions = html.Td([
            # Edit button
            dbc.Button(
                html.I(className="fas fa-edit"),
                id={"type": "track-edit-button", "index": row_id, "action": "edit"},
                color="primary",
                size="sm",
                className="me-1",
                title="Edit"
            ),
            # Delete button
            dbc.Button(
                html.I(className="fas fa-trash-alt"),
                id={"type": "track-delete-button", "index": row_id, "action": "delete"},
                color="danger",
                size="sm",
                title="Delete"
            )
        ])

        # Create table row
        row = html.Tr([
            html.Td(row_id),
            html.Td(track.get('year', '')),
            html.Td(track.get('month', '')),
            html.Td(f"{track.get('value', 0):.1f}%"),
            actions
        ])

        data_rows.append(row)

    # Create table
    table = html.Table(
        [html.Thead(header_row), html.Tbody(data_rows)],
        className="table table-striped table-bordered table-hover"
    )

    # Calculate total pages
    total_pages = (len(tracks) - 1) // page_size + 1 if tracks else 1

    # Create pagination
    pagination = dbc.Pagination(
        id="track-pagination",
        active_page=page_current + 1,  # +1 because UI is base 1, but code is base 0
        max_value=total_pages,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        className="mt-3 justify-content-center"
    )

    # Return table with pagination
    return html.Div([
        table,
        pagination,
        html.Div(f"Showing {len(paged_tracks)} of {len(tracks)} records",
                 className="text-muted text-center mt-2")
    ])


def create_usage_table(usage_data, page_current=0, page_size=10):
    """
    Creates a table for usage percentage data with edit and delete action buttons
    """
    # Calculate indices for pagination
    start_idx = page_current * page_size
    end_idx = start_idx + page_size

    paged_usage = usage_data[start_idx:end_idx] if usage_data else []

    # If no data, show message
    if not paged_usage:
        return html.Div("No usage percentage data found.", className="text-center my-4")

    # Table headers
    headers = ["ID", "YEAR", "MONTH", "VALUE (%)", "ACTIONS"]

    # Create header row
    header_row = html.Tr([html.Th(h) for h in headers])

    # Create data rows
    data_rows = []
    for i, usage in enumerate(paged_usage):
        # Row ID - important for uniqueness
        row_id = usage.get('id', str(i))

        # Create action buttons with unique IDs
        actions = html.Td([
            # Edit button
            dbc.Button(
                html.I(className="fas fa-edit"),
                id={"type": "usage-edit-button", "index": row_id, "action": "edit"},
                color="primary",
                size="sm",
                className="me-1",
                title="Edit"
            ),
            # Delete button
            dbc.Button(
                html.I(className="fas fa-trash-alt"),
                id={"type": "usage-delete-button", "index": row_id, "action": "delete"},
                color="danger",
                size="sm",
                title="Delete"
            )
        ])

        # Create table row
        row = html.Tr([
            html.Td(row_id),
            html.Td(usage.get('year', '')),
            html.Td(usage.get('month', '')),
            html.Td(f"{usage.get('value', 0):.1f}%"),
            actions
        ])

        data_rows.append(row)

    # Create table
    table = html.Table(
        [html.Thead(header_row), html.Tbody(data_rows)],
        className="table table-striped table-bordered table-hover"
    )

    # Calculate total pages
    total_pages = (len(usage_data) - 1) // page_size + 1 if usage_data else 1

    # Create pagination
    pagination = dbc.Pagination(
        id="usage-pagination",
        active_page=page_current + 1,  # +1 because UI is base 1, but code is base 0
        max_value=total_pages,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        className="mt-3 justify-content-center"
    )

    # Return table with pagination
    return html.Div([
        table,
        pagination,
        html.Div(f"Showing {len(paged_usage)} of {len(usage_data)} records",
                 className="text-muted text-center mt-2")
    ])


def create_tracks_usage_manager_layout():
    """
    Creates the layout for the track availability and usage percentage manager
    """
    return dbc.Container([
        # Tabs for switching between Track Availability and Usage Percentage
        dbc.Tabs([
            # Track Availability Tab
            dbc.Tab(
                label="Track Availability",
                tab_id="tab-track-availability",
                children=[
                    dbc.Card([
                        dbc.CardHeader("Track Availability Manager"),
                        dbc.CardBody([
                            # Search and action controls
                            dbc.Row([
                                # Search by year
                                dbc.Col([
                                    dbc.Label("Year:"),
                                    dbc.Input(id="track-search-year", type="number", placeholder="Enter year...", className="mb-2")
                                ], md=3),

                                # Search by month
                                dbc.Col([
                                    dbc.Label("Month:"),
                                    dbc.Input(id="track-search-month", type="number", placeholder="Enter month (1-12)...", className="mb-2")
                                ], md=3),

                                # Buttons
                                dbc.Col([
                                    html.Div([
                                        # Search button
                                        dbc.Button(
                                            "Search",
                                            id={"type": "track-search-button", "action": "search"},
                                            color="primary",
                                            className="me-2"
                                        ),

                                        # Add button
                                        dbc.Button(
                                            "Add New",
                                            id="add-track-button",
                                            color="success",
                                            className="me-2"
                                        )
                                    ], className="d-flex align-items-center h-100")
                                ], md=6)
                            ], className="mb-3"),

                            # Container for the table
                            html.Div(
                                id="track-table-container",
                                className="track-table-container",
                                style={
                                    "height": "calc(100vh - 350px)",
                                    "overflow-y": "auto",
                                    "padding-right": "5px"
                                }
                            ),
                        ], style={"height": "calc(100vh - 220px)", "overflow": "hidden"})
                    ], style={"height": "calc(100vh - 170px)"})
                ]
            ),

            # Usage Percentage Tab
            dbc.Tab(
                label="Usage Percentage",
                tab_id="tab-usage-percentage",
                children=[
                    dbc.Card([
                        dbc.CardHeader("Usage Percentage Manager"),
                        dbc.CardBody([
                            # Search and action controls
                            dbc.Row([
                                # Search by year
                                dbc.Col([
                                    dbc.Label("Year:"),
                                    dbc.Input(id="usage-search-year", type="number", placeholder="Enter year...", className="mb-2")
                                ], md=3),

                                # Search by month
                                dbc.Col([
                                    dbc.Label("Month:"),
                                    dbc.Input(id="usage-search-month", type="number", placeholder="Enter month (1-12)...", className="mb-2")
                                ], md=3),

                                # Buttons
                                dbc.Col([
                                    html.Div([
                                        # Search button
                                        dbc.Button(
                                            "Search",
                                            id={"type": "usage-search-button", "action": "search"},
                                            color="primary",
                                            className="me-2"
                                        ),

                                        # Add button
                                        dbc.Button(
                                            "Add New",
                                            id="add-usage-button",
                                            color="success",
                                            className="me-2"
                                        )
                                    ], className="d-flex align-items-center h-100")
                                ], md=6)
                            ], className="mb-3"),

                            # Container for the table
                            html.Div(
                                id="usage-table-container",
                                className="usage-table-container",
                                style={
                                    "height": "calc(100vh - 350px)",
                                    "overflow-y": "auto",
                                    "padding-right": "5px"
                                }
                            ),
                        ], style={"height": "calc(100vh - 220px)", "overflow": "hidden"})
                    ], style={"height": "calc(100vh - 170px)"})
                ]
            ),
        ], id="tracks-usage-tabs", active_tab="tab-track-availability"),

        # Common components for both tabs

        # Status toasts
        dbc.Toast(
            id="track-operation-status",
            header="Operation Status",
            is_open=False,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 20, "right": 20, "width": 350}
        ),
        dbc.Toast(
            id="usage-operation-status",
            header="Operation Status",
            is_open=False,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 80, "right": 20, "width": 350}
        ),

        # Track availability modals
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirm Delete")),
            dbc.ModalBody([
                html.P(id="track-delete-confirmation-message"),
                dbc.Input(id="track-delete-id", type="hidden")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="track-cancel-delete-button", color="secondary", className="me-2"),
                dbc.Button("Confirm", id="track-confirm-delete-button", color="danger")
            ])
        ], id="track-delete-modal", is_open=False),

        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="track-form-title")),
            dbc.ModalBody([
                # Hidden fields for mode and ID
                dbc.Input(id="track-form-mode", type="hidden", value="add"),
                dbc.Input(id="track-edit-id", type="hidden", value=""),

                # Form fields
                dbc.Label("Year:", html_for="track-year-input"),
                dbc.Input(
                    id="track-year-input",
                    type="number",
                    placeholder="Enter year",
                    className="mb-3"
                ),

                dbc.Label("Month:", html_for="track-month-input"),
                dbc.Input(
                    id="track-month-input",
                    type="number",
                    placeholder="Enter month (1-12)",
                    min=1,
                    max=12,
                    className="mb-3"
                ),

                dbc.Label("Value (%):", html_for="track-value-input"),
                dbc.Input(
                    id="track-value-input",
                    type="number",
                    placeholder="Enter percentage value",
                    step=0.1,
                    className="mb-3"
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="track-cancel-form-button", color="secondary", className="me-2"),
                dbc.Button("Save", id="track-save-form-button", color="primary")
            ])
        ], id="track-form-modal", is_open=False),

        # Usage percentage modals
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirm Delete")),
            dbc.ModalBody([
                html.P(id="usage-delete-confirmation-message"),
                dbc.Input(id="usage-delete-id", type="hidden")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="usage-cancel-delete-button", color="secondary", className="me-2"),
                dbc.Button("Confirm", id="usage-confirm-delete-button", color="danger")
            ])
        ], id="usage-delete-modal", is_open=False),

        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="usage-form-title")),
            dbc.ModalBody([
                # Hidden fields for mode and ID
                dbc.Input(id="usage-form-mode", type="hidden", value="add"),
                dbc.Input(id="usage-edit-id", type="hidden", value=""),

                # Form fields
                dbc.Label("Year:", html_for="usage-year-input"),
                dbc.Input(
                    id="usage-year-input",
                    type="number",
                    placeholder="Enter year",
                    className="mb-3"
                ),

                dbc.Label("Month:", html_for="usage-month-input"),
                dbc.Input(
                    id="usage-month-input",
                    type="number",
                    placeholder="Enter month (1-12)",
                    min=1,
                    max=12,
                    className="mb-3"
                ),

                dbc.Label("Value (%):", html_for="usage-value-input"),
                dbc.Input(
                    id="usage-value-input",
                    type="number",
                    placeholder="Enter percentage value",
                    step=0.1,
                    className="mb-3"
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="usage-cancel-form-button", color="secondary", className="me-2"),
                dbc.Button("Save", id="usage-save-form-button", color="primary")
            ])
        ], id="usage-form-modal", is_open=False),

        # Hidden data stores
        dcc.Store(id="track-data-store", data={}),
        dcc.Store(id="usage-data-store", data={}),
        html.Div(id="track-delete-refresh", style={'display': 'none'}),
        html.Div(id="usage-delete-refresh", style={'display': 'none'})
    ], fluid=True, style={"height": "100vh", "padding": "1rem"})
