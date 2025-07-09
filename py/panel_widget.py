import panel as pn
import xarray as xr
from py import generate_graphs as gg
from py import utils
from datetime import datetime
from flask import session, has_request_context
import os
import uuid
from py import forecasted_graphs as fg
from py import skill_score as ss
import io

pn.extension()

def get_panel_layout():

    # Custom CSS to enlarge the input fields (year labels)
    custom_css = pn.pane.HTML("""
    <style>
    .bigger-slider input[type='number'] {
        font-size: 18px !important;
        height: 32px;
        padding: 2px 6px;
    }
    .bigger-slider .bk-slider-title {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """)


    year_slider = pn.widgets.EditableRangeSlider(
        name='Year Range',
        start=1981, end=datetime.now().year,
        step=1,
        width=600,  # increase the width
        margin=(10, 0),  # optional: adds some vertical spacing
        css_classes=["bigger-slider"]
    )

    update_button = pn.widgets.Button(name='Generate Images', button_type='primary')


    status = pn.pane.Markdown()
    # Create 4 image panes
    image_pane_hurricane = pn.pane.PNG(height=300, width=500)
    image_pane_tc = pn.pane.PNG(height=300, width=500)
    image_pane_ace = pn.pane.PNG(height=300, width=500)
    image_pane_pdi = pn.pane.PNG(height=300, width=500)

    # Arrange them in a grid with captions below each image
    #image_grid = pn.GridSpec(sizing_mode='stretch_both', max_width=1000)
    #image_grid[0, 0] = pn.Column(image_pane_hurricane, pn.pane.Markdown("**Figure 1: Hurricane Frequency**"), margin=(10, 10, 30, 10))
    #image_grid[0, 1] = pn.Column(image_pane_tc, pn.pane.Markdown("**Figure 2: Tropical Cyclone Count**"), margin=(10, 10, 30, 10))
    #image_grid[1, 0] = pn.Column(image_pane_ace, pn.pane.Markdown("**Figure 3: ACE (Accumulated Cyclone Energy)**"), margin=(10, 10, 30, 10))
    #image_grid[1, 1] = pn.Column(image_pane_pdi, pn.pane.Markdown("**Figure 4: Power Dissipation Index (PDI)**"), margin=(10, 10, 30, 10))


    image_grid = pn.GridBox(
        pn.Column(image_pane_hurricane),
        pn.Column(image_pane_tc),
        pn.Column(image_pane_ace),
        pn.Column(image_pane_pdi),
        ncols=2,
        sizing_mode='stretch_width',
        width=1000,
        align='center',
        margin=10,
    )


    # centered_layout = pn.Column(
    # image_grid,
    #align='center',  # horizontally center the contents
    #width=950         # adjust based on your image widths + spacing
    #)



    def get_user_id():
        if has_request_context() and session.get('user_id'):
            return session['user_id']
        else:
            return str(uuid.uuid4())
        
    # This pane contains JavaScript to send a postMessage to the parent page
    message_pane = pn.pane.HTML("""
    <script>
      function notifyParentImagesUpdated() {
        window.parent.postMessage("images_updated", "*");
      }
    </script>
    """)

    def update_plot(event):
        start, end = year_slider.value
        user_id = get_user_id()
        
        try:
            image_pane_hurricane.object = gg.generate_image_for_user(start, end, user_id, 'Hurricane')
            image_pane_tc.object = gg.generate_image_for_user(start, end, user_id, 'Tropical Cyclone')
            image_pane_ace.object = gg.generate_image_for_user(start, end, user_id, 'ACE')
            image_pane_pdi.object = gg.generate_image_for_user(start, end, user_id, 'PDI')
            status.object = f"Images updated for {start}–{end}"
        except Exception as e:
            status.object = f"Error updating images: {e}"

        status.object = f"Images updated for {start}–{end}"
        message_pane.object += "<script>notifyParentImagesUpdated()</script>"

    update_button.on_click(update_plot)

    return pn.Column(
        custom_css,
        pn.pane.Markdown("<h2 style='font-size:28px;'>Interactive Year Selector</h2>", sizing_mode="stretch_width"),
        pn.pane.Markdown("<p style='font-size:18px;'>Use the slider below to select a range of years for plotting.</p>", sizing_mode="stretch_width"),
        year_slider,
        update_button,
        status,
        message_pane,
        image_grid,
        #centered_layout
        sizing_mode="stretch_width",
        #max_width=1600,
        align='center'
    )







