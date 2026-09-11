import markdown

from app.models.notification import Notification


def build_weekly_summary_html(
    notification: Notification,
) -> str:

    period_start = notification.period_start.strftime("%b %-d, %Y")
    period_end = notification.period_end.strftime("%b %-d, %Y")

    markdown_content = notification.content or ""

    content_html = markdown.markdown(
        markdown_content,
        extensions=[
            "extra",
            "sane_lists",
        ],
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Weekly Expense Summary</title>
    </head>

    <body style="
        margin: 0;
        padding: 0;
        background-color: #f7f5f2;
        font-family: Arial, Helvetica, sans-serif;
        color: #251f1a;
    ">

    <table
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="background-color: #f7f5f2; padding: 40px 16px;"
    >
        <tr>
            <td align="center">

                <!-- Main Card -->
                <table
                    width="600"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    style="
                        width: 100%;
                        max-width: 600px;
                        background-color: #ffffff;
                        border: 1px solid #e8e2dc;
                        border-radius: 10px;
                        overflow: hidden;
                    "
                >

                    <!-- Header -->
                    <tr>
                        <td style="
                            padding: 32px;
                            background-color: #ffffff;
                            border-bottom: 1px solid #eee8e2;
                        ">

                            <div style="
                                font-size: 12px;
                                font-weight: 600;
                                letter-spacing: 1.4px;
                                text-transform: uppercase;
                                color: #6f665e;
                                margin-bottom: 10px;
                            ">
                                Expense Tracker
                            </div>

                            <h1 style="
                                margin: 0;
                                font-size: 28px;
                                line-height: 1.25;
                                font-weight: 700;
                                color: #251f1a;
                            ">
                                Weekly Expense Summary
                            </h1>

                            <div style="
                                margin-top: 8px;
                                font-size: 14px;
                                line-height: 1.5;
                                color: #746b63;
                            ">
                                {period_start} – {period_end}
                            </div>

                        </td>
                    </tr>


                    <!-- Content -->
                    <tr>
                        <td style="
                            padding: 32px;
                        ">

                            <div style="
                                font-size: 15px;
                                line-height: 1.7;
                                color: #3f3832;
                            ">

                                <style>
                                    h2 {{
                                        margin: 28px 0 12px;
                                        font-size: 18px;
                                        line-height: 1.4;
                                        color: #251f1a;
                                    }}

                                    h3 {{
                                        margin: 22px 0 10px;
                                        font-size: 16px;
                                        color: #251f1a;
                                    }}

                                    p {{
                                        margin: 0 0 14px;
                                    }}

                                    strong {{
                                        color: #251f1a;
                                        font-weight: 700;
                                    }}

                                    ul {{
                                        margin: 8px 0 18px;
                                        padding-left: 22px;
                                    }}

                                    li {{
                                        margin-bottom: 8px;
                                    }}

                                    hr {{
                                        border: 0;
                                        border-top: 1px solid #eee8e2;
                                        margin: 22px 0;
                                    }}
                                </style>

                                {content_html}

                            </div>

                        </td>
                    </tr>


                    <!-- Footer -->
                    <tr>
                        <td style="
                            padding: 20px 32px;
                            background-color: #faf9f7;
                            border-top: 1px solid #eee8e2;
                            text-align: center;
                        ">

                            <div style="
                                font-size: 12px;
                                line-height: 1.5;
                                color: #91877e;
                            ">
                                Generated automatically by your Expense Tracker
                            </div>

                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

    </body>
    </html>
    """
