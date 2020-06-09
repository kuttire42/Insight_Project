"""
Grid features from https://github.com/MarcSkovMadsen/awesome-streamlit/blob/\
master/gallery/layout_experiments/app.py
"""

import streamlit as st
import pandas as pd
from typing import List, Optional
import markdown
import io
import matplotlib.pyplot as plt
from pathlib import Path
import base64


COLOR = "white"
BACKGROUND_COLOR = "#000"


class Cell:
    """A Cell can hold text, markdown, plots etc."""

    def __init__(
        self,
        class_: str = None,
        grid_column_start: Optional[int] = None,
        grid_column_end: Optional[int] = None,
        grid_row_start: Optional[int] = None,
        grid_row_end: Optional[int] = None,
    ):
        self.class_ = class_
        self.grid_column_start = grid_column_start
        self.grid_column_end = grid_column_end
        self.grid_row_start = grid_row_start
        self.grid_row_end = grid_row_end
        self.inner_html = ""

    def _to_style(self) -> str:
        return f"""
.{self.class_} {{
    grid-column-start: {self.grid_column_start};
    grid-column-end: {self.grid_column_end};
    grid-row-start: {self.grid_row_start};
    grid-row-end: {self.grid_row_end};
}}
"""

    def text(self, text: str = ""):
        self.inner_html = text

    def image_from_iostream(self, image_iostream, image_size=512):
        byte_str = image_iostream.getvalue()
        encoded = base64.b64encode(byte_str).decode()
        image_html = "<img height='{}' width='{}' src='data:image/png;base64,{}' >".format(image_size,
                                                                                           image_size,
                                                                                           encoded)
        self.inner_html = markdown.markdown(image_html)

    def image_from_file(self, image_filename, image_size=224):
        byte_str = Path(image_filename).read_bytes()
        encoded = base64.b64encode(byte_str).decode()
        image_html = "<img height='{}' width='{}' src='data:image/png;base64,{}'>".format(image_size,
                                                                                           image_size,
                                                                                           encoded)
        self.inner_html = markdown.markdown(image_html)

    def print_home_stats(self, home_stats):
        print_str = """##Statistics for Similar Homes   \n"""
        print_str += 'Average days on the market: %.1f    \n'% home_stats['Avg Days on Market']
        print_str += 'Year Built Range: %s to %s    \n' % (home_stats['Earliest Year Built'],\
                     home_stats['Latest Year Built'])
        print_str += 'Price Range: ${:,} to ${:,}    \n'.format(home_stats['Min Price'],\
                     home_stats['Max Price'])
        self.inner_html = markdown.markdown(print_str)

    def print_home_details(self, home_details_df):
        """
        Prints details for a particular home
        :param home_details_df: Dataframe with 1 row containing details of a particular home
        :return: html for the text to be printed
        """
        print_str = 'Price: ${:,}    \n'.format(home_details_df['PRICE'])
        print_str += 'Number of Beds: %s    \n'%(home_details_df['BEDS'])
        print_str += 'Number of Baths: %s    \n'%(home_details_df['BATHS'])
        print_str += 'URL: <%s>    \n'%(home_details_df['url'])
        self.inner_html = markdown.markdown(print_str)

    def markdown(self, text):
        self.inner_html = markdown.markdown(text)

    def dataframe(self, dataframe: pd.DataFrame):
        self.inner_html = dataframe.to_html()

    def pyplot(self, fig=None, **kwargs):
        string_io = io.StringIO()
        plt.savefig(string_io, format="svg")
        svg = string_io.getvalue()[215:]
        plt.close(fig)
        self.inner_html = '<div height="200px">' + svg + "</div>"

    def _to_html(self):
        return f"""<div class="box {self.class_}">{self.inner_html}</div>"""

class Grid:
    """A (CSS) Grid"""

    def __init__(self, template_columns="1 1 1",
        gap="5px",
        background_color=COLOR,
        color=BACKGROUND_COLOR,
    ):
        self.template_columns = template_columns
        self.gap = gap
        self.background_color = background_color
        self.color = color
        self.cells: List[Cell] = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        st.markdown(self._get_grid_style(), unsafe_allow_html=True)
        st.markdown(self._get_cells_style(), unsafe_allow_html=True)
        st.markdown(self._get_cells_html(), unsafe_allow_html=True)

    def _get_grid_style(self):
        return f"""
<style>
    .wrapper {{
    display: grid;
    grid-template-columns: {self.template_columns};
    grid-gap: {self.gap};
    background-color: {self.background_color};
    color: {self.color};
    }}
    .box {{
    background-color: {self.color};
    color: {self.background_color};
    border-radius: 5px;
    padding: 20px;
    font-size: 150%;
    }}
    table {{
        color: {self.color}
    }}
</style>
"""

    def _get_cells_style(self):
        return (
            "<style>"
            + "\n".join([cell._to_style() for cell in self.cells])
            + "</style>"
        )

    def _get_cells_html(self):
        return (
            '<div class="wrapper">'
            + "\n".join([cell._to_html() for cell in self.cells])
            + "</div>"
        )

    def cell(
        self,
        class_: str = None,
        grid_column_start: Optional[int] = None,
        grid_column_end: Optional[int] = None,
        grid_row_start: Optional[int] = None,
        grid_row_end: Optional[int] = None,
    ):
        cell = Cell(
            class_=class_,
            grid_column_start=grid_column_start,
            grid_column_end=grid_column_end,
            grid_row_start=grid_row_start,
            grid_row_end=grid_row_end,
        )
        self.cells.append(cell)
        return cell

def set_block_container_style(
    max_width: int = 1200,
    max_width_100_percent: bool = True,
    padding_top: int = 5,
    padding_right: int = 1,
    padding_left: int = 1,
    padding_bottom: int = 10,
):
    if max_width_100_percent:
        max_width_str = f"max-width: 100%;"
    else:
        max_width_str = f"max-width: {max_width}px;"
    st.markdown(
        f"""
<style>
    .reportview-container .main .block-container{{
        {max_width_str}
        padding-top: {padding_top}rem;
        padding-right: {padding_right}rem;
        padding-left: {padding_left}rem;
        padding-bottom: {padding_bottom}rem;
    }}
    .reportview-container .main {{
        color: {COLOR};
        background-color: {BACKGROUND_COLOR};
    }}
</style>
""",
        unsafe_allow_html=True,
    )