def get_forecast_layout():

    # Custom CSS to enlarge the input fields (year labels)
    custom_css = pn.pane.HTML("""
    <style>
    .bigger-slider input[type='number'] {
        font-size: 18px !important;
        height: 32px;
        padding: 2px 6px;
    }
    .bigger-slider .bk-slider-title {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """)



    # make a drop down menu for quantity of interest (ex. pdi)
    quantities = ['Hurricane', 'Tropical Cyclone', 'ACE', 'PDI']
    quantity_select = pn.widgets.Select(name='Quantity of Interest', options=quantities, value='Hurricane')
    # or use Dropdown:
    # quantity_select = pn.widgets.Dropdown(name='Quantity of Interest', options=quantities, value='Hurricane')
    # select one (for now) for init month
    init_month_multi_select = pn.widgets.Select(
        name='Initialization Month(s)',
        options=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August'],
        value='June',  # default selection
    )
    # select one (for now) for research center (model)
    model_multi_select = pn.widgets.Select(
        name='Research Center(s)',
        options=['BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO'],
        value='ECMWF',  # default selection
    )

    year_slider = pn.widgets.EditableRangeSlider(
        name='Year Range',
        start=1981, end=datetime.now().year,
        step=1,
        width=600,  # increase the width
        margin=(10, 0),  # optional: adds some vertical spacing
        css_classes=["bigger-slider"]
    )

    update_button = pn.widgets.Button(name='Generate Images', button_type='primary')


    status = pn.pane.Markdown()
    # Create 2 image panes -- one is time series, one is skill score
    image_pane_time_series = pn.pane.PNG(height=300, width=500)
    image_pane_skill_score_mdr = pn.pane.PNG(height=300, width=500)
    image_pane_skill_score_trop = pn.pane.PNG(height=300, width=500)

    # Arrange them in a grid with captions below each image
    #image_grid = pn.GridSpec(sizing_mode='stretch_both', max_width=1000)
    #image_grid[0, 0] = pn.Column(image_pane_hurricane, pn.pane.Markdown("**Figure 1: Hurricane Frequency**"), margin=(10, 10, 30, 10))
    #image_grid[0, 1] = pn.Column(image_pane_tc, pn.pane.Markdown("**Figure 2: Tropical Cyclone Count**"), margin=(10, 10, 30, 10))
    #image_grid[1, 0] = pn.Column(image_pane_ace, pn.pane.Markdown("**Figure 3: ACE (Accumulated Cyclone Energy)**"), margin=(10, 10, 30, 10))
    #image_grid[1, 1] = pn.Column(image_pane_pdi, pn.pane.Markdown("**Figure 4: Power Dissipation Index (PDI)**"), margin=(10, 10, 30, 10))


    # image_grid = pn.GridBox(
     #   pn.Column(image_pane_time_series),
     #   pn.Column(image_pane_skill_score_mdr),
     #   pn.Column(image_pane_skill_score_trop), 
    #    ncols=2,
      #  sizing_mode='stretch_width',
      #  width=1000,
      #  align='center',
      #  margin=10,
    #)
    # Top image: time series
    # Bottom row: skill scores (MDR and Trop)
    image_grid = pn.Column(
        pn.Row(
            pn.Column(image_pane_time_series),
            sizing_mode='stretch_width',
            align='center'
        ),
        pn.Row(
            pn.Column(image_pane_skill_score_mdr),
            pn.Column(image_pane_skill_score_trop),
            sizing_mode='stretch_width',
            align='center'
        ),
        sizing_mode='stretch_width',
        width=1000,
        margin=10,
    )


    # centered_layout = pn.Column(
    # image_grid,
    #align='center',  # horizontally center the contents
    #width=950         # adjust based on your image widths + spacing
    #)



    def get_user_id():
        if has_request_context() and session.get('user_id'):
            return session['user_id']
        else:
            return str(uuid.uuid4())
        
    # This pane contains JavaScript to send a postMessage to the parent page
    message_pane = pn.pane.HTML("""
    <script>
      function notifyParentImagesUpdated() {
        window.parent.postMessage("images_updated", "*");
      }
    </script>
    """)

    def update_plot(event):
        start, end = year_slider.value
        user_id = get_user_id()
        selected_quantity = quantity_select.value
        selected_center = model_multi_select.value
        selected_init_month = init_month_multi_select.value
        
        try:
            # img_bytes = fg.panel_predicted_graph(selected_quantity, start, end, selected_init_month, selected_center)
            # image_pane_time_series.object = io.BytesIO(img_bytes)
            image_pane_time_series.object = fg.panel_predicted_graph(selected_quantity, start, end, selected_init_month, selected_center)
            image_pane_skill_score_mdr.object = ss.skill_score_generate_graph('mdr', selected_center, selected_init_month, start, end)
            image_pane_skill_score_trop.object = ss.skill_score_generate_graph('trop', selected_center, selected_init_month, start, end)
            status.object = f"Images updated for {start}–{end}"
        except Exception as e:
            status.object = f"Error updating images: {e}"

        status.object = f"Images updated for {start}–{end}"
        message_pane.object += "<script>notifyParentImagesUpdated()</script>"

    update_button.on_click(update_plot)

    return pn.Column(
        custom_css,
        pn.pane.Markdown("<h2 style='font-size:28px;'>Interactive Year Selector</h2>", sizing_mode="stretch_width"),
        pn.pane.Markdown("<p style='font-size:18px;'>Use the slider below to select a range of years for plotting.</p>", sizing_mode="stretch_width"),
        quantity_select,
        model_multi_select,
        init_month_multi_select,
        year_slider,
        update_button,
        status,
        message_pane,
        image_grid,
        #centered_layout
        sizing_mode="stretch_width",
        #max_width=1600,
        align='center'
    )
